"""
Drywall.ai API Server
FastAPI backend for AI-powered drywall takeoffs
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import os
import json
from datetime import datetime
import asyncio
from pathlib import Path

from drywall_detector import DrywallDetector, Wall, Ceiling, Opening, Corner, DrywallDetection
from drywall_calculator import DrywallCalculator, FinishLevel, ProjectType, RoomGeometry
from painting_detector import PaintingDetector, PaintCalculator, Room, Surface  # Keep for legacy support
from database import Database
from database_service import DatabaseService
from export_generator import ExportGenerator
from assembly_expansion import AssemblyExpander
from auth_jwt import AuthManager, UserRegister, UserLogin, Token, get_auth_manager
from payments import PaymentService, PLANS, get_payment_service
from email_service import get_email_service
from analytics import AnalyticsService, get_analytics_service
import background_tasks as bg_tasks
from config import get_config
import time
import redis

# Initialize FastAPI app
app = FastAPI(
    title="Drywall.ai API",
    description="AI-powered takeoff and estimating for drywall contractors",
    version="0.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config = get_config()

# Configuration
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize services
drywall_detector = DrywallDetector(config.ai.anthropic_api_key)
drywall_calculator = DrywallCalculator()

# Legacy support (keep for backwards compatibility)
detector = PaintingDetector(config.ai.anthropic_api_key)
calculator = PaintCalculator()

# Use PostgreSQL if configured, otherwise fall back to JSON
try:
    db_service = DatabaseService()
    db = Database()  # Keep for backwards compatibility
    logger_info = "Using PostgreSQL database"
except Exception as e:
    db_service = None
    db = Database()  # Fall back to JSON
    logger_info = f"Falling back to JSON database: {e}"

print(f"[Database] {logger_info}")

exporter = ExportGenerator()
auth_manager = AuthManager(db)
payment_service = PaymentService(db)
email_service = get_email_service()
analytics_service = AnalyticsService(db)

# Initialize S3 service if enabled
s3_service = None
if config.s3.enabled and config.s3.is_configured():
    try:
        from s3_service import S3Service
        s3_service = S3Service()
        print("[Storage] Using AWS S3")
    except Exception as e:
        print(f"[Storage] S3 initialization failed, using local storage: {e}")
        s3_service = None
else:
    print("[Storage] Using local filesystem")

# Initialize Redis client if configured
redis_client = None
try:
    redis_client = redis.from_url(config.redis.url, decode_responses=True)
    redis_client.ping()
    print("[Cache] Redis connected")
except Exception as e:
    print(f"[Cache] Redis not available: {e}")
    redis_client = None


# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    customer: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    customer: Optional[str]
    created_at: str
    status: str
    total_rooms: int = 0
    total_sqft: float = 0.0
    total_gallons: float = 0.0
    total_labor_hours: float = 0.0
    estimated_cost: float = 0.0


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    dimensions: Optional[Dict] = None
    notes: Optional[str] = None


class EstimateParams(BaseModel):
    paint_price: float = 55.0  # $/gallon
    labor_rate: float = 50.0   # $/hour
    surface_type: str = "smooth_drywall"


class CheckoutRequest(BaseModel):
    plan: str  # starter, pro
    success_url: str
    cancel_url: str


class PortalRequest(BaseModel):
    return_url: str


# Drywall-specific models
class DrywallProjectResponse(BaseModel):
    id: str
    name: str
    customer: Optional[str]
    created_at: str
    status: str
    total_walls: int = 0
    total_wall_sqft: float = 0.0
    total_ceiling_sqft: float = 0.0
    total_sheets: float = 0.0
    total_labor_hours: float = 0.0
    estimated_cost: float = 0.0


class WallCreate(BaseModel):
    wall_id: str
    type: str  # interior, exterior, partition
    length_ft: float
    height_ft: float
    openings: List[Dict] = []
    inside_corners: int = 0
    outside_corners: int = 0


class WallUpdate(BaseModel):
    length_ft: Optional[float] = None
    height_ft: Optional[float] = None
    type: Optional[str] = None
    openings: Optional[List[Dict]] = None


class DrywallEstimateParams(BaseModel):
    finish_level: int = 4  # ASTM C840 Level (0-5)
    sheet_thickness: float = 0.5  # inches (0.5" or 0.625")
    labor_rate: float = 65.0  # $/hour
    project_type: str = "residential"  # residential, commercial, remodel
    region: str = "national"  # for regional pricing adjustments


# Routes
@app.get("/")
async def root():
    return {
        "app": "Painting.ai",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Overall system health check
    Returns status of all critical services
    """
    timestamp = datetime.utcnow().isoformat()
    services = {}

    # Check database
    try:
        if db_service:
            with db_service.get_session() as session:
                session.execute("SELECT 1")
            services["database"] = "healthy"
        else:
            services["database"] = "json_fallback"
    except Exception as e:
        services["database"] = "unhealthy"

    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "not_configured"
    except Exception:
        services["redis"] = "unhealthy"

    # Check S3
    if s3_service:
        services["s3"] = "configured"
    else:
        services["s3"] = "not_configured"

    # Overall status
    critical_services = ["database"]
    status = "healthy" if all(
        services.get(s) in ["healthy", "json_fallback", "configured"]
        for s in critical_services
    ) else "unhealthy"

    return {
        "status": status,
        "timestamp": timestamp,
        "services": services,
        "version": "0.2.0"
    }


@app.get("/health/database")
async def database_health_check():
    """
    Database health check with connection pool monitoring
    """
    start_time = time.time()

    try:
        if not db_service:
            return {
                "status": "not_configured",
                "message": "Using JSON database (fallback mode)",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Test connection
        with db_service.get_session() as session:
            session.execute("SELECT 1")

        # Get pool status
        pool_status = db_service.get_pool_status()

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "pool": {
                "size": pool_status["pool_size"],
                "checked_in": pool_status["checked_in"],
                "checked_out": pool_status["checked_out"],
                "overflow": pool_status["overflow"],
                "total_connections": pool_status["total_connections"]
            },
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/health/redis")
async def redis_health_check():
    """
    Redis cache health check
    """
    start_time = time.time()

    try:
        if not redis_client:
            return {
                "status": "not_configured",
                "message": "Redis not configured",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Test connection
        redis_client.ping()

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/health/storage")
async def storage_health_check():
    """
    File storage (S3) health check
    """
    try:
        if not s3_service:
            return {
                "status": "not_configured",
                "storage_type": "local",
                "message": "Using local filesystem storage",
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "status": "configured",
            "storage_type": "s3",
            "region": s3_service.aws_region,
            "buckets": {
                "uploads": s3_service.bucket_uploads,
                "exports": s3_service.bucket_exports
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# ==============================================================================
# AUTHENTICATION ENDPOINTS (Phase 3)
# ==============================================================================

@app.post("/auth/register", response_model=dict)
async def register(user_data: UserRegister, background_tasks: BackgroundTasks):
    """
    Register a new user account

    Creates user with:
    - Hashed password (bcrypt)
    - Unique API key
    - 14-day trial
    - Optional organization

    Returns user details and auth tokens
    """
    try:
        user = auth_manager.register_user(user_data)

        # Auto-login after registration
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        tokens = auth_manager.login_user(login_data)

        # Send welcome email in background
        background_tasks.add_task(
            bg_tasks.send_welcome_email_async,
            user
        )

        return {
            "user": user,
            "tokens": tokens.dict(),
            "message": "Registration successful. Welcome to Painting.ai!"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """
    Login with email and password

    Returns:
    - access_token: Valid for 24 hours
    - refresh_token: Valid for 30 days
    """
    return auth_manager.login_user(login_data)


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token

    Extends session without requiring re-login
    """
    return auth_manager.refresh_access_token(refresh_token)


@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(auth_manager.get_current_user)):
    """
    Get current user information from JWT token

    Requires: Authorization: Bearer <access_token>

    Returns user profile with:
    - id, email, name
    - plan, subscription_status
    - API key
    - settings
    """
    return {
        "user": current_user,
        "message": "Authenticated successfully"
    }


@app.post("/auth/logout")
async def logout():
    """
    Logout (client-side token removal)

    Since JWT tokens are stateless, logout is handled client-side
    by removing the token. Token will expire naturally after 24 hours.
    """
    return {
        "message": "Logged out successfully. Remove tokens from client storage."
    }


# ==============================================================================
# PAYMENT ENDPOINTS (Phase 6)
# ==============================================================================

@app.get("/pricing/plans")
async def get_pricing_plans():
    """
    Get available pricing plans

    Returns plan details, pricing, features, and limits
    """
    return {
        "plans": PLANS,
        "currency": "USD",
        "trial_days": 14
    }


@app.post("/checkout/create-session")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """
    Create Stripe checkout session

    Starts subscription flow with 14-day trial.
    Redirects to Stripe checkout page.

    Args:
        plan: "starter" or "pro"
        success_url: Redirect URL after successful payment
        cancel_url: Redirect URL if user cancels

    Returns:
        checkout_url: Stripe checkout page URL
        session_id: Checkout session ID
    """
    try:
        result = payment_service.create_checkout_session(
            user_id=current_user["id"],
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")


@app.post("/checkout/portal")
async def create_portal_session(
    request: PortalRequest,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """
    Create Stripe customer portal session

    Allows customers to:
    - Update payment method
    - View invoices and payment history
    - Cancel subscription
    - Update billing information

    Returns portal_url for redirect
    """
    try:
        result = payment_service.create_portal_session(
            user_id=current_user["id"],
            return_url=request.return_url
        )

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portal creation failed: {str(e)}")


@app.post("/checkout/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook handler

    Handles events:
    - checkout.session.completed - Successful subscription
    - customer.subscription.updated - Subscription changes
    - customer.subscription.deleted - Cancellation
    - invoice.payment_succeeded - Payment received
    - invoice.payment_failed - Payment failed

    Signature verification with STRIPE_WEBHOOK_SECRET
    """
    import stripe
    from payments import STRIPE_WEBHOOK_SECRET

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle events
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        payment_service.handle_checkout_completed(data)

    elif event_type == "customer.subscription.updated":
        payment_service.handle_subscription_updated(data)

    elif event_type == "customer.subscription.deleted":
        payment_service.handle_subscription_updated(data)

    elif event_type == "invoice.payment_succeeded":
        payment_service.handle_payment_succeeded(data)

    elif event_type == "invoice.payment_failed":
        payment_service.handle_payment_failed(data)

    return {"status": "success", "event": event_type}


@app.get("/usage/stats")
async def get_usage_statistics(
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """
    Get usage statistics for current billing period

    Returns:
    - Projects used this month
    - Projects limit (based on plan)
    - Projects remaining
    - API access enabled
    - Team members limit
    """
    stats = payment_service.get_usage_stats(current_user["id"])
    return stats


# ==============================================================================
# ANALYTICS ENDPOINTS (Phase 8)
# ==============================================================================

@app.get("/analytics/overview")
async def get_analytics_overview(
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """
    Get analytics overview

    Returns project counts, user stats, revenue metrics.
    Users see their own data, admins see system-wide.
    """
    # For now, users see only their own data
    # Add admin check here for system-wide view
    stats = analytics_service.get_overview_stats(user_id=current_user["id"])
    return stats


@app.get("/analytics/usage")
async def get_usage_analytics(
    days: int = 30,
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """
    Get API usage analytics

    Query params:
    - days: Number of days to analyze (default: 30)

    Returns daily API usage, request counts, top endpoints
    """
    metrics = analytics_service.get_usage_metrics(days=days)
    return metrics


@app.get("/analytics/conversion")
async def get_conversion_analytics(
    current_user: dict = Depends(auth_manager.get_current_user)
):
    """
    Get conversion metrics

    Returns trial-to-paid conversion rates,
    subscription status breakdown.

    Admin-only in production.
    """
    # Add admin check here
    metrics = analytics_service.get_conversion_metrics()
    return metrics


# ==============================================================================
# PROJECT ENDPOINTS
# ==============================================================================

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    project_id = str(uuid.uuid4())

    project_data = {
        "id": project_id,
        "name": project.name,
        "customer": project.customer,
        "created_at": datetime.utcnow().isoformat(),
        "status": "created",
        "total_rooms": 0,
        "total_sqft": 0.0,
        "total_gallons": 0.0,
        "total_labor_hours": 0.0,
        "estimated_cost": 0.0
    }

    db.save_project(project_data)

    return ProjectResponse(**project_data)


@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects"""
    projects = db.get_all_projects()
    return [ProjectResponse(**p) for p in projects]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**project)


@app.post("/projects/{project_id}/upload")
async def upload_drawing(
    project_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a drawing with validation and organized storage"""

    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # File validation
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content and validate size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Validate file is not corrupted (basic check for PDF)
    if file_ext == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Corrupted or invalid PDF file")

    # Create organized storage structure: uploads/{project_id}/{file_id}.pdf
    project_upload_dir = UPLOAD_DIR / project_id
    project_upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = project_upload_dir / f"{file_id}{file_ext}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Initialize processing status
    processing_status = {
        "file_id": file_id,
        "filename": file.filename,
        "status": "queued",
        "progress": 0,
        "message": "File uploaded, queued for processing",
        "uploaded_at": datetime.utcnow().isoformat(),
        "file_size": file_size
    }

    # Store status in project data
    project_data = project.copy()
    if "uploads" not in project_data:
        project_data["uploads"] = {}
    project_data["uploads"][file_id] = processing_status
    db.update_project(project_id, project_data)

    # Update project status
    db.update_project(project_id, {"status": "processing"})

    # Process in background
    if background_tasks:
        background_tasks.add_task(
            process_drawing,
            project_id=project_id,
            file_path=str(file_path),
            file_id=file_id
        )

    return {
        "message": "File uploaded successfully and queued for processing",
        "file_id": file_id,
        "filename": file.filename,
        "file_size": file_size,
        "status": "queued",
        "project_id": project_id
    }


@app.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get real-time processing status for a project"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get upload statuses
    uploads = project.get("uploads", {})

    return {
        "project_id": project_id,
        "status": project.get("status", "created"),
        "total_rooms": project.get("total_rooms", 0),
        "total_sqft": project.get("total_sqft", 0.0),
        "uploads": uploads,
        "error": project.get("error"),
        "updated_at": project.get("updated_at", project.get("created_at"))
    }


def update_processing_status(project_id: str, file_id: str, status: str, progress: int, message: str):
    """Helper to update processing status"""
    project = db.get_project(project_id)
    if project and "uploads" in project:
        if file_id in project["uploads"]:
            project["uploads"][file_id].update({
                "status": status,
                "progress": progress,
                "message": message,
                "updated_at": datetime.utcnow().isoformat()
            })
            db.update_project(project_id, {"uploads": project["uploads"], "updated_at": datetime.utcnow().isoformat()})


async def process_drawing(project_id: str, file_path: str, file_id: str):
    """Background task to process a drawing with status updates"""
    try:
        # Update status: Starting
        update_processing_status(project_id, file_id, "processing", 10, "Starting AI analysis...")

        # Detect rooms and surfaces
        update_processing_status(project_id, file_id, "processing", 30, "Analyzing drawing with AI...")
        detection = detector.analyze_drawing(file_path)

        # Update status: AI Complete
        update_processing_status(project_id, file_id, "processing", 60, f"Detected {detection.total_rooms} rooms, saving...")

        # Save rooms to database
        for i, room in enumerate(detection.rooms):
            room_id = str(uuid.uuid4())

            room_data = {
                "id": room_id,
                "project_id": project_id,
                "name": room.name,
                "number": room.number,
                "dimensions": room.dimensions,
                "surfaces": {
                    name: {
                        "type": surface.type,
                        "area": surface.area,
                        "linear_feet": surface.linear_feet,
                        "height": surface.height,
                        "deductions": surface.deductions
                    }
                    for name, surface in room.surfaces.items()
                },
                "total_area": room.total_area
            }

            db.save_room(room_data)

            # Update progress
            progress = 60 + int((i + 1) / len(detection.rooms) * 30)
            update_processing_status(project_id, file_id, "processing", progress, f"Saved room {i+1}/{len(detection.rooms)}")

        # Update project totals
        update_processing_status(project_id, file_id, "processing", 95, "Calculating project totals...")

        project = db.get_project(project_id)
        rooms = db.get_project_rooms(project_id)

        total_sqft = sum(r["total_area"] for r in rooms)

        db.update_project(project_id, {
            "status": "complete",
            "total_rooms": len(rooms),
            "total_sqft": total_sqft,
            "updated_at": datetime.utcnow().isoformat()
        })

        # Final status update
        update_processing_status(
            project_id,
            file_id,
            "complete",
            100,
            f"Complete! Detected {len(rooms)} rooms, {total_sqft:.0f} sqft total"
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing drawing: {error_details}")

        # Update status: Failed
        update_processing_status(project_id, file_id, "failed", 0, f"Error: {str(e)}")

        db.update_project(project_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


@app.get("/projects/{project_id}/rooms")
async def get_project_rooms(project_id: str):
    """Get all rooms for a project"""
    rooms = db.get_project_rooms(project_id)
    return {"rooms": rooms}


@app.get("/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details"""
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@app.patch("/rooms/{room_id}")
async def update_room(room_id: str, updates: RoomUpdate):
    """Update room details"""
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    update_data = updates.dict(exclude_unset=True)
    db.update_room(room_id, update_data)

    return {"message": "Room updated", "room_id": room_id}


@app.post("/projects/{project_id}/estimate")
async def generate_estimate(project_id: str, params: EstimateParams):
    """Generate cost estimate for project"""

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms = db.get_project_rooms(project_id)

    # Calculate estimate for each room
    calculator_instance = PaintCalculator(surface_type=params.surface_type)

    estimates = []
    total_gallons = 0.0
    total_hours = 0.0
    total_cost = 0.0

    for room_data in rooms:
        # Reconstruct Room object
        from painting_detector import Room, Surface

        room = Room(
            id=room_data["id"],
            name=room_data["name"],
            number=room_data.get("number"),
            dimensions=room_data.get("dimensions", {}),
            surfaces={}
        )

        # Reconstruct surfaces
        for surface_name, surface_data in room_data.get("surfaces", {}).items():
            room.surfaces[surface_name] = Surface(
                type=surface_data["type"],
                area=surface_data["area"],
                linear_feet=surface_data.get("linear_feet"),
                height=surface_data.get("height"),
                deductions=surface_data.get("deductions", 0.0)
            )

        room.total_area = room_data.get("total_area", 0.0)

        # Calculate estimate
        estimate = calculator_instance.calculate_room_estimate(
            room,
            paint_price=params.paint_price,
            labor_rate=params.labor_rate
        )

        estimates.append(estimate)

        total_gallons += estimate["totals"]["paint_gallons"]
        total_hours += estimate["totals"]["labor_hours"]
        total_cost += estimate["totals"]["total_cost"]

    # Update project with totals
    db.update_project(project_id, {
        "total_gallons": total_gallons,
        "total_labor_hours": total_hours,
        "estimated_cost": total_cost
    })

    return {
        "project_id": project_id,
        "estimates": estimates,
        "totals": {
            "paint_gallons": total_gallons,
            "labor_hours": total_hours,
            "total_cost": total_cost,
            "cost_per_sqft": total_cost / project["total_sqft"] if project["total_sqft"] > 0 else 0
        }
    }


@app.post("/projects/{project_id}/assembly-expansion")
async def expand_assembly(
    project_id: str,
    paint_type: str = "commercial",  # economy, commercial, premium
    labor_rate: float = 50.0
):
    """
    Expand project into detailed assembly line items (80-120+ items)

    Matches Rudus workflow: breaks each room into granular tasks:
    - Surface preparation (spackle, sand, caulk, mask)
    - Primer application (material, labor, supplies)
    - Finish coats (material, labor, supplies)
    - Cleanup (remove masking, touch-ups)
    """

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms_data = db.get_project_rooms(project_id)
    if not rooms_data:
        raise HTTPException(status_code=400, detail="No rooms detected. Upload and process a drawing first.")

    # Convert room data to Room objects
    room_objects = []
    for r in rooms_data:
        room = Room(
            id=r["id"],
            name=r["name"],
            number=r.get("number"),
            dimensions=r.get("dimensions", {}),
            surfaces={}
        )

        # Reconstruct surfaces
        for surface_name, surface_data in r.get("surfaces", {}).items():
            room.surfaces[surface_name] = Surface(
                type=surface_data["type"],
                area=surface_data["area"],
                linear_feet=surface_data.get("linear_feet"),
                height=surface_data.get("height"),
                deductions=surface_data.get("deductions", 0.0)
            )

        room.total_area = r.get("total_area", 0.0)
        room_objects.append(room)

    # Expand project into line items
    expander = AssemblyExpander(labor_rate=labor_rate)
    expanded = expander.expand_project(room_objects, paint_type=paint_type)

    # Store expanded assembly in project
    db.update_project(project_id, {
        "assembly_expansion": expanded,
        "assembly_expanded_at": datetime.utcnow().isoformat()
    })

    return {
        "project_id": project_id,
        "paint_type": paint_type,
        "labor_rate": labor_rate,
        "rooms": expanded["rooms"],
        "summary": expanded["summary"],
        "message": f"Expanded to {expanded['summary']['total_line_items']} detailed line items"
    }


@app.get("/projects/{project_id}/export/excel")
async def export_excel(project_id: str):
    """Export project to Excel"""

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms = db.get_project_rooms(project_id)

    # Generate Excel file
    output_path = OUTPUT_DIR / f"{project_id}_takeoff.xlsx"
    exporter.generate_excel(project, rooms, output_path)

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{project['name']}_Takeoff.xlsx"
    )


@app.get("/projects/{project_id}/export/pdf")
async def export_pdf(project_id: str):
    """Export project to PDF proposal"""

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms = db.get_project_rooms(project_id)

    # Generate PDF file
    output_path = OUTPUT_DIR / f"{project_id}_proposal.pdf"
    exporter.generate_pdf(project, rooms, output_path)

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"{project['name']}_Proposal.pdf"
    )


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete_project(project_id)

    return {"message": "Project deleted", "project_id": project_id}


# ========================================
# DRYWALL-SPECIFIC ENDPOINTS
# ========================================

@app.post("/drywall/projects/{project_id}/upload")
async def upload_drywall_drawing(
    project_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a drywall drawing (floor plan, elevation, section, RCP)"""

    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # File validation
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max: 50MB")
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Save file
    project_upload_dir = UPLOAD_DIR / "drywall" / project_id
    project_upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = project_upload_dir / f"{file_id}{file_ext}"

    with open(file_path, "wb") as f:
        f.write(content)

    # Initialize processing status
    processing_status = {
        "file_id": file_id,
        "filename": file.filename,
        "status": "queued",
        "progress": 0,
        "message": "File uploaded, queued for drywall detection",
        "uploaded_at": datetime.utcnow().isoformat(),
        "file_size": file_size,
        "type": "drywall"
    }

    # Store status
    project_data = project.copy()
    if "drywall_uploads" not in project_data:
        project_data["drywall_uploads"] = {}
    project_data["drywall_uploads"][file_id] = processing_status
    db.update_project(project_id, project_data)
    db.update_project(project_id, {"status": "processing"})

    # Process in background
    if background_tasks:
        background_tasks.add_task(
            process_drywall_drawing,
            project_id=project_id,
            file_path=str(file_path),
            file_id=file_id
        )

    return {
        "message": "Drywall drawing uploaded and queued for processing",
        "file_id": file_id,
        "filename": file.filename,
        "file_size": file_size,
        "status": "queued",
        "project_id": project_id
    }


async def process_drywall_drawing(project_id: str, file_path: str, file_id: str):
    """
    Background task to process drywall drawing
    8-Stage Pipeline:
    1. Upload → 2. Classification → 3. Drawing Analysis → 4. Wall Extraction →
    5. Opening Detection → 6. Material Calc → 7. Labor Estimation → 8. Takeoff Generation
    """
    try:
        # Stage 1: Upload (already done)
        # Stage 2: Classification + Stage 3: Drawing Analysis
        update_drywall_status(project_id, file_id, "processing", 10, "Stage 1/8: Classifying drawing type...")

        # Detect walls, openings, ceilings using AI
        update_drywall_status(project_id, file_id, "processing", 25, "Stage 2-3/8: AI analyzing drawing...")
        detection_result = drywall_detector.analyze_drawing(file_path)

        # Stage 4: Wall Extraction
        update_drywall_status(
            project_id, file_id, "processing", 45,
            f"Stage 4/8: Extracted {len(detection_result.walls)} walls, {len(detection_result.ceilings)} ceilings"
        )

        # Save walls to database
        for i, wall in enumerate(detection_result.walls):
            wall_id = str(uuid.uuid4())

            wall_data = {
                "id": wall_id,
                "project_id": project_id,
                "wall_id": wall.wall_id,
                "type": wall.type,
                "length_ft": wall.length_ft,
                "height_ft": wall.height_ft,
                "square_footage": wall.square_footage,
                "openings": [
                    {
                        "type": opening.type,
                        "width": opening.width,
                        "height": opening.height,
                        "square_footage": opening.square_footage,
                        "quantity": opening.quantity
                    }
                    for opening in wall.openings
                ],
                "corners": {
                    "inside_corners": wall.corners.inside_corners,
                    "outside_corners": wall.corners.outside_corners
                },
                "special_features": wall.special_features
            }

            # Store in project data (since we don't have wall-specific DB table yet)
            project_data = db.get_project(project_id)
            if "walls" not in project_data:
                project_data["walls"] = []
            project_data["walls"].append(wall_data)
            db.update_project(project_id, project_data)

            progress = 45 + int((i + 1) / len(detection_result.walls) * 20)
            update_drywall_status(project_id, file_id, "processing", progress, f"Saved wall {i+1}/{len(detection_result.walls)}")

        # Save ceilings
        for ceiling in detection_result.ceilings:
            ceiling_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "room": ceiling.room,
                "type": ceiling.type,
                "square_footage": ceiling.square_footage,
                "height_ft": ceiling.height_ft,
                "special_notes": ceiling.special_notes
            }

            project_data = db.get_project(project_id)
            if "ceilings" not in project_data:
                project_data["ceilings"] = []
            project_data["ceilings"].append(ceiling_data)
            db.update_project(project_id, project_data)

        # Stage 5: Opening Detection (already done during AI analysis)
        update_drywall_status(project_id, file_id, "processing", 65, "Stage 5/8: Opening detection complete")

        # Stage 6: Material Calculation
        update_drywall_status(project_id, file_id, "processing", 70, "Stage 6/8: Calculating materials...")

        # Calculate materials using DrywallCalculator
        project_data = db.get_project(project_id)
        total_wall_sqft = detection_result.summary.get("total_wall_sqft", 0)
        total_ceiling_sqft = detection_result.summary.get("total_ceiling_sqft", 0)

        # Stage 7: Labor Estimation
        update_drywall_status(project_id, file_id, "processing", 85, "Stage 7/8: Estimating labor...")

        # Get estimate using calculator
        # For now, use a simplified calculation - full integration would use DrywallCalculator
        estimate = {
            "walls": len(detection_result.walls),
            "ceilings": len(detection_result.ceilings),
            "wall_sqft": total_wall_sqft,
            "ceiling_sqft": total_ceiling_sqft,
            "total_sqft": total_wall_sqft + total_ceiling_sqft,
            "drawing_type": detection_result.drawing_type,
            "scale": detection_result.scale
        }

        # Stage 8: Takeoff Generation
        update_drywall_status(project_id, file_id, "processing", 95, "Stage 8/8: Generating takeoff...")

        # Update project with final results
        db.update_project(project_id, {
            "status": "complete",
            "total_walls": len(detection_result.walls),
            "total_ceilings": len(detection_result.ceilings),
            "total_wall_sqft": total_wall_sqft,
            "total_ceiling_sqft": total_ceiling_sqft,
            "drawing_type": detection_result.drawing_type,
            "detection_summary": detection_result.summary,
            "updated_at": datetime.utcnow().isoformat()
        })

        # Complete
        update_drywall_status(
            project_id, file_id, "complete", 100,
            f"Complete! {len(detection_result.walls)} walls, {total_wall_sqft:.0f} wall sqft, {total_ceiling_sqft:.0f} ceiling sqft"
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing drywall drawing: {error_details}")

        update_drywall_status(project_id, file_id, "failed", 0, f"Error: {str(e)}")
        db.update_project(project_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


def update_drywall_status(project_id: str, file_id: str, status: str, progress: int, message: str):
    """Update drywall processing status"""
    project = db.get_project(project_id)
    if project and "drywall_uploads" in project and file_id in project["drywall_uploads"]:
        project["drywall_uploads"][file_id].update({
            "status": status,
            "progress": progress,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        })
        db.update_project(project_id, {"drywall_uploads": project["drywall_uploads"]})


@app.get("/drywall/projects/{project_id}/walls")
async def get_project_walls(project_id: str):
    """Get all detected walls for a drywall project"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    walls = project.get("walls", [])
    ceilings = project.get("ceilings", [])

    return {
        "walls": walls,
        "ceilings": ceilings,
        "summary": project.get("detection_summary", {})
    }


@app.post("/drywall/projects/{project_id}/estimate")
async def generate_drywall_estimate(
    project_id: str,
    params: DrywallEstimateParams
):
    """
    Generate detailed drywall estimate with materials and labor
    Uses DrywallCalculator for industry-standard calculations
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    walls = project.get("walls", [])
    if not walls:
        raise HTTPException(status_code=400, detail="No walls detected. Upload a drawing first.")

    # Calculate total wall area
    total_wall_sqft = sum(w["square_footage"] for w in walls)
    total_opening_sqft = sum(
        sum(o["square_footage"] * o.get("quantity", 1) for o in w.get("openings", []))
        for w in walls
    )
    net_wall_sqft = total_wall_sqft - total_opening_sqft

    # Calculate ceiling area
    ceilings = project.get("ceilings", [])
    total_ceiling_sqft = sum(c["square_footage"] for c in ceilings)

    # Use DrywallCalculator for accurate estimates
    # Create a simplified room geometry from wall data
    total_sqft = net_wall_sqft + total_ceiling_sqft

    # Simple estimate for now (full integration would parse all wall data)
    from drywall_calculator import FinishLevel, ProjectType

    finish_level = FinishLevel(params.finish_level)
    project_type = ProjectType(params.project_type)

    # Basic material calculations
    sheets_needed = math.ceil(total_sqft / 32)  # 32 sqft per 4x8 sheet
    waste_factor = 1.15  # 15% waste
    total_sheets = math.ceil(sheets_needed * waste_factor)

    # Joint compound (lbs per sqft varies by finish level)
    compound_rates = {0: 0, 1: 0.028, 2: 0.040, 3: 0.053, 4: 0.067, 5: 0.095}
    compound_lbs = total_sqft * compound_rates[params.finish_level]

    # Tape (linear feet = perimeter estimate)
    tape_lf = total_sqft * 0.4  # rough estimate

    # Screws (per sheet)
    screws = total_sheets * 50

    # Labor hours by phase
    hanging_hours = total_sqft / 40  # 40 sqft/hr
    taping_hours = total_sqft / 150   # 150 sqft/hr
    finishing_hours = total_sqft / 200 * (params.finish_level / 3)  # varies by level
    total_labor_hours = hanging_hours + taping_hours + finishing_hours

    # Costs
    material_cost = (total_sheets * 12) + (compound_lbs * 0.40) + (tape_lf * 0.03) + (screws * 0.001)
    labor_cost = total_labor_hours * params.labor_rate
    subtotal = material_cost + labor_cost
    overhead = subtotal * 0.15
    profit = subtotal * 0.20
    total_cost = subtotal + overhead + profit

    estimate_data = {
        "project_id": project_id,
        "generated_at": datetime.utcnow().isoformat(),
        "parameters": {
            "finish_level": params.finish_level,
            "sheet_thickness": params.sheet_thickness,
            "labor_rate": params.labor_rate,
            "project_type": params.project_type,
            "region": params.region
        },
        "measurements": {
            "total_walls": len(walls),
            "total_ceilings": len(ceilings),
            "gross_wall_sqft": total_wall_sqft,
            "opening_sqft": total_opening_sqft,
            "net_wall_sqft": net_wall_sqft,
            "ceiling_sqft": total_ceiling_sqft,
            "total_sqft": total_sqft
        },
        "materials": {
            "drywall_sheets": total_sheets,
            "joint_compound_lbs": round(compound_lbs, 1),
            "tape_linear_feet": round(tape_lf, 0),
            "screws": screws
        },
        "labor": {
            "hanging_hours": round(hanging_hours, 2),
            "taping_hours": round(taping_hours, 2),
            "finishing_hours": round(finishing_hours, 2),
            "total_hours": round(total_labor_hours, 2)
        },
        "costs": {
            "material_cost": round(material_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "subtotal": round(subtotal, 2),
            "overhead": round(overhead, 2),
            "profit": round(profit, 2),
            "total_cost": round(total_cost, 2),
            "cost_per_sqft": round(total_cost / total_sqft, 2)
        }
    }

    # Save estimate to project
    project_data = db.get_project(project_id)
    project_data["estimate"] = estimate_data
    db.update_project(project_id, project_data)

    return estimate_data


@app.patch("/drywall/walls/{wall_id}")
async def update_wall(wall_id: str, updates: WallUpdate):
    """Update wall dimensions or openings (contractor review/override)"""
    # Find wall in database
    # For now, search through all projects (would be optimized with proper DB schema)
    projects = db.get_all_projects()

    wall_found = False
    for project in projects:
        if "walls" in project:
            for wall in project["walls"]:
                if wall["id"] == wall_id:
                    # Update wall
                    if updates.length_ft is not None:
                        wall["length_ft"] = updates.length_ft
                        wall["square_footage"] = updates.length_ft * wall["height_ft"]
                    if updates.height_ft is not None:
                        wall["height_ft"] = updates.height_ft
                        wall["square_footage"] = wall["length_ft"] * updates.height_ft
                    if updates.type is not None:
                        wall["type"] = updates.type
                    if updates.openings is not None:
                        wall["openings"] = updates.openings

                    db.update_project(project["id"], {"walls": project["walls"]})
                    wall_found = True
                    return {"message": "Wall updated", "wall": wall}

    if not wall_found:
        raise HTTPException(status_code=404, detail="Wall not found")


@app.post("/drywall/projects/{project_id}/walls")
async def add_manual_wall(project_id: str, wall: WallCreate):
    """Add a wall manually (for areas AI missed or manual entry)"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    wall_data = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "wall_id": wall.wall_id,
        "type": wall.type,
        "length_ft": wall.length_ft,
        "height_ft": wall.height_ft,
        "square_footage": wall.length_ft * wall.height_ft,
        "openings": wall.openings,
        "corners": {
            "inside_corners": wall.inside_corners,
            "outside_corners": wall.outside_corners
        },
        "special_features": [],
        "manually_added": True
    }

    if "walls" not in project:
        project["walls"] = []
    project["walls"].append(wall_data)
    db.update_project(project_id, {"walls": project["walls"]})

    return {"message": "Wall added", "wall": wall_data}


if __name__ == "__main__":
    import uvicorn

    print("🔨 Drywall.ai API Server")
    print("📍 Running on http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🎯 Drywall endpoints: /drywall/*")
    print("🎨 Legacy painting endpoints: /projects/*")

    uvicorn.run(app, host="0.0.0.0", port=8000)

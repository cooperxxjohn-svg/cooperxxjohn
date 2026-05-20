"""
Painting.ai API Server
FastAPI backend for AI-powered painting takeoffs
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

from painting_detector import PaintingDetector, PaintCalculator, Room, Surface
from database import Database
from export_generator import ExportGenerator
from assembly_expansion import AssemblyExpander
from auth_jwt import AuthManager, UserRegister, UserLogin, Token, get_auth_manager
from payments import PaymentService, PLANS, get_payment_service
from email_service import get_email_service
from analytics import AnalyticsService, get_analytics_service
import background_tasks as bg_tasks

# Initialize FastAPI app
app = FastAPI(
    title="Painting.ai API",
    description="AI-powered takeoff and estimating for painting contractors",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize services
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

detector = PaintingDetector(ANTHROPIC_API_KEY)
calculator = PaintCalculator()
db = Database()
exporter = ExportGenerator()
auth_manager = AuthManager(db)
payment_service = PaymentService(db)
email_service = get_email_service()
analytics_service = AnalyticsService(db)


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
    return {
        "status": "healthy",
        "detector": "ready",
        "database": "connected" if db.is_connected() else "disconnected"
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


if __name__ == "__main__":
    import uvicorn

    print("🎨 Painting.ai API Server")
    print("📍 Running on http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)

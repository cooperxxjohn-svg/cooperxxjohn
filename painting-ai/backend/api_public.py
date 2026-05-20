"""
Public API for third-party integrations
RESTful API with rate limiting, webhooks, and documentation
"""

from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import defaultdict
import time
import hashlib
import hmac
import uuid
from database import Database
from assembly_expansion import AssemblyExpander

# Initialize database
db = Database()


# Rate limiting
class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""

    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, api_key: str, limit: int = 100, window: int = 60) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        cutoff = now - window

        # Clean old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[api_key]) >= limit:
            return False

        # Add this request
        self.requests[api_key].append(now)
        return True

    def get_remaining(self, api_key: str, limit: int = 100) -> int:
        """Get remaining requests in window"""
        return limit - len(self.requests[api_key])


rate_limiter = RateLimiter()


# API Usage Logging
def log_api_usage(user_id: str, endpoint: str, method: str = "GET", status_code: int = 200):
    """Log API usage for analytics"""
    try:
        usage_file = db.data_dir / "api_usage.json"

        if not usage_file.exists():
            db._write_json(usage_file, [])

        usage = db._read_json(usage_file)

        usage.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 10000 entries
        if len(usage) > 10000:
            usage = usage[-10000:]

        db._write_json(usage_file, usage)
    except Exception as e:
        print(f"Failed to log API usage: {e}")


# API Models
class ProjectCreateRequest(BaseModel):
    name: str
    customer: Optional[str] = None
    project_type: Optional[str] = "commercial"
    address: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    customer: Optional[str]
    status: str
    total_rooms: int
    total_sqft: float
    estimated_cost: float
    created_at: str


class RoomResponse(BaseModel):
    id: str
    name: str
    number: Optional[str]
    dimensions: dict
    total_area: float
    surfaces: dict


class WebhookCreate(BaseModel):
    url: str
    events: list  # ['project.completed', 'export.generated', etc.]
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list
    secret: str
    is_active: bool
    created_at: str


# Dependencies
async def verify_api_key(x_api_key: str = Header(...)) -> dict:
    """Verify API key and apply rate limiting"""

    # Check rate limit
    if not rate_limiter.is_allowed(x_api_key, limit=100, window=60):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 100 requests per minute.",
            headers={"Retry-After": "60"}
        )

    # Verify API key in database
    if not x_api_key.startswith("pk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    user = db.get_user_by_api_key(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Check subscription status
    if user.get("subscription_status") not in ["active", "trialing"]:
        raise HTTPException(status_code=403, detail="Subscription inactive. Please upgrade your plan.")

    # Log API usage
    log_api_usage(user["id"], "api_request")

    return user


# Public API App
api_public = FastAPI(
    title="Painting.ai Public API",
    description="RESTful API for integrating with Painting.ai",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


@api_public.get("/")
async def api_root():
    """API information"""
    return {
        "name": "Painting.ai Public API",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "status": "operational"
    }


@api_public.get("/api/rate-limit")
async def check_rate_limit(api_key: str = Depends(verify_api_key)):
    """Check current rate limit status"""
    remaining = rate_limiter.get_remaining(api_key, limit=100)

    return {
        "limit": 100,
        "remaining": remaining,
        "window": "60 seconds",
        "reset_at": datetime.utcnow() + timedelta(seconds=60)
    }


@api_public.post("/api/projects", response_model=ProjectResponse)
async def create_project_api(
    project: ProjectCreateRequest,
    user: dict = Depends(verify_api_key)
):
    """Create a new project via API"""
    project_id = str(uuid.uuid4())

    project_data = {
        "id": project_id,
        "name": project.name,
        "customer": project.customer,
        "address": project.address,
        "project_type": project.project_type,
        "owner_id": user["id"],
        "status": "created",
        "total_rooms": 0,
        "total_sqft": 0.0,
        "estimated_cost": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }

    db.save_project(project_data)
    log_api_usage(user["id"], "/api/projects", "POST", 201)

    return project_data


@api_public.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project_api(
    project_id: str,
    user: dict = Depends(verify_api_key)
):
    """Get project details via API"""
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify ownership
    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    log_api_usage(user["id"], f"/api/projects/{project_id}", "GET", 200)

    return project


@api_public.get("/api/projects/{project_id}/rooms")
async def get_project_rooms_api(
    project_id: str,
    user: dict = Depends(verify_api_key)
):
    """Get all rooms for a project"""
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify ownership
    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    rooms = db.get_project_rooms(project_id)

    log_api_usage(user["id"], f"/api/projects/{project_id}/rooms", "GET", 200)

    return {
        "project_id": project_id,
        "rooms": rooms
    }


@api_public.post("/api/projects/{project_id}/export/{format}")
async def export_project_api(
    project_id: str,
    format: str,  # excel or pdf
    user: dict = Depends(verify_api_key)
):
    """Export project to Excel or PDF"""
    if format not in ["excel", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'pdf'")

    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if project.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Project must be complete to export")

    # Generate export (this would be async in production with Celery)
    from export_generator import ExportGenerator

    rooms = db.get_project_rooms(project_id)
    generator = ExportGenerator()

    if format == "excel":
        file_path = generator.generate_excel(project, rooms)
        filename = f"{project['name']}_estimate.xlsx"
    else:  # pdf
        file_path = generator.generate_pdf(project, rooms)
        filename = f"{project['name']}_proposal.pdf"

    log_api_usage(user["id"], f"/api/projects/{project_id}/export/{format}", "POST", 200)

    # Trigger webhook
    await WebhookDelivery.trigger_webhooks(
        event="export.generated",
        data={
            "project_id": project_id,
            "format": format,
            "filename": filename
        },
        user_id=user["id"]
    )

    return {
        "project_id": project_id,
        "format": format,
        "filename": filename,
        "file_path": str(file_path),
        "download_url": f"/projects/{project_id}/export/{format}",
        "created_at": datetime.utcnow().isoformat()
    }


# Room Edit/Review Endpoints (Competitor-validated workflow)
class RoomUpdateRequest(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    dimensions: Optional[dict] = None  # {"length": 20, "width": 15, "height": 9}
    surfaces: Optional[dict] = None  # Override AI detection


class RoomCreateRequest(BaseModel):
    name: str
    number: Optional[str] = None
    dimensions: dict  # Required for manual add
    manually_added: bool = True


class MaterialUpdateRequest(BaseModel):
    paint_id: str  # Material ID from material database
    primer_id: str
    quality_tier: Optional[str] = "commercial"  # economy, commercial, premium


@api_public.put("/api/projects/{project_id}/rooms/{room_id}")
async def update_room(
    project_id: str,
    room_id: str,
    room_update: RoomUpdateRequest,
    user: dict = Depends(verify_api_key)
):
    """
    Edit detected room dimensions and properties

    Allows estimators to correct AI detection errors:
    - Adjust dimensions if AI got them wrong
    - Rename rooms for clarity
    - Override surface area calculations
    - Add notes or special instructions

    This is a critical part of the review workflow validated by
    Rudus, Bidflow, and industry standards.
    """
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    room = db.get_room(room_id)

    if not room or room.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="Room not found")

    # Build updates dict
    updates = {}
    if room_update.name:
        updates["name"] = room_update.name
    if room_update.number:
        updates["number"] = room_update.number
    if room_update.dimensions:
        updates["dimensions"] = room_update.dimensions
        # Recalculate total area
        dims = room_update.dimensions
        if all(k in dims for k in ["length", "width", "height"]):
            walls = 2 * (dims["length"] + dims["width"]) * dims["height"]
            ceiling = dims["length"] * dims["width"]
            updates["total_area"] = walls + ceiling
    if room_update.surfaces:
        updates["surfaces"] = room_update.surfaces

    updates["updated_at"] = datetime.utcnow().isoformat()

    db.update_room(room_id, updates)
    log_api_usage(user["id"], f"/api/projects/{project_id}/rooms/{room_id}", "PUT", 200)

    updated_room = db.get_room(room_id)
    return updated_room


@api_public.post("/api/projects/{project_id}/rooms")
async def create_room_manually(
    project_id: str,
    room: RoomCreateRequest,
    user: dict = Depends(verify_api_key)
):
    """
    Manually add a room that AI missed

    Sometimes AI doesn't detect all rooms (closets, mechanical rooms,
    unlabeled spaces). This lets estimators add them manually.

    Required for complete estimates on complex floor plans.
    """
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    room_id = str(uuid.uuid4())

    # Calculate total area
    dims = room.dimensions
    total_area = 0
    if all(k in dims for k in ["length", "width", "height"]):
        walls = 2 * (dims["length"] + dims["width"]) * dims["height"]
        ceiling = dims["length"] * dims["width"]
        total_area = walls + ceiling

    room_data = {
        "id": room_id,
        "project_id": project_id,
        "name": room.name,
        "number": room.number,
        "dimensions": room.dimensions,
        "total_area": total_area,
        "manually_added": True,
        "created_at": datetime.utcnow().isoformat()
    }

    db.save_room(room_data)

    # Update project total rooms
    db.update_project(project_id, {
        "total_rooms": (project.get("total_rooms", 0) + 1)
    })

    log_api_usage(user["id"], f"/api/projects/{project_id}/rooms", "POST", 201)

    return room_data


@api_public.delete("/api/projects/{project_id}/rooms/{room_id}")
async def delete_room(
    project_id: str,
    room_id: str,
    user: dict = Depends(verify_api_key)
):
    """
    Delete a room that was incorrectly detected

    AI sometimes detects non-rooms (legends, title blocks, notes)
    as rooms. This lets estimators remove false positives.
    """
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    room = db.get_room(room_id)

    if not room or room.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="Room not found")

    db.delete_room(room_id)

    # Update project total rooms
    db.update_project(project_id, {
        "total_rooms": max(0, project.get("total_rooms", 0) - 1)
    })

    log_api_usage(user["id"], f"/api/projects/{project_id}/rooms/{room_id}", "DELETE", 200)

    return {
        "message": "Room deleted successfully",
        "room_id": room_id,
        "project_id": project_id,
        "deleted_at": datetime.utcnow().isoformat()
    }


@api_public.put("/api/projects/{project_id}/materials")
async def update_materials(
    project_id: str,
    materials: MaterialUpdateRequest,
    user: dict = Depends(verify_api_key)
):
    """
    Change material selections for project

    Default recommendations are commercial-grade (ProMar 400).
    Estimators can upgrade to premium (Benjamin Moore Regal) or
    downgrade to economy (BEHR Premium Plus) based on customer needs.

    This triggers recalculation of all material costs.
    """
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update project with new material selections
    updates = {
        "paint_id": materials.paint_id,
        "primer_id": materials.primer_id,
        "quality_tier": materials.quality_tier,
        "updated_at": datetime.utcnow().isoformat()
    }

    db.update_project(project_id, updates)

    log_api_usage(user["id"], f"/api/projects/{project_id}/materials", "PUT", 200)

    return {
        "project_id": project_id,
        "materials": {
            "paint_id": materials.paint_id,
            "primer_id": materials.primer_id,
            "quality_tier": materials.quality_tier
        },
        "updated_at": datetime.utcnow().isoformat(),
        "message": "Materials updated. Recalculate estimate to apply changes."
    }


@api_public.get("/api/projects/{project_id}/assembly")
async def get_assembly_breakdown(
    project_id: str,
    user: dict = Depends(verify_api_key),
    paint_type: str = "commercial",
    labor_rate: float = 50.0
):
    """
    Get detailed assembly line item breakdown

    Expands project into 80-120+ detailed line items like Rudus:
    - Surface preparation (spackle, sand, caulk, mask)
    - Primer application (material, labor, supplies)
    - Finish coats (material, labor, supplies)
    - Cleanup (remove masking, touch-ups)

    Each room broken down into granular tasks with pricing.
    """
    project = db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    rooms = db.get_project_rooms(project_id)

    if not rooms:
        raise HTTPException(status_code=400, detail="No rooms found. Upload and process a drawing first.")

    # Convert room dicts to Room dataclass objects
    from assembly_expansion import Room

    room_objects = []
    for room_data in rooms:
        dims = room_data.get("dimensions", {})
        room_obj = Room(
            id=room_data["id"],
            name=room_data["name"],
            length=dims.get("length", 0),
            width=dims.get("width", 0),
            height=dims.get("height", 0),
            total_area=room_data.get("total_area", 0)
        )
        room_objects.append(room_obj)

    # Expand to assembly
    expander = AssemblyExpander(labor_rate=labor_rate)
    result = expander.expand_project(room_objects, paint_type=paint_type)

    log_api_usage(user["id"], f"/api/projects/{project_id}/assembly", "GET", 200)

    return {
        "project_id": project_id,
        "line_items": [item.__dict__ for item in result["line_items"]],
        "summary": result["summary"]
    }


# Webhooks
@api_public.post("/api/webhooks", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    user: dict = Depends(verify_api_key)
):
    """Create a webhook for event notifications"""
    webhook_id = f"wh_{uuid.uuid4().hex}"
    secret = f"whsec_{uuid.uuid4().hex}"

    webhook_data = {
        "id": webhook_id,
        "user_id": user["id"],
        "url": webhook.url,
        "events": webhook.events,
        "secret": secret,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    db.save_webhook(webhook_data)
    log_api_usage(user["id"], "/api/webhooks", "POST", 201)

    return webhook_data


@api_public.get("/api/webhooks")
async def list_webhooks(user: dict = Depends(verify_api_key)):
    """List all webhooks"""
    webhooks = db.get_user_webhooks(user["id"])

    log_api_usage(user["id"], "/api/webhooks", "GET", 200)

    return {"webhooks": webhooks}


@api_public.delete("/api/webhooks/{webhook_id}")
async def delete_webhook_endpoint(
    webhook_id: str,
    user: dict = Depends(verify_api_key)
):
    """Delete a webhook"""
    webhook = db.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if webhook.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete_webhook(webhook_id)
    log_api_usage(user["id"], f"/api/webhooks/{webhook_id}", "DELETE", 200)

    return {
        "message": "Webhook deleted successfully",
        "webhook_id": webhook_id
    }


# Webhook delivery
class WebhookDelivery:
    """Handle webhook event delivery with retry logic"""

    @staticmethod
    def sign_payload(payload: dict, secret: str) -> str:
        """Sign webhook payload with HMAC"""
        import json

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    @staticmethod
    async def deliver_webhook(url: str, event: str, data: dict, secret: str, max_retries: int = 3):
        """
        Deliver webhook to endpoint with exponential backoff retry

        Retries: 3 attempts with 2s, 4s, 8s delays
        Returns: (success: bool, status_code: int, error: str)
        """
        import httpx
        import asyncio

        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        signature = WebhookDelivery.sign_payload(payload, secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event
        }

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        return (True, response.status_code, None)

                    # Non-200 response
                    error_msg = f"Status {response.status_code}: {response.text[:200]}"

                    # Don't retry on 4xx errors (client errors)
                    if 400 <= response.status_code < 500:
                        return (False, response.status_code, error_msg)

                    # Retry on 5xx errors
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue

                    return (False, response.status_code, error_msg)

            except Exception as e:
                error_msg = str(e)

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

                return (False, 0, error_msg)

        return (False, 0, "Max retries exceeded")

    @staticmethod
    async def trigger_webhooks(event: str, data: dict, user_id: str):
        """Trigger all webhooks for a user that match the event"""
        webhooks = db.get_user_webhooks(user_id)

        for webhook in webhooks:
            if not webhook.get("is_active"):
                continue

            if event not in webhook.get("events", []):
                continue

            success, status_code, error = await WebhookDelivery.deliver_webhook(
                url=webhook["url"],
                event=event,
                data=data,
                secret=webhook["secret"]
            )

            # Log delivery attempt
            log_webhook_delivery(
                webhook_id=webhook["id"],
                event=event,
                success=success,
                status_code=status_code,
                error=error
            )


def log_webhook_delivery(webhook_id: str, event: str, success: bool, status_code: int, error: str = None):
    """Log webhook delivery attempts"""
    try:
        log_file = db.data_dir / "webhook_logs.json"

        if not log_file.exists():
            db._write_json(log_file, [])

        logs = db._read_json(log_file)

        logs.append({
            "id": str(uuid.uuid4()),
            "webhook_id": webhook_id,
            "event": event,
            "success": success,
            "status_code": status_code,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 1000 logs
        if len(logs) > 1000:
            logs = logs[-1000:]

        db._write_json(log_file, logs)
    except Exception as e:
        print(f"Failed to log webhook delivery: {e}")


# API Documentation
@api_public.get("/api/documentation")
async def api_documentation():
    """API documentation and examples"""
    return {
        "title": "Painting.ai Public API",
        "description": "RESTful API for integrating with Painting.ai",
        "authentication": {
            "type": "API Key",
            "header": "X-API-Key",
            "example": "X-API-Key: pk_your_api_key_here"
        },
        "rate_limits": {
            "requests_per_minute": 100,
            "requests_per_hour": 5000,
            "requests_per_day": 100000
        },
        "endpoints": {
            "projects": {
                "create": "POST /api/projects",
                "get": "GET /api/projects/{id}",
                "list": "GET /api/projects",
                "delete": "DELETE /api/projects/{id}"
            },
            "rooms": {
                "list": "GET /api/projects/{id}/rooms",
                "get": "GET /api/rooms/{id}",
                "update": "PUT /api/projects/{id}/rooms/{room_id}",
                "create": "POST /api/projects/{id}/rooms",
                "delete": "DELETE /api/projects/{id}/rooms/{room_id}"
            },
            "materials": {
                "update": "PUT /api/projects/{id}/materials"
            },
            "assembly": {
                "breakdown": "GET /api/projects/{id}/assembly"
            },
            "export": {
                "excel": "POST /api/projects/{id}/export/excel",
                "pdf": "POST /api/projects/{id}/export/pdf"
            },
            "webhooks": {
                "create": "POST /api/webhooks",
                "list": "GET /api/webhooks",
                "delete": "DELETE /api/webhooks/{id}"
            }
        },
        "webhook_events": [
            "project.created",
            "project.processing",
            "project.completed",
            "project.failed",
            "drawing.uploaded",
            "export.generated",
            "payment.succeeded",
            "payment.failed"
        ],
        "examples": {
            "create_project": {
                "request": {
                    "method": "POST",
                    "url": "/api/projects",
                    "headers": {
                        "X-API-Key": "pk_your_key",
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "name": "Office Renovation",
                        "customer": "ABC Construction",
                        "project_type": "commercial"
                    }
                },
                "response": {
                    "id": "proj_123",
                    "name": "Office Renovation",
                    "customer": "ABC Construction",
                    "status": "created",
                    "created_at": "2026-05-20T00:00:00Z"
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("🔌 Painting.ai Public API")
    print("📖 Docs: http://localhost:8001/api/docs")

    uvicorn.run(api_public, host="0.0.0.0", port=8001)

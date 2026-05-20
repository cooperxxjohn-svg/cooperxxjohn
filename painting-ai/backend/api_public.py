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
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key and apply rate limiting"""

    # Check rate limit
    if not rate_limiter.is_allowed(x_api_key, limit=100, window=60):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 100 requests per minute.",
            headers={"Retry-After": "60"}
        )

    # Verify API key (would check database in production)
    if not x_api_key.startswith("pk_"):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


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
    api_key: str = Depends(verify_api_key)
):
    """Create a new project via API"""
    # In production, would use database service
    return {
        "id": "proj_123",
        "name": project.name,
        "customer": project.customer,
        "status": "created",
        "total_rooms": 0,
        "total_sqft": 0.0,
        "estimated_cost": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }


@api_public.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project_api(
    project_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get project details via API"""
    # Would fetch from database
    return {
        "id": project_id,
        "name": "Sample Project",
        "customer": "ABC Construction",
        "status": "complete",
        "total_rooms": 10,
        "total_sqft": 2500.0,
        "estimated_cost": 5000.0,
        "created_at": datetime.utcnow().isoformat()
    }


@api_public.get("/api/projects/{project_id}/rooms")
async def get_project_rooms_api(
    project_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get all rooms for a project"""
    return {
        "project_id": project_id,
        "rooms": [
            {
                "id": "room_1",
                "name": "Office 1",
                "number": "201",
                "dimensions": {"length": 20, "width": 15, "height": 9},
                "total_area": 630,
                "surfaces": {
                    "walls": {"area": 579},
                    "ceiling": {"area": 300}
                }
            }
        ]
    }


@api_public.post("/api/projects/{project_id}/export/{format}")
async def export_project_api(
    project_id: str,
    format: str,  # excel or pdf
    api_key: str = Depends(verify_api_key)
):
    """Export project to Excel or PDF"""
    if format not in ["excel", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'pdf'")

    return {
        "project_id": project_id,
        "format": format,
        "download_url": f"https://paintingai.com/downloads/{project_id}.{format}",
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
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
    api_key: str = Depends(verify_api_key)
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
    # In production, would update database
    return {
        "id": room_id,
        "project_id": project_id,
        "name": room_update.name or "Updated Room",
        "dimensions": room_update.dimensions or {"length": 20, "width": 15, "height": 9},
        "updated_at": datetime.utcnow().isoformat(),
        "message": "Room updated successfully"
    }


@api_public.post("/api/projects/{project_id}/rooms")
async def create_room_manually(
    project_id: str,
    room: RoomCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually add a room that AI missed

    Sometimes AI doesn't detect all rooms (closets, mechanical rooms,
    unlabeled spaces). This lets estimators add them manually.

    Required for complete estimates on complex floor plans.
    """
    import uuid

    room_id = f"room_{uuid.uuid4().hex[:8]}"

    return {
        "id": room_id,
        "project_id": project_id,
        "name": room.name,
        "number": room.number,
        "dimensions": room.dimensions,
        "manually_added": True,
        "created_at": datetime.utcnow().isoformat(),
        "message": "Room added successfully"
    }


@api_public.delete("/api/projects/{project_id}/rooms/{room_id}")
async def delete_room(
    project_id: str,
    room_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a room that was incorrectly detected

    AI sometimes detects non-rooms (legends, title blocks, notes)
    as rooms. This lets estimators remove false positives.
    """
    # In production, would delete from database
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
    api_key: str = Depends(verify_api_key)
):
    """
    Change material selections for project

    Default recommendations are commercial-grade (ProMar 400).
    Estimators can upgrade to premium (Benjamin Moore Regal) or
    downgrade to economy (BEHR Premium Plus) based on customer needs.

    This triggers recalculation of all material costs.
    """
    # Would fetch materials from database and recalculate costs
    return {
        "project_id": project_id,
        "materials": {
            "paint_id": materials.paint_id,
            "primer_id": materials.primer_id,
            "quality_tier": materials.quality_tier
        },
        "updated_at": datetime.utcnow().isoformat(),
        "message": "Materials updated, costs recalculated"
    }


@api_public.get("/api/projects/{project_id}/assembly")
async def get_assembly_breakdown(
    project_id: str,
    api_key: str = Depends(verify_api_key)
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
    # In production, would call AssemblyExpander
    return {
        "project_id": project_id,
        "line_items": [
            {
                "item_number": "1.1",
                "category": "Prep - Walls",
                "description": "Spackle nail holes and imperfections",
                "quantity": 0.5,
                "unit": "hour",
                "unit_cost": 50.0,
                "total_cost": 25.0
            },
            {
                "item_number": "1.2",
                "category": "Prep - Walls",
                "description": "Sand surfaces smooth",
                "quantity": 1.2,
                "unit": "hour",
                "unit_cost": 50.0,
                "total_cost": 60.0
            }
        ],
        "summary": {
            "total_line_items": 144,
            "material_cost": 2500.0,
            "labor_cost": 2500.0,
            "total_cost": 5000.0
        }
    }


# Webhooks
@api_public.post("/api/webhooks", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a webhook for event notifications"""
    import uuid

    # Generate webhook secret
    secret = f"whsec_{uuid.uuid4().hex}"

    return {
        "id": f"wh_{uuid.uuid4().hex}",
        "url": webhook.url,
        "events": webhook.events,
        "secret": secret,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }


@api_public.get("/api/webhooks")
async def list_webhooks(api_key: str = Depends(verify_api_key)):
    """List all webhooks"""
    return {
        "webhooks": [
            {
                "id": "wh_123",
                "url": "https://example.com/webhook",
                "events": ["project.completed"],
                "is_active": True,
                "created_at": "2026-05-20T00:00:00"
            }
        ]
    }


@api_public.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a webhook"""
    return {
        "message": "Webhook deleted",
        "webhook_id": webhook_id
    }


# Webhook delivery
class WebhookDelivery:
    """Handle webhook event delivery"""

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
    async def deliver_webhook(url: str, event: str, data: dict, secret: str):
        """Deliver webhook to endpoint"""
        import httpx

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

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )

                return response.status_code == 200

        except Exception as e:
            print(f"Webhook delivery failed: {e}")
            return False


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

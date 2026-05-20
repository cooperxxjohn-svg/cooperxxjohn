"""
Painting.ai API Server
FastAPI backend for AI-powered painting takeoffs
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
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

from painting_detector import PaintingDetector, PaintCalculator
from database import Database
from export_generator import ExportGenerator

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
    """Upload and process a drawing"""

    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

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
        "message": "File uploaded successfully",
        "file_id": file_id,
        "filename": file.filename,
        "status": "processing"
    }


async def process_drawing(project_id: str, file_path: str, file_id: str):
    """Background task to process a drawing"""
    try:
        # Detect rooms and surfaces
        detection = detector.analyze_drawing(file_path)

        # Save rooms to database
        for room in detection.rooms:
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

        # Update project totals
        project = db.get_project(project_id)
        rooms = db.get_project_rooms(project_id)

        total_sqft = sum(r["total_area"] for r in rooms)

        db.update_project(project_id, {
            "status": "complete",
            "total_rooms": len(rooms),
            "total_sqft": total_sqft
        })

    except Exception as e:
        print(f"Error processing drawing: {e}")
        db.update_project(project_id, {
            "status": "failed",
            "error": str(e)
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

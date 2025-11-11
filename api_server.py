"""
FastAPI Server for BOQ Estimation System
Production-ready REST API for BOQ estimation service

This provides HTTP endpoints for:
- Drawing upload and processing
- BOQ generation
- Validation
- Export
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import tempfile
import shutil
from pathlib import Path
import uuid
import logging
from datetime import datetime

from boq_estimator import BOQEstimator
from boq_schema import ContractDetails, BOQDocument
from boq_validator import CPWDValidator
from config import BOQConfig, default_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BOQ Estimation API",
    description="AI-powered BOQ estimation for construction projects",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for job results (use Redis/database in production)
job_storage: Dict[str, dict] = {}

# Temporary storage directory
TEMP_DIR = Path("./temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("./api_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


# Request/Response Models
class EstimationRequest(BaseModel):
    """Request model for BOQ estimation"""
    contract_name: str
    location: str
    client: str = "Client Name"
    department: str = "CPWD"
    completion_period_days: Optional[int] = None
    merge_duplicates: bool = True
    validate: bool = True
    export_excel: bool = True


class EstimationResponse(BaseModel):
    """Response model for estimation job"""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None


class ValidationResponse(BaseModel):
    """Response model for validation"""
    is_valid: bool
    summary: dict
    issues: List[dict]


# Initialize estimator
config = BOQConfig()
estimator = None

try:
    api_key = config.get_api_key()
    if api_key:
        estimator = BOQEstimator(
            anthropic_api_key=api_key,
            dsr_rates=config.get_all_rates(),
            enable_logging=True
        )
        logger.info("✓ BOQ Estimator initialized successfully")
    else:
        logger.warning("⚠ ANTHROPIC_API_KEY not set. Drawing extraction will not work.")
except Exception as e:
    logger.error(f"Failed to initialize estimator: {e}")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "BOQ Estimation API",
        "version": "1.0.0",
        "status": "operational",
        "estimator_ready": estimator is not None,
        "endpoints": {
            "POST /estimate": "Create new BOQ estimation job",
            "GET /status/{job_id}": "Get job status",
            "GET /download/{job_id}": "Download BOQ files",
            "POST /validate": "Validate BOQ document",
            "GET /rates": "Get current DSR rates",
            "POST /rates": "Update rates"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "estimator_initialized": estimator is not None
    }


@app.post("/estimate", response_model=EstimationResponse)
async def create_estimation(
    background_tasks: BackgroundTasks,
    drawings: List[UploadFile] = File(...),
    contract_name: str = Form(...),
    location: str = Form(...),
    client: str = Form("Client Name"),
    department: str = Form("CPWD"),
    completion_period_days: Optional[int] = Form(None),
    merge_duplicates: bool = Form(True),
    validate: bool = Form(True),
    export_excel: bool = Form(True)
):
    """
    Create new BOQ estimation job from uploaded drawings

    - Upload PDF drawings
    - Provide project details
    - Returns job ID for tracking
    """
    if not estimator:
        raise HTTPException(
            status_code=503,
            detail="Estimator not initialized. Check API key configuration."
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save uploaded files
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    drawing_paths = []
    for drawing in drawings:
        if not drawing.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {drawing.filename}. Only PDF and images allowed."
            )

        file_path = job_dir / drawing.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(drawing.file, f)
        drawing_paths.append(str(file_path))

    # Create job record
    job_storage[job_id] = {
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "drawing_count": len(drawing_paths),
        "contract_name": contract_name
    }

    # Create contract details
    contract = ContractDetails(
        contract_name=contract_name,
        location=location,
        client=client,
        department=department,
        completion_period_days=completion_period_days
    )

    # Schedule background processing
    background_tasks.add_task(
        process_estimation_job,
        job_id=job_id,
        drawing_paths=drawing_paths,
        contract=contract,
        merge_duplicates=merge_duplicates,
        validate=validate,
        export_excel=export_excel
    )

    logger.info(f"Created estimation job: {job_id}")

    return EstimationResponse(
        job_id=job_id,
        status="pending",
        message=f"Estimation job created. Processing {len(drawing_paths)} drawings."
    )


async def process_estimation_job(
    job_id: str,
    drawing_paths: List[str],
    contract: ContractDetails,
    merge_duplicates: bool,
    validate: bool,
    export_excel: bool
):
    """Background task to process estimation"""
    try:
        # Update status
        job_storage[job_id]["status"] = "processing"
        job_storage[job_id]["progress"] = 10

        # Create output directory
        output_dir = OUTPUT_DIR / job_id
        output_dir.mkdir(exist_ok=True)

        # Process drawings
        logger.info(f"Job {job_id}: Processing drawings...")
        job_storage[job_id]["progress"] = 30

        boq = estimator.estimate_from_drawings(
            drawing_paths=drawing_paths,
            contract_details=contract,
            output_dir=str(output_dir),
            merge_duplicates=merge_duplicates,
            validate=validate
        )

        job_storage[job_id]["progress"] = 80

        # Export to Excel if requested
        excel_path = None
        if export_excel:
            excel_path = output_dir / "boq.xlsx"
            estimator.export_to_excel(boq, excel_path)

        job_storage[job_id]["progress"] = 100

        # Store result
        job_storage[job_id]["status"] = "completed"
        job_storage[job_id]["completed_at"] = datetime.now().isoformat()
        job_storage[job_id]["result"] = {
            "boq_id": boq.boq_id,
            "total_amount": float(boq.total_amount),
            "total_sections": len(boq.sections),
            "total_items": sum(len(s.items) for s in boq.sections),
            "output_dir": str(output_dir),
            "excel_available": excel_path is not None
        }

        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_storage[job_id]["status"] = "failed"
        job_storage[job_id]["error"] = str(e)


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of estimation job"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        message=f"Job {job['status']}",
        result=job.get("result"),
        error=job.get("error")
    )


@app.get("/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """
    Download BOQ files

    file_type: json, excel, summary, validation
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    output_dir = OUTPUT_DIR / job_id

    file_map = {
        "json": "boq_document.json",
        "excel": "boq.xlsx",
        "summary": "boq_summary.json",
        "validation": "validation_report.json"
    }

    if file_type not in file_map:
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = output_dir / file_map[file_type]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"{file_type} file not available")

    return FileResponse(
        file_path,
        filename=f"boq_{job_id}_{file_map[file_type]}"
    )


@app.post("/validate", response_model=ValidationResponse)
async def validate_boq(boq_data: dict):
    """Validate BOQ document against CPWD standards"""
    try:
        # Parse BOQ document
        boq = BOQDocument(**boq_data)

        # Validate
        validator = CPWDValidator()
        is_valid, results = validator.validate_document(boq)

        return ValidationResponse(
            is_valid=is_valid,
            summary=validator.get_validation_summary(),
            issues=[r.to_dict() for r in results]
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@app.get("/rates")
async def get_rates():
    """Get current DSR rates"""
    return {
        "region": config.get('region'),
        "dsr_year": config.get('dsr_year'),
        "labour_rates": config.config["labour_rates"],
        "material_rates": config.config["material_rates"]
    }


@app.post("/rates")
async def update_rates(rate_updates: Dict[str, float]):
    """Update specific rates"""
    try:
        config.update_rates(rate_updates)

        # Reinitialize estimator with new rates
        global estimator
        api_key = config.get_api_key()
        if api_key:
            estimator = BOQEstimator(
                anthropic_api_key=api_key,
                dsr_rates=config.get_all_rates()
            )

        return {
            "status": "success",
            "message": f"Updated {len(rate_updates)} rates",
            "updated_rates": rate_updates
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete job and associated files"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete files
    job_dir = TEMP_DIR / job_id
    output_dir = OUTPUT_DIR / job_id

    if job_dir.exists():
        shutil.rmtree(job_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Remove from storage
    del job_storage[job_id]

    return {"status": "success", "message": f"Job {job_id} deleted"}


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API server...")
    # Clean up temporary files
    # In production, use proper cleanup mechanisms


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("BOQ Estimation API Server")
    print("=" * 80)
    print("\nStarting server on http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

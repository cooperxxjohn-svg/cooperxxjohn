# Drywall Takeoff System - Processing Pipeline Implementation

Technical implementation guide for the multi-stage backend processing pipeline.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
├─────────────────────────────────────────────────────────────────┤
│  Endpoints  │  Auth  │  Validation  │  Background Tasks         │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├──> PostgreSQL (Job State, Results)
         ├──> Redis (Job Queue, Cache)
         ├──> S3 / Local Storage (Files)
         └──> Anthropic API (AI Processing)

Processing Flow:
  User Request → API Endpoint → Create Job → Queue Worker
                                            → Process Stages 1-8
                                            → Update Status
                                            → Return Results
```

---

## Technology Stack

### Core Framework
- **FastAPI** - Modern Python async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and serialization

### Storage & Database
- **PostgreSQL** - Primary database (job state, results)
- **Redis** - Job queue and caching
- **AWS S3** - File storage (production)
- **Local filesystem** - File storage (development)

### Background Processing
- **FastAPI BackgroundTasks** - Simple async tasks
- **Celery** (optional) - Advanced job queue with retry/monitoring

### AI Processing
- **Anthropic Python SDK** - Claude Sonnet API client
- **pdf2image** - PDF to image conversion
- **Pillow** - Image manipulation

### Utilities
- **python-multipart** - File upload handling
- **python-dotenv** - Environment configuration
- **boto3** - AWS S3 client

---

## Project Structure

```
backend/
├── main.py                          # FastAPI application entry point
├── config.py                        # Configuration management
├── dependencies.py                  # Dependency injection
│
├── api/
│   ├── __init__.py
│   ├── takeoffs.py                  # Takeoff endpoints
│   ├── exports.py                   # Export endpoints
│   ├── config_api.py                # Configuration endpoints
│   └── webhooks.py                  # Webhook endpoints
│
├── models/
│   ├── __init__.py
│   ├── database.py                  # SQLAlchemy models
│   ├── schemas.py                   # Pydantic schemas
│   └── enums.py                     # Enumerations
│
├── services/
│   ├── __init__.py
│   ├── storage_service.py           # S3/local file storage
│   ├── ai_service.py                # Anthropic API wrapper
│   ├── calculation_service.py       # Material/labor calculations
│   └── export_service.py            # Excel/PDF export generation
│
├── processors/
│   ├── __init__.py
│   ├── pipeline.py                  # Main pipeline orchestrator
│   ├── stage_1_upload.py            # Upload & storage
│   ├── stage_2_classification.py    # Document classification
│   ├── stage_3_drawing_analysis.py  # Drawing metadata extraction
│   ├── stage_4_wall_extraction.py   # Wall detection
│   ├── stage_5_opening_detection.py # Opening detection
│   ├── stage_6_materials.py         # Material calculations
│   ├── stage_7_labor.py             # Labor estimation
│   └── stage_8_takeoff.py           # Final takeoff generation
│
├── utils/
│   ├── __init__.py
│   ├── validation.py                # Data validation utilities
│   ├── pdf_utils.py                 # PDF processing
│   ├── retry.py                     # Retry decorator
│   └── logging_config.py            # Logging setup
│
├── database/
│   ├── __init__.py
│   ├── connection.py                # Database connection pool
│   ├── migrations/                  # Alembic migrations
│   └── seeds/                       # Seed data
│
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_calculations.py
│   └── test_api.py
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Implementation Guide

### 1. Main Application (main.py)

```python
"""
Drywall Takeoff API Server
FastAPI backend for AI-powered drywall takeoff estimation
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api import takeoffs, exports, config_api, webhooks
from database.connection import init_db, close_db
from config import get_settings
from utils.logging_config import setup_logging

# Setup logging
setup_logging()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    await init_db(settings.database_url)
    print(f"[Startup] Database initialized")
    print(f"[Startup] Storage: {settings.storage_type}")
    print(f"[Startup] AI Service: Anthropic Claude Sonnet")
    
    yield
    
    # Shutdown
    await close_db()
    print("[Shutdown] Database connections closed")

# Create FastAPI app
app = FastAPI(
    title="Drywall Takeoff API",
    description="AI-powered takeoff and estimating for drywall contractors",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(takeoffs.router, prefix="/api/v1/takeoffs", tags=["Takeoffs"])
app.include_router(exports.router, prefix="/api/v1/takeoffs", tags=["Exports"])
app.include_router(config_api.router, prefix="/api/v1/config", tags=["Configuration"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

@app.get("/")
async def root():
    return {
        "app": "Drywall Takeoff API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/api/v1/health")
async def health_check():
    """System health check"""
    from database.connection import check_db_health
    from services.storage_service import check_storage_health
    from services.ai_service import check_ai_health
    
    services = {
        "database": await check_db_health(),
        "storage": await check_storage_health(),
        "ai_service": await check_ai_health()
    }
    
    status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Development only
    )
```

---

### 2. Configuration (config.py)

```python
"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "Drywall Takeoff API"
    debug: bool = False
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Storage
    storage_type: str = "local"  # "local" or "s3"
    s3_bucket_uploads: Optional[str] = None
    s3_bucket_exports: Optional[str] = None
    s3_region: str = "us-east-1"
    local_upload_dir: str = "./uploads"
    local_output_dir: str = "./outputs"
    
    # Anthropic AI
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4096
    anthropic_timeout: int = 120  # seconds
    
    # File upload limits
    max_file_size_mb: int = 50
    max_total_upload_mb: int = 200
    allowed_file_types: list = [".pdf", ".png", ".jpg", ".jpeg"]
    
    # Processing
    default_processing_mode: str = "fast"
    ai_confidence_threshold: float = 0.70
    retry_attempts: int = 3
    retry_backoff_factor: float = 2.0
    
    # Regional labor rates
    labor_base_rate: float = 55.00
    labor_regional_multipliers: dict = {
        "northeast": 1.10,
        "west": 1.20,
        "south": 0.95,
        "midwest": 1.00,
        "mountain": 1.05,
        "pacific": 1.15
    }
    
    # Material pricing
    material_prices_update_date: str = "2026-05-01"
    
    # Authentication (if needed)
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
```

---

### 3. Pipeline Orchestrator (processors/pipeline.py)

```python
"""
Main processing pipeline orchestrator
Coordinates execution of all 8 stages
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from processors import (
    stage_1_upload,
    stage_2_classification,
    stage_3_drawing_analysis,
    stage_4_wall_extraction,
    stage_5_opening_detection,
    stage_6_materials,
    stage_7_labor,
    stage_8_takeoff
)
from models.schemas import ProcessingJob, JobStatus
from database.connection import get_db_session
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """
    Orchestrates the complete 8-stage processing pipeline
    """
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job_data: Optional[ProcessingJob] = None
        
    async def execute(self):
        """
        Execute the complete pipeline
        """
        try:
            # Load job from database
            self.job_data = await self._load_job()
            
            # Update status
            await self._update_status(JobStatus.PROCESSING, "stage_1_upload", 5)
            
            # Execute stages sequentially
            if self.job_data.processing_mode == "manual":
                # Skip AI stages for manual mode
                await self._execute_stage_6()
                await self._execute_stage_7()
                await self._execute_stage_8()
            else:
                # Full pipeline
                await self._execute_stage_1()
                await self._execute_stage_2()
                await self._execute_stage_3()
                await self._execute_stage_4()
                await self._execute_stage_5()
                await self._execute_stage_6()
                await self._execute_stage_7()
                await self._execute_stage_8()
            
            # Mark as completed
            await self._update_status(JobStatus.COMPLETED, "stage_8_takeoff_generation", 100)
            logger.info(f"Job {self.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {str(e)}", exc_info=True)
            await self._handle_failure(e)
    
    async def _execute_stage_1(self):
        """Stage 1: Upload & Storage"""
        logger.info(f"Job {self.job_id}: Executing Stage 1 - Upload & Storage")
        await self._update_status(JobStatus.PROCESSING, "stage_1_upload", 5)
        
        # Already completed during job creation
        # Just validate files are accessible
        await stage_1_upload.validate_files(self.job_data.input_files)
        
        await self._update_status(JobStatus.PROCESSING, "stage_2_classification", 10)
    
    async def _execute_stage_2(self):
        """Stage 2: Document Classification"""
        logger.info(f"Job {self.job_id}: Executing Stage 2 - Classification")
        
        result = await stage_2_classification.classify_documents(
            job_id=self.job_id,
            files=self.job_data.input_files
        )
        
        self.job_data.page_classifications = result["classifications"]
        await self._save_stage_output("page_classifications", result)
        await self._update_status(JobStatus.PROCESSING, "stage_3_drawing_analysis", 25)
    
    async def _execute_stage_3(self):
        """Stage 3: Drawing Analysis"""
        logger.info(f"Job {self.job_id}: Executing Stage 3 - Drawing Analysis")
        
        # Filter floor plan pages
        floor_plans = [
            p for p in self.job_data.page_classifications
            if p["page_type"] == "floor_plan" and p["recommended_for_extraction"]
        ]
        
        if not floor_plans:
            raise ValueError("No floor plan pages found for processing")
        
        result = await stage_3_drawing_analysis.analyze_drawings(
            job_id=self.job_id,
            floor_plan_pages=floor_plans
        )
        
        self.job_data.drawing_metadata = result["metadata"]
        await self._save_stage_output("drawing_metadata", result)
        await self._update_status(JobStatus.PROCESSING, "stage_4_wall_extraction", 35)
    
    async def _execute_stage_4(self):
        """Stage 4: Wall Extraction (CRITICAL)"""
        logger.info(f"Job {self.job_id}: Executing Stage 4 - Wall Extraction")
        
        result = await stage_4_wall_extraction.extract_walls(
            job_id=self.job_id,
            floor_plan_pages=self._get_floor_plan_pages(),
            drawing_metadata=self.job_data.drawing_metadata,
            project_metadata=self.job_data.project_metadata
        )
        
        if not result["walls"] or len(result["walls"]) == 0:
            raise ValueError("No walls detected. Try manual mode or upload clearer drawings.")
        
        self.job_data.walls = result["walls"]
        await self._save_stage_output("walls", result)
        await self._update_status(JobStatus.PROCESSING, "stage_5_opening_detection", 55)
    
    async def _execute_stage_5(self):
        """Stage 5: Opening Detection"""
        logger.info(f"Job {self.job_id}: Executing Stage 5 - Opening Detection")
        
        result = await stage_5_opening_detection.detect_openings(
            job_id=self.job_id,
            floor_plan_pages=self._get_floor_plan_pages(),
            walls=self.job_data.walls
        )
        
        self.job_data.openings = result.get("openings", [])
        await self._save_stage_output("openings", result)
        await self._update_status(JobStatus.PROCESSING, "stage_6_material_calculations", 70)
    
    async def _execute_stage_6(self):
        """Stage 6: Material Calculations (DETERMINISTIC)"""
        logger.info(f"Job {self.job_id}: Executing Stage 6 - Material Calculations")
        
        result = await stage_6_materials.calculate_materials(
            job_id=self.job_id,
            walls=self.job_data.walls,
            openings=self.job_data.openings or [],
            project_metadata=self.job_data.project_metadata
        )
        
        self.job_data.materials = result
        await self._save_stage_output("materials", result)
        await self._update_status(JobStatus.PROCESSING, "stage_7_labor_estimation", 85)
    
    async def _execute_stage_7(self):
        """Stage 7: Labor Estimation (DETERMINISTIC)"""
        logger.info(f"Job {self.job_id}: Executing Stage 7 - Labor Estimation")
        
        result = await stage_7_labor.estimate_labor(
            job_id=self.job_id,
            materials=self.job_data.materials,
            project_metadata=self.job_data.project_metadata
        )
        
        self.job_data.labor = result
        await self._save_stage_output("labor", result)
        await self._update_status(JobStatus.PROCESSING, "stage_8_takeoff_generation", 95)
    
    async def _execute_stage_8(self):
        """Stage 8: Takeoff Generation"""
        logger.info(f"Job {self.job_id}: Executing Stage 8 - Takeoff Generation")
        
        result = await stage_8_takeoff.generate_takeoff(
            job_id=self.job_id,
            walls=self.job_data.walls,
            openings=self.job_data.openings or [],
            materials=self.job_data.materials,
            labor=self.job_data.labor,
            project_metadata=self.job_data.project_metadata
        )
        
        self.job_data.takeoff = result
        await self._save_stage_output("takeoff", result)
    
    async def _load_job(self) -> ProcessingJob:
        """Load job from database"""
        async with get_db_session() as session:
            job = await session.get(ProcessingJob, self.job_id)
            if not job:
                raise ValueError(f"Job {self.job_id} not found")
            return job
    
    async def _update_status(
        self, 
        status: JobStatus, 
        stage: str, 
        progress: int
    ):
        """Update job status in database"""
        async with get_db_session() as session:
            job = await session.get(ProcessingJob, self.job_id)
            job.status = status
            job.current_stage = stage
            job.progress_percent = progress
            
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
            
            await session.commit()
    
    async def _save_stage_output(self, field_name: str, data: Dict[Any, Any]):
        """Save stage output to database"""
        async with get_db_session() as session:
            job = await session.get(ProcessingJob, self.job_id)
            setattr(job, field_name, data)
            await session.commit()
    
    async def _handle_failure(self, error: Exception):
        """Handle pipeline failure"""
        async with get_db_session() as session:
            job = await session.get(ProcessingJob, self.job_id)
            job.status = JobStatus.FAILED
            job.failed_at = datetime.utcnow()
            job.errors = job.errors or []
            job.errors.append({
                "error_id": f"err_{len(job.errors) + 1}",
                "stage": job.current_stage,
                "error_code": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            })
            await session.commit()
    
    def _get_floor_plan_pages(self):
        """Get floor plan pages from classifications"""
        return [
            p for p in self.job_data.page_classifications
            if p["page_type"] == "floor_plan"
        ]


# Background task entry point
async def process_takeoff_job(job_id: str):
    """
    Entry point for background processing
    Called from FastAPI BackgroundTasks or Celery
    """
    pipeline = ProcessingPipeline(job_id)
    await pipeline.execute()
```

---

### 4. Stage 4: Wall Extraction (stage_4_wall_extraction.py)

```python
"""
Stage 4: Wall Extraction
Uses Claude Sonnet to detect walls from floor plan images
"""

import base64
from typing import List, Dict, Any
import logging

from services.ai_service import AnthropicService
from services.storage_service import StorageService
from utils.validation import validate_walls
from utils.pdf_utils import pdf_page_to_image

logger = logging.getLogger(__name__)

async def extract_walls(
    job_id: str,
    floor_plan_pages: List[Dict],
    drawing_metadata: List[Dict],
    project_metadata: Dict
) -> Dict[str, Any]:
    """
    Extract wall segments from floor plan pages using AI
    
    Returns:
        {
            "walls": List[Wall],
            "wall_summary": {...},
            "quality_checks": {...}
        }
    """
    
    ai_service = AnthropicService()
    storage_service = StorageService()
    
    all_walls = []
    
    for page in floor_plan_pages:
        # Get page metadata
        metadata = next(
            (m for m in drawing_metadata if m["page_number"] == page["page_number"]),
            None
        )
        
        # Load image
        image_path = await storage_service.get_file_path(page["file_id"])
        image_data = pdf_page_to_image(image_path, page["page_number"])
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Build AI prompt
        prompt = build_wall_extraction_prompt(metadata, project_metadata)
        
        # Call AI service
        response = await ai_service.analyze_image_with_prompt(
            image_base64=image_base64,
            prompt=prompt,
            max_tokens=4096
        )
        
        # Parse response
        page_walls = parse_wall_response(response, page, metadata)
        all_walls.extend(page_walls)
        
        logger.info(f"Extracted {len(page_walls)} walls from page {page['page_number']}")
    
    # Post-process walls
    processed_walls = post_process_walls(all_walls)
    
    # Run quality checks
    quality_checks = run_quality_checks(processed_walls, project_metadata)
    
    # Generate summary
    wall_summary = generate_wall_summary(processed_walls)
    
    return {
        "walls": processed_walls,
        "wall_summary": wall_summary,
        "quality_checks": quality_checks
    }

def build_wall_extraction_prompt(metadata: Dict, project_metadata: Dict) -> str:
    """Build AI prompt for wall extraction"""
    
    scale_info = ""
    if metadata and "scale" in metadata:
        scale_info = f"Scale: {metadata['scale']['ratio']}"
    
    ceiling_height = project_metadata.get("default_ceiling_height", 9.0)
    
    prompt = f"""Analyze this floor plan and extract ALL wall segments.

{scale_info}
Default ceiling height: {ceiling_height} feet

For each wall segment:
1. Identify start point and end point (x, y coordinates in pixels from top-left)
2. Calculate actual length in feet based on the scale
3. Determine wall type:
   - "exterior": Perimeter/exterior walls
   - "interior": Interior partition walls
   - "load_bearing": Structural walls (if clearly marked)
4. Estimate wall thickness in inches (typical: 4.5", 6", 8")
5. Use default ceiling height unless otherwise specified
6. Rate your confidence (0-1) for each wall detection

CRITICAL INSTRUCTIONS:
- Trace each distinct wall segment separately
- Include ALL walls, even short segments
- Note wall intersections (corners, T-junctions)
- If a wall is unclear or partially obscured, still include it but note low confidence
- Return valid JSON only

Return JSON format:
{{
  "walls": [
    {{
      "start_point": {{"x": 100, "y": 200}},
      "end_point": {{"x": 1100, "y": 200}},
      "length_ft": 40.0,
      "height_ft": 9.0,
      "type": "exterior",
      "thickness_inches": 6.0,
      "material_hint": "wood_frame",
      "confidence": 0.95,
      "notes": "North perimeter wall"
    }}
  ]
}}"""
    
    return prompt

def parse_wall_response(response: str, page: Dict, metadata: Dict) -> List[Dict]:
    """Parse AI response and convert to Wall objects"""
    import json
    
    try:
        data = json.loads(response)
        walls = data.get("walls", [])
        
        # Add page reference and IDs
        for i, wall in enumerate(walls):
            wall["id"] = f"W{len(walls) + i + 1}"
            wall["page_id"] = f"{page['file_id']}_p{page['page_number']}"
            wall["wall_area_sqft"] = wall["length_ft"] * wall["height_ft"]
        
        return walls
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise ValueError("AI returned invalid JSON for wall extraction")

def post_process_walls(walls: List[Dict]) -> List[Dict]:
    """
    Post-process walls:
    - Merge co-linear segments if appropriate
    - Detect intersections
    - Validate dimensions
    """
    
    # Validate each wall
    validated_walls = []
    for wall in walls:
        if validate_wall(wall):
            validated_walls.append(wall)
        else:
            logger.warning(f"Wall {wall.get('id')} failed validation, skipping")
    
    # TODO: Implement intersection detection
    # TODO: Implement co-linear segment merging
    
    return validated_walls

def validate_wall(wall: Dict) -> bool:
    """Validate wall dimensions"""
    length = wall.get("length_ft", 0)
    height = wall.get("height_ft", 0)
    
    # Reasonable ranges
    if length < 1 or length > 200:
        return False
    if height < 7 or height > 20:
        return False
    
    return True

def run_quality_checks(walls: List[Dict], project_metadata: Dict) -> Dict:
    """Run quality checks on extracted walls"""
    
    checks = {
        "disconnected_segments": 0,
        "low_confidence_walls": 0,
        "ratio_check": "unknown",
        "warnings": []
    }
    
    # Count low confidence walls
    low_conf = [w for w in walls if w.get("confidence", 1.0) < 0.85]
    checks["low_confidence_walls"] = len(low_conf)
    
    if low_conf:
        for wall in low_conf:
            checks["warnings"].append(
                f"Wall {wall['id']} has confidence {wall['confidence']:.2f} < 0.85"
            )
    
    # Check wall-to-floor ratio
    total_wall_area = sum(w["wall_area_sqft"] for w in walls)
    floor_area = project_metadata.get("floor_area_sqft")
    
    if floor_area:
        ratio = total_wall_area / floor_area
        if 0.2 <= ratio <= 0.5:
            checks["ratio_check"] = "pass"
        else:
            checks["ratio_check"] = "warn"
            checks["warnings"].append(
                f"Wall-to-floor ratio {ratio:.2f} is outside typical range (0.2-0.5)"
            )
    
    return checks

def generate_wall_summary(walls: List[Dict]) -> Dict:
    """Generate wall summary statistics"""
    
    total_linear_feet = sum(w["length_ft"] for w in walls)
    total_wall_area = sum(w["wall_area_sqft"] for w in walls)
    
    exterior_walls = [w for w in walls if w["type"] == "exterior"]
    interior_walls = [w for w in walls if w["type"] == "interior"]
    
    avg_height = sum(w["height_ft"] for w in walls) / len(walls) if walls else 0
    
    return {
        "total_walls": len(walls),
        "total_linear_feet": round(total_linear_feet, 2),
        "total_wall_area_sqft": round(total_wall_area, 2),
        "exterior_walls": len(exterior_walls),
        "interior_walls": len(interior_walls),
        "average_height": round(avg_height, 2)
    }
```

---

### 5. Stage 6: Material Calculations (stage_6_materials.py)

```python
"""
Stage 6: Material Calculations
100% deterministic calculations based on wall/opening data
"""

from typing import List, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Industry standard productivity rates
WASTE_FACTOR = 1.15  # 15% waste
STUDS_PER_FOOT_16OC = 12 / 16  # 0.75 studs per linear foot
STUDS_PER_FOOT_24OC = 12 / 24  # 0.50 studs per linear foot
SCREWS_PER_SHEET = 60
SCREWS_PER_LB = 400
JOINT_COMPOUND_PER_SQFT_PER_COAT = 0.05  # gallons

async def calculate_materials(
    job_id: str,
    walls: List[Dict],
    openings: List[Dict],
    project_metadata: Dict
) -> Dict[str, Any]:
    """
    Calculate all material quantities using deterministic formulas
    
    Returns complete material breakdown
    """
    
    # Extract configuration
    stud_spacing = project_metadata.get("default_stud_spacing", 16)
    finishing_level = project_metadata.get("finishing_level", 3)
    drywall_thickness = project_metadata.get("drywall_thickness", 0.5)
    
    # Calculate total areas
    total_wall_area = sum(w["wall_area_sqft"] for w in walls)
    total_opening_area = sum(o["area_sqft"] for o in openings)
    net_wall_area = total_wall_area - total_opening_area
    
    # Both sides of wall
    total_drywall_area = net_wall_area * 2
    
    # Calculate framing
    framing = calculate_framing(walls, stud_spacing)
    
    # Calculate drywall sheets
    drywall = calculate_drywall(total_drywall_area, drywall_thickness)
    
    # Calculate fasteners
    fasteners = calculate_fasteners(drywall["total_sheets"])
    
    # Calculate finishing materials
    finishing = calculate_finishing(total_drywall_area, finishing_level, walls)
    
    # Calculate summary
    material_summary = {
        "total_drywall_sqft": round(total_drywall_area, 2),
        "net_coverage_sqft": round(net_wall_area * 2 / WASTE_FACTOR, 2),
        "waste_factor": WASTE_FACTOR,
        "total_linear_feet_framing": round(sum(w["length_ft"] for w in walls), 2),
        "total_studs": framing.get("studs_16oc", {}).get("quantity", 0) + 
                      framing.get("studs_24oc", {}).get("quantity", 0),
        "estimated_material_cost": 0.0,  # Will calculate with pricing
        "cost_per_sqft": 0.0
    }
    
    return {
        "job_id": job_id,
        "calculated_at": datetime.utcnow().isoformat(),
        "calculation_method": "deterministic",
        "framing": framing,
        "drywall": drywall,
        "fasteners": fasteners,
        "finishing": finishing,
        "material_summary": material_summary,
        "calculation_metadata": {
            "calculated_at": datetime.utcnow().isoformat(),
            "assumptions": {
                "stud_spacing": f"{stud_spacing} inches OC",
                "drywall_thickness": f"{drywall_thickness} inch",
                "finish_level": finishing_level,
                "waste_factor": int((WASTE_FACTOR - 1) * 100),
                "sheet_size_primary": "4x12",
                "sheet_size_secondary": "4x8"
            }
        }
    }

def calculate_framing(walls: List[Dict], stud_spacing: int) -> Dict:
    """Calculate framing materials"""
    
    total_linear_feet = sum(w["length_ft"] for w in walls)
    
    # Studs
    studs_per_foot = STUDS_PER_FOOT_16OC if stud_spacing == 16 else STUDS_PER_FOOT_24OC
    total_studs = int(total_linear_feet * studs_per_foot * 1.10)  # 10% extra
    
    # Plates (top and bottom)
    total_track_feet = total_linear_feet * 2  # Double for top plate
    
    # Headers for openings (estimated)
    header_lf = total_linear_feet * 0.15  # Rough estimate
    
    result = {}
    
    if stud_spacing == 16:
        result["studs_16oc"] = {
            "item": "2x4 Wood Studs @ 16\" OC",
            "quantity": total_studs,
            "unit": "EA",
            "length": "10ft",
            "notes": "Includes 10% waste for cuts and blocking"
        }
    else:
        result["studs_24oc"] = {
            "item": "2x4 Wood Studs @ 24\" OC",
            "quantity": total_studs,
            "unit": "EA",
            "length": "10ft",
            "notes": "Includes 10% waste for cuts and blocking"
        }
    
    result["top_plate"] = {
        "item": "2x4 Top Plate (double)",
        "quantity": int(total_track_feet),
        "unit": "LF",
        "notes": "Double top plate for all walls"
    }
    
    result["bottom_plate"] = {
        "item": "2x4 Bottom Plate",
        "quantity": int(total_linear_feet),
        "unit": "LF"
    }
    
    result["header_material"] = {
        "item": "2x6 Header Stock",
        "quantity": int(header_lf),
        "unit": "LF",
        "notes": "For door and window headers"
    }
    
    return result

def calculate_drywall(total_area_sqft: float, thickness: float) -> Dict:
    """Calculate drywall sheet quantities"""
    
    # Apply waste factor
    area_with_waste = total_area_sqft * WASTE_FACTOR
    
    # Use 4x12 sheets (48 sqft) as primary
    # Use 4x8 sheets (32 sqft) for cuts and waste
    sheets_needed = area_with_waste / 48
    
    sheets_4x12 = int(sheets_needed * 0.85)
    sheets_4x8 = int((sheets_needed - sheets_4x12) * 1.5)
    
    thickness_str = "1/2" if thickness == 0.5 else "5/8"
    
    return {
        "sheets_4x12_1_2": {
            "item": f"{thickness_str}\" Drywall 4'x12' Sheets",
            "quantity": sheets_4x12,
            "unit": "EA",
            "sqft": sheets_4x12 * 48,
            "coverage_sqft": int(sheets_4x12 * 48 / WASTE_FACTOR),
            "waste_percent": 15
        },
        "sheets_4x8_1_2": {
            "item": f"{thickness_str}\" Drywall 4'x8' Sheets",
            "quantity": sheets_4x8,
            "unit": "EA",
            "sqft": sheets_4x8 * 32,
            "coverage_sqft": int(sheets_4x8 * 32 / WASTE_FACTOR),
            "waste_percent": 15
        },
        "total_sheets": sheets_4x12 + sheets_4x8
    }

def calculate_fasteners(total_sheets: int) -> Dict:
    """Calculate fastener quantities"""
    
    total_screws = total_sheets * SCREWS_PER_SHEET
    screws_lbs = total_screws / SCREWS_PER_LB
    
    return {
        "screws_1_5_8": {
            "item": "#6 x 1-5/8\" Drywall Screws",
            "quantity": int(screws_lbs) + 1,
            "unit": "LB",
            "approx_count": total_screws
        }
    }

def calculate_finishing(
    total_area_sqft: float, 
    finishing_level: int,
    walls: List[Dict]
) -> Dict:
    """Calculate finishing materials"""
    
    # Joint compound (varies by level)
    coats = finishing_level  # Level 3 = 3 coats, etc.
    joint_compound_gal = total_area_sqft * JOINT_COMPOUND_PER_SQFT_PER_COAT * coats
    
    # Paper tape (approximate: 50 LF per sheet)
    total_sheets = int(total_area_sqft / 48)
    paper_tape_lf = total_sheets * 50
    
    # Corner bead (all outside corners)
    # Rough estimate: 10% of total wall height
    total_wall_height = sum(w["height_ft"] for w in walls)
    corner_bead_lf = total_wall_height * 0.10
    
    return {
        "joint_compound_level3": {
            "item": "All-Purpose Joint Compound",
            "quantity": int(joint_compound_gal) + 1,
            "unit": "GAL",
            "coverage": "~80 sqft per gallon per coat",
            "coats": coats,
            "notes": f"Level {finishing_level} finish ({coats} coats)"
        },
        "paper_tape": {
            "item": "Paper Joint Tape",
            "quantity": int(paper_tape_lf),
            "unit": "LF",
            "rolls": int(paper_tape_lf / 250) + 1,
            "notes": "250 ft per roll standard"
        },
        "corner_bead_metal": {
            "item": "Metal Corner Bead",
            "quantity": int(corner_bead_lf),
            "unit": "LF",
            "pieces": int(corner_bead_lf / 10) + 1,
            "notes": "10 ft lengths standard"
        },
        "sanding_supplies": {
            "item": "Sanding Screens/Paper Assortment",
            "quantity": 1,
            "unit": "KIT"
        }
    }
```

---

## Next Steps

1. **Implement remaining stage processors** (stages 2, 3, 5, 7, 8)
2. **Create AI service wrapper** for Anthropic API
3. **Implement storage service** for S3/local files
4. **Set up database models** with SQLAlchemy
5. **Create API endpoints** using FastAPI routers
6. **Add export functionality** (Excel, PDF, CSV)
7. **Implement testing suite**
8. **Add monitoring and logging**

---

**Document Version**: 1.0
**Last Updated**: 2026-05-21
**Implementation Status**: Design Complete

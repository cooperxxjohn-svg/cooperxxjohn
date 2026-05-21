# Drywall Takeoff API - Complete Endpoint Specification

## Base URL
```
Production: https://api.drywalltakeoff.com/v1
Development: http://localhost:8000/api/v1
```

## Authentication
All endpoints except health checks require API authentication:

```http
Authorization: Bearer <access_token>
X-API-Key: <api_key>
```

---

## 1. Takeoff Management Endpoints

### POST /api/v1/takeoffs/create

Create a new takeoff job and upload drawings.

**Request:**
```http
POST /api/v1/takeoffs/create
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- files[]: File[] (PDF or images, max 50MB each)
- project_name: string
- project_type: "commercial" | "residential" | "industrial"
- default_ceiling_height: number (default: 9.0)
- finishing_level: 1 | 2 | 3 | 4 | 5 (default: 3)
- region: string (e.g., "northeast", "west", "south", "midwest")
- stud_spacing: 16 | 24 (default: 16)
- processing_mode: "fast" | "deep" | "manual" (default: "fast")
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123xyz",
    "status": "queued",
    "project": {
      "project_id": "proj_456def",
      "project_name": "Office Building - Level 1",
      "project_type": "commercial"
    },
    "files": [
      {
        "file_id": "file_001",
        "filename": "FloorPlan_L1.pdf",
        "size_bytes": 2457600,
        "page_count": 1,
        "storage_url": "s3://uploads/proj_456def/file_001.pdf"
      }
    ],
    "estimated_completion_time": "2026-05-21T10:35:00Z",
    "estimated_duration_seconds": 35
  },
  "message": "Takeoff job created and queued for processing"
}
```

**Error Responses:**
```json
// 400 Bad Request - Invalid file type
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only PDF, PNG, JPG files are allowed",
    "allowed_types": [".pdf", ".png", ".jpg", ".jpeg"]
  }
}

// 413 Payload Too Large
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds maximum of 50MB",
    "max_size_mb": 50,
    "uploaded_size_mb": 67
  }
}

// 429 Too Many Requests
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Maximum 10 jobs per minute exceeded",
    "retry_after_seconds": 45
  }
}
```

**Example cURL:**
```bash
curl -X POST "https://api.drywalltakeoff.com/v1/takeoffs/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files[]=@FloorPlan.pdf" \
  -F "project_name=Office Building L1" \
  -F "project_type=commercial" \
  -F "default_ceiling_height=9.0" \
  -F "finishing_level=3" \
  -F "region=northeast" \
  -F "processing_mode=fast"
```

---

### GET /api/v1/takeoffs/{job_id}/status

Get real-time processing status and progress.

**Request:**
```http
GET /api/v1/takeoffs/{job_id}/status
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123xyz",
    "status": "processing",
    "current_stage": "stage_4_wall_extraction",
    "progress_percent": 45,
    "started_at": "2026-05-21T10:30:00Z",
    "estimated_completion": "2026-05-21T10:35:00Z",
    "stages": {
      "stage_1_upload": {
        "status": "completed",
        "progress": 100,
        "completed_at": "2026-05-21T10:30:02Z",
        "message": "Files uploaded successfully"
      },
      "stage_2_classification": {
        "status": "completed",
        "progress": 100,
        "completed_at": "2026-05-21T10:30:10Z",
        "message": "Classified 1 floor plan page"
      },
      "stage_3_drawing_analysis": {
        "status": "completed",
        "progress": 100,
        "completed_at": "2026-05-21T10:30:18Z",
        "message": "Extracted scale and dimensions"
      },
      "stage_4_wall_extraction": {
        "status": "processing",
        "progress": 65,
        "message": "Detecting walls with AI... 12 walls found so far"
      },
      "stage_5_opening_detection": {
        "status": "pending",
        "progress": 0
      },
      "stage_6_material_calculations": {
        "status": "pending",
        "progress": 0
      },
      "stage_7_labor_estimation": {
        "status": "pending",
        "progress": 0
      },
      "stage_8_takeoff_generation": {
        "status": "pending",
        "progress": 0
      }
    },
    "partial_results": {
      "walls_detected": 12,
      "total_linear_feet": 280.5
    }
  }
}
```

**Response (200 OK - Completed):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123xyz",
    "status": "completed",
    "current_stage": "stage_8_takeoff_generation",
    "progress_percent": 100,
    "started_at": "2026-05-21T10:30:00Z",
    "completed_at": "2026-05-21T10:30:35Z",
    "processing_time_seconds": 35,
    "summary": {
      "total_walls": 15,
      "total_openings": 18,
      "total_wall_area_sqft": 2880.0,
      "total_material_cost": 8950.00,
      "total_labor_cost": 17645.00,
      "total_cost": 33642.68
    },
    "results_url": "/api/v1/takeoffs/job_abc123xyz/results"
  }
}
```

**Response (200 OK - Failed):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123xyz",
    "status": "failed",
    "current_stage": "stage_4_wall_extraction",
    "progress_percent": 35,
    "started_at": "2026-05-21T10:30:00Z",
    "failed_at": "2026-05-21T10:30:25Z",
    "error": {
      "code": "WALL_EXTRACTION_FAILED",
      "message": "No walls could be detected in the floor plan",
      "details": "The AI could not identify wall segments. Drawing may be too unclear or not a floor plan.",
      "suggestions": [
        "Try uploading a clearer floor plan image",
        "Use manual mode to input wall measurements directly",
        "Check that uploaded file is actually a floor plan"
      ]
    },
    "partial_results": {
      "page_classifications": {...},
      "drawing_metadata": {...}
    }
  }
}
```

**Error Responses:**
```json
// 404 Not Found
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "No job found with ID: job_abc123xyz"
  }
}
```

---

### GET /api/v1/takeoffs/{job_id}/results

Get complete takeoff results (only available when status = "completed").

**Request:**
```http
GET /api/v1/takeoffs/{job_id}/results
Authorization: Bearer <token>

Query Parameters (optional):
- format: "json" | "summary" (default: "json")
- include_audit: boolean (default: false)
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123xyz",
    "takeoff_id": "takeoff_final_001",
    "generated_at": "2026-05-21T10:30:35Z",
    "project": {
      "project_id": "proj_456def",
      "project_name": "Office Building - Level 1",
      "project_type": "commercial",
      "location": "Boston, MA",
      "total_area_sqft": 9600
    },
    "summary": {
      "total_wall_area_sqft": 2880.0,
      "net_drywall_area_sqft": 4750.0,
      "total_linear_feet": 320.0,
      "total_walls": 15,
      "total_openings": 18,
      "total_material_cost": 8950.00,
      "total_labor_cost": 17645.00,
      "subtotal": 26595.00,
      "overhead_percent": 15,
      "overhead_amount": 3989.25,
      "profit_percent": 10,
      "profit_amount": 3058.43,
      "total_cost": 33642.68,
      "cost_per_sqft": 7.08
    },
    "walls": [
      {
        "id": "W1",
        "length_ft": 40.0,
        "height_ft": 9.0,
        "area_sqft": 360.0,
        "type": "exterior",
        "thickness_inches": 6.0
      }
      // ... more walls
    ],
    "openings": [
      {
        "id": "D1",
        "wall_id": "W1",
        "type": "door",
        "width_ft": 3.0,
        "height_ft": 7.0,
        "area_sqft": 21.0
      }
      // ... more openings
    ],
    "materials": {
      "framing": {
        "studs_16oc": {
          "quantity": 185,
          "unit": "pieces",
          "unit_cost": 6.50,
          "total_cost": 1202.50
        }
        // ... more items
      },
      "drywall": {...},
      "fasteners": {...},
      "finishing": {...}
    },
    "labor": {
      "tasks": [
        {
          "phase": "framing",
          "hours": 57.0,
          "rate_per_hour": 55.00,
          "cost": 3135.00
        }
        // ... more tasks
      ],
      "labor_summary": {
        "total_hours": 341.5,
        "total_labor_cost": 17645.00,
        "average_rate_per_hour": 51.68
      }
    },
    "line_items": [
      {
        "section": "01 - FRAMING",
        "items": [
          {
            "item_no": "01.01",
            "description": "2x4 Wood Studs @ 16\" OC",
            "quantity": 185,
            "unit": "EA",
            "unit_cost": 6.50,
            "total_cost": 1202.50
          }
          // ... more items
        ]
      }
      // ... more sections
    ],
    "quality_score": {
      "overall": 92,
      "wall_detection_confidence": 94,
      "opening_detection_confidence": 88
    }
  }
}
```

**With Audit Trail (`?include_audit=true`):**
```json
{
  "success": true,
  "data": {
    // ... all data above, plus:
    "audit_trail": {
      "stage_1_upload": {...},
      "stage_2_classification": {...},
      "stage_3_drawing_analysis": {...},
      "stage_4_wall_extraction": {...},
      "stage_5_opening_detection": {...},
      "stage_6_material_calculations": {...},
      "stage_7_labor_estimation": {...}
    }
  }
}
```

**Error Responses:**
```json
// 404 Not Found
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "No job found with ID: job_abc123xyz"
  }
}

// 409 Conflict - Job not completed
{
  "success": false,
  "error": {
    "code": "JOB_NOT_COMPLETED",
    "message": "Job is still processing. Current status: processing",
    "current_stage": "stage_4_wall_extraction",
    "progress_percent": 45,
    "status_url": "/api/v1/takeoffs/job_abc123xyz/status"
  }
}
```

---

### POST /api/v1/takeoffs/{job_id}/review

Submit user edits to detected walls/openings and recalculate.

**Request:**
```http
POST /api/v1/takeoffs/{job_id}/review
Authorization: Bearer <token>
Content-Type: application/json

{
  "walls": [
    {
      "id": "W1",
      "action": "update",
      "updates": {
        "length_ft": 42.0,
        "type": "interior"
      }
    },
    {
      "id": "W15",
      "action": "delete"
    },
    {
      "action": "add",
      "new_wall": {
        "length_ft": 18.0,
        "height_ft": 9.0,
        "type": "interior",
        "thickness_inches": 4.5
      }
    }
  ],
  "openings": [
    {
      "id": "D3",
      "action": "update",
      "updates": {
        "width_ft": 3.5
      }
    }
  ],
  "recalculate": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123xyz",
    "revision_id": "rev_002",
    "updated_at": "2026-05-21T11:15:30Z",
    "changes_applied": {
      "walls_updated": 1,
      "walls_deleted": 1,
      "walls_added": 1,
      "openings_updated": 1
    },
    "recalculation_status": "completed",
    "summary": {
      "total_walls": 15,
      "total_wall_area_sqft": 2920.0,
      "total_material_cost": 9150.00,
      "total_labor_cost": 18025.00,
      "total_cost": 34430.00,
      "cost_change": 787.32,
      "cost_change_percent": 2.34
    },
    "results_url": "/api/v1/takeoffs/job_abc123xyz/results"
  }
}
```

---

### DELETE /api/v1/takeoffs/{job_id}

Delete a takeoff job and all associated data.

**Request:**
```http
DELETE /api/v1/takeoffs/{job_id}
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Takeoff job deleted successfully",
  "deleted": {
    "job_id": "job_abc123xyz",
    "files_deleted": 1,
    "storage_freed_mb": 2.34
  }
}
```

---

### GET /api/v1/takeoffs

List all takeoff jobs for the authenticated user.

**Request:**
```http
GET /api/v1/takeoffs
Authorization: Bearer <token>

Query Parameters:
- status: "queued" | "processing" | "completed" | "failed" (optional filter)
- limit: number (default: 20, max: 100)
- offset: number (default: 0)
- sort: "created_at" | "updated_at" | "project_name" (default: "created_at")
- order: "asc" | "desc" (default: "desc")
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "job_id": "job_abc123xyz",
        "project_name": "Office Building - Level 1",
        "status": "completed",
        "created_at": "2026-05-21T10:30:00Z",
        "completed_at": "2026-05-21T10:30:35Z",
        "summary": {
          "total_walls": 15,
          "total_cost": 33642.68
        }
      },
      {
        "job_id": "job_def456uvw",
        "project_name": "Residential House",
        "status": "processing",
        "created_at": "2026-05-21T09:15:00Z",
        "current_stage": "stage_5_opening_detection",
        "progress_percent": 60
      }
      // ... more jobs
    ],
    "pagination": {
      "total": 48,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

## 2. Export Endpoints

### GET /api/v1/takeoffs/{job_id}/export/excel

Export takeoff to Excel spreadsheet.

**Request:**
```http
GET /api/v1/takeoffs/{job_id}/export/excel
Authorization: Bearer <token>

Query Parameters (optional):
- include_audit: boolean (default: false)
- include_drawings: boolean (default: false)
```

**Response (200 OK):**
```http
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="Takeoff_Office_Building_L1.xlsx"

<binary Excel file>
```

**Excel File Structure:**
- **Summary** sheet: Project info, totals, costs
- **Walls** sheet: All wall details
- **Openings** sheet: All door/window details
- **Materials** sheet: Material quantities and costs
- **Labor** sheet: Labor breakdown by task
- **Line Items** sheet: Complete takeoff in line-item format
- **Audit** sheet (if included): Processing audit trail

---

### GET /api/v1/takeoffs/{job_id}/export/pdf

Export takeoff to PDF proposal.

**Request:**
```http
GET /api/v1/takeoffs/{job_id}/export/pdf
Authorization: Bearer <token>

Query Parameters (optional):
- template: "standard" | "detailed" | "summary" (default: "standard")
- logo_url: string (optional - URL to company logo)
- company_name: string (optional)
- company_info: string (optional - contact details)
```

**Response (200 OK):**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="Proposal_Office_Building_L1.pdf"

<binary PDF file>
```

**PDF Structure:**
- Cover page with project details
- Summary of quantities
- Detailed line items by section
- Material breakdown
- Labor breakdown
- Terms and conditions
- Company contact info

---

### GET /api/v1/takeoffs/{job_id}/export/csv

Export takeoff to CSV format.

**Request:**
```http
GET /api/v1/takeoffs/{job_id}/export/csv
Authorization: Bearer <token>

Query Parameters:
- type: "line_items" | "materials" | "labor" | "walls" (required)
```

**Response (200 OK):**
```http
Content-Type: text/csv
Content-Disposition: attachment; filename="Takeoff_LineItems.csv"

Item No,Section,Description,Quantity,Unit,Unit Cost,Total Cost
01.01,01 - FRAMING,2x4 Wood Studs @ 16" OC,185,EA,6.50,1202.50
01.02,01 - FRAMING,2x4 Top Plate (double),320,LF,1.20,384.00
...
```

---

## 3. Manual Entry Endpoints

### POST /api/v1/takeoffs/manual/create

Create a takeoff from manual wall measurements (skip AI detection).

**Request:**
```http
POST /api/v1/takeoffs/manual/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_name": "Warehouse Addition",
  "project_type": "industrial",
  "project_metadata": {
    "default_ceiling_height": 10.0,
    "finishing_level": 2,
    "region": "midwest"
  },
  "walls": [
    {
      "name": "North Wall",
      "length_ft": 100.0,
      "height_ft": 10.0,
      "type": "exterior",
      "thickness_inches": 6.0
    },
    {
      "name": "South Wall",
      "length_ft": 100.0,
      "height_ft": 10.0,
      "type": "exterior",
      "thickness_inches": 6.0
    },
    {
      "name": "East Wall",
      "length_ft": 50.0,
      "height_ft": 10.0,
      "type": "exterior",
      "thickness_inches": 6.0
    },
    {
      "name": "West Wall",
      "length_ft": 50.0,
      "height_ft": 10.0,
      "type": "exterior",
      "thickness_inches": 6.0
    }
  ],
  "openings": [
    {
      "wall_name": "North Wall",
      "type": "door",
      "width_ft": 4.0,
      "height_ft": 8.0
    },
    {
      "wall_name": "East Wall",
      "type": "window",
      "width_ft": 6.0,
      "height_ft": 4.0
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_manual_789ghi",
    "status": "completed",
    "processing_time_seconds": 2.5,
    "summary": {
      "total_walls": 4,
      "total_openings": 2,
      "total_linear_feet": 300.0,
      "total_wall_area_sqft": 3000.0,
      "total_material_cost": 12500.00,
      "total_labor_cost": 24750.00,
      "total_cost": 47125.00
    },
    "results_url": "/api/v1/takeoffs/job_manual_789ghi/results"
  }
}
```

---

## 4. Configuration Endpoints

### GET /api/v1/config/regions

Get available regions and labor rate multipliers.

**Request:**
```http
GET /api/v1/config/regions
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "regions": [
      {
        "id": "northeast",
        "name": "Northeast",
        "states": ["MA", "NY", "NJ", "CT", "RI", "VT", "NH", "ME", "PA"],
        "labor_multiplier": 1.10,
        "base_rate": 55.00,
        "adjusted_rate": 60.50
      },
      {
        "id": "west",
        "name": "West Coast",
        "states": ["CA", "OR", "WA"],
        "labor_multiplier": 1.20,
        "base_rate": 55.00,
        "adjusted_rate": 66.00
      },
      {
        "id": "south",
        "name": "South",
        "states": ["TX", "FL", "GA", "NC", "SC", "TN", "AL", "MS", "LA"],
        "labor_multiplier": 0.95,
        "base_rate": 55.00,
        "adjusted_rate": 52.25
      },
      {
        "id": "midwest",
        "name": "Midwest",
        "states": ["IL", "OH", "MI", "IN", "WI", "MN", "IA", "MO"],
        "labor_multiplier": 1.00,
        "base_rate": 55.00,
        "adjusted_rate": 55.00
      }
    ],
    "default_region": "midwest",
    "base_rate_description": "National average drywall labor rate"
  }
}
```

---

### GET /api/v1/config/material-prices

Get current material pricing.

**Request:**
```http
GET /api/v1/config/material-prices

Query Parameters (optional):
- region: string (to get regional pricing)
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "region": "northeast",
    "effective_date": "2026-05-01",
    "prices": {
      "framing": {
        "stud_2x4_10ft": {
          "unit": "EA",
          "price": 6.50,
          "description": "2x4 Wood Stud, 10ft length"
        },
        "plate_2x4_lf": {
          "unit": "LF",
          "price": 1.20,
          "description": "2x4 Plate Stock per linear foot"
        }
      },
      "drywall": {
        "sheet_4x12_1_2": {
          "unit": "EA",
          "price": 18.50,
          "description": "1/2\" Drywall 4'x12' sheet"
        },
        "sheet_4x8_1_2": {
          "unit": "EA",
          "price": 12.00,
          "description": "1/2\" Drywall 4'x8' sheet"
        }
      },
      "fasteners": {
        "screws_1_5_8_lb": {
          "unit": "LB",
          "price": 8.50,
          "description": "#6 x 1-5/8\" Drywall Screws per pound"
        }
      },
      "finishing": {
        "joint_compound_gal": {
          "unit": "GAL",
          "price": 15.00,
          "description": "All-Purpose Joint Compound per gallon"
        },
        "paper_tape_roll": {
          "unit": "EA",
          "price": 3.50,
          "description": "Paper Joint Tape 250ft roll"
        }
      }
    }
  }
}
```

---

## 5. Health & Status Endpoints

### GET /api/v1/health

Overall API health check.

**Request:**
```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-21T10:45:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "storage": "healthy",
    "ai_service": "healthy",
    "cache": "healthy"
  },
  "uptime_seconds": 86400
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "timestamp": "2026-05-21T10:45:00Z",
  "services": {
    "database": "healthy",
    "storage": "unhealthy",
    "ai_service": "healthy",
    "cache": "healthy"
  },
  "errors": [
    {
      "service": "storage",
      "error": "S3 connection timeout"
    }
  ]
}
```

---

### GET /api/v1/usage/stats

Get current usage statistics for authenticated user.

**Request:**
```http
GET /api/v1/usage/stats
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": "user_123",
    "plan": "pro",
    "billing_period": {
      "start": "2026-05-01T00:00:00Z",
      "end": "2026-05-31T23:59:59Z"
    },
    "usage": {
      "jobs_created": 42,
      "jobs_limit": 100,
      "jobs_remaining": 58,
      "storage_used_mb": 1250,
      "storage_limit_mb": 5000
    },
    "api_calls": {
      "this_month": 156,
      "rate_limit_per_minute": 10
    }
  }
}
```

---

## 6. Webhook Configuration (Optional)

### POST /api/v1/webhooks/configure

Configure webhook for job status updates.

**Request:**
```http
POST /api/v1/webhooks/configure
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-domain.com/webhooks/takeoff-status",
  "events": ["job.completed", "job.failed"],
  "secret": "your_webhook_secret"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "webhook_id": "webhook_abc123",
    "url": "https://your-domain.com/webhooks/takeoff-status",
    "events": ["job.completed", "job.failed"],
    "status": "active",
    "created_at": "2026-05-21T10:50:00Z"
  }
}
```

**Webhook Payload (sent to your URL):**
```json
{
  "event": "job.completed",
  "timestamp": "2026-05-21T10:30:35Z",
  "data": {
    "job_id": "job_abc123xyz",
    "status": "completed",
    "summary": {
      "total_walls": 15,
      "total_cost": 33642.68
    },
    "results_url": "https://api.drywalltakeoff.com/v1/takeoffs/job_abc123xyz/results"
  },
  "signature": "sha256=..."
}
```

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context about the error",
    "timestamp": "2026-05-21T10:45:00Z",
    "request_id": "req_xyz789"
  }
}
```

**Common Error Codes:**

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Request validation failed |
| 400 | `INVALID_FILE_TYPE` | Unsupported file type |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 404 | `JOB_NOT_FOUND` | Takeoff job doesn't exist |
| 409 | `JOB_NOT_COMPLETED` | Job still processing |
| 413 | `FILE_TOO_LARGE` | File exceeds size limit |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily down |

---

## Rate Limits

| Plan | Jobs per Minute | API Calls per Minute | Storage |
|------|-----------------|----------------------|---------|
| Free | 2 | 20 | 100 MB |
| Starter | 5 | 60 | 1 GB |
| Pro | 10 | 120 | 5 GB |
| Enterprise | Custom | Custom | Custom |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1716291600
```

---

## Versioning

API versions are specified in the URL path: `/api/v1/`

**Version Support:**
- v1: Current (2026-05-21 - ongoing)
- v2: Future (TBD)

Breaking changes will result in a new version. Non-breaking changes (new fields, new endpoints) are added to existing versions.

---

**Document Version**: 1.0
**Last Updated**: 2026-05-21
**API Version**: v1

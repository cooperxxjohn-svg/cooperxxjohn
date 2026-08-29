# Drywall Takeoff System - Complete Workflow Design

## Executive Summary

This document defines the complete backend processing pipeline for an AI-powered drywall takeoff system. The system processes floor plan PDFs/images through multiple stages to automatically extract walls, detect openings, calculate materials, estimate labor, and generate detailed takeoffs.

**Key Principles:**
- **Deterministic where possible**: Use code-based calculations for all material and labor math
- **AI only where needed**: Use Claude Sonnet for vision tasks (wall detection, opening detection)
- **Auditable**: Every stage produces structured output that can be reviewed
- **Fault-tolerant**: Graceful degradation with partial results and manual override options

---

## 1. Processing Pipeline Overview

The system consists of 8 sequential stages:

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Upload & Storage                                        │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  PDF/Image files from user                               │
│ Output: S3 URLs, processing job record                          │
│ Time:   ~2 seconds                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Document Classification                                │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  S3 URLs                                                  │
│ Output: page_classifications.json                               │
│ Time:   ~5-10 seconds (AI-based)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: Drawing Analysis                                       │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  Floor plan pages                                        │
│ Output: drawing_metadata.json (scale, units, dimensions)        │
│ Time:   ~5-8 seconds (AI-based)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: Wall Extraction                                        │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  Floor plan pages + drawing_metadata                     │
│ Output: walls.json (wall segments with coordinates & lengths)   │
│ Time:   ~10-15 seconds (AI-based, most critical stage)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: Opening Detection                                      │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  Floor plan pages + walls.json                           │
│ Output: openings.json (doors, windows with dimensions)          │
│ Time:   ~8-12 seconds (AI-based)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: Material Calculations                                  │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  walls.json + openings.json + project_metadata           │
│ Output: materials.json (studs, drywall, screws, mud, etc.)      │
│ Time:   ~1-2 seconds (deterministic calculation)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: Labor Estimation                                       │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  materials.json + project_metadata                       │
│ Output: labor.json (hours by task, crew size, duration)         │
│ Time:   ~1 second (deterministic calculation)                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: Takeoff Generation                                     │
│ ─────────────────────────────────────────────────────────────   │
│ Input:  All stage outputs                                       │
│ Output: takeoff.json (complete estimate with line items)        │
│ Time:   ~1 second (data aggregation)                            │
└─────────────────────────────────────────────────────────────────┘

Total Processing Time (Fast Mode): 30-40 seconds
Total Processing Time (Deep Mode): 60-90 seconds
```

---

## 2. Detailed Stage Definitions

### STAGE 1: Upload & Storage

**Purpose**: Securely receive files, store them, and initialize processing job

**Input Data:**
```json
{
  "project_id": "proj_abc123",
  "files": [
    {
      "type": "floor_plan",
      "filename": "Level1_FloorPlan.pdf",
      "file_data": "<binary>",
      "content_type": "application/pdf"
    }
  ],
  "project_metadata": {
    "project_name": "Office Building - Level 1",
    "project_type": "commercial",
    "default_ceiling_height": 9.0,
    "finishing_level": 3,
    "region": "northeast",
    "default_stud_spacing": 16
  }
}
```

**Processing Logic:**
1. Validate file types (PDF, PNG, JPG only)
2. Validate file sizes (max 50MB per file)
3. Generate unique file IDs
4. Upload to S3 bucket (or local storage for development)
5. Create processing job record in database
6. Initialize job status tracking
7. Queue job for Stage 2

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "status": "queued",
  "files": [
    {
      "file_id": "file_001",
      "original_filename": "Level1_FloorPlan.pdf",
      "storage_url": "s3://drywall-uploads/proj_abc123/file_001.pdf",
      "file_size": 2457600,
      "page_count": 1,
      "uploaded_at": "2026-05-21T10:30:00Z"
    }
  ],
  "project_metadata": {...}
}
```

**Error Handling:**
- Invalid file type → HTTP 400 with allowed types
- File too large → HTTP 413 with size limit
- Upload failure → Retry 3x with exponential backoff
- S3 unavailable → Fall back to local storage with warning

**Validation Rules:**
- At least 1 file must be provided
- Total upload size < 200MB
- Filename must not contain special characters
- Project ID must exist in database

---

### STAGE 2: Document Classification

**Purpose**: Classify each page of uploaded PDFs to identify floor plans vs other drawing types

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "files": [
    {
      "file_id": "file_001",
      "storage_url": "s3://...",
      "page_count": 5
    }
  ]
}
```

**Processing Logic:**
1. Convert PDF pages to images (300 DPI)
2. For each page, send to Claude Sonnet with classification prompt:
   ```
   Classify this construction drawing page into one of these categories:
   - floor_plan: Shows walls, rooms, doors, windows in plan view
   - reflected_ceiling_plan: Shows ceiling layout, light fixtures
   - wall_section: Vertical cross-section showing wall construction
   - wall_elevation: Vertical view of wall face
   - detail_drawing: Close-up construction detail
   - specification_text: Text-based specifications
   - schedule_table: Door/window/finish schedules
   - cover_sheet: Title block, index, general notes
   - other: Anything else
   
   Return JSON: {"page_type": "floor_plan", "confidence": 0.95, "notes": "..."}
   ```
3. Store classifications for each page
4. Flag pages for subsequent processing

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "page_classifications": [
    {
      "file_id": "file_001",
      "page_number": 1,
      "page_type": "floor_plan",
      "confidence": 0.98,
      "notes": "Clear floor plan showing walls, doors, windows. Scale: 1/4\" = 1'-0\"",
      "recommended_for_extraction": true
    },
    {
      "file_id": "file_001",
      "page_number": 2,
      "page_type": "wall_section",
      "confidence": 0.92,
      "notes": "Wall section detail showing stud spacing and drywall layers",
      "recommended_for_extraction": false
    }
  ],
  "summary": {
    "total_pages": 5,
    "floor_plan_pages": 2,
    "processable_pages": 2
  }
}
```

**Error Handling:**
- AI API failure → Retry 3x, then mark page as "unclassified"
- Low confidence (<0.7) → Flag for manual review
- No floor plans found → Warning to user, proceed with manual mode

**Validation Rules:**
- Confidence score must be 0-1
- At least 1 floor_plan page should be found (warn if not)

---

### STAGE 3: Drawing Analysis

**Purpose**: Extract metadata from floor plan pages (scale, units, dimensions)

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "floor_plan_pages": [
    {
      "file_id": "file_001",
      "page_number": 1,
      "storage_url": "s3://..."
    }
  ]
}
```

**Processing Logic:**
1. For each floor plan page, send to Claude Sonnet with analysis prompt:
   ```
   Analyze this floor plan and extract:
   1. Scale (e.g., "1/4 inch = 1 foot" or "1:48")
   2. Units (imperial: feet/inches OR metric: meters)
   3. Overall dimensions of the floor plan area
   4. Any dimension annotations visible on the drawing
   5. Grid system (if present: A-Z, 1-20, etc.)
   
   Return structured JSON with this information.
   ```

2. Parse AI response into structured metadata
3. Validate scale and units are consistent
4. Extract any dimension callouts for validation later

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "drawing_metadata": [
    {
      "file_id": "file_001",
      "page_number": 1,
      "scale": {
        "type": "architectural",
        "ratio": "1/4\" = 1'-0\"",
        "numeric_ratio": 48,
        "units": "imperial"
      },
      "overall_dimensions": {
        "length_ft": 120.0,
        "width_ft": 80.0,
        "area_sqft": 9600
      },
      "dimension_callouts": [
        {"label": "Overall Length", "value": 120.0, "unit": "ft"},
        {"label": "Overall Width", "value": 80.0, "unit": "ft"}
      ],
      "grid_system": {
        "present": true,
        "horizontal": ["A", "B", "C", "D", "E"],
        "vertical": ["1", "2", "3", "4", "5", "6"]
      }
    }
  ]
}
```

**Error Handling:**
- No scale detected → Warn user, assume 1/4" = 1'-0" (common default)
- Inconsistent units → Flag for manual review
- Missing dimensions → Proceed with wall detection anyway

**Validation Rules:**
- Scale ratio must be reasonable (10-200 range)
- Overall dimensions must be positive
- Units must be "imperial" or "metric"

---

### STAGE 4: Wall Extraction (CRITICAL STAGE)

**Purpose**: Detect and extract wall segments with precise measurements

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "floor_plan_pages": [...],
  "drawing_metadata": [...]
}
```

**Processing Logic:**
1. For each floor plan page, send to Claude Sonnet with detailed extraction prompt:
   ```
   Analyze this floor plan and extract ALL wall segments.
   
   For each wall:
   1. Identify start point and end point (x, y coordinates in pixels)
   2. Calculate actual length based on the scale: [scale from metadata]
   3. Determine wall type:
      - interior: Interior partition wall
      - exterior: Exterior/perimeter wall
      - load_bearing: Structural wall (if identifiable)
   4. Estimate wall height (use default: [ceiling_height] unless specified)
   5. Detect wall thickness in inches (typical: 4.5", 6", 8")
   6. Identify wall material hints (concrete, masonry, wood frame)
   
   IMPORTANT:
   - Trace each wall segment individually (even if they connect)
   - Include wall intersections and corners
   - Note confidence level for each wall
   - Flag any unclear or ambiguous sections
   
   Return JSON array of wall objects.
   ```

2. Parse AI response and validate wall data
3. Post-process walls:
   - Merge co-linear wall segments if appropriate
   - Detect wall intersections (corners, T-junctions)
   - Calculate total linear feet of walls
   - Calculate total wall area (length × height)

4. Run sanity checks:
   - Total wall area vs floor area ratio (should be 1.5-3.0×)
   - Check for disconnected wall segments
   - Validate wall lengths are reasonable

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "walls": [
    {
      "id": "W1",
      "page_id": "file_001_p1",
      "start_point": {"x": 100, "y": 200, "grid": "A1"},
      "end_point": {"x": 1100, "y": 200, "grid": "E1"},
      "length_ft": 40.0,
      "height_ft": 9.0,
      "wall_area_sqft": 360.0,
      "type": "exterior",
      "thickness_inches": 6.0,
      "material_hint": "wood_frame",
      "confidence": 0.97,
      "notes": "North exterior wall"
    },
    {
      "id": "W2",
      "page_id": "file_001_p1",
      "start_point": {"x": 100, "y": 200, "grid": "A1"},
      "end_point": {"x": 100, "y": 800, "grid": "A4"},
      "length_ft": 24.0,
      "height_ft": 9.0,
      "wall_area_sqft": 216.0,
      "type": "exterior",
      "thickness_inches": 6.0,
      "material_hint": "wood_frame",
      "confidence": 0.95,
      "notes": "West exterior wall"
    },
    {
      "id": "W3",
      "page_id": "file_001_p1",
      "start_point": {"x": 500, "y": 400},
      "end_point": {"x": 900, "y": 400},
      "length_ft": 16.0,
      "height_ft": 9.0,
      "wall_area_sqft": 144.0,
      "type": "interior",
      "thickness_inches": 4.5,
      "material_hint": "wood_frame",
      "confidence": 0.89,
      "notes": "Interior partition wall"
    }
  ],
  "wall_summary": {
    "total_walls": 15,
    "total_linear_feet": 320.0,
    "total_wall_area_sqft": 2880.0,
    "exterior_walls": 4,
    "interior_walls": 11,
    "average_height": 9.0,
    "floor_area_sqft": 9600,
    "wall_to_floor_ratio": 0.30
  },
  "quality_checks": {
    "disconnected_segments": 0,
    "low_confidence_walls": 2,
    "ratio_check": "pass",
    "warnings": [
      "Wall W3 has confidence < 0.90, review recommended"
    ]
  }
}
```

**Error Handling:**
- No walls detected → CRITICAL error, prompt for manual input
- Low confidence walls → Flag for review but continue
- Inconsistent scale application → Attempt auto-correction
- AI timeout → Retry with simplified prompt

**Validation Rules:**
- Each wall must have length > 1 ft and < 200 ft
- Wall height must be 7-20 ft (reasonable range)
- Total walls must be > 0
- Wall-to-floor ratio should be 0.2-0.5 (warn if outside)

---

### STAGE 5: Opening Detection

**Purpose**: Detect doors and windows on walls, calculate area reductions

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "floor_plan_pages": [...],
  "walls": [...]
}
```

**Processing Logic:**
1. For each floor plan page with walls, send to Claude Sonnet:
   ```
   Analyze this floor plan and detect ALL openings (doors and windows).
   
   Wall locations are provided for reference: [wall list]
   
   For each opening:
   1. Identify which wall it belongs to (match to wall ID)
   2. Determine type: door, window, sliding_door, french_door, etc.
   3. Extract dimensions:
      - Width (opening width)
      - Height (opening height, or use standard: doors 7ft, windows vary)
   4. Note if it's a rough opening (RO) or finished opening (FO)
   5. Detect any special features (sidelights, transoms, etc.)
   
   Return JSON array of opening objects.
   ```

2. Parse AI response and match openings to walls
3. Calculate opening areas
4. Validate opening sizes against standards:
   - Doors: typically 2'8" to 4'0" wide, 6'8" to 8'0" tall
   - Windows: vary widely, but should fit within wall dimensions

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "openings": [
    {
      "id": "D1",
      "wall_id": "W1",
      "type": "door",
      "subtype": "single_swing",
      "width_ft": 3.0,
      "height_ft": 7.0,
      "area_sqft": 21.0,
      "rough_opening": true,
      "rough_opening_size": {
        "width_ft": 3.167,
        "height_ft": 7.167
      },
      "position_on_wall": "center",
      "confidence": 0.92,
      "notes": "Standard single door, main entry"
    },
    {
      "id": "W1",
      "wall_id": "W2",
      "type": "window",
      "subtype": "double_hung",
      "width_ft": 4.0,
      "height_ft": 5.0,
      "area_sqft": 20.0,
      "rough_opening": true,
      "rough_opening_size": {
        "width_ft": 4.167,
        "height_ft": 5.167
      },
      "position_on_wall": "3ft from left edge",
      "confidence": 0.88,
      "notes": "Standard window on west wall"
    }
  ],
  "opening_summary": {
    "total_openings": 18,
    "total_doors": 12,
    "total_windows": 6,
    "total_opening_area_sqft": 340.0,
    "drywall_area_reduction_sqft": 340.0
  },
  "quality_checks": {
    "orphan_openings": 0,
    "oversized_openings": 0,
    "warnings": []
  }
}
```

**Error Handling:**
- Opening doesn't match any wall → Flag as "orphan", attempt best match
- Oversized opening (> wall dimensions) → Flag for review
- Low confidence → Continue but flag

**Validation Rules:**
- Opening width must be < wall length
- Opening height must be < wall height
- Opening area > 0
- Each opening must reference a valid wall_id

---

### STAGE 6: Material Calculations (DETERMINISTIC)

**Purpose**: Calculate precise material quantities using deterministic formulas

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "walls": [...],
  "openings": [...],
  "project_metadata": {
    "default_ceiling_height": 9.0,
    "finishing_level": 3,
    "default_stud_spacing": 16,
    "drywall_thickness": 0.5
  }
}
```

**Processing Logic (100% Code-Based):**

```python
# Pseudo-code for material calculations

def calculate_materials(walls, openings, metadata):
    # 1. Calculate wall areas with opening deductions
    total_wall_area = sum(w.area for w in walls)
    total_opening_area = sum(o.area for o in openings)
    net_wall_area = total_wall_area - total_opening_area
    
    # Double for both sides of wall (2 layers drywall per wall)
    total_drywall_area = net_wall_area * 2
    
    # 2. Calculate drywall sheets
    # Use 4x12 sheets (48 sqft each) primarily
    # Use 4x8 sheets (32 sqft each) for waste/cuts
    waste_factor = 1.15  # 15% waste
    
    total_sheets_needed = (total_drywall_area * waste_factor) / 48
    sheets_4x12 = int(total_sheets_needed * 0.85)
    sheets_4x8 = int((total_sheets_needed - sheets_4x12) * 1.5)
    
    # 3. Calculate framing (studs and tracks)
    total_linear_feet = sum(w.length for w in walls)
    
    stud_spacing = metadata.stud_spacing  # 16" or 24" OC
    studs_per_foot = 12 / stud_spacing
    total_studs = int(total_linear_feet * studs_per_foot * 1.10)  # 10% extra
    
    # Top and bottom tracks (double for plates)
    total_track_feet = total_linear_feet * 2
    
    # 4. Calculate fasteners
    # Screws: 1 per sqft for field, 1.5 per sqft for edges
    screws_per_sheet = 60  # average
    total_screws = int(total_sheets_needed * screws_per_sheet)
    screws_pounds = total_screws / 400  # ~400 screws per lb
    
    # 5. Calculate finishing materials (for Level 3 finish)
    # Joint compound: 0.05 gal per sqft per coat (3 coats for Level 3)
    joint_compound_gal = (total_drywall_area * 0.05 * 3)
    
    # Paper tape: linear feet of joints
    # Approximate: perimeter of each sheet + internal seams
    total_joints_lf = total_sheets_needed * 50  # average
    paper_tape_lf = total_joints_lf
    
    # Corner bead: all outside corners
    corner_bead_lf = calculate_corner_bead(walls)
    
    return {
        "framing": {...},
        "drywall": {...},
        "fasteners": {...},
        "finishing": {...}
    }
```

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "materials": {
    "framing": {
      "studs_16oc": {
        "item": "2x4 Wood Studs @ 16\" OC",
        "quantity": 185,
        "unit": "pieces",
        "length": "10ft",
        "notes": "Includes 10% waste for cuts and blocking"
      },
      "studs_24oc": {
        "item": "2x4 Wood Studs @ 24\" OC",
        "quantity": 0,
        "unit": "pieces",
        "length": "10ft"
      },
      "top_plate": {
        "item": "2x4 Top Plate",
        "quantity": 320,
        "unit": "lf",
        "notes": "Double top plate for all walls"
      },
      "bottom_plate": {
        "item": "2x4 Bottom Plate",
        "quantity": 320,
        "unit": "lf"
      },
      "header_material": {
        "item": "2x6 Header Stock",
        "quantity": 85,
        "unit": "lf",
        "notes": "For door and window headers"
      }
    },
    "drywall": {
      "sheets_4x12_1_2": {
        "item": "1/2\" Drywall 4'x12' Sheets",
        "quantity": 95,
        "unit": "sheets",
        "sqft": 4560,
        "coverage_sqft": 3970,
        "waste_percent": 15
      },
      "sheets_4x8_1_2": {
        "item": "1/2\" Drywall 4'x8' Sheets",
        "quantity": 28,
        "unit": "sheets",
        "sqft": 896,
        "coverage_sqft": 780,
        "waste_percent": 15
      },
      "moisture_resistant": {
        "item": "1/2\" Moisture-Resistant Drywall 4'x8'",
        "quantity": 0,
        "unit": "sheets",
        "notes": "For bathrooms/kitchens if specified"
      }
    },
    "fasteners": {
      "screws_1_5_8": {
        "item": "#6 x 1-5/8\" Drywall Screws",
        "quantity": 18,
        "unit": "lbs",
        "approx_count": 7200
      },
      "screws_2_1_2": {
        "item": "#6 x 2-1/2\" Drywall Screws",
        "quantity": 3,
        "unit": "lbs",
        "notes": "For double layers or fire-rated assemblies"
      }
    },
    "finishing": {
      "joint_compound_level3": {
        "item": "All-Purpose Joint Compound",
        "quantity": 48,
        "unit": "gal",
        "coverage": "~80 sqft per gallon per coat",
        "coats": 3,
        "notes": "Level 3 finish (3 coats)"
      },
      "paper_tape": {
        "item": "Paper Joint Tape",
        "quantity": 1200,
        "unit": "lf",
        "rolls": 24,
        "notes": "50 ft per roll standard"
      },
      "corner_bead_metal": {
        "item": "Metal Corner Bead",
        "quantity": 180,
        "unit": "lf",
        "pieces": 18,
        "notes": "10 ft lengths standard"
      },
      "sanding_supplies": {
        "item": "Sanding Screens/Paper Assortment",
        "quantity": 1,
        "unit": "kit"
      }
    },
    "adhesives": {
      "construction_adhesive": {
        "item": "Construction Adhesive (tubes)",
        "quantity": 12,
        "unit": "tubes",
        "notes": "For bottom plates and blocking"
      }
    }
  },
  "material_summary": {
    "total_drywall_sqft": 5456,
    "net_coverage_sqft": 4750,
    "waste_factor": 1.15,
    "total_linear_feet_framing": 320,
    "total_studs": 185,
    "estimated_material_cost": 8950.00,
    "cost_per_sqft": 1.88
  },
  "calculation_metadata": {
    "calculated_at": "2026-05-21T10:35:45Z",
    "calculation_method": "deterministic",
    "assumptions": {
      "stud_spacing": "16 inches OC",
      "drywall_thickness": "1/2 inch",
      "finish_level": 3,
      "waste_factor": 15,
      "sheet_size_primary": "4x12",
      "sheet_size_secondary": "4x8"
    }
  }
}
```

**Error Handling:**
- Division by zero → Use defaults
- Negative quantities → Flag data error in previous stage
- Unrealistic quantities → Warn user (e.g., > 10x typical)

**Validation Rules:**
- All quantities must be >= 0
- Waste factor must be 1.0-1.3 (0-30%)
- Material costs must be reasonable

---

### STAGE 7: Labor Estimation (DETERMINISTIC)

**Purpose**: Calculate labor hours and costs by task

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "materials": {...},
  "project_metadata": {
    "region": "northeast",
    "finishing_level": 3
  }
}
```

**Processing Logic (100% Code-Based):**

```python
# Industry-standard labor productivity rates

LABOR_RATES = {
    "framing": {
        "rate_per_sqft": 0.012,  # hours per sqft
        "description": "Frame walls, install studs, plates, headers"
    },
    "hanging": {
        "rate_per_sqft": 0.018,  # hours per sqft
        "description": "Hang drywall sheets, cut openings, screw off"
    },
    "taping_level3": {
        "coat1": 0.015,  # First coat (tape embed)
        "coat2": 0.012,  # Second coat
        "coat3": 0.010,  # Final coat
        "description": "Apply joint compound, tape, sand"
    },
    "corner_bead": {
        "rate_per_lf": 0.05,  # hours per linear foot
        "description": "Install metal corner bead"
    },
    "cleanup": {
        "rate_per_sqft": 0.003,
        "description": "Clean up debris, vacuum, dispose"
    }
}

def calculate_labor(materials, metadata):
    total_sqft = materials["material_summary"]["net_coverage_sqft"]
    corner_bead_lf = materials["finishing"]["corner_bead_metal"]["quantity"]
    
    # Calculate hours by task
    framing_hours = total_sqft * LABOR_RATES["framing"]["rate_per_sqft"]
    hanging_hours = total_sqft * LABOR_RATES["hanging"]["rate_per_sqft"]
    
    taping_hours = (
        total_sqft * LABOR_RATES["taping_level3"]["coat1"] +
        total_sqft * LABOR_RATES["taping_level3"]["coat2"] +
        total_sqft * LABOR_RATES["taping_level3"]["coat3"]
    )
    
    corner_bead_hours = corner_bead_lf * LABOR_RATES["corner_bead"]["rate_per_lf"]
    cleanup_hours = total_sqft * LABOR_RATES["cleanup"]["rate_per_sqft"]
    
    total_hours = (framing_hours + hanging_hours + taping_hours + 
                   corner_bead_hours + cleanup_hours)
    
    # Apply regional labor rate multiplier
    regional_rate = get_regional_labor_rate(metadata["region"])
    
    return {
        "tasks": [...],
        "total_hours": total_hours,
        "labor_cost": total_hours * regional_rate
    }
```

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "labor": {
    "tasks": [
      {
        "id": "L1",
        "phase": "framing",
        "description": "Frame all walls - install studs, plates, headers",
        "hours": 57.0,
        "rate_per_hour": 55.00,
        "cost": 3135.00,
        "crew_size": 2,
        "duration_days": 3.5,
        "notes": "Includes layout, cutting, assembly, plumbing/blocking"
      },
      {
        "id": "L2",
        "phase": "hanging",
        "description": "Hang drywall sheets on all surfaces",
        "hours": 85.5,
        "rate_per_hour": 55.00,
        "cost": 4702.50,
        "crew_size": 2,
        "duration_days": 5.0,
        "notes": "Includes measuring, cutting, lifting, screwing, cleanup"
      },
      {
        "id": "L3",
        "phase": "taping_coat1",
        "description": "First coat - tape embed",
        "hours": 71.25,
        "rate_per_hour": 50.00,
        "cost": 3562.50,
        "crew_size": 2,
        "duration_days": 4.5,
        "notes": "Embed tape in joints, first coat on fasteners"
      },
      {
        "id": "L4",
        "phase": "taping_coat2",
        "description": "Second coat - fill coat",
        "hours": 57.0,
        "rate_per_hour": 50.00,
        "cost": 2850.00,
        "crew_size": 2,
        "duration_days": 3.5,
        "notes": "Fill all joints and fasteners, feather edges"
      },
      {
        "id": "L5",
        "phase": "taping_coat3",
        "description": "Final coat and sanding",
        "hours": 47.5,
        "rate_per_hour": 50.00,
        "cost": 2375.00,
        "crew_size": 2,
        "duration_days": 3.0,
        "notes": "Final skim coat, sand smooth, Level 3 finish"
      },
      {
        "id": "L6",
        "phase": "corner_bead",
        "description": "Install metal corner beads",
        "hours": 9.0,
        "rate_per_hour": 50.00,
        "cost": 450.00,
        "crew_size": 1,
        "duration_days": 1.0,
        "notes": "All outside corners, archways"
      },
      {
        "id": "L7",
        "phase": "cleanup",
        "description": "Final cleanup and debris removal",
        "hours": 14.25,
        "rate_per_hour": 40.00,
        "cost": 570.00,
        "crew_size": 2,
        "duration_days": 1.0,
        "notes": "Sweep, vacuum, haul debris"
      }
    ],
    "labor_summary": {
      "total_hours": 341.5,
      "total_labor_cost": 17645.00,
      "average_rate_per_hour": 51.68,
      "total_duration_days": 21.5,
      "recommended_crew_size": 2,
      "hours_per_sqft": 0.072
    },
    "regional_adjustments": {
      "region": "northeast",
      "base_rate": 50.00,
      "regional_multiplier": 1.10,
      "adjusted_rate": 55.00,
      "notes": "Northeast rates ~10% above national average"
    }
  }
}
```

**Error Handling:**
- Missing material data → Use defaults based on wall area
- Invalid region → Use national average rates
- Unrealistic hours → Flag for review

**Validation Rules:**
- Total hours must be > 0
- Hours per sqft should be 0.05-0.15 (typical range)
- Labor cost must be >= material cost * 0.8 (sanity check)

---

### STAGE 8: Takeoff Generation

**Purpose**: Combine all data into final takeoff document

**Input Data:**
```json
{
  "job_id": "job_xyz789",
  "walls": {...},
  "openings": {...},
  "materials": {...},
  "labor": {...},
  "project_metadata": {...}
}
```

**Processing Logic:**
1. Aggregate all data from previous stages
2. Generate line items in standard takeoff format
3. Calculate totals and subtotals
4. Apply markup/overhead if specified
5. Generate summary report
6. Create audit trail with all stage outputs

**Output Data:**
```json
{
  "job_id": "job_xyz789",
  "takeoff_id": "takeoff_final_001",
  "generated_at": "2026-05-21T10:36:00Z",
  "project": {
    "project_id": "proj_abc123",
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
  "line_items": [
    {
      "section": "01 - FRAMING",
      "items": [
        {
          "item_no": "01.01",
          "description": "2x4 Wood Studs @ 16\" OC, 10ft lengths",
          "quantity": 185,
          "unit": "EA",
          "unit_cost": 6.50,
          "total_cost": 1202.50,
          "type": "material"
        },
        {
          "item_no": "01.02",
          "description": "2x4 Top Plate (double)",
          "quantity": 320,
          "unit": "LF",
          "unit_cost": 1.20,
          "total_cost": 384.00,
          "type": "material"
        },
        {
          "item_no": "01.03",
          "description": "Labor - Frame walls",
          "quantity": 57.0,
          "unit": "HR",
          "unit_cost": 55.00,
          "total_cost": 3135.00,
          "type": "labor"
        }
      ],
      "section_total": 8950.00
    },
    {
      "section": "02 - DRYWALL",
      "items": [...]
    },
    {
      "section": "03 - FINISHING",
      "items": [...]
    }
  ],
  "audit_trail": {
    "stage_1_upload": {...},
    "stage_2_classification": {...},
    "stage_3_drawing_analysis": {...},
    "stage_4_wall_extraction": {...},
    "stage_5_opening_detection": {...},
    "stage_6_material_calculations": {...},
    "stage_7_labor_estimation": {...}
  },
  "quality_score": {
    "overall": 92,
    "wall_detection_confidence": 94,
    "opening_detection_confidence": 88,
    "calculation_accuracy": 100,
    "notes": "High confidence extraction, all validations passed"
  }
}
```

**Error Handling:**
- Missing stage data → Use defaults and flag in report
- Calculation errors → Include error log in audit trail

**Validation Rules:**
- All required sections must be present
- Total cost must equal sum of line items
- All referenced IDs must exist

---

## 3. Processing Modes

### FAST Mode (30-40 seconds)
- Single floor plan page only
- AI detection with standard confidence thresholds
- Basic material calculations
- Standard labor rates
- **Use case**: Quick preliminary estimates

### DEEP Mode (60-90 seconds)
- Multiple pages processed
- Cross-reference between drawings
- Specification parsing (if text pages present)
- Advanced reconciliation between pages
- Higher confidence thresholds (more AI iterations)
- **Use case**: Final detailed takeoffs

### MANUAL Mode (5 seconds)
- Skip AI detection stages (2-5)
- User provides wall measurements directly
- Jump straight to material calculation (stage 6)
- **Use case**: When drawings are unclear or user has measurements

---

## 4. Error Handling Strategy

### Retry Logic
```python
@retry(max_attempts=3, backoff_factor=2)
def call_ai_service(prompt, image):
    # Exponential backoff: 2s, 4s, 8s
    response = anthropic.messages.create(...)
    return response
```

### Graceful Degradation
- If wall detection fails → Offer manual input mode
- If opening detection fails → Proceed without openings, warn user
- If classification fails → Assume all pages are floor plans
- If scale detection fails → Use default 1/4" = 1'-0"

### Partial Results
- Return data from successful stages even if later stages fail
- Example: If Stage 6 fails, still return walls and openings data
- User can review/edit and trigger recalculation

### User Override
- Allow manual corrections at any stage
- Store both AI-detected and user-corrected values
- Recalculate downstream stages when upstream is edited

---

## 5. Quality Control & Validation

### After Each Stage
```python
def validate_stage_output(stage_name, output_data):
    validation_rules = STAGE_VALIDATIONS[stage_name]
    
    errors = []
    warnings = []
    
    for rule in validation_rules:
        result = rule.check(output_data)
        if result.is_error:
            errors.append(result)
        elif result.is_warning:
            warnings.append(result)
    
    return ValidationResult(errors, warnings)
```

### Cross-Stage Validations
- **Wall area vs floor area**: Ratio should be 0.2-0.5
- **Opening area vs wall area**: Openings should be < 30% of wall area
- **Material quantities vs industry norms**: Compare to sqft benchmarks
- **Labor hours vs industry standards**: Validate productivity rates

### Confidence Scoring
```json
{
  "overall_confidence": 0.92,
  "stage_confidences": {
    "classification": 0.95,
    "wall_extraction": 0.91,
    "opening_detection": 0.88,
    "material_calc": 1.0,
    "labor_calc": 1.0
  },
  "quality_flags": [
    "2 walls with confidence < 0.90",
    "1 opening could not be matched to wall"
  ]
}
```

---

## 6. Performance Optimization

### Caching Strategy
- Cache AI responses for identical images (hash-based)
- Cache material calculation results for common configurations
- Cache regional labor rates

### Parallel Processing
- Process multiple pages in parallel (Stage 2-5)
- Run material and labor calculations in parallel (Stage 6-7)

### Database Indexing
- Index on job_id for fast status lookups
- Index on project_id for project history
- Index on created_at for reporting

---

## Next Documents

This workflow design should be accompanied by:

1. **PROCESSING_PIPELINE.md** - Technical implementation details
2. **API_ENDPOINTS.md** - Complete API specifications
3. **DATA_MODELS.md** - JSON schemas for all data structures
4. **DATABASE_SCHEMA.md** - PostgreSQL schema design

---

**Document Version**: 1.0
**Last Updated**: 2026-05-21
**Status**: Design Complete - Ready for Implementation

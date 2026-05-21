# Drywall Takeoff System - Data Models & JSON Schemas

Complete JSON schemas for all data structures used throughout the processing pipeline.

---

## Core Data Models

### 1. ProcessingJob

The main job record that tracks a takeoff from upload to completion.

```typescript
interface ProcessingJob {
  job_id: string;                    // Unique job identifier
  project_id: string;                // Associated project ID
  user_id: string;                   // User who created the job
  status: JobStatus;                 // Current status
  current_stage: ProcessingStage;    // Current processing stage
  progress_percent: number;          // Overall progress (0-100)
  
  // Timestamps
  created_at: string;                // ISO 8601 timestamp
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
  
  // Configuration
  processing_mode: ProcessingMode;   // "fast" | "deep" | "manual"
  project_metadata: ProjectMetadata;
  
  // Input files
  input_files: FileUpload[];
  
  // Stage outputs (populated as processing proceeds)
  page_classifications?: PageClassification[];
  drawing_metadata?: DrawingMetadata[];
  walls?: Wall[];
  openings?: Opening[];
  materials?: MaterialCalculation;
  labor?: LaborEstimation;
  takeoff?: Takeoff;
  
  // Error tracking
  errors?: ProcessingError[];
  warnings?: ProcessingWarning[];
  
  // Quality metrics
  quality_score?: QualityScore;
  
  // Audit trail
  audit_trail?: AuditTrail;
}

type JobStatus = 
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

type ProcessingStage = 
  | "stage_1_upload"
  | "stage_2_classification"
  | "stage_3_drawing_analysis"
  | "stage_4_wall_extraction"
  | "stage_5_opening_detection"
  | "stage_6_material_calculations"
  | "stage_7_labor_estimation"
  | "stage_8_takeoff_generation";

type ProcessingMode = "fast" | "deep" | "manual";
```

**Example JSON:**
```json
{
  "job_id": "job_abc123xyz",
  "project_id": "proj_456def",
  "user_id": "user_789ghi",
  "status": "completed",
  "current_stage": "stage_8_takeoff_generation",
  "progress_percent": 100,
  "created_at": "2026-05-21T10:30:00Z",
  "started_at": "2026-05-21T10:30:02Z",
  "completed_at": "2026-05-21T10:30:35Z",
  "processing_mode": "fast",
  "project_metadata": {
    "project_name": "Office Building - Level 1",
    "project_type": "commercial",
    "default_ceiling_height": 9.0,
    "finishing_level": 3,
    "region": "northeast",
    "default_stud_spacing": 16
  },
  "input_files": [...],
  "walls": [...],
  "quality_score": {
    "overall": 92
  }
}
```

---

### 2. ProjectMetadata

Configuration and metadata for the construction project.

```typescript
interface ProjectMetadata {
  project_name: string;
  project_type: ProjectType;
  
  // Default dimensions
  default_ceiling_height: number;    // feet (e.g., 9.0)
  default_stud_spacing: 16 | 24;     // inches on center
  default_wall_thickness?: number;   // inches (e.g., 4.5, 6.0)
  
  // Finishing specifications
  finishing_level: 1 | 2 | 3 | 4 | 5; // ASTM C840 levels
  drywall_thickness?: number;         // inches (default: 0.5)
  
  // Location and rates
  region: Region;
  location?: string;                  // City, State
  
  // Custom rates (optional overrides)
  custom_labor_rate?: number;         // $/hour
  custom_material_prices?: Partial<MaterialPrices>;
  
  // Special requirements
  fire_rating_required?: boolean;
  moisture_resistance_required?: boolean;
  sound_insulation_required?: boolean;
  
  // Markup
  overhead_percent?: number;          // default: 15
  profit_percent?: number;            // default: 10
}

type ProjectType = 
  | "commercial" 
  | "residential" 
  | "industrial" 
  | "institutional";

type Region = 
  | "northeast" 
  | "south" 
  | "midwest" 
  | "west" 
  | "mountain" 
  | "pacific";
```

**Example JSON:**
```json
{
  "project_name": "Office Building - Level 1",
  "project_type": "commercial",
  "default_ceiling_height": 9.0,
  "default_stud_spacing": 16,
  "finishing_level": 3,
  "drywall_thickness": 0.5,
  "region": "northeast",
  "location": "Boston, MA",
  "fire_rating_required": true,
  "overhead_percent": 15,
  "profit_percent": 10
}
```

---

### 3. FileUpload

Uploaded file information.

```typescript
interface FileUpload {
  file_id: string;                   // Unique file identifier
  original_filename: string;
  content_type: string;              // MIME type
  file_size: number;                 // bytes
  page_count?: number;               // for PDFs
  
  // Storage
  storage_url: string;               // S3 URL or local path
  storage_type: "s3" | "local";
  
  // Metadata
  uploaded_at: string;               // ISO 8601
  file_hash?: string;                // SHA-256 hash
  
  // Processing flags
  processable: boolean;
  processing_priority?: number;      // 1-10
}
```

**Example JSON:**
```json
{
  "file_id": "file_001",
  "original_filename": "FloorPlan_Level1.pdf",
  "content_type": "application/pdf",
  "file_size": 2457600,
  "page_count": 1,
  "storage_url": "s3://drywall-uploads/proj_456def/file_001.pdf",
  "storage_type": "s3",
  "uploaded_at": "2026-05-21T10:30:01Z",
  "file_hash": "a3d5f8c9...",
  "processable": true,
  "processing_priority": 1
}
```

---

### 4. PageClassification

Classification result for a single page.

```typescript
interface PageClassification {
  file_id: string;
  page_number: number;               // 1-indexed
  page_type: PageType;
  confidence: number;                // 0-1
  notes?: string;
  recommended_for_extraction: boolean;
  
  // Additional metadata extracted during classification
  detected_elements?: string[];      // ["walls", "doors", "dimensions"]
  scale_hint?: string;
  orientation?: "portrait" | "landscape";
}

type PageType = 
  | "floor_plan"
  | "reflected_ceiling_plan"
  | "wall_section"
  | "wall_elevation"
  | "detail_drawing"
  | "specification_text"
  | "schedule_table"
  | "cover_sheet"
  | "site_plan"
  | "other"
  | "unclassified";
```

**Example JSON:**
```json
{
  "file_id": "file_001",
  "page_number": 1,
  "page_type": "floor_plan",
  "confidence": 0.98,
  "notes": "Clear floor plan showing walls, doors, windows. Scale visible.",
  "recommended_for_extraction": true,
  "detected_elements": ["walls", "doors", "windows", "dimensions", "scale"],
  "scale_hint": "1/4\" = 1'-0\"",
  "orientation": "landscape"
}
```

---

### 5. DrawingMetadata

Metadata extracted from a drawing page.

```typescript
interface DrawingMetadata {
  file_id: string;
  page_number: number;
  
  // Scale information
  scale: Scale;
  
  // Overall dimensions
  overall_dimensions?: Dimensions;
  
  // Dimension annotations found
  dimension_callouts?: DimensionCallout[];
  
  // Grid system
  grid_system?: GridSystem;
  
  // Drawing info
  drawing_title?: string;
  drawing_number?: string;
  sheet_number?: string;
  
  // Extraction metadata
  extracted_at: string;
  confidence: number;
}

interface Scale {
  type: "architectural" | "engineering" | "metric";
  ratio: string;                     // e.g., "1/4\" = 1'-0\""
  numeric_ratio: number;             // e.g., 48
  units: "imperial" | "metric";
}

interface Dimensions {
  length_ft?: number;
  width_ft?: number;
  length_m?: number;
  width_m?: number;
  area_sqft?: number;
  area_sqm?: number;
}

interface DimensionCallout {
  label: string;
  value: number;
  unit: string;
  location?: string;
}

interface GridSystem {
  present: boolean;
  horizontal?: string[];             // ["A", "B", "C", ...]
  vertical?: string[];               // ["1", "2", "3", ...]
  spacing_ft?: number;
}
```

**Example JSON:**
```json
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
    {
      "label": "Overall Length",
      "value": 120.0,
      "unit": "ft"
    }
  ],
  "grid_system": {
    "present": true,
    "horizontal": ["A", "B", "C", "D", "E"],
    "vertical": ["1", "2", "3", "4", "5", "6"],
    "spacing_ft": 24.0
  },
  "drawing_title": "Level 1 Floor Plan",
  "sheet_number": "A1.1",
  "extracted_at": "2026-05-21T10:30:18Z",
  "confidence": 0.94
}
```

---

### 6. Wall

Individual wall segment.

```typescript
interface Wall {
  id: string;                        // Unique wall ID (e.g., "W1")
  page_id: string;                   // Source page reference
  
  // Location
  start_point: Point;
  end_point: Point;
  
  // Dimensions
  length_ft: number;
  height_ft: number;
  wall_area_sqft: number;            // length × height
  thickness_inches: number;
  
  // Classification
  type: WallType;
  material_hint?: MaterialHint;
  
  // Detection metadata
  confidence: number;                // 0-1
  notes?: string;
  
  // Relationships
  connected_walls?: string[];        // IDs of connecting walls
  intersection_type?: IntersectionType;
  
  // User edits
  user_edited?: boolean;
  original_values?: Partial<Wall>;
}

interface Point {
  x: number;                         // pixel coordinates
  y: number;
  grid?: string;                     // e.g., "A1"
}

type WallType = 
  | "exterior"
  | "interior"
  | "load_bearing"
  | "partition"
  | "demising"
  | "shaft";

type MaterialHint = 
  | "wood_frame"
  | "metal_frame"
  | "concrete"
  | "masonry"
  | "unknown";

type IntersectionType = 
  | "corner"
  | "t_junction"
  | "cross"
  | "isolated";
```

**Example JSON:**
```json
{
  "id": "W1",
  "page_id": "file_001_p1",
  "start_point": {
    "x": 100,
    "y": 200,
    "grid": "A1"
  },
  "end_point": {
    "x": 1100,
    "y": 200,
    "grid": "E1"
  },
  "length_ft": 40.0,
  "height_ft": 9.0,
  "wall_area_sqft": 360.0,
  "thickness_inches": 6.0,
  "type": "exterior",
  "material_hint": "wood_frame",
  "confidence": 0.97,
  "notes": "North exterior wall",
  "connected_walls": ["W2", "W4"],
  "intersection_type": "corner",
  "user_edited": false
}
```

---

### 7. Opening

Door or window opening.

```typescript
interface Opening {
  id: string;                        // Unique opening ID (e.g., "D1", "W1")
  wall_id: string;                   // Parent wall reference
  
  // Type
  type: OpeningType;
  subtype?: OpeningSubtype;
  
  // Dimensions
  width_ft: number;
  height_ft: number;
  area_sqft: number;                 // width × height
  
  // Rough opening
  rough_opening: boolean;
  rough_opening_size?: {
    width_ft: number;
    height_ft: number;
  };
  
  // Location on wall
  position_on_wall?: string;
  distance_from_start_ft?: number;
  
  // Detection metadata
  confidence: number;
  notes?: string;
  
  // User edits
  user_edited?: boolean;
  original_values?: Partial<Opening>;
}

type OpeningType = 
  | "door"
  | "window"
  | "sliding_door"
  | "overhead_door"
  | "opening";

type OpeningSubtype = 
  // Doors
  | "single_swing"
  | "double_swing"
  | "french_door"
  | "pocket_door"
  | "bifold"
  // Windows
  | "double_hung"
  | "casement"
  | "slider"
  | "picture"
  | "bay"
  | "awning";
```

**Example JSON:**
```json
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
  "distance_from_start_ft": 18.5,
  "confidence": 0.92,
  "notes": "Standard single door, main entry",
  "user_edited": false
}
```

---

### 8. MaterialCalculation

Complete material quantities and costs.

```typescript
interface MaterialCalculation {
  job_id: string;
  calculated_at: string;
  calculation_method: "deterministic" | "ai_assisted";
  
  // Organized by category
  framing: FramingMaterials;
  drywall: DrywallMaterials;
  fasteners: FastenerMaterials;
  finishing: FinishingMaterials;
  adhesives?: AdhesiveMaterials;
  
  // Summary
  material_summary: MaterialSummary;
  
  // Calculation metadata
  calculation_metadata: CalculationMetadata;
}

interface FramingMaterials {
  studs_16oc?: MaterialItem;
  studs_24oc?: MaterialItem;
  top_plate?: MaterialItem;
  bottom_plate?: MaterialItem;
  header_material?: MaterialItem;
  blocking?: MaterialItem;
  corner_studs?: MaterialItem;
}

interface DrywallMaterials {
  sheets_4x12_1_2?: MaterialItem;
  sheets_4x8_1_2?: MaterialItem;
  sheets_4x12_5_8?: MaterialItem;
  sheets_4x8_5_8?: MaterialItem;
  moisture_resistant?: MaterialItem;
  fire_rated?: MaterialItem;
}

interface FastenerMaterials {
  screws_1_5_8?: MaterialItem;
  screws_2_1_2?: MaterialItem;
  nails?: MaterialItem;
}

interface FinishingMaterials {
  joint_compound_level3?: MaterialItem;
  paper_tape?: MaterialItem;
  mesh_tape?: MaterialItem;
  corner_bead_metal?: MaterialItem;
  corner_bead_vinyl?: MaterialItem;
  sanding_supplies?: MaterialItem;
  primer?: MaterialItem;
}

interface AdhesiveMaterials {
  construction_adhesive?: MaterialItem;
  drywall_adhesive?: MaterialItem;
}

interface MaterialItem {
  item: string;                      // Description
  quantity: number;
  unit: string;                      // EA, LF, SF, GAL, LB, etc.
  unit_cost?: number;                // $ per unit
  total_cost?: number;               // quantity × unit_cost
  sqft?: number;                     // for sheet goods
  coverage_sqft?: number;            // actual coverage
  waste_percent?: number;
  notes?: string;
}

interface MaterialSummary {
  total_drywall_sqft: number;
  net_coverage_sqft: number;
  waste_factor: number;
  total_linear_feet_framing: number;
  total_studs: number;
  estimated_material_cost: number;
  cost_per_sqft: number;
}

interface CalculationMetadata {
  calculated_at: string;
  calculation_method: string;
  assumptions: {
    stud_spacing: string;
    drywall_thickness: string;
    finish_level: number;
    waste_factor: number;
    sheet_size_primary: string;
    sheet_size_secondary: string;
  };
}
```

**Example JSON:**
```json
{
  "job_id": "job_abc123xyz",
  "calculated_at": "2026-05-21T10:30:30Z",
  "calculation_method": "deterministic",
  "framing": {
    "studs_16oc": {
      "item": "2x4 Wood Studs @ 16\" OC",
      "quantity": 185,
      "unit": "EA",
      "unit_cost": 6.50,
      "total_cost": 1202.50,
      "notes": "10ft lengths, includes 10% waste"
    },
    "top_plate": {
      "item": "2x4 Top Plate (double)",
      "quantity": 320,
      "unit": "LF",
      "unit_cost": 1.20,
      "total_cost": 384.00
    }
  },
  "drywall": {
    "sheets_4x12_1_2": {
      "item": "1/2\" Drywall 4'x12' Sheets",
      "quantity": 95,
      "unit": "EA",
      "unit_cost": 18.50,
      "total_cost": 1757.50,
      "sqft": 4560,
      "coverage_sqft": 3970,
      "waste_percent": 15
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
    "calculated_at": "2026-05-21T10:30:30Z",
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

---

### 9. LaborEstimation

Labor hours and costs by task.

```typescript
interface LaborEstimation {
  job_id: string;
  calculated_at: string;
  
  // Labor tasks
  tasks: LaborTask[];
  
  // Summary
  labor_summary: LaborSummary;
  
  // Regional adjustments
  regional_adjustments: RegionalAdjustments;
}

interface LaborTask {
  id: string;
  phase: LaborPhase;
  description: string;
  hours: number;
  rate_per_hour: number;
  cost: number;                      // hours × rate_per_hour
  crew_size: number;
  duration_days: number;             // hours / (crew_size × 8)
  notes?: string;
  productivity_rate?: string;        // e.g., "0.015 hrs/sqft"
}

type LaborPhase = 
  | "framing"
  | "hanging"
  | "taping_coat1"
  | "taping_coat2"
  | "taping_coat3"
  | "taping_coat4"
  | "taping_coat5"
  | "corner_bead"
  | "sanding"
  | "priming"
  | "cleanup";

interface LaborSummary {
  total_hours: number;
  total_labor_cost: number;
  average_rate_per_hour: number;
  total_duration_days: number;
  recommended_crew_size: number;
  hours_per_sqft: number;
}

interface RegionalAdjustments {
  region: string;
  base_rate: number;
  regional_multiplier: number;
  adjusted_rate: number;
  notes?: string;
}
```

**Example JSON:**
```json
{
  "job_id": "job_abc123xyz",
  "calculated_at": "2026-05-21T10:30:32Z",
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
      "notes": "Includes layout, cutting, assembly",
      "productivity_rate": "0.012 hrs/sqft"
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
      "productivity_rate": "0.018 hrs/sqft"
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
```

---

### 10. Takeoff

Final complete takeoff document.

```typescript
interface Takeoff {
  job_id: string;
  takeoff_id: string;
  generated_at: string;
  
  // Project info
  project: ProjectInfo;
  
  // High-level summary
  summary: TakeoffSummary;
  
  // Detailed data
  walls: Wall[];
  openings: Opening[];
  materials: MaterialCalculation;
  labor: LaborEstimation;
  
  // Line items for export
  line_items: LineItemSection[];
  
  // Quality and audit
  quality_score: QualityScore;
  audit_trail?: AuditTrail;
}

interface ProjectInfo {
  project_id: string;
  project_name: string;
  project_type: ProjectType;
  location?: string;
  total_area_sqft?: number;
  client?: string;
  contractor?: string;
  estimator?: string;
}

interface TakeoffSummary {
  // Quantities
  total_wall_area_sqft: number;
  net_drywall_area_sqft: number;
  total_linear_feet: number;
  total_walls: number;
  total_openings: number;
  
  // Costs
  total_material_cost: number;
  total_labor_cost: number;
  subtotal: number;
  overhead_percent: number;
  overhead_amount: number;
  profit_percent: number;
  profit_amount: number;
  total_cost: number;
  cost_per_sqft: number;
  
  // Timeline
  estimated_duration_days: number;
  crew_size: number;
}

interface LineItemSection {
  section: string;                   // e.g., "01 - FRAMING"
  items: LineItem[];
  section_total: number;
}

interface LineItem {
  item_no: string;                   // e.g., "01.01"
  description: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  total_cost: number;
  type: "material" | "labor" | "equipment" | "other";
  notes?: string;
}

interface QualityScore {
  overall: number;                   // 0-100
  wall_detection_confidence: number;
  opening_detection_confidence: number;
  calculation_accuracy: number;
  notes?: string;
  warnings?: string[];
}

interface AuditTrail {
  stage_1_upload: object;
  stage_2_classification: object;
  stage_3_drawing_analysis: object;
  stage_4_wall_extraction: object;
  stage_5_opening_detection: object;
  stage_6_material_calculations: object;
  stage_7_labor_estimation: object;
}
```

**Example JSON:**
```json
{
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
    "cost_per_sqft": 7.08,
    "estimated_duration_days": 21.5,
    "crew_size": 2
  },
  "walls": [...],
  "openings": [...],
  "materials": {...},
  "labor": {...},
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
          "total_cost": 1202.50,
          "type": "material"
        }
      ],
      "section_total": 4850.00
    }
  ],
  "quality_score": {
    "overall": 92,
    "wall_detection_confidence": 94,
    "opening_detection_confidence": 88,
    "calculation_accuracy": 100
  }
}
```

---

## Support Data Models

### 11. ProcessingError

Error information during processing.

```typescript
interface ProcessingError {
  error_id: string;
  stage: ProcessingStage;
  error_code: string;
  message: string;
  details?: string;
  timestamp: string;
  recoverable: boolean;
  suggested_action?: string;
}
```

**Example:**
```json
{
  "error_id": "err_001",
  "stage": "stage_4_wall_extraction",
  "error_code": "NO_WALLS_DETECTED",
  "message": "No walls could be detected in the floor plan",
  "details": "AI analysis returned 0 wall segments with confidence > 0.7",
  "timestamp": "2026-05-21T10:30:25Z",
  "recoverable": true,
  "suggested_action": "Try manual mode or upload a clearer floor plan"
}
```

---

### 12. ProcessingWarning

Non-fatal warning during processing.

```typescript
interface ProcessingWarning {
  warning_id: string;
  stage: ProcessingStage;
  warning_code: string;
  message: string;
  details?: string;
  timestamp: string;
  severity: "low" | "medium" | "high";
}
```

**Example:**
```json
{
  "warning_id": "warn_001",
  "stage": "stage_4_wall_extraction",
  "warning_code": "LOW_CONFIDENCE_WALL",
  "message": "Wall W3 detected with low confidence",
  "details": "Confidence: 0.78 (threshold: 0.85). Wall may be partially obscured.",
  "timestamp": "2026-05-21T10:30:22Z",
  "severity": "medium"
}
```

---

## Validation Schemas

### Required Field Validation

```typescript
// Wall validation
const wallSchema = {
  id: { required: true, type: "string" },
  length_ft: { required: true, type: "number", min: 1, max: 200 },
  height_ft: { required: true, type: "number", min: 7, max: 20 },
  wall_area_sqft: { required: true, type: "number", min: 0 },
  thickness_inches: { required: true, type: "number", enum: [3.5, 4.5, 6, 8, 10] },
  type: { required: true, type: "string", enum: ["exterior", "interior", "load_bearing", "partition"] },
  confidence: { required: true, type: "number", min: 0, max: 1 }
};

// Opening validation
const openingSchema = {
  id: { required: true, type: "string" },
  wall_id: { required: true, type: "string", references: "Wall.id" },
  type: { required: true, type: "string", enum: ["door", "window", "sliding_door", "overhead_door", "opening"] },
  width_ft: { required: true, type: "number", min: 0.5, max: 20 },
  height_ft: { required: true, type: "number", min: 0.5, max: 12 },
  area_sqft: { required: true, type: "number", min: 0 },
  confidence: { required: true, type: "number", min: 0, max: 1 }
};
```

### Business Rule Validation

```typescript
// Example validation rules
const businessRules = {
  // Opening must fit within wall
  openingFitsInWall: (opening: Opening, wall: Wall) => {
    return opening.width_ft <= wall.length_ft && 
           opening.height_ft <= wall.height_ft;
  },
  
  // Wall-to-floor ratio sanity check
  wallToFloorRatio: (totalWallArea: number, floorArea: number) => {
    const ratio = totalWallArea / floorArea;
    return ratio >= 0.2 && ratio <= 0.5;  // Typical range
  },
  
  // Waste factor reasonableness
  wasteFactor: (factor: number) => {
    return factor >= 1.0 && factor <= 1.3;  // 0-30% waste
  },
  
  // Labor productivity check
  laborProductivity: (hoursPerSqft: number) => {
    return hoursPerSqft >= 0.05 && hoursPerSqft <= 0.15;  // Industry range
  }
};
```

---

## Database Schema Mapping

### PostgreSQL Tables

```sql
-- Main processing jobs table
CREATE TABLE processing_jobs (
    job_id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id),
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL,
    current_stage VARCHAR(50),
    progress_percent INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    
    processing_mode VARCHAR(20),
    project_metadata JSONB,
    
    -- Stage outputs
    page_classifications JSONB,
    drawing_metadata JSONB,
    walls JSONB,
    openings JSONB,
    materials JSONB,
    labor JSONB,
    takeoff JSONB,
    
    errors JSONB,
    warnings JSONB,
    quality_score JSONB,
    audit_trail JSONB,
    
    INDEX idx_status (status),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Uploaded files
CREATE TABLE uploaded_files (
    file_id UUID PRIMARY KEY,
    job_id UUID REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    content_type VARCHAR(100),
    file_size BIGINT,
    page_count INTEGER,
    storage_url TEXT,
    storage_type VARCHAR(10),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash VARCHAR(64),
    processable BOOLEAN DEFAULT true
);

-- Walls (denormalized for querying)
CREATE TABLE walls (
    wall_id UUID PRIMARY KEY,
    job_id UUID REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    wall_data JSONB,
    length_ft DECIMAL(10,2),
    height_ft DECIMAL(10,2),
    wall_area_sqft DECIMAL(10,2),
    type VARCHAR(50),
    confidence DECIMAL(3,2),
    user_edited BOOLEAN DEFAULT false,
    
    INDEX idx_job_id (job_id),
    INDEX idx_type (type)
);

-- Openings (denormalized for querying)
CREATE TABLE openings (
    opening_id UUID PRIMARY KEY,
    job_id UUID REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    wall_id UUID REFERENCES walls(wall_id),
    opening_data JSONB,
    type VARCHAR(50),
    width_ft DECIMAL(10,2),
    height_ft DECIMAL(10,2),
    area_sqft DECIMAL(10,2),
    confidence DECIMAL(3,2),
    
    INDEX idx_job_id (job_id),
    INDEX idx_wall_id (wall_id)
);
```

---

**Document Version**: 1.0
**Last Updated**: 2026-05-21
**Schema Version**: v1.0

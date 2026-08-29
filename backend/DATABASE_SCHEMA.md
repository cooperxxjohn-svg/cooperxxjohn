# Drywall Takeoff System - Database Schema

Complete PostgreSQL database schema design for the drywall takeoff processing system.

---

## Database Technology

**Primary Database**: PostgreSQL 15+
**Why PostgreSQL?**
- Excellent JSONB support for storing complex nested data
- Strong ACID compliance for transactional integrity
- Powerful indexing capabilities (B-tree, GiST, GIN for JSONB)
- Built-in full-text search
- Robust connection pooling
- Open source and well-supported

---

## Schema Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Core Tables                          │
├─────────────────────────────────────────────────────────┤
│  users                    - User accounts               │
│  projects                 - Construction projects       │
│  processing_jobs          - Takeoff processing jobs     │
│  uploaded_files           - Uploaded PDF/image files    │
│  takeoffs                 - Final takeoff results       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  Denormalized Tables                    │
├─────────────────────────────────────────────────────────┤
│  walls                    - Individual wall segments    │
│  openings                 - Doors and windows           │
│  material_items           - Material line items         │
│  labor_tasks              - Labor task breakdown        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  Reference Tables                       │
├─────────────────────────────────────────────────────────┤
│  material_prices          - Regional pricing            │
│  labor_rates              - Regional labor rates        │
│  productivity_rates       - Industry productivity       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Audit Tables                          │
├─────────────────────────────────────────────────────────┤
│  job_history              - Status change history       │
│  api_logs                 - API request logs            │
│  webhooks                 - Webhook configuration       │
└─────────────────────────────────────────────────────────┘
```

---

## Core Tables

### 1. users

User account information.

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile
    full_name VARCHAR(255),
    company_name VARCHAR(255),
    phone VARCHAR(50),
    
    -- Subscription
    plan VARCHAR(50) DEFAULT 'free',  -- free, starter, pro, enterprise
    subscription_status VARCHAR(50) DEFAULT 'active',  -- active, cancelled, expired
    subscription_started_at TIMESTAMP,
    subscription_expires_at TIMESTAMP,
    
    -- API access
    api_key VARCHAR(255) UNIQUE,
    api_key_created_at TIMESTAMP,
    
    -- Limits
    monthly_job_limit INTEGER DEFAULT 10,
    jobs_used_this_month INTEGER DEFAULT 0,
    storage_limit_mb INTEGER DEFAULT 100,
    storage_used_mb INTEGER DEFAULT 0,
    
    -- Authentication
    last_login_at TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_email (email),
    INDEX idx_api_key (api_key),
    INDEX idx_subscription_status (subscription_status)
);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 2. projects

Construction projects (can have multiple takeoff jobs).

```sql
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Project info
    project_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50),  -- commercial, residential, industrial, institutional
    project_location VARCHAR(255),
    
    -- Client info
    client_name VARCHAR(255),
    client_contact VARCHAR(255),
    client_email VARCHAR(255),
    client_phone VARCHAR(50),
    
    -- Project metadata
    total_area_sqft DECIMAL(10,2),
    number_of_levels INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, archived
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 3. processing_jobs

Main table for tracking takeoff processing jobs.

```sql
CREATE TABLE processing_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
        -- queued, processing, completed, failed, cancelled
    current_stage VARCHAR(50),
        -- stage_1_upload, stage_2_classification, ... stage_8_takeoff_generation
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    processing_time_seconds INTEGER,
    
    -- Configuration
    processing_mode VARCHAR(20) DEFAULT 'fast',  -- fast, deep, manual
    project_metadata JSONB NOT NULL,
    
    -- Stage outputs (JSONB for flexibility)
    page_classifications JSONB,
    drawing_metadata JSONB,
    walls JSONB,
    openings JSONB,
    materials JSONB,
    labor JSONB,
    takeoff JSONB,
    
    -- Quality and errors
    quality_score JSONB,
    errors JSONB,
    warnings JSONB,
    
    -- Audit trail
    audit_trail JSONB,
    
    -- Revisions (user edits)
    revision_number INTEGER DEFAULT 1,
    parent_job_id UUID REFERENCES processing_jobs(job_id),
    
    -- Metadata
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_status (status),
    INDEX idx_user_id (user_id),
    INDEX idx_project_id (project_id),
    INDEX idx_created_at (created_at),
    INDEX idx_current_stage (current_stage),
    
    -- GIN index for JSONB queries
    INDEX idx_walls_jsonb ON processing_jobs USING GIN (walls),
    INDEX idx_materials_jsonb ON processing_jobs USING GIN (materials)
);

CREATE TRIGGER update_processing_jobs_updated_at BEFORE UPDATE ON processing_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to calculate processing time on completion
CREATE OR REPLACE FUNCTION calculate_processing_time()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL THEN
        NEW.processing_time_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_processing_time BEFORE UPDATE ON processing_jobs
    FOR EACH ROW EXECUTE FUNCTION calculate_processing_time();
```

---

### 4. uploaded_files

Uploaded PDF and image files.

```sql
CREATE TABLE uploaded_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    
    -- File info
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,  -- bytes
    page_count INTEGER,
    
    -- Storage
    storage_url TEXT NOT NULL,
    storage_type VARCHAR(10) DEFAULT 'local',  -- local, s3
    storage_bucket VARCHAR(255),
    storage_key VARCHAR(500),
    
    -- File integrity
    file_hash VARCHAR(64),  -- SHA-256
    
    -- Processing
    processable BOOLEAN DEFAULT TRUE,
    processing_priority INTEGER DEFAULT 5,
    
    -- Metadata
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_job_id (job_id),
    INDEX idx_file_hash (file_hash),
    INDEX idx_uploaded_at (uploaded_at)
);
```

---

### 5. takeoffs

Final takeoff results (denormalized for fast querying).

```sql
CREATE TABLE takeoffs (
    takeoff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID UNIQUE NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    -- Summary metrics (denormalized for fast queries)
    total_wall_area_sqft DECIMAL(10,2),
    net_drywall_area_sqft DECIMAL(10,2),
    total_linear_feet DECIMAL(10,2),
    total_walls INTEGER,
    total_openings INTEGER,
    
    -- Costs
    total_material_cost DECIMAL(10,2),
    total_labor_cost DECIMAL(10,2),
    overhead_percent DECIMAL(5,2),
    overhead_amount DECIMAL(10,2),
    profit_percent DECIMAL(5,2),
    profit_amount DECIMAL(10,2),
    subtotal DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    cost_per_sqft DECIMAL(10,2),
    
    -- Timeline
    estimated_duration_days DECIMAL(5,1),
    recommended_crew_size INTEGER,
    
    -- Complete data (JSONB)
    takeoff_data JSONB NOT NULL,
    
    -- Quality
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
    confidence_level VARCHAR(20),  -- high, medium, low
    
    -- Timestamps
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_job_id (job_id),
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id),
    INDEX idx_generated_at (generated_at),
    INDEX idx_total_cost (total_cost),
    
    -- GIN index for full takeoff data
    INDEX idx_takeoff_data_jsonb ON takeoffs USING GIN (takeoff_data)
);

CREATE TRIGGER update_takeoffs_updated_at BEFORE UPDATE ON takeoffs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Denormalized Tables (for querying)

### 6. walls

Individual wall segments (denormalized from processing_jobs.walls JSONB).

```sql
CREATE TABLE walls (
    wall_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    
    -- Wall identifier
    wall_ref VARCHAR(50) NOT NULL,  -- e.g., "W1", "W2"
    page_id VARCHAR(100),
    
    -- Location (pixel coordinates)
    start_x INTEGER,
    start_y INTEGER,
    end_x INTEGER,
    end_y INTEGER,
    grid_start VARCHAR(10),
    grid_end VARCHAR(10),
    
    -- Dimensions
    length_ft DECIMAL(10,2) NOT NULL,
    height_ft DECIMAL(10,2) NOT NULL,
    wall_area_sqft DECIMAL(10,2) NOT NULL,
    thickness_inches DECIMAL(5,2),
    
    -- Classification
    type VARCHAR(50) NOT NULL,  -- exterior, interior, load_bearing, partition
    material_hint VARCHAR(50),  -- wood_frame, metal_frame, concrete, masonry
    
    -- Detection metadata
    confidence DECIMAL(3,2),
    notes TEXT,
    
    -- Relationships
    connected_walls JSONB,  -- Array of wall IDs
    intersection_type VARCHAR(50),  -- corner, t_junction, cross, isolated
    
    -- User edits
    user_edited BOOLEAN DEFAULT FALSE,
    original_values JSONB,
    
    -- Complete data
    wall_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_job_id (job_id),
    INDEX idx_type (type),
    INDEX idx_confidence (confidence),
    INDEX idx_wall_area (wall_area_sqft)
);

CREATE TRIGGER update_walls_updated_at BEFORE UPDATE ON walls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 7. openings

Doors and windows (denormalized from processing_jobs.openings JSONB).

```sql
CREATE TABLE openings (
    opening_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    wall_id UUID REFERENCES walls(wall_id) ON DELETE CASCADE,
    
    -- Opening identifier
    opening_ref VARCHAR(50) NOT NULL,  -- e.g., "D1", "W1"
    
    -- Type
    type VARCHAR(50) NOT NULL,  -- door, window, sliding_door, overhead_door
    subtype VARCHAR(50),  -- single_swing, double_hung, etc.
    
    -- Dimensions
    width_ft DECIMAL(10,2) NOT NULL,
    height_ft DECIMAL(10,2) NOT NULL,
    area_sqft DECIMAL(10,2) NOT NULL,
    
    -- Rough opening
    rough_opening BOOLEAN DEFAULT TRUE,
    rough_opening_width_ft DECIMAL(10,2),
    rough_opening_height_ft DECIMAL(10,2),
    
    -- Location
    position_on_wall VARCHAR(100),
    distance_from_start_ft DECIMAL(10,2),
    
    -- Detection metadata
    confidence DECIMAL(3,2),
    notes TEXT,
    
    -- User edits
    user_edited BOOLEAN DEFAULT FALSE,
    original_values JSONB,
    
    -- Complete data
    opening_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_job_id (job_id),
    INDEX idx_wall_id (wall_id),
    INDEX idx_type (type),
    INDEX idx_area (area_sqft)
);

CREATE TRIGGER update_openings_updated_at BEFORE UPDATE ON openings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Reference Tables

### 8. material_prices

Regional material pricing.

```sql
CREATE TABLE material_prices (
    price_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Region
    region VARCHAR(50) NOT NULL,  -- northeast, west, south, midwest, mountain, pacific
    effective_date DATE NOT NULL,
    expires_at DATE,
    
    -- Material info
    material_category VARCHAR(50) NOT NULL,  -- framing, drywall, fasteners, finishing
    material_item VARCHAR(100) NOT NULL,
    material_code VARCHAR(50),
    
    -- Pricing
    unit VARCHAR(20) NOT NULL,  -- EA, LF, SF, GAL, LB
    unit_price DECIMAL(10,2) NOT NULL,
    
    -- Metadata
    supplier VARCHAR(100),
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_region_effective (region, effective_date),
    INDEX idx_material_category (material_category),
    INDEX idx_material_code (material_code),
    
    -- Unique constraint
    UNIQUE (region, material_code, effective_date)
);

CREATE TRIGGER update_material_prices_updated_at BEFORE UPDATE ON material_prices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default national pricing
INSERT INTO material_prices (region, effective_date, material_category, material_item, material_code, unit, unit_price) VALUES
    ('national', '2026-05-01', 'framing', '2x4 Wood Stud 10ft', 'STUD_2X4_10', 'EA', 6.50),
    ('national', '2026-05-01', 'framing', '2x4 Plate Stock', 'PLATE_2X4', 'LF', 1.20),
    ('national', '2026-05-01', 'drywall', '1/2" Drywall 4x12', 'DW_4X12_1_2', 'EA', 18.50),
    ('national', '2026-05-01', 'drywall', '1/2" Drywall 4x8', 'DW_4X8_1_2', 'EA', 12.00),
    ('national', '2026-05-01', 'fasteners', 'Drywall Screws 1-5/8"', 'SCREW_1_5_8', 'LB', 8.50),
    ('national', '2026-05-01', 'finishing', 'Joint Compound', 'COMPOUND_AP', 'GAL', 15.00),
    ('national', '2026-05-01', 'finishing', 'Paper Joint Tape 250ft', 'TAPE_PAPER', 'EA', 3.50),
    ('national', '2026-05-01', 'finishing', 'Metal Corner Bead 10ft', 'BEAD_METAL', 'EA', 4.25);
```

---

### 9. labor_rates

Regional labor rates.

```sql
CREATE TABLE labor_rates (
    rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Region
    region VARCHAR(50) NOT NULL,
    effective_date DATE NOT NULL,
    expires_at DATE,
    
    -- Labor category
    labor_category VARCHAR(50) NOT NULL,  -- framing, hanging, taping, finishing
    skill_level VARCHAR(50),  -- apprentice, journeyman, master
    
    -- Rates
    base_rate DECIMAL(10,2) NOT NULL,
    regional_multiplier DECIMAL(5,2) DEFAULT 1.00,
    adjusted_rate DECIMAL(10,2) NOT NULL,
    
    -- Metadata
    union_rate BOOLEAN DEFAULT FALSE,
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_region_effective (region, effective_date),
    INDEX idx_labor_category (labor_category),
    
    UNIQUE (region, labor_category, effective_date)
);

CREATE TRIGGER update_labor_rates_updated_at BEFORE UPDATE ON labor_rates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default rates
INSERT INTO labor_rates (region, effective_date, labor_category, base_rate, regional_multiplier, adjusted_rate) VALUES
    ('northeast', '2026-05-01', 'framing', 50.00, 1.10, 55.00),
    ('northeast', '2026-05-01', 'hanging', 50.00, 1.10, 55.00),
    ('northeast', '2026-05-01', 'taping', 45.00, 1.10, 49.50),
    ('west', '2026-05-01', 'framing', 50.00, 1.20, 60.00),
    ('west', '2026-05-01', 'hanging', 50.00, 1.20, 60.00),
    ('west', '2026-05-01', 'taping', 45.00, 1.20, 54.00),
    ('midwest', '2026-05-01', 'framing', 50.00, 1.00, 50.00),
    ('midwest', '2026-05-01', 'hanging', 50.00, 1.00, 50.00),
    ('midwest', '2026-05-01', 'taping', 45.00, 1.00, 45.00);
```

---

### 10. productivity_rates

Industry-standard productivity rates.

```sql
CREATE TABLE productivity_rates (
    productivity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Task
    task_category VARCHAR(50) NOT NULL,  -- framing, hanging, taping, etc.
    task_name VARCHAR(100) NOT NULL,
    
    -- Productivity
    rate_value DECIMAL(10,4) NOT NULL,
    rate_unit VARCHAR(50) NOT NULL,  -- hrs/sqft, hrs/lf, etc.
    
    -- Conditions
    project_type VARCHAR(50),  -- commercial, residential
    difficulty_level VARCHAR(50),  -- easy, medium, hard
    
    -- Metadata
    source VARCHAR(100),  -- RS Means, industry average, etc.
    last_verified DATE,
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_task_category (task_category)
);

CREATE TRIGGER update_productivity_rates_updated_at BEFORE UPDATE ON productivity_rates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert standard productivity rates
INSERT INTO productivity_rates (task_category, task_name, rate_value, rate_unit, difficulty_level, source) VALUES
    ('framing', 'Frame walls - studs and plates', 0.012, 'hrs/sqft', 'medium', 'RS Means 2026'),
    ('hanging', 'Hang drywall sheets', 0.018, 'hrs/sqft', 'medium', 'RS Means 2026'),
    ('taping', 'First coat - tape embed', 0.015, 'hrs/sqft', 'medium', 'RS Means 2026'),
    ('taping', 'Second coat - fill coat', 0.012, 'hrs/sqft', 'medium', 'RS Means 2026'),
    ('taping', 'Final coat and sand', 0.010, 'hrs/sqft', 'medium', 'RS Means 2026'),
    ('finishing', 'Install corner bead', 0.050, 'hrs/lf', 'easy', 'Industry average'),
    ('cleanup', 'Cleanup and debris removal', 0.003, 'hrs/sqft', 'easy', 'Industry average');
```

---

## Audit Tables

### 11. job_history

Status change history for processing jobs.

```sql
CREATE TABLE job_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
    
    -- Status change
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    from_stage VARCHAR(50),
    to_stage VARCHAR(50),
    
    -- Progress
    progress_percent INTEGER,
    
    -- Details
    message TEXT,
    error_details JSONB,
    
    -- Metadata
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by UUID REFERENCES users(user_id),
    
    -- Indexes
    INDEX idx_job_id (job_id),
    INDEX idx_changed_at (changed_at)
);
```

---

### 12. api_logs

API request logs for monitoring and debugging.

```sql
CREATE TABLE api_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request
    user_id UUID REFERENCES users(user_id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_body JSONB,
    query_params JSONB,
    
    -- Response
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_endpoint (endpoint),
    INDEX idx_created_at (created_at),
    INDEX idx_status_code (status_code)
);

-- Partition by month for performance
CREATE TABLE api_logs_2026_05 PARTITION OF api_logs
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```

---

### 13. webhooks

Webhook configuration for event notifications.

```sql
CREATE TABLE webhooks (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Configuration
    url TEXT NOT NULL,
    secret VARCHAR(255),
    events TEXT[] NOT NULL,  -- ['job.completed', 'job.failed']
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, failed
    
    -- Delivery tracking
    last_triggered_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    failure_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Views

### Summary Views for Reporting

```sql
-- User statistics view
CREATE VIEW user_statistics AS
SELECT 
    u.user_id,
    u.email,
    u.plan,
    COUNT(DISTINCT pj.job_id) AS total_jobs,
    COUNT(DISTINCT CASE WHEN pj.status = 'completed' THEN pj.job_id END) AS completed_jobs,
    SUM(CASE WHEN pj.status = 'completed' THEN t.total_cost ELSE 0 END) AS total_estimated_value,
    AVG(pj.processing_time_seconds) AS avg_processing_time_seconds,
    MAX(pj.created_at) AS last_job_created_at
FROM users u
LEFT JOIN processing_jobs pj ON u.user_id = pj.user_id
LEFT JOIN takeoffs t ON pj.job_id = t.job_id
GROUP BY u.user_id, u.email, u.plan;

-- Project summary view
CREATE VIEW project_summary AS
SELECT 
    p.project_id,
    p.project_name,
    p.user_id,
    COUNT(DISTINCT pj.job_id) AS total_jobs,
    COUNT(DISTINCT CASE WHEN pj.status = 'completed' THEN pj.job_id END) AS completed_jobs,
    SUM(t.total_wall_area_sqft) AS total_wall_area,
    SUM(t.total_cost) AS total_estimated_cost,
    MAX(pj.created_at) AS last_job_date
FROM projects p
LEFT JOIN processing_jobs pj ON p.project_id = pj.project_id
LEFT JOIN takeoffs t ON pj.job_id = t.job_id
GROUP BY p.project_id, p.project_name, p.user_id;

-- Daily job statistics
CREATE VIEW daily_job_stats AS
SELECT 
    DATE(created_at) AS date,
    COUNT(*) AS jobs_created,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS jobs_completed,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) AS jobs_failed,
    AVG(CASE WHEN processing_time_seconds IS NOT NULL 
        THEN processing_time_seconds END) AS avg_processing_time
FROM processing_jobs
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Indexes for Performance

```sql
-- Composite indexes for common queries
CREATE INDEX idx_jobs_user_status ON processing_jobs(user_id, status, created_at DESC);
CREATE INDEX idx_jobs_project_status ON processing_jobs(project_id, status);
CREATE INDEX idx_takeoffs_user_generated ON takeoffs(user_id, generated_at DESC);

-- Full-text search on project names
CREATE INDEX idx_projects_name_fulltext ON projects USING GIN (to_tsvector('english', project_name));

-- Partial indexes for active records
CREATE INDEX idx_active_jobs ON processing_jobs(created_at DESC) 
    WHERE status IN ('queued', 'processing');
CREATE INDEX idx_active_users ON users(created_at DESC) 
    WHERE deleted_at IS NULL;
```

---

## Database Functions

### Get Current Material Price

```sql
CREATE OR REPLACE FUNCTION get_current_material_price(
    p_region VARCHAR,
    p_material_code VARCHAR,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    v_price DECIMAL(10,2);
BEGIN
    -- Try region-specific price first
    SELECT unit_price INTO v_price
    FROM material_prices
    WHERE region = p_region
      AND material_code = p_material_code
      AND effective_date <= p_date
      AND (expires_at IS NULL OR expires_at >= p_date)
    ORDER BY effective_date DESC
    LIMIT 1;
    
    -- Fall back to national price
    IF v_price IS NULL THEN
        SELECT unit_price INTO v_price
        FROM material_prices
        WHERE region = 'national'
          AND material_code = p_material_code
          AND effective_date <= p_date
          AND (expires_at IS NULL OR expires_at >= p_date)
        ORDER BY effective_date DESC
        LIMIT 1;
    END IF;
    
    RETURN v_price;
END;
$$ LANGUAGE plpgsql;
```

### Get Current Labor Rate

```sql
CREATE OR REPLACE FUNCTION get_current_labor_rate(
    p_region VARCHAR,
    p_labor_category VARCHAR,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    v_rate DECIMAL(10,2);
BEGIN
    SELECT adjusted_rate INTO v_rate
    FROM labor_rates
    WHERE region = p_region
      AND labor_category = p_labor_category
      AND effective_date <= p_date
      AND (expires_at IS NULL OR expires_at >= p_date)
    ORDER BY effective_date DESC
    LIMIT 1;
    
    RETURN v_rate;
END;
$$ LANGUAGE plpgsql;
```

---

## Migration Strategy

Using Alembic for database migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Backup Strategy

```sql
-- Full backup (daily)
pg_dump -Fc drywalldb > drywalldb_backup_$(date +%Y%m%d).dump

-- Restore
pg_restore -d drywalldb drywalldb_backup_20260521.dump

-- Point-in-time recovery (enable WAL archiving)
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
```

---

## Performance Tuning

```sql
-- PostgreSQL configuration recommendations
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1  -- For SSD
effective_io_concurrency = 200
work_mem = 16MB
max_connections = 100
```

---

**Document Version**: 1.0
**Last Updated**: 2026-05-21
**Database Version**: PostgreSQL 15+

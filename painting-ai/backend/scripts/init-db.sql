-- PostgreSQL initialization script for Painting.ai
-- This script is run automatically when the PostgreSQL container is first created

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimizations

-- Set timezone
SET timezone = 'UTC';

-- Create custom types (if needed in future)
-- CREATE TYPE user_role AS ENUM ('owner', 'admin', 'estimator', 'viewer');

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE paintingai TO paintingai;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Painting.ai database initialized successfully';
END
$$;

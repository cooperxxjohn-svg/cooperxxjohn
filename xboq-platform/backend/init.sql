-- XBOQ Platform - Initial Database Setup
-- This file runs once when PostgreSQL container is created

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schema (optional, for better organization)
-- Using public schema for now, can add custom schema later

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE xboq_db TO xboq_user;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'XBOQ Database initialized successfully';
END $$;

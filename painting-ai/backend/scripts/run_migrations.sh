#!/bin/bash
# Database Migration Script for Painting.ai
# This script runs Alembic migrations and verifies database setup

set -e

echo "=================================="
echo "Painting.ai Database Migration"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Change to backend directory
cd "$BACKEND_DIR"

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure it"
    echo ""
    read -p "Do you want to continue with default values? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if command -v pg_isready &> /dev/null; then
    if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${RED}✗ PostgreSQL is not running${NC}"
        echo "Please start PostgreSQL with: docker-compose up -d postgres"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ pg_isready not found, skipping connection check${NC}"
fi

# Check if Alembic is installed
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}✗ Alembic is not installed${NC}"
    echo "Installing Alembic..."
    pip install alembic
fi

# Show current migration status
echo ""
echo -e "${YELLOW}Current migration status:${NC}"
alembic current || echo "No migrations applied yet"

# Show migration history
echo ""
echo -e "${YELLOW}Available migrations:${NC}"
alembic history

# Run migrations
echo ""
echo -e "${YELLOW}Running migrations...${NC}"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations completed successfully${NC}"
else
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi

# Verify tables were created
echo ""
echo -e "${YELLOW}Verifying database tables...${NC}"
python3 -c "
from database_service import db
from sqlalchemy import inspect

inspector = inspect(db.engine)
tables = inspector.get_table_names()

print(f'Found {len(tables)} tables:')
for table in sorted(tables):
    print(f'  - {table}')
" || echo -e "${RED}Could not verify tables${NC}"

# Test database connection
echo ""
echo -e "${YELLOW}Testing database connection...${NC}"
python3 -c "
from database_service import db
pool_status = db.get_pool_status()
print(f'Connection pool status:')
print(f'  Pool size: {pool_status[\"pool_size\"]}')
print(f'  Checked in: {pool_status[\"checked_in\"]}')
print(f'  Checked out: {pool_status[\"checked_out\"]}')
" && echo -e "${GREEN}✓ Database connection successful${NC}" || echo -e "${RED}✗ Database connection failed${NC}"

echo ""
echo -e "${GREEN}=================================="
echo "Database setup complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Run tests: pytest tests/test_database_migration.py -v"
echo "2. Start the backend: uvicorn main:app --reload"
echo "3. Check DATABASE_SETUP.md for more information"
echo ""

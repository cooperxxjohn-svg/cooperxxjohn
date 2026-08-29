#!/bin/bash
# Verification script for Week 2 database setup
# Tests all components to ensure production readiness

set -e

echo "=================================="
echo "Week 2 Setup Verification"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Function to check status
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

# 1. Check Docker Compose file
echo "1. Checking Docker Compose configuration..."
if [ -f "../docker-compose.yml" ]; then
    grep -q "postgres:15" ../docker-compose.yml
    check "PostgreSQL 15 configured"

    grep -q "redis:7" ../docker-compose.yml
    check "Redis 7 configured"

    grep -q "healthcheck" ../docker-compose.yml
    check "Health checks configured"
else
    echo -e "${RED}✗${NC} docker-compose.yml not found"
    ((FAIL++))
fi

# 2. Check environment file
echo ""
echo "2. Checking environment configuration..."
if [ -f "../.env.example" ]; then
    grep -q "DATABASE_URL" ../.env.example
    check "DATABASE_URL in .env.example"

    grep -q "POSTGRES_USER" ../.env.example
    check "POSTGRES variables configured"

    grep -q "REDIS_URL" ../.env.example
    check "REDIS_URL configured"

    grep -q "DB_POOL_SIZE" ../.env.example
    check "Connection pool variables"
else
    echo -e "${RED}✗${NC} .env.example not found"
    ((FAIL++))
fi

# 3. Check database models
echo ""
echo "3. Checking database models..."
if [ -f "models.py" ]; then
    python3 -c "from models import Base, User, Project, Room, Drawing" 2>/dev/null
    check "Models import successfully"

    python3 -c "from models import Organization, TeamMember" 2>/dev/null
    check "Organization models exist"

    python3 -c "from models import MaterialItem, Template, Assembly" 2>/dev/null
    check "Support models exist"
else
    echo -e "${RED}✗${NC} models.py not found"
    ((FAIL++))
fi

# 4. Check database service
echo ""
echo "4. Checking database service..."
if [ -f "database_service.py" ]; then
    python3 -c "from database_service import DatabaseService" 2>/dev/null
    check "DatabaseService imports"

    grep -q "pool_size" database_service.py
    check "Connection pooling configured"

    grep -q "get_pool_status" database_service.py
    check "Pool monitoring available"
else
    echo -e "${RED}✗${NC} database_service.py not found"
    ((FAIL++))
fi

# 5. Check Alembic
echo ""
echo "5. Checking Alembic migrations..."
if [ -f "alembic.ini" ]; then
    check "alembic.ini exists"

    [ -d "alembic/versions" ]
    check "Migrations directory exists"

    [ -f "alembic/versions/001_initial_schema.py" ]
    check "Initial migration exists"

    [ -f "alembic/versions/002_complete_schema.py" ]
    check "Complete schema migration exists"
else
    echo -e "${RED}✗${NC} alembic.ini not found"
    ((FAIL++))
fi

# 6. Check scripts
echo ""
echo "6. Checking automation scripts..."
[ -f "scripts/init-db.sql" ]
check "init-db.sql exists"

[ -x "scripts/run_migrations.sh" ]
check "run_migrations.sh is executable"

[ -x "scripts/backup_database.sh" ]
check "backup_database.sh is executable"

[ -x "scripts/restore_database.sh" ]
check "restore_database.sh is executable"

# 7. Check tests
echo ""
echo "7. Checking test files..."
if [ -f "tests/test_database_migration.py" ]; then
    check "Database migration tests exist"

    grep -q "test_user_crud" tests/test_database_migration.py
    check "User CRUD tests"

    grep -q "test_project_crud" tests/test_database_migration.py
    check "Project CRUD tests"
else
    echo -e "${RED}✗${NC} test_database_migration.py not found"
    ((FAIL++))
fi

# 8. Check documentation
echo ""
echo "8. Checking documentation..."
[ -f "../DATABASE_SETUP.md" ]
check "DATABASE_SETUP.md exists"

[ -f "DATABASE_QUICKSTART.md" ]
check "DATABASE_QUICKSTART.md exists"

[ -f "../WEEK2_DATABASE_COMPLETE.md" ]
check "WEEK2_DATABASE_COMPLETE.md exists"

[ -f "../WEEK2_COMPLETION_REPORT.md" ]
check "WEEK2_COMPLETION_REPORT.md exists"

# 9. Check health check
echo ""
echo "9. Checking health check endpoint..."
if [ -f "health_check.py" ]; then
    python3 -c "from health_check import router" 2>/dev/null
    check "Health check module imports"

    grep -q "/health" health_check.py
    check "Health endpoint defined"
else
    echo -e "${RED}✗${NC} health_check.py not found"
    ((FAIL++))
fi

# 10. Check Makefile
echo ""
echo "10. Checking Makefile commands..."
if [ -f "../Makefile" ]; then
    grep -q "db-setup" ../Makefile
    check "db-setup command exists"

    grep -q "db-migrate" ../Makefile
    check "db-migrate command exists"

    grep -q "db-backup" ../Makefile
    check "db-backup command exists"

    grep -q "db-test" ../Makefile
    check "db-test command exists"
else
    echo -e "${RED}✗${NC} Makefile not found"
    ((FAIL++))
fi

# 11. Check if Docker is available
echo ""
echo "11. Checking Docker availability..."
if command -v docker &> /dev/null; then
    check "Docker is installed"

    if command -v docker-compose &> /dev/null; then
        check "Docker Compose is installed"
    else
        echo -e "${YELLOW}⚠${NC} Docker Compose not found (optional)"
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker not found (optional for development)"
fi

# 12. Check Python dependencies
echo ""
echo "12. Checking Python dependencies..."
python3 -c "import sqlalchemy" 2>/dev/null
check "SQLAlchemy installed"

python3 -c "import alembic" 2>/dev/null
check "Alembic installed"

python3 -c "import psycopg2" 2>/dev/null
check "psycopg2 installed"

python3 -c "import redis" 2>/dev/null
check "redis installed"

# Summary
echo ""
echo "=================================="
echo "Verification Summary"
echo "=================================="
echo -e "Passed: ${GREEN}${PASS}${NC}"
echo -e "Failed: ${RED}${FAIL}${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your setup is complete and ready for:"
    echo "  1. make db-setup     - Start databases and run migrations"
    echo "  2. make db-test      - Run database tests"
    echo "  3. make dev          - Start development server"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Please review the errors above and:"
    echo "  1. Check the documentation: DATABASE_SETUP.md"
    echo "  2. Ensure all files are present"
    echo "  3. Run: pip install -r requirements.txt"
    echo ""
    exit 1
fi

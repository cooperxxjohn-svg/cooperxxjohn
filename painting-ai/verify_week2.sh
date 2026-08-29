#!/bin/bash
#
# Week 2 Verification Script
# Verifies all Week 2 components are in place and working
#

set -e  # Exit on error

echo "=========================================="
echo "WEEK 2 VERIFICATION SCRIPT"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS="${GREEN}✓${NC}"
FAILURE="${RED}✗${NC}"
WARNING="${YELLOW}⚠${NC}"

# Track results
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${SUCCESS} ${description}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${FAILURE} ${description}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_command() {
    local cmd=$1
    local description=$2

    if command -v $cmd &> /dev/null; then
        echo -e "${SUCCESS} ${description}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${FAILURE} ${description}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_service() {
    local cmd=$1
    local description=$2

    if $cmd &> /dev/null; then
        echo -e "${SUCCESS} ${description}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${WARNING} ${description}"
        ((CHECKS_WARNING++))
        return 1
    fi
}

echo "1. CHECKING FILES..."
echo "-------------------------------------------"

# New files
check_file "backend/config.py" "Configuration management"
check_file "backend/tests/test_week2_integration.py" "Integration tests"
check_file "backend/migrate_json_to_postgres.py" "Migration script"
check_file "WEEK2_COMPLETE.md" "Completion report"
check_file "QUICKSTART_WEEK2.md" "Quick start guide"
check_file "DEPLOYMENT_CHECKLIST.md" "Deployment checklist"
check_file "WEEK2_BENCHMARKS.md" "Performance benchmarks"
check_file "WEEK2_INTEGRATION_COMPLETE.md" "Integration summary"
check_file "WEEK2_SUMMARY.md" "Executive summary"

# Existing files (should be present)
check_file "backend/database_service.py" "PostgreSQL service"
check_file "backend/s3_service.py" "S3 service"
check_file "backend/models.py" "SQLAlchemy models"
check_file "docker-compose.yml" "Docker Compose config"
check_file ".env.example" "Environment template"
check_file "backend/main.py" "Main application"

echo ""
echo "2. CHECKING DEPENDENCIES..."
echo "-------------------------------------------"

# Required commands
check_command "docker" "Docker installed"
check_command "docker-compose" "Docker Compose installed"
check_command "python3" "Python 3 installed"
check_command "psql" "PostgreSQL client installed" || echo "   (Optional for local testing)"

echo ""
echo "3. CHECKING PYTHON PACKAGES..."
echo "-------------------------------------------"

if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate 2>/dev/null || true

    # Check key packages
    python3 -c "import fastapi" 2>/dev/null && echo -e "${SUCCESS} FastAPI installed" || echo -e "${FAILURE} FastAPI not installed"
    python3 -c "import sqlalchemy" 2>/dev/null && echo -e "${SUCCESS} SQLAlchemy installed" || echo -e "${FAILURE} SQLAlchemy not installed"
    python3 -c "import boto3" 2>/dev/null && echo -e "${SUCCESS} boto3 installed" || echo -e "${FAILURE} boto3 not installed"
    python3 -c "import redis" 2>/dev/null && echo -e "${SUCCESS} redis installed" || echo -e "${FAILURE} redis not installed"
    python3 -c "import pydantic" 2>/dev/null && echo -e "${SUCCESS} pydantic installed" || echo -e "${FAILURE} pydantic not installed"
    python3 -c "import pytest" 2>/dev/null && echo -e "${SUCCESS} pytest installed" || echo -e "${WARNING} pytest not installed (required for tests)"
else
    echo -e "${WARNING} Virtual environment not found (backend/venv)"
    echo "   Run: python3 -m venv backend/venv && source backend/venv/bin/activate && pip install -r backend/requirements.txt"
    ((CHECKS_WARNING++))
fi

echo ""
echo "4. CHECKING DOCKER SERVICES..."
echo "-------------------------------------------"

# Check if docker-compose services are running
if docker-compose ps | grep -q "postgres.*Up"; then
    echo -e "${SUCCESS} PostgreSQL container running"
    ((CHECKS_PASSED++))
else
    echo -e "${WARNING} PostgreSQL container not running"
    echo "   Run: docker-compose up -d postgres"
    ((CHECKS_WARNING++))
fi

if docker-compose ps | grep -q "redis.*Up"; then
    echo -e "${SUCCESS} Redis container running"
    ((CHECKS_PASSED++))
else
    echo -e "${WARNING} Redis container not running"
    echo "   Run: docker-compose up -d redis"
    ((CHECKS_WARNING++))
fi

echo ""
echo "5. CHECKING CONFIGURATION..."
echo "-------------------------------------------"

if [ -f ".env" ]; then
    echo -e "${SUCCESS} .env file exists"
    ((CHECKS_PASSED++))

    # Check required variables
    if grep -q "ANTHROPIC_API_KEY=" .env && ! grep -q "ANTHROPIC_API_KEY=your-" .env; then
        echo -e "${SUCCESS} ANTHROPIC_API_KEY configured"
        ((CHECKS_PASSED++))
    else
        echo -e "${WARNING} ANTHROPIC_API_KEY not configured"
        ((CHECKS_WARNING++))
    fi

    if grep -q "SECRET_KEY=" .env && ! grep -q "SECRET_KEY=your-" .env; then
        echo -e "${SUCCESS} SECRET_KEY configured"
        ((CHECKS_PASSED++))
    else
        echo -e "${WARNING} SECRET_KEY not configured"
        ((CHECKS_WARNING++))
    fi

    if grep -q "DATABASE_URL=" .env; then
        echo -e "${SUCCESS} DATABASE_URL configured"
        ((CHECKS_PASSED++))
    else
        echo -e "${WARNING} DATABASE_URL not configured"
        ((CHECKS_WARNING++))
    fi
else
    echo -e "${WARNING} .env file not found"
    echo "   Run: cp .env.example .env"
    ((CHECKS_WARNING++))
fi

echo ""
echo "6. VALIDATING CONFIGURATION..."
echo "-------------------------------------------"

if [ -f "backend/config.py" ] && [ -d "backend/venv" ]; then
    if python3 backend/config.py &> /dev/null; then
        echo -e "${SUCCESS} Configuration validation passed"
        ((CHECKS_PASSED++))
    else
        echo -e "${FAILURE} Configuration validation failed"
        echo "   Run: python backend/config.py"
        ((CHECKS_FAILED++))
    fi
else
    echo -e "${WARNING} Cannot validate configuration (missing files or venv)"
    ((CHECKS_WARNING++))
fi

echo ""
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo ""
echo -e "Passed:   ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Failed:   ${RED}${CHECKS_FAILED}${NC}"
echo -e "Warnings: ${YELLOW}${CHECKS_WARNING}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    if [ $CHECKS_WARNING -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! Week 2 is ready.${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Start services: docker-compose up -d"
        echo "  2. Run migrations: cd backend && alembic upgrade head"
        echo "  3. Start backend: uvicorn main:app --reload"
        echo "  4. Verify health: curl http://localhost:8000/health"
        echo ""
        exit 0
    else
        echo -e "${YELLOW}⚠ Week 2 files present, but some services need configuration.${NC}"
        echo ""
        echo "To fix warnings:"
        echo "  1. Configure .env file: cp .env.example .env"
        echo "  2. Set required variables (ANTHROPIC_API_KEY, SECRET_KEY)"
        echo "  3. Start services: docker-compose up -d"
        echo "  4. Re-run verification: ./verify_week2.sh"
        echo ""
        exit 0
    fi
else
    echo -e "${RED}✗ Some required files are missing.${NC}"
    echo ""
    echo "Please ensure all Week 2 files are present."
    echo "See WEEK2_INTEGRATION_COMPLETE.md for complete file list."
    echo ""
    exit 1
fi

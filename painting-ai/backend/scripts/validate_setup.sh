#!/bin/bash
#
# Database Optimization Validation Script
#
# Verifies all Week 2 deliverables are properly configured
#
# Usage:
#   ./validate_setup.sh
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
FAILURES=0

check_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((SUCCESS++))
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_failure() {
    echo -e "${RED}✗${NC} $1"
    ((FAILURES++))
}

echo "================================================================================"
echo "Database Optimization Validation"
echo "================================================================================"
echo ""

# Check 1: Database connection
echo "1. Checking database connection..."
if psql -h localhost -U paintingai -d paintingai -c "SELECT 1;" > /dev/null 2>&1; then
    check_success "Database connection successful"
else
    check_failure "Cannot connect to database"
fi

# Check 2: Alembic migrations
echo ""
echo "2. Checking database migrations..."
cd /home/user/cooperxxjohn/painting-ai/backend
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oP '\d+' | head -1 || echo "none")
if [ "$CURRENT_VERSION" = "002" ]; then
    check_success "Migration 002 (indexes) applied"
elif [ "$CURRENT_VERSION" = "001" ]; then
    check_warning "Migration 002 not applied yet (run: alembic upgrade head)"
else
    check_failure "No migrations applied"
fi

# Check 3: Index count
echo ""
echo "3. Checking database indexes..."
INDEX_COUNT=$(psql -h localhost -U paintingai -d paintingai -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>/dev/null | xargs || echo "0")
if [ "$INDEX_COUNT" -gt 20 ]; then
    check_success "Found $INDEX_COUNT indexes (expected >20)"
elif [ "$INDEX_COUNT" -gt 0 ]; then
    check_warning "Found only $INDEX_COUNT indexes (expected >20, run migration 002)"
else
    check_failure "No indexes found"
fi

# Check 4: Connection pool configuration
echo ""
echo "4. Checking connection pool configuration..."
if grep -q "pool_size=20" database_service.py; then
    check_success "Connection pool configured (pool_size=20)"
else
    check_failure "Connection pool not configured"
fi

# Check 5: Scripts exist and are executable
echo ""
echo "5. Checking backup/restore scripts..."
if [ -x "scripts/backup_database.sh" ]; then
    check_success "Backup script exists and is executable"
else
    check_failure "Backup script missing or not executable"
fi

if [ -x "scripts/restore_database.sh" ]; then
    check_success "Restore script exists and is executable"
else
    check_failure "Restore script missing or not executable"
fi

if [ -x "scripts/check_backup_status.sh" ]; then
    check_success "Backup verification script exists and is executable"
else
    check_failure "Backup verification script missing or not executable"
fi

# Check 6: Monitoring script
echo ""
echo "6. Checking monitoring script..."
if [ -f "database_monitor.py" ]; then
    check_success "Database monitor script exists"
else
    check_failure "Database monitor script missing"
fi

# Check 7: Performance tests
echo ""
echo "7. Checking performance tests..."
if [ -f "tests/test_database_performance.py" ]; then
    check_success "Performance tests exist"
else
    check_failure "Performance tests missing"
fi

# Check 8: Documentation
echo ""
echo "8. Checking documentation..."
DOCS=0
[ -f "../DATABASE_OPTIMIZATION.md" ] && ((DOCS++))
[ -f "../DATABASE_QUICKSTART.md" ] && ((DOCS++))
[ -f "scripts/README.md" ] && ((DOCS++))

if [ "$DOCS" -eq 3 ]; then
    check_success "All documentation files present"
elif [ "$DOCS" -gt 0 ]; then
    check_warning "Some documentation missing ($DOCS/3 present)"
else
    check_failure "No documentation found"
fi

# Check 9: Python dependencies
echo ""
echo "9. Checking Python dependencies..."
if python -c "import sqlalchemy; from sqlalchemy.pool import QueuePool" 2>/dev/null; then
    check_success "SQLAlchemy with connection pooling available"
else
    check_failure "SQLAlchemy not installed or missing QueuePool"
fi

# Check 10: PostgreSQL client tools
echo ""
echo "10. Checking PostgreSQL tools..."
if command -v pg_dump &> /dev/null; then
    check_success "pg_dump available"
else
    check_warning "pg_dump not found (needed for backups)"
fi

if command -v psql &> /dev/null; then
    check_success "psql available"
else
    check_warning "psql not found"
fi

# Check 11: AWS CLI (optional)
echo ""
echo "11. Checking AWS CLI (optional for S3 backups)..."
if command -v aws &> /dev/null; then
    check_success "AWS CLI available"
else
    check_warning "AWS CLI not found (S3 backups won't work)"
fi

# Check 12: Health check endpoint
echo ""
echo "12. Checking if FastAPI main.py has health endpoint..."
if grep -q "/health/database" main.py; then
    check_success "Health check endpoint configured"
else
    check_failure "Health check endpoint missing"
fi

# Summary
echo ""
echo "================================================================================"
echo "Validation Summary"
echo "================================================================================"
echo -e "${GREEN}✓ Passed:${NC}  $SUCCESS"
echo -e "${YELLOW}⚠ Warnings:${NC} $WARNINGS"
echo -e "${RED}✗ Failed:${NC}  $FAILURES"
echo ""

if [ "$FAILURES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC} Database optimization is complete."
    echo ""
    echo "Next steps:"
    echo "  1. Apply migration: alembic upgrade head"
    echo "  2. Run tests: pytest tests/test_database_performance.py -v"
    echo "  3. Set up cron: crontab scripts/crontab.example"
    echo "  4. Test backup: ./scripts/backup_database.sh daily"
    exit 0
elif [ "$FAILURES" -eq 0 ]; then
    echo -e "${YELLOW}Setup mostly complete${NC} but with warnings."
    echo "Review warnings above and address if needed."
    exit 0
else
    echo -e "${RED}Setup incomplete.${NC} Please fix failures above."
    exit 1
fi

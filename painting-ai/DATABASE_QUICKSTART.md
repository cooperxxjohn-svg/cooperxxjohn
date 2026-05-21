# Database Optimization - Quick Start Guide

Get production database optimizations running in 10 minutes.

## Prerequisites

- PostgreSQL 15+ installed and running
- Python 3.11+ with SQLAlchemy
- AWS CLI installed (for backups)
- S3 bucket created (optional for backups)

## Quick Setup

### 1. Apply Database Migrations

Run the index migration to add performance indexes:

```bash
cd backend

# Apply migrations
alembic upgrade head

# Verify
alembic current
```

**Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Add performance indexes
```

### 2. Test Connection Pool

Verify connection pooling is working:

```python
# In Python or iPython
from database_service import DatabaseService

db = DatabaseService()

# Check pool status
status = db.get_pool_status()
print(status)
# {
#     'pool_size': 20,
#     'checked_in': 20,
#     'checked_out': 0,
#     'overflow': 0,
#     'utilization_percent': 0.0
# }
```

### 3. Run Performance Tests

Verify queries meet performance targets:

```bash
cd backend

# Install test dependencies
pip install pytest pytest-benchmark

# Run tests
pytest tests/test_database_performance.py -v

# With benchmarks
pytest tests/test_database_performance.py -v --benchmark-only
```

**Expected output:**
```
test_user_lookup_by_email_performance PASSED
✓ User lookup by email: 15.23ms

test_project_list_performance PASSED
✓ Project list (10 projects): 45.67ms

All tests passed!
```

### 4. Set Up Backups (Optional)

Configure automated backups:

```bash
cd backend/scripts

# Create backup directory
mkdir -p /tmp/db_backups

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=paintingai
export DB_USER=paintingai
export DB_PASSWORD=changeme123
export S3_BACKUP_BUCKET=painting-ai-backups

# Test backup
./backup_database.sh daily

# Verify
ls -lh /tmp/db_backups/
```

### 5. Install Cron Jobs

Set up automated maintenance:

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily backup at 2 AM
0 2 * * * /path/to/backend/scripts/backup_database.sh daily

# Database monitoring every 15 minutes
*/15 * * * * cd /path/to/backend && python database_monitor.py

# Save and exit

# Verify
crontab -l
```

### 6. Test Health Check Endpoint

Verify API health check works:

```bash
# Start API server
cd backend
python main.py

# In another terminal, test endpoint
curl http://localhost:8000/health/database
```

**Expected response:**
```json
{
  "status": "healthy",
  "response_time_ms": 45.2,
  "database": {
    "size": "245 MB",
    "connections": 12,
    "active_queries": 3
  },
  "connection_pool": {
    "size": 20,
    "checked_out": 5,
    "utilization_percent": 25.0
  },
  "performance": {
    "slow_queries_count": 0
  }
}
```

### 7. Run Database Monitor

Check database health:

```bash
cd backend
python database_monitor.py
```

**Output:**
```
================================================================================
DATABASE MONITORING REPORT
================================================================================

DATABASE STATISTICS
  Database Size: 245 MB
  Total Connections: 12
  Active Queries: 3

CONNECTION POOL
  Pool Size: 20
  Utilization: 25.0%

TABLE SIZES (Top 10)
  projects                  85 MB (12,453 rows)
  rooms                     42 MB (64,231 rows)
  ...

✓ All checks passed
```

## Verification Checklist

- [ ] Migrations applied (`alembic current` shows 002)
- [ ] Connection pool configured (pool_size=20)
- [ ] Indexes created (24+ indexes)
- [ ] Performance tests pass (<100ms queries)
- [ ] Backup script works
- [ ] Restore script works
- [ ] Health check endpoint returns 200
- [ ] Monitor script runs successfully

## Performance Targets

All targets should be met:

| Metric | Target | Check |
|--------|--------|-------|
| User lookup | <100ms | `pytest tests/test_database_performance.py::test_user_lookup_by_email_performance` |
| Project list | <100ms | `pytest tests/test_database_performance.py::test_project_list_performance` |
| Room list | <100ms | `pytest tests/test_database_performance.py::test_room_list_performance` |
| Pool utilization | <80% | `curl http://localhost:8000/health/database` |
| Slow queries | 0 | `python database_monitor.py` |

## Quick Commands

```bash
# Apply migrations
alembic upgrade head

# Run performance tests
pytest tests/test_database_performance.py -v

# Manual backup
./scripts/backup_database.sh daily

# Restore from backup
./scripts/restore_database.sh backup.sql.gz

# Monitor database
python database_monitor.py

# Health check
curl http://localhost:8000/health/database

# Check pool status
python -c "from database_service import db; print(db.get_pool_status())"

# List indexes
psql -U paintingai -d paintingai -c "\di"

# Check slow queries
psql -U paintingai -d paintingai -c "SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '1 second';"
```

## Troubleshooting

### Migrations Won't Apply

```bash
# Check current version
alembic current

# See migration history
alembic history

# Manually stamp version
alembic stamp 001

# Try upgrade again
alembic upgrade head
```

### Connection Pool Not Working

```python
# Check engine configuration
from database_service import db
print(db.engine.pool.size())  # Should be 20
print(db.engine.pool.status())  # Should show pool info
```

### Performance Tests Failing

```bash
# Check database is running
psql -U paintingai -d paintingai -c "SELECT 1;"

# Check indexes exist
psql -U paintingai -d paintingai -c "SELECT indexname FROM pg_indexes WHERE schemaname = 'public';"

# Run single test with verbose output
pytest tests/test_database_performance.py::test_user_lookup_by_email_performance -v -s
```

### Backup Script Fails

```bash
# Check database credentials
psql -h localhost -U paintingai -d paintingai -c "SELECT 1;"

# Check pg_dump is installed
which pg_dump

# Check disk space
df -h /tmp

# Run manually with verbose output
bash -x scripts/backup_database.sh daily
```

## Next Steps

Once basic setup is complete:

1. **Review full documentation**: `DATABASE_OPTIMIZATION.md`
2. **Set up monitoring alerts**: Configure Slack/email notifications
3. **Test backup restoration**: Verify backups work
4. **Tune for your workload**: Adjust pool size based on traffic
5. **Set up read replicas**: For scaling reads

## Support

**Documentation:**
- Full guide: `DATABASE_OPTIMIZATION.md`
- Scripts: `backend/scripts/README.md`

**Logs:**
- Application: `/var/log/paintingai/app.log`
- Backups: `/tmp/db_backups/backup.log`
- Monitoring: `/tmp/db_backups/monitor.log`

**Contact:**
- Email: ops@paintingai.com
- Issues: GitHub Issues
- Slack: #infrastructure

# Week 2 Integration Testing Guide

Quick guide to running Week 2 integration tests.

---

## Prerequisites

1. **PostgreSQL running:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Environment variables set:**
   ```bash
   # Copy and edit .env
   cp .env.example .env
   
   # Minimum required:
   DATABASE_URL=postgresql://paintingai:changeme123@localhost:5432/paintingai
   ANTHROPIC_API_KEY=your-key
   SECRET_KEY=your-secret-key
   ```

3. **Python dependencies installed:**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r tests/requirements-test.txt
   ```

---

## Running Tests

### All Week 2 Integration Tests

```bash
cd backend
pytest tests/test_week2_integration.py -v
```

### Specific Test Classes

```bash
# Database integration only
pytest tests/test_week2_integration.py::TestDatabaseIntegration -v

# Complete workflow tests
pytest tests/test_week2_integration.py::TestCompleteWorkflow -v

# Performance tests
pytest tests/test_week2_integration.py::TestPerformance -v

# Health check tests
pytest tests/test_week2_integration.py::TestHealthChecks -v
```

### Specific Test Functions

```bash
# Test database connection
pytest tests/test_week2_integration.py::TestDatabaseIntegration::test_database_connection -v

# Test complete workflow
pytest tests/test_week2_integration.py::TestCompleteWorkflow::test_complete_project_workflow -v

# Test bulk insert performance
pytest tests/test_week2_integration.py::TestPerformance::test_bulk_insert_performance -v
```

### With Coverage

```bash
pytest tests/test_week2_integration.py --cov=. --cov-report=html -v
```

Coverage report will be in `htmlcov/index.html`

---

## S3 Integration Tests

S3 tests are skipped by default (require AWS credentials).

To enable:

1. **Set S3 environment variables:**
   ```bash
   export S3_ENABLED=true
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export AWS_S3_BUCKET_UPLOADS=test-bucket-uploads
   export AWS_S3_BUCKET_EXPORTS=test-bucket-exports
   ```

2. **Run S3 tests:**
   ```bash
   pytest tests/test_week2_integration.py::TestS3Integration -v
   ```

---

## Test Database

Tests use a separate test database to avoid affecting development data.

**Default test database:**
```
postgresql://paintingai:changeme123@localhost:5432/paintingai_test
```

**To use custom test database:**
```bash
export TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db
```

---

## Expected Output

```
tests/test_week2_integration.py::TestDatabaseIntegration::test_database_connection PASSED [7%]
tests/test_week2_integration.py::TestDatabaseIntegration::test_connection_pool_status PASSED [14%]
tests/test_week2_integration.py::TestDatabaseIntegration::test_user_crud_operations PASSED [21%]
tests/test_week2_integration.py::TestDatabaseIntegration::test_project_crud_operations PASSED [28%]
tests/test_week2_integration.py::TestDatabaseIntegration::test_room_operations PASSED [35%]
tests/test_week2_integration.py::TestDatabaseIntegration::test_drawing_operations PASSED [42%]
tests/test_week2_integration.py::TestCompleteWorkflow::test_complete_project_workflow PASSED [50%]
tests/test_week2_integration.py::TestCompleteWorkflow::test_multi_user_isolation PASSED [57%]
tests/test_week2_integration.py::TestDatabaseBackupRestore::test_database_export_import PASSED [64%]
tests/test_week2_integration.py::TestHealthChecks::test_database_health PASSED [71%]
tests/test_week2_integration.py::TestHealthChecks::test_connection_pool_health PASSED [78%]
tests/test_week2_integration.py::TestPerformance::test_bulk_insert_performance PASSED [85%]
tests/test_week2_integration.py::TestPerformance::test_query_performance PASSED [92%]

========== 13 passed in 8.5s ==========
```

---

## Troubleshooting

### PostgreSQL connection refused

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for it to be ready
docker-compose logs postgres | grep "ready to accept connections"

# Test connection
psql postgresql://paintingai:changeme123@localhost:5432/paintingai -c "SELECT 1"
```

### Test database doesn't exist

```bash
# Create test database
psql postgresql://paintingai:changeme123@localhost:5432/postgres -c "CREATE DATABASE paintingai_test;"
```

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -r tests/requirements-test.txt

# Verify pytest is installed
pytest --version
```

### Slow tests

Integration tests are slower than unit tests (use real database).

To run faster:
```bash
# Run with multiple workers (requires pytest-xdist)
pip install pytest-xdist
pytest tests/test_week2_integration.py -v -n 4
```

---

## Test Structure

```
test_week2_integration.py
├── TestDatabaseIntegration
│   ├── test_database_connection
│   ├── test_connection_pool_status
│   ├── test_user_crud_operations
│   ├── test_project_crud_operations
│   ├── test_room_operations
│   └── test_drawing_operations
├── TestCompleteWorkflow
│   ├── test_complete_project_workflow
│   └── test_multi_user_isolation
├── TestS3Integration (skipped if S3 not enabled)
│   └── test_s3_upload_download
├── TestDatabaseBackupRestore
│   └── test_database_export_import
├── TestHealthChecks
│   ├── test_database_health
│   └── test_connection_pool_health
└── TestPerformance
    ├── test_bulk_insert_performance
    └── test_query_performance
```

---

## Performance Benchmarks

Tests include performance assertions:

| Test | Requirement | Typical |
|------|-------------|---------|
| Bulk insert (100 projects) | < 5s | ~0.9s |
| Query (50 projects) | < 100ms | ~50ms |
| Connection pool | 20+ connections | 20 |

If tests are slower, check:
- Database is running locally (not remote)
- SSD storage (not HDD)
- Sufficient RAM (2GB+ for PostgreSQL)

---

## Continuous Integration

To run in CI/CD:

```yaml
# .github/workflows/test.yml
- name: Start PostgreSQL
  run: docker-compose up -d postgres
  
- name: Wait for PostgreSQL
  run: |
    timeout 30 bash -c 'until docker-compose exec -T postgres pg_isready; do sleep 1; done'

- name: Run Week 2 Integration Tests
  run: |
    cd backend
    pytest tests/test_week2_integration.py -v --junitxml=test-results.xml
```

---

## Next Steps

After tests pass:
1. Run all tests: `./run_tests.sh`
2. Check coverage: `pytest --cov=. --cov-report=html`
3. Start application: `uvicorn main:app --reload`
4. Verify health: `curl http://localhost:8000/health`

---

**Happy Testing!** ✅

# Quick Start Guide - API Integration Tests

## Installation

```bash
cd /home/user/cooperxxjohn/painting-ai/backend
pip install -r tests/requirements-test.txt
```

## Run Tests

```bash
# All tests
./run_tests.sh

# Specific test file
./run_tests.sh --auth        # Authentication tests
./run_tests.sh --projects    # Project tests
./run_tests.sh --rooms       # Room tests
./run_tests.sh --upload      # Upload tests
./run_tests.sh --exports     # Export tests
./run_tests.sh --public      # Public API tests
./run_tests.sh --settings    # Settings tests

# With coverage
./run_tests.sh --coverage

# Quiet mode
./run_tests.sh --quiet
```

## Using pytest directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api_auth.py -v

# Run specific test class
pytest tests/test_api_auth.py::TestAuthRegistration -v

# Run specific test
pytest tests/test_api_auth.py::TestAuthRegistration::test_register_success -v

# Run with markers
pytest tests/ -m auth -v

# Parallel execution
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -v -s
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_api_auth.py         # Authentication (30+ tests)
├── test_api_projects.py     # Projects (35+ tests)
├── test_api_rooms.py        # Rooms (25+ tests)
├── test_api_upload.py       # Uploads (25+ tests)
├── test_api_exports.py      # Exports (20+ tests)
├── test_api_public.py       # Public API (35+ tests)
└── test_api_settings.py     # Settings (15+ tests)
```

## Key Fixtures

```python
# From conftest.py
test_client          # Sync FastAPI test client
async_client         # Async HTTP client
db                   # Database instance
auth_manager         # Auth manager
test_user            # Authenticated user with JWT
test_project         # Created project
auth_headers         # JWT auth headers
api_key_headers      # API key headers
sample_room_with_surfaces  # Room with surface data
```

## Example Test Usage

```python
def test_create_project(test_client, test_project_data):
    """Test creating a project"""
    response = test_client.post("/projects", json=test_project_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_project_data["name"]
    assert "id" in data

def test_protected_endpoint(test_client, auth_headers):
    """Test protected endpoint requires auth"""
    response = test_client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    assert "user" in response.json()
```

## Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=. --cov-report=term-missing
```

## Troubleshooting

### Tests fail with import errors
```bash
# Ensure you're in the backend directory
cd /home/user/cooperxxjohn/painting-ai/backend

# Install dependencies
pip install -r tests/requirements-test.txt
```

### Database connection errors
```bash
# Check database is running
# Set environment variables if needed
export DATABASE_URL="your-database-url"
```

### Authentication errors
```bash
# Ensure JWT secret is set
export JWT_SECRET_KEY="your-secret-key-min-32-chars"
```

### API key errors
```bash
# For tests using external APIs
export ANTHROPIC_API_KEY="your-key"
```

## Test Categories

- **Happy Path**: Valid requests return expected results
- **Validation**: Invalid data returns 422
- **Authentication**: No/invalid token returns 401
- **Authorization**: Users can only access their data
- **Error Handling**: Proper error codes and messages
- **Edge Cases**: Boundary conditions, special chars, etc.

## Common Patterns

### Test project workflow
```python
def test_complete_workflow(test_client, test_project_data):
    # Create project
    project_response = test_client.post("/projects", json=test_project_data)
    project_id = project_response.json()["id"]
    
    # Upload file
    files = {"file": ("drawing.pdf", pdf_content, "application/pdf")}
    upload_response = test_client.post(
        f"/projects/{project_id}/upload", 
        files=files
    )
    
    # Generate estimate
    estimate_response = test_client.post(
        f"/projects/{project_id}/estimate",
        json={"paint_price": 55.0, "labor_rate": 50.0}
    )
    
    # Export
    export_response = test_client.get(
        f"/projects/{project_id}/export/excel"
    )
    
    assert all([
        project_response.status_code == 200,
        upload_response.status_code == 200,
        estimate_response.status_code == 200,
        export_response.status_code == 200
    ])
```

## Help

- See `README.md` for comprehensive documentation
- See `TESTING_SUMMARY.md` for detailed overview
- Run `./run_tests.sh --help` for script options

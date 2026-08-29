# Painting.ai API Integration Tests

Comprehensive integration tests for all Painting.ai backend API endpoints.

## Test Coverage

### Authentication Tests (`test_api_auth.py`)
- ✅ POST /auth/register - User registration
- ✅ POST /auth/login - User login
- ✅ POST /auth/refresh - Token refresh
- ✅ GET /auth/me - Current user info
- ✅ POST /auth/logout - Logout

**Coverage:**
- Valid registration with all fields
- Duplicate email validation
- Missing required fields (422)
- Invalid email format
- Successful login
- Wrong password (401)
- Non-existent user (401)
- Token refresh with valid/invalid tokens
- Expired token handling

### Project Tests (`test_api_projects.py`)
- ✅ POST /projects - Create project
- ✅ GET /projects - List all projects
- ✅ GET /projects/{id} - Get project details
- ✅ GET /projects/{id}/status - Get processing status
- ✅ POST /projects/{id}/estimate - Generate estimate
- ✅ POST /projects/{id}/assembly-expansion - Assembly expansion
- ✅ GET /projects/{id}/rooms - Get project rooms
- ✅ DELETE /projects/{id} - Delete project

**Coverage:**
- Create project with full/minimal data
- Missing name validation (422)
- List empty/populated projects
- Get by ID, not found (404)
- Estimate generation with/without rooms
- Custom estimate parameters
- Assembly expansion validation
- Cascade delete (rooms deleted with project)

### Room Tests (`test_api_rooms.py`)
- ✅ GET /rooms/{id} - Get room details
- ✅ PATCH /rooms/{id} - Update room

**Coverage:**
- Get room with surfaces
- Room not found (404)
- Update name, dimensions, notes
- Multiple field updates
- Empty payload handling
- Invalid data types (422)
- Negative/zero/large dimensions
- Surface data preservation

### Upload Tests (`test_api_upload.py`)
- ✅ POST /projects/{id}/upload - Upload drawings

**Coverage:**
- Upload PDF, PNG, JPG files
- Project not found (404)
- Invalid file types (400)
- Empty file (400)
- Corrupted PDF (400)
- File size limit (50MB)
- No file provided (422)
- Status updates
- Upload record tracking
- Multiple uploads per project
- Special characters in filename

### Export Tests (`test_api_exports.py`)
- ✅ GET /projects/{id}/export/excel - Export to Excel
- ✅ GET /projects/{id}/export/pdf - Export to PDF

**Coverage:**
- Successful exports
- Project not found (404)
- Empty project export
- Filename generation
- File creation in outputs/
- Multiple rooms
- PDF format validation
- Both formats for same project
- Customer information inclusion

### Public API Tests (`test_api_public.py`)
- ✅ GET / - Root endpoint
- ✅ GET /health - Health check
- ✅ GET /pricing/plans - Pricing plans
- ✅ GET /analytics/overview - Analytics (auth required)
- ✅ GET /analytics/usage - Usage analytics (auth required)
- ✅ GET /analytics/conversion - Conversion metrics (auth required)
- ✅ GET /usage/stats - Usage statistics (auth required)
- ✅ POST /checkout/create-session - Create checkout (auth required)
- ✅ POST /checkout/portal - Customer portal (auth required)
- ✅ POST /checkout/webhook - Stripe webhook

**Coverage:**
- Public endpoints (no auth)
- Protected endpoints (401 without auth)
- Invalid plan validation
- Missing required fields (422)
- Webhook signature validation
- API key authentication
- JWT token validation
- Error response formats
- 404 for unknown routes
- 405 for wrong methods

### Settings Tests (`test_api_settings.py`)
- ✅ GET /auth/me - User profile
- ✅ API key management
- ✅ User plan information
- ✅ Authorization boundaries

**Coverage:**
- User profile fields
- Trial plan for new users
- API key uniqueness
- Password security (never exposed)
- Token refresh flow
- Complete auth flow
- Authorization boundaries

## Running Tests

### Run All Tests
```bash
cd /home/user/cooperxxjohn/painting-ai/backend
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_api_auth.py -v
pytest tests/test_api_projects.py -v
pytest tests/test_api_rooms.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_api_auth.py::TestAuthRegistration -v
```

### Run Specific Test
```bash
pytest tests/test_api_auth.py::TestAuthRegistration::test_register_success -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run Tests in Parallel
```bash
pytest tests/ -n auto
```

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_api_auth.py           # Authentication endpoint tests
├── test_api_projects.py       # Project endpoint tests
├── test_api_rooms.py          # Room endpoint tests
├── test_api_upload.py         # File upload tests
├── test_api_exports.py        # Export endpoint tests
├── test_api_public.py         # Public API tests
└── test_api_settings.py       # User settings tests
```

## Fixtures (conftest.py)

### Database & Services
- `db` - Database instance
- `auth_manager` - Authentication manager
- `test_client` - Synchronous test client
- `async_client` - Async test client

### Test Data
- `test_user_data` - User registration data
- `test_user` - Created user with tokens
- `test_project_data` - Project creation data
- `test_project` - Created project
- `test_room_data` - Room data
- `sample_room_with_surfaces` - Complete room with surfaces
- `estimate_params` - Default estimate parameters

### Authentication
- `auth_headers` - JWT authorization headers
- `api_key_headers` - API key headers
- `invalid_jwt_token` - Invalid token for testing
- `expired_jwt_token` - Expired token for testing

## Test Categories

### Happy Path Tests ✅
- Valid requests return 200/201
- Correct response structure
- Data persistence verification

### Validation Tests ✅
- Missing required fields → 422
- Invalid data types → 422
- Invalid formats → 400/422

### Authentication Tests ✅
- No auth → 401
- Invalid token → 401
- Expired token → 401
- Valid token → 200

### Authorization Tests ✅
- Users access only their data
- Invalid API keys rejected
- Protected routes enforced

### Error Handling Tests ✅
- Not found → 404
- Method not allowed → 405
- Business logic errors → 400
- Server errors → 500

### Edge Cases ✅
- Empty collections
- Missing optional fields
- Large values
- Special characters
- Unicode support

## Success Criteria

✅ All endpoints tested
✅ Auth/authz verified  
✅ Error cases covered
✅ Tests pass independently
✅ Fixtures shared efficiently
✅ Clear test organization
✅ Comprehensive coverage

## Dependencies

```
pytest
pytest-asyncio
httpx
fastapi
```

## Environment

Tests use the same database and services as the main application. Ensure:
- Database is accessible
- Required environment variables are set
- Dependencies are installed

## Notes

- Tests create temporary data (projects, users, rooms)
- Each test should be independent
- Use fixtures for common setup
- Clean up after tests when needed
- Mock external services (Stripe, email)

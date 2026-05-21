# Testing Guide - Painting.ai

Comprehensive testing documentation for backend and frontend.

## 📋 Table of Contents

- [Testing Strategy](#testing-strategy)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [E2E Testing](#e2e-testing)
- [Test Coverage](#test-coverage)
- [CI/CD Integration](#cicd-integration)
- [Manual Testing Checklist](#manual-testing-checklist)

## 🎯 Testing Strategy

### Testing Pyramid

```
        /\
       /  \      E2E Tests (5-10%)
      /____\     - Critical user flows
     /      \    - Happy path scenarios
    /________\   
   /          \  Integration Tests (20-30%)
  /____________\ - API endpoints
 /              \ - Database operations
/________________\ Unit Tests (60-70%)
                  - Business logic
                  - Calculations
                  - Utilities
```

### Test Coverage Goals

- **Backend:** 70%+ code coverage
- **Frontend:** 60%+ code coverage
- **Critical Paths:** 100% coverage
  - Authentication
  - Payment processing
  - AI room detection
  - Calculation engines

## 🔧 Backend Testing

### Setup

```bash
cd backend

# Install dependencies (if not already)
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_register_user

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Test Structure

```
backend/tests/
├── conftest.py              # Pytest fixtures & configuration
├── test_auth.py             # Authentication tests
├── test_api.py              # API endpoint tests
├── test_calculations.py     # Paint calculation tests
├── test_payments.py         # Stripe integration tests
├── test_email.py            # Email service tests
├── test_exports.py          # Excel/PDF generation tests
├── test_assembly.py         # Assembly expansion tests
└── test_database.py         # Database operations tests
```

### Writing Backend Tests

**Authentication Test Example:**
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    """Test user registration"""
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123",
        "full_name": "Test User",
        "company_name": "Test Company"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert "access_token" in data
    assert "refresh_token" in data

def test_login():
    """Test user login"""
    # First register
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "SecurePass123",
        "full_name": "Login User"
    })
    
    # Then login
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "SecurePass123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

**API Endpoint Test Example:**
```python
import pytest

@pytest.fixture
def authenticated_client():
    """Fixture that returns authenticated test client"""
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123"
    })
    token = response.json()["access_token"]
    
    # Create new client with auth header
    from fastapi.testclient import TestClient
    test_client = TestClient(app)
    test_client.headers = {"Authorization": f"Bearer {token}"}
    return test_client

def test_create_project(authenticated_client):
    """Test project creation"""
    response = authenticated_client.post("/projects", json={
        "name": "Test Project",
        "customer": "Test Customer",
        "address": "123 Test St"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["customer"] == "Test Customer"
    assert "id" in data

def test_get_projects(authenticated_client):
    """Test listing projects"""
    # Create a project first
    authenticated_client.post("/projects", json={
        "name": "Project 1"
    })
    
    # Get projects
    response = authenticated_client.get("/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) > 0
```

**Calculation Test Example:**
```python
from painting_detector import PaintCalculator

def test_paint_calculation():
    """Test paint coverage calculation"""
    calc = PaintCalculator()
    
    # Smooth drywall: 400 sqft/gallon
    gallons = calc.calculate_paint_needed(
        surface_area=800,
        coats=2,
        surface_type="smooth_drywall"
    )
    
    # 800 sqft * 2 coats / 400 sqft/gallon = 4 gallons
    assert gallons == 4.0

def test_labor_calculation():
    """Test labor hours calculation"""
    calc = PaintCalculator()
    
    # Walls: 300 sqft/hour
    hours = calc.calculate_labor_hours(
        surface_area=900,
        surface_type="walls"
    )
    
    # 900 sqft / 300 sqft/hour = 3 hours
    assert hours == 3.0
```

**Mocking External APIs:**
```python
import pytest
from unittest.mock import Mock, patch

@patch('painting_detector.anthropic.Anthropic')
def test_room_detection_mock(mock_anthropic):
    """Test room detection with mocked Claude API"""
    # Mock the API response
    mock_response = Mock()
    mock_response.content = [Mock(text=json.dumps({
        "rooms": [
            {
                "name": "Living Room",
                "length": 20,
                "width": 15,
                "height": 9
            }
        ]
    }))]
    
    mock_anthropic.return_value.messages.create.return_value = mock_response
    
    # Test the detector
    detector = PaintingDetector("fake-api-key")
    rooms = detector.detect_rooms_from_image("test.pdf")
    
    assert len(rooms) == 1
    assert rooms[0].name == "Living Room"
```

### Running Backend Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_auth.py

# Specific test function
pytest tests/test_auth.py::test_register_user

# Tests matching pattern
pytest -k "auth"

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show 10 slowest tests
pytest --durations=10

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## ⚛️ Frontend Testing

### Setup

```bash
cd frontend

# Install dependencies (if not already)
npm install

# Run unit tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Test Structure

```
frontend/src/
├── __tests__/
│   ├── components/
│   │   ├── Layout.test.jsx
│   │   ├── ProtectedRoute.test.jsx
│   │   └── RoomEditor.test.jsx
│   ├── pages/
│   │   ├── Login.test.jsx
│   │   ├── Dashboard.test.jsx
│   │   └── Upload.test.jsx
│   ├── store/
│   │   ├── authStore.test.js
│   │   └── toastStore.test.js
│   └── utils/
│       └── api.test.js
└── setupTests.js           # Test setup & global config
```

### Writing Frontend Tests

**Component Test Example:**
```javascript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'

describe('Login Component', () => {
  it('renders login form', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
  
  it('submits login form', async () => {
    const mockLogin = vi.fn()
    
    render(
      <BrowserRouter>
        <Login onLogin={mockLogin} />
      </BrowserRouter>
    )
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' }
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    // Wait for async operations
    await screen.findByText(/signing in/i)
  })
})
```

**Store Test Example:**
```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import useAuthStore from '../store/authStore'

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useAuthStore.getState().clearAuth()
  })
  
  it('sets auth correctly', () => {
    const user = { id: '1', email: 'test@example.com' }
    const accessToken = 'token123'
    const refreshToken = 'refresh123'
    
    useAuthStore.getState().setAuth(user, accessToken, refreshToken)
    
    const state = useAuthStore.getState()
    expect(state.user).toEqual(user)
    expect(state.accessToken).toBe(accessToken)
    expect(state.refreshToken).toBe(refreshToken)
    expect(state.isAuthenticated).toBe(true)
  })
  
  it('clears auth correctly', () => {
    useAuthStore.getState().setAuth({ id: '1' }, 'token', 'refresh')
    useAuthStore.getState().clearAuth()
    
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
```

**API Mock Test Example:**
```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { getProjects, createProject } from '../utils/api'

vi.mock('axios')

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  it('fetches projects', async () => {
    const mockProjects = [
      { id: '1', name: 'Project 1' },
      { id: '2', name: 'Project 2' }
    ]
    
    axios.get.mockResolvedValue({ data: mockProjects })
    
    const projects = await getProjects()
    expect(projects).toEqual(mockProjects)
    expect(axios.get).toHaveBeenCalledWith('/projects')
  })
  
  it('creates project', async () => {
    const newProject = { name: 'New Project', customer: 'Customer' }
    const createdProject = { id: '3', ...newProject }
    
    axios.post.mockResolvedValue({ data: createdProject })
    
    const result = await createProject(newProject)
    expect(result).toEqual(createdProject)
    expect(axios.post).toHaveBeenCalledWith('/projects', newProject)
  })
})
```

## 🧪 E2E Testing

### Setup Playwright

```bash
cd frontend

# Install Playwright
npm install -D @playwright/test

# Install browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test tests/e2e/login.spec.js

# Debug mode
npm run test:e2e:debug
```

### E2E Test Structure

```
frontend/tests/e2e/
├── login.spec.js           # Login flow
├── register.spec.js        # Registration flow
├── upload.spec.js          # File upload flow
├── project.spec.js         # Project management
└── payment.spec.js         # Payment flow
```

### Writing E2E Tests

**Login Flow Example:**
```javascript
import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('user can login', async ({ page }) => {
    await page.goto('http://localhost:3000/login')
    
    // Fill login form
    await page.fill('input[name="email"]', 'demo@painting.ai')
    await page.fill('input[name="password"]', 'demo123')
    
    // Submit form
    await page.click('button[type="submit"]')
    
    // Wait for navigation to dashboard
    await expect(page).toHaveURL(/.*dashboard/)
    
    // Verify dashboard content
    await expect(page.getByText('Projects')).toBeVisible()
  })
  
  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/login')
    
    await page.fill('input[name="email"]', 'wrong@example.com')
    await page.fill('input[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')
    
    // Verify error message
    await expect(page.getByText(/failed to sign in/i)).toBeVisible()
  })
})
```

**Upload Flow Example:**
```javascript
import { test, expect } from '@playwright/test'
import path from 'path'

test.describe('File Upload', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:3000/login')
    await page.fill('input[name="email"]', 'demo@painting.ai')
    await page.fill('input[name="password"]', 'demo123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/.*dashboard/)
  })
  
  test('user can upload floor plan', async ({ page }) => {
    // Navigate to upload
    await page.click('text=Upload')
    
    // Fill project details
    await page.fill('input[name="name"]', 'Test Project')
    await page.fill('input[name="customer"]', 'Test Customer')
    
    // Upload file
    const filePath = path.join(__dirname, 'fixtures', 'test-floor-plan.pdf')
    await page.setInputFiles('input[type="file"]', filePath)
    
    // Submit
    await page.click('button:has-text("Upload & Process")')
    
    // Wait for processing
    await expect(page.getByText(/processing/i)).toBeVisible()
    
    // Should redirect to project view
    await expect(page).toHaveURL(/.*projects\/.*/, { timeout: 30000 })
  })
  
  test('validates file size', async ({ page }) => {
    await page.click('text=Upload')
    
    // Try to upload large file (>50MB)
    const largFilePath = path.join(__dirname, 'fixtures', 'large-file.pdf')
    await page.setInputFiles('input[type="file"]', largeFilePath)
    
    // Should show error
    await expect(page.getByText(/file size must be less than 50mb/i)).toBeVisible()
  })
})
```

**Full User Journey:**
```javascript
import { test, expect } from '@playwright/test'

test('complete user journey', async ({ page }) => {
  // 1. Register
  await page.goto('http://localhost:3000/register')
  await page.fill('input[name="email"]', `test-${Date.now()}@example.com`)
  await page.fill('input[name="password"]', 'SecurePass123')
  await page.fill('input[name="full_name"]', 'Test User')
  await page.click('button[type="submit"]')
  
  // 2. Should be on dashboard
  await expect(page).toHaveURL(/.*dashboard/)
  
  // 3. Create project
  await page.click('text=Upload')
  await page.fill('input[name="name"]', 'E2E Test Project')
  await page.setInputFiles('input[type="file"]', 'test-plan.pdf')
  await page.click('button:has-text("Upload & Process")')
  
  // 4. Wait for project to be created
  await expect(page).toHaveURL(/.*projects\/.*/, { timeout: 30000 })
  
  // 5. Verify project details
  await expect(page.getByText('E2E Test Project')).toBeVisible()
  
  // 6. Export Excel
  await page.click('button:has-text("Export Excel")')
  
  // Wait for download
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('button:has-text("Download")')
  ])
  
  expect(download.suggestedFilename()).toContain('.xlsx')
})
```

## 📊 Test Coverage

### Viewing Coverage Reports

**Backend:**
```bash
cd backend
pytest --cov=. --cov-report=html
# Open coverage/index.html in browser
```

**Frontend:**
```bash
cd frontend
npm run test:coverage
# Open coverage/index.html in browser
```

### Coverage Targets

**Backend - Critical Modules (100% coverage):**
- `auth_jwt.py` - Authentication
- `payments.py` - Payment processing
- `painting_detector.py` - Paint calculations
- `assembly_expansion.py` - Assembly logic

**Frontend - Critical Components (90%+ coverage):**
- `pages/Login.jsx`
- `pages/Register.jsx`
- `components/ProtectedRoute.jsx`
- `store/authStore.js`
- `utils/api.js`

## 🔄 CI/CD Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json

  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Start backend
        run: |
          cd backend
          uvicorn main:app --port 8000 &
          sleep 5
      
      - name: Start frontend
        run: |
          cd frontend
          npm run dev &
          sleep 5
      
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## ✅ Manual Testing Checklist

### Authentication
- [ ] Register new account
- [ ] Login with valid credentials
- [ ] Login with invalid credentials shows error
- [ ] Logout clears session
- [ ] Protected routes redirect to login
- [ ] Token refresh works on expiry
- [ ] "Remember me" persists session

### File Upload
- [ ] Upload PDF file (< 50MB)
- [ ] Upload PNG file (< 50MB)
- [ ] Upload JPG file (< 50MB)
- [ ] File > 50MB shows error
- [ ] Invalid file type shows error
- [ ] Drag and drop works
- [ ] Progress indicator shows during upload
- [ ] Success notification after upload

### Project Management
- [ ] Create new project
- [ ] View project list
- [ ] View project details
- [ ] Edit project details
- [ ] Delete project
- [ ] Project statistics calculate correctly

### Room Editor
- [ ] View room list
- [ ] Edit room dimensions
- [ ] Add new room manually
- [ ] Delete room
- [ ] Room calculations update in real-time

### Exports
- [ ] Generate Excel export
- [ ] Download Excel file
- [ ] Excel contains all expected data
- [ ] Generate PDF proposal
- [ ] Download PDF file
- [ ] PDF formatting is correct

### Payments
- [ ] View pricing plans
- [ ] Start Stripe checkout
- [ ] Complete payment (test mode)
- [ ] View success page
- [ ] Subscription status updates
- [ ] Access customer portal
- [ ] Cancel subscription

### Responsive Design
- [ ] Mobile (320px width) - all features work
- [ ] Mobile (414px width) - all features work
- [ ] Tablet (768px width) - all features work
- [ ] Desktop (1024px width) - all features work
- [ ] Desktop (1920px width) - all features work

### Browser Compatibility
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Error Handling
- [ ] Network error shows toast
- [ ] 500 error shows error boundary
- [ ] 404 shows not found page
- [ ] Validation errors show inline
- [ ] Error boundary "Try Again" works

## 📝 Test Reporting

### Generate Test Reports

```bash
# Backend - JUnit XML report
pytest --junitxml=test-results.xml

# Frontend - JUnit XML report
npm run test -- --reporter=junit --outputFile=test-results.xml

# E2E - HTML report
npx playwright test --reporter=html
```

### View Reports

- **Backend Coverage:** `backend/htmlcov/index.html`
- **Frontend Coverage:** `frontend/coverage/index.html`
- **E2E Report:** `frontend/playwright-report/index.html`

---

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library](https://testing-library.com/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Questions?** Contact cooperxxjohn@gmail.com

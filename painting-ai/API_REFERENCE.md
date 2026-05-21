# Painting.ai API Reference

Complete API documentation for all endpoints.

## 📋 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Auth Endpoints](#auth-endpoints)
- [Project Endpoints](#project-endpoints)
- [Room Endpoints](#room-endpoints)
- [Export Endpoints](#export-endpoints)
- [Payment Endpoints](#payment-endpoints)
- [Analytics Endpoints](#analytics-endpoints)
- [Public API](#public-api)
- [Webhooks](#webhooks)

## 🌐 Base URL

**Production:** `https://api.painting.ai`  
**Development:** `http://localhost:8000`

## 🔐 Authentication

### JWT Authentication (User API)

Most endpoints require a JWT access token obtained from login/registration.

**Include token in headers:**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Token Expiry:**
- Access Token: 24 hours
- Refresh Token: 30 days

### API Key Authentication (Public API)

Public API endpoints use API key authentication.

**Include API key in headers:**
```http
X-API-Key: pk_your_api_key_here
```

## 🚦 Rate Limiting

**User API:**
- No explicit rate limit (fair use)
- 100 concurrent requests per user

**Public API:**
- 100 requests/minute
- 5,000 requests/hour
- 100,000 requests/day

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1621234567
```

## ❌ Error Handling

### Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR"
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_REQUIRED` - No auth token provided
- `INVALID_TOKEN` - Token invalid or expired
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `PERMISSION_DENIED` - User lacks permission
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `FILE_TOO_LARGE` - File exceeds 50MB limit
- `INVALID_FILE_TYPE` - Unsupported file format
- `SUBSCRIPTION_REQUIRED` - Upgrade required
- `PAYMENT_FAILED` - Payment processing failed

## 🔑 Auth Endpoints

### Register User

Create a new user account with 14-day free trial.

```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "company_name": "ABC Painting"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "company_name": "ABC Painting",
    "plan": "trial",
    "trial_ends_at": "2026-06-03T12:00:00Z",
    "created_at": "2026-05-20T12:00:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Validation:**
- Email: Valid email format
- Password: Minimum 8 characters
- Full name: Required

---

### Login

Authenticate user and receive JWT tokens.

```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "plan": "pro"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials

---

### Refresh Token

Get new access token using refresh token.

```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### Get Current User

Get authenticated user's profile.

```http
GET /auth/me
```

**Headers:**
```http
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "company_name": "ABC Painting",
  "plan": "pro",
  "subscription_status": "active",
  "trial_ends_at": null,
  "projects_used": 25,
  "projects_limit": null,
  "api_key": "pk_abc123...",
  "created_at": "2026-05-20T12:00:00Z"
}
```

---

### Logout

Invalidate current session.

```http
POST /auth/logout
```

**Headers:**
```http
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

## 📁 Project Endpoints

### List Projects

Get all projects for authenticated user.

```http
GET /projects
```

**Query Parameters:**
- `status` (optional): Filter by status (`created`, `processing`, `complete`, `failed`)
- `limit` (optional): Number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "proj_abc123",
    "name": "Office Renovation",
    "customer": "ABC Construction",
    "address": "123 Main St, San Francisco, CA",
    "status": "complete",
    "total_rooms": 8,
    "total_sqft": 2500.0,
    "total_gallons": 20.5,
    "total_labor_hours": 32.0,
    "estimated_cost": 5000.0,
    "created_at": "2026-05-20T12:00:00Z",
    "updated_at": "2026-05-20T14:30:00Z"
  }
]
```

---

### Create Project

Create a new painting project.

```http
POST /projects
```

**Request Body:**
```json
{
  "name": "Office Renovation",
  "customer": "ABC Construction",
  "address": "123 Main St, San Francisco, CA"
}
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123",
  "name": "Office Renovation",
  "customer": "ABC Construction",
  "address": "123 Main St, San Francisco, CA",
  "status": "created",
  "total_rooms": 0,
  "total_sqft": 0.0,
  "estimated_cost": 0.0,
  "created_at": "2026-05-20T12:00:00Z"
}
```

**Errors:**
- `403 Forbidden` - Project limit exceeded (upgrade required)

---

### Get Project

Get details of a specific project.

```http
GET /projects/{project_id}
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123",
  "name": "Office Renovation",
  "customer": "ABC Construction",
  "address": "123 Main St, San Francisco, CA",
  "status": "complete",
  "total_rooms": 8,
  "total_sqft": 2500.0,
  "total_gallons": 20.5,
  "total_labor_hours": 32.0,
  "estimated_cost": 5000.0,
  "created_at": "2026-05-20T12:00:00Z",
  "updated_at": "2026-05-20T14:30:00Z",
  "rooms": [
    {
      "id": "room_xyz789",
      "name": "Conference Room",
      "length": 20.0,
      "width": 15.0,
      "height": 9.0,
      "wall_area": 630.0,
      "ceiling_area": 300.0,
      "trim_length": 70.0
    }
  ]
}
```

**Errors:**
- `404 Not Found` - Project doesn't exist

---

### Update Project

Update project details.

```http
PATCH /projects/{project_id}
```

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "customer": "New Customer Name",
  "address": "New Address"
}
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123",
  "name": "Updated Project Name",
  "customer": "New Customer Name",
  "address": "New Address",
  "status": "complete",
  "updated_at": "2026-05-20T15:00:00Z"
}
```

---

### Delete Project

Delete a project and all associated data.

```http
DELETE /projects/{project_id}
```

**Response:** `200 OK`
```json
{
  "message": "Project deleted successfully"
}
```

---

### Upload Floor Plan

Upload PDF/image floor plan for AI processing.

```http
POST /projects/{project_id}/upload
```

**Request:**
- Content-Type: `multipart/form-data`
- Field name: `file`
- Max size: 50MB
- Allowed types: `.pdf`, `.png`, `.jpg`, `.jpeg`

**Example (curl):**
```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -F "file=@floor-plan.pdf" \
  https://api.painting.ai/projects/proj_abc123/upload
```

**Response:** `200 OK`
```json
{
  "message": "File uploaded successfully",
  "file_id": "file_xyz789",
  "filename": "floor-plan.pdf",
  "size": 2457600,
  "status": "processing"
}
```

**Errors:**
- `400 Bad Request` - Invalid file type or size
- `422 Unprocessable Entity` - File processing failed

---

### Get Project Rooms

Get all rooms for a project.

```http
GET /projects/{project_id}/rooms
```

**Response:** `200 OK`
```json
[
  {
    "id": "room_xyz789",
    "name": "Conference Room",
    "length": 20.0,
    "width": 15.0,
    "height": 9.0,
    "wall_area": 630.0,
    "ceiling_area": 300.0,
    "trim_length": 70.0,
    "paint_gallons": 3.5,
    "labor_hours": 5.2
  }
]
```

---

### Expand Assembly

Generate detailed assembly line items (80-120 items).

```http
POST /projects/{project_id}/expand-assembly
```

**Response:** `200 OK`
```json
{
  "message": "Assembly expanded successfully",
  "assembly_count": 95,
  "assemblies": [
    {
      "id": "asm_001",
      "category": "Prep Work",
      "description": "Mask windows and trim - Conference Room",
      "quantity": 12.0,
      "unit": "LF",
      "unit_price": 0.50,
      "total_price": 6.00
    },
    {
      "id": "asm_002",
      "category": "Prime",
      "description": "Prime walls - Conference Room - Smooth Drywall",
      "quantity": 630.0,
      "unit": "SF",
      "unit_price": 0.35,
      "total_price": 220.50
    }
  ]
}
```

**Errors:**
- `403 Forbidden` - Pro plan required

## 🏠 Room Endpoints

### Create Room

Manually add a room to a project.

```http
POST /rooms
```

**Request Body:**
```json
{
  "project_id": "proj_abc123",
  "name": "Lobby",
  "length": 30.0,
  "width": 20.0,
  "height": 12.0
}
```

**Response:** `200 OK`
```json
{
  "id": "room_xyz789",
  "project_id": "proj_abc123",
  "name": "Lobby",
  "length": 30.0,
  "width": 20.0,
  "height": 12.0,
  "wall_area": 1200.0,
  "ceiling_area": 600.0,
  "trim_length": 100.0,
  "paint_gallons": 7.5,
  "labor_hours": 10.0
}
```

---

### Update Room

Update room dimensions or details.

```http
PATCH /rooms/{room_id}
```

**Request Body:**
```json
{
  "name": "Updated Room Name",
  "length": 25.0,
  "width": 18.0,
  "height": 10.0
}
```

**Response:** `200 OK`
```json
{
  "id": "room_xyz789",
  "name": "Updated Room Name",
  "length": 25.0,
  "width": 18.0,
  "height": 10.0,
  "wall_area": 860.0,
  "ceiling_area": 450.0,
  "updated_at": "2026-05-20T15:00:00Z"
}
```

---

### Delete Room

Delete a room from a project.

```http
DELETE /rooms/{room_id}
```

**Response:** `200 OK`
```json
{
  "message": "Room deleted successfully"
}
```

## 📊 Export Endpoints

### Generate Excel Export

Create Excel spreadsheet with detailed estimates.

```http
POST /projects/{project_id}/export/excel
```

**Request Body (optional):**
```json
{
  "paint_price": 55.0,
  "labor_rate": 50.0,
  "include_assembly": true
}
```

**Response:** `200 OK`
```json
{
  "export_id": "exp_abc123",
  "file_url": "https://api.painting.ai/exports/exp_abc123/download",
  "filename": "Office_Renovation_Estimate.xlsx",
  "expires_at": "2026-05-21T12:00:00Z"
}
```

---

### Generate PDF Proposal

Create PDF proposal document.

```http
POST /projects/{project_id}/export/pdf
```

**Request Body (optional):**
```json
{
  "company_name": "ABC Painting",
  "company_phone": "(555) 123-4567",
  "company_email": "info@abcpainting.com",
  "notes": "All work guaranteed for 2 years"
}
```

**Response:** `200 OK`
```json
{
  "export_id": "exp_def456",
  "file_url": "https://api.painting.ai/exports/exp_def456/download",
  "filename": "Office_Renovation_Proposal.pdf",
  "expires_at": "2026-05-21T12:00:00Z"
}
```

---

### Download Export

Download generated export file.

```http
GET /exports/{export_id}/download
```

**Response:** `200 OK`
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel)
- Content-Type: `application/pdf` (PDF)
- File download

**Errors:**
- `404 Not Found` - Export expired or doesn't exist

## 💳 Payment Endpoints

### Get Pricing Plans

List available subscription plans.

```http
GET /pricing/plans
```

**Response:** `200 OK`
```json
{
  "plans": [
    {
      "id": "starter",
      "name": "Starter",
      "price": 99,
      "interval": "month",
      "features": [
        "50 projects/month",
        "Excel & PDF exports",
        "Email support"
      ],
      "limits": {
        "projects_per_month": 50
      }
    },
    {
      "id": "pro",
      "name": "Pro",
      "price": 299,
      "interval": "month",
      "features": [
        "Unlimited projects",
        "API access",
        "Priority support",
        "Team collaboration (5 members)"
      ],
      "limits": {
        "projects_per_month": null,
        "team_members": 5
      }
    }
  ]
}
```

---

### Create Checkout Session

Start Stripe checkout for subscription.

```http
POST /checkout/create-session
```

**Request Body:**
```json
{
  "plan": "pro",
  "success_url": "https://app.painting.ai/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://app.painting.ai/pricing"
}
```

**Response:** `200 OK`
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

---

### Customer Portal

Get link to Stripe customer portal for subscription management.

```http
POST /checkout/portal
```

**Response:** `200 OK`
```json
{
  "portal_url": "https://billing.stripe.com/p/session/..."
}
```

---

### Get Usage Stats

Get current billing period usage.

```http
GET /usage/stats
```

**Response:** `200 OK`
```json
{
  "billing_period": {
    "start": "2026-05-01T00:00:00Z",
    "end": "2026-06-01T00:00:00Z"
  },
  "projects_used": 25,
  "projects_limit": 50,
  "api_requests": 1523,
  "plan": "starter",
  "subscription_status": "active"
}
```

## 📈 Analytics Endpoints

### Get Overview

Get analytics overview.

```http
GET /analytics/overview
```

**Query Parameters:**
- `start_date` (optional): Start date (ISO 8601)
- `end_date` (optional): End date (ISO 8601)

**Response:** `200 OK`
```json
{
  "total_projects": 152,
  "active_projects": 12,
  "total_sqft": 125000.0,
  "total_value": 250000.0,
  "avg_project_value": 1645.0
}
```

---

### Get Usage Analytics

Get API usage over time.

```http
GET /analytics/usage
```

**Query Parameters:**
- `days` (optional): Number of days (default: 30)

**Response:** `200 OK`
```json
{
  "daily_usage": [
    {
      "date": "2026-05-20",
      "requests": 245,
      "unique_users": 12
    }
  ],
  "total_requests": 7350,
  "top_endpoints": [
    {
      "endpoint": "POST /projects",
      "count": 1250
    }
  ]
}
```

## 🔌 Public API

For detailed Public API documentation, see [`backend/docs/API_GUIDE.md`](backend/docs/API_GUIDE.md).

**Authentication:** API Key (`X-API-Key` header)  
**Base Path:** `/api/v1/`

### Key Endpoints:
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `POST /api/v1/projects/{id}/rooms` - Add room
- `POST /api/v1/webhooks` - Register webhook

## 🪝 Webhooks

Register webhooks to receive real-time notifications.

### Events

- `project.created` - New project created
- `project.completed` - Project processing complete
- `export.ready` - Export file ready for download
- `payment.succeeded` - Payment successful
- `payment.failed` - Payment failed

### Register Webhook

```http
POST /api/v1/webhooks
```

**Request Body:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["project.completed", "export.ready"],
  "secret": "your-webhook-secret"
}
```

### Webhook Payload

```json
{
  "event": "project.completed",
  "timestamp": "2026-05-20T12:00:00Z",
  "data": {
    "project_id": "proj_abc123",
    "status": "complete",
    "total_rooms": 8,
    "total_sqft": 2500.0
  }
}
```

**Signature Verification:**
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## 📝 Examples

### Complete Flow (Python)

```python
import requests

BASE_URL = "https://api.painting.ai"

# 1. Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe",
    "company_name": "ABC Painting"
})
data = response.json()
access_token = data["access_token"]

# 2. Create project
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(f"{BASE_URL}/projects", headers=headers, json={
    "name": "Office Renovation",
    "customer": "ABC Construction"
})
project = response.json()

# 3. Upload floor plan
with open("floor-plan.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/projects/{project['id']}/upload",
        headers=headers,
        files=files
    )

# 4. Wait for processing (poll or webhook)
import time
time.sleep(30)  # Wait for AI processing

# 5. Get project with rooms
response = requests.get(
    f"{BASE_URL}/projects/{project['id']}",
    headers=headers
)
project_details = response.json()
print(f"Detected {project_details['total_rooms']} rooms")

# 6. Generate Excel export
response = requests.post(
    f"{BASE_URL}/projects/{project['id']}/export/excel",
    headers=headers,
    json={"paint_price": 55.0, "labor_rate": 50.0}
)
export = response.json()

# 7. Download export
response = requests.get(export["file_url"], headers=headers)
with open("estimate.xlsx", "wb") as f:
    f.write(response.content)
```

### Complete Flow (JavaScript)

```javascript
const BASE_URL = 'https://api.painting.ai'

// 1. Register
const registerResponse = await fetch(`${BASE_URL}/auth/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123',
    full_name: 'John Doe',
    company_name: 'ABC Painting'
  })
})
const { access_token } = await registerResponse.json()

// 2. Create project
const projectResponse = await fetch(`${BASE_URL}/projects`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    name: 'Office Renovation',
    customer: 'ABC Construction'
  })
})
const project = await projectResponse.json()

// 3. Upload floor plan
const formData = new FormData()
formData.append('file', fileInput.files[0])

await fetch(`${BASE_URL}/projects/${project.id}/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
})

// 4. Generate Excel
const exportResponse = await fetch(
  `${BASE_URL}/projects/${project.id}/export/excel`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({ paint_price: 55.0, labor_rate: 50.0 })
  }
)
const exportData = await exportResponse.json()

// 5. Download
window.location.href = exportData.file_url
```

---

## 📚 Resources

- [API Guide (Public API)](backend/docs/API_GUIDE.md)
- [Authentication Guide](TESTING.md#authentication)
- [Error Handling](TESTING.md#error-handling)
- [Webhook Guide](#webhooks)

## 🆘 Support

- Email: cooperxxjohn@gmail.com
- Documentation: https://docs.painting.ai
- Status Page: https://status.painting.ai

---

**API Version:** 1.0.0  
**Last Updated:** May 21, 2026

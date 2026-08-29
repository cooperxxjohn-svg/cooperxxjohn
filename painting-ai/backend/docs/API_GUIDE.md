# Painting.ai Public API Guide

**Version:** 1.0.0  
**Base URL:** `https://api.painting.ai` (or `http://localhost:8001` for development)

---

## Authentication

All API requests require an API key passed in the `X-API-Key` header.

```bash
curl -H "X-API-Key: pk_your_api_key_here" \
  https://api.painting.ai/api/projects
```

### Getting Your API Key

1. Sign up at https://painting.ai
2. Go to Settings → API Keys
3. Click "Generate API Key"
4. Copy your key (starts with `pk_`)

**Security:** Keep your API key secret. Never commit it to version control.

---

## Rate Limits

- **100 requests per minute** per API key
- **5,000 requests per hour** per API key
- **100,000 requests per day** per API key

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 2026-05-20T12:00:00Z
```

When rate limited, you'll receive a `429 Too Many Requests` response.

---

## Projects

### Create Project

```http
POST /api/projects
```

**Request Body:**
```json
{
  "name": "Office Renovation",
  "customer": "ABC Construction",
  "project_type": "commercial",
  "address": "123 Main St, San Francisco, CA"
}
```

**Response:** `201 Created`
```json
{
  "id": "proj_abc123",
  "name": "Office Renovation",
  "customer": "ABC Construction",
  "status": "created",
  "total_rooms": 0,
  "total_sqft": 0.0,
  "estimated_cost": 0.0,
  "created_at": "2026-05-20T12:00:00Z"
}
```

### Get Project

```http
GET /api/projects/{project_id}
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123",
  "name": "Office Renovation",
  "customer": "ABC Construction",
  "status": "complete",
  "total_rooms": 8,
  "total_sqft": 2500.0,
  "estimated_cost": 5000.0,
  "created_at": "2026-05-20T12:00:00Z"
}
```

---

## Rooms

### List Project Rooms

```http
GET /api/projects/{project_id}/rooms
```

**Response:** `200 OK`
```json
{
  "project_id": "proj_abc123",
  "rooms": [
    {
      "id": "room_xyz789",
      "name": "Conference Room A",
      "number": "201",
      "dimensions": {
        "length": 20,
        "width": 15,
        "height": 9
      },
      "total_area": 630,
      "surfaces": {
        "walls": {"area": 579},
        "ceiling": {"area": 300},
        "doors": {"area": 40},
        "windows": {"area": 51}
      }
    }
  ]
}
```

### Update Room

```http
PUT /api/projects/{project_id}/rooms/{room_id}
```

**Request Body:**
```json
{
  "name": "Conference Room A (Updated)",
  "dimensions": {
    "length": 25,
    "width": 15,
    "height": 9
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "room_xyz789",
  "project_id": "proj_abc123",
  "name": "Conference Room A (Updated)",
  "dimensions": {
    "length": 25,
    "width": 15,
    "height": 9
  },
  "total_area": 720,
  "updated_at": "2026-05-20T12:05:00Z"
}
```

### Add Room Manually

```http
POST /api/projects/{project_id}/rooms
```

**Request Body:**
```json
{
  "name": "Storage Closet",
  "number": "210",
  "dimensions": {
    "length": 8,
    "width": 6,
    "height": 9
  },
  "manually_added": true
}
```

**Response:** `201 Created`
```json
{
  "id": "room_new123",
  "project_id": "proj_abc123",
  "name": "Storage Closet",
  "number": "210",
  "dimensions": {
    "length": 8,
    "width": 6,
    "height": 9
  },
  "total_area": 252,
  "manually_added": true,
  "created_at": "2026-05-20T12:10:00Z"
}
```

### Delete Room

```http
DELETE /api/projects/{project_id}/rooms/{room_id}
```

**Response:** `200 OK`
```json
{
  "message": "Room deleted successfully",
  "room_id": "room_xyz789",
  "project_id": "proj_abc123",
  "deleted_at": "2026-05-20T12:15:00Z"
}
```

---

## Assembly Breakdown

### Get Detailed Line Items

```http
GET /api/projects/{project_id}/assembly?paint_type=commercial&labor_rate=50.0
```

**Query Parameters:**
- `paint_type` (optional): `economy`, `commercial`, `premium`. Default: `commercial`
- `labor_rate` (optional): Labor rate in $/hour. Default: `50.0`

**Response:** `200 OK`
```json
{
  "project_id": "proj_abc123",
  "line_items": [
    {
      "item_number": "1.1",
      "category": "Prep - Walls",
      "description": "Spackle nail holes and imperfections",
      "quantity": 0.5,
      "unit": "hour",
      "unit_cost": 50.0,
      "total_cost": 25.0
    },
    {
      "item_number": "1.2",
      "category": "Prep - Walls",
      "description": "Sand surfaces smooth",
      "quantity": 1.2,
      "unit": "hour",
      "unit_cost": 50.0,
      "total_cost": 60.0
    }
    // ... 80-120 more line items
  ],
  "summary": {
    "total_line_items": 144,
    "material_cost": 2500.0,
    "labor_cost": 2500.0,
    "total_cost": 5000.0
  }
}
```

---

## Materials

### Update Project Materials

```http
PUT /api/projects/{project_id}/materials
```

**Request Body:**
```json
{
  "paint_id": "mat_promar400",
  "primer_id": "mat_promar200",
  "quality_tier": "commercial"
}
```

**Response:** `200 OK`
```json
{
  "project_id": "proj_abc123",
  "materials": {
    "paint_id": "mat_promar400",
    "primer_id": "mat_promar200",
    "quality_tier": "commercial"
  },
  "updated_at": "2026-05-20T12:20:00Z",
  "message": "Materials updated. Recalculate estimate to apply changes."
}
```

---

## Exports

### Export to Excel

```http
POST /api/projects/{project_id}/export/excel
```

**Response:** `200 OK`
```json
{
  "project_id": "proj_abc123",
  "format": "excel",
  "filename": "Office_Renovation_estimate.xlsx",
  "file_path": "exports/proj_abc123_20260520.xlsx",
  "download_url": "/projects/proj_abc123/export/excel",
  "created_at": "2026-05-20T12:25:00Z"
}
```

### Export to PDF

```http
POST /api/projects/{project_id}/export/pdf
```

**Response:** `200 OK`
```json
{
  "project_id": "proj_abc123",
  "format": "pdf",
  "filename": "Office_Renovation_proposal.pdf",
  "file_path": "exports/proj_abc123_20260520.pdf",
  "download_url": "/projects/proj_abc123/export/pdf",
  "created_at": "2026-05-20T12:30:00Z"
}
```

---

## Webhooks

Webhooks allow you to receive real-time notifications when events occur.

### Create Webhook

```http
POST /api/webhooks
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": [
    "project.completed",
    "export.generated"
  ],
  "description": "Production webhook"
}
```

**Response:** `201 Created`
```json
{
  "id": "wh_abc123",
  "url": "https://your-app.com/webhook",
  "events": [
    "project.completed",
    "export.generated"
  ],
  "secret": "whsec_def456xyz789",
  "is_active": true,
  "created_at": "2026-05-20T12:35:00Z"
}
```

**Important:** Save the `secret` - you'll need it to verify webhook signatures.

### List Webhooks

```http
GET /api/webhooks
```

**Response:** `200 OK`
```json
{
  "webhooks": [
    {
      "id": "wh_abc123",
      "url": "https://your-app.com/webhook",
      "events": ["project.completed"],
      "is_active": true,
      "created_at": "2026-05-20T12:35:00Z"
    }
  ]
}
```

### Delete Webhook

```http
DELETE /api/webhooks/{webhook_id}
```

**Response:** `200 OK`
```json
{
  "message": "Webhook deleted successfully",
  "webhook_id": "wh_abc123"
}
```

---

## Webhook Events

Available webhook events:

- `project.created` - New project created
- `project.processing` - AI processing started
- `project.completed` - AI processing finished
- `project.failed` - AI processing failed
- `drawing.uploaded` - Floor plan uploaded
- `export.generated` - Excel or PDF export created
- `payment.succeeded` - Payment successful
- `payment.failed` - Payment failed

### Webhook Payload Format

```json
{
  "event": "project.completed",
  "data": {
    "project_id": "proj_abc123",
    "name": "Office Renovation",
    "total_rooms": 8,
    "total_sqft": 2500.0,
    "estimated_cost": 5000.0
  },
  "timestamp": "2026-05-20T12:40:00Z"
}
```

### Verifying Webhook Signatures

All webhook requests include an `X-Webhook-Signature` header with an HMAC signature:

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    """Verify webhook signature"""
    payload_str = json.dumps(payload, sort_keys=True)
    expected_sig = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()

    expected_sig = f"sha256={expected_sig}"
    return hmac.compare_digest(signature, expected_sig)

# Usage
payload = request.json
signature = request.headers.get("X-Webhook-Signature")
secret = "whsec_your_secret"

if verify_webhook(payload, signature, secret):
    # Process webhook
    print("Valid webhook!")
else:
    # Reject
    print("Invalid signature!")
```

### Webhook Retry Logic

If your endpoint returns a non-200 status code or times out:

- **1st retry:** After 2 seconds
- **2nd retry:** After 4 seconds (exponential backoff)
- **3rd retry:** After 8 seconds

After 3 failed attempts, the webhook is marked as failed and won't retry.

**4xx errors (client errors):** No retries - fix your endpoint and re-enable the webhook.

---

## Error Responses

### Error Format

```json
{
  "detail": "Project not found"
}
```

### Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid API key
- `403 Forbidden` - Access denied (subscription inactive or wrong owner)
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Code Examples

### Python

```python
import requests

API_KEY = "pk_your_api_key"
BASE_URL = "https://api.painting.ai"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create project
response = requests.post(
    f"{BASE_URL}/api/projects",
    json={
        "name": "Office Renovation",
        "customer": "ABC Construction"
    },
    headers=headers
)

project = response.json()
print(f"Created project: {project['id']}")

# Get assembly breakdown
response = requests.get(
    f"{BASE_URL}/api/projects/{project['id']}/assembly",
    params={"paint_type": "commercial", "labor_rate": 50.0},
    headers=headers
)

assembly = response.json()
print(f"Line items: {assembly['summary']['total_line_items']}")
```

### JavaScript

```javascript
const API_KEY = 'pk_your_api_key';
const BASE_URL = 'https://api.painting.ai';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Create project
const response = await fetch(`${BASE_URL}/api/projects`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    name: 'Office Renovation',
    customer: 'ABC Construction'
  })
});

const project = await response.json();
console.log(`Created project: ${project.id}`);

// Get rooms
const roomsResponse = await fetch(
  `${BASE_URL}/api/projects/${project.id}/rooms`,
  { headers }
);

const { rooms } = await roomsResponse.json();
console.log(`Detected ${rooms.length} rooms`);
```

### cURL

```bash
# Create project
curl -X POST https://api.painting.ai/api/projects \
  -H "X-API-Key: pk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Office Renovation",
    "customer": "ABC Construction"
  }'

# Get project
curl -X GET https://api.painting.ai/api/projects/proj_abc123 \
  -H "X-API-Key: pk_your_api_key"

# Export to Excel
curl -X POST https://api.painting.ai/api/projects/proj_abc123/export/excel \
  -H "X-API-Key: pk_your_api_key"
```

---

## Support

- **Documentation:** https://docs.painting.ai
- **Email:** api@painting.ai
- **Status Page:** https://status.painting.ai

---

## Changelog

### Version 1.0.0 (2026-05-20)
- Initial public API release
- Projects, rooms, assembly, exports
- Webhook support
- Rate limiting

# Phase 5: Production API + Webhooks - COMPLETE

**Status:** ✅ Complete - Public API ready for production  
**Duration:** 3-4 hours

---

## What Was Built

### 1. Real Database Integration

**Before:** All endpoints returned hardcoded mock data  
**After:** All endpoints connected to real database (JSON storage)

**Changes:**
- Connected `api_public.py` to `Database` class
- All CRUD operations use real data
- User ownership verification on all operations
- Proper error responses (404, 403, 400)

---

### 2. API Key Verification

**Function:** `verify_api_key()`

**Before:**
```python
# Just checked if key starts with "pk_"
if not x_api_key.startswith("pk_"):
    raise HTTPException(status_code=401, detail="Invalid API key")
```

**After:**
```python
# Real database lookup
user = db.get_user_by_api_key(x_api_key)
if not user:
    raise HTTPException(status_code=401, detail="Invalid API key")

# Check subscription status
if user.get("subscription_status") not in ["active", "trialing"]:
    raise HTTPException(status_code=403, detail="Subscription inactive")

# Log usage
log_api_usage(user["id"], "api_request")

return user  # Return user object for ownership checks
```

**Security:**
- API keys stored in users.json
- Subscription status enforced
- Inactive subscriptions rejected
- Usage logged for analytics

---

### 3. API Usage Logging

**Function:** `log_api_usage()`

**Logs to:** `data/api_usage.json`

**Data Stored:**
```json
{
  "id": "uuid",
  "user_id": "user_123",
  "endpoint": "/api/projects",
  "method": "POST",
  "status_code": 201,
  "timestamp": "2026-05-20T12:00:00Z"
}
```

**Features:**
- Tracks all API requests
- Stores user ID, endpoint, method, status
- Keeps last 10,000 entries (auto-cleanup)
- Ready for analytics dashboard

---

### 4. Real Endpoints

All endpoints now use real database operations:

#### **POST /api/projects**
- Creates project in database
- Assigns to authenticated user
- Returns real project data
- Logs usage

#### **GET /api/projects/{id}**
- Fetches from database
- Verifies user ownership
- Returns 403 if not owner
- Returns 404 if not found

#### **GET /api/projects/{id}/rooms**
- Gets rooms from database
- Verifies project ownership
- Returns all rooms for project

#### **PUT /api/projects/{id}/rooms/{room_id}**
- Updates room in database
- Recalculates total_area if dimensions change
- Verifies ownership
- Returns updated room

#### **POST /api/projects/{id}/rooms**
- Adds manual room to database
- Calculates total_area from dimensions
- Updates project total_rooms count
- Marks as manually_added

#### **DELETE /api/projects/{id}/rooms/{room_id}**
- Deletes room from database
- Updates project total_rooms count
- Verifies ownership

#### **GET /api/projects/{id}/assembly**
- Fetches rooms from database
- Converts to Room dataclass
- Calls AssemblyExpander
- Returns 80-120 line items
- Supports paint_type and labor_rate params

#### **PUT /api/projects/{id}/materials**
- Updates project materials in database
- Stores paint_id, primer_id, quality_tier
- Returns update confirmation

#### **POST /api/projects/{id}/export/{format}**
- Verifies project is complete
- Calls ExportGenerator (real)
- Generates Excel or PDF file
- Triggers export.generated webhook
- Returns file path and download URL

---

### 5. Webhook System

#### **Webhook Storage**

**New database methods:**
- `save_webhook()` - Store webhook
- `get_user_webhooks()` - Get user's webhooks
- `get_webhook()` - Get by ID
- `delete_webhook()` - Delete webhook

**Storage:** `data/webhooks.json`

```json
{
  "wh_abc123": {
    "id": "wh_abc123",
    "user_id": "user_123",
    "url": "https://app.com/webhook",
    "events": ["project.completed", "export.generated"],
    "secret": "whsec_xyz789",
    "is_active": true,
    "created_at": "2026-05-20T12:00:00Z"
  }
}
```

#### **Webhook Delivery**

**Class:** `WebhookDelivery`

**Features:**
- **HMAC Signature:** Signs payload with sha256
- **Retry Logic:** 3 attempts with exponential backoff (2s, 4s, 8s)
- **Smart Retry:** No retry on 4xx errors (client fault)
- **Logging:** Logs all delivery attempts
- **Headers:** 
  - `X-Webhook-Signature: sha256=...`
  - `X-Webhook-Event: project.completed`

**Signature Verification:**
```python
def sign_payload(payload: dict, secret: str) -> str:
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

**Retry Flow:**
```
Attempt 1 → Fail → Wait 2s
Attempt 2 → Fail → Wait 4s
Attempt 3 → Fail → Mark failed

4xx error → No retry (fix endpoint first)
5xx error → Retry with backoff
Timeout → Retry with backoff
```

#### **Webhook Logging**

**Function:** `log_webhook_delivery()`

**Logs to:** `data/webhook_logs.json`

```json
{
  "id": "uuid",
  "webhook_id": "wh_abc123",
  "event": "project.completed",
  "success": false,
  "status_code": 500,
  "error": "Connection timeout",
  "timestamp": "2026-05-20T12:00:00Z"
}
```

Keeps last 1,000 delivery logs.

#### **Triggering Webhooks**

**Function:** `trigger_webhooks(event, data, user_id)`

**Usage:**
```python
await WebhookDelivery.trigger_webhooks(
    event="export.generated",
    data={
        "project_id": "proj_123",
        "format": "excel",
        "filename": "estimate.xlsx"
    },
    user_id="user_123"
)
```

**Flow:**
1. Get all user webhooks
2. Filter by event and is_active
3. Deliver to each matching webhook
4. Log delivery result

---

### 6. Webhook Endpoints

#### **POST /api/webhooks**
```json
Request:
{
  "url": "https://app.com/webhook",
  "events": ["project.completed"],
  "description": "Production webhook"
}

Response:
{
  "id": "wh_abc123",
  "url": "https://app.com/webhook",
  "events": ["project.completed"],
  "secret": "whsec_xyz789",  // SAVE THIS
  "is_active": true,
  "created_at": "2026-05-20T12:00:00Z"
}
```

#### **GET /api/webhooks**
```json
Response:
{
  "webhooks": [
    {
      "id": "wh_abc123",
      "url": "https://app.com/webhook",
      "events": ["project.completed"],
      "is_active": true,
      "created_at": "2026-05-20T12:00:00Z"
    }
  ]
}
```

#### **DELETE /api/webhooks/{id}**
```json
Response:
{
  "message": "Webhook deleted successfully",
  "webhook_id": "wh_abc123"
}
```

---

### 7. Webhook Events

Available events:
- `project.created` - New project created
- `project.processing` - AI processing started
- `project.completed` - AI processing complete
- `project.failed` - AI processing failed
- `drawing.uploaded` - Floor plan uploaded
- `export.generated` - Excel/PDF created
- `payment.succeeded` - Payment success
- `payment.failed` - Payment failure

**Payload Format:**
```json
{
  "event": "project.completed",
  "data": {
    "project_id": "proj_123",
    "name": "Office Renovation",
    "total_rooms": 8,
    "estimated_cost": 5000.0
  },
  "timestamp": "2026-05-20T12:00:00Z"
}
```

---

### 8. API Documentation

**File:** `backend/docs/API_GUIDE.md`

**Contents:**
- Authentication (X-API-Key header)
- Rate limits (100/min, 5k/hour, 100k/day)
- All endpoints with request/response examples
- Webhook setup and verification
- Code examples (Python, JavaScript, cURL)
- Error responses (401, 403, 404, 429, 500)
- Security best practices
- Signature verification code

**Length:** 600+ lines of complete documentation

---

## Database Methods Added

**database.py:**
```python
def get_user_by_api_key(self, api_key: str) -> Optional[Dict]:
    """Get user by API key"""
    # Looks up user in users.json by api_key field

def save_webhook(self, webhook: Dict):
    """Save webhook to webhooks.json"""

def get_user_webhooks(self, user_id: str) -> List[Dict]:
    """Get all webhooks for a user"""

def get_webhook(self, webhook_id: str) -> Optional[Dict]:
    """Get webhook by ID"""

def delete_webhook(self, webhook_id: str):
    """Delete webhook from webhooks.json"""
```

---

## Testing the Public API

### Start API Server

```bash
cd backend
source venv/bin/activate

# Start on port 8001
python api_public.py

# Or with uvicorn
uvicorn api_public:api_public --port 8001 --reload
```

### Get API Key

```python
# Create user with API key
from database import Database
import uuid

db = Database()

user = {
    "id": str(uuid.uuid4()),
    "email": "test@example.com",
    "name": "Test User",
    "api_key": "pk_test123",
    "subscription_status": "trialing",
    "plan": "trial"
}

db.save_user(user)
print(f"API Key: {user['api_key']}")
```

### Test Endpoints

```bash
# Check API
curl http://localhost:8001/

# Create project
curl -X POST http://localhost:8001/api/projects \
  -H "X-API-Key: pk_test123" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "customer": "Test Customer"}'

# Get project
curl http://localhost:8001/api/projects/proj_123 \
  -H "X-API-Key: pk_test123"

# Create webhook
curl -X POST http://localhost:8001/api/webhooks \
  -H "X-API-Key: pk_test123" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/unique-id", "events": ["project.completed"]}'

# Check rate limit
curl http://localhost:8001/api/rate-limit \
  -H "X-API-Key: pk_test123"
```

### Webhook Testing

Use https://webhook.site to get a test URL:

1. Go to webhook.site
2. Copy your unique URL
3. Create webhook with that URL
4. Trigger an event
5. See the webhook delivery on webhook.site

---

## Security Features

✅ **API Key Verification** - Real database lookup  
✅ **Subscription Enforcement** - Active/trialing only  
✅ **Ownership Checks** - User can only access their data  
✅ **Rate Limiting** - 100 requests/minute per key  
✅ **HMAC Signatures** - Verify webhook authenticity  
✅ **No Retry on 4xx** - Prevent abuse  
✅ **Usage Logging** - Track all API calls  

---

## Files Modified

**backend/api_public.py:**
- Added `from database import Database`
- Added `from assembly_expansion import AssemblyExpander`
- Updated `verify_api_key()` to check database
- Added `log_api_usage()` function
- Wired all 12 endpoints to real database
- Enhanced `WebhookDelivery` class with retry logic
- Added `trigger_webhooks()` function
- Added `log_webhook_delivery()` function

**backend/database.py:**
- Added `get_user_by_api_key()`
- Added `save_webhook()`
- Added `get_user_webhooks()`
- Added `get_webhook()`
- Added `delete_webhook()`

**backend/docs/API_GUIDE.md:**
- Complete API documentation (600+ lines)

---

## What Works Now

✅ Create projects via API  
✅ Get project details  
✅ List project rooms  
✅ Update room dimensions  
✅ Add manual rooms  
✅ Delete false positive rooms  
✅ Get assembly breakdown (80-120 line items)  
✅ Update material selections  
✅ Export to Excel/PDF  
✅ Create webhooks  
✅ List webhooks  
✅ Delete webhooks  
✅ Webhook delivery with retry  
✅ HMAC signature verification  
✅ API usage logging  
✅ Rate limiting  

---

## Integration with Main App

To integrate with main FastAPI app (`main.py`):

```python
from fastapi import FastAPI
from api_public import api_public

app = FastAPI()

# Mount public API
app.mount("/api", api_public)

# Now accessible at /api/projects, /api/webhooks, etc.
```

Or run separately on different port (recommended):
- Main app: port 8000
- Public API: port 8001

---

## Next Steps

### Phase 6: Stripe Payments (2-3 days)
- Subscription plans: Starter ($99), Pro ($299), Enterprise (custom)
- Checkout session creation
- Webhook handling for payment events
- Plan enforcement
- Trial expiration

### Phase 7: Email + Async Tasks (2 days)
- SendGrid integration
- Email templates
- Celery task queue
- Background processing

### Phase 8: Monitoring + Analytics (1-2 days)
- Analytics endpoints
- Usage dashboards
- Performance monitoring

---

## Phase 5 Status: ✅ COMPLETE

**Time Spent:** 3-4 hours  
**Endpoints Built:** 12 full CRUD operations  
**Lines of Code:** ~400 lines modified/added  
**Documentation:** 600+ line API guide  

**Production Ready:** Public API can now be used by third-party integrations!

https://claude.ai/code/session_01Tp5GDjdoMPwWrTte54Q76K

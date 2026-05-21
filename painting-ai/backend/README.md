# Painting.ai Backend

FastAPI backend for AI-powered painting takeoffs and estimates.

## 🏗️ Architecture

### Tech Stack
- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11+
- **Database:** PostgreSQL 15 (production) / JSON files (development)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Authentication:** JWT with python-jose, bcrypt
- **AI:** Anthropic Claude Sonnet 4 API
- **Payments:** Stripe
- **Email:** SendGrid
- **File Processing:** PyMuPDF, Pillow, pytesseract
- **Exports:** openpyxl (Excel), ReportLab (PDF)

### Key Components

```
backend/
├── main.py                  # FastAPI app & routes
├── auth_jwt.py              # JWT authentication
├── payments.py              # Stripe integration
├── email_service.py         # SendGrid email service
├── painting_detector.py     # AI room detection (Claude)
├── assembly_expansion.py   # Assembly line item expansion
├── export_generator.py      # Excel & PDF generation
├── database.py              # Database models & operations
├── analytics.py             # Usage analytics & metrics
├── models.py                # SQLAlchemy ORM models
├── background_tasks.py      # Async background jobs
├── materials.py             # Paint materials database
├── monitoring.py            # Health checks & monitoring
└── api_public.py            # Public API endpoints
```

## 🚀 Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (optional for development)
- Anthropic API key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env and configure
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Database (optional for development)
DATABASE_URL=postgresql://user:pass@localhost:5432/paintingai

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...

# SendGrid (for emails)
SENDGRID_API_KEY=SG....
FROM_EMAIL=noreply@paintingai.com

# Frontend URL (for CORS & emails)
FRONTEND_URL=http://localhost:3000

# Optional
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your-sentry-dsn
ENVIRONMENT=development
```

### Run Development Server

```bash
# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With custom port
uvicorn main:app --reload --port 8080

# Production mode (no reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

API will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **OpenAPI:** http://localhost:8000/openapi.json

## 🗄️ Database

### Using JSON (Development)

Default mode - no setup required. Data stored in:
- `database.json` - Main data
- `uploads/` - Uploaded files

### Using PostgreSQL (Production)

```bash
# Start PostgreSQL with Docker
docker compose up -d postgres

# Run migrations
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "Description"

# Rollback migration
alembic downgrade -1

# Seed demo data
python seed_demo_data.py
```

### Database Models

- **User** - User accounts with authentication
- **Organization** - Company/team accounts
- **Project** - Painting projects
- **Room** - Rooms within projects
- **Surface** - Walls, ceilings, trim
- **Material** - Paint materials
- **Assembly** - Line item assemblies
- **Subscription** - Stripe subscriptions
- **APIKey** - Public API keys
- **Webhook** - Webhook configurations
- **WebhookDelivery** - Webhook delivery logs

See `models.py` for complete schema.

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Test Structure

```
tests/
├── test_auth.py              # Authentication tests
├── test_api.py               # API endpoint tests
├── test_calculations.py      # Paint calculation tests
├── test_payments.py          # Stripe integration tests
├── test_exports.py           # Excel/PDF generation tests
└── conftest.py               # Pytest fixtures
```

### Writing Tests

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_project():
    # Login
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = response.json()["access_token"]
    
    # Create project
    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Project", "customer": "Test Customer"}
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"
```

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - Login (returns JWT)
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

### Projects
- `GET /projects` - List user's projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project details
- `PATCH /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/upload` - Upload floor plan
- `GET /projects/{id}/rooms` - List project rooms

### Rooms
- `POST /rooms` - Create room
- `PATCH /rooms/{id}` - Update room
- `DELETE /rooms/{id}` - Delete room
- `POST /projects/{id}/expand-assembly` - Expand to line items

### Exports
- `POST /projects/{id}/export/excel` - Generate Excel
- `POST /projects/{id}/export/pdf` - Generate PDF proposal
- `GET /exports/{file_id}` - Download export

### Payments
- `GET /pricing/plans` - List subscription plans
- `POST /checkout/create-session` - Create Stripe checkout
- `POST /checkout/portal` - Customer portal link
- `POST /checkout/webhook` - Stripe webhook handler
- `GET /usage/stats` - Usage statistics

### Public API
- `POST /api/v1/projects` - Create project (API key auth)
- `GET /api/v1/projects/{id}` - Get project
- `POST /api/v1/webhooks` - Register webhook
- See `docs/API_GUIDE.md` for complete API docs

## 🔒 Authentication

### JWT Flow

1. **Register:** `POST /auth/register`
   ```json
   {
     "email": "user@example.com",
     "password": "secure-password",
     "full_name": "John Doe",
     "company_name": "ABC Painting"
   }
   ```

2. **Login:** `POST /auth/login`
   ```json
   {
     "email": "user@example.com",
     "password": "secure-password"
   }
   ```
   
   Returns:
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1Q...",
     "refresh_token": "eyJ0eXAiOiJKV1Q...",
     "token_type": "bearer",
     "user": {...}
   }
   ```

3. **Use Token:** Add to requests
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1Q...
   ```

4. **Refresh:** `POST /auth/refresh` (when token expires)

### Password Security

- Passwords hashed with bcrypt (12 rounds)
- Minimum 8 characters
- Tokens expire after 24 hours
- Refresh tokens expire after 30 days

## 💳 Payments

### Stripe Integration

1. **Create Checkout Session:**
   ```python
   response = client.post("/checkout/create-session", json={
       "plan": "pro",
       "success_url": "https://app.com/success?session_id={CHECKOUT_SESSION_ID}",
       "cancel_url": "https://app.com/pricing"
   })
   checkout_url = response.json()["checkout_url"]
   # Redirect user to checkout_url
   ```

2. **Handle Webhook Events:**
   - `checkout.session.completed` - New subscription
   - `invoice.payment_succeeded` - Successful payment
   - `invoice.payment_failed` - Failed payment
   - `customer.subscription.deleted` - Cancellation

3. **Customer Portal:**
   ```python
   response = client.post("/checkout/portal")
   portal_url = response.json()["portal_url"]
   # Redirect user to manage subscription
   ```

### Plans

- **Starter:** $99/month - 50 projects/month
- **Pro:** $299/month - Unlimited projects + API
- **Enterprise:** Custom pricing

All plans include 14-day free trial.

## 📧 Email Service

### Email Templates

1. **Welcome Email** - New user registration
2. **Project Complete** - AI processing finished
3. **Export Ready** - Download link
4. **Payment Succeeded** - Receipt
5. **Payment Failed** - Update payment method

### Sending Emails

```python
from email_service import get_email_service

email_service = get_email_service()

# Send welcome email
await email_service.send_welcome_email(
    to_email="user@example.com",
    user_name="John Doe",
    trial_days=14
)

# Send project complete
await email_service.send_project_complete_email(
    to_email="user@example.com",
    project_name="Office Renovation",
    room_count=12,
    total_sqft=5000
)
```

## 🤖 AI Integration

### Claude Sonnet 4 Vision

```python
from painting_detector import PaintingDetector

detector = PaintingDetector(api_key=ANTHROPIC_API_KEY)

# Detect rooms from floor plan
rooms = await detector.detect_rooms_from_image(
    image_path="uploads/floor_plan.pdf"
)

# Returns list of Room objects with:
# - name (e.g., "Living Room")
# - dimensions (length, width, height)
# - surfaces (walls, ceiling, trim)
# - confidence_score
```

### Rate Limits
- Claude API: 50 requests/minute
- Automatic retry with exponential backoff
- Caching for repeated requests

## 📊 Assembly Expansion

Generates detailed line items following Rudus workflow:

```python
from assembly_expansion import AssemblyExpander

expander = AssemblyExpander()
assemblies = expander.expand_project(project_id, rooms)

# Generates 80-120 line items:
# - Prep work (masking, drop cloths, protection)
# - Prime (per surface type)
# - Paint (2 coats)
# - Cleanup & disposal
# - Labor breakdown
# - Materials list
```

## 📈 Analytics

Track usage and business metrics:

```python
# Get overview
stats = analytics_service.get_overview(user_id)
# Returns: total_projects, total_users, active_users, total_value

# Get usage over time
usage = analytics_service.get_usage(user_id, days=30)
# Returns: Daily API requests, unique users, top endpoints

# Get conversion metrics
conversion = analytics_service.get_conversion()
# Returns: Trial→paid conversion rate, subscription breakdown
```

## 🔧 Utilities

### Paint Calculations

```python
from painting_detector import PaintCalculator

calc = PaintCalculator()

# Calculate paint needed
gallons = calc.calculate_paint_needed(
    surface_area=1000,  # sqft
    coats=2,
    surface_type="smooth_drywall"  # 400 sqft/gallon
)

# Calculate labor hours
hours = calc.calculate_labor_hours(
    surface_area=1000,
    surface_type="walls"  # 300 sqft/hour
)
```

### Export Generation

```python
from export_generator import ExportGenerator

exporter = ExportGenerator()

# Generate Excel
excel_path = exporter.generate_excel(
    project_data=project,
    rooms=rooms,
    assemblies=assemblies
)

# Generate PDF proposal
pdf_path = exporter.generate_proposal_pdf(
    project_data=project,
    rooms=rooms,
    estimate=estimate
)
```

## 🚀 Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up

# Set environment variables
railway variables set ANTHROPIC_API_KEY=your-key
railway variables set DATABASE_URL=postgresql://...
```

### Render

```yaml
# render.yaml
services:
  - type: web
    name: painting-ai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: paintingai-db
          property: connectionString
```

### Docker

```bash
# Build image
docker build -t painting-ai-backend .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e DATABASE_URL=postgresql://... \
  painting-ai-backend
```

## 📝 Code Style

- **Formatting:** Black (line length 100)
- **Linting:** Ruff or Flake8
- **Type Hints:** Use Python 3.11+ type hints
- **Docstrings:** Google style

```bash
# Format code
black . --line-length 100

# Lint
ruff check .

# Type check
mypy .
```

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Interactive Testing

```bash
# Start Python REPL with app context
python
>>> from main import app, db
>>> from models import User, Project
>>> # Test code here
```

### Database Inspection

```bash
# Connect to PostgreSQL
psql postgresql://user:pass@localhost:5432/paintingai

# List tables
\dt

# Query users
SELECT * FROM users;
```

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Stripe API Docs](https://stripe.com/docs/api)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

## 🆘 Support

For issues or questions:
- Email: cooperxxjohn@gmail.com
- Review logs: `tail -f app.log`
- Check health: `GET /health`

---

Built with FastAPI & Claude Sonnet 4

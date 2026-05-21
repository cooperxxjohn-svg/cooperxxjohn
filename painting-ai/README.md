# Painting.ai

> AI-powered takeoff and estimating software for painting contractors

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)

## 🎯 Value Proposition

**Generate accurate painting takeoffs in 5 minutes instead of 4 hours**

- Upload architectural drawings (PDF, PNG, JPG)
- AI automatically detects rooms, walls, ceilings, trim
- Calculates paint quantities and labor hours
- Export to Excel or PDF proposal
- No learning curve - just upload and go

## ✨ Features

### Core Functionality
- ✅ **AI Room Detection** - Claude Sonnet 4 vision API
- ✅ **Automatic Calculations** - Paint coverage, labor hours, costs
- ✅ **Assembly Expansion** - 80-120 detailed line items (Rudus-style)
- ✅ **Professional Exports** - Excel spreadsheets & PDF proposals
- ✅ **User Authentication** - JWT-based auth with 14-day trial
- ✅ **Payment Processing** - Stripe integration with subscription plans
- ✅ **Public API** - REST API with webhooks for integrations
- ✅ **Email Notifications** - SendGrid for welcome, project complete, payment emails

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 15 (production) / JSON (development)
- Claude Sonnet 4 (Anthropic API)
- Stripe (payments)
- SendGrid (email)
- JWT authentication with bcrypt
- SQLAlchemy + Alembic (migrations)

**Frontend:**
- React 18 with Vite
- TanStack Query (React Query)
- Zustand (state management)
- Tailwind CSS
- React Router v6
- Axios (HTTP client)

**Infrastructure:**
- Docker Compose (PostgreSQL, Redis)
- Alembic (database migrations)
- Railway/Render (backend deployment)
- Vercel (frontend deployment)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- (Optional) Docker & Docker Compose for PostgreSQL

### 1. Clone the Repository

```bash
git clone https://github.com/cooperxxjohn/painting-ai.git
cd painting-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env if needed (default: VITE_API_URL=http://localhost:8000)

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

### 4. (Optional) Run with Docker

```bash
# Start PostgreSQL and Redis
docker compose up -d

# Run database migrations
cd backend
alembic upgrade head

# Seed demo data (optional)
python seed_demo_data.py
```

## 📁 Project Structure

```
painting-ai/
├── backend/                    # FastAPI backend
│   ├── main.py                 # Main API server
│   ├── auth_jwt.py             # JWT authentication
│   ├── payments.py             # Stripe integration
│   ├── email_service.py        # SendGrid email service
│   ├── painting_detector.py   # AI room detection
│   ├── assembly_expansion.py  # Assembly line item expansion
│   ├── export_generator.py    # Excel & PDF generation
│   ├── database.py             # Database models
│   ├── analytics.py            # Usage analytics
│   ├── models.py               # SQLAlchemy models
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Backend tests
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Backend documentation
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/              # Page components
│   │   ├── components/         # Reusable components
│   │   ├── store/              # Zustand stores
│   │   ├── utils/              # Utilities (API client)
│   │   ├── App.jsx             # Main app component
│   │   └── main.jsx            # Entry point
│   ├── package.json            # Node dependencies
│   └── README.md               # Frontend documentation
├── docs/                       # Documentation
│   ├── product_spec.md         # Product specification
│   └── painting_formulas.md   # Paint calculation formulas
├── .env.example                # Environment variables template
├── docker-compose.yml          # Docker services
├── TESTING.md                  # Testing guide
├── DEPLOYMENT.md               # Deployment guide
├── API_REFERENCE.md            # API documentation
└── README.md                   # This file
```

## 🎨 Usage

### 1. Create an Account

Navigate to http://localhost:3000/register and create an account. You'll get a 14-day free trial.

### 2. Upload a Floor Plan

1. Go to Dashboard → Upload
2. Enter project details (name, customer, address)
3. Upload a PDF, PNG, or JPG floor plan (max 50MB)
4. Click "Upload & Process"

### 3. Review AI Detections

The AI will automatically detect:
- Rooms (name, dimensions)
- Walls (area calculations)
- Ceilings (area calculations)
- Trim (linear feet)

You can edit, add, or delete rooms as needed.

### 4. Generate Estimate

1. Click "Expand Assembly" to generate detailed line items
2. Customize paint prices and labor rates
3. Download Excel spreadsheet or PDF proposal

## 💰 Pricing

| Plan | Price | Features |
|------|-------|----------|
| **Starter** | $99/mo | 50 projects/month, Excel/PDF exports |
| **Pro** | $299/mo | Unlimited projects, API access, 5 team members |
| **Enterprise** | Custom | White-label, custom integrations, dedicated support |

All plans include:
- 14-day free trial
- AI room detection
- Professional exports
- Email support

## 📊 Paint Calculation Formulas

### Coverage Rates (per gallon)
- Smooth Drywall: 400 sqft/gallon
- Textured Drywall: 350 sqft/gallon
- Wood/Trim: 350 sqft/gallon

### Labor Rates (sqft/hour)
- Walls: 300 sqft/hour
- Ceilings: 350 sqft/hour
- Trim: 200 sqft/hour

### Standard Coats
- Primer: 1 coat
- Finish: 2 coats
- Trim: 2-3 coats

See [`docs/painting_formulas.md`](docs/painting_formulas.md) for complete formulas.

## 🧪 Testing

See [TESTING.md](TESTING.md) for comprehensive testing guide.

```bash
# Backend tests
cd backend
pytest --cov=. --cov-report=html

# Frontend unit tests
cd frontend
npm run test

# Frontend E2E tests
npm run test:e2e
```

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

**Quick Deploy:**
- Backend: Railway, Render, or AWS
- Frontend: Vercel, Netlify, or Cloudflare Pages
- Database: Railway PostgreSQL or AWS RDS

## 📚 Documentation

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Testing Guide](TESTING.md) - How to run tests
- [Deployment Guide](DEPLOYMENT.md) - Deploy to production
- [Backend README](backend/README.md) - Backend setup & development
- [Frontend README](frontend/README.md) - Frontend setup & development

## 🤝 Contributing

This is a proprietary project. For questions or support, contact:

- Email: cooperxxjohn@gmail.com
- Issues: GitHub Issues (if repository is public)

## 📄 License

Proprietary - All rights reserved

## 🔒 Security

- JWT authentication with bcrypt password hashing
- Rate limiting on all API endpoints
- CORS protection
- SQL injection prevention (parameterized queries)
- File upload validation (type & size)
- Stripe webhook signature verification
- Environment variable security

## 🎯 Roadmap

See [ROADMAP_3_MONTHS.md](ROADMAP_3_MONTHS.md) for detailed 3-month roadmap.

### Next Up (Month 1)
- ✅ Week 1: Testing & Quality Assurance
- [ ] Week 2: Database & Storage (PostgreSQL, S3)
- [ ] Week 3: Deployment & Infrastructure
- [ ] Week 4: Monitoring & Performance

### Future Features
- RS Means pricing integration
- Mobile app (iOS/Android)
- Team collaboration features
- QuickBooks/Sage integration
- Historical pricing data
- Win rate analytics

## 📧 Contact

**John Cooper**
- Email: cooperxxjohn@gmail.com
- Project: Painting.ai

---

**Built with ❤️ to help painting contractors win more bids**

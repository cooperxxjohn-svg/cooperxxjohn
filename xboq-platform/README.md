# XBOQ Platform 🏗️

**AI-Powered Construction Intelligence**

Two products, one platform:
1. **BOQ Generator** - Extract Bill of Quantities from tender documents
2. **Construction Estimator** - Generate estimates for drywall, painting, concrete

---

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
./install.sh
source venv/bin/activate
python app.py
```

Backend runs on: **http://localhost:5000**

### Frontend Setup (Day 2+)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: **http://localhost:3000**

---

## 📂 Project Structure

```
xboq-platform/
├── backend/
│   ├── app.py                    # Unified Flask API
│   ├── modules/
│   │   ├── boq_generator.py      # BOQ extraction
│   │   └── estimator.py          # Construction estimates
│   ├── utils/
│   │   ├── pdf_processor.py      # PDF text extraction
│   │   └── claude_client.py      # Claude API wrapper
│   ├── uploads/                  # Temporary uploads
│   ├── requirements.txt          # Python dependencies
│   ├── install.sh                # Setup script
│   ├── test_backend.py           # Test suite
│   └── README.md                 # Backend docs
│
├── frontend/                     # (Day 2+)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── BOQPage.jsx
│   │   │   └── EstimatorPage.jsx
│   │   └── components/
│   ├── package.json
│   └── README.md
│
└── README.md                     # This file
```

---

## 🎯 Products

### 1. BOQ Generator

**Purpose:** Extract structured Bill of Quantities from tender documents

**How it works:**
1. Upload tender PDF
2. AI extracts all quantities, units, descriptions
3. Returns organized BOQ by construction phase
4. Ready for bidding

**API Endpoint:**
```bash
POST /api/boq/upload
```

### 2. Construction Estimator

**Purpose:** Generate detailed estimates for construction trades

**Supported Trades:**
- ✅ Drywall (materials, labor, costs)
- ✅ Painting (coverage, primer, paint)
- 🚧 Concrete (coming soon)

**How it works:**
1. Manual input OR upload floor plan
2. AI calculates materials and labor
3. Returns professional estimate
4. Bidding-ready breakdown

**API Endpoints:**
```bash
POST /api/estimate/manual   # Manual room input
POST /api/estimate/upload   # Upload floor plan
```

---

## 🛠️ Tech Stack

**Backend:**
- Flask 2.3 - Web framework
- Anthropic Claude - AI generation
- PyPDF2 + Tesseract - PDF extraction
- Python 3.8+

**Frontend (Day 2+):**
- React 18
- Vite
- React Router
- TailwindCSS

---

## 📅 Development Timeline (30-Day Sprint)

### ✅ Day 1: Backend Foundation (COMPLETE)
- [x] Merge backend code (BOQ + Estimator)
- [x] Create unified Flask app
- [x] Shared utilities (PDF processor, Claude client)
- [x] Test suite created
- [x] Documentation complete

### Day 2-7: Frontend Build
- [ ] React Router setup
- [ ] Homepage with product selector
- [ ] BOQ interface (/boq route)
- [ ] Estimator interface (/estimator route)
- [ ] Connect to backend API

### Week 2: Payments & Launch
- [ ] Stripe integration
- [ ] User authentication
- [ ] Deploy to production (xboq.ai)
- [ ] Public launch

### Week 3-4: Sales & Growth
- [ ] Contractor outreach (50+ conversations)
- [ ] First paying customers (10+ target)
- [ ] Product improvements
- [ ] Content marketing

**Goal:** 20+ paying customers, $3K MRR by Day 30

---

## 🔑 Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## 📊 API Documentation

See [backend/README.md](backend/README.md) for complete API docs.

**Key Endpoints:**

```
GET  /health              - Health check
GET  /api/products        - List products
GET  /api/trades          - List trades

POST /api/boq/upload      - BOQ from tender
POST /api/estimate/manual - Manual estimate
POST /api/estimate/upload - Floor plan estimate
```

---

## 🧪 Testing

```bash
cd backend
python test_backend.py
```

Should see:
```
✅ BOQGenerator imported
✅ ConstructionEstimator imported
✅ PDFProcessor imported
✅ Flask app imported
🎉 All tests passed!
```

---

## 🚀 Deployment

### Backend (Render/Railway)

**Build:**
```bash
pip install -r requirements.txt
```

**Start:**
```bash
gunicorn app:app
```

**Environment:**
- `ANTHROPIC_API_KEY`

### Frontend (Vercel/Netlify)

**Build:**
```bash
npm run build
```

**Output:** `dist/`

---

## 📈 Success Metrics

### Week 1
- [ ] Staging deployed
- [ ] Both tools working
- [ ] Database connected

### Week 2
- [ ] Production live (xboq.ai)
- [ ] Stripe payments
- [ ] 50+ signups
- [ ] 5+ paying customers

### Month 1
- [ ] 500+ users
- [ ] 20+ paying customers
- [ ] $3K MRR
- [ ] 100+ contractor conversations

---

## 🤝 Contributing

**Current Focus:** Day 1 Complete ✅

**Next:** Day 2 - Build React frontend with routing

---

## 📄 License

MIT License

---

## 💬 Contact

- **Email:** cooperxxjohn@gmail.com
- **Website:** xboq.ai (coming soon)

---

**Built with ❤️ for contractors and construction professionals**

---

## Day 1 Status Report

### ✅ Completed (4 hours)
1. **Backend merged** - BOQ + Estimator in one Flask app
2. **Modules created:**
   - `boq_generator.py` (94 lines)
   - `estimator.py` (187 lines)
3. **Utilities created:**
   - `pdf_processor.py` (103 lines)
   - `claude_client.py` (55 lines)
4. **Main app:** `app.py` (246 lines)
5. **Testing:** `test_backend.py` ready
6. **Documentation:** Complete README

### 📦 Files Created
- `backend/app.py`
- `backend/modules/boq_generator.py`
- `backend/modules/estimator.py`
- `backend/utils/pdf_processor.py`
- `backend/utils/claude_client.py`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/install.sh`
- `backend/test_backend.py`
- `backend/README.md`
- `README.md` (this file)

### 🎯 Ready For
- Day 2: Frontend build
- Testing with dependencies installed
- Deployment to staging

---

**Time Used:** 4 hours  
**Time Remaining Today:** 6 hours

**Next Tasks (remaining 6 hours):**
1. Install dependencies and test backend (1 hr)
2. Set up staging environment on Render (1 hr)
3. Deploy backend to staging (1 hr)
4. Create frontend project structure (2 hrs)
5. Start homepage component (1 hr)

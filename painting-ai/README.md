# Painting.ai

AI-powered takeoff and estimating software for painting contractors in the USA.

## 🎯 Value Proposition

**Generate accurate painting takeoffs in 5 minutes instead of 4 hours**

- Upload architectural drawings (PDF, PNG, JPG)
- AI automatically detects rooms, walls, ceilings, trim
- Calculates paint quantities and labor hours
- Export to Excel or PDF proposal
- No learning curve - just upload and go

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export ANTHROPIC_API_KEY="your-api-key-here"

# Run server
python main.py
```

Backend runs on http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs on http://localhost:3000

## 📁 Project Structure

```
painting-ai/
├── backend/
│   ├── main.py                  # FastAPI server
│   ├── painting_detector.py    # AI detection engine
│   ├── database.py              # Simple JSON database
│   ├── export_generator.py     # Excel/PDF exports
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── NewProject.jsx
│   │   │   └── ProjectView.jsx
│   │   ├── components/
│   │   │   └── Layout.jsx
│   │   └── utils/
│   │       └── api.js
│   └── package.json
└── docs/
    ├── product_spec.md
    └── painting_formulas.md
```

## 🎨 Features

### MVP (Week 1)

- ✅ Project management
- ✅ Drawing upload (PDF/PNG/JPG)
- ✅ AI room detection
- ✅ Surface area calculation
- ✅ Paint volume calculation
- ✅ Labor hour estimation
- ✅ Excel export
- ✅ PDF proposal export

### Roadmap (Post-MVP)

- [ ] RS Means pricing integration
- [ ] Mobile app
- [ ] Team collaboration
- [ ] Integration with QuickBooks, Sage
- [ ] Historical pricing data
- [ ] Win rate analytics

## 💰 Pricing

- **Free Trial:** 3 projects, no credit card
- **Starter:** $299/month - 50 projects/month
- **Pro:** $699/month - Unlimited projects + API access
- **Enterprise:** $1,499/month - Custom integrations

## 🎯 Target Market

- **Primary:** Commercial painting contractors ($5M-50M revenue)
- **Secondary:** Residential painting contractors ($1M-5M revenue)
- **Market Size:** 300,000+ contractors in USA, $50-60B annual market

## 🔧 Tech Stack

### Backend
- FastAPI (Python)
- Claude Sonnet 4 (AI vision)
- PostgreSQL (planned, using JSON for MVP)
- Anthropic API

### Frontend
- React 18
- Vite
- Tailwind CSS
- React Query

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

See `docs/painting_formulas.md` for complete formulas.

## 🤝 Contributing

This is an MVP in active development. Feedback and contributions welcome!

## 📄 License

Proprietary - All rights reserved

## 📧 Contact

cooperxxjohn@gmail.com

---

**Built with ❤️ to help painting contractors win more bids**

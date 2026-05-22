# Construction Estimator Web App 🏗️

**AI-Powered Takeoffs for Contractors** - Generate professional construction estimates in 40 seconds instead of 4 hours.

Similar to your XBOQ project, but built specifically for construction trades (drywall, painting, concrete, etc.).

---

## Features

### ✅ Currently Supported
- **Drywall Estimation**
  - Manual room input or floor plan upload
  - Material calculations (sheets, compound, tape, screws)
  - Labor breakdown by phase
  - Complete cost breakdown
  - ASTM C840 finish levels

- **Painting Estimation**
  - Wall and ceiling area calculations
  - Paint and primer quantities
  - Labor hours (prep, primer, paint)
  - Material and labor costs

### 🚧 Coming Soon
- Concrete estimation
- MEP trades (electrical, plumbing, HVAC)
- Multi-trade projects
- Export to Excel/PDF
- Project history
- Team collaboration

---

## Tech Stack

### Backend
- **Flask** - Python web framework
- **Anthropic Claude API** - AI-powered estimate generation
- **PyPDF2 & PyMuPDF** - PDF text extraction
- **Pytesseract** - OCR for image-based PDFs
- **Flask-CORS** - Cross-origin support

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **CSS3** - Modern styling with gradients

---

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Tesseract OCR (for floor plan processing)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run backend
python app.py
```

Backend will run on: **http://localhost:5000**

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run on: **http://localhost:3000**

---

## Usage

### Option 1: Manual Input

1. Select trade (Drywall or Painting)
2. Click "Manual Input"
3. Enter room dimensions:
   - Length, width, height
   - Number of doors and windows
4. Add more rooms if needed
5. Click "Generate Estimate"

**Example Input:**
```
Room 1: 20×15 ft, 9ft ceilings, 1 door, 2 windows
Room 2: 12×10 ft, 9ft ceilings, 1 door, 1 window
```

**Output:**
- Material quantities
- Labor hours
- Complete cost breakdown
- Cost per square foot

### Option 2: Upload Floor Plan

1. Select trade
2. Click "Upload Floor Plan"
3. Upload PDF floor plan
4. Click "Upload & Generate Estimate"
5. AI analyzes the plan and returns estimate

**Supported Formats:**
- PDF (searchable or image-based)
- PNG/JPG (via OCR)

---

## API Endpoints

### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "running",
  "version": "1.0.0",
  "service": "Construction Estimator API"
}
```

### Manual Estimate
```
POST /estimate/manual
Content-Type: application/json

{
  "trade": "drywall",
  "rooms": [
    {
      "name": "Room 1",
      "length": 20,
      "width": 15,
      "height": 9,
      "doors": 1,
      "windows": 2
    }
  ],
  "project_type": "commercial",
  "finish_level": 4
}
```

**Response:**
```json
{
  "status": "success",
  "trade": "drywall",
  "estimate": {
    "project_name": "Drywall Estimate",
    "summary": {
      "total_walls": 4,
      "wall_sqft": 585,
      "ceiling_sqft": 300,
      "total_sqft": 885
    },
    "materials": {
      "sheets": 32,
      "compound_lbs": 60,
      "tape_lf": 354,
      "screws": 1600
    },
    "labor": {
      "hanging_hours": 22.13,
      "taping_hours": 5.9,
      "finishing_hours": 5.9,
      "total_hours": 33.92
    },
    "costs": {
      "material_cost": 420.22,
      "labor_cost": 2205.13,
      "subtotal": 2625.35,
      "overhead": 656.34,
      "profit": 656.34,
      "total_cost": 3938.02,
      "cost_per_sqft": 4.45
    }
  }
}
```

### Upload Floor Plan
```
POST /estimate/upload
Content-Type: multipart/form-data

file: [PDF/PNG/JPG file]
trade: "drywall"
```

**Response:** Same as manual estimate

### List Supported Trades
```
GET /trades
```

**Response:**
```json
{
  "trades": [
    {
      "id": "drywall",
      "name": "Drywall",
      "description": "Drywall installation and finishing",
      "available": true
    },
    {
      "id": "painting",
      "name": "Painting",
      "description": "Interior/exterior painting",
      "available": true
    },
    {
      "id": "concrete",
      "name": "Concrete",
      "description": "Concrete work",
      "available": false,
      "coming_soon": true
    }
  ]
}
```

---

## Industry Standards

### Drywall
- **ASTM C840** - Finish levels 0-5
- **RS Means 2026** - Labor rates
- **GA-214** - Gypsum Association standards
- Waste factor: 15%
- Standard sheet: 4' × 8' (32 sqft)
- Labor rates: $65/hr commercial, $60/hr residential

### Painting
- Coverage: 350-400 sqft/gallon
- 2 coats standard
- Labor: $50-60/hr
- Prep work: 30% of total time

---

## Project Structure

```
construction-estimator-web/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── uploads/            # Temporary file uploads
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── App.css         # Styling
│   │   ├── main.jsx        # React entry point
│   │   └── index.css       # Global styles
│   ├── public/
│   ├── index.html          # HTML template
│   ├── vite.config.js      # Vite configuration
│   └── package.json        # Node dependencies
└── README.md               # This file
```

---

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run with auto-reload
python app.py
```

Logs will show:
- File uploads
- PDF processing status
- Claude API calls
- Estimate generation

### Frontend Development
```bash
cd frontend

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Deployment

### Backend (Flask)

**Option 1: Render**
1. Create new Web Service
2. Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variable: `ANTHROPIC_API_KEY`

**Option 2: Railway**
1. Create new project
2. Deploy from GitHub
3. Add `Procfile`: `web: gunicorn app:app`
4. Set environment variables

### Frontend (React + Vite)

**Option 1: Vercel**
```bash
npm run build
vercel --prod
```

**Option 2: Netlify**
```bash
npm run build
netlify deploy --prod --dir=dist
```

Update `frontend/src/App.jsx` to use production backend URL:
```javascript
const API_URL = import.meta.env.PROD 
  ? 'https://your-backend.onrender.com'
  : 'http://localhost:5000'
```

---

## Troubleshooting

### Backend Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**"Anthropic API key not found"**
- Check `.env` file exists
- Verify `ANTHROPIC_API_KEY` is set
- Restart Flask server

**OCR not working**
```bash
# Mac
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Frontend Issues

**"Cannot connect to backend"**
- Verify backend is running on port 5000
- Check CORS is enabled
- Confirm fetch URL is correct

**Vite build errors**
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Roadmap

### Phase 1 (Current)
- [x] Drywall estimation
- [x] Painting estimation
- [x] Manual input mode
- [x] Floor plan upload
- [x] Basic UI

### Phase 2 (Week 2)
- [ ] Concrete estimation
- [ ] Export to Excel/PDF
- [ ] Save project history
- [ ] User authentication

### Phase 3 (Month 1)
- [ ] MEP trades (electrical, plumbing)
- [ ] Multi-trade projects
- [ ] Team collaboration
- [ ] Custom pricing templates

### Phase 4 (Month 2)
- [ ] Mobile app
- [ ] Bluebeam integration
- [ ] Procore integration
- [ ] API for third-party tools

---

## Comparison: Construction Estimator vs XBOQ

| Feature | XBOQ | Construction Estimator |
|---------|------|------------------------|
| Purpose | BOQ from tender docs | Construction estimates |
| Input | Tender PDFs | Floor plans or manual |
| Output | Bill of Quantities | Detailed estimates |
| Trades | General construction | Drywall, Painting, Concrete |
| AI Model | Claude Opus | Claude Opus |
| Backend | Flask + Python | Flask + Python |
| Frontend | React + Vite | React + Vite |
| PDF Processing | PyPDF2 + OCR | PyPDF2 + OCR |
| Use Case | Government tenders | Contractor estimates |

**Same architecture, different domain!**

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes
4. Test locally (both backend and frontend)
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature-name`
7. Create Pull Request

---

## License

MIT License - see LICENSE file

---

## Support

- **Email:** cooperxxjohn@gmail.com
- **Issues:** GitHub Issues
- **Documentation:** This README

---

## Acknowledgments

- Built using same architecture as **XBOQ** (BOQ Generator)
- Powered by **Anthropic Claude** for AI estimates
- Industry standards: ASTM, RS Means, GA-214

---

**Built for contractors, by builders.** 🏗️

**Star this repo if you find it useful!** ⭐

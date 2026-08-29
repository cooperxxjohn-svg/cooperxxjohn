# XBOQ Platform - Backend API

Unified Flask backend serving both BOQ Generator and Construction Estimator.

---

## Architecture

```
Flask App (app.py)
    ├── modules/
    │   ├── boq_generator.py      # BOQ from tender docs
    │   └── estimator.py          # Drywall/Painting estimates
    └── utils/
        ├── pdf_processor.py      # Shared PDF extraction
        └── claude_client.py      # Shared Claude API client
```

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Test Backend

```bash
python test_backend.py
```

Should see:
```
✅ BOQGenerator imported
✅ ConstructionEstimator imported
✅ PDFProcessor imported
✅ Flask app imported
✅ All routes exist
🎉 All tests passed!
```

### 4. Run Server

```bash
python app.py
```

Server runs on: **http://localhost:5000**

---

## API Endpoints

### Health & Info

**GET /health**
```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "running",
  "version": "2.0.0",
  "services": ["BOQ Generator", "Construction Estimator"]
}
```

**GET /api/products**
```bash
curl http://localhost:5000/api/products
```

**GET /api/trades**
```bash
curl http://localhost:5000/api/trades
```

---

### BOQ Generator

**POST /api/boq/upload**

Upload tender document PDF:

```bash
curl -X POST \
  -F "file=@tender.pdf" \
  http://localhost:5000/api/boq/upload
```

Response:
```json
{
  "status": "success",
  "boq": {
    "project_name": "Office Building Tender",
    "sections": [
      {
        "section_name": "SITE PREPARATION",
        "items": [...]
      }
    ]
  },
  "tool": "boq_generator"
}
```

---

### Construction Estimator

**POST /api/estimate/manual**

Manual room input:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "trade": "drywall",
    "rooms": [
      {
        "name": "Office 1",
        "length": 20,
        "width": 15,
        "height": 9,
        "doors": 1,
        "windows": 2
      }
    ],
    "finish_level": 4,
    "project_type": "commercial"
  }' \
  http://localhost:5000/api/estimate/manual
```

**POST /api/estimate/upload**

Upload floor plan:

```bash
curl -X POST \
  -F "file=@floorplan.pdf" \
  -F "trade=drywall" \
  http://localhost:5000/api/estimate/upload
```

Response:
```json
{
  "status": "success",
  "trade": "drywall",
  "estimate": {
    "summary": { "total_sqft": 885 },
    "materials": { "sheets": 32, "compound_lbs": 60 },
    "labor": { "total_hours": 33.92 },
    "costs": { "total_cost": 3938.02 }
  },
  "tool": "estimator"
}
```

---

## Module Details

### BOQ Generator (`modules/boq_generator.py`)

**Purpose:** Extract Bill of Quantities from tender documents

**Process:**
1. Extract text from tender PDF
2. Send to Claude with BOQ extraction prompt
3. Return structured JSON with sections/items

**Usage:**
```python
from modules.boq_generator import BOQGenerator

boq = BOQGenerator()
result = boq.process("tender.pdf")
```

---

### Construction Estimator (`modules/estimator.py`)

**Purpose:** Generate trade estimates (drywall, painting)

**Methods:**
- `generate_drywall_estimate(input_data)` - Drywall calculations
- `generate_painting_estimate(input_data)` - Painting calculations
- `process_floor_plan(pdf_path, trade)` - Extract + estimate from PDF

**Usage:**
```python
from modules.estimator import ConstructionEstimator

estimator = ConstructionEstimator()

# Manual input
result = estimator.generate_drywall_estimate({
    "rooms": [...],
    "finish_level": 4
})

# From floor plan
result = estimator.process_floor_plan("floorplan.pdf", "drywall")
```

---

### PDF Processor (`utils/pdf_processor.py`)

**Purpose:** Extract text from PDFs (hybrid approach)

**Methods:**
- `extract_text_from_searchable_pdf()` - PyPDF2 extraction
- `extract_text_with_ocr()` - Tesseract OCR
- `extract_text_hybrid()` - Try searchable, fallback to OCR

**Usage:**
```python
from utils.pdf_processor import PDFProcessor

processor = PDFProcessor(max_pages=100)
text = processor.extract_text_hybrid("document.pdf")
```

---

### Claude Client (`utils/claude_client.py`)

**Purpose:** Wrapper for Anthropic Claude API

**Methods:**
- `generate(prompt, max_tokens)` - Send prompt, get response

**Usage:**
```python
from utils.claude_client import ClaudeClient

claude = ClaudeClient()
response = claude.generate("Extract BOQ from this text...", max_tokens=3000)
```

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
FLASK_ENV=development
FLASK_DEBUG=True
MAX_FILE_SIZE_MB=100
```

---

## Dependencies

**Core:**
- Flask 2.3.3 - Web framework
- flask-cors 4.0.0 - CORS support
- anthropic - Claude API client

**PDF Processing:**
- PyPDF2 3.0.1 - Searchable PDF extraction
- pymupdf 1.23.8 - Alternative PDF library
- pdf2image 1.16.3 - Convert PDF to images
- pytesseract 0.3.10 - OCR for image-based PDFs
- Pillow 10.0.0 - Image processing

**Deployment:**
- gunicorn 21.2.0 - Production server
- python-dotenv 1.0.0 - Environment variables

---

## Testing

### Run Test Suite

```bash
python test_backend.py
```

### Manual Testing

**1. Test Health Endpoint:**
```bash
curl http://localhost:5000/health
```

**2. Test Products List:**
```bash
curl http://localhost:5000/api/products
```

**3. Test Manual Estimate:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"trade":"drywall","rooms":[{"name":"Test","length":20,"width":15,"height":9}]}' \
  http://localhost:5000/api/estimate/manual
```

---

## Deployment

### Local Development

```bash
python app.py
```

### Production (Render/Railway)

**Procfile:**
```
web: gunicorn app:app
```

**Environment Variables:**
- Add `ANTHROPIC_API_KEY`
- Set `FLASK_ENV=production`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## Troubleshooting

### "Module not found" errors

```bash
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found"

```bash
# Check .env file exists
ls -la .env

# Verify key is set
cat .env | grep ANTHROPIC_API_KEY
```

### OCR not working

```bash
# Mac
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Import errors

```bash
# Make sure you're in the right directory
cd backend

# Activate virtual environment
source venv/bin/activate
```

---

## Day 1 Checklist

- [x] Backend code merged (BOQ + Estimator)
- [x] Unified Flask app created
- [x] All routes implemented
- [x] Test script passing
- [ ] Deploy to staging (next: use Render/Railway)

**Status:** Backend complete! Ready for Day 2 (frontend integration).

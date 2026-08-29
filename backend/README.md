# TakeoffAI Backend

Flask backend for processing construction drawings and generating BOQ using Claude AI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. Run the server:
```bash
python app.py
```

Server will start on `http://localhost:5000`

## API Endpoints

### POST /api/process-drawing
Upload a PDF construction drawing and get BOQ analysis.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (PDF)

**Response:**
```json
{
  "projectName": "Project Name",
  "projectType": "Construction Type",
  "totalValue": 1234567.89,
  "lineItems": 25,
  "accuracy": "High",
  "processingTime": 12.5,
  "boqItems": [
    {
      "item": "1.1",
      "description": "Excavation work",
      "qty": 100.0,
      "unit": "cum",
      "rate": 500.0,
      "amount": 50000.0
    }
  ]
}
```

### GET /api/health
Health check endpoint.

### GET /api/test
Test endpoint to verify API is running.

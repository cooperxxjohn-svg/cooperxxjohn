# TakeoffAI - Full Stack Application

Complete web application for AI-powered Bill of Quantities (BOQ) estimation from construction drawings using Claude AI.

## 🚀 Overview

TakeoffAI automates the creation of Bills of Quantities from construction drawing PDFs using advanced AI. Upload a PDF drawing, and get a detailed BOQ with quantities, rates, and total estimates in minutes.

## 📁 Project Structure

```
cooperxxjohn/
├── backend/              # Flask API server
│   ├── app.py           # Main Flask application
│   ├── requirements.txt # Python dependencies
│   ├── .env.example     # Environment variables template
│   └── README.md        # Backend documentation
│
├── frontend/            # React web application
│   ├── src/
│   │   ├── App.jsx     # Main React component
│   │   ├── index.css   # Tailwind CSS
│   │   └── main.jsx    # React entry point
│   ├── package.json    # Node dependencies
│   └── README.md       # Frontend documentation
│
└── TAKEOFFAI_README.md # This file
```

## 🎯 Features

### Backend (Python Flask)
- ✅ PDF file upload endpoint (`POST /api/process-drawing`)
- ✅ Text extraction from PDFs using PyPDF2
- ✅ Claude AI integration (claude-sonnet-4-20250514) for BOQ generation
- ✅ Structured JSON response with project details and BOQ items
- ✅ CORS enabled for frontend communication
- ✅ Health check and test endpoints

### Frontend (React)
- ✅ Dark theme with gradient background (gray-900 to black)
- ✅ Cyan/blue accent colors throughout
- ✅ Three-tab interface:
  - **Upload**: Drag-and-drop PDF interface
  - **Processing**: Animated loading with 8-15 minute simulation
  - **Results**: BOQ table with statistics
- ✅ Export functionality (CSV and Excel)
- ✅ Responsive design with Tailwind CSS
- ✅ Lucide React icons
- ✅ Real-time API integration

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn
- Anthropic API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. Run the Flask server:
```bash
python app.py
```

Backend will start on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

Frontend will start on `http://localhost:3000`

## 🚀 Running the Application

### Development Mode

1. **Start Backend** (Terminal 1):
```bash
cd backend
python app.py
```

2. **Start Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```

3. **Access Application**:
Open your browser to `http://localhost:3000`

### Production Build

**Backend**:
```bash
cd backend
# Use production WSGI server like gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Frontend**:
```bash
cd frontend
npm run build
npm run preview
```

## 📊 API Documentation

### POST /api/process-drawing

Upload a PDF construction drawing for BOQ generation.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (PDF)

**Response:**
```json
{
  "projectName": "Residential Building Construction",
  "projectType": "Residential",
  "totalValue": 2500000.00,
  "lineItems": 25,
  "accuracy": "High",
  "processingTime": 12.5,
  "boqItems": [
    {
      "item": "1.1",
      "description": "Excavation in foundation",
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

## 🎨 UI Features

### Upload Tab
- Drag-and-drop interface for PDF files
- File size display
- Visual feedback for drag state
- File validation (PDF only)

### Processing Tab
- Animated spinner
- Progress bar (0-100%)
- Step-by-step status updates:
  - Uploading PDF drawing
  - Extracting text and specifications
  - Analyzing with Claude AI
  - Generating BOQ

### Results Tab
- **Statistics Cards**:
  - Total Value (₹)
  - Line Items count
  - Accuracy level
  - Processing time
- **BOQ Table**:
  - Item number
  - Description
  - Quantity
  - Unit
  - Rate
  - Amount
- **Export Options**:
  - Export to CSV
  - Export to Excel

## 🔧 Technologies Used

### Backend
- **Flask** - Web framework
- **PyPDF2** - PDF text extraction
- **Anthropic** - Claude AI API
- **Flask-CORS** - Cross-origin support

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icon library
- **XLSX** - Excel export
- **File-saver** - Download management

## 🔐 Environment Variables

Create a `.env` file in the `backend` directory:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 📝 Usage Example

1. Open the application at `http://localhost:3000`
2. Drag and drop a construction drawing PDF or click to browse
3. Click "Process Drawing"
4. Wait for AI analysis (8-15 minutes simulated, actual time varies)
5. View results in the Results tab
6. Export BOQ as CSV or Excel if needed
7. Click "New Upload" to process another drawing

## 🧪 Testing

**Backend**:
```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test with a sample PDF
curl -X POST -F "file=@sample.pdf" http://localhost:5000/api/process-drawing
```

**Frontend**:
The frontend includes error handling and displays user-friendly messages for:
- Invalid file types
- Upload failures
- API connection issues
- Processing errors

## 🐛 Troubleshooting

**Backend won't start:**
- Check if Python dependencies are installed: `pip install -r requirements.txt`
- Verify ANTHROPIC_API_KEY is set in `.env`
- Ensure port 5000 is not in use

**Frontend won't start:**
- Check if Node dependencies are installed: `npm install`
- Verify port 3000 is not in use
- Clear npm cache: `npm cache clean --force`

**API connection errors:**
- Ensure backend is running on port 5000
- Check CORS configuration in `backend/app.py`
- Verify network/firewall settings

**PDF processing fails:**
- Ensure PDF is not password-protected
- Check file size (max 50MB)
- Verify PDF contains extractable text (not just images)

## 📄 License

This project is proprietary software.

## 👥 Support

For issues and questions, contact the development team.

## 🎉 Credits

Powered by Claude AI (Anthropic)

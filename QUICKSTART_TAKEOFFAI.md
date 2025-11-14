# TakeoffAI Quick Start Guide

Get your TakeoffAI application running in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- Node.js 18+ installed
- Anthropic API key

## Step 1: Set Up Backend

Open Terminal 1:

```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_actual_api_key_here

# Start Flask server
python app.py
```

You should see:
```
TakeoffAI Backend Server
Server starting on http://localhost:5000
✓ Anthropic API key configured
```

## Step 2: Set Up Frontend

Open Terminal 2:

```bash
# Navigate to frontend
cd frontend

# Install Node dependencies (first time only)
npm install

# Start development server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 3: Use the Application

1. Open your browser to **http://localhost:3000**

2. You'll see the TakeoffAI interface with three tabs

3. **Upload a PDF**:
   - Drag and drop a construction drawing PDF
   - Or click to browse and select a file
   - Click "Process Drawing"

4. **Watch Processing**:
   - See real-time progress (8-15 minute simulation)
   - Step-by-step status updates

5. **View Results**:
   - See project details and statistics
   - Browse the generated BOQ table
   - Export to CSV or Excel

## Troubleshooting

**Backend Issues:**
```bash
# Check if backend is running
curl http://localhost:5000/api/health

# Expected response:
# {"status":"healthy","timestamp":"...","api_initialized":true}
```

**Frontend Issues:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**API Key Issues:**
- Verify your `.env` file has `ANTHROPIC_API_KEY=sk-...`
- Make sure there are no quotes around the key
- Restart the backend after changing `.env`

## Testing

Test with a sample API call:
```bash
curl -X POST -F "file=@your_drawing.pdf" http://localhost:5000/api/process-drawing
```

## Production Deployment

**Backend:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Frontend:**
```bash
npm run build
npm run preview
```

## File Structure

```
cooperxxjohn/
├── backend/         # Flask API (Port 5000)
│   ├── app.py
│   ├── requirements.txt
│   └── .env
└── frontend/        # React App (Port 3000)
    ├── src/
    ├── package.json
    └── vite.config.js
```

## Next Steps

- Read TAKEOFFAI_README.md for detailed documentation
- Check backend/README.md for API details
- Check frontend/README.md for UI customization

## Support

If you encounter any issues:
1. Check that both servers are running
2. Verify API key is set correctly
3. Check browser console for errors
4. Review backend logs for API errors

Enjoy using TakeoffAI! 🚀

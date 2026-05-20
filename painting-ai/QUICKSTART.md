# Painting.ai Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Get Your Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Create an API key
4. Copy the key

### Step 2: Set Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

Or create a `.env` file in the `backend/` directory:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Step 3: Run the Application

**Option A: Use the startup script (easiest)**
```bash
./run.sh
```

**Option B: Run manually**

Terminal 1 - Backend:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Step 4: Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 📝 First Project

1. Click **"New Project"**
2. Enter project name (e.g., "Office Renovation")
3. Enter customer name (optional)
4. Click **"Continue"**
5. Upload a floor plan (PDF, PNG, or JPG)
6. Wait for AI processing (~30 seconds)
7. View detected rooms and paintable surfaces
8. Adjust paint price and labor rate as needed
9. Click **"Generate Estimate"**
10. Export to Excel or PDF

## 🎨 Sample Drawings

To test the system, you can use:
- **Free floor plans:** https://www.houseplans.com
- **Sample PDFs:** Search "architectural floor plan PDF sample"
- **Create your own:** Sketch a simple floor plan with room labels

The AI works best with:
- Clear room labels (e.g., "Living Room", "Bedroom 1")
- Visible dimensions
- Standard architectural floor plans
- PDF or high-quality images

## 💡 Tips

### For Best Results:
- Use professional architectural drawings when possible
- Ensure dimensions are visible on the drawing
- Label all rooms clearly
- Include a scale (e.g., "1/4\" = 1'-0\"")

### Pricing Guidance:
- **Paint Price:** $40-80/gallon (depends on quality)
  - Economy: $25-35/gallon
  - Mid-range: $40-55/gallon
  - Premium: $60-80/gallon

- **Labor Rate:** $40-65/hour (depends on location)
  - Rural: $30-45/hour
  - Suburban: $40-55/hour
  - Urban: $50-65/hour

### Coverage Rates:
The system automatically uses these industry-standard rates:
- Smooth drywall: 400 sqft/gallon
- Textured drywall: 350 sqft/gallon
- Wood trim: 350 sqft/gallon

## 🔧 Troubleshooting

### Backend won't start
- **Issue:** `ANTHROPIC_API_KEY not set`
- **Fix:** Run `export ANTHROPIC_API_KEY="your-key-here"`

### Drawing processing fails
- **Issue:** AI can't detect rooms
- **Fix:** Ensure drawing has clear room labels and dimensions

### Frontend won't connect to backend
- **Issue:** CORS error or connection refused
- **Fix:** Make sure backend is running on port 8000

### Excel export is empty
- **Issue:** Estimate not generated yet
- **Fix:** Click "Generate Estimate" before exporting

## 📊 Understanding Results

### Room Detection
The AI detects:
- Room names (from labels on drawing)
- Dimensions (length × width × height)
- Doors and windows (for deductions)

### Surface Calculations
For each room, the system calculates:
- **Walls:** Perimeter × Height - Deductions
- **Ceiling:** Length × Width
- **Trim:** Perimeter - Door widths
- **Doors:** Both sides included

### Paint Requirements
- **Primer:** 1 coat on all surfaces
- **Finish:** 2 coats on all surfaces
- **Waste factor:** 10-15% added automatically

### Labor Estimation
- **Base time:** Surface area ÷ Production rate
- **Prep time:** 15% of base time
- **Touch-up:** 5% of base time
- **Total:** All time combined

## 🎯 Next Steps

1. **Test with real drawings:** Upload your actual project drawings
2. **Validate accuracy:** Compare AI results with manual estimates
3. **Customize pricing:** Adjust rates to match your market
4. **Export proposals:** Generate professional PDFs for clients
5. **Track results:** Monitor how estimates compare to actual costs

## 💬 Support

- **Email:** cooperxxjohn@gmail.com
- **Issues:** Open an issue on GitHub
- **Documentation:** See `/docs` folder for detailed formulas

## 🚀 Production Deployment

Once you're ready to deploy:

1. **Backend:**
   - Deploy to AWS EC2 or Heroku
   - Use PostgreSQL instead of JSON files
   - Set up Redis for caching
   - Configure environment variables

2. **Frontend:**
   - Build: `npm run build`
   - Deploy to Vercel or Netlify
   - Update API base URL

3. **Domain:**
   - Register paintingai.com
   - Set up SSL certificate
   - Configure DNS

## 📈 Success Metrics

Track these to measure success:
- **Accuracy:** ±10% of manual estimates
- **Speed:** <5 minutes vs 4 hours manual
- **Usage:** Projects per week
- **Customer satisfaction:** Testimonials

---

**Ready to transform your painting estimates? Let's go! 🎨**

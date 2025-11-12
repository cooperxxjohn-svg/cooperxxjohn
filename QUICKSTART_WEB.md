# Quick Start Guide - BOQ Web Interface

Get your BOQ estimation web application running in 5 minutes!

## Method 1: Quick Start Script (Recommended)

```bash
# 1. Set your API key in .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Run the application
./run_web.sh
```

That's it! The script will:
- Create a virtual environment
- Install all dependencies
- Start the web server

Access at: **http://localhost:5000**

## Method 2: Manual Setup

### Step 1: Install Dependencies

```bash
# System dependencies
sudo apt-get install poppler-utils  # Ubuntu/Debian
# or
brew install poppler                 # macOS

# Python dependencies
pip install -r requirements.txt
pip install -r web_requirements.txt
```

### Step 2: Configure

```bash
# Create .env file
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 3: Run

```bash
# Development
python web_app.py

# Production
gunicorn --config gunicorn_config.py web_app:app
```

## Method 3: Docker (Zero Setup)

```bash
# 1. Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# 2. Run with Docker Compose
docker-compose -f docker-compose.web.yml up

# Access at http://localhost:5000
```

## Using the Application

### 1. Upload Drawing
- Go to http://localhost:5000
- Upload your construction drawing PDF
- Fill in project details (name and location required)

### 2. Generate BOQ
- Click "Generate BOQ Estimate"
- Wait 1-3 minutes for processing

### 3. Download Results
- View results in the browser
- Download as Excel, PDF, CSV, or JSON

## Troubleshooting

### Problem: Port already in use
```bash
# Use a different port
export PORT=8080
./run_web.sh
```

### Problem: API key error
```bash
# Verify your API key is set
grep ANTHROPIC_API_KEY .env

# Should output: ANTHROPIC_API_KEY=sk-ant-...
```

### Problem: PDF processing fails
```bash
# Install poppler
sudo apt-get install poppler-utils
```

## Next Steps

- Read full documentation: `WEB_APP_README.md`
- Deploy to production: See deployment section in README
- Customize rates: Edit `config.py`

## Support

- Issues: Report on GitHub
- Documentation: See WEB_APP_README.md
- API Docs: https://docs.anthropic.com/

---

**Ready to deploy?** See `WEB_APP_README.md` for production deployment instructions.

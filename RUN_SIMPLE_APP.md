# Simple BOQ Web Interface - Quick Start

A clean, single-file Flask application with embedded HTML templates.

## Features

✓ Simple drag-and-drop file upload
✓ Professional modern UI with Tailwind CSS
✓ Clean results table
✓ Download as CSV, Excel, or PDF
✓ All in one file (simple_app.py)

## Quick Start

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY=your-key-here

# 2. Run the app
python simple_app.py
```

Access at: **http://localhost:8000**

## What You Get

- **Upload Page**: 
  - Drag-and-drop file upload
  - Project details form
  - Clean, modern design

- **Results Page**:
  - Summary cards with total cost
  - Clean BOQ table
  - Download buttons (CSV, Excel, PDF)

- **Single File**: Everything in `simple_app.py`

## Customization

All HTML is embedded in the Python file. Edit the template strings:
- `INDEX_HTML` - Upload page
- `RESULTS_HTML` - Results page

## Production

For production, use Gunicorn:

```bash
gunicorn simple_app:app
```

Or use the full web_app.py for more features.

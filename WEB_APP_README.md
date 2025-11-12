# BOQ Estimation Web Application

A production-ready Flask web interface for the BOQ (Bill of Quantities) Estimation System. This application allows government contractors to upload construction drawings and automatically generate CPWD-compliant BOQ estimates.

## Features

- 📤 **Simple File Upload**: Drag-and-drop or browse to upload PDF construction drawings
- 🤖 **AI-Powered Extraction**: Automatic extraction of quantities using Claude Vision API
- ✅ **CPWD Validation**: Automatic compliance checking against government standards
- 📊 **Professional Results Display**: Clean, organized presentation of BOQ items
- 💾 **Multiple Export Formats**: Download BOQ as Excel, PDF, CSV, or JSON
- 🔒 **Production-Ready**: Secure, scalable, and deployment-ready

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Anthropic API key (for Claude Vision)
- Poppler utilities (for PDF processing)

### Installation

1. **Install system dependencies:**

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install poppler-utils

   # macOS
   brew install poppler
   ```

2. **Install Python dependencies:**

   ```bash
   # Install core BOQ system dependencies
   pip install -r requirements.txt

   # Install web application dependencies
   pip install -r web_requirements.txt
   ```

3. **Set environment variables:**

   ```bash
   # Create .env file
   cat > .env << EOF
   ANTHROPIC_API_KEY=your-api-key-here
   SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   FLASK_DEBUG=False
   EOF
   ```

4. **Run the application:**

   ```bash
   # Development server
   python web_app.py

   # Production server with Gunicorn
   gunicorn --config gunicorn_config.py web_app:app
   ```

5. **Access the application:**

   Open your browser and navigate to: `http://localhost:5000`

## Docker Deployment

### Quick Start with Docker

1. **Build and run with Docker Compose:**

   ```bash
   # Create .env file with your API key
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env

   # Build and start the application
   docker-compose -f docker-compose.web.yml up -d

   # View logs
   docker-compose -f docker-compose.web.yml logs -f
   ```

2. **Access the application:**

   Navigate to: `http://localhost:5000`

3. **Stop the application:**

   ```bash
   docker-compose -f docker-compose.web.yml down
   ```

### With Nginx Reverse Proxy

For production deployments with SSL and load balancing:

```bash
# Start with Nginx
docker-compose -f docker-compose.web.yml --profile nginx up -d
```

This will:
- Run the Flask app on port 5000 (internal)
- Run Nginx on ports 80 (HTTP) and 443 (HTTPS)
- Provide SSL termination (configure SSL certificates in `nginx.conf`)
- Add rate limiting and security headers

## Usage Guide

### 1. Upload Drawings

- Click "Choose PDF files" or drag and drop your construction drawing PDFs
- Multiple files are supported (up to 50MB each)
- Only PDF format is accepted

### 2. Fill Project Details

**Required fields:**
- Project Name
- Location

**Optional fields:**
- Contract Number
- Department (defaults to CPWD)
- Client Name
- Completion Period
- Estimated Cost

### 3. Generate BOQ

- Click "Generate BOQ Estimate"
- Processing typically takes 1-3 minutes
- The system will:
  - Extract quantities from drawings using AI
  - Calculate rates and amounts
  - Validate against CPWD standards
  - Generate complete BOQ

### 4. Review Results

The results page displays:
- **Summary**: Total cost, project details
- **Validation Status**: CPWD compliance check results
- **Category Summary**: Breakdown by work category
- **Detailed BOQ**: All items with specifications and rates
- **Material & Labour Breakdown**: Click any item to expand details

### 5. Download BOQ

Choose from multiple formats:
- **Excel (.xlsx)**: Fully formatted spreadsheet with all details
- **PDF**: Professional PDF document ready for printing
- **CSV**: Simple spreadsheet format
- **JSON**: Raw data for further processing

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (required) | - |
| `SECRET_KEY` | Flask secret key for sessions | Auto-generated |
| `FLASK_DEBUG` | Enable debug mode | False |
| `PORT` | Server port | 5000 |
| `GUNICORN_WORKERS` | Number of worker processes | CPU count × 2 + 1 |
| `LOG_LEVEL` | Logging level | info |

### Application Settings

Edit `web_app.py` to customize:
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 50MB)
- `ALLOWED_EXTENSIONS`: Allowed file types (default: PDF)
- File cleanup age (default: 24 hours)

## Production Deployment

### Option 1: Traditional Server (Ubuntu/Debian)

1. **Install dependencies:**

   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3-pip poppler-utils nginx
   ```

2. **Set up application:**

   ```bash
   # Clone or copy application files
   cd /opt
   git clone <your-repo> boq-web
   cd boq-web

   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt -r web_requirements.txt
   ```

3. **Configure systemd service:**

   Create `/etc/systemd/system/boq-web.service`:

   ```ini
   [Unit]
   Description=BOQ Web Application
   After=network.target

   [Service]
   Type=notify
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/boq-web
   Environment="PATH=/opt/boq-web/venv/bin"
   Environment="ANTHROPIC_API_KEY=your-api-key"
   Environment="SECRET_KEY=your-secret-key"
   ExecStart=/opt/boq-web/venv/bin/gunicorn --config gunicorn_config.py web_app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start service:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable boq-web
   sudo systemctl start boq-web
   ```

5. **Configure Nginx:**

   Create `/etc/nginx/sites-available/boq-web`:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       client_max_body_size 50M;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_connect_timeout 300;
           proxy_send_timeout 300;
           proxy_read_timeout 300;
       }

       location /static {
           alias /opt/boq-web/static;
           expires 1y;
       }
   }
   ```

   Enable and restart:

   ```bash
   sudo ln -s /etc/nginx/sites-available/boq-web /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Option 2: Docker Deployment

See Docker section above for quick deployment with Docker Compose.

### Option 3: Cloud Platforms

#### AWS Elastic Beanstalk

1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init -p python-3.11 boq-web`
3. Create environment: `eb create boq-web-env`
4. Set environment variables:
   ```bash
   eb setenv ANTHROPIC_API_KEY=your-key SECRET_KEY=your-secret
   ```
5. Deploy: `eb deploy`

#### Google Cloud Run

1. Build image: `gcloud builds submit --tag gcr.io/PROJECT_ID/boq-web -f Dockerfile.web`
2. Deploy:
   ```bash
   gcloud run deploy boq-web \
     --image gcr.io/PROJECT_ID/boq-web \
     --platform managed \
     --set-env-vars ANTHROPIC_API_KEY=your-key
   ```

#### Heroku

1. Create `Procfile`:
   ```
   web: gunicorn --config gunicorn_config.py web_app:app
   ```
2. Deploy:
   ```bash
   heroku create boq-web
   heroku config:set ANTHROPIC_API_KEY=your-key
   git push heroku main
   ```

## Architecture

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask Web App  │  ← User interface
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  BOQ Estimator  │  ← Core estimation engine
└────────┬────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌──────────────────┐  ┌───────────────┐
│ Claude Vision API│  │ CPWD Validator│
└──────────────────┘  └───────────────┘
```

### Components

- **web_app.py**: Flask application with routes and handlers
- **templates/**: Jinja2 templates for UI
- **static/**: CSS, JavaScript, and static assets
- **gunicorn_config.py**: Production server configuration
- **BOQ Estimator**: Core estimation engine (from existing system)

## Security Considerations

1. **API Key Protection**:
   - Never commit API keys to version control
   - Use environment variables or secrets management
   - Rotate keys periodically

2. **File Upload Security**:
   - Only PDF files are accepted
   - File size limited to 50MB
   - Uploaded files are stored temporarily and cleaned up

3. **Session Security**:
   - Use strong SECRET_KEY (auto-generated)
   - Sessions are server-side only
   - CSRF protection enabled

4. **Production Settings**:
   - Debug mode disabled in production
   - HTTPS recommended (use Nginx with SSL)
   - Rate limiting via Nginx
   - Regular security updates

## Monitoring & Logging

### Application Logs

Logs are written to:
- **Console**: stdout/stderr (captured by Gunicorn)
- **Files**: `logs/` directory (in production)

### Health Check Endpoint

Monitor application health:
```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "api_key_configured": true
}
```

### Metrics

For production monitoring, integrate with:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking
- **CloudWatch/Stackdriver**: Cloud-native monitoring

## Troubleshooting

### Issue: API key not configured

**Error**: "System configuration error: API key not configured"

**Solution**:
```bash
export ANTHROPIC_API_KEY=your-api-key-here
# or add to .env file
```

### Issue: File upload fails

**Error**: "File too large"

**Solution**: Increase `MAX_CONTENT_LENGTH` in `web_app.py` or Nginx `client_max_body_size`

### Issue: PDF processing fails

**Error**: "Unable to convert PDF"

**Solution**: Install poppler-utils:
```bash
sudo apt-get install poppler-utils  # Ubuntu
brew install poppler                 # macOS
```

### Issue: Slow processing

**Cause**: Large or complex drawings

**Solutions**:
- Increase timeout in `gunicorn_config.py` (default: 300s)
- Increase Nginx proxy timeout
- Use async task queue (Celery) for background processing

## Performance Optimization

1. **Increase Workers**: Adjust `GUNICORN_WORKERS` based on CPU cores
2. **Enable Caching**: Cache drawing extraction results
3. **Use CDN**: Serve static files from CDN in production
4. **Async Processing**: Implement Celery for long-running tasks
5. **Database**: Store BOQ results in database instead of sessions

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=web_app tests/
```

### Code Style

```bash
# Install formatting tools
pip install black flake8 isort

# Format code
black web_app.py
isort web_app.py

# Check style
flake8 web_app.py
```

## Support

- **Documentation**: See main `README.md` for BOQ system details
- **Issues**: Report bugs or request features via GitHub issues
- **API Documentation**: https://docs.anthropic.com/claude/reference

## License

[Your License Here]

## Credits

Built with:
- Flask - Web framework
- Claude AI - Vision and language processing
- ReportLab - PDF generation
- Gunicorn - WSGI server
- CPWD standards for BOQ calculations

# Quick Start Guide - Week 2 (Database & Storage)

Get Painting.ai running with PostgreSQL, Redis, and S3 in 5 minutes.

---

## Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ installed
- AWS account (optional, for S3)
- Anthropic API key

---

## Step 1: Clone & Setup

```bash
# Clone repository (if not already)
git clone https://github.com/your-username/painting-ai.git
cd painting-ai

# Create environment file
cp .env.example .env
```

---

## Step 2: Configure Environment

Edit `.env` file with your credentials:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here
SECRET_KEY=your-secret-key-at-least-32-characters-long

# Database (defaults are fine for local development)
DATABASE_URL=postgresql://paintingai:changeme123@localhost:5432/paintingai
POSTGRES_USER=paintingai
POSTGRES_PASSWORD=changeme123
POSTGRES_DB=paintingai

# Redis (defaults are fine)
REDIS_URL=redis://localhost:6379/0

# S3 (optional for development - set S3_ENABLED=false to use local storage)
S3_ENABLED=false
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
# AWS_S3_BUCKET_UPLOADS=paintingai-uploads
# AWS_S3_BUCKET_EXPORTS=paintingai-exports
```

---

## Step 3: Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be ready (30 seconds)
docker-compose ps

# Check health
docker-compose logs postgres | tail -20
docker-compose logs redis | tail -20
```

**Expected output:**
```
postgres  | database system is ready to accept connections
redis     | Ready to accept connections
```

---

## Step 4: Setup Backend

```bash
cd backend

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify configuration
python config.py
```

**Expected output:**
```
============================================================
PAINTING.AI CONFIGURATION
============================================================

Environment: development
Host: 0.0.0.0:8000

Database:
  Connected: True
  Pool Size: 20

Redis:
  Configured: True

S3 Storage:
  Enabled: False
  Configured: False
  Region: us-east-1

✅ Configuration valid!
============================================================
```

---

## Step 5: Run Database Migrations

```bash
# Still in backend directory
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> abc123, Initial schema
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, Add indexes
```

---

## Step 6: Start Backend Server

```bash
# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 7: Verify Health

Open a new terminal and run:

```bash
# Check overall health
curl http://localhost:8000/health

# Check database health
curl http://localhost:8000/health/database

# Check Redis health
curl http://localhost:8000/health/redis

# Check S3 health (will show "not configured" if disabled)
curl http://localhost:8000/health/storage
```

**Expected responses:**

**Overall Health:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-21T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "s3": "not_configured"
  }
}
```

**Database Health:**
```json
{
  "status": "healthy",
  "pool": {
    "size": 20,
    "checked_in": 19,
    "checked_out": 1,
    "overflow": 0
  },
  "latency_ms": 5
}
```

---

## Step 8: Start Frontend (Optional)

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Expected output:**
```
  ➜  Local:   http://localhost:3000
  ➜  Network: http://192.168.1.100:3000
```

---

## Step 9: Test the System

### Create a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "name": "Test User",
    "company": "Test Company"
  }'
```

### Create a Project

```bash
# Save the access_token from registration response

curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Test Project",
    "customer": "ABC Construction"
  }'
```

### Upload a Drawing

```bash
# Save the project_id from project creation response

curl -X POST http://localhost:8000/projects/PROJECT_ID/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/floor_plan.pdf"
```

---

## Step 10: Run Tests

```bash
# In backend directory with venv activated

# Run integration tests
pytest tests/test_week2_integration.py -v

# Run all tests
./run_tests.sh
```

---

## Common Issues & Solutions

### Issue: PostgreSQL connection refused

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# If not running, start it
docker-compose up -d postgres

# Wait 30 seconds for startup
sleep 30

# Check logs
docker-compose logs postgres
```

### Issue: Redis connection refused

**Solution:**
```bash
# Start Redis
docker-compose up -d redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Issue: Alembic migration fails

**Solution:**
```bash
# Check database is accessible
psql postgresql://paintingai:changeme123@localhost:5432/paintingai -c "SELECT 1;"

# Reset migrations (CAUTION: drops all data)
alembic downgrade base
alembic upgrade head
```

### Issue: S3 credentials error (in production)

**Solution:**
```bash
# For development, disable S3
echo "S3_ENABLED=false" >> .env

# For production, verify AWS credentials
aws s3 ls s3://paintingai-uploads

# Create buckets if they don't exist
aws s3 mb s3://paintingai-uploads
aws s3 mb s3://paintingai-exports
```

### Issue: Import errors

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify boto3 is installed
pip show boto3

# If missing, install manually
pip install boto3==1.34.34
```

---

## Development Workflow

### Daily Development

```bash
# Start services
docker-compose up -d postgres redis

# Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

### Stop Services

```bash
# Stop backend: Ctrl+C in terminal

# Stop frontend: Ctrl+C in terminal

# Stop Docker services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### View Logs

```bash
# Backend logs: in terminal running uvicorn

# Database logs
docker-compose logs -f postgres

# Redis logs
docker-compose logs -f redis

# All services
docker-compose logs -f
```

---

## Production Setup (AWS S3)

### 1. Create S3 Buckets

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create buckets
aws s3 mb s3://paintingai-uploads --region us-east-1
aws s3 mb s3://paintingai-exports --region us-east-1

# Enable versioning (for backup/recovery)
aws s3api put-bucket-versioning \
  --bucket paintingai-uploads \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
  --bucket paintingai-exports \
  --versioning-configuration Status=Enabled
```

### 2. Configure CORS (for direct uploads)

Create `cors.json`:
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://paintingai.com", "http://localhost:3000"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

Apply CORS:
```bash
aws s3api put-bucket-cors \
  --bucket paintingai-uploads \
  --cors-configuration file://cors.json
```

### 3. Update .env for Production

```bash
S3_ENABLED=true
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
AWS_S3_BUCKET_UPLOADS=paintingai-uploads
AWS_S3_BUCKET_EXPORTS=paintingai-exports
S3_SIGNED_URL_EXPIRY=86400
```

### 4. Test S3 Integration

```bash
# Run S3 integration tests
pytest tests/test_week2_integration.py::TestS3Integration -v

# Verify S3 health
curl http://localhost:8000/health/storage
```

---

## Performance Tips

### Database Optimization

```bash
# In .env, tune connection pool for your workload
DB_POOL_SIZE=20          # Base connections
DB_MAX_OVERFLOW=10       # Extra connections when busy
DB_POOL_TIMEOUT=30       # Seconds to wait for connection
DB_POOL_RECYCLE=3600     # Recycle connections after 1 hour
```

### Redis Optimization

```bash
# Use separate databases for different purposes
REDIS_SESSION_DB=1    # User sessions
REDIS_CACHE_DB=2      # API response cache
```

### S3 Optimization

```bash
# Longer signed URL expiry for exports (1 week)
S3_SIGNED_URL_EXPIRY=604800

# Enable CloudFront CDN for faster downloads
# (Configure in AWS Console)
```

---

## Monitoring

### Check System Health

```bash
# Overall health
curl http://localhost:8000/health | jq

# Database pool status
curl http://localhost:8000/health/database | jq '.pool'

# Redis latency
curl http://localhost:8000/health/redis | jq '.latency_ms'
```

### Database Backup

```bash
# Manual backup
docker-compose exec postgres pg_dump -U paintingai paintingai > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U paintingai paintingai
```

---

## Next Steps

1. ✅ Services running
2. ✅ Health checks passing
3. ✅ Test user created
4. ✅ Test project created

**Ready for:**
- Week 3: Production deployment
- Load testing
- Frontend integration
- User acceptance testing

---

## Support

**Documentation:**
- API Reference: http://localhost:8000/docs
- Configuration: `WEEK2_COMPLETE.md`
- Troubleshooting: See "Common Issues" section above

**Need Help?**
1. Check logs: `docker-compose logs`
2. Verify config: `python backend/config.py`
3. Run health checks: `curl http://localhost:8000/health`
4. Check database: `docker-compose exec postgres psql -U paintingai`

---

**Status:** Week 2 infrastructure ready! 🚀

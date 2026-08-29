# Deployment Guide

Production deployment guide for Painting.ai

---

## Quick Deploy (Docker)

### Prerequisites
- Docker & Docker Compose installed
- Domain name pointed to server
- SSL certificate (Let's Encrypt)

### 1. Clone & Configure

```bash
git clone <repo>
cd painting-ai

# Copy and edit environment variables
cp .env.example .env
nano .env
```

Set these required variables:
```
ANTHROPIC_API_KEY=your-key
STRIPE_SECRET_KEY=your-key
DATABASE_URL=postgresql://paintingai:password@postgres:5432/paintingai
```

### 2. Deploy

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Initialize Database

```bash
# Load demo data
docker-compose exec backend python demo_data.py
```

### 4. Access

- Frontend: http://your-domain.com
- API: http://your-domain.com/api
- Docs: http://your-domain.com/api/docs

---

## Production Deployment (AWS)

### Architecture

```
                  ┌─────────────┐
                  │  Route 53   │
                  │   (DNS)     │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │ CloudFront  │
                  │    (CDN)    │
                  └──────┬──────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │   S3    │     │   ALB   │     │   S3    │
   │(Static) │     │(LB)     │     │(Uploads)│
   └─────────┘     └────┬────┘     └─────────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
         ┌────▼───┐ ┌──▼────┐ ┌──▼────┐
         │  ECS   │ │  ECS  │ │  ECS  │
         │Backend │ │Backend│ │Backend│
         └────┬───┘ └───┬───┘ └───┬───┘
              │         │         │
              └─────────┼─────────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
         ┌────▼────┐ ┌──▼─────┐
         │   RDS   │ │ ElastiCache│
         │(Postgres│ │  (Redis)   │
         └─────────┘ └──────────┘
```

### 1. Infrastructure Setup

```bash
# Install AWS CLI
pip install awscli

# Configure
aws configure

# Create resources
./deploy/setup-aws.sh
```

### 2. Database Migration

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier paintingai-prod \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username paintingai \
  --master-user-password <password> \
  --allocated-storage 20

# Run migrations
alembic upgrade head
```

### 3. Deploy Backend

```bash
# Build and push Docker image
docker build -t paintingai/backend:latest backend/
docker tag paintingai/backend:latest <ecr-url>/paintingai/backend:latest
docker push <ecr-url>/paintingai/backend:latest

# Update ECS service
aws ecs update-service \
  --cluster paintingai \
  --service backend \
  --force-new-deployment
```

### 4. Deploy Frontend

```bash
# Build
cd frontend
npm run build

# Deploy to S3
aws s3 sync dist/ s3://paintingai-frontend/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <id> \
  --paths "/*"
```

---

## Environment Variables

### Required
```bash
ANTHROPIC_API_KEY=        # From console.anthropic.com
STRIPE_SECRET_KEY=        # From stripe.com
DATABASE_URL=             # PostgreSQL connection string
```

### Optional
```bash
REDIS_URL=                # Redis connection (for caching)
SENTRY_DSN=               # Error tracking
SENDGRID_API_KEY=         # Email notifications
AWS_ACCESS_KEY_ID=        # For S3 uploads
AWS_SECRET_ACCESS_KEY=    # For S3 uploads
```

---

## Monitoring

### Health Checks

```bash
# API health
curl https://api.paintingai.com/health

# Database connection
curl https://api.paintingai.com/health/db

# Redis connection
curl https://api.paintingai.com/health/redis
```

### Logs

```bash
# View backend logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f postgres

# View all logs
docker-compose logs -f
```

### Metrics

```bash
# Get analytics stats
curl https://api.paintingai.com/admin/stats

# Get error logs
curl https://api.paintingai.com/admin/errors
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale backend
docker-compose up -d --scale backend=3

# On ECS
aws ecs update-service \
  --cluster paintingai \
  --service backend \
  --desired-count 5
```

### Database Scaling

```bash
# Upgrade RDS instance
aws rds modify-db-instance \
  --db-instance-identifier paintingai-prod \
  --db-instance-class db.t3.large \
  --apply-immediately
```

---

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups (RDS)
aws rds modify-db-instance \
  --db-instance-identifier paintingai-prod \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"

# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier paintingai-prod \
  --db-snapshot-identifier paintingai-backup-$(date +%Y%m%d)
```

### File Backups

```bash
# Sync uploads to S3
aws s3 sync /app/uploads s3://paintingai-backups/uploads/

# Restore from S3
aws s3 sync s3://paintingai-backups/uploads/ /app/uploads/
```

---

## Security

### SSL Certificate

```bash
# Let's Encrypt (free)
certbot --nginx -d paintingai.com -d www.paintingai.com

# Auto-renewal
certbot renew --dry-run
```

### Secrets Management

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name paintingai/prod \
  --secret-string '{"ANTHROPIC_API_KEY":"xxx","STRIPE_SECRET_KEY":"yyy"}'
```

### Rate Limiting

```nginx
# In nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}
```

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing ANTHROPIC_API_KEY
#    Fix: Set in .env file
# 2. Database connection failed
#    Fix: Check DATABASE_URL
# 3. Port already in use
#    Fix: Change port in docker-compose.yml
```

### Frontend shows blank page

```bash
# Check if backend is accessible
curl http://localhost:8000/health

# Check nginx logs
docker-compose logs frontend

# Rebuild frontend
cd frontend && npm run build
```

### Database connection issues

```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U paintingai

# Reset database
docker-compose down -v
docker-compose up -d
```

---

## Cost Optimization

### Estimated Monthly Costs

**100 customers:**
- ECS (2 × t3.small): $30
- RDS (db.t3.small): $40
- ElastiCache (cache.t3.micro): $15
- S3 + CloudFront: $10
- Anthropic API (20K API calls): $100
- **Total: ~$195/month**

**1,000 customers:**
- ECS (4 × t3.medium): $120
- RDS (db.t3.large): $180
- ElastiCache (cache.t3.small): $40
- S3 + CloudFront: $50
- Anthropic API (200K API calls): $1,000
- **Total: ~$1,390/month**

### Optimization Tips

1. **Use reserved instances** (30-50% savings)
2. **Enable S3 lifecycle policies** (move old files to Glacier)
3. **Cache API responses** (reduce Anthropic API calls)
4. **Use spot instances** for batch processing
5. **Optimize Docker images** (reduce deployment time)

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
- Push to main → Run tests
- Tests pass → Build Docker images
- Push images to ECR
- Deploy to ECS
- Run smoke tests
- Notify Slack
```

---

## Support

- **Docs:** https://docs.paintingai.com
- **Status:** https://status.paintingai.com
- **Email:** support@paintingai.com

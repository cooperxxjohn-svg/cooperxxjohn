# Database Setup Guide

Complete guide for setting up PostgreSQL and Redis for Painting.ai.

## Overview

Painting.ai uses:
- **PostgreSQL 15** - Production database
- **Redis 7** - Caching and session management
- **Alembic** - Database migrations
- **SQLAlchemy** - ORM

## Quick Start

### 1. Start Database Services

```bash
# Start PostgreSQL and Redis with Docker Compose
docker-compose up -d postgres redis

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres redis
```

### 2. Run Migrations

```bash
# Navigate to backend directory
cd backend

# Run Alembic migrations
alembic upgrade head

# Check migration status
alembic current
```

### 3. Verify Setup

```bash
# Test database connection
python database_service.py

# Run migration tests
pytest tests/test_database_migration.py -v
```

## Detailed Setup

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database Configuration
DATABASE_URL=postgresql://paintingai:your-password@localhost:5432/paintingai
POSTGRES_USER=paintingai
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=paintingai
POSTGRES_PORT=5432

# Database Connection Pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_PORT=6379
REDIS_SESSION_DB=1
REDIS_CACHE_DB=2
```

### Docker Compose Configuration

The `docker-compose.yml` includes:

**PostgreSQL:**
- Image: `postgres:15-alpine`
- Port: `5432`
- Persistent volume: `postgres_data`
- Health checks enabled
- Auto-restart policy

**Redis:**
- Image: `redis:7-alpine`
- Port: `6379`
- Persistent volume: `redis_data`
- AOF persistence enabled
- Health checks enabled

### Database Schema

The database includes these tables:

**Core Tables:**
- `users` - User accounts and authentication
- `organizations` - Company organizations
- `team_members` - Organization team members
- `projects` - Painting projects
- `rooms` - Project rooms
- `drawings` - Uploaded floor plans
- `material_items` - Project materials

**Support Tables:**
- `templates` - Reusable templates
- `assemblies` - Pre-built assemblies
- `pricing_data` - Historical pricing
- `activities` - Activity logs
- `notifications` - User notifications
- `integrations` - Third-party integrations
- `webhooks` - Webhook endpoints
- `api_usage` - API usage tracking

## Database Operations

### Connect to PostgreSQL

```bash
# Using Docker
docker exec -it paintingai_db psql -U paintingai -d paintingai

# Using psql directly
psql -h localhost -U paintingai -d paintingai
```

### Common SQL Commands

```sql
-- List all tables
\dt

-- Describe a table
\d users

-- Count records
SELECT COUNT(*) FROM users;

-- View recent projects
SELECT id, name, status, created_at FROM projects ORDER BY created_at DESC LIMIT 10;

-- Check user projects
SELECT u.email, COUNT(p.id) as project_count 
FROM users u 
LEFT JOIN projects p ON u.id = p.owner_id 
GROUP BY u.email;
```

### Alembic Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current

# Rollback to specific version
alembic downgrade <revision_id>
```

### Backup and Restore

```bash
# Backup database
docker exec paintingai_db pg_dump -U paintingai paintingai > backup.sql

# Restore database
docker exec -i paintingai_db psql -U paintingai -d paintingai < backup.sql

# Backup with compression
docker exec paintingai_db pg_dump -U paintingai paintingai | gzip > backup.sql.gz

# Restore from compressed backup
gunzip -c backup.sql.gz | docker exec -i paintingai_db psql -U paintingai -d paintingai
```

## Connection Pooling

The application uses SQLAlchemy connection pooling for optimal performance:

**Configuration:**
- `pool_size=20` - Base number of connections
- `max_overflow=10` - Additional connections when needed
- `pool_timeout=30` - Wait time for connection (seconds)
- `pool_recycle=3600` - Recycle connections after 1 hour
- `pool_pre_ping=True` - Verify connections before use

**Monitoring:**

```python
from database_service import db

# Get pool status
status = db.get_pool_status()
print(f"Pool size: {status['pool_size']}")
print(f"Checked out: {status['checked_out']}")
print(f"Checked in: {status['checked_in']}")
```

## Redis Operations

### Connect to Redis

```bash
# Using Docker
docker exec -it paintingai_redis redis-cli

# Test connection
redis-cli ping
```

### Common Redis Commands

```bash
# Select database
SELECT 0

# View all keys
KEYS *

# Get a value
GET key_name

# Set a value
SET key_name value

# Delete a key
DEL key_name

# Clear database
FLUSHDB

# View memory usage
INFO memory
```

### Redis Databases

The application uses separate Redis databases:
- **DB 0** - General cache
- **DB 1** - Session storage
- **DB 2** - Application cache

## Performance Tuning

### PostgreSQL Optimization

Edit `postgresql.conf` for production:

```conf
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB

# Connections
max_connections = 100

# Checkpoints
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query Planner
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Create Indexes

```sql
-- Email lookup
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- API key lookup
CREATE INDEX CONCURRENTLY idx_users_api_key ON users(api_key);

-- Project status
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);

-- Project owner
CREATE INDEX CONCURRENTLY idx_projects_owner_id ON projects(owner_id);

-- Room project
CREATE INDEX CONCURRENTLY idx_rooms_project_id ON rooms(project_id);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY idx_projects_owner_status 
ON projects(owner_id, status);

CREATE INDEX CONCURRENTLY idx_activities_project_created 
ON activities(project_id, created_at DESC);
```

## Troubleshooting

### PostgreSQL Issues

**Connection refused:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Migration errors:**
```bash
# Check current migration version
alembic current

# View pending migrations
alembic history

# Reset to specific version
alembic downgrade <revision_id>
alembic upgrade head
```

**Slow queries:**
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Reload configuration
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Redis Issues

**Connection refused:**
```bash
# Check if Redis is running
docker-compose ps redis

# Check logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

**Memory issues:**
```bash
# Check memory usage
redis-cli INFO memory

# Set max memory
redis-cli CONFIG SET maxmemory 256mb

# Set eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Common Errors

**Error: `password authentication failed`**
- Check `POSTGRES_PASSWORD` in `.env`
- Ensure password matches in `DATABASE_URL`
- Restart PostgreSQL container

**Error: `role "paintingai" does not exist`**
- Rebuild PostgreSQL container
- Run initialization script

**Error: `database "paintingai" does not exist`**
```bash
# Create database manually
docker exec -it paintingai_db psql -U paintingai -c "CREATE DATABASE paintingai;"
```

**Error: `connection pool exhausted`**
- Increase `DB_POOL_SIZE` in `.env`
- Check for connection leaks
- Monitor with `db.get_pool_status()`

## Monitoring

### Database Health Check

```bash
# PostgreSQL health
docker exec paintingai_db pg_isready -U paintingai

# Redis health
docker exec paintingai_redis redis-cli ping
```

### Database Size

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('paintingai'));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Connection Monitoring

```sql
-- Active connections
SELECT COUNT(*) FROM pg_stat_activity;

-- Connection details
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'paintingai';
```

## Production Deployment

### Security Checklist

- [ ] Change default passwords
- [ ] Use strong `POSTGRES_PASSWORD`
- [ ] Set `REDIS_PASSWORD`
- [ ] Enable SSL/TLS for connections
- [ ] Restrict database ports (don't expose publicly)
- [ ] Enable firewall rules
- [ ] Regular backups configured
- [ ] Monitoring and alerting setup

### Backup Strategy

**Automated backups:**

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/paintingai_$TIMESTAMP.sql.gz"

# Create backup
docker exec paintingai_db pg_dump -U paintingai paintingai | gzip > $BACKUP_FILE

# Keep last 7 days
find $BACKUP_DIR -name "paintingai_*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
```

**Cron job:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup-db.sh
```

### Monitoring Setup

Use tools like:
- **pg_stat_statements** - Query performance
- **pgBadger** - Log analysis
- **Prometheus + Grafana** - Metrics and dashboards
- **Sentry** - Error tracking

## Testing

Run the test suite:

```bash
# Run all database tests
pytest backend/tests/test_database_migration.py -v

# Run specific test
pytest backend/tests/test_database_migration.py::TestDatabaseMigration::test_user_crud -v

# Run with coverage
pytest backend/tests/test_database_migration.py --cov=backend --cov-report=html
```

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## Support

For issues or questions:
1. Check logs: `docker-compose logs postgres redis`
2. Review this documentation
3. Check GitHub issues
4. Contact support: cooperxxjohn@gmail.com

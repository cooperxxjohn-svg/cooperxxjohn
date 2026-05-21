# Database Quick Start

Quick reference for common database operations.

## Setup (One-time)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and set database password
nano .env  # Change POSTGRES_PASSWORD

# 3. Start databases and run migrations
make db-setup
```

## Daily Commands

```bash
# Start databases
docker-compose up -d postgres redis

# Stop databases
docker-compose down

# View logs
docker-compose logs -f postgres redis

# Check status
make db-status
```

## Migration Commands

```bash
# Run pending migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Your description"

# View migration history
alembic history

# Check current version
alembic current

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

## Database Access

```bash
# PostgreSQL shell
make db-shell
# or
docker exec -it paintingai_db psql -U paintingai -d paintingai

# Redis shell
make redis-shell
# or
docker exec -it paintingai_redis redis-cli
```

## Common SQL Queries

```sql
-- Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM rooms;

-- List recent projects
SELECT id, name, status, created_at 
FROM projects 
ORDER BY created_at DESC 
LIMIT 10;

-- User statistics
SELECT 
    u.email,
    COUNT(p.id) as project_count,
    SUM(p.bid_amount) as total_bids
FROM users u
LEFT JOIN projects p ON u.id = p.owner_id
GROUP BY u.email
ORDER BY project_count DESC;

-- Project statistics
SELECT 
    status,
    COUNT(*) as count,
    AVG(bid_amount) as avg_bid
FROM projects
GROUP BY status;

-- List tables
\dt

-- Describe table
\d projects

-- Exit
\q
```

## Backup & Restore

```bash
# Backup
make db-backup

# Restore (interactive)
make db-restore

# Manual backup
docker exec paintingai_db pg_dump -U paintingai paintingai > backup.sql

# Manual restore
cat backup.sql | docker exec -i paintingai_db psql -U paintingai -d paintingai
```

## Testing

```bash
# Run database tests
make db-test

# Run specific test
pytest backend/tests/test_database_migration.py::test_user_crud -v

# Run all tests
cd backend && pytest -v
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Migration Errors

```bash
# Check current version
alembic current

# Try running migrations again
alembic upgrade head

# If stuck, check migration history
alembic history

# Downgrade and retry
alembic downgrade -1
alembic upgrade head
```

### Reset Database (WARNING: Deletes all data)

```bash
make db-reset
```

### Connection Pool Exhausted

```python
# Check pool status
from database_service import db
print(db.get_pool_status())

# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20
```

## Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# Redis health
curl http://localhost:8000/health/redis

# PostgreSQL direct check
docker exec paintingai_db pg_isready -U paintingai

# Redis direct check
docker exec paintingai_redis redis-cli ping
```

## Environment Variables

Required in `.env`:

```bash
# Database
DATABASE_URL=postgresql://paintingai:YOUR_PASSWORD@localhost:5432/paintingai
POSTGRES_USER=paintingai
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_DB=paintingai

# Redis
REDIS_URL=redis://localhost:6379/0

# Connection Pool (optional, defaults shown)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Python Usage

```python
from database_service import db

# Create user
user = db.create_user(
    email="test@example.com",
    name="Test User"
)

# Get user
user = db.get_user(user_id)
user = db.get_user_by_email("test@example.com")
user = db.get_user_by_api_key(api_key)

# Create project
project = db.create_project(
    owner_id=user.id,
    name="Office Building",
    customer="ABC Corp"
)

# Get projects
projects = db.get_user_projects(user_id)

# Create room
room = db.create_room(
    project_id=project.id,
    name="Conference Room",
    length=20.0,
    width=15.0,
    height=9.0
)

# Update room
db.update_room(room.id, total_gallons=5.5)

# Delete project (cascades to rooms/drawings)
db.delete_project(project.id)
```

## Redis Usage

```python
import redis
import os

# Connect to Redis
r = redis.from_url(os.getenv("REDIS_URL"))

# Set value
r.set("key", "value")

# Get value
value = r.get("key")

# Set with expiry (1 hour)
r.setex("session:123", 3600, "session_data")

# Delete
r.delete("key")

# Use different database
r_sessions = redis.from_url(os.getenv("REDIS_URL").replace("/0", "/1"))
```

## Performance Tips

1. **Use eager loading for relationships:**
```python
# Bad (N+1 queries)
projects = db.get_user_projects(user_id)
for project in projects:
    print(len(project.rooms))  # Triggers new query

# Good (single query)
from sqlalchemy.orm import selectinload
with db.get_session() as session:
    projects = session.query(Project)\
        .options(selectinload(Project.rooms))\
        .filter(Project.owner_id == user_id)\
        .all()
```

2. **Use pagination for large datasets:**
```python
projects = db.get_user_projects(user_id, limit=20, offset=0)
```

3. **Add indexes for frequently queried fields:**
```sql
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);
```

## Need More Help?

- Full documentation: [DATABASE_SETUP.md](../DATABASE_SETUP.md)
- Backend docs: [README.md](README.md)
- Contact: cooperxxjohn@gmail.com

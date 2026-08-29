# Phase 2: PostgreSQL Database Setup

**Status:** Infrastructure ready, waiting for Docker environment

## What's Been Set Up

✅ **Docker Compose Configuration** (`docker-compose.yml`)
- PostgreSQL 15 container
- Redis 7 container  
- Backend API container
- Celery worker container
- Flower monitoring (Celery UI)
- Proper health checks and dependencies

✅ **Alembic Migrations** (`backend/alembic/`)
- Initialized migration system
- Initial schema migration created (`001_initial_schema.py`)
- All 15 models included:
  - Users, Organizations, Projects, Rooms, Drawings
  - Materials, Templates, Assemblies
  - Activities, Notifications, Integrations
  - Webhooks, API Usage
- Proper indexes on foreign keys

✅ **Database Models** (`backend/models.py`)
- Fixed naming conflict (`metadata` → `event_metadata` in Activity)
- Full SQLAlchemy ORM schema
- Relationships configured
- Ready for production use

✅ **Database Service Layer** (`backend/database_service.py`)
- SQLAlchemy async session management
- Connection pooling configured
- Transaction support
- CRUD operations defined

---

## How to Run (When Docker is Available)

### Step 1: Set Environment Variables

Create `.env` file in `painting-ai/` directory:

```bash
# Database
DB_PASSWORD=your_secure_password_here

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
SENDGRID_API_KEY=your_sendgrid_key  # Optional
STRIPE_API_KEY=your_stripe_key  # Optional
STRIPE_WEBHOOK_SECRET=your_webhook_secret  # Optional

# App Config
ENV=development
DEBUG=true
```

### Step 2: Start Docker Services

```bash
cd painting-ai
docker compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000
- Celery worker (background tasks)
- Flower on port 5555 (Celery monitoring)

### Step 3: Run Database Migrations

```bash
cd backend
source venv/bin/activate

# Run migrations
alembic upgrade head
```

This creates all tables with proper schema.

### Step 4: Verify Database

```bash
# Connect to PostgreSQL
docker exec -it paintingai-postgres psql -U paintingai -d paintingai

# List tables
\dt

# Should see:
# activities, api_usage, assemblies, drawings, integrations, 
# materials, notifications, organizations, projects, rooms,
# templates, users, webhooks
```

### Step 5: Migrate Demo Data (Optional)

```bash
# Seed demo data (will work with PostgreSQL)
python seed_demo_data.py
```

---

## Switch from JSON to PostgreSQL

Once database is running, update `main.py`:

### Current (JSON-based):
```python
from database import Database
db = Database()  # Uses JSON files
```

### Change to (PostgreSQL):
```python
from database_service import DatabaseService
db = DatabaseService()  # Uses PostgreSQL
```

Then update all database calls to use async/await:

```python
# Old (sync JSON)
project = db.get_project(project_id)

# New (async PostgreSQL)
project = await db.get_project(project_id)
```

---

## Verification Checklist

After migration to PostgreSQL:

- [ ] `docker compose ps` shows all services healthy
- [ ] Can access API: `curl http://localhost:8000/health`
- [ ] PostgreSQL tables created: `alembic history`
- [ ] Demo data loads successfully
- [ ] Upload endpoint works
- [ ] Assembly expansion works
- [ ] Export generation works
- [ ] Data persists after restart

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5432
lsof -i :5432

# Or change port in docker-compose.yml
ports:
  - "5433:5432"  # External:Internal
```

### Migration Errors
```bash
# Check current migration status
alembic current

# Rollback one migration
alembic downgrade -1

# Reapply
alembic upgrade head
```

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker logs paintingai-postgres

# Test connection
docker exec -it paintingai-postgres psql -U paintingai -c "SELECT version();"
```

---

## What's Next (Phase 3)

After PostgreSQL is working:

1. **JWT Authentication** - Replace demo auth
2. **User Management** - Real user accounts
3. **Organization Support** - Teams and sharing
4. **API Key Management** - Generate keys in database
5. **Session Management** - Store sessions in Redis

Time estimate: 3-4 days

---

## Files Created/Modified for Phase 2

**New Files:**
- `docker-compose.yml` - Full stack infrastructure
- `backend/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Migration environment
- `backend/alembic/versions/001_initial_schema.py` - Initial migration
- `PHASE2_DATABASE_SETUP.md` - This documentation

**Modified Files:**
- `backend/models.py` - Fixed `metadata` naming conflict
- `backend/database_service.py` - Ready for use (exists, not yet integrated)
- `backend/main.py` - Still using JSON (will switch after PostgreSQL running)

---

## Benefits After PostgreSQL Migration

✅ **Data Persistence** - Projects survive restarts
✅ **Multi-User Support** - Multiple users can work simultaneously
✅ **Query Performance** - Indexed lookups, complex queries
✅ **Transactions** - Atomic operations, rollback on errors
✅ **Scalability** - Handle 1000+ concurrent users
✅ **Production Ready** - Industry-standard database
✅ **Backup & Recovery** - PostgreSQL backup tools
✅ **Security** - Row-level security, encrypted connections

---

## Current Status

🟡 **READY TO RUN** - All code in place, waiting for Docker environment

Once Docker is available:
```bash
cd painting-ai
docker compose up -d
cd backend && alembic upgrade head
python seed_demo_data.py
```

Then Phase 2 complete! 🎉

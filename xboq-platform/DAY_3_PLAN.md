# Day 3 Plan: Database & Backend Infrastructure

**Date**: May 23, 2026  
**Goal**: Replace JSON/mock data with PostgreSQL, add persistence  
**Hours**: 10 (10 hrs/day target)  

---

## 🎯 Day 3 Objectives

### Primary Goals
1. Set up PostgreSQL database
2. Design and implement database schema
3. Create SQLAlchemy models
4. Implement database service layer
5. Migrate from mock data to real persistence
6. Set up Alembic migrations
7. Test data persistence

### Success Criteria
- ✅ PostgreSQL running locally (Docker)
- ✅ All database tables created
- ✅ CRUD operations working
- ✅ API endpoints persist data
- ✅ Data survives server restart
- ✅ Migration system in place

---

## 📋 Hour-by-Hour Plan

### Hours 1-2: Database Setup & Schema Design (2 hrs)

**Hour 1: PostgreSQL + Docker Setup**
- [ ] Create docker-compose.yml with PostgreSQL
- [ ] Add pgAdmin (optional)
- [ ] Update requirements.txt (psycopg2, SQLAlchemy)
- [ ] Test database connection
- [ ] Create .env variables for DB connection

**Hour 2: Schema Design**
- [ ] Design User model (id, email, name, created_at)
- [ ] Design Project model (id, user_id, type, name, created_at)
- [ ] Design BOQ model (id, project_id, data JSON)
- [ ] Design Estimate model (id, project_id, trade, data JSON)
- [ ] Design relationships
- [ ] Document schema in diagram

**Deliverables**:
- docker-compose.yml running
- Schema documented
- Database accessible

---

### Hours 3-4: SQLAlchemy Models & Database Service (2 hrs)

**Hour 3: Create Models**
- [ ] backend/models.py with all models
- [ ] Define User model
- [ ] Define Project model
- [ ] Define BOQ model
- [ ] Define Estimate model
- [ ] Add timestamps, relationships
- [ ] Add helper methods

**Hour 4: Database Service Layer**
- [ ] backend/database.py with DatabaseService class
- [ ] Connection pooling
- [ ] Session management
- [ ] CRUD methods for each model
- [ ] Error handling
- [ ] Transaction support

**Deliverables**:
- models.py complete
- database.py with CRUD operations
- Connection tested

---

### Hours 5-6: Alembic Migrations & Integration (2 hrs)

**Hour 5: Alembic Setup**
- [ ] Install Alembic
- [ ] Initialize Alembic
- [ ] Create initial migration
- [ ] Test migration up/down
- [ ] Document migration commands

**Hour 6: Integrate Database into API**
- [ ] Update app.py to use DatabaseService
- [ ] Update /api/boq/upload to save to DB
- [ ] Update /api/estimate/manual to save to DB
- [ ] Update /api/estimate/upload to save to DB
- [ ] Add GET endpoints for retrieving data
- [ ] Test persistence

**Deliverables**:
- Migrations working
- API saves to database
- Data persists across restarts

---

### Hours 7-8: User Management & Projects API (2 hrs)

**Hour 7: User CRUD**
- [ ] POST /api/users/register (basic, no auth yet)
- [ ] GET /api/users/me (placeholder)
- [ ] Store users in database
- [ ] Associate projects with users

**Hour 8: Projects API**
- [ ] GET /api/projects (list user's projects)
- [ ] GET /api/projects/:id (get single project)
- [ ] PUT /api/projects/:id (update project)
- [ ] DELETE /api/projects/:id (soft delete)
- [ ] Test all CRUD operations

**Deliverables**:
- User management basic API
- Projects API complete
- Full CRUD working

---

### Hours 9-10: Testing, Seed Data & Documentation (2 hrs)

**Hour 9: Database Testing**
- [ ] Create test_database.py
- [ ] Test all CRUD operations
- [ ] Test relationships
- [ ] Test data persistence
- [ ] Test error handling
- [ ] Performance check (query times)

**Hour 10: Seed Data & Documentation**
- [ ] Create seed_data.py with sample users/projects
- [ ] Update README with database setup
- [ ] Update DEPLOYMENT.md with PostgreSQL steps
- [ ] Create DATABASE.md documentation
- [ ] Update automated tests
- [ ] Day 3 completion summary

**Deliverables**:
- Test suite for database
- Seed data script
- Documentation updated
- Day 3 complete

---

## 🗄️ Database Schema Design

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),  -- Future: JWT auth
    api_key VARCHAR(255) UNIQUE,  -- Future: API access
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Projects Table
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) NOT NULL,  -- 'boq' or 'estimate'
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, complete, error
    file_url TEXT,  -- Path to uploaded file
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### BOQs Table
```sql
CREATE TABLE boqs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    project_name VARCHAR(255),
    sections JSONB NOT NULL,  -- Store full BOQ data as JSON
    total_items INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Estimates Table
```sql
CREATE TABLE estimates (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    trade VARCHAR(50) NOT NULL,  -- 'drywall', 'painting', etc.
    rooms JSONB NOT NULL,  -- Store rooms array as JSON
    summary JSONB NOT NULL,  -- Store summary as JSON
    total_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📦 Technology Stack (Day 3 Additions)

### Database
- **PostgreSQL 15** - Main database
- **SQLAlchemy 2.0** - ORM
- **psycopg2-binary** - PostgreSQL driver
- **Alembic** - Database migrations

### Development
- **Docker Compose** - Local database
- **pgAdmin** (optional) - Database management UI

---

## 🔧 Configuration

### Environment Variables (backend/.env)
```bash
# Database
DATABASE_URL=postgresql://xboq_user:xboq_pass@localhost:5432/xboq_db

# Existing
ANTHROPIC_API_KEY=...
TEST_MODE=true
FLASK_ENV=development
```

### Docker Compose (docker-compose.yml)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: xboq_postgres
    environment:
      POSTGRES_USER: xboq_user
      POSTGRES_PASSWORD: xboq_pass
      POSTGRES_DB: xboq_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  pgadmin:  # Optional
    image: dpage/pgadmin4
    container_name: xboq_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@xboq.ai
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

---

## 🧪 Testing Strategy

### Database Tests
1. **Connection Test**: Verify DB connects
2. **Model Tests**: Create, read, update, delete
3. **Relationship Tests**: User → Projects → BOQs/Estimates
4. **Transaction Tests**: Rollback on error
5. **Migration Tests**: Up/down migrations work
6. **Performance Tests**: Query response times

### API Tests
1. **Persistence Test**: POST → restart → GET (data exists)
2. **User Flow**: Register → Create project → View projects
3. **BOQ Flow**: Upload → Save → Retrieve
4. **Estimate Flow**: Generate → Save → Retrieve
5. **Error Handling**: Invalid data, missing fields

---

## 📊 Success Metrics

### Functional
- [ ] Database running and accessible
- [ ] All tables created via migrations
- [ ] API endpoints persist data
- [ ] Data survives server restart
- [ ] Queries return correct data

### Performance
- [ ] Database queries < 100ms
- [ ] API response times < 500ms (with DB)
- [ ] Handles 100+ concurrent requests
- [ ] No memory leaks

### Quality
- [ ] All database tests passing
- [ ] API tests updated and passing
- [ ] Code reviewed and clean
- [ ] Documentation complete

---

## 🚨 Potential Challenges

### Challenge 1: PostgreSQL Installation
**Risk**: Local PostgreSQL setup issues
**Mitigation**: Use Docker Compose (isolated, reproducible)

### Challenge 2: SQLAlchemy Learning Curve
**Risk**: Complex ORM queries
**Mitigation**: Start simple, use documentation, async patterns

### Challenge 3: Migration Conflicts
**Risk**: Database schema changes break existing data
**Mitigation**: Test migrations thoroughly, keep backups

### Challenge 4: Data Modeling
**Risk**: Schema doesn't support future features
**Mitigation**: Use JSONB for flexibility, plan for extensions

---

## 🔄 Migration from Mock to Real Data

### Current State (Test Mode)
```python
# Returns hardcoded mock data
def generate_estimate():
    return {
        "status": "success",
        "estimate": {...}  # Mock data
    }
```

### Target State (Database)
```python
# Saves to database, returns real data
def generate_estimate():
    result = estimator.generate(data)
    
    # Save to database
    project = Project(user_id=user_id, type='estimate')
    estimate = Estimate(project_id=project.id, data=result)
    db.save(project)
    db.save(estimate)
    
    return result
```

---

## 📝 Documentation Deliverables

### New Files
- [ ] docker-compose.yml
- [ ] backend/models.py
- [ ] backend/database.py
- [ ] backend/alembic.ini
- [ ] backend/alembic/env.py
- [ ] backend/alembic/versions/001_initial_schema.py
- [ ] backend/seed_data.py
- [ ] backend/test_database.py
- [ ] DATABASE.md

### Updated Files
- [ ] README.md (database setup section)
- [ ] DEPLOYMENT.md (PostgreSQL deployment)
- [ ] backend/requirements.txt (new dependencies)
- [ ] backend/app.py (database integration)

---

## 🎯 End of Day 3 Target

### What Should Work
1. ✅ Start app with `docker-compose up && python app.py`
2. ✅ Upload BOQ → Saves to database → Retrieve via GET
3. ✅ Generate estimate → Saves to database → Retrieve via GET
4. ✅ Restart server → Data still exists
5. ✅ Run `python seed_data.py` → Database populated
6. ✅ Run `pytest test_database.py` → All tests pass

### What's Ready for Day 4
- Database fully functional
- Basic user management
- Projects API complete
- Ready for JWT authentication (Day 4)
- Ready for Stripe integration (Day 5-6)

---

**Day 3 Start Time**: Now  
**Expected Completion**: 10 hours  
**Difficulty**: Medium (Docker + SQLAlchemy setup)  
**Priority**: HIGH (Foundation for all future features)

Let's build! 🚀

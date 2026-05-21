.PHONY: help install dev test deploy clean demo db-setup db-migrate db-reset db-backup db-restore

help:
	@echo "Painting.ai - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install all dependencies"
	@echo "  make db-setup      Setup PostgreSQL + Redis"
	@echo "  make db-migrate    Run database migrations"
	@echo ""
	@echo "Development:"
	@echo "  make dev           Run development servers"
	@echo "  make test          Run test suite"
	@echo "  make demo          Load demo data"
	@echo ""
	@echo "Database:"
	@echo "  make db-reset      Reset database (WARNING: deletes data)"
	@echo "  make db-backup     Backup database"
	@echo "  make db-restore    Restore database from backup"
	@echo "  make db-shell      Connect to PostgreSQL"
	@echo "  make redis-shell   Connect to Redis"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     Start all containers"
	@echo "  make docker-down   Stop all containers"
	@echo "  make docker-logs   View container logs"
	@echo ""
	@echo "Other:"
	@echo "  make deploy        Deploy to production"
	@echo "  make clean         Clean up temp files"
	@echo ""

install:
	@echo "📦 Installing dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "✓ Dependencies installed"

dev:
	@echo "🚀 Starting development servers..."
	@./run.sh

test:
	@echo "🧪 Running tests..."
	cd backend && . venv/bin/activate && pytest -v

demo:
	@echo "🎨 Loading demo data..."
	cd backend && . venv/bin/activate && python demo_data.py

deploy:
	@echo "🚀 Deploying to production..."
	docker-compose build
	docker-compose up -d
	@echo "✓ Deployed successfully"

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/uploads/* backend/outputs/* 2>/dev/null || true
	@echo "✓ Cleaned"

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

check:
	@echo "✓ Checking setup..."
	@command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found"; exit 1; }
	@test -f .env || { echo "⚠️  .env file not found (copy from .env.example)"; }
	@echo "✓ All checks passed"

# Database commands
db-setup:
	@echo "🗄️  Setting up databases..."
	docker-compose up -d postgres redis
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@sleep 5
	cd backend && ./scripts/run_migrations.sh
	@echo "✓ Database setup complete"

db-migrate:
	@echo "🔄 Running database migrations..."
	cd backend && alembic upgrade head
	@echo "✓ Migrations complete"

db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "\n🗑️  Resetting database..."; \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		cd backend && alembic upgrade head; \
		echo "✓ Database reset complete"; \
	else \
		echo "\n❌ Cancelled"; \
	fi

db-backup:
	@echo "💾 Backing up database..."
	@mkdir -p backups
	docker exec paintingai_db pg_dump -U paintingai paintingai | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "✓ Backup saved to backups/"

db-restore:
	@echo "📥 Restoring database..."
	@echo "Available backups:"
	@ls -lt backups/*.sql.gz | head -5
	@read -p "Enter backup filename: " backup; \
	gunzip -c backups/$$backup | docker exec -i paintingai_db psql -U paintingai -d paintingai
	@echo "✓ Database restored"

db-shell:
	@echo "🐘 Connecting to PostgreSQL..."
	docker exec -it paintingai_db psql -U paintingai -d paintingai

redis-shell:
	@echo "🔴 Connecting to Redis..."
	docker exec -it paintingai_redis redis-cli

db-status:
	@echo "📊 Database Status:"
	@echo ""
	@echo "PostgreSQL:"
	@docker exec paintingai_db psql -U paintingai -d paintingai -c "SELECT COUNT(*) as users FROM users;" 2>/dev/null || echo "  Not running"
	@docker exec paintingai_db psql -U paintingai -d paintingai -c "SELECT COUNT(*) as projects FROM projects;" 2>/dev/null || echo ""
	@docker exec paintingai_db psql -U paintingai -d paintingai -c "SELECT COUNT(*) as rooms FROM rooms;" 2>/dev/null || echo ""
	@echo ""
	@echo "Redis:"
	@docker exec paintingai_redis redis-cli DBSIZE 2>/dev/null || echo "  Not running"

db-test:
	@echo "🧪 Testing database connection..."
	cd backend && pytest tests/test_database_migration.py -v

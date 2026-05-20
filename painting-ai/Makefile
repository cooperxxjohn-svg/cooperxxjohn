.PHONY: help install dev test deploy clean demo

help:
	@echo "Painting.ai - Development Commands"
	@echo ""
	@echo "  make install    Install all dependencies"
	@echo "  make dev        Run development servers"
	@echo "  make test       Run test suite"
	@echo "  make demo       Load demo data"
	@echo "  make deploy     Deploy to production"
	@echo "  make clean      Clean up temp files"
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

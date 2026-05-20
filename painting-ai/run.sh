#!/bin/bash

# Painting.ai Startup Script

echo "🎨 Starting Painting.ai..."

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable not set"
    echo "Please run: export ANTHROPIC_API_KEY='your-api-key'"
    exit 1
fi

# Start backend
echo "📦 Starting backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

python main.py &
BACKEND_PID=$!

# Start frontend
echo "🎨 Starting frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Painting.ai is running!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

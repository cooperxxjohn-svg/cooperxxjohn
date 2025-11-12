#!/bin/bash
# Quick start script for BOQ Web Application

set -e

echo "🚀 Starting BOQ Web Application..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file. Please edit it and add your ANTHROPIC_API_KEY"
        exit 1
    else
        echo "❌ .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r web_requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs logs

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "❌ ANTHROPIC_API_KEY not set in .env file"
    echo "   Please edit .env and add your Anthropic API key"
    exit 1
fi

echo "✓ Configuration verified"
echo ""
echo "🌐 Starting web server..."
echo "   Access the application at: http://localhost:${PORT:-5000}"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the application
if [ "$FLASK_DEBUG" = "True" ] || [ "$FLASK_DEBUG" = "true" ]; then
    # Development mode
    python web_app.py
else
    # Production mode with Gunicorn
    gunicorn --config gunicorn_config.py web_app:app
fi

#!/bin/bash

# Energy Storage Investment Decision API - Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/energy-storage-api"

echo "🔋 Energy Storage Investment Decision API"
echo "========================================="
echo ""

# Check if directory exists
if [ ! -d "$API_DIR" ]; then
    echo "❌ Error: API directory not found: $API_DIR"
    exit 1
fi

cd "$API_DIR"

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
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Start server
echo ""
echo "🚀 Starting FastAPI server..."
echo "📍 API will be available at: http://127.0.0.1:8000"
echo "📖 Interactive docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

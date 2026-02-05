#!/bin/bash

# Agentic Honey-Pot Quick Start Script

echo "🚀 Starting Agentic Honey-Pot API..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  IMPORTANT: Edit .env and set your API_KEY before starting!"
    echo ""
    exit 1
fi

# Check if API_KEY is set
if ! grep -q "API_KEY=your_secret_api_key_here" .env; then
    echo "✅ API_KEY appears to be configured"
else
    echo "⚠️  WARNING: API_KEY still has default value in .env"
    echo "   Please edit .env and set a secure API_KEY"
    echo ""
fi

# Install dependencies if needed
if ! command -v uvicorn &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo "🌐 Starting server on http://localhost:10000"
echo "📖 API docs available at http://localhost:10000/docs"
echo "💚 Health check: http://localhost:10000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py

#!/bin/bash

# Letta Knowledge Management & Personal Assistant
# Startup Script

set -e

echo "🧠 Starting Letta Knowledge Management & Personal Assistant..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
    echo "   Required: OPENAI_API_KEY or other LLM provider API key"
    echo "   Optional: ANTHROPIC_API_KEY, GEMINI_API_KEY"
    echo ""
    echo "After editing .env, run this script again."
    exit 1
fi

# Load environment variables
source .env

# Check for required API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: At least one LLM API key is required"
    echo "   Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker and try again"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads data logs static

# Start services
echo "🚀 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Web Interface: http://localhost:5000"
    echo "🤖 Letta Server: http://localhost:8283"
    echo "📊 Agent Development Environment: https://app.letta.com"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Open http://localhost:5000 in your browser"
    echo "   2. Upload some documents or create notes"
    echo "   3. Start chatting with your assistant"
    echo ""
    echo "🔧 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Reset data: docker-compose down -v"
    echo ""
else
    echo "❌ Error: Services failed to start"
    echo "   Check logs with: docker-compose logs"
    exit 1
fi
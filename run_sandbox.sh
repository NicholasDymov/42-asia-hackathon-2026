#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "⚡ 42 Asia Hackathon 2026 Tokyo — WorkPulse AI Agent"
echo "=========================================================="

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "ℹ️  Created .env from .env.example"
    fi
fi

# Stop any previous instance
docker stop workpulse_sandbox 2>/dev/null || true

echo "🔨 Building sandboxed Docker image..."
docker build -t mistral-hackathon-agent .

echo "📦 Running in isolated sandbox container (port 8501)..."
docker run -d --rm \
    --name workpulse_sandbox \
    -p 8501:8501 \
    --env-file .env \
    mistral-hackathon-agent

echo ""
echo "✅ Sandboxed container is running!"
echo "🌐 Open dashboard at: http://localhost:8501"
echo "📋 View live logs with: docker logs -f workpulse_sandbox"
echo "🛑 Stop container with: docker stop workpulse_sandbox"

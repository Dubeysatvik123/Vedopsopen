#!/bin/bash

# VedOps Start Script
echo "🚀 Starting VedOps DevSecOps Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check VedOps
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ VedOps UI is ready"
else
    echo "⚠️ VedOps UI is starting up..."
fi

# Check Prometheus
if curl -f http://localhost:9090/-/ready > /dev/null 2>&1; then
    echo "✅ Prometheus is ready"
else
    echo "⚠️ Prometheus is starting up..."
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is ready"
else
    echo "⚠️ Grafana is starting up..."
fi

echo ""
echo "🎉 VedOps is starting up!"
echo ""
echo "🌐 Access points:"
echo "   - VedOps UI: http://localhost:8501"
echo "   - Grafana: http://localhost:3000"
echo "   - Prometheus: http://localhost:9090"
echo "   - Jaeger: http://localhost:16686"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"

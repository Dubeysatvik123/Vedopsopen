#!/bin/bash

# VedOps Setup Script
echo "🚀 Setting up VedOps DevSecOps Platform..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create directories
echo "📁 Creating project directories..."
mkdir -p projects reports artifacts monitoring/dashboards monitoring/grafana/dashboards monitoring/grafana/datasources

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Setup monitoring configuration
echo "⚙️ Setting up monitoring configuration..."
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'vedops'
    static_configs:
      - targets: ['localhost:8501']
  
  - job_name: 'application'
    static_configs:
      - targets: ['localhost:8080']
EOF

# Setup Grafana datasource
cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Make scripts executable
chmod +x scripts/*.sh
chmod +x run.py

echo "✅ VedOps setup completed successfully!"
echo ""
echo "🚀 To start VedOps:"
echo "   docker-compose up -d"
echo ""
echo "🌐 Access points:"
echo "   - VedOps UI: http://localhost:8501"
echo "   - Grafana: http://localhost:3000 (admin/vedops123)"
echo "   - Prometheus: http://localhost:9090"
echo "   - Jaeger: http://localhost:16686"

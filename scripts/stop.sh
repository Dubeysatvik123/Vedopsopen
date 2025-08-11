#!/bin/bash

# VedOps Stop Script
echo "🛑 Stopping VedOps DevSecOps Platform..."

# Stop Docker services
docker-compose down

echo "✅ VedOps stopped successfully"

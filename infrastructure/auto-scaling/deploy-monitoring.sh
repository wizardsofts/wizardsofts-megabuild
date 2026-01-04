#!/bin/bash

# Monitoring Stack Deployment Script for Server 84
# This script deploys Prometheus, Alertmanager, Grafana, Loki, and Promtail

set -e

echo "========================================"
echo "Monitoring Stack Deployment - Server 84"
echo "========================================"
echo ""

# Check if running on correct server
CURRENT_IP=$(hostname -I | awk '{print $1}')
if [[ "$CURRENT_IP" != "10.0.0.84" ]]; then
    echo "⚠️  Warning: This script is designed for Server 84 (10.0.0.84)"
    echo "   Current IP: $CURRENT_IP"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to deployment directory
cd "$(dirname "$0")"
DEPLOY_DIR=$(pwd)
echo "📂 Deployment directory: $DEPLOY_DIR"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file from .env.alertmanager.example"
    echo ""
    echo "   cp .env.alertmanager.example .env"
    echo "   nano .env  # Update with actual credentials"
    echo ""
    exit 1
fi

# Source environment variables
source .env

# Validate required environment variables
MISSING_VARS=()
[[ -z "$GF_SECURITY_ADMIN_PASSWORD" ]] && MISSING_VARS+=("GF_SECURITY_ADMIN_PASSWORD")
[[ -z "$SMTP_PASSWORD" ]] && MISSING_VARS+=("SMTP_PASSWORD")
[[ -z "$APPWRITE_API_KEY" ]] && MISSING_VARS+=("APPWRITE_API_KEY")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "   Please update .env file with actual values"
    exit 1
fi

echo "✅ Environment variables validated"
echo ""

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Validate configuration files
echo "🔍 Validating configuration files..."

# Validate Prometheus config
if docker run --rm -v "$DEPLOY_DIR/monitoring/prometheus:/prometheus" \
    prom/prometheus:latest \
    promtool check config /prometheus/prometheus.yml > /dev/null 2>&1; then
    echo "  ✅ Prometheus configuration valid"
else
    echo "  ❌ Prometheus configuration invalid"
    exit 1
fi

# Validate alert rules
if docker run --rm -v "$DEPLOY_DIR/monitoring/prometheus:/prometheus" \
    prom/prometheus:latest \
    promtool check rules /prometheus/infrastructure-alerts.yml > /dev/null 2>&1; then
    echo "  ✅ Infrastructure alert rules valid"
else
    echo "  ❌ Infrastructure alert rules invalid"
    exit 1
fi

if docker run --rm -v "$DEPLOY_DIR/monitoring/prometheus:/prometheus" \
    prom/prometheus:latest \
    promtool check rules /prometheus/security-alerts.yml > /dev/null 2>&1; then
    echo "  ✅ Security alert rules valid"
else
    echo "  ❌ Security alert rules invalid"
    exit 1
fi

# Validate Alertmanager config
if docker run --rm -v "$DEPLOY_DIR/monitoring/alertmanager:/alertmanager" \
    prom/alertmanager:latest \
    amtool check-config /alertmanager/alertmanager.yml > /dev/null 2>&1; then
    echo "  ✅ Alertmanager configuration valid"
else
    echo "  ❌ Alertmanager configuration invalid"
    exit 1
fi

echo ""

# Stop existing containers (if any)
echo "🛑 Stopping existing monitoring containers..."
docker-compose down 2>/dev/null || true
echo ""

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose pull prometheus alertmanager grafana loki promtail
echo ""

# Start services
echo "🚀 Starting monitoring services..."
docker-compose up -d prometheus alertmanager grafana loki promtail

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

check_service() {
    local service=$1
    local port=$2
    local endpoint=$3
    
    if curl -sf "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo "  ✅ $service is healthy"
        return 0
    else
        echo "  ❌ $service is not responding"
        return 1
    fi
}

FAILED=0

check_service "Prometheus" "9090" "/-/healthy" || FAILED=1
check_service "Alertmanager" "9093" "/-/healthy" || FAILED=1
check_service "Grafana" "3002" "/api/health" || FAILED=1
check_service "Loki" "3100" "/ready" || FAILED=1

echo ""

if [ $FAILED -eq 0 ]; then
    echo "========================================" 
    echo "✅ Deployment Successful!"
    echo "========================================"
    echo ""
    echo "Access URLs:"
    echo "  - Prometheus:    http://10.0.0.84:9090"
    echo "  - Alertmanager:  http://10.0.0.84:9093"
    echo "  - Grafana:       http://10.0.0.84:3002"
    echo "    Username: admin"
    echo "    Password: (from GF_SECURITY_ADMIN_PASSWORD)"
    echo "  - Loki:          http://10.0.0.84:3100"
    echo ""
    echo "Next Steps:"
    echo "  1. Access Grafana and verify dashboards are loaded"
    echo "  2. Check Prometheus targets: http://10.0.0.84:9090/targets"
    echo "  3. Verify alerts are configured: http://10.0.0.84:9090/alerts"
    echo "  4. Test Alertmanager routing: http://10.0.0.84:9093"
    echo "  5. Deploy Appwrite alert-processor function"
    echo ""
    echo "View logs:"
    echo "  docker-compose logs -f prometheus"
    echo "  docker-compose logs -f alertmanager"
    echo "  docker-compose logs -f grafana"
    echo ""
else
    echo "========================================"
    echo "⚠️  Deployment completed with errors"
    echo "========================================"
    echo ""
    echo "Some services failed health checks."
    echo "Check logs for details:"
    echo "  docker-compose logs prometheus"
    echo "  docker-compose logs alertmanager"
    echo "  docker-compose logs grafana"
    echo "  docker-compose logs loki"
    echo ""
    exit 1
fi

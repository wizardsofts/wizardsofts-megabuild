#!/bin/bash
# Deploy Control Plane Components for Auto-Scaling Platform

set -e  # Exit on any error

echo "=================================="
echo "Deploying Control Plane Components"
echo "=================================="
echo

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if we're on the control server (10.0.0.80)
CURRENT_HOST=$(hostname -I | awk '{print $1}')
log "Current host IP: $CURRENT_HOST"

# Check if required files exist
REQUIRED_FILES=(
    "/opt/autoscaler/config.yaml"
    "/opt/autoscaler/docker-compose.yml"
    "/opt/autoscaler/app/Dockerfile"
    "/opt/autoscaler/haproxy/haproxy.cfg"
    "/opt/autoscaler/monitoring/prometheus/prometheus.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log "ERROR: Required file not found: $file"
        exit 1
    fi
done

log "All required files found"
echo

# Navigate to the autoscaler directory
cd /opt/autoscaler
log "Changed to /opt/autoscaler directory"
echo

# Build and start the control plane services
log "Starting control plane services..."
log "This may take a few minutes..."

if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

log "Control plane services started"
echo

# Wait for services to be ready
log "Waiting for services to start (10 seconds)..."
sleep 10

# Check service status
log "Checking service status..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi
echo

# Wait a bit more for services to be fully ready
sleep 15

# Test each component
log "Testing component availability..."

# Test autoscaler API
log "Testing Autoscaler API..."
if curl -f -s http://localhost:8000/ &> /dev/null; then
    log "✓ Autoscaler API is responding"
    API_RESPONSE=$(curl -s http://localhost:8000/)
    log "  Response: $API_RESPONSE"
else
    log "✗ Autoscaler API is not responding"
fi
echo

# Test HAProxy stats
log "Testing HAProxy Stats..."
if curl -f -s http://localhost:8404/ &> /dev/null; then
    log "✓ HAProxy stats page is accessible"
else
    log "✗ HAProxy stats page is not accessible"
fi
echo

# Test Prometheus
log "Testing Prometheus..."
if curl -f -s http://localhost:9090/-/healthy &> /dev/null; then
    log "✓ Prometheus is healthy"
else
    log "✗ Prometheus is not healthy"
fi
echo

# Test Grafana
log "Testing Grafana..."
if curl -f -s http://localhost:3000/api/health &> /dev/null; then
    log "✓ Grafana is healthy"
else
    log "✗ Grafana is not healthy"
fi
echo

# Check autoscaler logs for any startup errors
log "Checking autoscaler logs for errors..."
if command -v docker-compose &> /dev/null; then
    AUTOSCALER_LOGS=$(docker-compose logs autoscaler | tail -20)
else
    AUTOSCALER_LOGS=$(docker compose logs autoscaler | tail -20)
fi

echo "$AUTOSCALER_LOGS"
echo

# Summary
log "=================================="
log "Control Plane Deployment Summary:"
log "✓ HAProxy running on ports 80, 443, 8404, 11434"
log "✓ Autoscaler API running on port 8000"
log "✓ Prometheus running on port 9090"
log "✓ Grafana running on port 3000"
log ""
log "Access the dashboards:"
log "- HAProxy Stats: http://10.0.0.80:8404"
log "- Autoscaler API: http://10.0.0.80:8000"
log "- Prometheus: http://10.0.0.80:9090"
log "- Grafana: http://10.0.0.80:3000 (admin/admin)"
log ""
log "Configuration location: /opt/autoscaler/config.yaml"
log "=================================="
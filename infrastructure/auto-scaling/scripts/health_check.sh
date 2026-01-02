#!/bin/bash
# Health check script for Auto-Scaling Platform

echo "=== Auto-Scaling Platform Health Check ==="
echo "Date: $(date)"
echo

# Check if Docker is running
echo "1. Checking Docker status..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "   ✓ Docker is running"
    else
        echo "   ✗ Docker is not accessible"
    fi
else
    echo "   ✗ Docker is not installed"
fi
echo

# Check if docker-compose is available
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "   ✓ Docker Compose is available"
else
    echo "   ⚠ Docker Compose is not available (may use 'docker compose' instead)"
fi
echo

# Check control plane services
echo "3. Checking control plane services..."
if [ -f "/opt/autoscaler/docker-compose.yml" ]; then
    cd /opt/autoscaler
    if docker-compose ps &> /dev/null; then
        docker-compose ps
    else
        echo "   ✗ Could not check service status"
    fi
else
    echo "   ✗ Docker Compose file not found at /opt/autoscaler/docker-compose.yml"
fi
echo

# Check autoscaler API
echo "4. Checking autoscaler API..."
if curl -f -s http://localhost:8000/ &> /dev/null; then
    echo "   ✓ Autoscaler API is responding"
    API_STATUS=$(curl -s http://localhost:8000/ | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "   Status: $API_STATUS"
else
    echo "   ✗ Autoscaler API is not responding"
fi
echo

# Check HAProxy stats
echo "5. Checking HAProxy..."
if curl -f -s http://localhost:8404/ &> /dev/null; then
    echo "   ✓ HAProxy stats page is accessible"
else
    echo "   ✗ HAProxy stats page is not accessible"
fi
echo

# Check Prometheus
echo "6. Checking Prometheus..."
if curl -f -s http://localhost:9090/-/healthy &> /dev/null; then
    echo "   ✓ Prometheus is healthy"
else
    echo "   ✗ Prometheus is not healthy"
fi
echo

# Check Grafana
echo "7. Checking Grafana..."
if curl -f -s http://localhost:3000/api/health &> /dev/null; then
    echo "   ✓ Grafana is healthy"
else
    echo "   ✗ Grafana is not healthy"
fi
echo

# Check cAdvisor on each server
echo "8. Checking cAdvisor on servers..."
for server in "10.0.0.80" "10.0.0.81" "10.0.0.82" "10.0.0.84"; do
    if curl -f -s http://$server:8080/metrics &> /dev/null; then
        echo "   ✓ cAdvisor on $server is accessible"
    else
        echo "   ✗ cAdvisor on $server is not accessible"
    fi
done
echo

# Check disk space
echo "9. Checking disk space..."
df -h /opt/autoscaler /data
echo

echo "Health check complete!"
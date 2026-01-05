#!/bin/bash
# Remove HAProxy and Custom Autoscaler Infrastructure
# Run on Server 84: ssh wizardsofts@10.0.0.84

set -e

echo "=== Removing HAProxy and Custom Autoscaler ==="

# Step 1: Stop and remove HAProxy
echo "[1/4] Removing HAProxy..."
if docker ps -a | grep -q haproxy; then
    echo "  Stopping HAProxy container..."
    docker stop haproxy 2>/dev/null || true

    echo "  Removing HAProxy container..."
    docker rm haproxy 2>/dev/null || true

    echo "✅ HAProxy removed"
else
    echo "  HAProxy container not found (already removed)"
fi

# Step 2: Stop and remove Autoscaler
echo "[2/4] Removing Custom Autoscaler..."
if docker ps -a | grep -q autoscaler; then
    echo "  Stopping Autoscaler container..."
    docker stop autoscaler 2>/dev/null || true

    echo "  Removing Autoscaler container..."
    docker rm autoscaler 2>/dev/null || true

    echo "✅ Autoscaler removed"
else
    echo "  Autoscaler container not found (already removed)"
fi

# Step 3: Remove unused volumes
echo "[3/4] Cleaning up unused volumes..."
docker volume prune -f

# Step 4: Check disk and memory freed
echo "[4/4] Checking freed resources..."

echo ""
echo "Disk space:"
df -h / | tail -1

echo ""
echo "Memory usage:"
free -h | grep -E 'Mem:|Swap:'

echo ""
echo "Docker system info:"
docker system df

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Removed components:"
echo "  - ❌ HAProxy (port 8404)"
echo "  - ❌ Custom Autoscaler (Python FastAPI)"
echo ""
echo "Remaining components:"
echo "  - ✅ Traefik (reverse proxy + load balancer)"
echo "  - ✅ Docker Swarm (orchestration + auto-discovery)"
echo ""
echo "To verify:"
echo "  docker ps | grep -E 'haproxy|autoscaler'"
echo "  (should return nothing)"
echo ""

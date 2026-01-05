#!/bin/bash
# Deploy multiple Ray workers on a server with resource limits
# Usage: ./deploy-multi-workers.sh <server_ip> <num_workers> <cpus_per_worker> <memory_per_worker>

set -euo pipefail

SERVER_IP=${1:-}
NUM_WORKERS=${2:-2}
CPUS_PER_WORKER=${3:-2}
MEMORY_PER_WORKER=${4:-6G}
HEAD_ADDRESS=${5:-10.0.0.84:6379}

if [ -z "$SERVER_IP" ]; then
    echo "Usage: $0 <server_ip> [num_workers] [cpus_per_worker] [memory_per_worker] [head_address]"
    echo "Example: $0 10.0.0.80 4 2 6G 10.0.0.84:6379"
    exit 1
fi

echo "🚀 Deploying $NUM_WORKERS Ray workers on $SERVER_IP"
echo "   CPUs per worker: $CPUS_PER_WORKER"
echo "   Memory per worker: $MEMORY_PER_WORKER"
echo "   Head address: $HEAD_ADDRESS"

# Create deployment directory
ssh wizardsofts@$SERVER_IP "mkdir -p ~/ray-workers"

# Copy lightweight Dockerfile
scp "$(dirname "$0")/../ray/Dockerfile.ray-worker-light" wizardsofts@$SERVER_IP:~/ray-workers/Dockerfile.ray-worker

# Generate docker-compose with N workers
ssh wizardsofts@$SERVER_IP "cat > ~/ray-workers/docker-compose.yml << 'EOF'
version: '3.8'

services:
EOF"

# Add worker services
for i in $(seq 1 $NUM_WORKERS); do
    ssh wizardsofts@$SERVER_IP "cat >> ~/ray-workers/docker-compose.yml << EOF
  ray-worker-$i:
    build:
      context: .
      dockerfile: Dockerfile.ray-worker
    container_name: ray-worker-$i
    hostname: ray-worker-$i
    environment:
      - RAY_HEAD_ADDRESS=$HEAD_ADDRESS
      - RAY_NUM_CPUS=$CPUS_PER_WORKER
      - RAY_NUM_GPUS=0
      - RAY_OBJECT_STORE_MEMORY=2000000000
    deploy:
      resources:
        limits:
          cpus: '$CPUS_PER_WORKER'
          memory: $MEMORY_PER_WORKER
        reservations:
          cpus: '1'
          memory: 2G
    restart: unless-stopped
    network_mode: host
    shm_size: '2g'
    labels:
      - \"com.wizardsofts.service=ray-worker\"
      - \"com.wizardsofts.server=$SERVER_IP\"
      - \"com.wizardsofts.worker-id=$i\"

EOF"
done

# Build and start workers
echo ""
echo "📦 Building and starting workers..."
# Try docker compose first (v2), fallback to docker-compose (v1)
ssh wizardsofts@$SERVER_IP "cd ~/ray-workers && (docker compose version &>/dev/null && docker compose up -d --build || docker-compose up -d --build)"

# Wait for startup
sleep 10

# Check status
echo ""
echo "✅ Workers deployed on $SERVER_IP:"
ssh wizardsofts@$SERVER_IP "docker ps --filter label=com.wizardsofts.service=ray-worker --format 'table {{.Names}}\t{{.Status}}'"

echo ""
echo "✅ Deployment complete!"

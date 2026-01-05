#!/bin/bash
set -euo pipefail

# Usage: ./setup-ray-worker.sh <server-ip> <worker-id> <num-cpus> <memory-gb>
# Example: ./setup-ray-worker.sh 10.0.0.80 1 4 8

SERVER_IP=${1:-"10.0.0.80"}
WORKER_ID=${2:-"1"}
NUM_CPUS=${3:-"4"}
MEMORY_GB=${4:-"8"}

echo "🚀 Deploying Ray Worker on $SERVER_IP (ID: $WORKER_ID)..."

# Copy files to remote server
echo "📦 Copying deployment files..."
scp -r infrastructure/distributed-ml/ray wizardsofts@$SERVER_IP:/tmp/

# Execute deployment on remote server
ssh wizardsofts@$SERVER_IP << EOF
set -e

# Create required directories
sudo mkdir -p /opt/ml-datasets /opt/ml-models /opt/wizardsofts-megabuild/infrastructure/distributed-ml
sudo chown -R \$USER:\$USER /opt/ml-datasets /opt/ml-models /opt/wizardsofts-megabuild

# Move files to proper location
sudo mv /tmp/ray /opt/wizardsofts-megabuild/infrastructure/distributed-ml/
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Create .env file for this worker
cat > .env.ray-worker << EOL
RAY_HEAD_ADDRESS=10.0.0.84:6379
WORKER_ID=$WORKER_ID
RAY_NUM_CPUS=$NUM_CPUS
RAY_NUM_GPUS=0
RAY_OBJECT_STORE_MEMORY=2000000000
RAY_MEMORY_LIMIT=${MEMORY_GB}G
EOL

# Build and start worker
docker-compose -f docker-compose.ray-worker.yml --env-file .env.ray-worker up -d --build

echo "✅ Ray worker deployed on $SERVER_IP"
EOF

# Verify worker connected
echo "⏳ Verifying worker connection..."
sleep 10

ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status" | grep "worker" && \
    echo "✅ Worker $WORKER_ID connected successfully!" || \
    echo "⚠️  Worker may still be connecting, check: docker logs ray-worker-$WORKER_ID"

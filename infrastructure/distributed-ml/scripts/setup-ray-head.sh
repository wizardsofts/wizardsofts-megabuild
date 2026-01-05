#!/bin/bash
set -euo pipefail

echo "🚀 Deploying Ray Head Node on Server 84..."

# Navigate to Ray directory
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Create required directories
sudo mkdir -p /opt/ml-datasets /opt/ml-models
sudo chown -R $USER:$USER /opt/ml-datasets /opt/ml-models

# Generate secure Redis password if not exists
if ! grep -q "RAY_REDIS_PASSWORD" .env.ray || grep -q "CHANGE_THIS" .env.ray; then
    REDIS_PASS=$(openssl rand -hex 32)
    sed -i "s/CHANGE_THIS_TO_SECURE_PASSWORD/$REDIS_PASS/" .env.ray
    echo "✅ Generated secure Redis password"
fi

# Pull latest images
docker-compose -f docker-compose.ray-head.yml pull

# Start Ray head node
docker-compose -f docker-compose.ray-head.yml up -d

# Wait for Ray to be ready
echo "⏳ Waiting for Ray head node to start..."
sleep 30

# Verify Ray is running
docker exec ray-head ray status || {
    echo "❌ Ray head node failed to start"
    docker logs ray-head --tail 50
    exit 1
}

echo "✅ Ray head node deployed successfully!"
echo "📊 Dashboard: http://10.0.0.84:8265"
echo "🔗 Connect with: ray.init(address='ray://10.0.0.84:10001')"

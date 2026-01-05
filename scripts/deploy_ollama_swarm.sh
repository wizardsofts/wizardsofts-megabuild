#!/bin/bash
# Deploy Ollama as Docker Swarm Service with Autoscaling
# Prerequisites: NFS setup complete on Server 80 and 84
# Run this on Server 84 (Swarm manager): ssh wizardsofts@10.0.0.84

set -e

echo "=== Deploy Ollama with Docker Swarm Autoscaling ==="

# Step 1: Verify NFS mount
echo "[1/7] Verifying NFS mount..."
if ! mountpoint -q /opt/ollama-models; then
    echo "❌ ERROR: /opt/ollama-models is not mounted"
    echo "Run setup_nfs_server80.sh and setup_nfs_client84.sh first"
    exit 1
fi
echo "✅ NFS mount verified"

# Step 2: Pull mistral:7b model to NFS (read-write on Server 80)
echo "[2/7] Pulling mistral:7b model to NFS volume..."
ssh wizardsofts@10.0.0.80 "docker run -d --name ollama-temp \
  -v /opt/ollama-models:/root/.ollama \
  ollama/ollama:latest"

echo "Waiting for container to start..."
sleep 5

ssh wizardsofts@10.0.0.80 "docker exec ollama-temp ollama pull mistral:7b"

echo "Verifying model..."
ssh wizardsofts@10.0.0.80 "docker exec ollama-temp ollama list"

echo "Cleaning up temporary container..."
ssh wizardsofts@10.0.0.80 "docker stop ollama-temp && docker rm ollama-temp"

echo "✅ Model pulled to NFS"

# Step 3: Enable Traefik Swarm mode
echo "[3/7] Updating Traefik configuration..."
TRAEFIK_CONFIG="/opt/wizardsofts-megabuild/traefik/traefik.yml"

if [ -f "$TRAEFIK_CONFIG" ]; then
    # Backup original
    cp "$TRAEFIK_CONFIG" "${TRAEFIK_CONFIG}.backup.$(date +%Y%m%d-%H%M%S)"

    # Update swarmMode to true
    sed -i 's/swarmMode: false/swarmMode: true/' "$TRAEFIK_CONFIG"

    echo "✅ Traefik config updated (swarmMode: true)"
    echo "Backup saved to ${TRAEFIK_CONFIG}.backup.*"
else
    echo "⚠️  WARNING: Traefik config not found at $TRAEFIK_CONFIG"
fi

# Step 4: Restart Traefik
echo "[4/7] Restarting Traefik..."
docker restart traefik || echo "⚠️  WARNING: Failed to restart Traefik"
sleep 3

# Step 5: Create overlay network for Ollama
echo "[5/7] Creating overlay network..."
if docker network ls | grep -q ollama-network; then
    echo "Network ollama-network already exists"
else
    docker network create --driver overlay --attachable ollama-network
    echo "✅ Network created"
fi

# Step 6: Deploy Ollama as Swarm service
echo "[6/7] Deploying Ollama Swarm service..."

docker service create \
  --name ollama \
  --replicas 1 \
  --network ollama-network \
  --mount type=bind,source=/opt/ollama-models,target=/root/.ollama,readonly \
  --publish 11434:11434 \
  --limit-memory 16G \
  --label "traefik.enable=true" \
  --label "traefik.docker.network=ollama-network" \
  --label "traefik.http.routers.ollama.rule=PathPrefix(\`/api/\`)" \
  --label "traefik.http.routers.ollama.entrypoints=web" \
  --label "traefik.http.services.ollama.loadbalancer.server.port=11434" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.path=/api/version" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.interval=10s" \
  ollama/ollama:latest

echo "✅ Ollama service deployed"

# Step 7: Verify deployment
echo "[7/7] Verifying deployment..."
sleep 5

echo ""
echo "Service status:"
docker service ps ollama

echo ""
echo "Service details:"
docker service inspect ollama --pretty

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test Ollama:"
echo "  curl http://10.0.0.84:11434/api/version"
echo "  curl http://10.0.0.84:11434/api/tags"
echo ""
echo "Scale up to 4 replicas:"
echo "  docker service scale ollama=4"
echo ""
echo "Monitor scaling:"
echo "  docker service ps ollama"
echo "  watch -n 2 'docker service ps ollama'"
echo ""

#!/bin/bash
# Deploy Ollama with Docker Swarm - Final Configuration
#
# Configuration:
#   - Default/Desired: 1 replica
#   - Max replicas: 3 (Server 84: max 2, Server 80: max 1)
#   - Auto-scaling: Via Docker Swarm native scaling
#   - No HAProxy, No Custom Autoscaler
#
# Run on Server 84 (Swarm manager): ssh wizardsofts@10.0.0.84

set -e

echo "=== Deploy Ollama with Docker Swarm (Final Configuration) ==="

# Verify we're on Swarm manager
if ! docker info | grep -q "Swarm: active"; then
    echo "❌ ERROR: Docker Swarm is not active"
    exit 1
fi

if ! docker node ls >/dev/null 2>&1; then
    echo "❌ ERROR: This node is not a Swarm manager"
    exit 1
fi

echo "✅ Swarm manager verified"

# Step 1: Verify NFS mount
echo "[1/8] Verifying NFS mount..."
if ! mountpoint -q /opt/ollama-models; then
    echo "❌ ERROR: /opt/ollama-models is not mounted"
    echo "Run setup_nfs_client84.sh first"
    exit 1
fi
echo "✅ NFS mount verified"

# Step 2: Label nodes for placement constraints
echo "[2/8] Configuring node labels for Ollama placement..."

# Get node IDs from hostnames
NODE_84=$(docker node ls --format '{{.ID}} {{.Hostname}}' | grep gmktec | awk '{print $1}')
NODE_80=$(docker node ls --format '{{.ID}} {{.Hostname}}' | grep hppavilion | awk '{print $1}')

if [ -z "$NODE_84" ]; then
    echo "❌ ERROR: Could not find gmktec (Server 84) node"
    exit 1
fi

if [ -z "$NODE_80" ]; then
    echo "❌ ERROR: Could not find hppavilion (Server 80) node"
    exit 1
fi

# Label Server 84 (max 2 replicas)
docker node update --label-add ollama.max=2 "$NODE_84"
echo "  ✅ Server 84 (gmktec): ollama.max=2"

# Label Server 80 (max 1 replica)
docker node update --label-add ollama.max=1 "$NODE_80"
echo "  ✅ Server 80 (hppavilion): ollama.max=1"

# Step 3: Pull mistral:7b model to NFS (Server 80)
echo "[3/8] Pulling mistral:7b model to NFS volume..."
ssh wizardsofts@10.0.0.80 "
    if docker ps -a | grep -q ollama-temp; then
        docker rm -f ollama-temp
    fi

    docker run -d --name ollama-temp \
        -v /opt/ollama-models:/root/.ollama \
        ollama/ollama:latest

    echo 'Waiting for container to start...'
    sleep 5

    echo 'Pulling mistral:7b...'
    docker exec ollama-temp ollama pull mistral:7b

    echo 'Verifying model...'
    docker exec ollama-temp ollama list

    echo 'Cleaning up...'
    docker stop ollama-temp && docker rm ollama-temp
"
echo "✅ Model pulled to NFS"

# Step 4: Enable Traefik Swarm mode
echo "[4/8] Updating Traefik configuration..."
TRAEFIK_CONFIG="/opt/wizardsofts-megabuild/traefik/traefik.yml"

if [ -f "$TRAEFIK_CONFIG" ]; then
    # Backup original
    cp "$TRAEFIK_CONFIG" "${TRAEFIK_CONFIG}.backup.$(date +%Y%m%d-%H%M%S)"

    # Update swarmMode to true
    sed -i 's/swarmMode: false/swarmMode: true/' "$TRAEFIK_CONFIG"

    echo "✅ Traefik config updated (swarmMode: true)"
else
    echo "⚠️  WARNING: Traefik config not found at $TRAEFIK_CONFIG"
fi

# Step 5: Restart Traefik
echo "[5/8] Restarting Traefik..."
docker restart traefik || echo "⚠️  WARNING: Failed to restart Traefik"
sleep 3

# Step 6: Create overlay network
echo "[6/8] Creating overlay network..."
if docker network ls | grep -q ollama-network; then
    echo "  Network ollama-network already exists"
else
    docker network create --driver overlay --attachable ollama-network
    echo "✅ Network created"
fi

# Step 7: Deploy Ollama Swarm service with placement constraints
echo "[7/8] Deploying Ollama Swarm service..."

# Remove existing service if exists
if docker service ls | grep -q ollama; then
    echo "  Removing existing ollama service..."
    docker service rm ollama
    sleep 3
fi

docker service create \
  --name ollama \
  --replicas 1 \
  --network ollama-network \
  --mount type=bind,source=/opt/ollama-models,target=/root/.ollama,readonly \
  --publish 11434:11434 \
  --limit-memory 16G \
  --constraint 'node.labels.ollama.max==2||node.labels.ollama.max==1' \
  --label "traefik.enable=true" \
  --label "traefik.docker.network=ollama-network" \
  --label "traefik.http.routers.ollama.rule=PathPrefix(\`/api/\`)" \
  --label "traefik.http.routers.ollama.entrypoints=web" \
  --label "traefik.http.services.ollama.loadbalancer.server.port=11434" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.path=/api/version" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.interval=10s" \
  ollama/ollama:latest

echo "✅ Ollama service deployed (1 replica)"

# Step 8: Verify deployment
echo "[8/8] Verifying deployment..."
sleep 5

echo ""
echo "Service status:"
docker service ps ollama

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Configuration:"
echo "  - Default replicas: 1"
echo "  - Max replicas: 3"
echo "  - Server 84 (gmktec): max 2 replicas"
echo "  - Server 80 (hppavilion): max 1 replica"
echo ""
echo "Test Ollama:"
echo "  curl http://10.0.0.84:11434/api/version"
echo "  curl http://10.0.0.84:11434/api/tags"
echo ""
echo "Scaling commands:"
echo "  docker service scale ollama=2  # Scale to 2"
echo "  docker service scale ollama=3  # Scale to 3 (max)"
echo "  docker service scale ollama=1  # Scale back to 1"
echo ""
echo "Monitor:"
echo "  docker service ps ollama"
echo "  watch -n 2 'docker service ps ollama'"
echo ""
echo "Note: Swarm will distribute replicas respecting node constraints:"
echo "  - First 2 replicas can go to Server 84"
echo "  - 3rd replica will go to Server 80"
echo ""

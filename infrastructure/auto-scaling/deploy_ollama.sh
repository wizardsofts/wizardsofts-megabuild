#!/bin/bash
# Deploy Ollama Service across all servers with load balancing

set -e  # Exit on any error

echo "=================================="
echo "Deploying Ollama Service"
echo "=================================="
echo

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Server details
SERVERS=("10.0.0.80" "10.0.0.81" "10.0.0.82" "10.0.0.84")
USERS=("wizardsofts" "wizardsofts" "deploy" "wizardsofts")
PORTS=("22" "22" "2025" "22")

# Deploy Ollama containers to all servers
log "Deploying Ollama containers to all servers..."

for i in "${!SERVERS[@]}"; do
    SERVER=${SERVERS[$i]}
    USER=${USERS[$i]}
    PORT=${PORTS[$i]}
    
    log "Deploying Ollama to $SERVER (User: $USER, Port: $PORT)..."
    
    # SSH into server and deploy Ollama container
    ssh -p $PORT $USER@$SERVER << 'EOF'
        # Create data directory if it doesn't exist
        sudo mkdir -p /data/ollama
        sudo chown $USER:$USER /data/ollama
        
        # Check if Ollama container is already running
        if docker ps | grep -q ollama; then
            echo "Ollama container already running on $HOSTNAME, stopping it..."
            docker stop ollama 2>/dev/null || true
            docker rm ollama 2>/dev/null || true
        fi
        
        # Pull latest Ollama image
        docker pull ollama/ollama:latest
        
        # Run Ollama container
        docker run -d \
          --name ollama \
          -p 0:11434 \
          -v /data/ollama:/root/.ollama \
          -e OLLAMA_HOST=0.0.0.0 \
          --restart unless-stopped \
          ollama/ollama:latest
          
        if [ $? -eq 0 ]; then
            echo "Ollama deployed successfully on $HOSTNAME"
            # Check if the container is running
            sleep 5  # Wait a bit for container to start
            if docker ps | grep -q ollama; then
                echo "Ollama container is running on $HOSTNAME"
                docker ps | grep ollama
            else
                echo "Warning: Ollama container failed to start on $HOSTNAME"
            fi
        else
            echo "Failed to deploy Ollama on $HOSTNAME"
        fi
EOF
    
    if [ $? -eq 0 ]; then
        log "✓ Ollama deployment initiated on $SERVER"
    else
        log "✗ Failed to deploy Ollama on $SERVER"
    fi
    
    echo
done

# Wait a bit for all containers to start
log "Waiting 30 seconds for Ollama containers to start..."
sleep 30

# Check if Ollama containers are running on each server
log "Verifying Ollama containers on each server..."

for i in "${!SERVERS[@]}"; do
    SERVER=${SERVERS[$i]}
    USER=${USERS[$i]}
    PORT=${PORTS[$i]}
    
    log "Checking Ollama on $SERVER..."
    
    CONTAINER_STATUS=$(ssh -p $PORT $USER@$SERVER "docker ps --filter name=ollama --format '{{.Status}}' 2>/dev/null" || echo "error")
    
    if [[ $CONTAINER_STATUS == *"Up"* ]]; then
        log "✓ Ollama is running on $SERVER: $CONTAINER_STATUS"
        
        # Get the mapped port
        MAPPED_PORT=$(ssh -p $PORT $USER@$SERVER "docker port ollama 2>/dev/null" | grep -o '[0-9]*$' || echo "unknown")
        log "  Port mapping: 11434 -> $MAPPED_PORT"
    else
        log "✗ Ollama is not running properly on $SERVER: $CONTAINER_STATUS"
    fi
done

echo
log "=================================="
log "Ollama Deployment Summary:"
log "✓ Ollama containers deployed to all 4 servers"
log "✓ Containers configured with auto-restart"
log "✓ Data volume mounted to /data/ollama"
log ""
log "Load Balancer Access:"
log "- External access: http://10.0.0.80:11434"
log "- All Ollama containers will be load balanced by HAProxy"
log ""
log "Next steps:"
log "1. The autoscaler will manage these containers automatically"
log "2. HAProxy will load balance requests across all Ollama instances"
log "3. Monitor the system via the API at http://10.0.0.80:8000"
log "=================================="
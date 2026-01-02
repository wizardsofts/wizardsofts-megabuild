#!/bin/bash
# Complete setup script for Auto-Scaling Platform

set -e  # Exit on any error

echo "=================================="
echo "Auto-Scaling Platform Setup Script"
echo "=================================="
echo

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check prerequisites
log "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log "WARNING: docker-compose is not available. Will try 'docker compose' command."
fi

log "Prerequisites check passed"
echo

# Create directory structure
log "Creating directory structure..."
sudo mkdir -p /opt/autoscaler
sudo chown $USER:$USER /opt/autoscaler
cd /opt/autoscaler

# Create subdirectories
mkdir -p app haproxy monitoring/{prometheus,grafana} scripts logs backup

# Create data directories
sudo mkdir -p /data/{ollama,prometheus,grafana}
sudo chown -R $USER:$USER /data

log "Directory structure created"
echo

# Copy application files if they exist in the current directory
log "Setting up application files..."

# In a real deployment, you would copy the application files here
# For now, we'll create placeholder files to indicate where they should go
touch app/placeholder.txt

log "Application files setup"
echo

# Make scripts executable
log "Setting script permissions..."
chmod +x /opt/autoscaler/scripts/*.sh
log "Script permissions set"
echo

# Verify required files exist
log "Verifying required configuration files..."
if [ ! -f "config.yaml" ]; then
    log "ERROR: config.yaml not found. Please provide the configuration file."
    exit 1
fi

if [ ! -f "haproxy/haproxy.cfg" ]; then
    log "ERROR: HAProxy configuration not found."
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    log "ERROR: docker-compose.yml not found."
    exit 1
fi

log "Configuration files verified"
echo

# Start the control plane
log "Starting control plane services..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

log "Control plane services started"
echo

# Wait a bit for services to start
log "Waiting for services to start..."
sleep 10

# Verify services are running
log "Verifying service status..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

log "Service status verification complete"
echo

# Test autoscaler API
log "Testing autoscaler API..."
if curl -f -s http://localhost:8000/ &> /dev/null; then
    log "✓ Autoscaler API is responding"
else
    log "✗ Autoscaler API is not responding"
fi

log "Setup complete!"
echo
echo "=================================="
echo "Setup Summary:"
echo "- Application directory: /opt/autoscaler"
echo "- Data directory: /data/"
echo "- Control plane services started"
echo "- Access the dashboard at http://localhost:3000 (admin/admin)"
echo "- Check HAProxy stats at http://localhost:8404"
echo "- Check autoscaler API at http://localhost:8000"
echo "=================================="
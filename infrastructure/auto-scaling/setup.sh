#!/bin/bash
# Setup script for Auto-Scaling Platform
# Creates the directory structure as specified in the PRD

set -e  # Exit on any error

echo "=== Auto-Scaling Platform Setup Script ==="
echo

# Check prerequisites
if ! command -v docker >/dev/null 2>&1; then
    echo "✗ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "⚠ docker-compose not found. This may be needed for the control plane."
fi

# Create base directories
echo "Creating directory structure..."
sudo mkdir -p /opt/autoscaler
sudo chown $USER:$USER /opt/autoscaler
cd /opt/autoscaler

# Create subdirectories as specified in PRD
mkdir -p app haproxy monitoring/{prometheus,grafana} scripts logs backup

# Create data directories
sudo mkdir -p /data/{ollama,prometheus,grafana}
sudo chown -R $USER:$USER /data

# Set proper permissions
sudo chown -R $USER:$USER /opt/autoscaler /data

# Create the PRD-specified app subdirectories
mkdir -p app/{__pycache__}

echo "Directory structure created successfully:"
echo
tree /opt/autoscaler -L 2 2>/dev/null || find /opt/autoscaler -maxdepth 2 -type d

echo
echo "Base directory structure is ready at /opt/autoscaler"
echo "Data directories are ready at /data/"
echo
echo "Next steps:"
echo "1. Create your configuration files"
echo "2. Deploy the application code"
echo "3. Start the control plane"
echo
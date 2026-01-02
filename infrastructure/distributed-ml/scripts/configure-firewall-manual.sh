#!/bin/bash
# Manual Firewall Configuration for Ray Cluster
# Run this script with sudo on each server

set -euo pipefail

echo "🔧 Configuring UFW firewall for Ray cluster..."

# Allow Ray GCS (Global Control Service)
sudo ufw allow from 10.0.0.0/24 to any port 6379 comment 'Ray GCS'

# Allow Ray Dashboard
sudo ufw allow from 10.0.0.0/24 to any port 8265 comment 'Ray Dashboard'

# Allow Ray Client
sudo ufw allow from 10.0.0.0/24 to any port 10001 comment 'Ray Client'

# Allow Ray Metrics
sudo ufw allow from 10.0.0.0/24 to any port 9091 comment 'Ray Metrics'

# Reload UFW
sudo ufw reload

echo "✅ Firewall configured for Ray cluster"
echo ""
echo "Allowed ports:"
sudo ufw status numbered | grep Ray

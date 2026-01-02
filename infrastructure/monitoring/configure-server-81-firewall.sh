#!/bin/bash
# Configure UFW on Server 81 for Monitoring Services
# Run this script on Server 81 as: sudo bash configure-server-81-firewall.sh

set -e

echo "=== Configuring UFW Firewall on Server 81 ==="
echo ""

# Reset UFW to default (optional - comment out if you want to keep existing rules)
# echo "Resetting UFW to defaults..."
# ufw --force reset

# Set default policies
echo "Setting default policies..."
ufw default deny incoming
ufw default allow outgoing

# Allow SSH from anywhere (IMPORTANT - don't lock yourself out!)
echo "Allowing SSH (port 22) from anywhere..."
ufw allow 22/tcp comment 'SSH access'

# Allow monitoring services from local network only (10.0.0.0/24)
echo "Allowing monitoring services from local network (10.0.0.0/24)..."

# Prometheus
ufw allow from 10.0.0.0/24 to any port 9090 proto tcp comment 'Prometheus - local network only'

# Grafana
ufw allow from 10.0.0.0/24 to any port 3002 proto tcp comment 'Grafana - local network only'

# Loki
ufw allow from 10.0.0.0/24 to any port 3100 proto tcp comment 'Loki - local network only'

# AlertManager
ufw allow from 10.0.0.0/24 to any port 9093 proto tcp comment 'AlertManager - local network only'

# Node Exporter (if running on Server 81)
ufw allow from 10.0.0.0/24 to any port 9100 proto tcp comment 'Node Exporter - local network only'

# Security Metrics (if running on Server 81)
ufw allow from 10.0.0.0/24 to any port 9101 proto tcp comment 'Security Metrics - local network only'

# Docker Swarm ports (from local network only)
echo "Allowing Docker Swarm ports from local network..."
ufw allow from 10.0.0.0/24 to any port 2377 proto tcp comment 'Docker Swarm management'
ufw allow from 10.0.0.0/24 to any port 7946 proto tcp comment 'Docker Swarm node discovery TCP'
ufw allow from 10.0.0.0/24 to any port 7946 proto udp comment 'Docker Swarm node discovery UDP'
ufw allow from 10.0.0.0/24 to any port 4789 proto udp comment 'Docker Swarm overlay network'

# Enable UFW
echo ""
echo "Enabling UFW..."
ufw --force enable

# Show status
echo ""
echo "=== UFW Configuration Complete ==="
echo ""
ufw status verbose
echo ""
echo "=== UFW Numbered Rules ==="
ufw status numbered

echo ""
echo "✅ Firewall configured successfully!"
echo ""
echo "Summary:"
echo "  - SSH (22): Allowed from anywhere"
echo "  - Monitoring services (9090, 3002, 3100, 9093): Local network only (10.0.0.0/24)"
echo "  - Docker Swarm ports: Local network only (10.0.0.0/24)"
echo "  - All other incoming: DENIED"
echo ""
echo "IMPORTANT: Make sure you can still SSH into this server!"

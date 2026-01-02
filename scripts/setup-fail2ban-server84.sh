#!/bin/bash
#
# fail2ban Setup Script for Server 84 (10.0.0.84)
# This script installs and configures fail2ban for SSH protection
#
# Usage: sudo ./setup-fail2ban-server84.sh
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  fail2ban Setup for Server 84${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Step 1: Install fail2ban
echo -e "${YELLOW}[1/6] Installing fail2ban...${NC}"
apt update
apt install -y fail2ban

# Step 2: Enable and start fail2ban
echo -e "${YELLOW}[2/6] Enabling fail2ban service...${NC}"
systemctl enable fail2ban
systemctl start fail2ban

# Step 3: Create jail.local configuration
echo -e "${YELLOW}[3/6] Creating /etc/fail2ban/jail.local...${NC}"
cat > /etc/fail2ban/jail.local << 'EOF'
# WizardSofts fail2ban Configuration
# Server 84 (10.0.0.84) - HP Production Server
#
# This configuration protects SSH from brute force attacks
# while allowing legitimate access from the local network.

[DEFAULT]
# Ban hosts for 1 hour (3600 seconds)
bantime = 3600

# A host is banned if it has generated "maxretry" during the last "findtime" seconds
findtime = 600

# Number of failures before a host gets banned
maxretry = 5

# Destination email for ban notifications (optional - set your email)
destemail = root@localhost
sender = fail2ban@wizardsofts.com

# Action: ban only (don't send emails by default)
action = %(action_)s

# Ignore local network IPs (adjust if needed)
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/24

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600

# For servers with heavy legitimate traffic, consider:
# maxretry = 10
# findtime = 1200

EOF

# Step 4: Disable SSH password authentication
echo -e "${YELLOW}[4/6] Disabling SSH password authentication...${NC}"

# Backup sshd_config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# Disable password authentication
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Disable root login
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Ensure PubkeyAuthentication is enabled
sed -i 's/^#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Step 5: Deploy fail2ban Prometheus exporter
echo -e "${YELLOW}[5/8] Deploying fail2ban Prometheus exporter...${NC}"

# Create directory for fail2ban exporter
mkdir -p ~/fail2ban-exporter

# Create docker-compose.yml for fail2ban exporter
cat > ~/fail2ban-exporter/docker-compose.yml << 'EXPORTER_EOF'
version: '3.8'

services:
  fail2ban-exporter:
    image: registry.gitlab.com/hectorjsmith/fail2ban-prometheus-exporter:latest
    container_name: fail2ban-exporter
    restart: unless-stopped
    network_mode: host
    volumes:
      - /var/run/fail2ban:/var/run/fail2ban:ro
      - /var/log/fail2ban.log:/var/log/fail2ban.log:ro
    environment:
      - F2B_DB_PATH=/var/lib/fail2ban/fail2ban.sqlite3
    ports:
      - "127.0.0.1:9191:9191"
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9191/metrics"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
EXPORTER_EOF

# Start fail2ban exporter
cd ~/fail2ban-exporter
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    docker compose up -d
else
    echo -e "${YELLOW}⚠ Docker/Docker Compose not found, skipping Prometheus exporter${NC}"
fi
cd -

# Step 6: Restart services
echo -e "${YELLOW}[6/8] Restarting SSH and fail2ban services...${NC}"
systemctl restart sshd
systemctl restart fail2ban

# Step 7: Update Prometheus configuration
echo -e "${YELLOW}[7/8] Updating Prometheus configuration...${NC}"

PROMETHEUS_CONFIG="/home/wizardsofts/prometheus-config/prometheus.yml"
if [ -f "$PROMETHEUS_CONFIG" ]; then
    # Check if fail2ban job already exists
    if ! grep -q "job_name: 'fail2ban-84'" "$PROMETHEUS_CONFIG"; then
        # Backup prometheus config
        cp "$PROMETHEUS_CONFIG" "${PROMETHEUS_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

        # Add fail2ban exporter to prometheus config
        cat >> "$PROMETHEUS_CONFIG" << 'PROM_EOF'

  # fail2ban exporter
  - job_name: 'fail2ban-84'
    static_configs:
      - targets: ['10.0.0.84:9191']
        labels:
          server: 'server-84'
          service: 'fail2ban'
PROM_EOF

        # Restart Prometheus container
        if docker ps | grep -q prometheus; then
            docker restart prometheus
            echo -e "${GREEN}✓ Prometheus configuration updated and restarted${NC}"
        else
            echo -e "${YELLOW}⚠ Prometheus container not found, manual restart required${NC}"
        fi
    else
        echo -e "${GREEN}✓ Prometheus already configured for fail2ban${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Prometheus config not found at $PROMETHEUS_CONFIG${NC}"
fi

# Step 8: Verify installation
echo -e "${YELLOW}[8/8] Verifying installation...${NC}"
echo ""

# Check fail2ban status
if systemctl is-active --quiet fail2ban; then
    echo -e "${GREEN}✓ fail2ban is running${NC}"
else
    echo -e "${RED}✗ fail2ban is not running${NC}"
    exit 1
fi

# Check SSH configuration
if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
    echo -e "${GREEN}✓ SSH password authentication disabled${NC}"
else
    echo -e "${YELLOW}⚠ SSH password authentication may still be enabled${NC}"
fi

if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
    echo -e "${GREEN}✓ SSH root login disabled${NC}"
else
    echo -e "${YELLOW}⚠ SSH root login may still be enabled${NC}"
fi

# Show fail2ban status
echo ""
echo -e "${GREEN}fail2ban jails status:${NC}"
fail2ban-client status

echo ""
echo -e "${GREEN}sshd jail status:${NC}"
fail2ban-client status sshd

# Check Prometheus exporter
echo ""
if docker ps | grep -q fail2ban-exporter; then
    echo -e "${GREEN}✓ fail2ban Prometheus exporter is running${NC}"
    echo -e "${GREEN}Metrics available at: http://localhost:9191/metrics${NC}"

    # Test metrics endpoint
    if curl -s http://localhost:9191/metrics > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Metrics endpoint is accessible${NC}"
    fi
else
    echo -e "${YELLOW}⚠ fail2ban Prometheus exporter not running (Docker may not be available)${NC}"
fi

echo ""
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo -e "Configuration summary:"
echo -e "  - Ban time: 1 hour"
echo -e "  - Max retries: 5 attempts in 10 minutes"
echo -e "  - Protected service: SSH"
echo -e "  - Password authentication: DISABLED"
echo -e "  - Root login: DISABLED"
echo -e "  - Prometheus exporter: http://localhost:9191/metrics"
echo ""
echo -e "Useful commands:"
echo -e "  ${YELLOW}sudo fail2ban-client status${NC}           - Show all jails"
echo -e "  ${YELLOW}sudo fail2ban-client status sshd${NC}      - Show SSH jail status"
echo -e "  ${YELLOW}sudo fail2ban-client unban --all${NC}      - Unban all IPs"
echo -e "  ${YELLOW}sudo fail2ban-client set sshd unbanip IP${NC} - Unban specific IP"
echo -e "  ${YELLOW}curl http://localhost:9191/metrics${NC}    - View fail2ban metrics"
echo -e "  ${YELLOW}docker logs fail2ban-exporter${NC}         - View exporter logs"
echo ""
echo -e "${YELLOW}Note: Backup of sshd_config saved to /etc/ssh/sshd_config.backup.*${NC}"
echo ""

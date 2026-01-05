#!/bin/bash
# Deploy Ray Worker Cleanup Script to All Servers
# This script can be run manually or integrated into CI/CD pipeline
# Usage: ./deploy_ray_cleanup.sh

set -e

# Configuration
SCRIPT_NAME="cleanup_ray_workers_smart.sh"
SCRIPT_PATH="$(dirname "$0")/$SCRIPT_NAME"
SERVERS=("10.0.0.80" "10.0.0.81" "10.0.0.82" "10.0.0.84")
REMOTE_USER="wizardsofts"
REMOTE_PATH="/home/$REMOTE_USER/$SCRIPT_NAME"
LOG_DIR="/home/$REMOTE_USER/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================================="
echo "Ray Worker Cleanup Deployment Script"
echo "=================================================================="
echo "Script: $SCRIPT_NAME"
echo "Servers: ${SERVERS[*]}"
echo "Started: $(date)"
echo ""

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}ERROR: Cleanup script not found at $SCRIPT_PATH${NC}"
    exit 1
fi

# Function to deploy to a single server
deploy_to_server() {
    local server=$1

    echo "[$server] Deploying cleanup script..."

    # Check connectivity
    if ! ping -c 1 -W 2 "$server" > /dev/null 2>&1; then
        echo -e "${YELLOW}  ⚠️  Server unreachable, skipping${NC}"
        return 1
    fi

    # Copy script to server
    if scp -q "$SCRIPT_PATH" "$REMOTE_USER@$server:$REMOTE_PATH"; then
        echo -e "${GREEN}  ✅ Script copied successfully${NC}"
    else
        echo -e "${RED}  ❌ Failed to copy script${NC}"
        return 1
    fi

    # Make script executable and create log directory
    ssh "$REMOTE_USER@$server" "chmod +x $REMOTE_PATH && mkdir -p $LOG_DIR" 2>/dev/null

    # Setup cron job
    echo "[$server] Setting up cron job..."
    ssh "$REMOTE_USER@$server" 'bash -s' <<'REMOTE_SCRIPT'
# Backup existing crontab
crontab -l > /tmp/cron.bak 2>/dev/null || echo "# WizardSofts Crontab" > /tmp/cron.bak

# Remove any existing Ray cleanup jobs
grep -v "cleanup_ray_workers" /tmp/cron.bak > /tmp/cron.new || true

# Add hourly cleanup job
echo "# Ray worker /tmp cleanup - runs hourly (deployed: $(date +%Y-%m-%d))" >> /tmp/cron.new
echo "0 * * * * /home/wizardsofts/cleanup_ray_workers_smart.sh \$(hostname -I | awk '{print \$1}') >> /home/wizardsofts/logs/ray_cleanup.log 2>&1" >> /tmp/cron.new

# Install new crontab
crontab /tmp/cron.new

# Cleanup temp files
rm /tmp/cron.bak /tmp/cron.new 2>/dev/null || true
REMOTE_SCRIPT

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✅ Cron job installed${NC}"
    else
        echo -e "${RED}  ❌ Failed to install cron job${NC}"
        return 1
    fi

    # Verify installation
    echo "[$server] Verifying installation..."
    local script_exists=$(ssh "$REMOTE_USER@$server" "[ -x $REMOTE_PATH ] && echo 'yes' || echo 'no'" 2>/dev/null)
    local cron_exists=$(ssh "$REMOTE_USER@$server" "crontab -l | grep -q 'cleanup_ray_workers' && echo 'yes' || echo 'no'" 2>/dev/null)

    if [ "$script_exists" = "yes" ] && [ "$cron_exists" = "yes" ]; then
        echo -e "${GREEN}  ✅ Deployment verified successfully${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}  ❌ Deployment verification failed${NC}"
        echo "     Script exists: $script_exists"
        echo "     Cron exists: $cron_exists"
        echo ""
        return 1
    fi
}

# Deploy to all servers
success_count=0
fail_count=0

for server in "${SERVERS[@]}"; do
    if deploy_to_server "$server"; then
        ((success_count++))
    else
        ((fail_count++))
    fi
done

echo "=================================================================="
echo "Deployment Summary"
echo "=================================================================="
echo -e "${GREEN}Successful: $success_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo "Finished: $(date)"
echo "=================================================================="

# Exit with error if any deployments failed
if [ $fail_count -gt 0 ]; then
    exit 1
fi

exit 0

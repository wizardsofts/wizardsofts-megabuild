#!/bin/bash
# Phase 4: Service & Docker Hardening
# Task: S1 - Disable unnecessary services
# Task: D1 - Harden Docker daemon

set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"

log_info "=== Phase 4: Service & Docker Hardening ==="
log_info "Target: $TARGET_IP | Mode: $MODE"

if [[ "$MODE" == "check" ]]; then
  log_info "Checking service configuration..."
  ssh "$TARGET_USER@$TARGET_IP" "sudo systemctl is-enabled bluetooth.service > /dev/null 2>&1 && echo 'S1: FAIL' || echo 'S1: PASS'"
  ssh "$TARGET_USER@$TARGET_IP" "test -f /etc/docker/daemon.json && echo 'D1: PASS' || echo 'D1: FAIL'"
  exit 0
fi

if [[ "$MODE" == "apply" ]]; then
  log_info "Applying service/docker hardening..."
  
  # Step 1: Disable unnecessary services
  log_info "Disabling unnecessary services..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Disabling unnecessary services..."
    for service in bluetooth.service cups.service avahi-daemon.service; do
      if systemctl is-enabled "$service" > /dev/null 2>&1; then
        echo "Disabling $service..."
        sudo systemctl disable "$service" 2>/dev/null || true
        sudo systemctl stop "$service" 2>/dev/null || true
      else
        echo "$service already disabled"
      fi
    done
    echo "Services disabled"
EOF

  # Step 2: Configure Docker daemon
  log_info "Configuring Docker daemon..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    DOCKER_CONFIG="/etc/docker/daemon.json"
    
    echo "Backing up daemon.json..."
    sudo mkdir -p /etc/docker
    test -f "$DOCKER_CONFIG" && sudo cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.bak.$(date +%s)" || true
    
    echo "Creating hardened daemon.json..."
    sudo tee "$DOCKER_CONFIG" > /dev/null << 'DOCKER_JSON'
{
  "userns-remap": "default",
  "icc": false,
  "no-new-privileges": true,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 2048,
      "Soft": 1024
    }
  },
  "live-restore": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
DOCKER_JSON
    
    echo "Docker daemon configuration updated"
    sudo systemctl reload docker || echo "Docker reload skipped"
EOF

  # Step 3: Restrict Docker socket
  log_info "Restricting Docker socket access..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    if test -S /var/run/docker.sock; then
      echo "Restricting docker.sock permissions..."
      sudo chmod 660 /var/run/docker.sock
      echo "Done"
    else
      echo "docker.sock not found"
    fi
EOF

  log_success "Phase 4 completed successfully"
  
elif [[ "$MODE" == "rollback" ]]; then
  log_info "Rolling back service/docker changes..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    for service in bluetooth.service cups.service avahi-daemon.service; do
      echo "Re-enabling $service..."
      sudo systemctl enable "$service" 2>/dev/null || true
    done
    
    LATEST_DOCKER=$(ls -t /etc/docker/daemon.json.bak.* 2>/dev/null | head -1)
    if [[ -n "$LATEST_DOCKER" ]]; then
      sudo cp "$LATEST_DOCKER" /etc/docker/daemon.json
      sudo systemctl reload docker
      echo "Docker config restored"
    fi
EOF
  log_success "Rollback complete"
fi

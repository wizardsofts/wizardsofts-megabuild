#!/bin/bash
# Phase 1: SSH & Network Hardening
# Task: N1 - Restrict SSH to Subnet
# Task: N2 - Configure UFW Firewall

set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"  # apply, check, or rollback

log_info "=== Phase 1: SSH & Network Hardening ==="
log_info "Target: $TARGET_IP | Mode: $MODE"

if [[ "$MODE" == "check" ]]; then
  log_info "Checking SSH/Network configuration..."
  ssh "$TARGET_USER@$TARGET_IP" "sudo ufw status | grep -q '22/tcp.*ALLOW.*10.0.0.0/24' && echo 'N1: PASS' || echo 'N1: FAIL'"
  ssh "$TARGET_USER@$TARGET_IP" "sudo grep -q '^PasswordAuthentication no' /etc/ssh/sshd_config && echo 'N2: PASS' || echo 'N2: FAIL'"
  exit 0
fi

if [[ "$MODE" == "apply" ]]; then
  log_info "Applying SSH/Network hardening..."
  
  # Step 1: Configure UFW
  log_info "Configuring UFW firewall..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Setting UFW defaults..."
    sudo ufw --force reset > /dev/null 2>&1 || true
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    echo "Adding SSH rule for local subnet..."
    sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp
    
    echo "Adding DNS rule..."
    sudo ufw allow from 10.0.0.0/24 to any port 53
    
    echo "Enabling UFW..."
    echo "y" | sudo ufw enable || true
    
    echo "UFW configuration complete"
    sudo ufw status numbered
EOF
  
  # Step 2: Harden sshd_config
  log_info "Hardening SSH configuration..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    SSHD_CONFIG="/etc/ssh/sshd_config"
    
    echo "Backing up sshd_config..."
    sudo cp "$SSHD_CONFIG" "$SSHD_CONFIG.bak.$(date +%s)"
    
    echo "Applying SSH hardening rules..."
    sudo sed -i '/^#PermitRootLogin/d; /^PermitRootLogin/d' "$SSHD_CONFIG"
    echo "PermitRootLogin no" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#PasswordAuthentication/d; /^PasswordAuthentication/d' "$SSHD_CONFIG"
    echo "PasswordAuthentication no" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#PubkeyAuthentication/d; /^PubkeyAuthentication/d' "$SSHD_CONFIG"
    echo "PubkeyAuthentication yes" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#MaxAuthAttempts/d; /^MaxAuthAttempts/d' "$SSHD_CONFIG"
    echo "MaxAuthAttempts 3" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#LoginGraceTime/d; /^LoginGraceTime/d' "$SSHD_CONFIG"
    echo "LoginGraceTime 20" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#X11Forwarding/d; /^X11Forwarding/d' "$SSHD_CONFIG"
    echo "X11Forwarding no" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#AllowTcpForwarding/d; /^AllowTcpForwarding/d' "$SSHD_CONFIG"
    echo "AllowTcpForwarding no" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    sudo sed -i '/^#PermitEmptyPasswords/d; /^PermitEmptyPasswords/d' "$SSHD_CONFIG"
    echo "PermitEmptyPasswords no" | sudo tee -a "$SSHD_CONFIG" > /dev/null
    
    echo "Validating SSH configuration..."
    sudo sshd -t && echo "SSH config valid" || (echo "SSH config invalid"; exit 1)
    
    echo "Restarting SSH service..."
    sudo systemctl restart ssh
    echo "SSH hardening complete"
EOF

  # Step 3: Set SSH key permissions
  log_info "Fixing SSH key permissions..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Setting SSH key permissions..."
    chmod 700 ~/.ssh || true
    chmod 600 ~/.ssh/authorized_keys || true
    echo "SSH key permissions updated"
EOF

  log_success "Phase 1 completed successfully"
  
elif [[ "$MODE" == "rollback" ]]; then
  log_info "Rolling back SSH/Network changes..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Restoring sshd_config from backup..."
    LATEST_BACKUP=$(ls -t /etc/ssh/sshd_config.bak.* 2>/dev/null | head -1)
    if [[ -n "$LATEST_BACKUP" ]]; then
      sudo cp "$LATEST_BACKUP" /etc/ssh/sshd_config
      sudo systemctl restart ssh
      echo "Rollback complete"
    else
      echo "No backup found"
    fi
    
    echo "Disabling UFW..."
    echo "y" | sudo ufw disable || true
EOF
  log_success "Rollback complete"
fi

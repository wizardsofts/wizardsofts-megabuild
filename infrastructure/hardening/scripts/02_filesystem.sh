#!/bin/bash
# Phase 2: File System & Permission Hardening
# Task: F1 - Remount /tmp with noexec
# Task: F2 - Audit and remove world-executable files

set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"

log_info "=== Phase 2: File System Hardening ==="
log_info "Target: $TARGET_IP | Mode: $MODE"

if [[ "$MODE" == "check" ]]; then
  log_info "Checking file system configuration..."
  ssh "$TARGET_USER@$TARGET_IP" "mount | grep -q '/tmp.*noexec' && echo 'F1: PASS' || echo 'F1: FAIL'"
  ssh "$TARGET_USER@$TARGET_IP" "sudo find /usr/local -perm -001 -type f 2>/dev/null | wc -l | awk '{print (\$1==0 ? \"F2: PASS\" : \"F2: FAIL\")}'}"
  exit 0
fi

if [[ "$MODE" == "apply" ]]; then
  log_info "Applying file system hardening..."
  
  # Step 1: Remount /tmp with noexec
  log_info "Remounting /tmp with noexec,nosuid,nodev..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Backing up /etc/fstab..."
    sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)
    
    echo "Remounting /tmp..."
    # Check if /tmp has an entry in fstab
    if grep -q "^[^#]*[[:space:]]/tmp[[:space:]]" /etc/fstab; then
      echo "/tmp already in fstab, updating options..."
      sudo sed -i '/^[^#]*[[:space:]]\/tmp[[:space:]]/s/defaults/noexec,nosuid,nodev,mode=1777/' /etc/fstab
    else
      echo "Adding /tmp mount options..."
      echo "tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev,mode=1777 0 0" | sudo tee -a /etc/fstab > /dev/null
    fi
    
    echo "Remounting /tmp..."
    sudo mount -o remount,noexec,nosuid,nodev /tmp
    
    echo "Verifying..."
    mount | grep "/tmp" || echo "Warning: /tmp not found in mount output"
EOF

  # Step 2: Remount /var/tmp with noexec
  log_info "Remounting /var/tmp with noexec,nosuid,nodev..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Binding /var/tmp to /tmp..."
    sudo mount --bind /tmp /var/tmp
    echo "Mounted"
EOF

  # Step 3: Remount /dev/shm with noexec
  log_info "Remounting /dev/shm with noexec,nosuid,nodev..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Remounting /dev/shm..."
    sudo mount -o remount,noexec,nosuid,nodev /dev/shm
    echo "Done"
EOF

  # Step 4: Restrict /opt/apps permissions
  log_info "Restricting /opt/apps permissions..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Setting /opt/apps permissions..."
    sudo chmod 750 /opt/apps
    sudo chmod 750 /opt/apps/llm-server
    sudo chmod 700 /opt/apps/llm-server/data 2>/dev/null || true
    echo "Permissions updated"
EOF

  # Step 5: Restrict home directory permissions
  log_info "Restricting home directory permissions..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Setting home directory permissions..."
    chmod 700 ~/.ssh || true
    chmod 600 ~/.ssh/authorized_keys || true
    chmod 700 ~ || echo "Cannot change home ownership, skipping"
    echo "Done"
EOF

  log_success "Phase 2 completed successfully"
  
elif [[ "$MODE" == "rollback" ]]; then
  log_info "Rolling back file system changes..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Restoring /etc/fstab..."
    LATEST_BACKUP=$(ls -t /etc/fstab.bak.* 2>/dev/null | head -1)
    if [[ -n "$LATEST_BACKUP" ]]; then
      sudo cp "$LATEST_BACKUP" /etc/fstab
      echo "Fstab restored"
    fi
    
    echo "Remounting /tmp with defaults..."
    sudo mount -o remount,defaults /tmp || true
    sudo mount -o remount,defaults /dev/shm || true
EOF
  log_success "Rollback complete"
fi

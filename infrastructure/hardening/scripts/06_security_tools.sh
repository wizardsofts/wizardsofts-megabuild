#!/bin/bash
# Phase 6: Security Tools & Monitoring
# Task: T1 - Install and configure Fail2Ban
# Task: T2 - Install and configure auditd
# Task: T3 - Configure remote logging

set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"

log_info "=== Phase 6: Security Tools & Monitoring ==="
log_info "Target: $TARGET_IP | Mode: $MODE"

if [[ "$MODE" == "check" ]]; then
  log_info "Checking security tools..."
  ssh "$TARGET_USER@$TARGET_IP" "sudo systemctl is-active fail2ban > /dev/null 2>&1 && echo 'T1: PASS' || echo 'T1: FAIL'"
  ssh "$TARGET_USER@$TARGET_IP" "sudo systemctl is-active auditd > /dev/null 2>&1 && echo 'T2: PASS' || echo 'T2: FAIL'"
  ssh "$TARGET_USER@$TARGET_IP" "sudo grep -q '@10.0.0.80' /etc/rsyslog.conf 2>/dev/null && echo 'T3: PASS' || echo 'T3: FAIL (optional)'"
  exit 0
fi

if [[ "$MODE" == "apply" ]]; then
  log_info "Applying security tools..."
  
  # Step 1: Install Fail2Ban
  log_info "Installing Fail2Ban..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Installing fail2ban..."
    sudo apt update > /dev/null
    sudo apt install -y fail2ban > /dev/null
    echo "Installed"
    
    echo "Configuring fail2ban jail.local..."
    sudo tee /etc/fail2ban/jail.local > /dev/null << 'FAIL2BAN'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
destemail = admin@example.com
sendername = Fail2Ban

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200
FAIL2BAN
    
    echo "Enabling fail2ban..."
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    echo "Fail2Ban configured"
EOF

  # Step 2: Install auditd
  log_info "Installing auditd..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Installing auditd..."
    sudo apt install -y auditd audispd-plugins > /dev/null
    echo "Installed"
    
    echo "Configuring audit rules..."
    sudo tee /etc/audit/rules.d/hardening.rules > /dev/null << 'AUDIT'
# Remove any existing rules
-D

# Buffer Size
-b 8192

# Failure Mode
-f 2

# Audit sudo usage
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Audit system calls
-a always,exit -F arch=b64 -S execve -F uid>=1000 -F uid!=4294967295 -k user_commands

# Audit file deletion
-a always,exit -F arch=b64 -S unlink,unlinkat,rename,renameat -F auid>=1000 -k delete

# Audit network changes
-w /etc/hosts -p wa -k network_modifications
-w /etc/hostname -p wa -k network_modifications

# Audit SSH configuration
-w /etc/ssh/sshd_config -p wa -k sshd_config

# Make immutable
-e 2
AUDIT
    
    echo "Loading audit rules..."
    sudo service auditd restart
    echo "auditd configured"
EOF

  # Step 3: Configure remote logging (optional)
  log_info "Configuring remote logging..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Backing up rsyslog.conf..."
    sudo cp /etc/rsyslog.conf /etc/rsyslog.conf.bak.$(date +%s)
    
    echo "Adding remote logging rule..."
    if ! grep -q '@10.0.0.80' /etc/rsyslog.conf; then
      echo "*.* @10.0.0.80:514" | sudo tee -a /etc/rsyslog.conf > /dev/null
      echo "Note: Remote logging requires syslog server on 10.0.0.80"
    else
      echo "Remote logging already configured"
    fi
    
    sudo systemctl restart rsyslog
    echo "Remote logging configured"
EOF

  log_success "Phase 6 completed successfully"
  
elif [[ "$MODE" == "rollback" ]]; then
  log_info "Rolling back security tools..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Stopping and removing fail2ban..."
    sudo systemctl stop fail2ban
    sudo systemctl disable fail2ban
    sudo apt remove -y fail2ban > /dev/null || true
    
    echo "Stopping and removing auditd..."
    sudo systemctl stop auditd
    sudo systemctl disable auditd
    sudo apt remove -y auditd > /dev/null || true
    
    echo "Restoring rsyslog.conf..."
    LATEST_RSYSLOG=$(ls -t /etc/rsyslog.conf.bak.* 2>/dev/null | head -1)
    if [[ -n "$LATEST_RSYSLOG" ]]; then
      sudo cp "$LATEST_RSYSLOG" /etc/rsyslog.conf
      sudo systemctl restart rsyslog
    fi
    
    echo "Rollback complete"
EOF
  log_success "Rollback complete"
fi

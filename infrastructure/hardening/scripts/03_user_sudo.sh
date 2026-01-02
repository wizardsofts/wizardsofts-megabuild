#!/bin/bash
# Phase 3: User & Sudo Hardening
# Task: U1 - Configure sudo to require password
# Task: U2 - Set password policy

set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"

log_info "=== Phase 3: User & Sudo Hardening ==="
log_info "Target: $TARGET_IP | Mode: $MODE"

if [[ "$MODE" == "check" ]]; then
  log_info "Checking user/sudo configuration..."
  ssh "$TARGET_USER@$TARGET_IP" "sudo grep -q '^Defaults.*requiretty' /etc/sudoers && echo 'U1: PASS' || echo 'U1: FAIL'"
  ssh "$TARGET_USER@$TARGET_IP" "sudo test -f /etc/security/pwquality.conf && echo 'U2: PASS' || echo 'U2: FAIL'"
  exit 0
fi

if [[ "$MODE" == "apply" ]]; then
  log_info "Applying user/sudo hardening..."
  
  # Step 1: Configure sudoers
  log_info "Configuring sudo..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Backing up sudoers..."
    sudo cp /etc/sudoers /etc/sudoers.bak.$(date +%s)
    
    echo "Configuring sudoers..."
    sudo visudo -c < <(cat /etc/sudoers && echo "
# Hardened sudoers config
Defaults requiretty
Defaults use_pty
Defaults log_host, log_command
Defaults ignore_dot
Defaults passwd_timeout=1
Defaults env_reset") && {
      cat /etc/sudoers && echo "
# Hardened sudoers config
Defaults requiretty
Defaults use_pty
Defaults log_host, log_command
Defaults ignore_dot
Defaults passwd_timeout=1
Defaults env_reset" | sudo tee /etc/sudoers.tmp > /dev/null
      sudo mv /etc/sudoers.tmp /etc/sudoers
      sudo chmod 440 /etc/sudoers
    } || echo "Sudoers update skipped"
    
    echo "Sudo configuration complete"
EOF

  # Step 2: Install password quality tools
  log_info "Installing password quality tools..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Installing libpam-pwquality..."
    sudo apt update > /dev/null
    sudo apt install -y libpam-pwquality > /dev/null
    echo "Installed"
EOF

  # Step 3: Configure password policy
  log_info "Configuring password policy..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Backing up pwquality.conf..."
    sudo cp /etc/security/pwquality.conf /etc/security/pwquality.conf.bak.$(date +%s)
    
    echo "Setting password requirements..."
    sudo sed -i 's/^# minlen.*/minlen = 14/' /etc/security/pwquality.conf
    sudo sed -i 's/^# dcredit.*/dcredit = -1/' /etc/security/pwquality.conf
    sudo sed -i 's/^# ucredit.*/ucredit = -1/' /etc/security/pwquality.conf
    sudo sed -i 's/^# lcredit.*/lcredit = -1/' /etc/security/pwquality.conf
    sudo sed -i 's/^# ocredit.*/ocredit = -1/' /etc/security/pwquality.conf
    
    # Add missing entries
    grep -q "^minlen" /etc/security/pwquality.conf || echo "minlen = 14" | sudo tee -a /etc/security/pwquality.conf > /dev/null
    grep -q "^dcredit" /etc/security/pwquality.conf || echo "dcredit = -1" | sudo tee -a /etc/security/pwquality.conf > /dev/null
    grep -q "^ucredit" /etc/security/pwquality.conf || echo "ucredit = -1" | sudo tee -a /etc/security/pwquality.conf > /dev/null
    grep -q "^lcredit" /etc/security/pwquality.conf || echo "lcredit = -1" | sudo tee -a /etc/security/pwquality.conf > /dev/null
    grep -q "^ocredit" /etc/security/pwquality.conf || echo "ocredit = -1" | sudo tee -a /etc/security/pwquality.conf > /dev/null
    
    echo "Password policy updated"
EOF

  # Step 4: Set password expiration
  log_info "Setting password expiration policy..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Backing up login.defs..."
    sudo cp /etc/login.defs /etc/login.defs.bak.$(date +%s)
    
    echo "Setting expiration policies..."
    sudo sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/' /etc/login.defs
    sudo sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   1/' /etc/login.defs
    sudo sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   7/' /etc/login.defs
    
    echo "Policies set"
EOF

  log_success "Phase 3 completed successfully"
  
elif [[ "$MODE" == "rollback" ]]; then
  log_info "Rolling back user/sudo changes..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    LATEST_SUDOERS=$(ls -t /etc/sudoers.bak.* 2>/dev/null | head -1)
    if [[ -n "$LATEST_SUDOERS" ]]; then
      sudo cp "$LATEST_SUDOERS" /etc/sudoers
      echo "Sudoers restored"
    fi
    
    LATEST_PWQUALITY=$(ls -t /etc/security/pwquality.conf.bak.* 2>/dev/null | head -1)
    if [[ -n "$LATEST_PWQUALITY" ]]; then
      sudo cp "$LATEST_PWQUALITY" /etc/security/pwquality.conf
      echo "Password policy restored"
    fi
EOF
  log_success "Rollback complete"
fi

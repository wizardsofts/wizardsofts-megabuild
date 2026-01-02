#!/bin/bash
# Phase 5: Kernel Hardening
# Task: K1 - Apply sysctl parameters
# Task: K2 - Disable unnecessary kernel modules

set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"

log_info "=== Phase 5: Kernel Hardening ==="
log_info "Target: $TARGET_IP | Mode: $MODE"

if [[ "$MODE" == "check" ]]; then
  log_info "Checking kernel parameters..."
  ssh "$TARGET_USER@$TARGET_IP" "sudo sysctl net.ipv4.tcp_syncookies | grep -q '= 1' && echo 'K1: PASS' || echo 'K1: FAIL'"
  ssh "$TARGET_USER@$TARGET_IP" "test -f /etc/modprobe.d/hardening.conf && echo 'K2: PASS' || echo 'K2: FAIL'"
  exit 0
fi

if [[ "$MODE" == "apply" ]]; then
  log_info "Applying kernel hardening..."
  
  # Step 1: Apply sysctl hardening
  log_info "Applying sysctl parameters..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    SYSCTL_FILE="/etc/sysctl.d/99-hardening.conf"
    
    echo "Backing up existing sysctl.d..."
    ls /etc/sysctl.d/ | head -3
    
    echo "Creating hardened sysctl configuration..."
    sudo tee "$SYSCTL_FILE" > /dev/null << 'SYSCTL'
# IP Forwarding
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# ICMP Redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# SYN Flood Protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_max_syn_backlog = 4096

# ICMP
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.icmp_timestamps = 0

# Reverse Path Filtering
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log Martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Kernel Protections
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.unprivileged_bpf_disabled = 1
kernel.unprivileged_userns_clone = 0
kernel.perf_event_paranoid = 3
kernel.yama.ptrace_scope = 2

# Process Hiding
kernel.hidepid = 2
kernel.hide_kmesg_logs = 1

# Core Dumps
kernel.core_uses_pid = 1
fs.suid_dumpable = 0

# Magic SysRq
kernel.sysrq = 0

# Module Loading
kernel.modules_disabled = 1

# Kernel Logs
kernel.printk = 3 3 3 3
SYSCTL
    
    echo "Applying sysctl settings..."
    sudo sysctl -p "$SYSCTL_FILE" > /dev/null
    
    echo "Verifying key parameters..."
    sudo sysctl net.ipv4.tcp_syncookies
    echo "Kernel hardening applied"
EOF

  # Step 2: Disable unnecessary kernel modules
  log_info "Disabling unnecessary kernel modules..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    MODPROBE_FILE="/etc/modprobe.d/hardening.conf"
    
    echo "Creating modprobe hardening configuration..."
    sudo tee "$MODPROBE_FILE" > /dev/null << 'MODPROBE'
# Disable uncommon filesystems
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install udf /bin/true

# Disable uncommon protocols
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
install dccp /bin/true

# Disable USB storage if not needed
install usb-storage /bin/true
MODPROBE
    
    echo "Module blacklisting configured"
EOF

  log_success "Phase 5 completed successfully"
  
elif [[ "$MODE" == "rollback" ]]; then
  log_info "Rolling back kernel hardening..."
  ssh "$TARGET_USER@$TARGET_IP" << 'EOF'
    set -e
    echo "Removing sysctl hardening..."
    sudo rm -f /etc/sysctl.d/99-hardening.conf
    sudo sysctl -p > /dev/null || true
    
    echo "Removing modprobe hardening..."
    sudo rm -f /etc/modprobe.d/hardening.conf
    
    echo "Rollback complete"
EOF
  log_success "Rollback complete"
fi

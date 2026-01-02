#!/bin/bash
# Quick Vulnerability Remediation Script
# Automatically fixes identified vulnerabilities on the target server

set -euo pipefail

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
SSH_PASSWORD="${3:-}"

if [ -z "$SSH_PASSWORD" ]; then
  echo "Error: SSH password required"
  echo "Usage: $0 <target_ip> <target_user> <ssh_password>"
  exit 1
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       QUICK VULNERABILITY REMEDIATION SCRIPT                  ║"
echo "║       Target: $TARGET_IP | User: $TARGET_USER                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Function to execute commands on remote server
execute_on_remote() {
  local cmd="$1"
  echo "Executing: $cmd"
  sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << EOF
$cmd
EOF
}

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
  echo "⚠ sshpass is not installed. Please install it:"
  echo "  macOS: brew install sshpass"
  echo "  Ubuntu: sudo apt install sshpass"
  exit 1
fi

echo "Starting vulnerability remediation..."
echo ""

# 1. Update system
echo "1️⃣  Updating system packages..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << 'EOF'
echo "Updating package lists..."
sudo apt update > /dev/null
echo "Upgrading packages (this may take several minutes)..."
sudo apt upgrade -y > /dev/null 2>&1
echo "✓ System updated"
EOF

# 2. Remove risky packages
echo ""
echo "2️⃣  Removing risky packages (telnet, ftp)..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << 'EOF'
echo "Removing telnet and ftp..."
sudo apt remove -y telnet ftp > /dev/null 2>&1
echo "✓ Risky packages removed"
EOF

# 3. Install auditd
echo ""
echo "3️⃣  Installing auditd..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << 'EOF'
echo "Installing auditd..."
sudo apt install -y auditd audispd-plugins > /dev/null 2>&1
sudo systemctl enable auditd > /dev/null 2>&1
sudo systemctl start auditd > /dev/null 2>&1
echo "✓ Auditd installed and started"
EOF

# 4. Fix SSH config permissions
echo ""
echo "4️⃣  Fixing SSH configuration permissions..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << 'EOF'
echo "Fixing /etc/ssh/sshd_config permissions..."
sudo chmod 600 /etc/ssh/sshd_config
echo "✓ SSH config permissions fixed (600)"
EOF

# 5. Disable IP forwarding
echo ""
echo "5️⃣  Disabling IP forwarding (if not needed)..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << 'EOF'
echo "Disabling IP forwarding..."
sudo sysctl -w net.ipv4.ip_forward=0 > /dev/null
echo "✓ IP forwarding disabled"
EOF

# 6. Fix /root permissions
echo ""
echo "6️⃣  Setting /root directory permissions..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" << 'EOF'
echo "Setting /root permissions to 700..."
sudo chmod 700 /root
echo "✓ /root permissions set to 700"
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  REMEDIATION COMPLETE                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Quick fixes applied successfully!"
echo ""
echo "NEXT STEPS:"
echo "1. Run the full hardening script for comprehensive security:"
echo "   source .env && source hardening/.env"
echo "   bash hardening/harden.sh 10.0.0.84 wizardsofts apply"
echo ""
echo "2. Verify remediation:"
echo "   bash hardening/scripts/scan_vulnerabilities.sh 10.0.0.84 wizardsofts"
echo ""
echo "3. Review the detailed vulnerability report:"
echo "   cat hardening/logs/VULNERABILITY_REPORT_20251219.md"
echo ""

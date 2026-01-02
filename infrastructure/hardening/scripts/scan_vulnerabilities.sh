#!/bin/bash
# Comprehensive Vulnerability Scan Script
# Scans target server for security vulnerabilities, misconfigurations, and open ports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
SCAN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCAN_REPORT_DIR="$SCRIPT_DIR/../logs/vulnerability_scans"
SCAN_REPORT="$SCAN_REPORT_DIR/${TARGET_IP}_vulnerability_scan_${SCAN_TIMESTAMP}.log"

# Initialize scan report directory
mkdir -p "$SCAN_REPORT_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_header() {
  echo -e "${BLUE}=== $1 ===${NC}" | tee -a "$SCAN_REPORT"
}

log_pass() {
  echo -e "${GREEN}✓ PASS:${NC} $1" | tee -a "$SCAN_REPORT"
}

log_fail() {
  echo -e "${RED}✗ FAIL:${NC} $1" | tee -a "$SCAN_REPORT"
}

log_warn() {
  echo -e "${YELLOW}⚠ WARN:${NC} $1" | tee -a "$SCAN_REPORT"
}

log_info() {
  echo -e "${BLUE}ℹ INFO:${NC} $1" | tee -a "$SCAN_REPORT"
}

# Initialize report
cat > "$SCAN_REPORT" << EOF
╔════════════════════════════════════════════════════════════════╗
║       SERVER VULNERABILITY SCAN REPORT                         ║
║       Target: $TARGET_IP                                       ║
║       User: $TARGET_USER                                       ║
║       Timestamp: $(date '+%Y-%m-%d %H:%M:%S')                  ║
╚════════════════════════════════════════════════════════════════╝

EOF

echo -e "${BLUE}Starting comprehensive vulnerability scan on $TARGET_IP...${NC}"
echo "Report will be saved to: $SCAN_REPORT"
echo ""

# Test connectivity first
log_header "CONNECTIVITY CHECK"
if ping -c 1 -W 2 "$TARGET_IP" &> /dev/null; then
  log_pass "Server is reachable"
else
  log_fail "Server is not reachable. Aborting scan."
  exit 1
fi

# SSH connectivity check
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" "echo 'connected'" &> /dev/null; then
  log_pass "SSH connection successful"
else
  log_fail "SSH connection failed. Some checks will be unavailable."
fi

# ============================================================================
# 1. OPEN PORTS AND SERVICES SCAN
# ============================================================================
log_header "OPEN PORTS AND SERVICES SCAN"

log_info "Scanning for open ports (nmap)..."
NMAP_RESULTS=$(nmap -sV -p- --max-retries 1 "$TARGET_IP" 2>/dev/null | grep -E "^[0-9]+/" || true)

if [ -z "$NMAP_RESULTS" ]; then
  log_warn "nmap not available or no open ports detected on local scan"
  log_info "Checking exposed services via SSH..."
  
  ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1 || true
    echo "Remote port scan (netstat):"
    sudo netstat -tulpn 2>/dev/null | grep LISTEN || sudo ss -tulpn 2>/dev/null | grep LISTEN || true
SSHEOF
else
  echo "$NMAP_RESULTS" | tee -a "$SCAN_REPORT"
  
  # Check for common high-risk ports
  for port in 23 69 161 389 3389; do
    if echo "$NMAP_RESULTS" | grep -q "^$port/"; then
      log_fail "High-risk port $port is open (consider closing if not needed)"
    fi
  done
fi

# ============================================================================
# 2. SSH CONFIGURATION SECURITY AUDIT
# ============================================================================
log_header "SSH CONFIGURATION SECURITY AUDIT"

log_info "Checking SSH configuration..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "SSH Configuration Review:"
echo "============================"

# Check PermitRootLogin
if sudo grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
  echo "✓ PermitRootLogin disabled"
else
  echo "✗ WARNING: PermitRootLogin might be enabled"
fi

# Check PasswordAuthentication
if sudo grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
  echo "✓ PasswordAuthentication disabled"
else
  echo "✗ WARNING: PasswordAuthentication is enabled (use key-based auth)"
fi

# Check PubkeyAuthentication
if sudo grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config; then
  echo "✓ PubkeyAuthentication enabled"
else
  echo "✗ WARNING: PubkeyAuthentication might be disabled"
fi

# Check PermitEmptyPasswords
if sudo grep -q "^PermitEmptyPasswords no" /etc/ssh/sshd_config; then
  echo "✓ PermitEmptyPasswords disabled"
else
  echo "✗ WARNING: Empty passwords might be permitted"
fi

# Check X11Forwarding
if sudo grep -q "^X11Forwarding no" /etc/ssh/sshd_config; then
  echo "✓ X11Forwarding disabled"
else
  echo "⚠ WARNING: X11Forwarding enabled (consider disabling)"
fi

# Check MaxAuthTries
if sudo grep -q "^MaxAuthTries" /etc/ssh/sshd_config; then
  echo "✓ MaxAuthTries configured: $(sudo grep 'MaxAuthTries' /etc/ssh/sshd_config | cut -d' ' -f2)"
else
  echo "⚠ WARNING: MaxAuthTries might be at default (6)"
fi

SSHEOF

# ============================================================================
# 3. FIREWALL STATUS CHECK
# ============================================================================
log_header "FIREWALL STATUS CHECK"

log_info "Checking firewall configuration..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Firewall Configuration:"
echo "========================"

# UFW status
if command -v ufw &> /dev/null; then
  UFW_STATUS=$(sudo ufw status | head -1)
  echo "UFW Status: $UFW_STATUS"
  
  if echo "$UFW_STATUS" | grep -q "inactive"; then
    echo "✗ WARNING: UFW firewall is INACTIVE"
  elif echo "$UFW_STATUS" | grep -q "active"; then
    echo "✓ UFW firewall is ACTIVE"
    echo "Rules:"
    sudo ufw status | tail -n +3 | head -20
  fi
else
  echo "⚠ UFW not installed"
fi

# iptables status
echo ""
echo "iptables rules (INPUT chain):"
sudo iptables -L INPUT -n 2>/dev/null | head -10 || echo "Unable to check iptables"

SSHEOF

# ============================================================================
# 4. SYSTEM UPDATES AND PATCH STATUS
# ============================================================================
log_header "SYSTEM UPDATES AND PATCH STATUS"

log_info "Checking for available updates..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Update Status:"
echo "=============="

# Check for available updates
if command -v apt &> /dev/null; then
  sudo apt update > /dev/null 2>&1
  UPDATES=$(sudo apt list --upgradable 2>/dev/null | grep -c upgradable || echo "0")
  
  if [ "$UPDATES" -gt 0 ]; then
    echo "✗ WARNING: $UPDATES packages available for update"
    echo "Run: sudo apt upgrade -y"
  else
    echo "✓ System is up to date"
  fi
  
  # Check kernel version
  echo ""
  echo "Kernel version: $(uname -r)"
elif command -v yum &> /dev/null; then
  UPDATES=$(sudo yum check-update | wc -l)
  if [ "$UPDATES" -gt 1 ]; then
    echo "✗ WARNING: Updates available"
  else
    echo "✓ System is up to date"
  fi
fi

SSHEOF

# ============================================================================
# 5. USER AND PERMISSION AUDIT
# ============================================================================
log_header "USER AND PERMISSION AUDIT"

log_info "Checking user accounts and permissions..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "User Accounts Review:"
echo "===================="

# Check for users with UID 0 (root privileges)
echo "Accounts with UID 0:"
awk -F: '$3 == 0 {print $1}' /etc/passwd

# Check for empty password fields
echo ""
echo "Checking for accounts with empty passwords:"
awk -F: '($2 == "" || $2 == "!" || $2 == "!!") {print $1 " - " $2}' /etc/shadow | head -5 || echo "✓ No empty password fields found"

# Check sudo access
echo ""
echo "Users with sudo access:"
getent group sudo 2>/dev/null | cut -d: -f4 || echo "No sudo group members"

# Check for SUID binaries
echo ""
echo "SUID binaries (first 10):"
find /usr/bin /usr/sbin -perm -4000 2>/dev/null | head -10 || echo "None found"

SSHEOF

# ============================================================================
# 6. INSTALLED PACKAGES AUDIT
# ============================================================================
log_header "INSTALLED PACKAGES AUDIT"

log_info "Analyzing installed packages for known vulnerabilities..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Installed Packages Summary:"
echo "============================"

if command -v apt &> /dev/null; then
  PACKAGE_COUNT=$(dpkg -l | grep '^ii' | wc -l)
  echo "Total installed packages: $PACKAGE_COUNT"
  
  # Check for potentially risky packages
  echo ""
  echo "Checking for risky/unnecessary packages:"
  
  RISKY_PACKAGES=("telnet" "ftp" "rsh-client" "rsh-server" "nis")
  for pkg in "${RISKY_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $pkg "; then
      echo "✗ WARNING: Risky package installed: $pkg"
    fi
  done
  
  # Check for important security packages
  echo ""
  echo "Security tools installed:"
  SECURITY_TOOLS=("openssh-server" "fail2ban" "auditd" "aide")
  for tool in "${SECURITY_TOOLS[@]}"; do
    if dpkg -l | grep -q "^ii  $tool"; then
      echo "✓ $tool is installed"
    fi
  done
fi

SSHEOF

# ============================================================================
# 7. FILE SYSTEM INTEGRITY
# ============================================================================
log_header "FILE SYSTEM INTEGRITY CHECK"

log_info "Checking critical file system permissions..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Critical File Permissions:"
echo "=========================="

# Check critical files
FILES_TO_CHECK=(
  "/etc/passwd:644"
  "/etc/shadow:640"
  "/etc/group:644"
  "/etc/gshadow:640"
  "/etc/ssh/sshd_config:600"
  "/boot/grub/grub.cfg:600"
  "/root:.700"
)

for file_perm in "${FILES_TO_CHECK[@]}"; do
  FILE=$(echo "$file_perm" | cut -d: -f1)
  EXPECTED=$(echo "$file_perm" | cut -d: -f2)
  
  if [ -e "$FILE" ]; then
    ACTUAL=$(stat -c '%a' "$FILE" 2>/dev/null || stat -f '%OLp' "$FILE" 2>/dev/null | tail -c 3)
    if [ "$ACTUAL" = "$EXPECTED" ]; then
      echo "✓ $FILE has correct permissions ($EXPECTED)"
    else
      echo "✗ WARNING: $FILE has permissions $ACTUAL (expected $EXPECTED)"
    fi
  fi
done

SSHEOF

# ============================================================================
# 8. NETWORK SECURITY CHECK
# ============================================================================
log_header "NETWORK SECURITY CHECK"

log_info "Checking network configuration..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Network Configuration:"
echo "====================="

# Check for IPv6 if not needed
if ip addr show | grep -q "inet6"; then
  echo "⚠ IPv6 is enabled - ensure it's needed"
else
  echo "✓ IPv6 disabled (if not needed)"
fi

# Check IP forwarding
IP_FORWARD=$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo "1")
if [ "$IP_FORWARD" = "0" ]; then
  echo "✓ IP forwarding disabled"
else
  echo "⚠ WARNING: IP forwarding is enabled"
fi

# Check for listening services
echo ""
echo "Network services listening:"
sudo ss -tlnp 2>/dev/null | grep LISTEN | tail -10 || echo "Unable to list services"

SSHEOF

# ============================================================================
# 9. DOCKER SECURITY AUDIT
# ============================================================================
log_header "DOCKER SECURITY AUDIT"

log_info "Checking Docker installation and configuration..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Docker Configuration:"
echo "===================="

if command -v docker &> /dev/null; then
  echo "✓ Docker is installed"
  echo "Docker version: $(docker --version)"
  
  # Check if user is in docker group
  if groups | grep -q docker; then
    echo "⚠ WARNING: Current user in docker group (has root-like privileges)"
  fi
  
  # Check Docker daemon security options
  echo ""
  echo "Docker daemon info:"
  sudo docker info 2>/dev/null | grep -E "Security Options|Live Restore|Log Driver" || true
  
  # Check for insecure registries
  if sudo grep -q "insecure-registries" /etc/docker/daemon.json 2>/dev/null; then
    echo "✗ WARNING: Insecure Docker registries configured"
  else
    echo "✓ No insecure registries detected"
  fi
else
  echo "ℹ Docker is not installed on this system"
fi

SSHEOF

# ============================================================================
# 10. AUDIT LOG REVIEW
# ============================================================================
log_header "AUDIT LOG REVIEW"

log_info "Checking audit daemon and logs..."
ssh "$TARGET_USER@$TARGET_IP" << 'SSHEOF' >> "$SCAN_REPORT" 2>&1
echo "Audit System Status:"
echo "===================="

if command -v auditctl &> /dev/null; then
  if sudo systemctl is-active --quiet auditd; then
    echo "✓ Auditd is running"
    
    # Show recent suspicious activity
    echo ""
    echo "Recent failed login attempts:"
    sudo tail -20 /var/log/auth.log 2>/dev/null | grep -i "failed\|denied" | tail -5 || echo "None found"
    
    echo ""
    echo "Recent sudo usage:"
    sudo tail -10 /var/log/auth.log 2>/dev/null | grep sudo | tail -5 || echo "None found"
  else
    echo "✗ WARNING: Auditd is not running"
  fi
else
  echo "⚠ Auditd is not installed"
fi

# Check syslog for errors
echo ""
echo "Recent system errors (last 5):"
sudo tail -50 /var/log/syslog 2>/dev/null | grep -i "error\|critical" | tail -5 || echo "None found"

SSHEOF

# ============================================================================
# 11. SUMMARY AND RECOMMENDATIONS
# ============================================================================
log_header "SCAN SUMMARY AND RECOMMENDATIONS"

cat >> "$SCAN_REPORT" << EOF

╔════════════════════════════════════════════════════════════════╗
║                   REMEDIATION RECOMMENDATIONS                  ║
╚════════════════════════════════════════════════════════════════╝

IMMEDIATE ACTIONS (Critical):
  1. Run system updates: sudo apt update && sudo apt upgrade -y
  2. Ensure SSH key-based authentication is configured
  3. Verify firewall is ACTIVE and properly configured
  4. Check for exposed services and close unnecessary ports

HIGH PRIORITY:
  5. Review and harden SSH configuration (/etc/ssh/sshd_config)
  6. Enable and verify fail2ban is running
  7. Configure and enable auditd for comprehensive logging
  8. Set correct permissions on critical system files

MEDIUM PRIORITY:
  9. Review user accounts and remove unnecessary ones
  10. Check Docker security (if Docker is installed)
  11. Implement network segmentation if possible
  12. Enable SELinux or AppArmor if not already active

ONGOING MAINTENANCE:
  - Monitor audit logs regularly
  - Apply security patches promptly
  - Review SSH logs for unauthorized access attempts
  - Keep vulnerability scanning scripts up to date

HARDENING SCRIPT STATUS:
  - Run the full hardening script: bash harden.sh 10.0.0.84 wizardsofts apply
  - Check hardening status: bash scripts/06_security_tools.sh 10.0.0.84 wizardsofts check

╔════════════════════════════════════════════════════════════════╗
║                    END OF SCAN REPORT                          ║
╚════════════════════════════════════════════════════════════════╝

Generated: $(date '+%Y-%m-%d %H:%M:%S')
Scanner: Comprehensive Vulnerability Scan Script v1.0

EOF

log_header "SCAN COMPLETE"
log_pass "Vulnerability scan completed successfully"
log_info "Full report saved to: $SCAN_REPORT"
echo ""
echo "To view the complete report:"
echo "  cat $SCAN_REPORT"
echo ""
echo "To continue with hardening:"
echo "  source .env && source hardening/.env"
echo "  bash hardening/harden.sh 10.0.0.84 wizardsofts apply"

#!/bin/bash

################################################################################
# QUICK START GUIDE - SERVER HARDENING EXECUTION
################################################################################

# This file contains the essential commands to execute and verify hardening
# Copy and paste commands as needed

echo "=========================================="
echo "SERVER HARDENING - QUICK START REFERENCE"
echo "=========================================="
echo ""

# ============================================================================
# SECTION 1: PRE-EXECUTION VERIFICATION
# ============================================================================

echo "[1] VERIFY SSH CONNECTIVITY"
echo "Command: ssh -o ConnectTimeout=5 wizardsofts@10.0.0.84 'echo OK'"
echo ""

echo "[2] CREATE PRE-HARDENING BACKUP"
echo "Command: ssh wizardsofts@10.0.0.84 'sudo tar czf /tmp/pre_hardening_backup.tar.gz /etc /home /root /opt 2>/dev/null; ls -lh /tmp/pre_hardening_backup.tar.gz'"
echo ""

echo "[3] CHECK DISK SPACE"
echo "Command: ssh wizardsofts@10.0.0.84 'df -h / /tmp /var/tmp'"
echo ""

echo "[4] VERIFY TIME SYNC"
echo "Command: ssh wizardsofts@10.0.0.84 'timedatectl'"
echo ""

# ============================================================================
# SECTION 2: EXECUTION METHODS
# ============================================================================

echo "========== EXECUTION METHODS =========="
echo ""

echo "[METHOD 1] INTERACTIVE FULL EXECUTION (RECOMMENDED)"
echo "Command:"
echo "  ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'"
echo ""
echo "Expected: Interactive execution with password prompts, ~30-45 minutes"
echo ""

echo "[METHOD 2] AUTOMATED WITH NOPASSWD (LESS SECURE)"
echo "Step 1: Enable NOPASSWD (one-time, requires password)"
echo "  ssh -t wizardsofts@10.0.0.84 'echo \"wizardsofts ALL=(ALL) NOPASSWD: ALL\" | sudo tee -a /etc/sudoers.d/hardening'"
echo ""
echo "Step 2: Run hardening without password prompts"
echo "  ssh wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'"
echo ""

echo "[METHOD 3] PER-PHASE EXECUTION (FLEXIBLE)"
echo "Execute one phase at a time:"
echo "  bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts apply"
echo "  bash hardening/scripts/02_filesystem.sh 10.0.0.84 wizardsofts apply"
echo "  bash hardening/scripts/03_user_sudo.sh 10.0.0.84 wizardsofts apply"
echo "  bash hardening/scripts/04_services_docker.sh 10.0.0.84 wizardsofts apply"
echo "  bash hardening/scripts/05_kernel.sh 10.0.0.84 wizardsofts apply"
echo "  bash hardening/scripts/06_security_tools.sh 10.0.0.84 wizardsofts apply"
echo ""

# ============================================================================
# SECTION 3: DURING EXECUTION
# ============================================================================

echo "========== DURING EXECUTION =========="
echo ""

echo "[MONITOR LOGS REAL-TIME]"
echo "Command: ssh wizardsofts@10.0.0.84 'tail -f hardening/logs/10.0.0.84_*.log'"
echo ""

echo "[CHECK PROGRESS IN ANOTHER TERMINAL]"
echo "Command: ssh wizardsofts@10.0.0.84 'cat hardening/logs/10.0.0.84_progress_*.json | jq .'"
echo ""

# ============================================================================
# SECTION 4: POST-EXECUTION VERIFICATION
# ============================================================================

echo "========== POST-EXECUTION VERIFICATION =========="
echo ""

echo "[1] QUICK HEALTH CHECK"
echo "Command: ssh wizardsofts@10.0.0.84 'uptime && free -h && df -h / && systemctl status ssh fail2ban auditd --no-pager'"
echo ""

echo "[2] VERIFY SSH RESTRICTION TO LOCAL SUBNET"
echo "From internal (should work):"
echo "  ssh -o ConnectTimeout=5 wizardsofts@10.0.0.84 'echo SSH OK'"
echo ""
echo "From external (should timeout after 5 seconds):"
echo "  timeout 5 ssh external_ip@10.0.0.84 'echo test' 2>&1 | grep -i 'timeout\\|refused\\|connection'"
echo ""

echo "[3] CHECK FIREWALL RULES"
echo "Command: ssh wizardsofts@10.0.0.84 'sudo ufw status | head -15'"
echo ""

echo "[4] VERIFY FILE SYSTEM MOUNTS"
echo "Command: ssh wizardsofts@10.0.0.84 'mount | grep -E 'tmp|shm'"
echo ""

echo "[5] CHECK SECURITY TOOLS"
echo "Command: ssh wizardsofts@10.0.0.84 'sudo systemctl status fail2ban auditd --no-pager'"
echo ""

echo "[6] REVIEW LOGS"
echo "Command: ssh wizardsofts@10.0.0.84 'tail -50 hardening/logs/10.0.0.84_*.log | tail -50'"
echo ""

echo "[7] CHECK AUDIT LOG"
echo "Command: ssh wizardsofts@10.0.0.84 'sudo tail -20 /var/log/audit/audit.log 2>/dev/null'"
echo ""

echo "[8] CHECK FAIL2BAN STATUS"
echo "Command: ssh wizardsofts@10.0.0.84 'sudo fail2ban-client status ssh 2>/dev/null'"
echo ""

# ============================================================================
# SECTION 5: IF SOMETHING GOES WRONG
# ============================================================================

echo "========== TROUBLESHOOTING =========="
echo ""

echo "[CHECK EXECUTION STATUS]"
echo "Command: ssh wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts check'"
echo ""

echo "[VIEW DETAILED LOGS]"
echo "Command: ssh wizardsofts@10.0.0.84 'cat hardening/logs/10.0.0.84_*.log | tail -100'"
echo ""

echo "[VIEW PROGRESS JSON]"
echo "Command: ssh wizardsofts@10.0.0.84 'cat hardening/logs/10.0.0.84_progress_*.json'"
echo ""

echo "[ROLLBACK SINGLE PHASE]"
echo "Example (rollback phase 1):"
echo "  bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts rollback"
echo ""

echo "[ROLLBACK ALL PHASES]"
echo "Command: for i in 06 05 04 03 02 01; do bash hardening/scripts/0\${i}_*.sh 10.0.0.84 wizardsofts rollback; done"
echo ""

echo "[TEST ROLLBACK (NO ACTUAL CHANGES)]"
echo "Command: ssh wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts check'"
echo ""

# ============================================================================
# SECTION 6: DOCUMENTATION
# ============================================================================

echo "========== DOCUMENTATION =========="
echo ""
echo "📖 Quick Reference:         hardening/README.md"
echo "📖 Detailed Guide:          hardening/HANDOFF.md"
echo "📖 Infrastructure Summary:  hardening/INFRASTRUCTURE_SUMMARY.md"
echo "📊 Current Status:          hardening/IMPLEMENTATION_STATUS.json"
echo "⚙️  Server Config:           hardening/inventory/10.0.0.84.json"
echo ""

echo "=========================================="
echo "Ready to execute? Start with:"
echo "  ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'"
echo "=========================================="

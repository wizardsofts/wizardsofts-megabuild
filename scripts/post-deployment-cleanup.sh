#!/bin/bash
# Post-Deployment Cleanup Script
#
# MANDATORY cleanup after ANY infrastructure operation per AGENT.md §13.11
#
# Usage:
#   ./scripts/post-deployment-cleanup.sh <SERVER_IP> [--dry-run]
#
# Examples:
#   ./scripts/post-deployment-cleanup.sh 10.0.0.84
#   ./scripts/post-deployment-cleanup.sh 10.0.0.84 --dry-run
#
# Required:
#   - SSH access as agent user (passwordless sudo for docker)
#
# What it does:
#   1. Docker system prune (removes unused containers, images, volumes)
#   2. Drop system memory caches
#   3. Verify disk space
#   4. Check for large log files
#   5. Generate cleanup report

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
SERVER="${1:-}"
DRY_RUN="${2:-}"
SSH_USER="agent"
REPORT_FILE="/tmp/cleanup-report-$(date +%Y%m%d-%H%M%S).txt"

usage() {
  cat << EOF
Post-Deployment Cleanup Script (AGENT.md §13.11)

Usage:
  $0 <SERVER_IP> [--dry-run]

Arguments:
  SERVER_IP   Target server IP (e.g., 10.0.0.84)
  --dry-run   Show what would be cleaned without executing

Examples:
  $0 10.0.0.84
  $0 10.0.0.84 --dry-run

Cleanup Operations:
  ✓ Docker system prune (containers, images, volumes)
  ✓ Drop system memory caches
  ✓ Verify disk space
  ✓ Check for large log files (>100MB)
  ✓ Generate cleanup report

EOF
  exit 1
}

if [[ -z "${SERVER}" ]] || [[ "${SERVER}" == "--help" ]]; then
  usage
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Post-Deployment Cleanup (AGENT.md §13.11)            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Target Server: ${SERVER}${NC}"
echo -e "${YELLOW}SSH User: ${SSH_USER}${NC}"

if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  echo -e "${YELLOW}Mode: DRY RUN (no changes will be made)${NC}"
else
  echo -e "${GREEN}Mode: EXECUTE${NC}"
fi

echo ""

# Check SSH connectivity
echo -e "${YELLOW}Checking SSH connectivity...${NC}"
if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "${SSH_USER}@${SERVER}" "echo ok" >/dev/null 2>&1; then
  echo -e "${RED}✗ SSH to ${SSH_USER}@${SERVER} failed${NC}"
  echo "Ensure SSH keys are configured and agent user has access"
  exit 1
fi
echo -e "${GREEN}✓ SSH connectivity verified${NC}"
echo ""

# Collect before-cleanup metrics
echo -e "${YELLOW}Collecting pre-cleanup metrics...${NC}"

DISK_BEFORE=$(ssh "${SSH_USER}@${SERVER}" "df -h / | tail -1" || echo "N/A")
DOCKER_USAGE_BEFORE=$(ssh "${SSH_USER}@${SERVER}" "sudo docker system df" 2>/dev/null || echo "N/A")

echo "Disk usage before:"
echo "${DISK_BEFORE}"
echo ""
echo "Docker usage before:"
echo "${DOCKER_USAGE_BEFORE}"
echo ""

if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  echo -e "${YELLOW}=== DRY RUN MODE ===${NC}"
  echo "Would execute the following:"
  echo "  1. sudo docker system prune -af --volumes"
  echo "  2. sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches"
  echo "  3. df -h"
  echo "  4. find /var/log -type f -size +100M"
  echo ""
  echo "Run without --dry-run to execute cleanup"
  exit 0
fi

# 1. Docker system prune
echo -e "${YELLOW}Step 1/4: Docker system prune${NC}"
echo "This will remove:"
echo "  - All stopped containers"
echo "  - All unused networks"
echo "  - All dangling images"
echo "  - All unused volumes"
echo ""

PRUNE_OUTPUT=$(ssh "${SSH_USER}@${SERVER}" "sudo docker system prune -af --volumes 2>&1" || echo "Failed")

if echo "${PRUNE_OUTPUT}" | grep -qi "failed"; then
  echo -e "${RED}✗ Docker prune failed${NC}"
  echo "${PRUNE_OUTPUT}"
  exit 1
else
  echo -e "${GREEN}✓ Docker system pruned${NC}"

  # Extract freed space from output
  FREED_SPACE=$(echo "${PRUNE_OUTPUT}" | grep -i "Total reclaimed space" || echo "Unknown")
  echo "${FREED_SPACE}"
fi
echo ""

# 2. Drop memory caches
echo -e "${YELLOW}Step 2/4: Drop system memory caches${NC}"

CACHE_OUTPUT=$(ssh "${SSH_USER}@${SERVER}" "sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches" 2>&1 || echo "Failed")

if echo "${CACHE_OUTPUT}" | grep -qi "failed"; then
  echo -e "${RED}✗ Cache drop failed${NC}"
  echo "${CACHE_OUTPUT}"
else
  echo -e "${GREEN}✓ Memory caches dropped${NC}"
fi
echo ""

# 3. Verify disk space after cleanup
echo -e "${YELLOW}Step 3/4: Verify disk space after cleanup${NC}"

DISK_AFTER=$(ssh "${SSH_USER}@${SERVER}" "df -h / | tail -1" || echo "N/A")

echo "Disk usage after:"
echo "${DISK_AFTER}"
echo ""

# 4. Check for large log files
echo -e "${YELLOW}Step 4/4: Check for large log files (>100MB)${NC}"

LARGE_LOGS=$(ssh "${SSH_USER}@${SERVER}" "find /var/log -type f -size +100M 2>/dev/null || echo 'No large logs found'" || echo "Failed to check")

if [[ "${LARGE_LOGS}" == "No large logs found" ]]; then
  echo -e "${GREEN}✓ No large log files (>100MB)${NC}"
else
  echo -e "${YELLOW}⚠ Large log files found:${NC}"
  echo "${LARGE_LOGS}"
  echo ""
  echo "Consider rotating logs: sudo logrotate -f /etc/logrotate.conf"
fi
echo ""

# Generate cleanup report
echo -e "${YELLOW}Generating cleanup report...${NC}"

cat > "${REPORT_FILE}" << EOREPORT
Post-Deployment Cleanup Report
Generated: $(date)
Server: ${SERVER}

=== BEFORE CLEANUP ===

${DISK_BEFORE}

Docker Usage:
${DOCKER_USAGE_BEFORE}

=== CLEANUP OPERATIONS ===

1. Docker System Prune: EXECUTED
   ${FREED_SPACE}

2. Memory Cache Drop: EXECUTED

3. Large Log Files Check: EXECUTED
   ${LARGE_LOGS}

=== AFTER CLEANUP ===

${DISK_AFTER}

Docker Usage (after):
$(ssh "${SSH_USER}@${SERVER}" "sudo docker system df" 2>/dev/null || echo "N/A")

=== SUMMARY ===

BEFORE:
$(echo "${DISK_BEFORE}" | awk '{print "  Disk: " $3 " used, " $4 " free (" $5 " usage)"}')

AFTER:
$(echo "${DISK_AFTER}" | awk '{print "  Disk: " $3 " used, " $4 " free (" $5 " usage)"}')

EOREPORT

echo -e "${GREEN}✓ Report saved to: ${REPORT_FILE}${NC}"
echo ""

# Display summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Cleanup Complete!                             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Summary:"
echo "${FREED_SPACE}"
echo ""
echo "Before:"
echo "${DISK_BEFORE}" | awk '{print "  Disk: " $3 " used, " $4 " free (" $5 " usage)"}'
echo ""
echo "After:"
echo "${DISK_AFTER}" | awk '{print "  Disk: " $3 " used, " $4 " free (" $5 " usage)"}'
echo ""
echo "Full report: ${REPORT_FILE}"
echo ""
echo "Next steps:"
echo "  1. Review cleanup report"
echo "  2. Document in handoff (copy ${REPORT_FILE} to handoff folder)"
echo "  3. Monitor server for any issues"

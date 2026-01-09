#!/bin/bash
# GitLab Upgrade - Phase 0: Pre-flight + Backup (SSH: agent)
#
# This script performs ground-truth checks and creates a fresh GitLab backup
# on the NFS path before the upgrade. It connects to the target host via SSH
# using the 'agent' user defined in AGENT.md.
#
# Usage:
#   SUDO_PASSWORD='<remote-sudo-pass>' ./scripts/gitlab-upgrade-phase0.sh
#
# Optional env vars:
#   HOST=10.0.0.84
#   NFS_SERVER=10.0.0.80
#   SSH_USER_AGENT=agent
#   DB_HOST=10.0.0.80
#   DB_PORT=5435
#   REDIS_HOST=10.0.0.80
#   REDIS_PORT=6380
#   BACKUP_DIR=/mnt/data/Backups/server/gitlab
#   LOG_REMOTE=/tmp/gitlab-phase0-$(date +%Y%m%d-%H%M%S).log
#
# Requirements on remote:
#   - docker available (GitLab container named 'gitlab')
#   - sudo available
#   - NFS /mnt/data mounted (contains Backups/server/gitlab)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Config
HOST="${HOST:-10.0.0.84}"
NFS_SERVER="${NFS_SERVER:-10.0.0.80}"
SSH_USER_AGENT="${SSH_USER_AGENT:-agent}"
DB_HOST="${DB_HOST:-10.0.0.80}"
DB_PORT="${DB_PORT:-5435}"
REDIS_HOST="${REDIS_HOST:-10.0.0.80}"
REDIS_PORT="${REDIS_PORT:-6380}"
BACKUP_DIR="${BACKUP_DIR:-/mnt/data/Backups/server/gitlab}"
LOG_REMOTE="${LOG_REMOTE:-/tmp/gitlab-phase0-$(date +%Y%m%d-%H%M%S).log}"

# Note: agent user has passwordless sudo for docker commands
# SUDO_PASSWORD not required

# Basic SSH check
if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "${SSH_USER_AGENT}@${HOST}" "echo ok" >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} SSH to ${SSH_USER_AGENT}@${HOST} failed. Ensure keys and access are configured." 1>&2
  exit 1
fi

echo -e "${YELLOW}Running Phase 0 pre-flight and backup on ${HOST} as ${SSH_USER_AGENT}...${NC}"

ssh "${SSH_USER_AGENT}@${HOST}" bash -s << 'EOSSH'
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Receive variables from outer scope by re-defining them via heredoc injections below
EOSSH

# Re-open SSH and inject variables into remote shell safely
ssh "${SSH_USER_AGENT}@${HOST}" bash -s << EOSSH
set -euo pipefail

# Color codes for remote shell
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# SUDO_PASSWORD removed - agent user has passwordless sudo
HOST="$HOST"
NFS_SERVER="$NFS_SERVER"
DB_HOST="$DB_HOST"
DB_PORT="$DB_PORT"
REDIS_HOST="$REDIS_HOST"
REDIS_PORT="$REDIS_PORT"
BACKUP_DIR="$BACKUP_DIR"
LOG_REMOTE="$LOG_REMOTE"

exec > >(tee -a "\${LOG_REMOTE}") 2>&1

echo -e "\${YELLOW}=== Phase 0: Ground Truth & Backup (\$(date)) ===\${NC}"

# 1) Ground truth: mounts and directories
if mount | grep -q "\${NFS_SERVER}:/mnt/data"; then
  echo -e "\${GREEN}✓ NFS mount for /mnt/data detected from \${NFS_SERVER}\${NC}"
else
  echo -e "\${RED}✗ NFS mount not detected for /mnt/data from \${NFS_SERVER}\${NC}"
  echo "Run setup_nfs_client84.sh and verify mounts before proceeding."
  exit 1
fi

if [[ -d "\${BACKUP_DIR}" ]]; then
  echo -e "\${GREEN}✓ Backup directory exists: \${BACKUP_DIR}\${NC}"
else
  echo -e "\${RED}✗ Backup directory missing: \${BACKUP_DIR}\${NC}"
  exit 1
fi

# Check write permission to backup dir
if sudo bash -lc "touch '\${BACKUP_DIR}/.__write_test' && rm -f '\${BACKUP_DIR}/.__write_test'"; then
  echo -e "\${GREEN}✓ Backup directory is writable\${NC}"
else
  echo -e "\${RED}✗ Backup directory not writable; check NFS permissions\${NC}"
  exit 1
fi

# 2) Connectivity to external services
if timeout 5 bash -c "</dev/tcp/\${DB_HOST}/\${DB_PORT}" 2>/dev/null; then
  echo -e "\${GREEN}✓ PostgreSQL reachable at \${DB_HOST}:\${DB_PORT}\${NC}"
else
  echo -e "\${RED}✗ Cannot reach PostgreSQL at \${DB_HOST}:\${DB_PORT}\${NC}"
  exit 1
fi

if timeout 5 bash -c "</dev/tcp/\${REDIS_HOST}/\${REDIS_PORT}" 2>/dev/null; then
  echo -e "\${GREEN}✓ Redis reachable at \${REDIS_HOST}:\${REDIS_PORT}\${NC}"
else
  echo -e "\${RED}✗ Cannot reach Redis at \${REDIS_HOST}:\${REDIS_PORT}\${NC}"
  exit 1
fi

# 3) Trigger GitLab backup inside container
echo -e "\${YELLOW}Creating GitLab backup (this may take a while)...\${NC}"
if sudo docker exec -t gitlab gitlab-backup create; then
  echo -e "\${GREEN}✓ Backup command completed\${NC}"
else
  echo -e "\${RED}✗ GitLab backup command failed\${NC}"
  exit 1
fi

# 4) Verify backup artifacts are recent (check inside container)
recent_file=\$(sudo docker exec gitlab find /var/opt/gitlab/backups -type f -name "*_gitlab_backup.tar" -mmin -10 2>/dev/null | head -1 || true)
if [[ -n "\${recent_file}" ]]; then
  echo -e "\${GREEN}✓ Recent backup found: \${recent_file}\${NC}"
else
  echo -e "\${RED}✗ No recent backup (.tar) found in last 10 minutes inside GitLab container\${NC}"
  exit 1
fi

echo -e "\${GREEN}=== Phase 0 complete. Log: \${LOG_REMOTE} ===\${NC}"
EOSSH

echo -e "${GREEN}Phase 0 finished successfully.${NC}"
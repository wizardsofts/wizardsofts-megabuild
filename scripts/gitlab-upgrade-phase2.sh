#!/bin/bash
# GitLab Upgrade - Phase 2: Deploy updated container (SSH: deploy)
#
# This script syncs the repository to the target host and updates ONLY the
# GitLab service using the compose file at infrastructure/gitlab/docker-compose.yml.
# It uses the 'deploy' user (AGENT.md) and requires sudo for docker.
#
# NOTE: CI/CD-only deployments are preferred. This script acts as an operator
# fallback to execute the same steps in a controlled manner if CI trigger is
# not available. Ensure change control is followed.
#
# Usage:
#   SUDO_PASSWORD='<remote-sudo-pass>' ./scripts/gitlab-upgrade-phase2.sh
#
# Optional env vars:
#   HOST=10.0.0.84
#   SSH_USER_AGENT=deploy
#   DEPLOY_PATH=/opt/wizardsofts-megabuild
#   COMPOSE_FILE=infrastructure/gitlab/docker-compose.yml

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

HOST="${HOST:-10.0.0.84}"
SSH_USER_AGENT="${SSH_USER_AGENT:-agent}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/wizardsofts-megabuild}"
COMPOSE_FILE="${COMPOSE_FILE:-infrastructure/gitlab/docker-compose.yml}"

# Note: agent user has passwordless sudo for docker commands
# SUDO_PASSWORD not required

# Check SSH connectivity
if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "${SSH_USER_AGENT}@${HOST}" "echo ok" >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} SSH to ${SSH_USER_AGENT}@${HOST} failed. Ensure keys and access are configured." 1>&2
  exit 1
fi

echo -e "${YELLOW}Syncing repository and updating GitLab service on ${HOST}...${NC}"

# Rsync repository (respect existing exclusions similar to deploy-to-84.sh)
rsync -avz --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'target' \
  --exclude '.m2' \
  --exclude '.cache' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --progress \
  ./ "${SSH_USER_AGENT}@${HOST}:${DEPLOY_PATH}/"

echo -e "${GREEN}✓ Files synced${NC}"

echo -e "${YELLOW}Applying GitLab service update...${NC}"
ssh "${SSH_USER_AGENT}@${HOST}" bash -s << EOSSH
set -euo pipefail

# SUDO_PASSWORD removed - agent user has passwordless sudo
DEPLOY_PATH="$DEPLOY_PATH"
COMPOSE_FILE="$COMPOSE_FILE"

cd "\${DEPLOY_PATH}"

# Pull updated image(s) for gitlab service
if sudo docker compose -f "\${COMPOSE_FILE}" pull gitlab; then
  echo "Pulled latest image for gitlab"
else
  echo "Failed to pull image(s) for gitlab" >&2
  exit 1
fi

# Restart/update only 'gitlab' service
if sudo docker compose -f "\${COMPOSE_FILE}" up -d gitlab; then
  echo "GitLab service started"
else
  echo "Failed to start GitLab service" >&2
  exit 1
fi

# Wait for health
sleep 20

# Verify health
if docker ps --format '{{.Names}} {{.Status}}' | grep -E '^gitlab ' | grep -qi 'healthy\|up'; then
  echo "GitLab container reports healthy/up"
else
  echo "GitLab container not healthy yet; printing last 100 lines of logs:" >&2
  docker logs --tail 100 gitlab || true
  exit 1
fi

# Print version for confirmation
if docker exec gitlab gitlab-rake gitlab:env:info 2>/dev/null | grep -i '^GitLab' -A1; then
  echo "Captured GitLab env info"
else
  echo "Warning: could not capture gitlab:env:info" >&2
fi

EOSSH

echo -e "${GREEN}Phase 2 completed: GitLab service updated on ${HOST}.${NC}"
#!/bin/bash
# GitLab Upgrade - Phase 3: Post-upgrade verification (SSH: agent)
#
# This script verifies the GitLab service after the upgrade. It checks
# health endpoints, container health, GitLab version, ports, and runs the
# repo-provided gitlab-integration-test.sh on the remote host.
#
# Usage:
#   ./scripts/gitlab-upgrade-phase3.sh
#
# Optional env vars:
#   HOST=10.0.0.84
#   SSH_USER_AGENT=agent
#   DEPLOY_PATH=/opt/wizardsofts-megabuild
#   GITLAB_URL=http://10.0.0.84:8090

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

HOST="${HOST:-10.0.0.84}"
SSH_USER_AGENT="${SSH_USER_AGENT:-agent}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/wizardsofts-megabuild}"
GITLAB_URL="${GITLAB_URL:-http://10.0.0.84:8090}"

# Check SSH connectivity
if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "${SSH_USER_AGENT}@${HOST}" "echo ok" >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} SSH to ${SSH_USER_AGENT}@${HOST} failed. Ensure keys and access are configured." 1>&2
  exit 1
fi

echo -e "${YELLOW}Verifying GitLab post-upgrade on ${HOST}...${NC}"

# 1) Quick health checks
if ssh "${SSH_USER_AGENT}@${HOST}" "curl -fsS ${GITLAB_URL}/-/health >/dev/null"; then
  echo -e "${GREEN}✓ GitLab health endpoint OK${NC}"
else
  echo -e "${RED}✗ GitLab health endpoint failed${NC}"
  exit 1
fi

# 2) Container health & version
if ssh "${SSH_USER_AGENT}@${HOST}" "docker ps --format '{{.Names}} {{.Status}}' | grep -E '^gitlab ' | grep -qi 'healthy|up'"; then
  echo -e "${GREEN}✓ GitLab container healthy/up${NC}"
else
  echo -e "${RED}✗ GitLab container not healthy${NC}"
  ssh "${SSH_USER_AGENT}@${HOST}" "docker logs --tail 100 gitlab || true"
  exit 1
fi

# Capture version
if ssh "${SSH_USER_AGENT}@${HOST}" "docker exec gitlab gitlab-rake gitlab:env:info 2>/dev/null | grep -i '^GitLab' -A1"; then
  echo -e "${GREEN}✓ Retrieved GitLab version info${NC}"
else
  echo -e "${YELLOW}! Unable to retrieve version info (non-fatal)${NC}"
fi

# 3) Ports availability
for p in 8090 2222 5050; do
  if ssh "${SSH_USER_AGENT}@${HOST}" "timeout 5 bash -c '</dev/tcp/127.0.0.1/${p}'" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Port ${p} reachable on host${NC}"
  else
    echo -e "${YELLOW}! Port ${p} not reachable locally (check Traefik/firewall)${NC}"
  fi
done

# 4) Run integration test suite from repo (remote)
if ssh "${SSH_USER_AGENT}@${HOST}" "bash -lc 'cd ${DEPLOY_PATH} && chmod +x ./scripts/gitlab-integration-test.sh && ./scripts/gitlab-integration-test.sh'"; then
  echo -e "${GREEN}✓ Integration tests passed${NC}"
else
  echo -e "${RED}✗ Integration tests failed - see remote logs under /tmp and /var/log/gitlab-integration-tests${NC}"
  exit 1
fi

echo -e "${GREEN}Phase 3 verification complete. GitLab looks healthy.${NC}"
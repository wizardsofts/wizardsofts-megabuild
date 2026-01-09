#!/bin/bash
# GitLab Upgrade Orchestrator - CI/CD First Approach
#
# This script orchestrates the GitLab upgrade using CI/CD pipelines where possible,
# with manual SSH fallback only when explicitly requested.
#
# Usage:
#   ./scripts/gitlab-upgrade-orchestrator.sh [--use-cicd|--use-ssh-fallback]
#
# Environment variables:
#   GITLAB_TOKEN - GitLab API token with api scope (required for CI/CD mode)
#   SUDO_PASSWORD - Remote sudo password (required for SSH fallback mode)
#   GITLAB_API_URL - GitLab API endpoint (default: http://10.0.0.84:8090/api/v4)
#   GITLAB_PROJECT_ID - Project ID for pipeline trigger (default: auto-detect)
#   HOST - Target host (default: 10.0.0.84)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
MODE="${1:-}"
GITLAB_API_URL="${GITLAB_API_URL:-http://10.0.0.84:8090/api/v4}"
HOST="${HOST:-10.0.0.84}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat << EOF
GitLab Upgrade Orchestrator

Usage:
  $0 [MODE]

Modes:
  --use-cicd          Trigger GitLab CI/CD pipeline (RECOMMENDED, AGENT.md compliant)
  --use-ssh-fallback  Use direct SSH scripts (fallback only, requires justification)
  --help              Show this help

CI/CD Mode (Recommended):
  Requires GITLAB_TOKEN environment variable with api scope.
  Creates a pipeline variable GITLAB_UPGRADE=true and triggers deployment.
  
  Example:
    GITLAB_TOKEN='glpat-xxxx' $0 --use-cicd

SSH Fallback Mode:
  Only use when CI/CD is unavailable or broken. Document reason in session notes.
  Requires SUDO_PASSWORD environment variable.
  
  Example:
    SUDO_PASSWORD='xxxx' $0 --use-ssh-fallback

EOF
  exit 0
}

if [[ "${MODE}" == "--help" || -z "${MODE}" ]]; then
  usage
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         GitLab Upgrade to 18.7.1 - Orchestrator               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Phase 0: Always run preflight via SSH (read-only checks)
run_phase0() {
  echo -e "${YELLOW}Phase 0: Pre-flight checks + Backup${NC}"
  echo "Running ground-truth validation and backup creation..."

  # Note: agent user has passwordless sudo for docker commands

  if ! bash "${SCRIPT_DIR}/gitlab-upgrade-phase0.sh"; then
    echo -e "${RED}Phase 0 failed. Aborting upgrade.${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ Phase 0 complete${NC}"
  echo ""
}

# Phase 2: CI/CD mode
run_phase2_cicd() {
  echo -e "${YELLOW}Phase 2: Deploy via CI/CD Pipeline${NC}"
  
  if [[ -z "${GITLAB_TOKEN:-}" ]]; then
    echo -e "${RED}Error: GITLAB_TOKEN required for CI/CD mode${NC}"
    echo "Generate token at: ${GITLAB_API_URL%/api/v4}/-/profile/personal_access_tokens"
    echo "Required scopes: api, read_repository, write_repository"
    exit 1
  fi
  
  # Auto-detect project ID if not set
  if [[ -z "${GITLAB_PROJECT_ID:-}" ]]; then
    echo "Auto-detecting GitLab project ID..."
    PROJECT_PATH="wizardsofts-megabuild"
    GITLAB_PROJECT_ID=$(curl -sSf -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
      "${GITLAB_API_URL}/projects?search=${PROJECT_PATH}" | \
      jq -r '.[0].id' 2>/dev/null || echo "")
    
    if [[ -z "${GITLAB_PROJECT_ID}" ]]; then
      echo -e "${RED}Could not auto-detect project ID. Set GITLAB_PROJECT_ID manually.${NC}"
      exit 1
    fi
    echo "Detected project ID: ${GITLAB_PROJECT_ID}"
  fi
  
  # Create pipeline with upgrade trigger variable
  echo "Triggering GitLab CI/CD pipeline for upgrade..."
  PIPELINE_RESPONSE=$(curl -sSf -X POST \
    -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
    -F "ref=main" \
    -F "variables[GITLAB_UPGRADE]=true" \
    -F "variables[TARGET_SERVICE]=gitlab" \
    -F "variables[GITLAB_VERSION]=18.7.1-ce.0" \
    "${GITLAB_API_URL}/projects/${GITLAB_PROJECT_ID}/pipeline" || echo "")
  
  if [[ -z "${PIPELINE_RESPONSE}" ]]; then
    echo -e "${RED}Failed to trigger pipeline via API${NC}"
    exit 1
  fi
  
  PIPELINE_ID=$(echo "${PIPELINE_RESPONSE}" | jq -r '.id' 2>/dev/null || echo "")
  PIPELINE_URL=$(echo "${PIPELINE_RESPONSE}" | jq -r '.web_url' 2>/dev/null || echo "")
  
  if [[ -n "${PIPELINE_ID}" ]]; then
    echo -e "${GREEN}✓ Pipeline triggered: ID ${PIPELINE_ID}${NC}"
    echo "Monitor at: ${PIPELINE_URL}"
    echo ""
    echo "Waiting for pipeline completion (timeout: 30 minutes)..."
    
    # Poll pipeline status
    TIMEOUT=1800
    ELAPSED=0
    while [[ ${ELAPSED} -lt ${TIMEOUT} ]]; do
      sleep 15
      ELAPSED=$((ELAPSED + 15))
      
      STATUS=$(curl -sSf -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
        "${GITLAB_API_URL}/projects/${GITLAB_PROJECT_ID}/pipelines/${PIPELINE_ID}" | \
        jq -r '.status' 2>/dev/null || echo "unknown")
      
      case "${STATUS}" in
        success)
          echo -e "${GREEN}✓ Pipeline completed successfully${NC}"
          return 0
          ;;
        failed)
          echo -e "${RED}✗ Pipeline failed. Check logs at: ${PIPELINE_URL}${NC}"
          exit 1
          ;;
        canceled)
          echo -e "${RED}✗ Pipeline was canceled${NC}"
          exit 1
          ;;
        running|pending)
          echo -ne "\rPipeline status: ${STATUS} (${ELAPSED}s elapsed)..."
          ;;
        *)
          echo -e "\n${YELLOW}Unknown pipeline status: ${STATUS}${NC}"
          ;;
      esac
    done
    
    echo -e "\n${RED}Timeout waiting for pipeline${NC}"
    exit 1
  else
    echo -e "${RED}Failed to parse pipeline response${NC}"
    exit 1
  fi
}

# Phase 2: SSH fallback mode
run_phase2_ssh() {
  echo -e "${YELLOW}Phase 2: Deploy via SSH (Fallback Mode)${NC}"
  echo -e "${RED}WARNING: Using SSH fallback bypasses CI/CD audit trail${NC}"
  echo "Document reason in session notes per AGENT.md §13.1"
  echo ""

  # Note: agent user has passwordless sudo for docker commands

  read -p "Confirm SSH fallback deployment? (yes/no): " confirm
  if [[ "${confirm}" != "yes" ]]; then
    echo "Aborted."
    exit 1
  fi

  if ! bash "${SCRIPT_DIR}/gitlab-upgrade-phase2.sh"; then
    echo -e "${RED}Phase 2 SSH deployment failed${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ Phase 2 complete (SSH mode)${NC}"
  echo ""
}

# Phase 3: Post-upgrade verification
run_phase3() {
  echo -e "${YELLOW}Phase 3: Post-upgrade verification${NC}"
  
  if ! bash "${SCRIPT_DIR}/gitlab-upgrade-phase3.sh"; then
    echo -e "${RED}Phase 3 verification failed${NC}"
    echo "GitLab may be unhealthy. Check logs and consider rollback."
    exit 1
  fi
  
  echo -e "${GREEN}✓ Phase 3 complete${NC}"
  echo ""
}

# Main execution
main() {
  case "${MODE}" in
    --use-cicd)
      echo -e "${GREEN}Mode: CI/CD Pipeline (AGENT.md compliant)${NC}"
      echo ""
      run_phase0
      run_phase2_cicd
      run_phase3
      ;;
    --use-ssh-fallback)
      echo -e "${YELLOW}Mode: SSH Fallback (document reason)${NC}"
      echo ""
      run_phase0
      run_phase2_ssh
      run_phase3
      ;;
    *)
      echo -e "${RED}Invalid mode: ${MODE}${NC}"
      usage
      ;;
  esac
  
  echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║           GitLab Upgrade Complete!                            ║${NC}"
  echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Monitor GitLab at http://${HOST}:8090"
  echo "2. Update session handoff: docs/handoffs/2026-01-09-gitlab-upgrade/"
  echo "3. Move logs from /tmp to handoff folder"
  echo "4. Verify all integrations working"
}

main

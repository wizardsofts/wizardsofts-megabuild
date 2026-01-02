#!/bin/bash
# Main Hardening Orchestrator
# Executes all phases sequentially with progress tracking

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_IP="${1:-10.0.0.84}"
TARGET_USER="${2:-wizardsofts}"
MODE="${3:-apply}"  # apply, check, or rollback
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Progress tracking
PROGRESS_FILE="$SCRIPT_DIR/logs/${TARGET_IP}_progress_${TIMESTAMP}.json"
LOG_FILE="$SCRIPT_DIR/logs/${TARGET_IP}_${TIMESTAMP}.log"

# Initialize directories
mkdir -p "$(dirname "$PROGRESS_FILE")"

# Log to file
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# Initialize progress JSON
init_progress() {
  cat > "$PROGRESS_FILE" << 'EOF'
{
  "server": "10.0.0.84",
  "timestamp": "TIMESTAMP",
  "mode": "apply",
  "status": "in_progress",
  "phases": {
    "phase_1_ssh_network": {"status": "pending", "tasks": ["N1", "N2"]},
    "phase_2_filesystem": {"status": "pending", "tasks": ["F1", "F2"]},
    "phase_3_user_sudo": {"status": "pending", "tasks": ["U1", "U2"]},
    "phase_4_services_docker": {"status": "pending", "tasks": ["S1", "D1"]},
    "phase_5_kernel": {"status": "pending", "tasks": ["K1", "K2"]},
    "phase_6_security_tools": {"status": "pending", "tasks": ["T1", "T2", "T3"]}
  },
  "summary": {
    "total_tasks": 14,
    "completed": 0,
    "failed": 0,
    "skipped": 0
  }
}
EOF
}

# Update phase status
update_phase() {
  local phase="$1"
  local status="$2"
  # In production, use jq to update JSON
  sed -i "s/\"$phase\": {\"status\": \"[^\"]*\"/\"$phase\": {\"status\": \"$status\"/" "$PROGRESS_FILE" 2>/dev/null || true
}

# Main orchestration
main() {
  echo -e "${BLUE}========================================${NC}"
  echo -e "${BLUE}Server Hardening Orchestrator${NC}"
  echo -e "${BLUE}========================================${NC}"
  echo ""
  echo -e "Server: ${YELLOW}$TARGET_IP${NC}"
  echo -e "User: ${YELLOW}$TARGET_USER${NC}"
  echo -e "Mode: ${YELLOW}$MODE${NC}"
  echo -e "Timestamp: ${YELLOW}$TIMESTAMP${NC}"
  echo -e "Log: ${YELLOW}$LOG_FILE${NC}"
  echo -e "Progress: ${YELLOW}$PROGRESS_FILE${NC}"
  echo ""

  init_progress

  # Validate SSH connection
  echo -e "${BLUE}[PRE-FLIGHT]${NC} Validating SSH connection..."
  if ! ssh -o ConnectTimeout=5 "$TARGET_USER@$TARGET_IP" "echo 'SSH OK'" > /dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} Cannot connect to $TARGET_USER@$TARGET_IP"
    exit 1
  fi
  echo -e "${GREEN}[OK]${NC} SSH connection established"
  echo ""

  # Phase 1: SSH & Network
  echo -e "${BLUE}[PHASE 1]${NC} SSH & Network Hardening..."
  update_phase "phase_1_ssh_network" "in_progress"
  if bash "$SCRIPT_DIR/scripts/01_ssh_network.sh" "$TARGET_IP" "$TARGET_USER" "$MODE"; then
    echo -e "${GREEN}[PHASE 1 OK]${NC}"
    update_phase "phase_1_ssh_network" "success"
  else
    echo -e "${RED}[PHASE 1 FAILED]${NC}"
    update_phase "phase_1_ssh_network" "failed"
    [[ "$MODE" != "check" ]] && exit 1
  fi
  echo ""

  # Phase 2: File System
  echo -e "${BLUE}[PHASE 2]${NC} File System Hardening..."
  update_phase "phase_2_filesystem" "in_progress"
  if bash "$SCRIPT_DIR/scripts/02_filesystem.sh" "$TARGET_IP" "$TARGET_USER" "$MODE"; then
    echo -e "${GREEN}[PHASE 2 OK]${NC}"
    update_phase "phase_2_filesystem" "success"
  else
    echo -e "${RED}[PHASE 2 FAILED]${NC}"
    update_phase "phase_2_filesystem" "failed"
    [[ "$MODE" != "check" ]] && exit 1
  fi
  echo ""

  # Phase 3: User & Sudo
  echo -e "${BLUE}[PHASE 3]${NC} User & Sudo Hardening..."
  update_phase "phase_3_user_sudo" "in_progress"
  if bash "$SCRIPT_DIR/scripts/03_user_sudo.sh" "$TARGET_IP" "$TARGET_USER" "$MODE"; then
    echo -e "${GREEN}[PHASE 3 OK]${NC}"
    update_phase "phase_3_user_sudo" "success"
  else
    echo -e "${RED}[PHASE 3 FAILED]${NC}"
    update_phase "phase_3_user_sudo" "failed"
    [[ "$MODE" != "check" ]] && exit 1
  fi
  echo ""

  # Phase 4: Services & Docker
  echo -e "${BLUE}[PHASE 4]${NC} Services & Docker Hardening..."
  update_phase "phase_4_services_docker" "in_progress"
  if bash "$SCRIPT_DIR/scripts/04_services_docker.sh" "$TARGET_IP" "$TARGET_USER" "$MODE"; then
    echo -e "${GREEN}[PHASE 4 OK]${NC}"
    update_phase "phase_4_services_docker" "success"
  else
    echo -e "${RED}[PHASE 4 FAILED]${NC}"
    update_phase "phase_4_services_docker" "failed"
    [[ "$MODE" != "check" ]] && exit 1
  fi
  echo ""

  # Phase 5: Kernel
  echo -e "${BLUE}[PHASE 5]${NC} Kernel Hardening..."
  update_phase "phase_5_kernel" "in_progress"
  if bash "$SCRIPT_DIR/scripts/05_kernel.sh" "$TARGET_IP" "$TARGET_USER" "$MODE"; then
    echo -e "${GREEN}[PHASE 5 OK]${NC}"
    update_phase "phase_5_kernel" "success"
  else
    echo -e "${RED}[PHASE 5 FAILED]${NC}"
    update_phase "phase_5_kernel" "failed"
    [[ "$MODE" != "check" ]] && exit 1
  fi
  echo ""

  # Phase 6: Security Tools
  echo -e "${BLUE}[PHASE 6]${NC} Security Tools & Monitoring..."
  update_phase "phase_6_security_tools" "in_progress"
  if bash "$SCRIPT_DIR/scripts/06_security_tools.sh" "$TARGET_IP" "$TARGET_USER" "$MODE"; then
    echo -e "${GREEN}[PHASE 6 OK]${NC}"
    update_phase "phase_6_security_tools" "success"
  else
    echo -e "${RED}[PHASE 6 FAILED]${NC}"
    update_phase "phase_6_security_tools" "failed"
    [[ "$MODE" != "check" ]] && exit 1
  fi
  echo ""

  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}Hardening ${MODE} completed successfully!${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo -e "Log file: ${YELLOW}$LOG_FILE${NC}"
  echo -e "Progress: ${YELLOW}$PROGRESS_FILE${NC}"
  echo ""
}

main

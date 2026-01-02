#!/bin/bash
# Server Security Audit & Remediation Master Script
# Orchestrates vulnerability scanning, hardening, and verification

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARDENING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$HARDENING_DIR/logs"
AUDIT_LOGS_DIR="$LOGS_DIR/audit_sessions"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Create logs directory
mkdir -p "$AUDIT_LOGS_DIR"

# Logging
log_msg() { echo -e "${1}${2}${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
log_header() { echo -e "${BLUE}\n╔════════════════════════════════════════════════════════════════╗"; echo "║ $1"; echo "╚════════════════════════════════════════════════════════════════╝${NC}\n"; }

# Help
show_help() {
cat << 'HELP'
Server Security Audit & Remediation Master Script

USAGE: ./server-security-audit.sh [ACTION] [IP] [USER]

ACTIONS:
  scan    - Vulnerability scan only
  fix     - Hardening/remediation only  
  verify  - Verification only
  all     - Full cycle: scan → fix → verify (DEFAULT)
  help    - Show this help

EXAMPLES:
  ./server-security-audit.sh all 10.0.0.84 wizardsofts
  ./server-security-audit.sh scan
  ./server-security-audit.sh verify 10.0.0.84 wizardsofts

ENVIRONMENT: Set up before running:
  source .env && source hardening/.env

HELP
exit 0
}

# Main execution
main() {
  local ACTION="${1:-all}"
  local TARGET_IP="${2:-}"
  local TARGET_USER="${3:-}"
  local START_TIME=$(date +%s)
  
  # Load environment if not provided
  if [ -z "$TARGET_IP" ] && [ -f "$WORKSPACE_DIR/.env" ]; then
    source "$WORKSPACE_DIR/.env" 2>/dev/null || true
    TARGET_IP="${TARGET_IP:-10.0.0.84}"
  fi
  
  if [ -z "$TARGET_USER" ] && [ -f "$WORKSPACE_DIR/hardening/.env" ]; then
    source "$WORKSPACE_DIR/hardening/.env" 2>/dev/null || true
    TARGET_USER="${TARGET_USER:-wizardsofts}"
  fi

  # Handle help
  if [ "$ACTION" = "help" ] || [ "$ACTION" = "-h" ]; then
    show_help
  fi

  # Validate action
  case "$ACTION" in
    scan|fix|verify|all) ;;
    *) log_error "Invalid action: $ACTION"; show_help ;;
  esac

  # Session log
  local SESSION_LOG="$AUDIT_LOGS_DIR/${ACTION}_${TIMESTAMP}.log"
  
  # Display header
  log_header "SERVER SECURITY AUDIT - $ACTION"
  log_info "Target: $TARGET_IP | User: $TARGET_USER"
  log_info "Session: $SESSION_LOG\n"

  # Check connectivity
  if ! ping -c 1 -W 2 "$TARGET_IP" &> /dev/null; then
    log_error "Server $TARGET_IP is not reachable"
    exit 1
  fi
  log_success "Server is reachable"

  # Check SSH
  if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" "echo ok" &> /dev/null; then
    log_error "SSH connection failed"
    exit 1
  fi
  log_success "SSH connection successful\n"

  # Execute actions
  case "$ACTION" in
    scan)
      log_header "PHASE 1: VULNERABILITY SCAN"
      bash "$SCRIPT_DIR/scan_vulnerabilities.sh" "$TARGET_IP" "$TARGET_USER" 2>&1 | tee -a "$SESSION_LOG"
      ;;
    fix)
      log_header "PHASE 2: HARDENING & REMEDIATION"
      bash "$HARDENING_DIR/harden.sh" "$TARGET_IP" "$TARGET_USER" apply 2>&1 | tee -a "$SESSION_LOG"
      ;;
    verify)
      log_header "PHASE 3: VERIFICATION"
      bash "$SCRIPT_DIR/06_security_tools.sh" "$TARGET_IP" "$TARGET_USER" check 2>&1 | tee -a "$SESSION_LOG"
      ;;
    all)
      log_header "PHASE 1: VULNERABILITY SCAN"
      bash "$SCRIPT_DIR/scan_vulnerabilities.sh" "$TARGET_IP" "$TARGET_USER" 2>&1 | tee -a "$SESSION_LOG"
      
      log_header "PHASE 2: HARDENING & REMEDIATION"
      bash "$HARDENING_DIR/harden.sh" "$TARGET_IP" "$TARGET_USER" apply 2>&1 | tee -a "$SESSION_LOG"
      
      log_header "PHASE 3: VERIFICATION"
      bash "$SCRIPT_DIR/06_security_tools.sh" "$TARGET_IP" "$TARGET_USER" check 2>&1 | tee -a "$SESSION_LOG"
      ;;
  esac

  # Summary
  local END_TIME=$(date +%s)
  local ELAPSED=$((END_TIME - START_TIME))
  
  log_header "AUDIT COMPLETE"
  log_success "Action completed: $ACTION"
  log_info "Duration: ${ELAPSED}s"
  log_info "Session log: $SESSION_LOG\n"
  
  echo "Next steps:"
  case "$ACTION" in
    scan) echo "  1. Review: cat $LOGS_DIR/VULNERABILITY_REPORT_*.md" ;;
    fix) echo "  1. Verify: ./server-security-audit.sh verify $TARGET_IP $TARGET_USER" ;;
    verify) echo "  1. Re-scan: ./server-security-audit.sh scan $TARGET_IP $TARGET_USER" ;;
    all) echo "  1. Check logs: tail -100 $SESSION_LOG" ;;
  esac
  echo ""
}

# Run
main "$@"

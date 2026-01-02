#!/bin/bash
# Server Security Audit Wrapper - Quick access from workspace root
# Run from workspace directory: ./audit-server.sh [action] [ip] [user]

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")" && pwd)"
AUDIT_SCRIPT="$WORKSPACE_DIR/hardening/scripts/server-security-audit.sh"

# Check if audit script exists
if [ ! -f "$AUDIT_SCRIPT" ]; then
  echo "Error: server-security-audit.sh not found at $AUDIT_SCRIPT"
  exit 1
fi

# Load environment if available
if [ -f "$WORKSPACE_DIR/.env" ]; then
  source "$WORKSPACE_DIR/.env" 2>/dev/null || true
fi

if [ -f "$WORKSPACE_DIR/hardening/.env" ]; then
  source "$WORKSPACE_DIR/hardening/.env" 2>/dev/null || true
fi

# Forward all arguments to the actual audit script
exec bash "$AUDIT_SCRIPT" "$@"

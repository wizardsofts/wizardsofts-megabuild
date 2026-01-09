#!/bin/bash
################################################################################
# validate-service-infrastructure.sh
#
# Purpose: Ground truth verification for service infrastructure
#          Validates actual system state vs documentation assumptions
#
# Based on: GitLab hardening session (2026-01-08)
#           AGENT.md Section 9.0 (Ground Truth Verification Protocol)
#
# Usage: ./validate-service-infrastructure.sh <service-name> <host-ip> [options]
#
# Options:
#   --skip-external    Skip external connectivity checks
#   --skip-logs        Skip log analysis
#   --report <file>    Save report to file (default: stdout)
#   --strict           Exit with error if any check fails
#
# Examples:
#   ./validate-service-infrastructure.sh gitlab 10.0.0.84
#   ./validate-service-infrastructure.sh keycloak 10.0.0.84 --strict
#   ./validate-service-infrastructure.sh nexus 10.0.0.84 --report /tmp/nexus-report.txt
#
################################################################################

set -e

# Cleanup handler
cleanup() {
    local exit_code="${1:-0}"
    # Cleanup logic if needed
    exit "${exit_code}"
}
trap 'cleanup 130' INT TERM

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="${1}"
HOST="${2}"
SSH_USER="${SSH_USER:-agent}"
SKIP_EXTERNAL=false
SKIP_LOGS=false
REPORT_FILE=""
STRICT_MODE=false

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Parse options
shift 2 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-external)
            SKIP_EXTERNAL=true
            shift
            ;;
        --skip-logs)
            SKIP_LOGS=true
            shift
            ;;
        --report)
            REPORT_FILE="$2"
            shift 2
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$SERVICE_NAME" ]] || [[ -z "$HOST" ]]; then
    echo "Usage: $0 <service-name> <host-ip> [options]"
    echo ""
    echo "Options:"
    echo "  --skip-external    Skip external connectivity checks"
    echo "  --skip-logs        Skip log analysis"
    echo "  --report <file>    Save report to file"
    echo "  --strict           Exit with error if any check fails"
    exit 1
fi

# Output function
output() {
    if [[ -n "$REPORT_FILE" ]]; then
        echo "$1" | tee -a "$REPORT_FILE"
    else
        echo "$1"
    fi
}

# Test result tracking
test_result() {
    local status=$1
    local message=$2
    
    if [[ "$status" == "PASS" ]]; then
        output "  ${GREEN}✅ PASS${NC}: $message"
        ((CHECKS_PASSED++))
    elif [[ "$status" == "FAIL" ]]; then
        output "  ${RED}❌ FAIL${NC}: $message"
        ((CHECKS_FAILED++))
        if [[ "$STRICT_MODE" == true ]]; then
            exit 1
        fi
    elif [[ "$status" == "WARN" ]]; then
        output "  ${YELLOW}⚠️  WARN${NC}: $message"
        ((CHECKS_WARNING++))
    else
        output "  ${BLUE}ℹ️  INFO${NC}: $message"
    fi
}

# Initialize report (atomic write)
if [[ -n "$REPORT_FILE" ]]; then
    {
        echo "=== Infrastructure Validation Report ==="
        echo "Service: $SERVICE_NAME"
        echo "Host: $HOST"
        echo "Date: $(date)"
        echo "========================================"
        echo ""
    } > "$REPORT_FILE"
fi

output ""
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output "${BLUE}  Infrastructure Validation: $SERVICE_NAME @ $HOST${NC}"
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output ""

# 1. Container Status Check
output "${BLUE}[1/8] Container Status${NC}"
if ! CONTAINER_OUTPUT=$(ssh "${SSH_USER}@${HOST}" "docker ps -a --filter name=\"${SERVICE_NAME}\" --format '{{.Names}}|{{.Status}}|{{.State}}'" 2>&1); then
    test_result "FAIL" "Cannot connect to ${HOST} via SSH"
    output "       Ensure SSH access is configured: ssh ${SSH_USER}@${HOST}"
    cleanup 1
fi

if echo "$CONTAINER_OUTPUT" | grep -q "$SERVICE_NAME"; then
    CONTAINER_STATE=$(echo "$CONTAINER_OUTPUT" | cut -d'|' -f3)
    CONTAINER_STATUS=$(echo "$CONTAINER_OUTPUT" | cut -d'|' -f2)
    
    if [[ "$CONTAINER_STATE" == "running" ]]; then
        test_result "PASS" "Container '$SERVICE_NAME' is running"
        output "       Status: $CONTAINER_STATUS"
    else
        test_result "FAIL" "Container '$SERVICE_NAME' is not running (state: $CONTAINER_STATE)"
    fi
else
    test_result "FAIL" "Container '$SERVICE_NAME' not found"
fi

# 2. Container Health Check
output ""
output "${BLUE}[2/8] Container Health${NC}"
HEALTH=$(ssh "${SSH_USER}@${HOST}" "docker inspect \"${SERVICE_NAME}\" --format '{{.State.Health.Status}}' 2>/dev/null || echo 'no-healthcheck'" 2>&1)

if [[ "$HEALTH" == "healthy" ]]; then
    test_result "PASS" "Container health is healthy"
elif [[ "$HEALTH" == "no-healthcheck" ]]; then
    test_result "WARN" "No health check configured for container"
else
    test_result "FAIL" "Container health is $HEALTH"
fi

# 3. Port Binding Check
output ""
output "${BLUE}[3/8] Port Bindings${NC}"
PORTS=$(ssh "${SSH_USER}@${HOST}" "docker port \"${SERVICE_NAME}\" 2>/dev/null" 2>&1)

if [[ -n "$PORTS" ]]; then
    test_result "PASS" "Port bindings configured"
    while IFS= read -r line; do
        output "       $line"
    done <<< "$PORTS"
else
    test_result "WARN" "No port bindings found (might use host network mode)"
fi

# 4. NFS Mount Check
output ""
output "${BLUE}[4/8] NFS Mounts${NC}"
NFS_MOUNTS=$(ssh "${SSH_USER}@${HOST}" "mount | grep nfs | grep -i \"${SERVICE_NAME}\" || echo ''" 2>&1)

if [[ -n "$NFS_MOUNTS" ]]; then
    test_result "PASS" "NFS mounts found for service"
    while IFS= read -r line; do
        output "       $line"
    done <<< "$NFS_MOUNTS"
    
    # Check mount permissions
    NFS_EXPORT=$(echo "$NFS_MOUNTS" | head -1 | awk '{print $3}')
    if [[ -n "$NFS_EXPORT" ]]; then
        MOUNT_OPTIONS=$(ssh "${SSH_USER}@${HOST}" "mount | grep \"${NFS_EXPORT}\" | grep -oP '\\(.*\\)' || echo ''" 2>&1)
        if echo "$MOUNT_OPTIONS" | grep -q "rw"; then
            test_result "PASS" "NFS mount is read-write"
        else
            test_result "WARN" "NFS mount might be read-only"
        fi
    fi
else
    test_result "INFO" "No NFS mounts found (service might not require NFS)"
fi

# 5. Configuration Validation
output ""
output "${BLUE}[5/8] Configuration Files${NC}"
CONFIG_CHECK=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" ls -la \"/etc/${SERVICE_NAME}/\" 2>/dev/null || docker exec \"${SERVICE_NAME}\" env | grep -E '^[A-Z_]+=' | head -10 2>/dev/null || echo 'config-check-failed'" 2>&1)

if [[ "$CONFIG_CHECK" != "config-check-failed" ]]; then
    test_result "PASS" "Configuration accessible inside container"
    # Show first few config entries
    echo "$CONFIG_CHECK" | head -5 | while IFS= read -r line; do
        output "       $line"
    done
else
    test_result "WARN" "Could not verify configuration files"
fi

# 6. Service Connectivity (Internal)
output ""
output "${BLUE}[6/8] Internal Connectivity${NC}"
INTERNAL_PORTS=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" netstat -tlnp 2>/dev/null | grep LISTEN || ss -tlnp 2>/dev/null | grep LISTEN || echo 'no-netstat'" 2>&1)

if [[ "$INTERNAL_PORTS" != "no-netstat" ]]; then
    test_result "PASS" "Service has listening ports"
    echo "$INTERNAL_PORTS" | head -5 | while IFS= read -r line; do
        output "       $line"
    done
else
    test_result "INFO" "Could not query listening ports (netstat/ss not available)"
fi

# 7. Recent Logs Analysis
if [[ "$SKIP_LOGS" != true ]]; then
    output ""
    output "${BLUE}[7/8] Recent Logs Analysis${NC}"
    RECENT_LOGS=$(ssh "${SSH_USER}@${HOST}" "docker logs \"${SERVICE_NAME}\" --tail 100 2>&1" 2>&1)
    
    # Check for errors in logs
    ERROR_COUNT=$(echo "$RECENT_LOGS" | grep -i -E "error|exception|fatal|panic" | wc -l)
    
    if [[ $ERROR_COUNT -eq 0 ]]; then
        test_result "PASS" "No errors found in recent logs (last 100 lines)"
    elif [[ $ERROR_COUNT -lt 5 ]]; then
        test_result "WARN" "Found $ERROR_COUNT error(s) in recent logs"
    else
        test_result "FAIL" "Found $ERROR_COUNT error(s) in recent logs - investigate"
    fi
    
    # Show last 3 log lines
    output "       Last 3 log entries:"
    echo "$RECENT_LOGS" | tail -3 | while IFS= read -r line; do
        output "         $(echo "$line" | cut -c1-100)"
    done
else
    output ""
    output "${BLUE}[7/8] Recent Logs Analysis${NC}"
    test_result "INFO" "Skipped (--skip-logs)"
fi

# 8. External Connectivity
if [[ "$SKIP_EXTERNAL" != true ]]; then
    output ""
    output "${BLUE}[8/8] External Connectivity${NC}"

    # Get external port from docker port command
    EXTERNAL_PORT=$(ssh "${SSH_USER}@${HOST}" "docker port \"${SERVICE_NAME}\" 2>/dev/null | head -1 | awk -F: '{print \$2}'" 2>&1)
    
    if [[ -n "$EXTERNAL_PORT" ]]; then
        # Test HTTP connectivity
        HTTP_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}:${EXTERNAL_PORT}/health" 2>/dev/null || echo "000")
        
        if [[ "$HTTP_TEST" == "200" ]]; then
            test_result "PASS" "Health endpoint responding on port $EXTERNAL_PORT"
        elif [[ "$HTTP_TEST" == "000" ]]; then
            test_result "WARN" "Could not connect to port $EXTERNAL_PORT (might not have /health endpoint)"
        else
            test_result "WARN" "Health endpoint returned HTTP $HTTP_TEST"
        fi
    else
        test_result "INFO" "No external ports to test"
    fi
else
    output ""
    output "${BLUE}[8/8] External Connectivity${NC}"
    test_result "INFO" "Skipped (--skip-external)"
fi

# Summary
output ""
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output "${BLUE}  Validation Summary${NC}"
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output ""
output "  ${GREEN}✅ Passed${NC}:  $CHECKS_PASSED"
output "  ${RED}❌ Failed${NC}:  $CHECKS_FAILED"
output "  ${YELLOW}⚠️  Warnings${NC}: $CHECKS_WARNING"
output ""

if [[ $CHECKS_FAILED -gt 0 ]]; then
    output "${RED}❌ Validation FAILED${NC} - $CHECKS_FAILED check(s) failed"
    exit 1
elif [[ $CHECKS_WARNING -gt 0 ]]; then
    output "${YELLOW}⚠️  Validation PASSED with warnings${NC} - $CHECKS_WARNING warning(s)"
    exit 0
else
    output "${GREEN}✅ Validation PASSED${NC} - All checks successful"
    exit 0
fi

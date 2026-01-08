#!/bin/bash
################################################################################
# test-service-integration.sh
#
# Purpose: Run integration tests for service infrastructure
#          Validates APIs, databases, cache, monitoring, backups
#
# Based on: GitLab integration testing (2026-01-08)
#           28 tests covering all infrastructure components
#           AGENT.md Section 9.4 (Integration Testing)
#
# Usage: ./test-service-integration.sh <service-name> <host-ip> [options]
#
# Options:
#   --config <file>      Test configuration file (JSON)
#   --report <file>      Save report to file (default: stdout)
#   --strict             Exit on first failure
#   --skip <test-id>     Skip specific test (can be used multiple times)
#
# Examples:
#   ./test-service-integration.sh gitlab 10.0.0.84
#   ./test-service-integration.sh gitlab 10.0.0.84 --config gitlab-tests.json
#   ./test-service-integration.sh keycloak 10.0.0.84 --report /tmp/keycloak-tests.txt
#   ./test-service-integration.sh nexus 10.0.0.84 --skip backup --skip monitoring
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
CONFIG_FILE=""
REPORT_FILE=""
STRICT_MODE=false
SKIP_TESTS=()

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0
TOTAL_TESTS=0

# Parse options
shift 2 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --report)
            REPORT_FILE="$2"
            shift 2
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --skip)
            SKIP_TESTS+=("$2")
            shift 2
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
    echo "  --config <file>      Test configuration file"
    echo "  --report <file>      Save report to file"
    echo "  --strict             Exit on first failure"
    echo "  --skip <test-id>     Skip specific test"
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
    local test_id=$1
    local test_name=$2
    local status=$3
    local message=$4
    
    ((TOTAL_TESTS++))
    
    if [[ "$status" == "PASS" ]]; then
        output "  ${GREEN}✅ PASS${NC} [$test_id] $test_name"
        if [[ -n "$message" ]]; then
            output "       $message"
        fi
        ((TESTS_PASSED++))
    elif [[ "$status" == "FAIL" ]]; then
        output "  ${RED}❌ FAIL${NC} [$test_id] $test_name"
        if [[ -n "$message" ]]; then
            output "       $message"
        fi
        ((TESTS_FAILED++))
        if [[ "$STRICT_MODE" == true ]]; then
            exit 1
        fi
    elif [[ "$status" == "SKIP" ]]; then
        output "  ${YELLOW}⏭️  SKIP${NC} [$test_id] $test_name"
        ((TESTS_SKIPPED++))
    fi
}

# Check if test should be skipped
should_skip() {
    local test_id=$1
    for skip in "${SKIP_TESTS[@]}"; do
        if [[ "$skip" == "$test_id" ]]; then
            return 0
        fi
    done
    return 1
}

# Initialize report (atomic write)
if [[ -n "$REPORT_FILE" ]]; then
    {
        echo "=== Integration Test Report ==="
        echo "Service: $SERVICE_NAME"
        echo "Host: $HOST"
        echo "Date: $(date)"
        echo "==============================="
        echo ""
    } > "$REPORT_FILE"
fi

output ""
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output "${BLUE}  Integration Tests: $SERVICE_NAME @ $HOST${NC}"
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output ""

# Test Suite 1: Container Health
output "${BLUE}[Suite 1] Container Health Tests${NC}"

if should_skip "container-running"; then
    test_result "container-running" "Container is running" "SKIP" ""
else
    CONTAINER_STATE=$(ssh "${SSH_USER}@${HOST}" "docker inspect \"${SERVICE_NAME}\" --format '{{.State.Running}}' 2>/dev/null || echo 'false'" 2>&1)
    if [[ "$CONTAINER_STATE" == "true" ]]; then
        test_result "container-running" "Container is running" "PASS" ""
    else
        test_result "container-running" "Container is running" "FAIL" "Container state: $CONTAINER_STATE"
    fi
fi

if should_skip "container-health"; then
    test_result "container-health" "Container health check" "SKIP" ""
else
    HEALTH_STATUS=$(ssh "${SSH_USER}@${HOST}" "docker inspect \"${SERVICE_NAME}\" --format '{{.State.Health.Status}}' 2>/dev/null || echo 'no-healthcheck'" 2>&1)
    if [[ "$HEALTH_STATUS" == "healthy" ]]; then
        test_result "container-health" "Container health check" "PASS" "Status: healthy"
    elif [[ "$HEALTH_STATUS" == "no-healthcheck" ]]; then
        test_result "container-health" "Container health check" "SKIP" "No health check configured"
        ((TESTS_SKIPPED++))
        ((TOTAL_TESTS--))
    else
        test_result "container-health" "Container health check" "FAIL" "Status: $HEALTH_STATUS"
    fi
fi

output ""

# Test Suite 2: Network Connectivity
output "${BLUE}[Suite 2] Network Connectivity Tests${NC}"

if should_skip "port-listening"; then
    test_result "port-listening" "Service port listening" "SKIP" ""
else
    LISTENING=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" netstat -tln 2>/dev/null | grep LISTEN || ss -tln 2>/dev/null | grep LISTEN || echo ''" 2>&1)
    if [[ -n "$LISTENING" ]]; then
        PORT_COUNT=$(echo "$LISTENING" | wc -l)
        test_result "port-listening" "Service port listening" "PASS" "$PORT_COUNT port(s) listening"
    else
        test_result "port-listening" "Service port listening" "FAIL" "No listening ports found"
    fi
fi

if should_skip "external-connectivity"; then
    test_result "external-connectivity" "External connectivity" "SKIP" ""
else
    EXTERNAL_PORT=$(ssh "${SSH_USER}@${HOST}" "docker port \"${SERVICE_NAME}\" 2>/dev/null | head -1 | awk -F: '{print \$2}'" 2>&1)
    if [[ -n "$EXTERNAL_PORT" ]]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}:${EXTERNAL_PORT}" 2>/dev/null || echo "000")
        if [[ "$HTTP_CODE" != "000" ]]; then
            test_result "external-connectivity" "External connectivity" "PASS" "HTTP $HTTP_CODE on port $EXTERNAL_PORT"
        else
            test_result "external-connectivity" "External connectivity" "FAIL" "Cannot connect to port $EXTERNAL_PORT"
        fi
    else
        test_result "external-connectivity" "External connectivity" "SKIP" "No external ports"
        ((TESTS_SKIPPED++))
        ((TOTAL_TESTS--))
    fi
fi

output ""

# Test Suite 3: Database Connectivity
output "${BLUE}[Suite 3] Database Tests${NC}"

if should_skip "database-connection"; then
    test_result "database-connection" "Database connection" "SKIP" ""
else
    # Try to detect database connection from environment variables
    DB_HOST=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" env | grep -i 'DB_HOST\\|DATABASE_HOST\\|POSTGRES_HOST' | head -1 | cut -d= -f2" 2>&1 || echo "")
    
    if [[ -n "$DB_HOST" ]]; then
        # Try to verify database is accessible
        DB_CHECK=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" timeout 5 nc -zv \"${DB_HOST}\" 5432 2>&1 || echo 'failed'" 2>&1)
        if [[ "$DB_CHECK" != "failed" ]] && ! echo "$DB_CHECK" | grep -q "Connection refused"; then
            test_result "database-connection" "Database connection" "PASS" "Connected to $DB_HOST"
        else
            test_result "database-connection" "Database connection" "FAIL" "Cannot reach database at $DB_HOST"
        fi
    else
        test_result "database-connection" "Database connection" "SKIP" "No database configured"
        ((TESTS_SKIPPED++))
        ((TOTAL_TESTS--))
    fi
fi

output ""

# Test Suite 4: Cache/Redis Tests
output "${BLUE}[Suite 4] Cache Tests${NC}"

if should_skip "cache-connection"; then
    test_result "cache-connection" "Cache connection" "SKIP" ""
else
    REDIS_HOST=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" env | grep -i 'REDIS_HOST\\|CACHE_HOST' | head -1 | cut -d= -f2" 2>&1 || echo "")
    
    if [[ -n "$REDIS_HOST" ]]; then
        REDIS_CHECK=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" timeout 5 nc -zv \"${REDIS_HOST}\" 6379 2>&1 || echo 'failed'" 2>&1)
        if [[ "$REDIS_CHECK" != "failed" ]] && ! echo "$REDIS_CHECK" | grep -q "Connection refused"; then
            test_result "cache-connection" "Cache connection" "PASS" "Connected to $REDIS_HOST"
        else
            test_result "cache-connection" "Cache connection" "FAIL" "Cannot reach cache at $REDIS_HOST"
        fi
    else
        test_result "cache-connection" "Cache connection" "SKIP" "No cache configured"
        ((TESTS_SKIPPED++))
        ((TOTAL_TESTS--))
    fi
fi

output ""

# Test Suite 5: Storage Tests
output "${BLUE}[Suite 5] Storage Tests${NC}"

if should_skip "nfs-mount"; then
    test_result "nfs-mount" "NFS mount accessible" "SKIP" ""
else
    NFS_MOUNTS=$(ssh "${SSH_USER}@${HOST}" "mount | grep nfs | grep -i \"${SERVICE_NAME}\" || echo ''" 2>&1)
    if [[ -n "$NFS_MOUNTS" ]]; then
        MOUNT_PATH=$(echo "$NFS_MOUNTS" | awk '{print $3}' | head -1)
        WRITE_TEST=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" touch \"${MOUNT_PATH}/test-write-$$\" 2>&1 && docker exec \"${SERVICE_NAME}\" rm \"${MOUNT_PATH}/test-write-$$\" 2>&1 && echo 'success' || echo 'failed'" 2>&1)
        if [[ "$WRITE_TEST" == "success" ]]; then
            test_result "nfs-mount" "NFS mount accessible" "PASS" "Write test successful"
        else
            test_result "nfs-mount" "NFS mount accessible" "FAIL" "Write test failed"
        fi
    else
        test_result "nfs-mount" "NFS mount accessible" "SKIP" "No NFS mounts found"
        ((TESTS_SKIPPED++))
        ((TOTAL_TESTS--))
    fi
fi

output ""

# Test Suite 6: Backup Tests
output "${BLUE}[Suite 6] Backup Tests${NC}"

if should_skip "backup-directory"; then
    test_result "backup-directory" "Backup directory exists" "SKIP" ""
else
    BACKUP_DIR=$(ssh "${SSH_USER}@${HOST}" "docker exec \"${SERVICE_NAME}\" ls -la \"/var/backups/${SERVICE_NAME}\" 2>/dev/null || docker exec \"${SERVICE_NAME}\" ls -la \"/var/opt/${SERVICE_NAME}/backups\" 2>/dev/null || echo 'not-found'" 2>&1)
    if [[ "$BACKUP_DIR" != "not-found" ]]; then
        test_result "backup-directory" "Backup directory exists" "PASS" "Directory accessible"
    else
        test_result "backup-directory" "Backup directory exists" "FAIL" "Backup directory not found"
    fi
fi

output ""

# Test Suite 7: Monitoring Tests
output "${BLUE}[Suite 7] Monitoring Tests${NC}"

if should_skip "metrics-endpoint"; then
    test_result "metrics-endpoint" "Metrics endpoint" "SKIP" ""
else
    METRICS_PORT=$(ssh "${SSH_USER}@${HOST}" "docker port \"${SERVICE_NAME}\" 2>/dev/null | grep 9090 || docker port \"${SERVICE_NAME}\" 2>/dev/null | grep 9187 || echo ''" 2>&1)
    if [[ -n "$METRICS_PORT" ]]; then
        METRICS_PORT_NUM=$(echo "$METRICS_PORT" | awk -F: '{print $2}')
        METRICS_CHECK=$(curl -s "http://${HOST}:${METRICS_PORT_NUM}/metrics" | head -5 || echo "failed")
        if [[ "$METRICS_CHECK" != "failed" ]]; then
            test_result "metrics-endpoint" "Metrics endpoint" "PASS" "Accessible on port $METRICS_PORT_NUM"
        else
            test_result "metrics-endpoint" "Metrics endpoint" "FAIL" "Cannot access metrics"
        fi
    else
        test_result "metrics-endpoint" "Metrics endpoint" "SKIP" "No metrics port exposed"
        ((TESTS_SKIPPED++))
        ((TOTAL_TESTS--))
    fi
fi

output ""

# Test Suite 8: Log Analysis
output "${BLUE}[Suite 8] Log Analysis Tests${NC}"

if should_skip "log-errors"; then
    test_result "log-errors" "Recent log errors" "SKIP" ""
else
    ERROR_COUNT=$(ssh "${SSH_USER}@${HOST}" "docker logs \"${SERVICE_NAME}\" --tail 200 2>&1 | grep -i -E 'error|exception|fatal' | wc -l" 2>&1)
    if [[ $ERROR_COUNT -eq 0 ]]; then
        test_result "log-errors" "Recent log errors" "PASS" "No errors in last 200 lines"
    elif [[ $ERROR_COUNT -lt 5 ]]; then
        test_result "log-errors" "Recent log errors" "PASS" "Low error count: $ERROR_COUNT"
    else
        test_result "log-errors" "Recent log errors" "FAIL" "High error count: $ERROR_COUNT"
    fi
fi

output ""

# Summary
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output "${BLUE}  Test Summary${NC}"
output "${BLUE}═══════════════════════════════════════════════════════════${NC}"
output ""
output "  Total Tests:    $TOTAL_TESTS"
output "  ${GREEN}✅ Passed${NC}:      $TESTS_PASSED"
output "  ${RED}❌ Failed${NC}:      $TESTS_FAILED"
output "  ${YELLOW}⏭️  Skipped${NC}:     $TESTS_SKIPPED"

if [[ $TOTAL_TESTS -gt 0 ]]; then
    PASS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))
    output ""
    output "  Pass Rate:      ${PASS_RATE}%"
fi

output ""

if [[ $TESTS_FAILED -gt 0 ]]; then
    output "${RED}❌ Tests FAILED${NC} - $TESTS_FAILED test(s) failed"
    exit 1
else
    output "${GREEN}✅ Tests PASSED${NC} - All tests successful"
    exit 0
fi

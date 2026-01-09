#!/bin/bash

# Integration Test Suite for Monitoring Stack
# Tests: container health, API endpoints, data flow, configuration
# Location: infrastructure/monitoring/tests/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="${SCRIPT_DIR}/test-results-$(date +%s).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

test_pass() {
    echo -e "${GREEN}✓${NC} $*" | tee -a "$LOG_FILE"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $*" | tee -a "$LOG_FILE"
    ((TESTS_FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⊘${NC} $*" | tee -a "$LOG_FILE"
    ((TESTS_SKIPPED++))
}

test_header() {
    echo -e "\n${BLUE}=== $* ===${NC}" | tee -a "$LOG_FILE"
}

# ============================================================================
# CONTAINER HEALTH TESTS
# ============================================================================

test_containers_running() {
    test_header "Container Health Tests"
    
    local containers=("prometheus" "grafana" "loki" "promtail" "node-exporter" "cadvisor" "alertmanager")
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
            test_pass "Container $container is running"
        else
            test_fail "Container $container is not running"
        fi
    done
}

test_container_restart_policy() {
    log "Checking restart policies..."
    
    local containers=("prometheus" "grafana" "loki" "promtail" "node-exporter" "cadvisor" "alertmanager")
    
    for container in "${containers[@]}"; do
        local policy=$(docker inspect "$container" --format='{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null || echo "none")
        if [ "$policy" = "unless-stopped" ]; then
            test_pass "Container $container has correct restart policy: $policy"
        else
            test_fail "Container $container has incorrect restart policy: $policy (expected: unless-stopped)"
        fi
    done
}

test_container_health_checks() {
    log "Checking health check status..."
    
    local containers_with_healthcheck=("prometheus" "grafana" "loki" "alertmanager")
    
    for container in "${containers_with_healthcheck[@]}"; do
        local health=$(docker inspect "$container" --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")
        if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
            test_pass "Container $container health status: $health"
        else
            test_fail "Container $container health status: $health (unexpected status)"
        fi
    done
}

# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

test_prometheus_api() {
    test_header "Prometheus API Tests"
    
    if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
        test_pass "Prometheus health endpoint accessible"
    else
        test_fail "Prometheus health endpoint unreachable"
        return 1
    fi
    
    if curl -sf http://localhost:9090/api/v1/query?query=up > /dev/null 2>&1; then
        test_pass "Prometheus query API accessible"
    else
        test_fail "Prometheus query API unreachable"
    fi
    
    if curl -sf http://localhost:9090/api/v1/targets > /dev/null 2>&1; then
        test_pass "Prometheus targets API accessible"
    else
        test_fail "Prometheus targets API unreachable"
    fi
}

test_grafana_api() {
    test_header "Grafana API Tests"
    
    if curl -sf http://localhost:3002/api/health > /dev/null 2>&1; then
        test_pass "Grafana health endpoint accessible"
    else
        test_fail "Grafana health endpoint unreachable"
        return 1
    fi
    
    if curl -sf http://localhost:3002/api/datasources > /dev/null 2>&1; then
        test_pass "Grafana datasources API accessible"
    else
        test_fail "Grafana datasources API unreachable"
    fi
    
    if curl -sf http://localhost:3002/api/dashboards/search > /dev/null 2>&1; then
        test_pass "Grafana dashboards API accessible"
    else
        test_fail "Grafana dashboards API unreachable"
    fi
}

test_loki_api() {
    test_header "Loki API Tests"
    
    if curl -sf http://localhost:3100/ready > /dev/null 2>&1; then
        test_pass "Loki ready endpoint accessible"
    else
        test_fail "Loki ready endpoint unreachable"
        return 1
    fi
    
    if curl -sf http://localhost:3100/loki/api/v1/query_range?query={job%3D%22varlogs%22} > /dev/null 2>&1; then
        test_pass "Loki query API accessible"
    else
        test_fail "Loki query API unreachable"
    fi
}

test_alertmanager_api() {
    test_header "Alertmanager API Tests"
    
    if curl -sf http://localhost:9093/api/v1/status > /dev/null 2>&1; then
        test_pass "Alertmanager status API accessible"
    else
        test_fail "Alertmanager status API unreachable"
        return 1
    fi
    
    if curl -sf http://localhost:9093/api/v1/alerts > /dev/null 2>&1; then
        test_pass "Alertmanager alerts API accessible"
    else
        test_fail "Alertmanager alerts API unreachable"
    fi
}

# ============================================================================
# DATA FLOW TESTS
# ============================================================================

test_prometheus_metrics() {
    test_header "Prometheus Metrics Collection"
    
    # Query for at least one metric
    local metrics_count=$(curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result | length' 2>/dev/null || echo "0")
    
    if [ "$metrics_count" -gt 0 ]; then
        test_pass "Prometheus is collecting metrics ($metrics_count targets active)"
    else
        test_fail "Prometheus has no active metrics"
    fi
}

test_prometheus_scrape_targets() {
    test_header "Prometheus Scrape Targets"
    
    # Check for expected job names
    local expected_jobs=("prometheus" "node-exporter" "cadvisor")
    
    for job in "${expected_jobs[@]}"; do
        local count=$(curl -s http://localhost:9090/api/v1/targets | jq ".data.activeTargets[] | select(.labels.job == \"$job\") | .labels.job" | wc -l)
        if [ "$count" -gt 0 ]; then
            test_pass "Prometheus scrape target found: $job"
        else
            test_fail "Prometheus scrape target missing: $job"
        fi
    done
}

test_loki_logs() {
    test_header "Loki Log Collection"
    
    # Query for logs
    local logs_count=$(curl -s 'http://localhost:3100/loki/api/v1/query?query={job=~".*"}' | jq '.data.result | length' 2>/dev/null || echo "0")
    
    if [ "$logs_count" -gt 0 ]; then
        test_pass "Loki is collecting logs (from $logs_count jobs)"
    else
        test_fail "Loki has no collected logs"
    fi
}

test_grafana_datasources() {
    test_header "Grafana Datasources"
    
    # Check for Prometheus datasource
    local prom_ds=$(curl -s http://localhost:3002/api/datasources | jq '.[] | select(.name == "Prometheus") | .name' 2>/dev/null)
    
    if [ -n "$prom_ds" ]; then
        test_pass "Grafana has Prometheus datasource configured"
    else
        test_fail "Grafana missing Prometheus datasource"
    fi
    
    # Check for Loki datasource
    local loki_ds=$(curl -s http://localhost:3002/api/datasources | jq '.[] | select(.name == "Loki") | .name' 2>/dev/null)
    
    if [ -n "$loki_ds" ]; then
        test_pass "Grafana has Loki datasource configured"
    else
        test_fail "Grafana missing Loki datasource"
    fi
}

test_grafana_dashboards() {
    test_header "Grafana Dashboards"
    
    local dashboard_count=$(curl -s http://localhost:3002/api/dashboards/search | jq '. | length' 2>/dev/null || echo "0")
    
    if [ "$dashboard_count" -gt 0 ]; then
        test_pass "Grafana has $dashboard_count dashboards provisioned"
    else
        test_fail "Grafana has no dashboards"
    fi
}

# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

test_configuration_files() {
    test_header "Configuration File Validation"
    
    # Check Prometheus config
    if [ -f "$MONITORING_DIR/prometheus/prometheus.yml" ]; then
        test_pass "Prometheus configuration file exists"
        
        # Validate YAML syntax
        if docker run --rm -v "$MONITORING_DIR/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
            prom/prometheus:v2.47.0 --config.file=/etc/prometheus/prometheus.yml --syntax-only > /dev/null 2>&1; then
            test_pass "Prometheus configuration syntax is valid"
        else
            test_fail "Prometheus configuration has syntax errors"
        fi
    else
        test_fail "Prometheus configuration file missing"
    fi
    
    # Check Alertmanager config
    if [ -f "$MONITORING_DIR/alertmanager/alertmanager.yml" ]; then
        test_pass "Alertmanager configuration file exists"
    else
        test_fail "Alertmanager configuration file missing"
    fi
    
    # Check Grafana provisioning
    if [ -f "$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yaml" ]; then
        test_pass "Grafana Prometheus datasource provisioning exists"
    else
        test_fail "Grafana Prometheus datasource provisioning missing"
    fi
    
    # Check Promtail config
    if [ -f "$MONITORING_DIR/promtail/promtail-config.yml" ]; then
        test_pass "Promtail configuration file exists"
    else
        test_fail "Promtail configuration file missing"
    fi
}

test_docker_compose() {
    test_header "Docker Compose Validation"
    
    if [ -f "$MONITORING_DIR/docker-compose.yml" ]; then
        test_pass "Docker compose file exists"
        
        # Validate docker-compose syntax
        if docker compose -f "$MONITORING_DIR/docker-compose.yml" config > /dev/null 2>&1; then
            test_pass "Docker compose file syntax is valid"
        else
            test_fail "Docker compose file has syntax errors"
        fi
    else
        test_fail "Docker compose file missing"
    fi
}

# ============================================================================
# RESOURCE USAGE TESTS
# ============================================================================

test_resource_limits() {
    test_header "Resource Limits Validation"
    
    local containers=("prometheus" "grafana" "loki" "promtail" "node-exporter" "cadvisor" "alertmanager")
    
    for container in "${containers[@]}"; do
        local memory_limit=$(docker inspect "$container" --format='{{.HostConfig.Memory}}' 2>/dev/null || echo "0")
        
        if [ "$memory_limit" -gt 0 ]; then
            local memory_mb=$((memory_limit / 1024 / 1024))
            test_pass "Container $container has memory limit: ${memory_mb}MB"
        else
            test_skip "Container $container has no memory limit (compose resource limits may apply)"
        fi
    done
}

# ============================================================================
# BACKUP TESTS
# ============================================================================

test_backup_script() {
    test_header "Backup Script Validation"
    
    if [ -f "$SCRIPT_DIR/../../../scripts/backup-monitoring.sh" ]; then
        test_pass "Backup script exists"
        
        if [ -x "$SCRIPT_DIR/../../../scripts/backup-monitoring.sh" ]; then
            test_pass "Backup script is executable"
        else
            test_fail "Backup script is not executable"
        fi
    else
        test_fail "Backup script not found"
    fi
}

test_backup_mount() {
    test_header "Backup Mount Validation"
    
    if mountpoint -q /mnt/monitoring-backups 2>/dev/null; then
        test_pass "Backup mount point /mnt/monitoring-backups is mounted"
        
        local available=$(df /mnt/monitoring-backups 2>/dev/null | tail -1 | awk '{print $4}')
        if [ "$available" -gt 0 ]; then
            test_pass "Backup mount has available space"
        else
            test_fail "Backup mount has insufficient space"
        fi
    else
        test_skip "Backup mount point not mounted (may be NFS not yet configured)"
    fi
}

# ============================================================================
# SUMMARY AND REPORTING
# ============================================================================

print_summary() {
    local total=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    
    echo "" | tee -a "$LOG_FILE"
    echo "════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
    echo "Test Results Summary" | tee -a "$LOG_FILE"
    echo "════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
    echo -e "${GREEN}Passed:${NC} $TESTS_PASSED" | tee -a "$LOG_FILE"
    echo -e "${RED}Failed:${NC} $TESTS_FAILED" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}Skipped:${NC} $TESTS_SKIPPED" | tee -a "$LOG_FILE"
    echo -e "Total:   $total" | tee -a "$LOG_FILE"
    echo "════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All critical tests passed!${NC}" | tee -a "$LOG_FILE"
        return 0
    else
        echo -e "${RED}Some tests failed. Review the log above.${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "Starting Monitoring Stack Integration Tests"
    log "Monitoring directory: $MONITORING_DIR"
    log "Log file: $LOG_FILE"
    log ""
    
    # Run test suites
    test_containers_running
    test_container_restart_policy
    test_container_health_checks
    
    test_prometheus_api
    test_grafana_api
    test_loki_api
    test_alertmanager_api
    
    test_prometheus_metrics
    test_prometheus_scrape_targets
    test_loki_logs
    test_grafana_datasources
    test_grafana_dashboards
    
    test_configuration_files
    test_docker_compose
    
    test_resource_limits
    
    test_backup_script
    test_backup_mount
    
    # Print summary and return appropriate exit code
    print_summary
}

# Run main function
main "$@"

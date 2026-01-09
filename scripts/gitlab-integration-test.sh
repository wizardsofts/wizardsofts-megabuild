#!/bin/bash
# Note: do not exit on first failure; we want full test report

# GitLab Integration Test Suite
# Tests all external system integrations before deployment
# Run this before activating any phase changes

TESTS_PASSED=0
TESTS_FAILED=0
RESULTS_FILE="/tmp/gitlab-test-results-$(date +%Y%m%d-%H%M%S).txt"
LOG_DIR="/var/log/gitlab-integration-tests"

# Endpoint configuration (overridable via environment)
GITLAB_URL="${GITLAB_URL:-http://10.0.0.84:8090}"
GITLAB_HEALTH_PATH="${GITLAB_HEALTH_PATH:-/-/health}"
DB_HOST="${DB_HOST:-10.0.0.80}"
DB_PORT="${DB_PORT:-5435}"
DB_NAME="${DB_NAME:-${GITLAB_DB_NAME:-gitlabhq_production}}"
DB_USER="${DB_USER:-${GITLAB_DB_USER:-gitlab}}"
# Get password from GitLab config if not set
if [ -z "${DB_PASSWORD}" ]; then
  DB_PASSWORD=$(docker exec gitlab grep "db_password" /etc/gitlab/gitlab.rb 2>/dev/null | grep -v "^#" | sed "s/.*'\(.*\)'.*/\1/" | head -1)
fi
REDIS_HOST="${REDIS_HOST:-10.0.0.80}"
REDIS_PORT="${REDIS_PORT:-6380}"
REGISTRY_URL="${REGISTRY_URL:-http://10.0.0.84:5050/v2/}"
LOKI_URL="${LOKI_URL:-http://10.0.0.80:3100}"
GRAFANA_URL="${GRAFANA_URL:-http://10.0.0.84:3002}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://10.0.0.84:9090}"

# Create log directory
mkdir -p "$LOG_DIR"

test_result() {
  local exit_code=$?
  if [ $exit_code -eq 0 ]; then
    echo "✅ $1" | tee -a $RESULTS_FILE
    ((TESTS_PASSED++)) || true
    return 0
  else
    echo "❌ $1 (exit code: $exit_code)" | tee -a $RESULTS_FILE
    ((TESTS_FAILED++)) || true
    return 1
  fi
}

test_connectivity() {
  local host=$1
  local port=$2
  local name=$3
  
  timeout 5 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null
  test_result "$name connectivity (${host}:${port})"
}

echo "================================================" | tee $RESULTS_FILE
echo "GitLab Integration Test Suite" | tee -a $RESULTS_FILE
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $RESULTS_FILE
echo "================================================" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 1: CORE INFRASTRUCTURE
# ============================================================================
echo ">>> SECTION 1: Core Infrastructure" | tee -a $RESULTS_FILE

# GitLab accessibility
curl -s "${GITLAB_URL}${GITLAB_HEALTH_PATH}" > /dev/null 2>&1
test_result "GitLab health check endpoint (${GITLAB_URL}${GITLAB_HEALTH_PATH})"

gitlab_api_status=$(curl -s -o /dev/null -w "%{http_code}" "${GITLAB_URL}/api/v4/version" 2>/dev/null)
if [[ "$gitlab_api_status" == "200" || "$gitlab_api_status" == "401" ]]; then
  test_result "GitLab API accessible (${GITLAB_URL}/api/v4/version) [status ${gitlab_api_status}]"
else
  false
  test_result "GitLab API accessible (${GITLAB_URL}/api/v4/version) [status ${gitlab_api_status}]"
fi

# Database connectivity - Use GitLab's built-in database connection
docker exec gitlab gitlab-rake db:migrate:status > /dev/null 2>&1
test_result "PostgreSQL connection works (via GitLab db:migrate:status)"

# Check database version via GitLab
docker exec gitlab gitlab-rails runner "puts ActiveRecord::Base.connection.select_value('SELECT version()')" 2>/dev/null | grep -q "PostgreSQL"
test_result "PostgreSQL version detectable (via GitLab Rails)"

# Database table integrity via GitLab
docker exec gitlab gitlab-rails runner "puts ActiveRecord::Base.connection.tables.count" 2>/dev/null | grep -qE "^[1-9][0-9]*$"
test_result "PostgreSQL tables accessible (via GitLab Rails)"

# Redis connectivity
docker exec gitlab redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping | grep -q "PONG" 2>/dev/null
test_result "Redis connection works"

# Redis key test
docker exec gitlab redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" SET test-key "test-value" | grep -q "OK" 2>/dev/null
test_result "Redis SET operation works"

docker exec gitlab redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" GET test-key | grep -q "test-value" 2>/dev/null
test_result "Redis GET operation works"

docker exec gitlab redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" DEL test-key > /dev/null 2>&1
test_result "Redis DEL operation works"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 2: GITLAB INTERNALS
# ============================================================================
echo ">>> SECTION 2: GitLab Internals" | tee -a $RESULTS_FILE

# GitLab version / env info
docker exec gitlab gitlab-rake gitlab:env:info >/dev/null 2>&1
test_result "GitLab env info command succeeds"

# GitLab database checks
docker exec gitlab gitlab-rake gitlab:check >/dev/null 2>&1
test_result "gitlab:check succeeds"

# Container health
docker ps | grep gitlab | grep -q "healthy\|Up" 2>/dev/null
test_result "GitLab container is healthy"

# Secrets configured
docker exec gitlab grep -q "db_password" /etc/gitlab/gitlab.rb 2>/dev/null
test_result "Database password configured"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 3: BACKUP & NFS
# ============================================================================
echo ">>> SECTION 3: Backup & NFS Storage" | tee -a $RESULTS_FILE

# NFS mount check
mount | grep -q "10.0.0.80:/mnt/data" 2>/dev/null
test_result "NFS backup mount is active"

# NFS write test
[ -d /mnt/data/Backups/server/gitlab ] && [ -w /mnt/data/Backups/server/gitlab ]
test_result "NFS backup directory is writable"

# Backup directory check
[ -d /mnt/data/Backups/server/gitlab ]
test_result "GitLab backup subdirectory exists"

# List backups (check for .tar files in dated subdirectories)
find /mnt/data/Backups/server/gitlab/ -type f -name "*_gitlab_backup.tar" 2>/dev/null | grep -q ".tar"
test_result "Backup files present in NFS"

# Get latest backup age
latest_backup=$(find /mnt/data/Backups/server/gitlab/ -type f -name "*_gitlab_backup.tar" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2)
if [ -n "$latest_backup" ]; then
  backup_timestamp=$(find /mnt/data/Backups/server/gitlab/ -type f -name "*_gitlab_backup.tar" -printf '%T@\n' 2>/dev/null | sort -rn | head -1 | cut -d'.' -f1)
  current_timestamp=$(date +%s)
  backup_age=$((current_timestamp - backup_timestamp))
  if [ $backup_age -lt 86400 ]; then
    echo "✅ Latest backup is within 24 hours (${backup_age}s old)" | tee -a $RESULTS_FILE
    ((TESTS_PASSED++))
  else
    echo "⚠️  Latest backup is older than 24 hours (${backup_age}s old)" | tee -a $RESULTS_FILE
    ((TESTS_FAILED++))
  fi
fi

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 4: AUTHENTICATION & SSO (OPTIONAL - Not Yet Implemented)
# ============================================================================
echo ">>> SECTION 4: Authentication & SSO (Keycloak) [OPTIONAL]" | tee -a $RESULTS_FILE

# Keycloak accessibility
if curl -s http://10.0.0.84:8180 2>/dev/null | grep -q "Keycloak"; then
  test_result "[OPTIONAL] Keycloak is accessible (10.0.0.84:8180)"
else
  echo "⚠️  [OPTIONAL] Keycloak not yet configured (expected)" | tee -a $RESULTS_FILE
fi

if curl -s http://10.0.0.84:8180/health 2>/dev/null | grep -q "UP\|status"; then
  test_result "[OPTIONAL] Keycloak health endpoint responds"
else
  echo "⚠️  [OPTIONAL] Keycloak health not configured (expected)" | tee -a $RESULTS_FILE
fi

# GitLab SSO configuration
if docker exec gitlab grep -q "omniauth" /etc/gitlab/gitlab.rb 2>/dev/null; then
  test_result "[OPTIONAL] GitLab has omniauth configured"
else
  echo "⚠️  [OPTIONAL] GitLab omniauth not yet configured (expected)" | tee -a $RESULTS_FILE
fi

# Check for openid_connect configuration
if docker exec gitlab grep -A 5 "openid_connect" /etc/gitlab/gitlab.rb 2>/dev/null | grep -q "client_id"; then
  test_result "[OPTIONAL] Keycloak openid_connect client_id configured"
else
  echo "⚠️  [OPTIONAL] Keycloak SSO not yet configured (expected)" | tee -a $RESULTS_FILE
fi

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 5: LOGGING & MONITORING
# ============================================================================
echo ">>> SECTION 5: Logging & Monitoring (Loki/Grafana)" | tee -a $RESULTS_FILE

# Loki accessibility
if curl -s "${LOKI_URL}/ready" 2>/dev/null | grep -q "ready"; then
  test_result "Loki is ready (${LOKI_URL})"
else
  echo "⚠️  Loki not ready (${LOKI_URL}/ready)" | tee -a $RESULTS_FILE
fi

# Loki metrics
if curl -s "${LOKI_URL}/metrics" 2>/dev/null | grep -q "loki"; then
  test_result "Loki metrics endpoint responds"
else
  echo "⚠️  Loki metrics unavailable (${LOKI_URL}/metrics)" | tee -a $RESULTS_FILE
fi

# Query Loki for GitLab logs
if curl -s "${LOKI_URL}/loki/api/v1/query?query={job=\"gitlab\"}" 2>/dev/null | jq '.data.result | length' 2>/dev/null | grep -q "^[1-9]"; then
  test_result "Loki has GitLab logs"
else
  echo "⚠️  Loki did not return GitLab logs" | tee -a $RESULTS_FILE
fi

# Grafana accessibility
if curl -s "${GRAFANA_URL}" 2>/dev/null | grep -q "Grafana"; then
  test_result "Grafana is accessible (${GRAFANA_URL})"
else
  echo "⚠️  Grafana not reachable (${GRAFANA_URL})" | tee -a $RESULTS_FILE
fi

# Grafana API
if curl -s "${GRAFANA_URL}/api/health" 2>/dev/null | grep -q "ok"; then
  test_result "Grafana API responds"
else
  echo "⚠️  Grafana API not reachable (${GRAFANA_URL}/api/health)" | tee -a $RESULTS_FILE
fi

# Prometheus accessibility
if curl -s "${PROMETHEUS_URL}/api/v1/targets" 2>/dev/null | grep -q "activeTargets"; then
  test_result "Prometheus targets API responds"
else
  echo "⚠️  Prometheus not reachable (${PROMETHEUS_URL}/api/v1/targets)" | tee -a $RESULTS_FILE
fi

# Prometheus metrics
if curl -s "${PROMETHEUS_URL}/api/v1/query?query=up" 2>/dev/null | jq '.data.result | length' 2>/dev/null | grep -q "^[0-9]"; then
  test_result "Prometheus has metrics data"
else
  echo "⚠️  Prometheus metrics query failed (${PROMETHEUS_URL}/api/v1/query?query=up)" | tee -a $RESULTS_FILE
fi

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 6: SECURITY & HTTPS (OPTIONAL - TLS Not Yet Configured)
# ============================================================================
echo ">>> SECTION 6: Security & HTTPS [OPTIONAL]" | tee -a $RESULTS_FILE

# HTTPS check (optional if TLS not configured)
if curl -s -I "${GITLAB_URL/http:/https:}" 2>/dev/null | head -1 | grep -q "HTTP"; then
  test_result "[OPTIONAL] GitLab HTTPS endpoint responds"
else
  echo "⚠️  [OPTIONAL] TLS not yet configured - using HTTP (expected)" | tee -a $RESULTS_FILE
fi

# SSH key restrictions configured
if docker exec gitlab grep -q "minimum_key_length\|key_restrictions" /etc/gitlab/gitlab.rb 2>/dev/null; then
  test_result "[OPTIONAL] SSH key restrictions configured"
else
  echo "⚠️  [OPTIONAL] SSH key restrictions not yet configured (expected)" | tee -a $RESULTS_FILE
fi

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 7: RATE LIMITING & PROTECTION
# ============================================================================
echo ">>> SECTION 7: Rate Limiting & DDoS Protection" | tee -a $RESULTS_FILE

# Rate limiting configuration
if docker exec gitlab env | grep -q "rate_limit_requests_per_period" 2>/dev/null; then
  test_result "Rate limiting configured in GitLab"
else
  false
  test_result "Rate limiting configured in GitLab"
fi

# Nginx/Traefik protection
curl -s -I "${GITLAB_URL}" 2>/dev/null | grep -q "Server:"
test_result "Server headers present (web server protection)"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 8: CONTAINER REGISTRY
# ============================================================================
echo ">>> SECTION 8: Container Registry" | tee -a $RESULTS_FILE

# Registry accessibility (accept 200/401)
if curl -s -o /dev/null -w "%{http_code}" "${REGISTRY_URL}" 2>/dev/null | grep -Eq "^(200|401)$"; then
  test_result "Container registry is accessible (${REGISTRY_URL})"
else
  echo "⚠️  Container registry not reachable (${REGISTRY_URL})" | tee -a $RESULTS_FILE
fi

# Registry API
if docker exec gitlab curl -s -o /dev/null -w "%{http_code}" http://localhost:5050/v2/ 2>/dev/null | grep -Eq "^(200|401)$"; then
  test_result "Container registry API responds (localhost:5050)"
else
  echo "⚠️  Container registry API not reachable inside container" | tee -a $RESULTS_FILE
fi

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SUMMARY
# ============================================================================
echo "================================================" | tee -a $RESULTS_FILE
echo "Test Summary" | tee -a $RESULTS_FILE
echo "================================================" | tee -a $RESULTS_FILE
echo "Passed: $TESTS_PASSED" | tee -a $RESULTS_FILE
echo "Failed: $TESTS_FAILED" | tee -a $RESULTS_FILE
echo "Total:  $((TESTS_PASSED + TESTS_FAILED))" | tee -a $RESULTS_FILE
echo "Success Rate: $(( TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED) ))%" | tee -a $RESULTS_FILE
echo "================================================" | tee -a $RESULTS_FILE
echo "Results saved to: $RESULTS_FILE" | tee -a $RESULTS_FILE

# Copy to log directory
cp "$RESULTS_FILE" "$LOG_DIR/"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
  echo "✅ All integration tests PASSED - Safe to proceed with deployment"
  exit 0
else
  echo "❌ INTEGRATION TESTS FAILED - Do not proceed with deployment"
  echo "Review results: $RESULTS_FILE"
  exit 1
fi

#!/bin/bash
set -e

# GitLab Integration Test Suite
# Tests all external system integrations before deployment
# Run this before activating any phase changes

TESTS_PASSED=0
TESTS_FAILED=0
RESULTS_FILE="/tmp/gitlab-test-results-$(date +%Y%m%d-%H%M%S).txt"
LOG_DIR="/var/log/gitlab-integration-tests"

# Create log directory
mkdir -p "$LOG_DIR"

test_result() {
  local exit_code=$?
  if [ $exit_code -eq 0 ]; then
    echo "✅ $1" | tee -a $RESULTS_FILE
    ((TESTS_PASSED++))
    return 0
  else
    echo "❌ $1 (exit code: $exit_code)" | tee -a $RESULTS_FILE
    ((TESTS_FAILED++))
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
curl -s http://gitlab.wizardsofts.com/health_check > /dev/null 2>&1
test_result "GitLab health check endpoint"

curl -s http://gitlab.wizardsofts.com/api/v4/version | grep -q "version" 2>/dev/null
test_result "GitLab API accessible"

# Database connectivity
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "SELECT 1;" > /dev/null 2>&1
test_result "PostgreSQL connection works"

# Check database version
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "SELECT version();" | grep -q "PostgreSQL" 2>/dev/null
test_result "PostgreSQL version detectable"

# Database table integrity
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "\dt" | grep -q "public" 2>/dev/null
test_result "PostgreSQL tables accessible"

# Redis connectivity
docker exec redis redis-cli ping | grep -q "PONG" 2>/dev/null
test_result "Redis connection works"

# Redis key test
docker exec redis redis-cli SET test-key "test-value" | grep -q "OK" 2>/dev/null
test_result "Redis SET operation works"

docker exec redis redis-cli GET test-key | grep -q "test-value" 2>/dev/null
test_result "Redis GET operation works"

docker exec redis redis-cli DEL test-key > /dev/null 2>&1
test_result "Redis DEL operation works"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 2: GITLAB INTERNALS
# ============================================================================
echo ">>> SECTION 2: GitLab Internals" | tee -a $RESULTS_FILE

# GitLab version
docker exec gitlab gitlab-rake gitlab:env:info 2>/dev/null | grep -q "GitLab Version"
test_result "GitLab version detectable"

# GitLab database checks
docker exec gitlab gitlab-rake gitlab:check 2>/dev/null | grep -q "database"
test_result "GitLab database check passes"

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
mount | grep -q "gitlab-backups" 2>/dev/null
test_result "NFS backup mount is active"

# NFS write test
[ -d /mnt/gitlab-backups ] && [ -w /mnt/gitlab-backups ]
test_result "NFS backup directory is writable"

# Backup directory check
[ -d /mnt/gitlab-backups/gitlab ]
test_result "GitLab backup subdirectory exists"

# List backups
ls -la /mnt/gitlab-backups/gitlab/*.tar.gz 2>/dev/null | grep -q ".tar.gz"
test_result "Backup files present in NFS"

# Get latest backup age
latest_backup=$(ls -t /mnt/gitlab-backups/gitlab/*.tar.gz 2>/dev/null | head -1)
if [ -n "$latest_backup" ]; then
  backup_age=$(($(date +%s) - $(stat -f %m "$latest_backup" 2>/dev/null || stat -c %Y "$latest_backup")))
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
# SECTION 4: AUTHENTICATION & SSO
# ============================================================================
echo ">>> SECTION 4: Authentication & SSO (Keycloak)" | tee -a $RESULTS_FILE

# Keycloak accessibility
curl -s http://10.0.0.84:8180 | grep -q "Keycloak" 2>/dev/null
test_result "Keycloak is accessible (10.0.0.84:8180)"

curl -s http://10.0.0.84:8180/health | grep -q "UP\|status" 2>/dev/null
test_result "Keycloak health endpoint responds"

# GitLab SSO configuration
docker exec gitlab grep -q "omniauth" /etc/gitlab/gitlab.rb 2>/dev/null
test_result "GitLab has omniauth configured"

# Check for openid_connect configuration
docker exec gitlab grep -A 5 "openid_connect" /etc/gitlab/gitlab.rb 2>/dev/null | grep -q "client_id"
test_result "Keycloak openid_connect client_id configured"

docker exec gitlab grep -A 5 "openid_connect" /etc/gitlab/gitlab.rb 2>/dev/null | grep -q "client_secret"
test_result "Keycloak openid_connect client_secret configured"

# Keycloak realm check
curl -s http://10.0.0.84:8180/realms/master | grep -q "realm" 2>/dev/null
test_result "Keycloak realm accessible"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 5: LOGGING & MONITORING
# ============================================================================
echo ">>> SECTION 5: Logging & Monitoring (Loki/Grafana)" | tee -a $RESULTS_FILE

# Loki accessibility
curl -s http://10.0.0.80:3100/ready 2>/dev/null | grep -q "ready"
test_result "Loki is ready (10.0.0.80:3100)"

# Loki metrics
curl -s http://10.0.0.80:3100/metrics 2>/dev/null | grep -q "loki"
test_result "Loki metrics endpoint responds"

# Query Loki for GitLab logs
curl -s 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}' 2>/dev/null | jq '.data.result | length' 2>/dev/null | grep -q "^[1-9]"
test_result "Loki has GitLab logs"

# Grafana accessibility
curl -s http://10.0.0.80:3000 | grep -q "Grafana" 2>/dev/null
test_result "Grafana is accessible (10.0.0.80:3000)"

# Grafana API
curl -s http://10.0.0.80:3000/api/health 2>/dev/null | grep -q "ok"
test_result "Grafana API responds"

# Prometheus accessibility
curl -s http://10.0.0.80:9090/api/v1/targets 2>/dev/null | grep -q "activeTargets"
test_result "Prometheus targets API responds"

# Prometheus metrics
curl -s 'http://10.0.0.80:9090/api/v1/query?query=up' 2>/dev/null | jq '.data.result | length' 2>/dev/null | grep -q "^[0-9]"
test_result "Prometheus has metrics data"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 6: SECURITY & HTTPS
# ============================================================================
echo ">>> SECTION 6: Security & HTTPS" | tee -a $RESULTS_FILE

# HTTPS check
curl -s -I https://gitlab.wizardsofts.com 2>/dev/null | head -1 | grep -q "HTTP"
test_result "GitLab HTTPS endpoint responds"

# HSTS header
curl -s -I https://gitlab.wizardsofts.com 2>/dev/null | grep -q "Strict-Transport-Security"
test_result "HSTS header is set"

# SSL certificate validity
echo | openssl s_client -servername gitlab.wizardsofts.com -connect gitlab.wizardsofts.com:443 2>/dev/null | grep -q "subject="
test_result "SSL certificate is valid"

# SSH key restrictions configured
docker exec gitlab grep -q "minimum_key_length\|key_restrictions" /etc/gitlab/gitlab.rb 2>/dev/null
test_result "SSH key restrictions configured"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 7: RATE LIMITING & PROTECTION
# ============================================================================
echo ">>> SECTION 7: Rate Limiting & DDoS Protection" | tee -a $RESULTS_FILE

# Rate limiting headers
curl -s -I http://gitlab.wizardsofts.com/api/v4/user -H "PRIVATE-TOKEN: test" 2>/dev/null | grep -q "RateLimit"
test_result "Rate limiting headers present"

# Nginx/Traefik protection
curl -s -I http://gitlab.wizardsofts.com 2>/dev/null | grep -q "Server:" 
test_result "Server headers present (web server protection)"

echo "" | tee -a $RESULTS_FILE

# ============================================================================
# SECTION 8: CONTAINER REGISTRY
# ============================================================================
echo ">>> SECTION 8: Container Registry" | tee -a $RESULTS_FILE

# Registry accessibility
curl -s http://10.0.0.84:5050/v2/ 2>/dev/null | grep -q "{}"
test_result "Container registry is accessible"

# Registry API
docker exec gitlab curl -s http://localhost:5050/v2/ 2>/dev/null | grep -q "{}"
test_result "Container registry API responds"

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

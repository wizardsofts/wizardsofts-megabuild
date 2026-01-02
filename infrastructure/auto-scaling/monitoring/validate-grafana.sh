#!/bin/bash
#
# Grafana Monitoring Validation Script
# Tests all core functionality and reports status
#
# Usage: bash validate-grafana.sh
#

set -e

echo "========================================="
echo "   GRAFANA MONITORING VALIDATION"
echo "========================================="

FAILURES=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Container Status
echo -e "\n1. CONTAINER STATUS"
echo "-------------------"
if docker ps | grep -q "grafana.*healthy"; then
    echo -e "${GREEN}✅ Grafana: UP and HEALTHY${NC}"
    docker ps --format "   {{.Names}}: {{.Status}}" | grep grafana
else
    echo -e "${RED}❌ Grafana: Not healthy${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 2. API Health
echo -e "\n2. API HEALTH"
echo "-------------"
HEALTH=$(curl -s http://localhost:3002/api/health 2>/dev/null || echo '{"database":"error"}')
DB_STATUS=$(echo "$HEALTH" | python3 -c "import json, sys; print(json.load(sys.stdin).get('database', 'unknown'))" 2>/dev/null || echo "error")
VERSION=$(echo "$HEALTH" | python3 -c "import json, sys; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")

if [ "$DB_STATUS" = "ok" ]; then
    echo -e "${GREEN}✅ API Health: Database OK${NC}"
    echo "   Version: $VERSION"
else
    echo -e "${RED}❌ API Health: Failed${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 3. Authentication
echo -e "\n3. AUTHENTICATION"
echo "-----------------"
USER_INFO=$(curl -s -u admin:admin http://localhost:3002/api/user 2>/dev/null || echo '{}')
USERNAME=$(echo "$USER_INFO" | python3 -c "import json, sys; print(json.load(sys.stdin).get('login', 'failed'))" 2>/dev/null || echo "failed")

if [ "$USERNAME" = "admin" ]; then
    echo -e "${GREEN}✅ Basic Auth: Working${NC}"
    ROLE=$(echo "$USER_INFO" | python3 -c "import json, sys; print(json.load(sys.stdin).get('orgRole', 'N/A'))" 2>/dev/null || echo "N/A")
    echo "   User: admin"
    echo "   Role: $ROLE"
else
    echo -e "${RED}❌ Basic Auth: Failed${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 4. Datasources
echo -e "\n4. DATASOURCES"
echo "--------------"
DATASOURCES=$(curl -s -u admin:admin http://localhost:3002/api/datasources 2>/dev/null || echo '[]')
DS_COUNT=$(echo "$DATASOURCES" | python3 -c "import json, sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$DS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $DS_COUNT datasource(s)${NC}"
    echo "$DATASOURCES" | python3 -c "
import json, sys
try:
    for ds in json.load(sys.stdin):
        name = ds.get('name', 'N/A')
        ds_type = ds.get('type', 'N/A')
        is_default = '(default)' if ds.get('isDefault', False) else ''
        print(f'   - {name}: {ds_type} {is_default}')
except:
    pass
" 2>/dev/null
else
    echo -e "${YELLOW}⚠️  No datasources found${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 5. Dashboards
echo -e "\n5. DASHBOARDS"
echo "-------------"
DASHBOARDS=$(curl -s -u admin:admin 'http://localhost:3002/api/search?type=dash-db' 2>/dev/null || echo '[]')
DASH_COUNT=$(echo "$DASHBOARDS" | python3 -c "import json, sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$DASH_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $DASH_COUNT dashboard(s)${NC}"
    echo "$DASHBOARDS" | python3 -c "
import json, sys
try:
    for dash in json.load(sys.stdin):
        title = dash.get('title', 'N/A')
        uid = dash.get('uid', 'N/A')
        print(f'   - {title} (uid: {uid})')
except:
    pass
" 2>/dev/null
else
    echo -e "${YELLOW}⚠️  No dashboards found${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 6. Prometheus Connectivity
echo -e "\n6. PROMETHEUS CONNECTIVITY"
echo "--------------------------"
PROM_TEST=$(curl -s -u admin:admin 'http://localhost:3002/api/datasources/proxy/uid/prometheus/api/v1/query?query=up' 2>/dev/null || echo '{"status":"error"}')
PROM_STATUS=$(echo "$PROM_TEST" | python3 -c "import json, sys; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null || echo "error")

if [ "$PROM_STATUS" = "success" ]; then
    echo -e "${GREEN}✅ Prometheus datasource: Working${NC}"
    RESULT_COUNT=$(echo "$PROM_TEST" | python3 -c "import json, sys; print(len(json.load(sys.stdin).get('data', {}).get('result', [])))" 2>/dev/null || echo "0")
    echo "   Query results: $RESULT_COUNT metrics"
else
    echo -e "${YELLOW}⚠️  Prometheus datasource: Issue detected${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 7. Keycloak Integration
echo -e "\n7. KEYCLOAK SSO INTEGRATION"
echo "---------------------------"
OAUTH_CONFIG=$(docker exec grafana cat /etc/grafana/grafana.ini 2>/dev/null | grep -A 10 "auth.generic_oauth" || echo "")

if echo "$OAUTH_CONFIG" | grep -q "enabled = true"; then
    echo -e "${GREEN}✅ OAuth: Enabled${NC}"
    CLIENT_ID=$(echo "$OAUTH_CONFIG" | grep "client_id" | cut -d'=' -f2 | tr -d ' ' || echo "N/A")
    AUTH_URL=$(echo "$OAUTH_CONFIG" | grep "auth_url" | cut -d'=' -f2 | tr -d ' ' | head -1 || echo "N/A")
    echo "   Client ID: $CLIENT_ID"
    echo "   Auth URL: $AUTH_URL"
else
    echo -e "${YELLOW}⚠️  OAuth: Not enabled${NC}"
fi

# 8. Network Connectivity
echo -e "\n8. NETWORK CONNECTIVITY"
echo "------------------------"
GRAFANA_NETWORKS=$(docker inspect grafana --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}' 2>/dev/null || echo "")

if echo "$GRAFANA_NETWORKS" | grep -q "microservices-overlay"; then
    echo -e "${GREEN}✅ Grafana on microservices-overlay network${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana not on microservices-overlay${NC}"
fi

# Test Keycloak reachability
if docker exec grafana ping -c 1 keycloak >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Grafana → Keycloak: Reachable${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana → Keycloak: Not reachable${NC}"
fi

# Summary
echo -e "\n========================================="
echo "   VALIDATION SUMMARY"
echo "========================================="

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "System Status: OPERATIONAL"
    echo "Grafana URL: http://$(hostname -I | awk '{print $1}'):3002"
    echo "Login: admin / admin"
    exit 0
else
    echo -e "${RED}❌ $FAILURES CHECK(S) FAILED${NC}"
    echo ""
    echo "System Status: DEGRADED"
    echo "Review failures above and check logs:"
    echo "  docker logs grafana --tail 50"
    exit 1
fi

#!/bin/bash

# Grafana Configuration Validation Script
# This script checks if all required files are in place before deployment

set -e

echo "🔍 Validating Grafana Configuration..."
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} Missing: $1"
        ((ERRORS++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} Missing directory: $1"
        ((ERRORS++))
    fi
}

check_json() {
    if python3 -c "import json; json.load(open('$1'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Valid JSON: $1"
    else
        echo -e "${RED}✗${NC} Invalid JSON: $1"
        ((ERRORS++))
    fi
}

check_yaml() {
    if grep -q "apiVersion:" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Valid YAML: $1"
    else
        echo -e "${YELLOW}⚠${NC} Check YAML: $1"
        ((WARNINGS++))
    fi
}

echo "📁 Checking directory structure..."
check_dir "monitoring/grafana"
check_dir "monitoring/grafana/dashboards"
check_dir "monitoring/grafana/provisioning"
check_dir "monitoring/grafana/provisioning/dashboards"
check_dir "monitoring/grafana/provisioning/datasources"
check_dir "monitoring/grafana/provisioning/alerting"
check_dir "monitoring/grafana/provisioning/preferences"
echo ""

echo "📄 Checking dashboard files..."
check_file "monitoring/grafana/dashboards/executive-dashboard.json"
check_file "monitoring/grafana/dashboards/autoscaling-dashboard.json"
check_json "monitoring/grafana/dashboards/executive-dashboard.json"
check_json "monitoring/grafana/dashboards/autoscaling-dashboard.json"
echo ""

echo "⚙️ Checking provisioning files..."
check_file "monitoring/grafana/provisioning/dashboards/dashboards.yaml"
check_file "monitoring/grafana/provisioning/datasources/prometheus.yaml"
check_file "monitoring/grafana/provisioning/alerting/alerts.yaml"
check_file "monitoring/grafana/provisioning/preferences/preferences.yaml"
check_yaml "monitoring/grafana/provisioning/dashboards/dashboards.yaml"
check_yaml "monitoring/grafana/provisioning/datasources/prometheus.yaml"
check_yaml "monitoring/grafana/provisioning/alerting/alerts.yaml"
check_yaml "monitoring/grafana/provisioning/preferences/preferences.yaml"
echo ""

echo "🔧 Checking configuration files..."
check_file "monitoring/grafana/grafana.ini"
check_file "docker-compose.yml"
echo ""

echo "🔍 Checking dashboard UIDs..."
EXEC_UID=$(grep -o '"uid":\s*"[^"]*"' monitoring/grafana/dashboards/executive-dashboard.json | head -1 | cut -d'"' -f4)
AUTO_UID=$(grep -o '"uid":\s*"[^"]*"' monitoring/grafana/dashboards/autoscaling-dashboard.json | head -1 | cut -d'"' -f4)

if [ "$EXEC_UID" == "executive-overview" ]; then
    echo -e "${GREEN}✓${NC} Executive dashboard UID: $EXEC_UID"
else
    echo -e "${RED}✗${NC} Executive dashboard UID should be 'executive-overview', got: $EXEC_UID"
    ((ERRORS++))
fi

if [ "$AUTO_UID" == "autoscaling-platform" ]; then
    echo -e "${GREEN}✓${NC} Autoscaling dashboard UID: $AUTO_UID"
else
    echo -e "${RED}✗${NC} Autoscaling dashboard UID should be 'autoscaling-platform', got: $AUTO_UID"
    ((ERRORS++))
fi
echo ""

echo "🏠 Checking default dashboard setting..."
if grep -q "homeDashboardUID: executive-overview" monitoring/grafana/provisioning/preferences/preferences.yaml; then
    echo -e "${GREEN}✓${NC} Default dashboard set to: executive-overview"
else
    echo -e "${YELLOW}⚠${NC} Default dashboard might not be set correctly"
    ((WARNINGS++))
fi
echo ""

echo "🐳 Checking docker-compose.yml volume mounts..."
if grep -q "./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro" docker-compose.yml; then
    echo -e "${GREEN}✓${NC} Dashboards volume mount correct"
else
    echo -e "${RED}✗${NC} Dashboards volume mount incorrect"
    ((ERRORS++))
fi

if grep -q "./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro" docker-compose.yml; then
    echo -e "${GREEN}✓${NC} Provisioning volume mount correct"
else
    echo -e "${RED}✗${NC} Provisioning volume mount incorrect"
    ((ERRORS++))
fi
echo ""

echo "📊 Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Configuration is ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy to your server using FIX_GRAFANA_DASHBOARDS.md"
    echo "2. Or test locally: docker-compose up -d grafana"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found. Review before deploying.${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found. Fix these before deploying.${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS warning(s) also found.${NC}"
    fi
    exit 1
fi

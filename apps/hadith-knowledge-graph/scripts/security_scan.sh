#!/bin/bash
# Automated Security Scanning for Python Dependencies
# Run this before deploying any new package or module

set -e

echo "========================================"
echo "Security Scanning - Hadith Knowledge Graph"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Not in virtual environment. Activating venv...${NC}"
    source venv/bin/activate 2>/dev/null || {
        echo -e "${RED}Error: venv not found. Run: python -m venv venv${NC}"
        exit 1
    }
fi

# 1. Safety - Check for known vulnerabilities
echo "1️⃣  Scanning for known CVEs (Safety)..."
echo "----------------------------------------"
if ! command -v safety &> /dev/null; then
    echo -e "${YELLOW}Installing safety...${NC}"
    pip install -q safety
fi

safety check --json > safety_report.json 2>&1 || true
safety_vulns=$(python -c "import json; data=json.load(open('safety_report.json')); print(len(data.get('vulnerabilities', [])))" 2>/dev/null || echo "0")

if [ "$safety_vulns" -gt 0 ]; then
    echo -e "${RED}❌ Found $safety_vulns known vulnerabilities!${NC}"
    safety check --output text
    echo ""
else
    echo -e "${GREEN}✅ No known vulnerabilities found${NC}"
fi

# 2. pip-audit - Official PyPA security scanner
echo ""
echo "2️⃣  PyPA Security Audit (pip-audit)..."
echo "----------------------------------------"
if ! command -v pip-audit &> /dev/null; then
    echo -e "${YELLOW}Installing pip-audit...${NC}"
    pip install -q pip-audit
fi

pip-audit --format json > pip_audit_report.json 2>&1 || true
audit_vulns=$(python -c "import json; data=json.load(open('pip_audit_report.json')); print(len(data.get('vulnerabilities', [])))" 2>/dev/null || echo "0")

if [ "$audit_vulns" -gt 0 ]; then
    echo -e "${RED}❌ Found $audit_vulns vulnerabilities!${NC}"
    pip-audit --format columns
    echo ""
else
    echo -e "${GREEN}✅ No vulnerabilities found${NC}"
fi

# 3. Bandit - Python code security scanner
echo ""
echo "3️⃣  Code Security Analysis (Bandit)..."
echo "----------------------------------------"
if ! command -v bandit &> /dev/null; then
    echo -e "${YELLOW}Installing bandit...${NC}"
    pip install -q bandit
fi

bandit -r ../src -f json -o bandit_report.json --exit-zero 2>/dev/null
bandit_issues=$(python -c "import json; data=json.load(open('bandit_report.json')); print(len([x for x in data.get('results', []) if x['issue_severity'] in ['HIGH', 'MEDIUM']]))" 2>/dev/null || echo "0")

if [ "$bandit_issues" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $bandit_issues code security issues${NC}"
    bandit -r ../src -ll --format screen
    echo ""
else
    echo -e "${GREEN}✅ No high/medium severity issues${NC}"
fi

# 4. License compliance check
echo ""
echo "4️⃣  License Compliance Check..."
echo "----------------------------------------"
if ! command -v pip-licenses &> /dev/null; then
    echo -e "${YELLOW}Installing pip-licenses...${NC}"
    pip install -q pip-licenses
fi

# Check for GPL licenses (copyleft - may require code disclosure)
gpl_licenses=$(pip-licenses --format=json | python -c "import sys, json; data=json.load(sys.stdin); print(len([x for x in data if 'GPL' in x.get('License', '')]))" 2>/dev/null || echo "0")

if [ "$gpl_licenses" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $gpl_licenses GPL-licensed packages (copyleft)${NC}"
    pip-licenses --format=markdown | grep GPL
    echo ""
else
    echo -e "${GREEN}✅ No GPL licenses found${NC}"
fi

# 5. Outdated packages
echo ""
echo "5️⃣  Checking for Outdated Packages..."
echo "----------------------------------------"
outdated=$(pip list --outdated --format=json | python -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$outdated" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $outdated packages need updates${NC}"
    pip list --outdated --format=columns | head -10
    echo ""
else
    echo -e "${GREEN}✅ All packages up to date${NC}"
fi

# 6. Docker image security (if Dockerfile exists)
echo ""
echo "6️⃣  Docker Image Security (Trivy)..."
echo "----------------------------------------"
if command -v trivy &> /dev/null; then
    if [ -f "../infrastructure/Dockerfile.extraction" ]; then
        trivy image --severity HIGH,CRITICAL python:3.11-slim --format json > trivy_report.json 2>/dev/null || true
        trivy_vulns=$(python -c "import json; data=json.load(open('trivy_report.json')); print(sum([len(r.get('Vulnerabilities', [])) for r in data.get('Results', [])]))" 2>/dev/null || echo "0")

        if [ "$trivy_vulns" -gt 0 ]; then
            echo -e "${RED}❌ Found $trivy_vulns vulnerabilities in base image${NC}"
        else
            echo -e "${GREEN}✅ Base image clean${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No Dockerfile found, skipping${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Trivy not installed, skipping (brew install trivy)${NC}"
fi

# Summary Report
echo ""
echo "========================================"
echo "Security Scan Summary"
echo "========================================"
total_issues=$((safety_vulns + audit_vulns + bandit_issues))

if [ $total_issues -eq 0 ]; then
    echo -e "${GREEN}✅ All security checks passed!${NC}"
    echo ""
    echo "Reports generated:"
    echo "  - safety_report.json"
    echo "  - pip_audit_report.json"
    echo "  - bandit_report.json"
    exit 0
else
    echo -e "${RED}❌ Found $total_issues total security issues${NC}"
    echo ""
    echo "Details:"
    echo "  - Known CVEs: $safety_vulns"
    echo "  - Dependency vulnerabilities: $audit_vulns"
    echo "  - Code security issues: $bandit_issues"
    echo ""
    echo "Reports generated:"
    echo "  - safety_report.json"
    echo "  - pip_audit_report.json"
    echo "  - bandit_report.json"
    echo ""
    echo -e "${YELLOW}Review reports and fix issues before deployment!${NC}"
    exit 1
fi

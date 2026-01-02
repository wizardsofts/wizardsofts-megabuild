#!/bin/bash
# Setup Local Development with Traefik
# This script configures /etc/hosts and starts services

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Wizardsofts Local Traefik Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running on macOS or Linux
if [[ "$OSTYPE" != "darwin"* ]] && [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}This script only supports macOS and Linux${NC}"
    exit 1
fi

# ============================================================================
# Step 1: Configure /etc/hosts
# ============================================================================

echo -e "${YELLOW}Step 1: Configuring /etc/hosts...${NC}"
echo ""

HOSTS_ENTRIES="
# Wizardsofts Megabuild - Local Development
127.0.0.1 www.wizardsofts.local
127.0.0.1 dailydeenguide.local
127.0.0.1 quant.wizardsofts.local
127.0.0.1 api.wizardsofts.local
127.0.0.1 eureka.wizardsofts.local
127.0.0.1 traefik.wizardsofts.local
127.0.0.1 grafana.wizardsofts.local
127.0.0.1 prometheus.wizardsofts.local
127.0.0.1 gitlab.wizardsofts.local
127.0.0.1 nexus.wizardsofts.local
127.0.0.1 n8n.wizardsofts.local
127.0.0.1 keycloak.wizardsofts.local
"

# Check if entries already exist
if grep -q "www.wizardsofts.local" /etc/hosts 2>/dev/null; then
    echo -e "${GREEN}✓ /etc/hosts already configured${NC}"
else
    echo "Adding entries to /etc/hosts (requires sudo)..."
    echo "$HOSTS_ENTRIES" | sudo tee -a /etc/hosts > /dev/null
    echo -e "${GREEN}✓ /etc/hosts updated${NC}"
fi

echo ""

# ============================================================================
# Step 2: Stop any existing services
# ============================================================================

echo -e "${YELLOW}Step 2: Stopping existing services...${NC}"
docker compose down 2>/dev/null || true
echo -e "${GREEN}✓ Services stopped${NC}"
echo ""

# ============================================================================
# Step 3: Start Traefik and Web Apps
# ============================================================================

echo -e "${YELLOW}Step 3: Starting services with Traefik...${NC}"
echo ""

# Start with web-apps profile (includes Traefik from override)
docker compose --profile web-apps up -d

echo ""
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# ============================================================================
# Step 4: Wait for services to be ready
# ============================================================================

echo -e "${YELLOW}Step 4: Waiting for services to be ready...${NC}"
echo ""

sleep 10

# Check Traefik
if curl -s http://localhost:8090/api/overview > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Traefik Dashboard: http://localhost:8090${NC}"
else
    echo -e "${RED}✗ Traefik not responding${NC}"
fi

echo ""

# ============================================================================
# Completion
# ============================================================================

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "You can now access your applications via domain names:"
echo ""
echo -e "${GREEN}Public Web Applications:${NC}"
echo "  ✓ Wizardsofts.com:    http://www.wizardsofts.local"
echo "  ✓ Daily Deen Guide:   http://dailydeenguide.local"
echo "  ✓ Quant-Flow:         http://quant.wizardsofts.local"
echo ""
echo -e "${GREEN}Infrastructure (Direct IP Access):${NC}"
echo "  ✓ Traefik Dashboard:  http://localhost:8090"
echo "  ✓ Eureka Dashboard:   http://eureka.wizardsofts.local (or http://localhost:8762)"
echo "  ✓ API Gateway:        http://api.wizardsofts.local (or http://localhost:8080)"
echo ""
echo -e "${YELLOW}Note:${NC} Infrastructure services require Basic Auth via Traefik"
echo "      Username: admin / Password: admin"
echo ""
echo -e "${GREEN}To start all services (including ML):${NC}"
echo "  docker compose --profile all up -d"
echo ""
echo -e "${GREEN}To stop all services:${NC}"
echo "  docker compose down"
echo ""

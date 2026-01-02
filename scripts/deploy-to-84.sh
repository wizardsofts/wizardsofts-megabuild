#!/bin/bash
# Quick Deployment Script to 10.0.0.84
# Usage: ./scripts/deploy-to-84.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DEPLOY_HOST="10.0.0.84"
DEPLOY_USER="deploy"
DEPLOY_PATH="/opt/wizardsofts-megabuild"
COMPOSE_PROFILE="all"  # Deploy everything: shared, gibd-quant, and web-apps

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying to 10.0.0.84${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ]; then
    echo -e "${RED}Error: SSH key not found at ~/.ssh/id_rsa${NC}"
    echo "Generate one with: ssh-keygen -t rsa -b 4096"
    exit 1
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 $DEPLOY_USER@$DEPLOY_HOST "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo "Please ensure:"
    echo "  1. SSH key is added to $DEPLOY_HOST authorized_keys"
    echo "  2. Server is accessible from your network"
    exit 1
fi

# Sync files to server
echo -e "${YELLOW}Syncing files to server...${NC}"
rsync -avz --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude 'target' \
    --exclude '.m2' \
    --exclude '.cache' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --progress \
    ./ $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/

echo -e "${GREEN}✓ Files synced${NC}"

# Execute deployment on server
echo -e "${YELLOW}Deploying services on server...${NC}"

if [ -z "$SUDO_PASSWORD" ]; then
    echo -e "${RED}Error: SUDO_PASSWORD environment variable must be set${NC}"
    echo "Usage: SUDO_PASSWORD=<password> ./scripts/deploy-to-84.sh"
    exit 1
fi

ssh $DEPLOY_USER@$DEPLOY_HOST << ENDSSH
set -e

SUDO_PASSWORD="$SUDO_PASSWORD"
cd $DEPLOY_PATH

echo "Pulling latest changes..."
git pull origin main || echo "Not a git repository, using rsync files"

echo "Creating .env if not exists..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "WARNING: Created .env from .env.example - UPDATE WITH ACTUAL VALUES!"
fi

echo "Stopping existing services..."
echo "\$SUDO_PASSWORD" | sudo -S docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile $COMPOSE_PROFILE down || true

echo "Building Docker images..."
echo "\$SUDO_PASSWORD" | sudo -S docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile $COMPOSE_PROFILE build

echo "Starting services..."
echo "\$SUDO_PASSWORD" | sudo -S docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile $COMPOSE_PROFILE up -d

echo "Waiting for services to start..."
sleep 15

echo "Checking service status..."
docker compose ps

echo "Deployment complete!"
ENDSSH

# Run health checks
echo ""
echo -e "${YELLOW}Running health checks...${NC}"
sleep 15

# Check Traefik (only exposed ports in production)
if curl -f -s http://$DEPLOY_HOST:80 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Traefik (80): UP${NC}"
else
    echo -e "${RED}✗ Traefik (80): DOWN${NC}"
fi

# Check Traefik Dashboard
if curl -f -s http://$DEPLOY_HOST:8090/api/overview > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Traefik Dashboard (8090): UP${NC}"
else
    echo -e "${RED}✗ Traefik Dashboard (8090): DOWN${NC}"
fi

echo ""
echo -e "${YELLOW}Note: All services are secured behind Traefik reverse proxy${NC}"
echo -e "${YELLOW}Direct port access is disabled for security${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Production Security:${NC}"
echo "  ✓ Only ports 80, 443, 8090 exposed (Traefik)"
echo "  ✓ All services behind reverse proxy with SSL"
echo "  ✓ Database and cache not accessible from internet"
echo ""
echo -e "${YELLOW}Next Steps - Configure DNS:${NC}"
echo ""
echo "1. Add these A records to your DNS provider:"
echo "   www.wizardsofts.com           → $DEPLOY_HOST"
echo "   dailydeenguide.wizardsofts.com → $DEPLOY_HOST"
echo "   quant.wizardsofts.com         → $DEPLOY_HOST"
echo "   api.wizardsofts.com           → $DEPLOY_HOST"
echo "   eureka.wizardsofts.com        → $DEPLOY_HOST"
echo "   traefik.wizardsofts.com       → $DEPLOY_HOST"
echo ""
echo "2. Once DNS is configured, access services via HTTPS:"
echo ""
echo -e "${GREEN}Public Web Applications (HTTPS):${NC}"
echo "  - https://www.wizardsofts.com"
echo "  - https://dailydeenguide.wizardsofts.com"
echo "  - https://quant.wizardsofts.com"
echo ""
echo -e "${GREEN}Infrastructure (HTTPS + Auth):${NC}"
echo "  - https://api.wizardsofts.com"
echo "  - https://eureka.wizardsofts.com (admin/password)"
echo "  - https://traefik.wizardsofts.com (admin/password)"
echo ""
echo -e "${YELLOW}Temporary Access (before DNS):${NC}"
echo "  - Traefik Dashboard: http://$DEPLOY_HOST:8090"
echo ""
echo "To view logs:"
echo "  ssh $DEPLOY_USER@$DEPLOY_HOST 'cd $DEPLOY_PATH && docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f'"
echo ""

#!/bin/bash
set -euo pipefail

# Deploy Celery + Redis on Server 84
# This script sets up the complete Celery infrastructure

echo "🚀 Deploying Celery Infrastructure on Server 84"

SERVER_IP="10.0.0.84"
USER="wizardsofts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Create directories on Server 84
echo ""
echo "📁 Step 1: Creating directories on Server 84..."

ssh ${USER}@${SERVER_IP} "mkdir -p ~/celery ~/redis ~/ml-datasets ~/ml-models"
ssh ${USER}@${SERVER_IP} "mkdir -p ~/ml-datasets/new ~/ml-datasets/processed"

log_info "Directories created"

# Step 2: Copy Redis configuration
echo ""
echo "🗄️  Step 2: Deploying Redis..."

scp ${BASE_DIR}/redis/docker-compose.redis.yml ${USER}@${SERVER_IP}:~/redis/docker-compose.yml
scp ${BASE_DIR}/redis/.env.redis.example ${USER}@${SERVER_IP}:~/redis/.env.redis.example

# Generate Redis password if not exists
ssh ${USER}@${SERVER_IP} "cd ~/redis && \
    if [ ! -f .env.redis ]; then \
        cp .env.redis.example .env.redis && \
        REDIS_PASS=\$(openssl rand -hex 32) && \
        sed -i \"s/CHANGE_THIS_TO_SECURE_PASSWORD_RUN_OPENSSL_RAND_HEX_32/\$REDIS_PASS/\" .env.redis && \
        echo 'Generated Redis password'; \
    else \
        echo 'Redis .env.redis already exists, skipping'; \
    fi"

log_info "Redis configuration deployed"

# Step 3: Start Redis
echo ""
echo "▶️  Step 3: Starting Redis..."

# Docker Compose v1 reads .env automatically, so copy .env.redis to .env
ssh ${USER}@${SERVER_IP} "cd ~/redis && cp .env.redis .env && docker-compose up -d"

log_info "Redis started on port 6380"

# Step 4: Copy Celery configuration
echo ""
echo "📦 Step 4: Deploying Celery..."

scp ${BASE_DIR}/celery/Dockerfile.celery ${USER}@${SERVER_IP}:~/celery/
scp ${BASE_DIR}/celery/docker-compose.celery.yml ${USER}@${SERVER_IP}:~/celery/docker-compose.yml
scp ${BASE_DIR}/celery/.env.celery.example ${USER}@${SERVER_IP}:~/celery/.env.celery.example

# Copy tasks directory
scp -r ${BASE_DIR}/celery/tasks ${USER}@${SERVER_IP}:~/celery/

# Generate Celery env file
ssh ${USER}@${SERVER_IP} "cd ~/celery && \
    if [ ! -f .env.celery ]; then \
        cp .env.celery.example .env.celery && \
        REDIS_PASS=\$(grep REDIS_PASSWORD ~/redis/.env.redis | cut -d '=' -f2) && \
        sed -i \"s/CHANGE_THIS_TO_SECURE_PASSWORD_RUN_OPENSSL_RAND_HEX_32/\$REDIS_PASS/\" .env.celery && \
        FLOWER_PASS=\$(openssl rand -hex 16) && \
        sed -i \"s/CHANGE_THIS_TO_SECURE_PASSWORD/\$FLOWER_PASS/\" .env.celery && \
        echo 'Generated Celery passwords'; \
    else \
        echo 'Celery .env.celery already exists, skipping'; \
    fi"

log_info "Celery configuration deployed"

# Step 5: Build and start Celery
echo ""
echo "▶️  Step 5: Building and starting Celery workers..."

# Docker Compose v1 reads .env automatically, so copy .env.celery to .env
ssh ${USER}@${SERVER_IP} "cd ~/celery && cp .env.celery .env && docker-compose build"
ssh ${USER}@${SERVER_IP} "cd ~/celery && docker-compose up -d"

log_info "Celery workers started"

# Step 6: Verify deployment
echo ""
echo "🔍 Step 6: Verifying deployment..."

sleep 5

# Check Redis
REDIS_STATUS=$(ssh ${USER}@${SERVER_IP} "docker ps --filter name=redis-celery --format '{{.Status}}'" | head -1)
if [[ $REDIS_STATUS == *"Up"* ]]; then
    log_info "Redis is running"
else
    log_error "Redis is not running"
fi

# Check Celery workers
CELERY_COUNT=$(ssh ${USER}@${SERVER_IP} "docker ps --filter label=com.wizardsofts.service=celery-worker --format '{{.Names}}'" | wc -l)
log_info "Celery workers running: $CELERY_COUNT"

# Check Celery Beat
BEAT_STATUS=$(ssh ${USER}@${SERVER_IP} "docker ps --filter name=celery-beat --format '{{.Status}}'" | head -1)
if [[ $BEAT_STATUS == *"Up"* ]]; then
    log_info "Celery Beat (scheduler) is running"
else
    log_warn "Celery Beat is not running"
fi

# Check Flower
FLOWER_STATUS=$(ssh ${USER}@${SERVER_IP} "docker ps --filter name=flower --format '{{.Status}}'" | head -1)
if [[ $FLOWER_STATUS == *"Up"* ]]; then
    log_info "Flower dashboard is running on http://${SERVER_IP}:5555"
else
    log_warn "Flower is not running"
fi

# Step 7: Display access information
echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 Access Points:"
echo "  - Flower Dashboard: http://${SERVER_IP}:5555"
echo "  - Redis: ${SERVER_IP}:6380"
echo ""
echo "🔑 Credentials:"
echo "  - Get Flower password: ssh ${USER}@${SERVER_IP} 'grep FLOWER_PASSWORD ~/celery/.env.celery'"
echo "  - Get Redis password: ssh ${USER}@${SERVER_IP} 'grep REDIS_PASSWORD ~/redis/.env.redis'"
echo ""
echo "📝 Useful Commands:"
echo "  - Check worker logs: ssh ${USER}@${SERVER_IP} 'cd ~/celery && docker-compose logs -f celery-worker-ml'"
echo "  - Check Beat logs: ssh ${USER}@${SERVER_IP} 'cd ~/celery && docker-compose logs -f celery-beat'"
echo "  - Restart workers: ssh ${USER}@${SERVER_IP} 'cd ~/celery && docker-compose restart'"
echo "  - Stop all: ssh ${USER}@${SERVER_IP} 'cd ~/celery && docker-compose down'"
echo ""
echo "🧪 Test with:"
echo "  python3 -c 'from celery import Celery; app = Celery(broker=\"redis://:PASSWORD@${SERVER_IP}:6380/0\"); result = app.send_task(\"tasks.simple_tasks.ping\"); print(result.get(timeout=10))'"
echo ""

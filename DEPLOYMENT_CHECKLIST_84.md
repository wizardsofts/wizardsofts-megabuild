# Deployment Checklist for 10.0.0.84

## Current Status (as of now)

✅ **Running Services:**
- Appwrite (BaaS Platform) - 1.8.1
- Mailcow (Email Server)
- Traefik (Reverse Proxy) - implied by DNS routing working

❌ **NOT Running Services:**
- gibd-quant-web (Frontend)
- ws-gateway (API Gateway)
- ws-discovery (Eureka)
- ws-trades, ws-company, ws-news (Backend APIs)
- gibd-quant-signal, gibd-quant-nlq, gibd-quant-calibration, gibd-quant-agent (Python ML services)
- PostgreSQL database
- Redis cache

---

## Complete Deployment Guide

### Step 1: Navigate to Deployment Directory

```bash
# Check where you are
pwd

# You should be in one of these locations:
# /home/wizardsofts/wizardsofts-megabuild  OR
# /opt/wizardsofts-megabuild

# If not sure, find it:
find ~ -name "docker-compose.yml" -type f 2>/dev/null | grep -v node_modules
```

### Step 2: Create .env File

```bash
# Navigate to the deployment directory found above
cd /path/to/wizardsofts-megabuild

# Create the .env file (copy from ENV_CONFIGURATION_GUIDE.md)
cat > .env << 'EOF'
# ============================================================================
# APPLICATION SERVICES
# ============================================================================

# Database Configuration
DB_PASSWORD=29Dec2#24

# OpenAI API (for NLQ and Agent services)
OPENAI_API_KEY=sk-your-openai-api-key-here

# ============================================================================
# GIBD QUANT WEB - Guardian Investment BD (Trading Platform)
# ============================================================================

# Google Analytics - Trading Platform Analytics
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Google AdSense - For trading signals page ads
NEXT_PUBLIC_ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
NEXT_PUBLIC_ADSENSE_BANNER_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_INFEED_SLOT=XXXXXXXXXX

# ============================================================================
# INFRASTRUCTURE SERVICES
# ============================================================================

# Keycloak (Authentication)
KEYCLOAK_DB_PASSWORD=keycloak_db_password
KEYCLOAK_ADMIN_PASSWORD=Keycl0ak!Admin2025

# Traefik (Reverse Proxy)
TRAEFIK_DASHBOARD_PASSWORD=W1z4rdS0fts!2025
ACME_EMAIL=admin@wizardsofts.com

# N8N (Workflow Automation)
N8N_PASSWORD=W1z4rdS0fts!2025

# Grafana (Monitoring)
GRAFANA_PASSWORD=W1z4rdS0fts!2025

# GitLab
GITLAB_ROOT_PASSWORD=29Dec2#24

# Infrastructure Database
INFRA_DB_PASSWORD=29Dec2#24

# ============================================================================
# OPTIONAL SERVICES
# ============================================================================

# Redis
REDIS_PASSWORD=

# Ollama
OLLAMA_MODEL=llama3.1

# ============================================================================
# DEPLOYMENT CREDENTIALS (10.0.0.84 Server)
# ============================================================================

DEPLOY_HOST=10.0.0.84
DEPLOY_USER=wizardsofts
DEPLOY_PASSWORD=29Dec2#24
DEPLOY_PATH=/opt/wizardsofts-megabuild
EOF

# Verify file created
cat .env | head -10
```

### Step 3: Pull Latest Code

```bash
git pull origin master
```

### Step 4: Start All Services

```bash
# Option A: Build and start everything (takes 10-15 minutes first time)
docker-compose --profile gibd-quant build
docker-compose --profile gibd-quant up -d

# Option B: Just start (if images already exist)
docker-compose --profile gibd-quant up -d
```

### Step 5: Monitor Service Startup

```bash
# Watch logs in real-time (Ctrl+C to exit)
docker-compose logs -f

# Or check specific service logs
docker-compose logs -f ws-gateway
docker-compose logs -f postgres
docker-compose logs -f gibd-quant-web
```

### Step 6: Verify Services Are Running

```bash
# Check all containers
docker-compose ps

# Expected output - should see these running:
# - postgres
# - redis
# - ws-discovery (Eureka)
# - ws-gateway (API Gateway)
# - ws-trades, ws-company, ws-news
# - gibd-quant-signal, gibd-quant-nlq, gibd-quant-calibration, gibd-quant-agent
# - gibd-quant-web
# - traefik
```

### Step 7: Health Checks

```bash
# Check API Gateway
curl http://localhost:8080/actuator/health

# Check Eureka
curl http://localhost:8761/actuator/health

# Check Frontend
curl http://localhost:3000/

# Check Traefik via domain
curl -H "Host: www.guardianinvestmentbd.com" http://localhost/

# Expected response: Coming Soon page (because of middleware)
```

---

## Troubleshooting

### Issue: "docker-compose: command not found"

**Solution**: Use `docker compose` instead (newer Docker):
```bash
docker compose --profile gibd-quant up -d
```

### Issue: "No such file or directory: .env"

**Solution**: .env file missing, create it as shown in Step 2

### Issue: "Database connection refused"

**Solution**: PostgreSQL not started yet, wait 1-2 minutes
```bash
docker-compose logs postgres
```

### Issue: "Services won't start"

**Solution**: Check logs for errors
```bash
# Full logs
docker-compose logs

# Specific service
docker-compose logs postgres
docker-compose logs ws-gateway

# Last 100 lines
docker-compose logs --tail=100
```

### Issue: Port already in use

**Solution**: Stop conflicting containers
```bash
# Find what's using port 3000
lsof -i :3000

# Or stop all and start fresh
docker-compose down
docker-compose --profile gibd-quant up -d
```

---

## Service Startup Order (and dependencies)

Services start in this order due to healthchecks:

1. **postgres** (database) - no dependencies
2. **redis** (cache) - no dependencies
3. **ws-discovery** (Eureka) - depends on health
4. **ws-gateway** (API Gateway) - depends on ws-discovery healthy
5. **ws-trades, ws-company, ws-news** - depend on postgres + ws-discovery healthy
6. **gibd-quant-signal, gibd-quant-nlq, gibd-quant-calibration, gibd-quant-agent** - depend on postgres + ws-discovery healthy
7. **gibd-quant-web** (Frontend) - no critical dependencies (graceful fallback if APIs down)

**Expected startup time**: 5-10 minutes for first build, 2-3 minutes for subsequent starts

---

## Complete Service List

### Frontend Services (Port 3000-3002)
- **gibd-quant-web** - Guardian Investment BD trading platform
- **ws-daily-deen-web** - Daily Deen Islamic guide
- **pf-padmafoods-web** - Padma Foods e-commerce

### Backend Infrastructure
- **ws-discovery** - Eureka service registry (port 8761)
- **ws-gateway** - API Gateway (port 8080)
- **postgres** - PostgreSQL database (port 5432)
- **redis** - Cache (port 6379)

### Business Logic Services
- **ws-trades** - Stock trading data (port 8182)
- **ws-company** - Company information (port 8183)
- **ws-news** - News service (port 8184)

### ML/AI Services
- **gibd-quant-signal** - Trading signals (port 5001)
- **gibd-quant-nlq** - Natural Language Queries (port 5002)
- **gibd-quant-calibration** - Model calibration (port 5003)
- **gibd-quant-agent** - AI Agent (port 5004)

### Infrastructure
- **traefik** - Reverse proxy (port 80, 443, 8080)
- **appwrite** - BaaS platform (already running)
- **mailcow** - Email server (already running)

---

## After Services Start

### Test Coming Soon Feature

```bash
# Domain access should show Coming Soon page
curl -H "Host: www.guardianinvestmentbd.com" http://localhost/ | grep -i "coming soon"

# Local IP should show full app
curl http://localhost:3000/ | grep -i "signals\|trading"
```

### Test Multi-Criteria Feature

```bash
# Should work now with API gateway running
curl http://localhost:4002/signals
# or
curl http://localhost:3000/multi-criteria
```

### Test API Endpoints

```bash
# Get suggestions
curl http://localhost:8080/api/v1/nlq/examples

# Compound query
curl -X POST http://localhost:8080/api/v1/nlq/compound \
  -H "Content-Type: application/json" \
  -d '{"criteria": [{"id": "1", "query": "price > 100"}], "match_all": true}'
```

---

## Docker Compose Commands Cheat Sheet

```bash
# Start all services with gibd-quant profile
docker-compose --profile gibd-quant up -d

# Stop all services
docker-compose down

# View running services
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f gibd-quant-web

# Restart a service
docker-compose restart gibd-quant-web

# View service logs (last 100 lines)
docker-compose logs --tail=100 ws-gateway

# Rebuild a specific service
docker-compose build gibd-quant-web

# Execute command in container
docker-compose exec gibd-quant-web sh

# Remove containers and volumes
docker-compose down -v

# Pull latest images
docker-compose pull

# Check service health
docker-compose ps | grep healthy
```

---

## Next Steps After Deployment

1. ✅ Create .env file
2. ✅ Pull latest code
3. ✅ Start services with `docker-compose --profile gibd-quant up -d`
4. ✅ Wait for services to become healthy (5-10 minutes)
5. ✅ Test Coming Soon page works
6. ✅ Test multi-criteria endpoint works
7. ✅ Configure Google Analytics IDs (optional)
8. ✅ Configure OpenAI API key (optional but recommended)
9. ✅ Monitor logs for any errors
10. ✅ Set up monitoring and alerts

---

## Important Notes

⚠️ **First Build Takes Time**:
- Building all services from scratch: 15-30 minutes
- Downloading Maven dependencies: 5-10 minutes
- Pulling Docker images: 2-3 minutes

⚠️ **Database Initialization**:
- PostgreSQL may take 1-2 minutes to initialize
- Spring Boot services wait for postgres to be healthy
- Be patient and check logs

⚠️ **Memory Requirements**:
- Multiple Java services (Spring Boot) consume significant memory
- Each service: 500MB-1GB
- Ensure server has at least 8GB free RAM

⚠️ **Disk Space**:
- Docker images: 10-15GB
- Data volumes: depends on usage
- Ensure at least 30GB free disk space

---

## References

- [ENV_CONFIGURATION_GUIDE.md](./ENV_CONFIGURATION_GUIDE.md)
- [COMING_SOON_DEPLOYMENT_GUIDE.md](./COMING_SOON_DEPLOYMENT_GUIDE.md)
- [EMERGENCY_RECOVERY.md](./EMERGENCY_RECOVERY.md)
- [docker-compose.yml](./docker-compose.yml)

# Quick Start Guide - Wizardsofts Megabuild

**Last Updated**: December 27, 2025

---

## Prerequisites

- Docker & Docker Compose installed
- 8GB+ RAM available
- 20GB+ disk space
- `.env` file configured

---

## Quick Deployment

### 1. Deploy Shared Services (Infrastructure)

```bash
# Start Postgres, Redis, Eureka, Gateway, and shared APIs
docker compose --profile shared up -d

# Wait for services to be healthy (2-3 minutes)
docker compose ps

# Verify Eureka
curl http://localhost:8762/actuator/health
# Expected: {"status":"UP"}

# Verify Gateway
curl http://localhost:8080/actuator/health
# Expected: {"status":"UP"}
```

**Services Started**:
- postgres (Port 5433)
- redis (Port 6379)
- ws-discovery/Eureka (Port 8762)
- ws-gateway (Port 8080)
- ws-trades (Port 8182)
- ws-company (Port 8183)
- ws-news (Port 8184)

---

### 2. Deploy Web Applications

```bash
# Start corporate website and Daily Deen Guide
docker compose --profile web-apps up -d

# Verify services
curl http://localhost:3000  # Wizardsofts.com
curl http://localhost:3002  # Daily Deen Guide

# Open in browser
open http://localhost:3000
open http://localhost:3002
```

**Services Started**:
- ws-wizardsofts-web (Port 3000)
- ws-daily-deen-web (Port 3002)

---

### 3. Deploy GIBD Quant-Flow (ML Services)

```bash
# Start all GIBD Quant services (includes shared dependencies)
docker compose --profile gibd-quant up -d

# Wait for ML services to start (3-5 minutes)
docker compose ps

# Verify ML services
curl http://localhost:5001/health  # Signal Service
curl http://localhost:5002/health  # NLQ Service
curl http://localhost:5003/health  # Calibration Service
curl http://localhost:5004/health  # Agent Service

# Verify frontend
open http://localhost:3001
```

**Services Started** (in addition to shared):
- gibd-quant-signal (Port 5001)
- gibd-quant-nlq (Port 5002)
- gibd-quant-calibration (Port 5003)
- gibd-quant-agent (Port 5004)
- gibd-quant-celery (background worker)
- gibd-quant-web (Port 3001)

---

### 4. Deploy Everything

```bash
# Start all services at once
docker compose --profile all up -d

# Monitor startup
docker compose logs -f --tail=50

# Check status
docker compose ps
```

---

### 5. Deploy Infrastructure Services

```bash
# Start Traefik, Keycloak, GitLab, monitoring, etc.
docker compose -f docker-compose.infrastructure.yml --profile infrastructure up -d

# Verify Traefik
curl http://localhost:8090/api/overview

# Verify Prometheus
curl http://localhost:9090/-/healthy

# Verify Grafana
open http://localhost:3000  # Note: Conflicts with Grafana if web-apps running
```

**Infrastructure Services**:
- traefik (Ports 80, 443, 8090)
- keycloak (Port 8080 - via Traefik)
- gitlab (Ports 80, 443, 2222)
- nexus (Port 8081)
- prometheus (Port 9090)
- grafana (Port 3000)
- ollama (Port 11434)
- n8n (Port 5678 - via Traefik)

---

## Service Status

### Check Running Services

```bash
# List all running containers
docker compose ps

# Check specific service logs
docker compose logs -f ws-discovery
docker compose logs -f ws-gateway
docker compose logs -f gibd-quant-signal

# Check health of all services
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

### Check Eureka Service Registration

```bash
# Wait 30-60 seconds after startup for registration
curl http://localhost:8762/eureka/apps | grep -o '<app>[^<]*</app>'

# Expected registered services:
# - WS-DISCOVERY
# - WS-GATEWAY
# - WS-TRADES
# - WS-COMPANY
# - WS-NEWS
# - GIBD-QUANT-SIGNAL (if gibd-quant profile)
# - GIBD-QUANT-NLQ (if gibd-quant profile)
# - GIBD-QUANT-CALIBRATION (if gibd-quant profile)
# - GIBD-QUANT-AGENT (if gibd-quant profile)
```

---

## Stop Services

```bash
# Stop specific profile
docker compose --profile shared down
docker compose --profile web-apps down
docker compose --profile gibd-quant down

# Stop all services
docker compose down

# Stop and remove volumes (⚠️ WARNING: Deletes all data!)
docker compose down -v

# Stop infrastructure
docker compose -f docker-compose.infrastructure.yml down
```

---

## Troubleshooting

### Port Conflicts

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :5432  # Postgres
lsof -i :8761  # Eureka
lsof -i :8080  # Gateway

# The megabuild uses:
# - Port 5433 for Postgres (not 5432)
# - Port 8762 for Eureka (not 8761)
```

### Service Not Starting

```bash
# Check logs
docker compose logs <service-name>

# Check health status
docker compose ps

# Restart specific service
docker compose restart <service-name>

# Rebuild if Dockerfile changed
docker compose build <service-name>
docker compose up -d <service-name>
```

### Database Connection Issues

```bash
# Verify Postgres is running
docker compose ps postgres

# Check Postgres logs
docker compose logs postgres

# Connect to Postgres
docker exec -it postgres psql -U gibd -d ws_gibd_dse_daily_trades

# List databases
\l

# Quit
\q
```

### Eureka Registration Issues

```bash
# Check Eureka logs
docker compose logs ws-discovery

# Check if service can reach Eureka
docker exec -it <service-name> ping ws-discovery

# Verify Eureka URL in service logs
docker compose logs <service-name> | grep eureka
```

---

## Quick Tests

### Test Spring Boot Services

```bash
# Health checks
curl http://localhost:8762/actuator/health  # Eureka
curl http://localhost:8080/actuator/health  # Gateway
curl http://localhost:8182/actuator/health  # Trades
curl http://localhost:8183/actuator/health  # Company
curl http://localhost:8184/actuator/health  # News

# Test Gateway routing
curl http://localhost:8080/api/trades/health  # Should route to ws-trades
```

### Test Python ML Services

```bash
# Health checks
curl http://localhost:5001/health  # Signal Service
curl http://localhost:5002/health  # NLQ Service
curl http://localhost:5003/health  # Calibration Service
curl http://localhost:5004/health  # Agent Service

# Generate signal
curl -X POST http://localhost:5001/api/v1/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"ticker": "GP"}'

# NLQ query
curl -X POST http://localhost:5002/api/v1/nlq/query \
  -H "Content-Type: application/json" \
  -d '{"query": "stocks with RSI above 70"}'
```

### Test Web Applications

```bash
# Wizardsofts.com
curl -I http://localhost:3000
open http://localhost:3000

# Daily Deen Guide
curl -I http://localhost:3002
open http://localhost:3002

# GIBD Quant-Flow
curl -I http://localhost:3001
open http://localhost:3001
```

---

## Environment Setup

### Create .env File

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

### Required Variables

```bash
# Database
DB_PASSWORD=your_secure_password

# OpenAI (for NLQ and Agent services)
OPENAI_API_KEY=sk-your-api-key

# Optional: Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX
ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
```

---

## Performance Tips

### Resource Allocation

```bash
# Check Docker resource usage
docker stats

# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory: 8GB+

# Limit service resources in docker-compose.yml
services:
  my-service:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

### Build Cache

```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with cache
docker compose build --parallel

# Clear build cache if needed
docker builder prune
```

---

## Next Steps

1. ✅ Start services
2. ⏸️ Verify health checks
3. ⏸️ Test API endpoints
4. ⏸️ Test web applications
5. ⏸️ Deploy to production (10.0.0.84)

---

## Useful Commands

```bash
# View all service endpoints
docker compose ps --format "table {{.Name}}\t{{.Ports}}"

# Follow logs for all services
docker compose logs -f

# Restart all services
docker compose restart

# Update and restart specific service
docker compose up -d --build <service-name>

# Clean up everything
docker compose down -v --remove-orphans
docker system prune -a --volumes -f
```

---

## Support

- Documentation: `/docs/`
- Issues: Report in GitLab
- Logs: `docker compose logs <service>`

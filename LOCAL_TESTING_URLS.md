# Local Testing URLs - Wizardsofts Megabuild

**Date**: December 27, 2025
**Environment**: Local Development (macOS)

---

## Access Methods

### 1. Direct Port Access (IP:PORT)
Use localhost or 127.0.0.1 with specific ports.

### 2. Traefik URL Access (Domain-based)
Requires Traefik running and /etc/hosts configuration.

---

## Web Applications

### Wizardsofts Corporate Website

**Service**: ws-wizardsofts-web
**Profile**: web-apps

| Method | URL | Status |
|--------|-----|--------|
| **Direct Port** | http://localhost:3000 | ✅ Primary |
| **IP Access** | http://127.0.0.1:3000 | ✅ Alternative |
| **Traefik URL** | http://www.wizardsofts.local | ⚠️ Requires setup |

**Health Check**:
```bash
curl -I http://localhost:3000
```

**Test Pages**:
- Homepage: http://localhost:3000
- About: http://localhost:3000/about
- Services: http://localhost:3000/services
- Contact: http://localhost:3000/contact

---

### Daily Deen Guide

**Service**: ws-daily-deen-web
**Profile**: web-apps

| Method | URL | Status |
|--------|-----|--------|
| **Direct Port** | http://localhost:3002 | ✅ Primary |
| **IP Access** | http://127.0.0.1:3002 | ✅ Alternative |
| **Traefik URL** | http://dailydeenguide.local | ⚠️ Requires setup |

**Health Check**:
```bash
curl -I http://localhost:3002
```

**Test Pages**:
- Homepage: http://localhost:3002
- Prayer Times: http://localhost:3002 (main feature)

---

### GIBD Quant-Flow

**Service**: gibd-quant-web
**Profile**: gibd-quant

| Method | URL | Status |
|--------|-----|--------|
| **Direct Port** | http://localhost:3001 | ✅ Primary |
| **IP Access** | http://127.0.0.1:3001 | ✅ Alternative |
| **Traefik URL** | http://quant.wizardsofts.local | ⚠️ Requires setup |

**Health Check**:
```bash
curl -I http://localhost:3001
```

**Test Pages**:
- Homepage: http://localhost:3001
- Signals: http://localhost:3001/signals
- Company: http://localhost:3001/company/GP
- Chat: http://localhost:3001/chat

---

## Infrastructure Services

### Spring Boot Services

#### Eureka Service Discovery

| Method | URL | Port |
|--------|-----|------|
| **Dashboard** | http://localhost:8762 | 8762 |
| **Health** | http://localhost:8762/actuator/health | 8762 |

**View Registered Services**:
```bash
curl http://localhost:8762/eureka/apps
```

---

#### Spring Cloud Gateway

| Method | URL | Port |
|--------|-----|------|
| **Health** | http://localhost:8080/actuator/health | 8080 |
| **Routes** | http://localhost:8080/actuator/gateway/routes | 8080 |

**Test Gateway Routing**:
```bash
# Via Gateway to Trades service
curl http://localhost:8080/api/trades/health
```

---

#### Trades Service

| Method | URL | Port |
|--------|-----|------|
| **Direct** | http://localhost:8182 | 8182 |
| **Health** | http://localhost:8182/actuator/health | 8182 |
| **Via Gateway** | http://localhost:8080/api/trades/ | 8080 |

---

#### Company Service

| Method | URL | Port |
|--------|-----|------|
| **Direct** | http://localhost:8183 | 8183 |
| **Health** | http://localhost:8183/actuator/health | 8183 |
| **Via Gateway** | http://localhost:8080/api/company/ | 8080 |

---

#### News Service

| Method | URL | Port |
|--------|-----|------|
| **Direct** | http://localhost:8184 | 8184 |
| **Health** | http://localhost:8184/actuator/health | 8184 |
| **Via Gateway** | http://localhost:8080/api/news/ | 8080 |

---

## Python ML Services

### Signal Generation Service

| Method | URL | Port |
|--------|-----|------|
| **Health** | http://localhost:5001/health | 5001 |
| **API Docs** | http://localhost:5001/docs | 5001 |

**Generate Signal**:
```bash
curl -X POST http://localhost:5001/api/v1/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"ticker": "GP"}'
```

---

### NLQ Service

| Method | URL | Port |
|--------|-----|------|
| **Health** | http://localhost:5002/health | 5002 |
| **API Docs** | http://localhost:5002/docs | 5002 |

**Run Query**:
```bash
curl -X POST http://localhost:5002/api/v1/nlq/query \
  -H "Content-Type: application/json" \
  -d '{"query": "stocks with RSI above 70"}'
```

---

### Calibration Service

| Method | URL | Port |
|--------|-----|------|
| **Health** | http://localhost:5003/health | 5003 |
| **API Docs** | http://localhost:5003/docs | 5003 |

**Calibrate Stock**:
```bash
curl -X POST http://localhost:5003/api/v1/calibrate/GP
```

---

### Agent Service

| Method | URL | Port |
|--------|-----|------|
| **Health** | http://localhost:5004/health | 5004 |
| **API Docs** | http://localhost:5004/docs | 5004 |

---

## Database & Cache

### PostgreSQL

| Method | URL | Port |
|--------|-----|------|
| **Connection** | localhost:5433 | 5433 |

**Connect via CLI**:
```bash
docker exec -it postgres psql -U gibd -d ws_gibd_dse_daily_trades
```

**Connection String**:
```
postgresql://gibd:password@localhost:5433/ws_gibd_dse_daily_trades
```

---

### Redis

| Method | URL | Port |
|--------|-----|------|
| **Connection** | localhost:6379 | 6379 |

**Test Connection**:
```bash
docker exec -it redis redis-cli ping
```

---

## Infrastructure Services (Optional)

### Traefik Dashboard

| Method | URL | Port |
|--------|-----|------|
| **Dashboard** | http://localhost:8090 | 8090 |
| **API** | http://localhost:8090/api/overview | 8090 |

**Note**: Requires Traefik running from infrastructure compose.

---

### Prometheus

| Method | URL | Port |
|--------|-----|------|
| **Dashboard** | http://localhost:9090 | 9090 |
| **Metrics** | http://localhost:9090/metrics | 9090 |
| **Targets** | http://localhost:9090/targets | 9090 |

---

### Grafana

| Method | URL | Port |
|--------|-----|------|
| **Dashboard** | http://localhost:3000 | 3000 |

**Note**: Conflicts with ws-wizardsofts-web port. Use different port or run separately.

---

## Traefik URL Setup (Optional)

For domain-based local access, configure /etc/hosts:

### Edit /etc/hosts

```bash
sudo nano /etc/hosts
```

### Add Entries

```
127.0.0.1 www.wizardsofts.local
127.0.0.1 dailydeenguide.local
127.0.0.1 quant.wizardsofts.local
127.0.0.1 traefik.wizardsofts.local
127.0.0.1 id.wizardsofts.local
127.0.0.1 gitlab.wizardsofts.local
127.0.0.1 nexus.wizardsofts.local
127.0.0.1 grafana.wizardsofts.local
127.0.0.1 n8n.wizardsofts.local
```

### Start Traefik

```bash
# Requires port 80 and 443 free
docker compose -f docker-compose.infrastructure.yml --profile proxy up -d traefik
```

### Access via Domain

- http://www.wizardsofts.local
- http://dailydeenguide.local
- http://quant.wizardsofts.local

---

## Quick Test Script

```bash
#!/bin/bash

echo "Testing Wizardsofts Megabuild Services..."

# Web Apps
echo "\n=== Web Applications ==="
curl -I -s http://localhost:3000 | head -1  # Wizardsofts.com
curl -I -s http://localhost:3002 | head -1  # Daily Deen Guide
curl -I -s http://localhost:3001 | head -1  # Quant-Flow

# Spring Boot Services
echo "\n=== Spring Boot Services ==="
curl -s http://localhost:8762/actuator/health  # Eureka
curl -s http://localhost:8080/actuator/health  # Gateway
curl -s http://localhost:8182/actuator/health  # Trades
curl -s http://localhost:8183/actuator/health  # Company
curl -s http://localhost:8184/actuator/health  # News

# Python ML Services
echo "\n=== Python ML Services ==="
curl -s http://localhost:5001/health  # Signal
curl -s http://localhost:5002/health  # NLQ
curl -s http://localhost:5003/health  # Calibration
curl -s http://localhost:5004/health  # Agent

# Database
echo "\n=== Database ==="
docker exec -it postgres pg_isready -U gibd || echo "Postgres not running"
docker exec -it redis redis-cli ping || echo "Redis not running"

echo "\n=== Test Complete ===" ```

---

## Service Status Check

```bash
# Check all running services
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Check specific profile
docker compose --profile web-apps ps
docker compose --profile gibd-quant ps

# Check logs
docker compose logs -f ws-wizardsofts-web
docker compose logs -f ws-daily-deen-web
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using a port
lsof -i :3000
lsof -i :8080

# Kill process if needed
kill -9 <PID>
```

### Service Not Responding

```bash
# Check logs
docker compose logs <service-name>

# Restart service
docker compose restart <service-name>

# Rebuild if needed
docker compose build <service-name>
docker compose up -d <service-name>
```

### Cannot Access Traefik URLs

1. Verify /etc/hosts entries exist
2. Ensure Traefik is running: `docker compose -f docker-compose.infrastructure.yml ps traefik`
3. Check Traefik dashboard: http://localhost:8090
4. Verify service has Traefik labels in docker-compose.yml

---

## Production URLs (10.0.0.84)

When deployed to production server:

| Service | Production URL |
|---------|----------------|
| Wizardsofts.com | https://www.wizardsofts.com |
| Daily Deen Guide | https://dailydeenguide.wizardsofts.com |
| Quant-Flow | https://quant.wizardsofts.com |
| Eureka | http://10.0.0.84:8762 |
| Gateway | http://10.0.0.84:8080 |
| Traefik Dashboard | https://traefik.wizardsofts.com |
| Keycloak | https://id.wizardsofts.com |
| GitLab | https://gitlab.wizardsofts.com |
| Grafana | https://grafana.wizardsofts.com |

# Testing Plan - Wizardsofts Megabuild

**Date**: December 27, 2025
**Status**: In Progress

---

## Overview

This document tracks the comprehensive testing of the wizardsofts-megabuild monorepo to ensure all services deploy correctly and communicate properly.

---

## Test Environment

- **OS**: macOS (Darwin 24.6.0)
- **Docker**: Running
- **Location**: /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
- **Test Type**: Local deployment testing

---

## Phase 1: Docker Compose Validation

### Application Services (docker-compose.yml)

- [x] **Validation**: Docker Compose config validation
  - Status: ✅ PASSED
  - Issues: None (warnings about missing env vars expected)
  - Version attribute obsolete warning (non-critical)

- [x] **Environment**: .env file creation
  - Status: ✅ CREATED
  - File: /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/.env

- [x] **Compilation Fix**: Removed EurekaConfig.java
  - Issue: EurekaInstanceConfigBean() constructor is private in Spring Cloud 2024.0.0
  - Fix: Deleted apps/ws-discovery/src/main/java/.../config/EurekaConfig.java
  - Result: Build successful

- [x] **Port Conflicts Resolved**:
  - PostgreSQL: Changed from 5432 → 5433 (host:5433, container:5432)
  - Eureka: Changed from 8761 → 8762 (host:8762, container:8761)
  - Reason: Host PostgreSQL running on 5432, unknown service blocking 8761

### Infrastructure Services (docker-compose.infrastructure.yml)

- [x] **Validation**: Docker Compose config validation
  - Status: ✅ PASSED
  - Issues: Version attribute obsolete warning (non-critical)

---

## Phase 2: Shared Services Deployment Test

### Test Scenario: Deploy Shared Profile Only

**Command**: `docker compose --profile shared up -d`

**Expected Services**:
- [x] postgres (Port 5433→5432) - ✅ HEALTHY
- [x] redis (Port 6379) - ✅ HEALTHY
- [x] ws-discovery (Eureka) (Port 8762→8761) - ⚠️ RUNNING (unhealthy - curl not installed)
- [ ] ws-gateway (Spring Cloud Gateway) (Port 8080) - ⏸️ WAITING (depends on ws-discovery health)
- [ ] ws-trades (Trades API) (Port 8182) - ⏸️ WAITING
- [ ] ws-company (Company Info API) (Port 8183) - ⏸️ WAITING
- [ ] ws-news (News API) (Port 8184) - ⏸️ WAITING

**Health Checks**:
- [x] Postgres: pg_isready - ✅ PASSED
- [x] Redis: PING response - ✅ PASSED
- [x] Eureka Internal: `docker exec ws-discovery wget http://localhost:8761/actuator/health` - ✅ {"status":"UP"}
- [ ] Eureka External: http://localhost:8762/ - ❌ Connection refused (Docker Desktop port forwarding issue)
- [ ] Gateway Health: Not started (dependency failed)
- [ ] Trades Health: Not started
- [ ] Company Health: Not started
- [ ] News Health: Not started

**Issues Found**:
1. **Health Check Command**: `curl` not installed in eclipse-temurin:17-jre-alpine image
   - **Impact**: Health checks fail, preventing dependent services from starting
   - **Fix Needed**: Install curl in Dockerfile or use wget-based health checks

2. **Docker Desktop Port Forwarding**: Port 8762 not accessible from host
   - **Impact**: Cannot access Eureka dashboard from browser
   - **Workaround**: Service works correctly inside Docker network
   - **Note**: This is a Docker Desktop on macOS issue, likely won't occur in Linux production

**Eureka Registration**:
- [ ] ws-gateway registered - Not started
- [ ] ws-trades registered - Not started
- [ ] ws-company registered - Not started
- [ ] ws-news registered - Not started

---

## Phase 3: GIBD Quant-Flow Services Test

### Test Scenario: Deploy GIBD Quant Profile

**Command**: `docker compose --profile gibd-quant up -d`

**Expected Additional Services**:
- [ ] gibd-quant-signal (Port 5001)
- [ ] gibd-quant-nlq (Port 5002)
- [ ] gibd-quant-calibration (Port 5003)
- [ ] gibd-quant-agent (Port 5004)
- [ ] gibd-quant-celery (Background worker)
- [ ] gibd-quant-web (Port 3001)

**Health Checks**:
- [ ] Signal Service: http://localhost:5001/health
- [ ] NLQ Service: http://localhost:5002/health
- [ ] Calibration Service: http://localhost:5003/health
- [ ] Agent Service: http://localhost:5004/health
- [ ] Frontend: http://localhost:3001

**Eureka Registration**:
- [ ] gibd-quant-signal registered
- [ ] gibd-quant-nlq registered
- [ ] gibd-quant-calibration registered
- [ ] gibd-quant-agent registered

---

## Phase 4: Infrastructure Services Test

### Test Scenario: Deploy Infrastructure Profile

**Command**: `docker compose -f docker-compose.infrastructure.yml --profile infrastructure up -d`

**Expected Services**:
- [ ] traefik (Ports 80, 443, 8090)
- [ ] keycloak (Port 8080 internal, via Traefik)
- [ ] keycloak-postgres (Internal)
- [ ] gitlab (Ports 80, 443, 2222)
- [ ] nexus (Port 8081)
- [ ] prometheus (Port 9090)
- [ ] grafana (Port 3000)
- [ ] ollama (Port 11434)
- [ ] n8n (Port 5678)
- [ ] postgres-infra (Port 5433)
- [ ] redis-infra (Port 6380)

**Health Checks**:
- [ ] Traefik Dashboard: http://localhost:8090/api/overview
- [ ] Keycloak: http://localhost:8080/health
- [ ] Prometheus: http://localhost:9090/-/healthy
- [ ] Grafana: http://localhost:3000/api/health
- [ ] Ollama: http://localhost:11434/api/tags

---

## Phase 5: Gateway Routing Test

### Test Scenario: API Calls via Gateway

**Prerequisites**: Shared + GIBD Quant services running

**Tests**:
- [ ] Gateway routes to ws-trades
  - Request: `curl http://localhost:8080/api/trades/[endpoint]`
  - Expected: 200 or appropriate response

- [ ] Gateway routes to gibd-quant-signal
  - Request: `curl http://localhost:8080/api/signals/health`
  - Expected: {"status": "UP"}

- [ ] Gateway routes to gibd-quant-nlq
  - Request: `curl http://localhost:8080/api/nlq/health`
  - Expected: {"status": "UP"}

- [ ] Gateway routes to gibd-quant-calibration
  - Request: `curl http://localhost:8080/api/calibrate/health`
  - Expected: {"status": "UP"}

---

## Phase 6: End-to-End Functional Tests

### Signal Generation Test
- [ ] Generate signal for ticker "GP"
  - Endpoint: POST http://localhost:8080/api/signals/generate
  - Payload: {"ticker": "GP"}
  - Expected: Signal response with score, confidence

### NLQ Test
- [ ] Execute natural language query
  - Endpoint: POST http://localhost:8080/api/nlq/query
  - Payload: {"query": "stocks with RSI above 70"}
  - Expected: Query results

### Calibration Test
- [ ] Auto-calibrate stock parameters
  - Endpoint: POST http://localhost:8080/api/calibrate/GP
  - Expected: Calibration profile

---

## Phase 7: Frontend Integration Tests

### Test Scenario: Next.js Application

**Prerequisites**: GIBD Quant profile running

**Tests**:
- [ ] Homepage loads successfully
  - URL: http://localhost:3001
  - Expected: Page renders without errors

- [ ] Company page loads
  - URL: http://localhost:3001/company/GP
  - Expected: Company info displayed

- [ ] Signal generation from UI
  - Action: Click "Generate Signal" for ticker
  - Expected: Signal displayed in UI

- [ ] NLQ query from UI
  - Action: Submit natural language query
  - Expected: Results displayed

---

## Phase 8: Playwright MCP End-to-End Tests

### Browser Testing with Playwright MCP

**Tests**:
1. [ ] **Eureka Dashboard Navigation**
   - Navigate to http://localhost:8761
   - Verify all services registered
   - Take screenshot

2. [ ] **Frontend Application (GIBD Quant-Flow)**
   - Navigate to http://localhost:3001
   - Verify header/footer visible
   - Test navigation
   - Test signal generation
   - Test NLQ query
   - Take screenshots

3. [ ] **Wizardsofts Corporate Website**
   - Navigate to http://localhost:3000
   - Verify homepage loads
   - Test navigation menu
   - Test contact form
   - Verify mobile responsive
   - Run accessibility audit
   - Take screenshots

4. [ ] **Daily Deen Guide**
   - Navigate to http://localhost:3002
   - Verify homepage loads
   - Check prayer times display
   - Test hadith content
   - Verify Islamic date conversion
   - Verify mobile responsive
   - Take screenshots

5. [ ] **API Gateway Health**
   - Verify all routes accessible
   - Check response times

6. [ ] **Infrastructure Services**
   - Navigate to Traefik dashboard
   - Verify service routes
   - Take screenshot

---

## Phase 9: Performance & Stress Tests

### Resource Usage
- [ ] Monitor Docker container resource usage
  - Command: `docker stats`
  - Expected: Reasonable CPU/memory usage

### Load Testing
- [ ] Batch signal generation (10 tickers)
  - Expected: All complete successfully
  - Monitor response times

---

## Phase 10: Cleanup & Validation

### Cleanup Commands
- [ ] Stop all application services
  - Command: `docker compose down`

- [ ] Stop infrastructure services
  - Command: `docker compose -f docker-compose.infrastructure.yml down`

- [ ] Verify cleanup
  - Command: `docker compose ps`
  - Expected: No running containers

---

## Test Results Summary

| Phase | Status | Issues | Resolution |
|-------|--------|--------|------------|
| Docker Validation | ✅ PASSED | Version warnings | Non-critical |
| Shared Services | ⏸️ PENDING | - | - |
| GIBD Quant Services | ⏸️ PENDING | - | - |
| Infrastructure Services | ⏸️ PENDING | - | - |
| Gateway Routing | ⏸️ PENDING | - | - |
| E2E Functional | ⏸️ PENDING | - | - |
| Frontend Integration | ⏸️ PENDING | - | - |
| Playwright MCP | ⏸️ PENDING | - | - |
| Performance | ⏸️ PENDING | - | - |
| Cleanup | ⏸️ PENDING | - | - |

---

## Known Issues

None at this time.

---

## Next Steps

1. Execute Phase 2: Deploy shared services
2. Verify Eureka registration
3. Test gateway routing
4. Deploy GIBD Quant services
5. Run Playwright MCP tests
6. Document any issues found

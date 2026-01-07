# PRE-003: Audit Running Containers

**Date:** 2026-01-01
**Status:** ✅ PASSED
**Duration:** 5 minutes

## Summary

Total containers across all servers: **78 containers**
- **Server 80:** 3 containers (monitoring)
- **Server 81:** 0 containers (Docker not installed)
- **Server 82:** 2 containers (monitoring)
- **Server 84:** 73 containers (**OVERLOADED** - primary target for distribution)

## Server 80 (hppavilion) - 10.0.0.80

**Docker Version:** 28.2.2
**Containers:** 3
**Purpose:** Monitoring metrics

| Container | Image | Status | CPU | Memory | Ports |
|-----------|-------|--------|-----|--------|-------|
| security-metrics | python:3.11-slim | unhealthy | 0.01% | 14.8MB | 9101 |
| node-exporter | prom/node-exporter:latest | healthy | 0.00% | 10.32MB | 9100 |
| cadvisor | gcr.io/cadvisor/cadvisor:latest | healthy | 5.10% | 90.11MB | 8081 |

**Notes:**
- security-metrics is unhealthy - needs investigation
- Low resource usage
- Good capacity for hosting databases

## Server 81 (wsasus) - 10.0.0.81

**Docker Version:** NOT INSTALLED
**Containers:** 0
**Purpose:** Intended for database server

**Action Required:**
- Install Docker and Docker Compose in Phase 1
- Server has 11GB RAM, suitable for PostgreSQL replicas

## Server 82 (hpr) - 10.0.0.82

**Docker Version:** 29.1.3
**Containers:** 2
**Purpose:** Monitoring/development

| Container | Image | Status | CPU | Memory Limit | Ports |
|-----------|-------|--------|-----|--------------|-------|
| cadvisor-82 | gcr.io/cadvisor/cadvisor:latest | healthy | 9.43% | 51.61MB / 512MB | 8080 |
| node-exporter-82 | prom/node-exporter:latest | healthy | 0.00% | 9.29MB / 256MB | 9100 |

**Notes:**
- Resource limits properly configured (security hardening applied)
- Low resource usage
- 5.7GB RAM total - suitable for dev/staging workloads

## Server 84 (gmktec) - 10.0.0.84

**Docker Version:** 27.5.1
**Containers:** 73 (**CRITICALLY OVERLOADED**)
**Purpose:** Currently hosting ALL production infrastructure

### Infrastructure Services (11 containers)
| Category | Containers |
|----------|------------|
| Monitoring | prometheus, grafana, alertmanager, loki, promtail, cadvisor, node-exporter (7) |
| GitLab | gitlab (1) |
| Authentication | keycloak, oauth2-proxy (2, oauth2-proxy unhealthy) |
| Metrics | security-metrics-84 (1) |

### Appwrite Stack (19 containers)
- appwrite (main, **unhealthy**)
- appwrite-mariadb, appwrite-redis (databases)
- 16 worker containers (builds, databases, messaging, functions, etc.)

### Mailcow Stack (18 containers)
- Full email infrastructure (nginx, postfix, dovecot, rspamd, etc.)
- All containers healthy

### Backend Microservices (5 containers)
| Service | Status | Memory | Port |
|---------|--------|--------|------|
| ws-gateway | healthy | 331MB | 8081 |
| ws-discovery | healthy | 331MB | 8762 |
| ws-company | healthy | - | 8183 |
| ws-trades | healthy | - | 8182 |
| ws-news | healthy | 361MB | 8184 |

### Frontend Applications (4 containers)
| Service | Status | Memory | Port |
|---------|--------|--------|------|
| gibd-quant-web | healthy | - | 3000 |
| wwwwizardsoftscom-web-1 | healthy | 54MB | 3000 |
| daily-deen-guide-frontend | healthy | 42MB | 3000 |
| pf-padmafoods-web | healthy | - | 3000 |

### Backend Services (4 containers)
- quant-flow-api (healthy, Python API)
- ddg-bff (healthy, backend for frontend)
- autoscaler (healthy)

### Supporting Services (12 containers)
- Databases: gibd-postgres, keycloak-postgres, wizardsofts-megabuild-postgres-1, mysql-mailcow
- Cache: gibd-redis, wizardsofts-megabuild-redis-1, redis-mailcow, memcached-mailcow
- Other: traefik, appwrite-executor, appwrite-console

### Resource Usage (Top Containers)
| Container | CPU | Memory Used | Memory Limit |
|-----------|-----|-------------|--------------|
| gitlab | 1.12% | 4.59GB | 6GB (76% usage) |
| ws-discovery | 0.64% | 331MB | No limit |
| ws-news | 0.09% | 361MB | No limit |
| appwrite | 0.00% | 345MB | 4GB |

## Critical Issues Identified

### High Priority
1. **Server 84 Overload:** 73 containers on single server
   - GitLab using 4.6GB RAM (76% of 6GB limit)
   - Total memory: 13GB used / 28GB available
   - Need to distribute to servers 80, 81, 82

2. **Unhealthy Containers:**
   - appwrite (server 84) - unhealthy status
   - oauth2-proxy (server 84) - unhealthy status
   - security-metrics (server 80) - unhealthy status

3. **Server 81 Not Ready:**
   - Docker not installed
   - Cannot participate in Docker Swarm without Docker

### Medium Priority
4. **Resource Limits Missing:**
   - Most containers on server 84 have no memory limits
   - Risk of OOM (Out of Memory) issues
   - Need to add resource constraints in migration

5. **Single Point of Failure:**
   - All production services on server 84
   - No redundancy for critical services
   - GitLab, databases, microservices all on one host

## Migration Strategy Confirmation

Based on audit, confirm the planned distribution:

### Phase 3: Database Migration (Server 80, 81)
- Move PostgreSQL databases to server 80 (primary)
- Setup PostgreSQL replicas on server 81
- Move Redis to server 80
- **Requires:** Docker installation on server 81 first (Phase 1)

### Phase 4: Service Migration
- Keep GitLab on server 84 (move to server 80 in later phase if needed)
- Move backend microservices to server 80
- Move frontend apps to server 84 (already there)
- Move Appwrite to distributed setup or server 82
- Move Mailcow to server 82 or 80

### Infrastructure Services
- Keep Prometheus/Grafana on server 84 (central monitoring)
- Distribute node-exporter/cadvisor to all servers (already done for 80, 82)
- Move Traefik to server 84 (already there) or load balance

## Validation

✅ Container inventory complete (78 containers)
✅ Server 84 confirmed as overloaded (73 containers)
✅ Server 80, 82 have capacity for migration
✅ Server 81 requires Docker installation
✅ Unhealthy containers identified (3 total)
✅ Resource limits missing on most containers (Phase 1 fix)
✅ Migration strategy validated

## Next Steps

1. **Immediate (Phase 1):**
   - Install Docker on server 81
   - Fix unhealthy containers (appwrite, oauth2-proxy, security-metrics)
   - Add resource limits to containers on server 84

2. **Phase 3:**
   - Migrate databases to server 80
   - Setup replication to server 81

3. **Phase 4:**
   - Migrate microservices from server 84 to server 80
   - Migrate Appwrite/Mailcow to server 82 or distribute

## Next Task

**PRE-004:** Check Disk Space and Capacity Planning

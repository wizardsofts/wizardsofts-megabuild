# Phase 4: Service Migration - Detailed Plan

**Date:** 2026-01-01
**Status:** PLANNING
**Risk Level:** MEDIUM
**Estimated Duration:** 4-6 hours

---

## Overview

Phase 4 focuses on migrating services from server 84 to their target servers in the distributed architecture. Priority is given to monitoring infrastructure and microservices modernization.

## Service Inventory (Server 84)

### Monitoring Stack (7 containers) - Target: Server 81
- prometheus
- grafana
- alertmanager
- loki
- promtail
- cadvisor
- node-exporter

### WS Microservices (5 containers) - Target: Server 84 (Swarm)
- ws-gateway
- ws-discovery
- ws-company
- ws-trades
- ws-news

### Appwrite Stack (16+ containers) - Target: Server 82 (Optional)
- appwrite (main app + console)
- 15+ worker containers
- appwrite-executor

### Mailcow Stack (10+ containers) - Target: Server 82 (Optional)
- Multiple Mailcow services

### Frontend Apps - Target: Server 84 (Swarm)
- gibd-quant-web
- daily-deen-guide
- pf-padmafoods-web
- etc.

---

## Migration Strategy

### Phase 4a: Monitoring Migration (PRIORITY 1)

**Objective:** Move monitoring stack to server 81 for centralized observability

**Services to Migrate:**
1. Prometheus (metrics collection)
2. Grafana (visualization)
3. Alertmanager (alerting)
4. Loki (log aggregation)
5. Promtail (log shipper)
6. cAdvisor (container metrics)
7. Node Exporter (host metrics)

**Benefits:**
- Dedicated monitoring server
- Observability for migration process
- Separation of concerns
- Better resource utilization

**Steps:**
1. Export Prometheus data and Grafana dashboards
2. Deploy monitoring stack on server 81 as Swarm services
3. Configure Prometheus to scrape all servers
4. Import Grafana dashboards
5. Test alerting
6. Switch traffic to new monitoring

**Duration:** 2-3 hours

---

### Phase 4b: Microservices Modernization (PRIORITY 2)

**Objective:** Convert microservices to Docker Swarm services on server 84

**Services:**
1. ws-gateway (API Gateway)
2. ws-discovery (Service Discovery)
3. ws-company (Company Service)
4. ws-trades (Trades Service)
5. ws-news (News Service)

**Why Keep on Server 84:**
- Already optimized for this server
- Close to Traefik (reverse proxy)
- Low risk, high reward (just modernization)

**Changes:**
- Convert to Swarm services
- Update database connections (→ server 80)
- Add resource limits
- Improve health checks
- Enable rolling updates

**Duration:** 2-3 hours

---

### Phase 4c: Large Stack Migration (OPTIONAL/DEFERRED)

**Appwrite Stack:**
- **Current:** Server 84, 16+ containers
- **Target:** Server 82
- **Complexity:** HIGH (many interconnected services)
- **Decision:** DEFER to later or separate migration project

**Mailcow Stack:**
- **Current:** Server 84, 10+ containers
- **Target:** Server 82
- **Complexity:** HIGH (email infrastructure)
- **Decision:** DEFER to later or separate migration project

**Rationale for Deferral:**
- Both stacks are complex and stable
- Low ROI for migration effort
- Can stay on server 84 without issues
- Focus on higher-value migrations first

---

## Detailed Steps: Phase 4a - Monitoring Migration

### Step 1: Export Current Monitoring Data

**Prometheus:**
```bash
# Stop Prometheus gracefully
docker stop prometheus

# Copy data directory
docker cp prometheus:/prometheus /tmp/prometheus-backup

# Export config
docker cp prometheus:/etc/prometheus/prometheus.yml /tmp/
```

**Grafana:**
```bash
# Export dashboards via API
curl -H "Authorization: Bearer <token>" \
  http://10.0.0.84:3002/api/search > /tmp/grafana-dashboards.json

# Copy Grafana data
docker cp grafana:/var/lib/grafana /tmp/grafana-backup
```

**Loki:**
```bash
# Copy Loki data
docker cp loki:/loki /tmp/loki-backup
```

### Step 2: Deploy Monitoring Stack on Server 81

**Create Docker Compose for Swarm:**
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    networks:
      - monitoring-network
    volumes:
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname==wsasus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    networks:
      - monitoring-network
    volumes:
      - grafana-data:/var/lib/grafana
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname==wsasus
    ports:
      - "3000:3000"

  # ... similar for other services
```

### Step 3: Configure Prometheus Scraping

**Update prometheus.yml to scrape all servers:**
```yaml
scrape_configs:
  # Server 80 (Database)
  - job_name: 'server-80-node'
    static_configs:
      - targets: ['10.0.0.80:9100']

  # Server 81 (Monitoring)
  - job_name: 'server-81-node'
    static_configs:
      - targets: ['10.0.0.81:9100']

  # Server 82 (Dev/Staging)
  - job_name: 'server-82-node'
    static_configs:
      - targets: ['10.0.0.82:9100']

  # Server 84 (Production)
  - job_name: 'server-84-node'
    static_configs:
      - targets: ['10.0.0.84:9100']

  # Database metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['10.0.0.80:9187']

  # Docker Swarm
  - job_name: 'docker-swarm'
    static_configs:
      - targets: ['10.0.0.84:9323']
```

### Step 4: Import Data

**Prometheus:**
```bash
# Copy data to new Prometheus container on server 81
docker cp /tmp/prometheus-backup <container>:/prometheus
```

**Grafana:**
```bash
# Import dashboards via API or manual upload
# Copy data directory
docker cp /tmp/grafana-backup <container>:/var/lib/grafana
```

### Step 5: Test and Verify

**Verification Checklist:**
- [ ] Prometheus scraping all targets
- [ ] Grafana dashboards accessible
- [ ] Historical data available
- [ ] Alerts configured and working
- [ ] Logs flowing to Loki

---

## Detailed Steps: Phase 4b - Microservices Modernization

### For Each Microservice:

**1. Check Current Configuration:**
```bash
docker inspect ws-gateway > ws-gateway-config.json
```

**2. Create Swarm Service:**
```bash
docker service create \
  --name ws-gateway \
  --network services-network \
  --replicas 1 \
  --constraint 'node.hostname==gmktec' \
  --env SPRING_DATASOURCE_URL=jdbc:postgresql://10.0.0.80:5435/gibd \
  --publish 8080:8080 \
  wizardsofts-megabuild-ws-gateway:latest
```

**3. Update Database Connections:**
```bash
# Old: localhost:5432
# New: 10.0.0.80:5435
```

**4. Test Service:**
```bash
curl http://10.0.0.84:8080/health
```

**5. Stop Old Container:**
```bash
docker stop ws-gateway-old
```

---

## Success Criteria

### Phase 4a: Monitoring
- [ ] All monitoring services running on server 81
- [ ] Prometheus scraping all 4 servers
- [ ] Grafana accessible with all dashboards
- [ ] Alerting functional
- [ ] Historical data preserved

### Phase 4b: Microservices
- [ ] All 5 microservices as Swarm services
- [ ] Connected to new databases on server 80
- [ ] Health checks passing
- [ ] API responses working
- [ ] Old containers stopped

---

## Rollback Plan

### Monitoring
- Keep old monitoring containers stopped but not removed
- Can restart quickly if issues: `docker start prometheus grafana`

### Microservices
- Old containers available for rollback
- Database connections can switch back to old databases
- Minimal risk due to blue-green approach

---

## Timeline Estimate

| Task | Duration |
|------|----------|
| **Phase 4a: Monitoring** | 2-3 hours |
| - Export data | 30 min |
| - Deploy on server 81 | 1 hour |
| - Configure & test | 1-1.5 hours |
| **Phase 4b: Microservices** | 2-3 hours |
| - Plan & prepare | 30 min |
| - Deploy services | 1 hour |
| - Update connections | 30 min |
| - Test & verify | 1 hour |
| **Total** | **4-6 hours** |

---

## Decision Point

**Before proceeding with Phase 4:**

✅ **Recommended:**
- Phase 4a: Monitoring Migration (HIGH VALUE)
- Phase 4b: Microservices Modernization (MEDIUM VALUE)

⏸️ **Deferred:**
- Phase 4c: Appwrite/Mailcow Migration (LOW VALUE for effort)

**Next Steps:**
1. Start with Phase 4a (Monitoring)
2. Then Phase 4b (Microservices)
3. Skip Phase 4c for now (revisit later if needed)

---

**Status:** Ready to begin Phase 4a
**Next Task:** Export Prometheus and Grafana data from server 84

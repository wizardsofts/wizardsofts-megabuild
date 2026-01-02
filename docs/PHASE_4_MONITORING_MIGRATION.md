# Phase 4: Monitoring Stack Migration to Server 81

**Date Started:** 2026-01-01
**Status:** IN PROGRESS
**Risk Level:** MEDIUM (Monitoring downtime acceptable)
**Estimated Duration:** 2-3 hours

---

## Objective

Move entire monitoring stack from Server 84 to Server 81 to:
1. Free up resources on production server (Server 84)
2. Isolate monitoring from production workloads
3. Follow distributed architecture plan
4. Improve monitoring reliability

---

## Current State Analysis

### Monitoring Services on Server 84 (To Migrate)

| Service | Image | Port | Data Location | Size | Purpose |
|---------|-------|------|---------------|------|---------|
| **prometheus** | prom/prometheus:latest | 9090 | /home/wizardsofts/prometheus-data | ~500MB | Metrics collection |
| **grafana** | grafana/grafana:latest | 3002 | auto-scaling_grafana-data volume | ~200MB | Visualization |
| **loki** | grafana/loki:2.9.2 | 3100 | None (in-memory) | - | Log aggregation |
| **promtail** | grafana/promtail:2.9.2 | - | None | - | Log shipping |
| **alertmanager** | prom/alertmanager:latest | 9093 | None (default) | - | Alerting |

### Metrics Exporters (Stay on Each Server)

| Service | Server | Port | Purpose |
|---------|--------|------|---------|
| **node-exporter** | 84, 80, 81, 82 | 9100 | System metrics |
| **cadvisor** | 84, 80, 82 | 8080/8085 | Container metrics |
| **security-metrics** | 84, 80, 81 | 9101 | Security monitoring |

**Total Migration Size:** ~700 MB data + configs

---

## Server 81 Current State

- **OS:** Ubuntu (assumption based on Server 82)
- **Docker Containers:** 0 (clean slate)
- **Disk Space:**
  - Root: 67GB available (29% used)
  - /home: 112GB available (1% used)
- **RAM:** 11 GB total
- **Status:** Ready for deployment

---

## Migration Strategy

### Approach: Blue-Green with Docker Swarm

1. **Deploy new monitoring stack on Server 81** via Docker Swarm
2. **Transfer critical data** (Prometheus metrics, Grafana dashboards)
3. **Update scrape configs** to use new Prometheus location
4. **Test thoroughly** before switching
5. **Update all references** to monitoring services
6. **Stop old monitoring stack** on Server 84

### Why Not Direct Migration?
- Cleaner to deploy fresh stack via Docker Swarm
- Easier rollback if issues occur
- Better for long-term maintenance
- Prometheus data can be rebuilt from exporters

---

## Detailed Migration Steps

### Step 1: Prepare Server 81

```bash
# SSH into Server 81
ssh wizardsofts@10.0.0.81

# Verify Docker Swarm membership
docker node ls

# Create directories for configs
mkdir -p ~/monitoring/{prometheus,grafana,loki,alertmanager}
mkdir -p ~/monitoring/grafana/{provisioning,dashboards}
```

### Step 2: Transfer Configuration Files

```bash
# From local machine or Server 84
scp -r wizardsofts@10.0.0.84:/home/wizardsofts/prometheus-config/* \
    wizardsofts@10.0.0.81:~/monitoring/prometheus/

scp -r wizardsofts@10.0.0.84:/home/wizardsofts/grafana-config/* \
    wizardsofts@10.0.0.81:~/monitoring/grafana/

scp -r wizardsofts@10.0.0.84:/home/wizardsofts/grafana-provisioning/* \
    wizardsofts@10.0.0.81:~/monitoring/grafana/provisioning/

scp -r wizardsofts@10.0.0.84:/home/wizardsofts/grafana-dashboards/* \
    wizardsofts@10.0.0.81:~/monitoring/grafana/dashboards/
```

### Step 3: Update Prometheus Configuration

Edit `~/monitoring/prometheus/prometheus.yml` on Server 81:
- Update all target addresses to use IPs (not service names)
- Ensure all servers (80, 81, 82, 84) are in scrape configs
- Update alertmanager reference to localhost

### Step 4: Create Docker Swarm Stack

Create `monitoring-stack.yml` with placement constraints for Server 81:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - prometheus-data:/prometheus
      - /home/wizardsofts/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    deploy:
      placement:
        constraints:
          - node.labels.server==81
      replicas: 1

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3002:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - /home/wizardsofts/monitoring/grafana/grafana.ini:/etc/grafana/grafana.ini:ro
      - /home/wizardsofts/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - /home/wizardsofts/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    environment:
      - GF_SERVER_ROOT_URL=http://10.0.0.81:3002
      - GF_SECURITY_ADMIN_PASSWORD=${GF_ADMIN_PASSWORD}
    deploy:
      placement:
        constraints:
          - node.labels.server==81
      replicas: 1

  loki:
    image: grafana/loki:2.9.2
    ports:
      - "3100:3100"
    deploy:
      placement:
        constraints:
          - node.labels.server==81
      replicas: 1

  promtail:
    image: grafana/promtail:2.9.2
    volumes:
      - /var/log:/var/log:ro
      - /var/snap/docker/common/var-lib-docker/containers:/var/lib/docker/containers:ro
    deploy:
      mode: global  # Run on all nodes
      restart_policy:
        condition: on-failure

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    deploy:
      placement:
        constraints:
          - node.labels.server==81
      replicas: 1

volumes:
  prometheus-data:
  grafana-data:
```

### Step 5: Label Server 81 Node

```bash
# From any manager node (Server 84)
docker node update --label-add server=81 <server-81-node-id>
```

### Step 6: Deploy Stack

```bash
# From Server 84 (manager node)
docker stack deploy -c monitoring-stack.yml monitoring
```

### Step 7: Verify Deployment

```bash
# Check services
docker stack services monitoring

# Check if running on Server 81
docker stack ps monitoring

# Test Prometheus
curl http://10.0.0.81:9090/-/healthy

# Test Grafana
curl http://10.0.0.81:3002/api/health
```

### Step 8: Update Application References

Update any hardcoded references to monitoring:
- Grafana dashboards: Change from `http://10.0.0.84:3002` to `http://10.0.0.81:3002`
- Prometheus queries: Change from `http://10.0.0.84:9090` to `http://10.0.0.81:9090`
- Alertmanager: Change from `http://10.0.0.84:9093` to `http://10.0.0.81:9093`

### Step 9: Transfer Historical Data (Optional)

```bash
# Copy Prometheus data (if needed)
ssh wizardsofts@10.0.0.84 "tar -czf /tmp/prometheus-data.tar.gz -C /home/wizardsofts/prometheus-data ."
scp wizardsofts@10.0.0.84:/tmp/prometheus-data.tar.gz /tmp/
scp /tmp/prometheus-data.tar.gz wizardsofts@10.0.0.81:/tmp/

# On Server 81, extract into Docker volume
ssh wizardsofts@10.0.0.81
PROM_CONTAINER=$(docker ps --filter name=monitoring_prometheus -q)
docker cp /tmp/prometheus-data.tar.gz $PROM_CONTAINER:/tmp/
docker exec $PROM_CONTAINER sh -c "cd /prometheus && tar -xzf /tmp/prometheus-data.tar.gz"
docker restart $PROM_CONTAINER
```

### Step 10: Stop Old Monitoring Stack

```bash
# On Server 84
docker stop prometheus grafana loki promtail alertmanager

# Verify stopped
docker ps | grep -E '(prometheus|grafana|loki|promtail|alertmanager)'
```

### Step 11: Clean Up (After 48 Hours)

```bash
# Remove old containers
docker rm prometheus grafana loki promtail alertmanager

# Remove old volumes (keep backup)
docker volume ls | grep monitoring
```

---

## Rollback Plan

### If New Stack Fails

```bash
# Stop new stack
docker stack rm monitoring

# Restart old stack on Server 84
ssh wizardsofts@10.0.0.84
docker start prometheus grafana loki promtail alertmanager

# Verify services
docker ps | grep -E '(prometheus|grafana|loki)'
```

---

## Success Criteria

✅ **Deployment:**
- All 5 monitoring services running on Server 81
- Services accessible via their ports
- Docker Swarm stack healthy

✅ **Data:**
- Prometheus scraping all targets successfully
- Grafana dashboards loading correctly
- Loki receiving logs from all servers

✅ **Performance:**
- Query response times acceptable
- No missing metrics
- Alerts functioning

✅ **Stability:**
- No crashes for 48+ hours
- Memory usage under 8 GB (leaving 3 GB buffer)
- CPU usage acceptable

---

## Network Access Requirements

### Firewall Rules for Server 81

```bash
# Allow from local network only
sudo ufw allow from 10.0.0.0/24 to any port 9090 proto tcp  # Prometheus
sudo ufw allow from 10.0.0.0/24 to any port 3002 proto tcp  # Grafana
sudo ufw allow from 10.0.0.0/24 to any port 3100 proto tcp  # Loki
sudo ufw allow from 10.0.0.0/24 to any port 9093 proto tcp  # Alertmanager
```

### Services Must Scrape

- Server 80: node-exporter (9100), cadvisor (8081), security (9101)
- Server 81: node-exporter (9100), security (9101)
- Server 82: node-exporter (9100), cadvisor (8080)
- Server 84: node-exporter (9100), cadvisor (8080), security (9101), applications

---

## Expected Resource Usage on Server 81

| Service | Memory | CPU | Disk |
|---------|--------|-----|------|
| Prometheus | 2-3 GB | 0.5-1 core | ~10 GB (30 days retention) |
| Grafana | 500 MB | 0.2 core | ~500 MB |
| Loki | 1-2 GB | 0.3 core | ~5 GB |
| Promtail | 100 MB | 0.1 core | - |
| AlertManager | 200 MB | 0.1 core | ~100 MB |
| **Total** | **~7 GB** | **~2 cores** | **~15 GB** |

**Server 81 Capacity:** 11 GB RAM, 4 CPU cores → ✅ Sufficient headroom

---

## Post-Migration Tasks

1. Update [docs/DISTRIBUTED_ARCHITECTURE_PLAN.md](DISTRIBUTED_ARCHITECTURE_PLAN.md) - mark monitoring migration complete
2. Update [CLAUDE.md](../CLAUDE.md) - document new Grafana URL (http://10.0.0.81:3002)
3. Create Serena memory: `monitoring-migration-complete`
4. Test all Grafana dashboards
5. Verify alert delivery
6. Monitor for 48 hours before cleanup

---

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Preparation | 30 min | Transfer configs, create directories |
| Deployment | 15 min | Deploy Docker Swarm stack |
| Verification | 30 min | Test all services, verify data flow |
| Data Transfer | 30 min | Optional historical data migration |
| Cleanup | 15 min | Stop old services |
| **Total** | **~2 hours** | Plus 48-hour monitoring period |

---

**Next Step:** Execute Step 1 (Prepare Server 81)

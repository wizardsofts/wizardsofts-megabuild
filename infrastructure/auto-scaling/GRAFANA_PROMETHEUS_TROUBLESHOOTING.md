# Grafana & Prometheus Troubleshooting Guide

## Server Environment: 10.0.0.84

### System Configuration
- **OS**: Ubuntu with Docker installed via **Snap**
- **Critical Limitation**: Docker Snap has AppArmor restrictions that prevent mounting from `/opt`
- **Credentials**: 
  - SSH: `wizardsofts@10.0.0.84` (password: `29Dec2#24`)
  - Grafana: `admin:admin`

### Deployment Architecture

```
Server 10.0.0.84
├── Prometheus: http://10.0.0.84:9090
│   ├── Config: ~/prometheus-config/prometheus.yml
│   ├── Data: ~/prometheus-data/
│   └── Targets:
│       ├── prometheus (self-monitoring)
│       ├── node-exporter (system metrics)
│       ├── cadvisor (container metrics - optional)
│       └── auto-scaler (app metrics - optional)
│
├── Grafana: http://10.0.0.84:3002
│   ├── Data Volume: wizardsofts-megabuild_grafana-data
│   ├── Dashboards: /var/lib/grafana/dashboards/
│   │   ├── executive-dashboard.json (15 panels)
│   │   └── autoscaling-dashboard.json (empty template)
│   └── Provisioning: /etc/grafana/provisioning/
│
└── node-exporter: :9100 (Docker container)
```

## Common Issues & Solutions

### Issue 1: "read-only file system" Error

**Error Message:**
```
error while creating mount source path '/opt/wizardsofts-megabuild/...': 
mkdir /opt/wizardsofts-megabuild: read-only file system
```

**Root Cause:** Docker Snap AppArmor security policies prevent mounting from `/opt`

**Solution:** Use home directory mounts instead
```yaml
# ❌ WRONG - Will fail on Snap Docker
volumes:
  - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

# ✅ CORRECT - Works with Snap Docker  
volumes:
  - ~/prometheus-config/prometheus.yml:/etc/prometheus/prometheus.yml
  - ~/prometheus-data:/prometheus
```

**Deployment Steps:**
```bash
# On server 10.0.0.84
mkdir -p ~/prometheus-config ~/prometheus-data
cp monitoring/prometheus/prometheus.yml ~/prometheus-config/
chmod 777 ~/prometheus-data  # Prometheus runs as user 65534:65534
docker-compose up -d prometheus
```

### Issue 2: Prometheus Not Scraping Metrics

**Symptoms:**
- Grafana dashboards show "No data"
- Prometheus `/targets` page shows only 1 target (itself)

**Diagnosis Commands:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check what config Prometheus is actually using
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Test if Prometheus can reach node-exporter
docker exec prometheus wget -O- http://node-exporter:9100/metrics | head
```

**Common Causes:**

1. **Config file not mounted correctly**
   - Verify: `docker inspect prometheus --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'`
   - Fix: Recreate container with correct mounts

2. **Containers on different networks**
   - Check: `docker inspect prometheus --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{println}}{{end}}'`
   - Fix: `docker network connect <network-name> prometheus`

3. **node-exporter not running**
   - Check: `docker ps | grep node-exporter`
   - Fix: Start node-exporter or update scrape config

### Issue 3: Grafana Dashboard Shows "An unexpected error happened"

**Symptoms:**
- Dashboard loads but specific panels show error
- Example: "System Status" panel in Executive dashboard

**Root Cause:** Dashboard JSON has wrapper structure

**Wrong Format (has wrapper):**
```json
{
  "dashboard": {
    "id": null,
    "title": "My Dashboard",
    "panels": [...]
  },
  "overwrite": true
}
```

**Correct Format (unwrapped):**
```json
{
  "id": null,
  "title": "My Dashboard",
  "panels": [...]
}
```

**Fix Script:**
```bash
# Unwrap dashboard
cat dashboard.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'dashboard' in data:
    dashboard = data['dashboard']
    dashboard.pop('id', None)
    print(json.dumps(dashboard, indent=2))
else:
    print(json.dumps(data, indent=2))
" > dashboard-unwrapped.json

# Deploy to container
docker cp dashboard-unwrapped.json grafana:/var/lib/grafana/dashboards/
docker exec -u 0 grafana chown 472:472 /var/lib/grafana/dashboards/dashboard-unwrapped.json
docker restart grafana
```

### Issue 4: Dashboard Panels Show "No data"

**Diagnosis Process:**

1. **Verify Prometheus has metrics:**
   ```bash
   # Check if metrics exist
   curl 'http://localhost:9090/api/v1/query?query=node_memory_MemTotal_bytes'
   
   # List all node metrics
   curl 'http://localhost:9090/api/v1/label/__name__/values' | grep node_
   ```

2. **Check Grafana datasource:**
   ```bash
   # Test datasource connection
   curl -u admin:admin http://localhost:3002/api/datasources
   ```

3. **Verify network connectivity:**
   ```bash
   # From Grafana to Prometheus
   docker exec grafana wget -O- http://prometheus:9090/api/v1/query?query=up
   ```

**Common Fixes:**
- Connect Grafana and Prometheus to same Docker network
- Restart Grafana after Prometheus config changes
- Wait 1-2 minutes for initial scrape to complete

### Issue 5: Changes to prometheus.yml Not Applied

**Problem:** Updated prometheus.yml but targets unchanged

**Causes:**
1. Config file not mounted (using default internal config)
2. Prometheus needs reload/restart
3. Wrong file path updated

**Verification:**
```bash
# Check what config Prometheus is actually using
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Compare with host file
cat ~/prometheus-config/prometheus.yml
```

**Fix:**
```bash
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# OR restart container
docker restart prometheus
```

## Monitoring Health Check Commands

### Quick Status Check
```bash
# Check all containers
docker ps --filter "name=prometheus|grafana|node-exporter"

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json, sys
data = json.load(sys.stdin)
for t in data['data']['activeTargets']:
    print(f\"{t['labels']['job']}: {t['health']}\")
"

# Test key metrics
curl -s 'http://localhost:9090/api/v1/query?query=node_uname_info' | grep -q result && echo "✅ Metrics OK" || echo "❌ No metrics"
```

### Full Diagnostic Script
```bash
#!/bin/bash
echo "=== Monitoring Stack Health Check ==="

echo -e "\n1. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "prometheus|grafana|node-exporter|cadvisor"

echo -e "\n2. Prometheus Targets:"
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json, sys
data = json.load(sys.stdin)
targets = data.get('data', {}).get('activeTargets', [])
for t in targets:
    job = t['labels']['job']
    health = t['health']
    symbol = '✅' if health == 'up' else '❌'
    print(f'{symbol} {job}: {health}')
"

echo -e "\n3. Available Metrics:"
METRICS=$(curl -s 'http://localhost:9090/api/v1/label/__name__/values' | python3 -c "
import json, sys
data = json.load(sys.stdin)
node_metrics = [m for m in data['data'] if m.startswith('node_')]
print(len(node_metrics))
")
echo "   node_* metrics: $METRICS"

echo -e "\n4. Grafana Dashboards:"
curl -s -u admin:admin http://localhost:3002/api/search?type=dash-db | python3 -c "
import json, sys
for dash in json.load(sys.stdin):
    print(f\"   - {dash['title']} (uid: {dash['uid']})\")
"

echo -e "\n✅ Health check complete"
```

## Key Metrics Queries

### System Monitoring
```promql
# RAM Usage (%)
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))

# CPU Usage (%)
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Disk Usage (%)
100 - ((node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"})

# SWAP Usage (%)
100 * (1 - (node_memory_SwapFree_bytes / node_memory_SwapTotal_bytes))

# System Uptime (days)
(time() - node_boot_time_seconds) / 86400

# Load Average (5m)
node_load5

# System Status (1=up, 0=down)
up{job="node-exporter"}
```

## Recovery Procedures

### Complete Monitoring Stack Reset
```bash
# 1. Stop all containers
cd /opt/wizardsofts-megabuild/infrastructure/auto-scaling
docker-compose down

# 2. Ensure configs are in place
mkdir -p ~/prometheus-config ~/prometheus-data
cp monitoring/prometheus/prometheus.yml ~/prometheus-config/
chmod 777 ~/prometheus-data

# 3. Start fresh
docker-compose up -d

# 4. Wait and verify
sleep 15
curl http://localhost:9090/api/v1/targets
```

### Grafana Dashboard Reset
```bash
# Copy fresh dashboards
docker cp ~/path/to/dashboard.json grafana:/var/lib/grafana/dashboards/
docker exec -u 0 grafana chown 472:472 /var/lib/grafana/dashboards/dashboard.json
docker restart grafana
```

## Contact Information

- **Grafana**: http://10.0.0.84:3002 (admin/admin)
- **Prometheus**: http://10.0.0.84:9090
- **Server**: ssh wizardsofts@10.0.0.84

## Lessons Learned

1. **Always check Docker installation type** (apt vs snap) - snap has significant restrictions
2. **Mount configs from allowed paths** - use `~/` instead of `/opt` on snap installations
3. **Unwrap Grafana dashboards** - remove `{"dashboard": {...}, "overwrite": true}` wrapper
4. **Verify container networks** - ensure Prometheus and targets can communicate
5. **Wait for first scrape** - metrics take 15-30 seconds to populate after container start
6. **Use numeric user IDs** - `chown 472:472` works when `grafana:grafana` doesn't

# Docker Snap Deployment Notes

## Issue: Docker Snap AppArmor Restrictions

When deploying on Ubuntu with Docker installed via Snap, AppArmor security policies prevent mounting files from certain directories like `/opt`.

### Error Message
```
error while creating mount source path '/opt/wizardsofts-megabuild/...': mkdir /opt/wizardsofts-megabuild: read-only file system
```

## Workaround for Server 10.0.0.84

### Prometheus Configuration

On the deployment server (10.0.0.84), Prometheus config and data are stored in the home directory:

```bash
~/prometheus-config/prometheus.yml  # Prometheus configuration
~/prometheus-data/                  # Prometheus time-series data
```

### Deployment Steps

1. **Create config directory:**
   ```bash
   mkdir -p ~/prometheus-config
   cp infrastructure/auto-scaling/monitoring/prometheus/prometheus.yml ~/prometheus-config/
   ```

2. **Create data directory:**
   ```bash
   mkdir -p ~/prometheus-data
   chmod 777 ~/prometheus-data  # Prometheus runs as user 65534:65534
   ```

3. **Deploy with docker-compose:**
   ```bash
   cd /opt/wizardsofts-megabuild/infrastructure/auto-scaling
   docker-compose up -d prometheus
   ```

### Other Affected Services

The same workaround was applied to Grafana:
- Dashboards copied directly into Docker volume: `wizardsofts-megabuild_grafana-data`
- Configuration files bind-mounted from allowed directories

## Alternative Solutions

1. **Use Docker from apt instead of snap** (requires reinstallation)
2. **Use named Docker volumes** instead of bind mounts
3. **Store configs in `/home` or `/tmp`** (current workaround)

## Verification

Check that Prometheus is scraping metrics:
```bash
curl http://localhost:9090/api/v1/targets
```

Expected targets:
- ✅ prometheus (localhost:9090)
- ✅ node-exporter (node-exporter:9100)
- ⚠️ cadvisor (may be down if not deployed)
- ⚠️ auto-scaler (may be down if not deployed)

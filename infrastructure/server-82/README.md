# Server 82 Metrics Exporters

This directory contains the metrics exporters for server 10.0.0.82.

Metrics are scraped by central Prometheus on server 84 (10.0.0.84:9090).
Visualization is done via central Grafana on server 84 (http://10.0.0.84:3002).

## Components

- **Node Exporter**: Exposes system metrics (CPU, memory, disk, network) on port 9100
- **cAdvisor**: Provides container metrics on port 8080

## Security

The firewall (UFW) is configured to only allow access from the local network (10.0.0.0/24):
- SSH: Port 22
- Node Exporter: Port 9100
- cAdvisor: Port 8080

## Docker Security Hardening

All containers are configured with security best practices:

**Node Exporter:**
- Memory limit: 256MB (reservation: 64MB)
- CPU limit: 0.5 cores (reservation: 0.1 cores)
- Read-only root filesystem
- All capabilities dropped except SYS_TIME
- no-new-privileges enabled
- tmpfs mounted on /tmp

**cAdvisor:**
- Memory limit: 512MB (reservation: 128MB)
- CPU limit: 1.0 core (reservation: 0.25 cores)
- Privileged mode (required for container inspection)
- no-new-privileges enabled

## Deployment

### Initial Setup

1. Copy this directory to the server:
   ```bash
   scp -r infrastructure/server-82 wizardsofts@10.0.0.82:~/
   ```

2. SSH into the server:
   ```bash
   ssh wizardsofts@10.0.0.82
   ```

3. Start the metric exporters:
   ```bash
   cd ~/server-82
   docker compose up -d
   ```

### Verify Deployment

Check that all containers are running:
```bash
docker ps
```

You should see:
- `node-exporter-82` (running)
- `cadvisor-82` (healthy)

### Check Resource Limits

Verify that containers are running within resource limits:
```bash
docker stats --no-stream
```

Expected:
- `node-exporter-82`: < 256MB memory, < 50% CPU
- `cadvisor-82`: < 512MB memory, < 100% CPU

### Check Metrics Endpoints

From any machine on the local network:

```bash
# Node Exporter metrics
curl http://10.0.0.82:9100/metrics

# cAdvisor metrics
curl http://10.0.0.82:8080/metrics
```

### Access Dashboards

Metrics are visualized via central Grafana on server 84:
```
http://10.0.0.84:3002
```

Look for "Server 82" dashboards in the Grafana interface.

## Central Prometheus Integration

This server is configured to be scraped by the central Prometheus instance on server 84 (10.0.0.84:9090).

The following scrape jobs need to be added to the central Prometheus configuration:

```yaml
scrape_configs:
  # Server 82 - System Metrics
  - job_name: 'node-exporter-82'
    static_configs:
      - targets: ['10.0.0.82:9100']
        labels:
          instance: 'server-82'
          server: 'hpr-server'
          environment: 'production'

  # Server 82 - Container Metrics
  - job_name: 'cadvisor-82'
    static_configs:
      - targets: ['10.0.0.82:8080']
        labels:
          instance: 'server-82'
```

After updating the central Prometheus configuration, reload it:
```bash
# On server 84
docker exec prometheus kill -HUP 1
```

## Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f node-exporter
docker compose logs -f cadvisor
```

### Restart Services

```bash
# All services
docker compose restart

# Specific service
docker compose restart node-exporter
docker compose restart cadvisor
```

### Stop Services

```bash
docker compose down
```

### Update Services

```bash
docker compose pull
docker compose up -d
```

## Dashboards

Dashboards for server 82 metrics are available on the central Grafana instance:
- **URL**: http://10.0.0.84:3002
- **Location**: "Server 82" folder in Grafana

To create custom dashboards, use the Grafana UI on server 84.

## Troubleshooting

### Container won't start

Check logs:
```bash
docker compose logs <service-name>
```

### Metrics not appearing in Grafana

1. Verify the exporters are running: `docker ps`
2. Check the metrics endpoints locally:
   ```bash
   curl http://localhost:9100/metrics  # Node Exporter
   curl http://localhost:8080/metrics  # cAdvisor
   ```
3. Verify firewall allows access from server 84: `sudo ufw status`
4. Check Prometheus targets on server 84: http://10.0.0.84:9090/targets
5. Look for `node-exporter-82` and `cadvisor-82` targets - they should show as "UP"

### Container resource limits exceeded

If a container is killed due to OOM (Out Of Memory):
1. Check logs: `docker compose logs <service-name>`
2. Review resource usage: `docker stats`
3. If needed, increase limits in `docker-compose.yml` and redeploy

## Server Information

- **IP**: 10.0.0.82
- **OS**: Ubuntu 24.04.3 LTS
- **Hostname**: hpr
- **Docker**: 29.1.3
- **Docker Compose**: v5.0.0

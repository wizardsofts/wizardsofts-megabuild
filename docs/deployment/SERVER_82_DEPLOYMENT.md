# Server 82 (10.0.0.82) Deployment Guide

## Server Information

- **IP Address**: 10.0.0.82
- **Hostname**: hpr
- **OS**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: 6.8.0-90-generic
- **Docker**: 29.1.3
- **Docker Compose**: v5.0.0
- **User**: wizardsofts
- **SSH Port**: 22

## Deployment Date

- **Initial Setup**: 2025-12-31

## Security Hardening

### Firewall (UFW)

The server is protected by UFW firewall with the following configuration:

```bash
Default: deny (incoming), allow (outgoing)
Status: active
```

#### Allowed Ports (Local Network Only - 10.0.0.0/24)

| Port | Protocol | Service       | Description                   |
| ---- | -------- | ------------- | ----------------------------- |
| 22   | TCP      | SSH           | SSH access from local network |
| 3000 | TCP      | Grafana       | Grafana web interface         |
| 8080 | TCP      | cAdvisor      | Container metrics             |
| 9100 | TCP      | Node Exporter | System metrics                |
| 9090 | TCP      | Prometheus    | Prometheus (if enabled)       |

**All access is restricted to the local network (10.0.0.0/24)**. External access is blocked.

### Security Best Practices Applied

1. ✅ Firewall enabled with default deny incoming
2. ✅ Access restricted to local network only
3. ✅ Docker containers run with `no-new-privileges:true`
4. ✅ Grafana runs as non-root user (472:472)
5. ✅ Anonymous access disabled in Grafana
6. ✅ User sign-up disabled in Grafana

## Installed Services

### Docker Containers

All services are managed via Docker Compose at `~/server-82/docker-compose.yml`

#### 1. Node Exporter (node-exporter-82)

- **Image**: `prom/node-exporter:latest`
- **Port**: 9100
- **Purpose**: Exposes system metrics (CPU, memory, disk, network)
- **Health**: No health check (stateless exporter)

#### 2. cAdvisor (cadvisor-82)

- **Image**: `gcr.io/cadvisor/cadvisor:latest`
- **Port**: 8080
- **Purpose**: Container metrics and resource usage
- **Health**: Built-in health check

#### 3. Grafana (grafana-82)

- **Image**: `grafana/grafana:latest`
- **Port**: 3000
- **Purpose**: Metrics visualization and dashboards
- **Health**: HTTP health check on `/api/health`
- **Data Volume**: `grafana-data` (persistent)

### Service Management

```bash
# Start all services
cd ~/server-82
docker compose up -d

# Stop all services
docker compose down

# Restart a specific service
docker compose restart grafana

# View logs
docker compose logs -f grafana
docker compose logs -f node-exporter
docker compose logs -f cadvisor

# Check status
docker ps
```

## Monitoring Integration

### Prometheus Configuration

Server 82 metrics are scraped by the central Prometheus instance on server 84 (10.0.0.84:9090).

The following scrape jobs were added to `infrastructure/monitoring/prometheus/prometheus.yml`:

```yaml
# Server 82 (HPR Server)
- job_name: "node-exporter-82"
  static_configs:
    - targets: ["10.0.0.82:9100"]
      labels:
        instance: "server-82"
        server: "hpr-server"
        environment: "production"

# cAdvisor - Server 82
- job_name: "cadvisor-82"
  static_configs:
    - targets: ["10.0.0.82:8080"]
      labels:
        instance: "server-82"
```

### Grafana Configuration

#### Default Credentials

- **Username**: `admin`
- **Password**: `admin` (default, should be changed)

#### Data Source

- **Prometheus**: Auto-provisioned to connect to `http://10.0.0.84:9090`

#### Pre-loaded Dashboards

- **Server 82 - System Metrics**: Displays CPU, memory, disk, network, system load, and disk I/O

#### Accessing Grafana

From any machine on the local network:

```
http://10.0.0.82:3000
```

## Verification Steps

### 1. Check Docker Containers

```bash
ssh wizardsofts@10.0.0.82
docker ps
```

Expected output: 3 running containers (node-exporter-82, cadvisor-82, grafana-82)

### 2. Check Metrics Endpoints

```bash
# Node Exporter
curl http://10.0.0.82:9100/metrics | head

# cAdvisor
curl http://10.0.0.82:8080/metrics | head

# Grafana Health
curl http://10.0.0.82:3000/api/health
```

### 3. Check Firewall Status

```bash
ssh wizardsofts@10.0.0.82
sudo ufw status verbose
```

### 4. Verify Prometheus Scraping

On server 84, check Prometheus targets:

```
http://10.0.0.84:9090/targets
```

Look for:

- `node-exporter-82` (up)
- `cadvisor-82` (up)

## Troubleshooting

### Container Permission Issues

If Grafana fails to start with permission denied errors:

```bash
ssh wizardsofts@10.0.0.82
cd ~/server-82
sudo chown -R 472:472 grafana/provisioning
docker compose restart grafana
```

### Firewall Blocking Access

If unable to access services from local network:

```bash
ssh wizardsofts@10.0.0.82
sudo ufw status
sudo ufw allow from 10.0.0.0/24 to any port <PORT>
```

### Grafana Not Loading Dashboards

Check provisioning logs:

```bash
docker logs grafana-82 | grep provisioning
```

Verify file permissions:

```bash
ls -la ~/server-82/grafana/provisioning
```

### Metrics Not Appearing in Prometheus

1. Check target status in Prometheus UI
2. Verify network connectivity from server 84 to server 82:
   ```bash
   # On server 84
   curl http://10.0.0.82:9100/metrics
   ```
3. Check Prometheus configuration reload:
   ```bash
   # On server 84
   docker exec prometheus kill -HUP 1
   ```

## Maintenance

### Update Docker Images

```bash
ssh wizardsofts@10.0.0.82
cd ~/server-82
docker compose pull
docker compose up -d
```

### Backup Grafana Data

```bash
ssh wizardsofts@10.0.0.82
docker run --rm -v server-82_grafana-data:/data -v $(pwd):/backup ubuntu tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Grafana Data

```bash
ssh wizardsofts@10.0.0.82
docker compose down
docker run --rm -v server-82_grafana-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/grafana-backup-YYYYMMDD.tar.gz -C /
docker compose up -d
```

## Future Improvements

1. **Security Metrics**: Add security metrics exporter (port 9101) similar to servers 80, 81, 84
2. **Local Prometheus**: Consider running a local Prometheus instance for redundancy
3. **Alerting**: Configure Prometheus alert rules for critical metrics
4. **SSL/TLS**: Add TLS encryption for Grafana if exposed beyond local network
5. **Backup Automation**: Implement automated backup script for Grafana data

## Related Documentation

- [Server 82 Monitoring Stack README](../infrastructure/server-82/README.md)
- [Prometheus Configuration](../infrastructure/monitoring/prometheus/prometheus.yml)
- [Appwrite Deployment](./APPWRITE_DEPLOYMENT.md)
- [Security Improvements Changelog](./SECURITY_IMPROVEMENTS_CHANGELOG.md)

## Change Log

| Date       | Change                                                 | Author      |
| ---------- | ------------------------------------------------------ | ----------- |
| 2025-12-31 | Initial deployment: Docker, firewall, monitoring stack | Claude Code |
| 2025-12-31 | Fixed Grafana provisioning permissions                 | Claude Code |
| 2025-12-31 | Added to central Prometheus monitoring                 | Claude Code |

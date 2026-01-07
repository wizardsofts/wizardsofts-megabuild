# Server 80 Security Monitoring

This document describes the security monitoring infrastructure deployed on Server 80 (10.0.0.80).

## Overview

Server 80 has comprehensive security monitoring that includes:
- Malware scanning (ClamAV)
- Docker image vulnerability scanning (Trivy)
- Container security best practices (Dockle)
- Intrusion detection (failed logins, suspicious processes)
- File integrity monitoring (SUID, world-writable files)
- Docker daemon security checks

## Components

### Security Scanner

**Location:** `/mnt/data/security/security_scanner.sh`

The security scanner performs two types of scans:

#### Quick Scan (runs every 15 minutes)
- Failed SSH login attempts monitoring
- Open ports enumeration
- Suspicious process detection (crypto miners, reverse shells)
- File permission auditing
- Docker security configuration checks

#### Full Scan (runs daily at 4 AM)
- All quick scan checks
- Docker image vulnerability scanning with Trivy
- Container best practices audit with Dockle
- Malware scanning with ClamAV

### Metrics Exporter

**Location:** `/mnt/data/security/metrics_server.py`
**Port:** 9101
**Endpoint:** `http://10.0.0.80:9101/metrics`

The metrics exporter serves Prometheus-compatible metrics for Grafana visualization.

### Docker Services

```bash
# Start security metrics server
cd ~
docker compose -f docker-compose.security.yml up -d
```

## Metrics

| Metric | Description |
|--------|-------------|
| `security_scan_timestamp` | Unix timestamp of last scan |
| `security_scan_status` | 1=success, 0=failed |
| `security_docker_vulnerabilities{severity}` | CVE counts by severity |
| `security_malware_detected` | Number of infected files |
| `security_failed_logins{type}` | Failed login attempts |
| `security_open_ports{type}` | Open port counts |
| `security_suspicious_processes{type}` | Suspicious process counts |
| `security_world_writable_files` | World-writable file count |
| `security_suid_files` | SUID file count |
| `security_docker_config{check}` | Docker security checks |
| `security_container_issues` | Container configuration issues |

## Grafana Dashboard

**URL:** `http://10.0.0.84:3002/d/security-overview-80/server-80-security-dashboard`

The dashboard displays:
- Security status overview (SECURE/ALERT)
- Critical and high vulnerability counts
- Malware detection status
- Failed login trends
- Open port monitoring
- Docker security configuration
- Suspicious activity monitoring

## Crontab Schedule

```cron
# Quick security scan every 15 minutes
*/15 * * * * /bin/bash /mnt/data/security/security_scanner.sh

# Full security scan daily at 4 AM
0 4 * * * /bin/bash /mnt/data/security/security_scanner.sh --full

# Security logs cleanup weekly
0 5 * * 0 find /mnt/data/security/logs -name '*.log' -mtime +30 -delete
```

## Directory Structure

```
/mnt/data/security/
├── security_scanner.sh    # Main scanner script
├── metrics_server.py      # Prometheus exporter
├── logs/                  # Scan logs
│   ├── security_scan.log
│   ├── full_scan.log
│   └── cron.log
├── metrics/              # Prometheus metrics
│   └── security_metrics.prom
└── reports/              # Scan reports
```

## Manual Operations

### Trigger Manual Scan

```bash
# Quick scan
/mnt/data/security/security_scanner.sh

# Full scan (includes Docker image scanning)
/mnt/data/security/security_scanner.sh --full
```

### Check Scan Logs

```bash
tail -f /mnt/data/security/logs/security_scan.log
```

### View Current Metrics

```bash
curl http://localhost:9101/metrics
```

### Restart Metrics Server

```bash
cd ~
docker compose -f docker-compose.security.yml restart
```

## Prometheus Configuration

The security metrics are scraped by Prometheus on Server 84:

```yaml
# In ~/prometheus-config/prometheus.yml on server 84
- job_name: 'security-80'
  scrape_interval: 30s
  static_configs:
    - targets: ['10.0.0.80:9101']
      labels:
        instance: 'server-80'
        type: 'security'
```

## Security Thresholds

| Check | Warning | Critical |
|-------|---------|----------|
| Critical CVEs | 1 | 5 |
| High CVEs | 5 | 20 |
| Failed Logins | 10 | 100 |
| Malware | - | 1 |
| Suspicious Processes | - | 1 |
| Privileged Containers | 1 | 3 |

## Troubleshooting

### Metrics Not Updating

1. Check if scanner is running:
   ```bash
   ps aux | grep security_scanner
   ```

2. Check metrics file:
   ```bash
   cat /mnt/data/security/metrics/security_metrics.prom
   ```

3. Check metrics server:
   ```bash
   docker ps | grep security-metrics
   docker logs security-metrics
   ```

### Trivy Scan Failures

1. Check Docker socket access:
   ```bash
   docker ps
   ```

2. Update Trivy database:
   ```bash
   docker pull aquasec/trivy:latest
   ```

### High Vulnerability Counts

1. Review specific image vulnerabilities:
   ```bash
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy:latest image IMAGE_NAME
   ```

2. Update base images to latest versions

3. Consider using distroless or alpine-based images

# WizardSofts Security Monitoring

This document describes the comprehensive security monitoring infrastructure deployed across WizardSofts servers.

## Overview

Security monitoring is deployed on the following servers:

| Server | IP | Role | Monitoring Type |
|--------|-----|------|-----------------|
| Server 80 | 10.0.0.80 | GIBD Services | Full (Docker + System) |
| Server 81 | 10.0.0.81 | Database Server | System Only (No Docker) |
| Server 84 | 10.0.0.84 | HP Production | Full (Docker + System) |

## Architecture

```
                              +-----------------+
                              |    Grafana      |
                              |  (10.0.0.84)    |
                              |   Port 3002     |
                              +--------+--------+
                                       |
                              +--------v--------+
                              |   Prometheus    |
                              |  (10.0.0.84)    |
                              |   Port 9090     |
                              +--------+--------+
                                       |
         +-----------------------------+-----------------------------+
         |                             |                             |
+--------v--------+         +----------v--------+         +----------v--------+
|   Server 80     |         |    Server 81      |         |    Server 84      |
| (GIBD Services) |         | (Database Server) |         | (HP Production)   |
+--------+--------+         +----------+--------+         +----------+--------+
         |                             |                             |
  +------+------+               +------+------+               +------+------+
  |node-exporter|               |node-exporter|               |node-exporter|
  |  (9100)     |               |  (9100)     |               |  (9100)     |
  +------+------+               +------+------+               +------+------+
         |                             |                             |
  +------+------+               +------+------+               +------+------+
  |  security   |               |  security   |               |  security   |
  |  metrics    |               |  metrics    |               |  metrics    |
  |  (9101)     |               |  (9101)     |               |  (9101)     |
  +-------------+               +-------------+               +-------------+
```

## Components

### 1. Node Exporter (All Servers)
System metrics including CPU, memory, disk, and network usage.
- **Port:** 9100
- **Metrics:** Prometheus format

### 2. fail2ban Intrusion Prevention (Server 84)
Automated intrusion prevention that bans IPs showing malicious behavior.
- **Service:** SSH protection
- **Ban Duration:** 1 hour (3600 seconds)
- **Max Retries:** 5 failed attempts in 10 minutes
- **Whitelist:** Local network (10.0.0.0/24)
- **Configuration:** `/etc/fail2ban/jail.local`
- **Documentation:** [FAIL2BAN_SETUP.md](FAIL2BAN_SETUP.md)

**Status by Server:**
| Server | Status | Notes |
|--------|--------|-------|
| Server 80 | ⏳ Pending | To be deployed |
| Server 81 | ⏳ Pending | To be deployed |
| Server 82 | ⏳ Pending | To be deployed |
| Server 84 | ✅ Active | Configured 2026-01-01 |

### 3. Security Scanner

#### Server 80 & 84 (Full Scan)
- Failed SSH login attempts monitoring
- Open ports enumeration
- Suspicious process detection (crypto miners, reverse shells)
- File permission auditing (SUID, world-writable)
- Docker security configuration checks
- Docker image vulnerability scanning (Trivy)
- Container best practices audit (Dockle)
- Malware scanning (ClamAV)

#### Server 81 (System Scan Only)
- Failed SSH login attempts monitoring
- Open ports enumeration
- Suspicious process detection
- File permission auditing
- No Docker metrics (Docker not installed)

### 4. Security Metrics Exporter
Python HTTP server serving Prometheus-compatible metrics.
- **Port:** 9101
- **Endpoint:** `/metrics`
- **Health Check:** `/health`

## Grafana Dashboards

Access via: `http://10.0.0.84:3002`

| Dashboard | UID | Description |
|-----------|-----|-------------|
| All Servers Security Overview | `security-overview-all` | Combined view of all servers |
| Server 80 Security Dashboard | `security-overview-80` | Detailed GIBD server security |
| Server 81 Security Dashboard | `security-overview-81` | Detailed database server security |
| Server 84 Security Dashboard | `security-overview-84` | Detailed HP production security |

## Metrics Reference

### Common Metrics (All Servers)

| Metric | Description |
|--------|-------------|
| `security_scan_timestamp` | Unix timestamp of last scan |
| `security_scan_status` | 1=success, 0=failed |
| `security_failed_logins{type}` | Failed login attempts by type |
| `security_open_ports{type}` | Open port counts |
| `security_suspicious_processes{type}` | Suspicious process counts |
| `security_world_writable_files` | World-writable file count |
| `security_suid_files` | SUID file count |

### Docker Metrics (Servers 80 & 84 Only)

| Metric | Description |
|--------|-------------|
| `security_docker_vulnerabilities{severity}` | CVE counts by severity |
| `security_malware_detected` | Number of infected files |
| `security_docker_config{check}` | Docker security checks |
| `security_container_issues` | Container configuration issues |

## Deployment Locations

### Server 80 (10.0.0.80)
```
/mnt/data/security/
├── security_scanner.sh
├── metrics_server.py
├── logs/
├── metrics/
└── reports/
```

### Server 81 (10.0.0.81)
```
~/monitoring/
├── bin/
│   └── node_exporter
├── security/
│   ├── security_scanner.sh
│   ├── metrics_server.py
│   ├── logs/
│   └── metrics/
├── logs/
└── start_monitoring.sh
```

### Server 84 (10.0.0.84)
```
~/security/
├── security_scanner.sh
├── metrics_server.py
├── logs/
├── metrics/
└── reports/
```

## Cron Schedules

### Quick Security Scan (Every 15 minutes)
```cron
*/15 * * * * /path/to/security_scanner.sh
```

### Full Security Scan (Daily at 4 AM) - Servers 80 & 84 only
```cron
0 4 * * * /path/to/security_scanner.sh --full
```

### Metrics Server Health Check (Every 5 minutes)
```cron
*/5 * * * * pgrep -f 'metrics_server.py' || nohup python3 /path/to/metrics_server.py
```

### Log Cleanup (Weekly)
```cron
0 5 * * 0 find /path/to/logs -name '*.log' -mtime +30 -delete
```

## Security Thresholds

| Check | Warning | Critical | Action |
|-------|---------|----------|--------|
| Critical CVEs | 1 | 5 | Update images immediately |
| High CVEs | 5 | 20 | Schedule updates |
| Failed Logins | 10 | 100 | Review logs (fail2ban auto-bans) |
| Malware | - | 1 | Quarantine and investigate |
| Suspicious Processes | - | 1 | Kill process and investigate |
| Privileged Containers | 1 | 3 | Review necessity |
| fail2ban Banned IPs | - | - | Auto-handled, monitor logs |

**Note:** With fail2ban enabled on Server 84, failed login attempts exceeding the threshold (5 in 10 minutes) will result in automatic IP bans for 1 hour. The security scanner will continue to report cumulative failed attempts, but active threats are mitigated by fail2ban.

## Manual Operations

### Security Scanner

#### Trigger Manual Scan
```bash
# Quick scan
/path/to/security_scanner.sh

# Full scan (servers 80 & 84)
/path/to/security_scanner.sh --full
```

#### View Current Metrics
```bash
curl http://localhost:9101/metrics
```

#### Check Scan Logs
```bash
tail -f /path/to/logs/security_scan.log
```

#### Restart Metrics Server
```bash
# Find and kill existing process
pkill -f metrics_server.py

# Start new instance
nohup python3 /path/to/metrics_server.py > /path/to/logs/metrics_server.log 2>&1 &
```

### fail2ban Operations (Server 84)

#### Check Status
```bash
# Overall status
sudo fail2ban-client status

# SSH jail status
sudo fail2ban-client status sshd
```

#### Manage Banned IPs
```bash
# List currently banned IPs
sudo fail2ban-client status sshd | grep "Banned IP list"

# Unban specific IP
sudo fail2ban-client set sshd unbanip 10.0.0.12

# Unban all IPs
sudo fail2ban-client unban --all
```

#### View Logs
```bash
# Real-time fail2ban logs
sudo tail -f /var/log/fail2ban.log

# Recent bans
sudo grep "Ban" /var/log/fail2ban.log | tail -20
```

#### Reload Configuration
```bash
# After editing /etc/fail2ban/jail.local
sudo fail2ban-client reload
```

## Troubleshooting

### Metrics Not Updating

1. Check if scanner is running:
   ```bash
   ps aux | grep security_scanner
   ```

2. Check metrics file:
   ```bash
   cat /path/to/metrics/security_metrics.prom
   ```

3. Check metrics server:
   ```bash
   ps aux | grep metrics_server
   curl http://localhost:9101/health
   ```

### Prometheus Target Down

1. Verify service is running on target server
2. Check firewall rules allow port 9100/9101
3. Test connectivity:
   ```bash
   curl http://<target-ip>:9101/metrics
   ```

### Server 81 Firewall Note

Server 81 has UFW firewall enabled. To allow Prometheus scraping, an administrator needs to run:
```bash
sudo ufw allow from 10.0.0.84 to any port 9100
sudo ufw allow from 10.0.0.84 to any port 9101
```

### High Vulnerability Counts

1. Review specific image vulnerabilities:
   ```bash
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy:latest image IMAGE_NAME
   ```

2. Update base images to latest versions

3. Consider using distroless or alpine-based images

## Prometheus Configuration

Located at: `~/prometheus-config/prometheus.yml` on Server 84

```yaml
scrape_configs:
  # Node exporters
  - job_name: 'node-exporter-80'
    targets: ['10.0.0.80:9100']
  - job_name: 'node-exporter-81'
    targets: ['10.0.0.81:9100']
  - job_name: 'node-exporter-84'
    targets: ['node-exporter:9100']

  # Security metrics
  - job_name: 'security-80'
    targets: ['10.0.0.80:9101']
  - job_name: 'security-81'
    targets: ['10.0.0.81:9101']
  - job_name: 'security-84'
    targets: ['10.0.0.84:9101']
```

## SSH Hardening (Server 84)

Following security best practices, Server 84 has been hardened with:

1. **Password Authentication Disabled** - SSH keys required
2. **Root Login Disabled** - Must use sudo from regular user
3. **fail2ban Active** - Automatic IP banning for repeated failures

**Configuration File:** `/etc/ssh/sshd_config`

```bash
# Verify SSH hardening
ssh wizardsofts@10.0.0.84 "grep -E '^(PasswordAuthentication|PermitRootLogin|PubkeyAuthentication)' /etc/ssh/sshd_config"
```

**Expected Output:**
```
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
```

## Related Documentation

- [fail2ban Setup Guide](FAIL2BAN_SETUP.md) - Complete fail2ban configuration and usage
- [Server 80 Security Monitoring](SERVER_80_SECURITY_MONITORING.md) - Original detailed documentation
- [Security Improvements Changelog](SECURITY_IMPROVEMENTS_CHANGELOG.md) - Historical security changes
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [fail2ban Documentation](https://www.fail2ban.org/)

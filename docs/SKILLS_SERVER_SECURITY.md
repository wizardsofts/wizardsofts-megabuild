# Server Security Skill - User-Level Claude Code Skill

**Skill Type:** User-level
**Storage Location:** `~/.claude/skills/server-security/`
**Trigger phrases:** "security", "fail2ban", "firewall", "ufw", "ssh hardening", "port security", "intrusion detection", "banned ips", "security scan"

---

## Overview

This skill provides comprehensive server security management for WizardSofts infrastructure, covering intrusion prevention (fail2ban), SSH hardening, firewall configuration, port security enforcement, and automated security scanning across all servers.

---

## What This Skill Has

### fail2ban Intrusion Prevention

**Automated IP Banning:**
- SSH brute-force protection
- Configurable ban duration (default: 1 hour)
- Configurable max retries (default: 5 attempts in 10 minutes)
- Local network whitelist (10.0.0.0/24)
- Prometheus exporter for monitoring (port 9191)

**Deployment Status:**
| Server | Status | Configuration | Notes |
|--------|--------|---------------|-------|
| Server 80 | ⏳ Pending | N/A | To be deployed |
| Server 81 | ⏳ Pending | N/A | To be deployed |
| Server 82 | ⏳ Pending | N/A | To be deployed |
| Server 84 | ✅ Active | SSH protection | Production server |

**Configuration Files:**
- `/etc/fail2ban/jail.local` - Main configuration
- `/var/log/fail2ban.log` - Ban activity logs
- `~/fail2ban-exporter/docker-compose.yml` - Prometheus exporter

### SSH Hardening

**Security Measures:**
- Password authentication DISABLED (key-only access)
- Root login DISABLED (must use sudo)
- Public key authentication ENFORCED
- Automated sshd_config backup before changes

**Configuration Management:**
- Backup location: `/etc/ssh/sshd_config.backup.YYYYMMDD_HHMMSS`
- Restoration capability
- Verification checks post-deployment

### Port Security Architecture

**Before Security Implementation (Insecure):**
- 14 exposed ports directly to internet
- Databases accessible from internet (5433, 6379)
- No SSL/HTTPS
- No rate limiting
- No authentication on admin interfaces

**After Security Implementation (Secure):**
- 3 controlled entry points (80, 443, 8090)
- Databases localhost-only (`127.0.0.1:5433:5432`)
- Automatic SSL/TLS via Let's Encrypt
- Rate limiting (100 req/s average, 50 burst)
- Basic authentication on admin interfaces

**Port Binding Strategy:**
```yaml
# ✅ SECURE - Database bound to localhost only
postgres:
  ports:
    - "127.0.0.1:5433:5432"

# ✅ SECURE - Redis bound to localhost only
redis:
  ports:
    - "127.0.0.1:6379:6379"

# ❌ INSECURE - Database exposed to internet
postgres:
  ports:
    - "5433:5432"  # Anyone can connect!
```

### Security Monitoring Infrastructure

**Node Exporter (All Servers):**
- Port: 9100
- Metrics: CPU, memory, disk, network
- Format: Prometheus

**Security Scanner (Servers 80 & 84):**
- Failed SSH login attempts monitoring
- Open ports enumeration
- Suspicious process detection (crypto miners, reverse shells)
- File permission auditing (SUID, world-writable files)
- Docker security configuration checks
- Container image vulnerability scanning (Trivy)
- Container best practices audit (Dockle)
- Malware scanning (ClamAV)

**Security Scanner (Server 81 - System Only):**
- Failed SSH login attempts monitoring
- Open ports enumeration
- Suspicious process detection
- File permission auditing
- No Docker metrics (Docker not installed)

**Security Metrics Exporter:**
- Port: 9101
- Endpoint: `/metrics`
- Health check: `/health`

**Grafana Dashboards:**
- Security Overview - All Servers (combined view)
- Server 80 Security Dashboard (detailed)
- Server 81 Security Dashboard (detailed)
- Server 84 Security Dashboard (detailed)

### UFW Firewall Configuration

**Network Strategy:**
- **Local network access** (10.0.0.0/24) - Allowed for distributed services
- **External internet** - BLOCKED for internal services
- **Traefik only** - Exposes to public (0.0.0.0 on ports 80, 443)

**Rationale:**
- Distributed infrastructure (Ray, Celery, distributed ML) requires cross-server access
- UFW firewall prevents external internet access
- Maintains security while enabling internal communication

---

## What This Skill Will Do

### 1. fail2ban Management

**Deploy fail2ban to Server:**
```bash
# 1. Copy setup script to target server
scp scripts/setup-fail2ban-server84.sh wizardsofts@<SERVER_IP>:~/

# 2. SSH into server
ssh wizardsofts@<SERVER_IP>

# 3. Run setup script
sudo bash setup-fail2ban-server84.sh

# The script will:
# - Install fail2ban
# - Create /etc/fail2ban/jail.local with WizardSofts config
# - Disable SSH password authentication
# - Disable root SSH login
# - Deploy fail2ban Prometheus exporter (Docker)
# - Update Prometheus configuration
# - Restart services
# - Verify installation
```

**Check Banned IPs:**
```bash
# Show all jails
sudo fail2ban-client status

# Show sshd jail with banned IPs
sudo fail2ban-client status sshd

# View recent ban activity
sudo grep 'Ban' /var/log/fail2ban.log | tail -20
```

**Unban IP Address:**
```bash
# Unban specific IP
sudo fail2ban-client set sshd unbanip <IP_ADDRESS>

# Unban all IPs
sudo fail2ban-client unban --all
```

**Monitor fail2ban Metrics:**
```bash
# Check Prometheus exporter
curl http://localhost:9191/metrics

# View in Grafana
# Navigate to http://10.0.0.84:3002
# Dashboard: Security Overview - All Servers
# Panel: fail2ban Banned IPs
```

**Adjust fail2ban Configuration:**
```bash
# Edit configuration
sudo nano /etc/fail2ban/jail.local

# Example: Increase ban time to 24 hours
[sshd]
bantime = 86400    # 24 hours
findtime = 300     # 5 minutes
maxretry = 3       # 3 attempts only

# Restart fail2ban
sudo systemctl restart fail2ban

# Verify changes
sudo fail2ban-client status sshd
```

### 2. SSH Security Hardening

**Harden SSH Configuration:**
```bash
# Backup current configuration
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# Disable password authentication
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Disable root login
sudo sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Ensure public key authentication is enabled
sudo sed -i 's/^#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Verify changes
grep -E "^(PasswordAuthentication|PermitRootLogin|PubkeyAuthentication)" /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart sshd
```

**Restore SSH Configuration:**
```bash
# Find backup
ls -lah /etc/ssh/sshd_config.backup.*

# Restore from backup
sudo cp /etc/ssh/sshd_config.backup.20260103_120000 /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd
```

**Test SSH Key Authentication:**
```bash
# From local machine
ssh -i ~/.ssh/id_rsa wizardsofts@10.0.0.84

# Should connect without password
# If prompted for password, key authentication failed
```

### 3. Firewall Configuration (UFW)

**Configure UFW for Local Network Access:**
```bash
# Allow SSH from anywhere (required for remote access)
sudo ufw allow 22/tcp

# Allow local network access to Node Exporter
sudo ufw allow from 10.0.0.0/24 to any port 9100 proto tcp

# Allow local network access to Security Metrics
sudo ufw allow from 10.0.0.0/24 to any port 9101 proto tcp

# Allow local network access to fail2ban exporter
sudo ufw allow from 10.0.0.0/24 to any port 9191 proto tcp

# Block external internet access to these ports
sudo ufw deny 9100/tcp
sudo ufw deny 9101/tcp
sudo ufw deny 9191/tcp

# Enable UFW
sudo ufw enable

# Verify rules
sudo ufw status verbose
```

**Allow Traefik Public Access:**
```bash
# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Allow Traefik dashboard (localhost only - already restricted by Traefik)
sudo ufw allow 8090/tcp
```

**Check Firewall Status:**
```bash
# Show all rules
sudo ufw status numbered

# Check if port is allowed
sudo ufw status | grep 9100

# Show listening ports
sudo netstat -tlnp
```

### 4. Security Scanning

**Run Quick Security Scan (15 minutes interval):**
```bash
# SSH into target server
ssh wizardsofts@<SERVER_IP>

# Run security scanner
sudo /mnt/data/security/security_scanner.sh  # Server 80
sudo ~/security/security_scanner.sh          # Server 84
sudo ~/monitoring/security/security_scanner.sh  # Server 81

# View results
cat /mnt/data/security/logs/security_scan.log  # Server 80
cat ~/security/logs/security_scan.log          # Server 84
cat ~/monitoring/security/logs/security_scan.log  # Server 81
```

**Run Full Security Scan (Daily at 4 AM - Servers 80 & 84 only):**
```bash
# Run full scan manually
sudo /mnt/data/security/security_scanner.sh --full  # Server 80
sudo ~/security/security_scanner.sh --full          # Server 84

# Full scan includes:
# - Failed SSH login attempts
# - Open ports enumeration
# - Suspicious process detection
# - File permission auditing
# - Docker security checks
# - Trivy CVE scanning (all images)
# - Dockle container best practices
# - ClamAV malware scan
```

**Check Security Metrics:**
```bash
# View metrics locally
curl http://localhost:9101/metrics

# View in Grafana
# Navigate to http://10.0.0.84:3002
# Dashboard: Server XX Security Dashboard
# Panels:
#   - Failed Login Attempts
#   - Open Ports
#   - Suspicious Processes
#   - Docker Vulnerabilities (Critical/High/Medium/Low)
#   - Malware Detected
#   - Security Scan Status
```

**Security Scan Thresholds:**
| Check | Warning | Critical | Action |
|-------|---------|----------|--------|
| Critical CVEs | 1 | 5 | Update images immediately |
| High CVEs | 5 | 20 | Schedule updates |
| Failed Logins | 10 | 100 | Review logs (fail2ban auto-bans) |
| Malware | - | 1 | Quarantine and investigate |
| Suspicious Processes | - | 1 | Kill process and investigate |
| Privileged Containers | 1 | 3 | Review necessity |

### 5. Port Security Enforcement

**Validate docker-compose.yml for Insecure Port Bindings:**
```bash
# Scan docker-compose.yml for insecure bindings
grep -E "^\s+- \"[0-9]+:[0-9]+\"" docker-compose.yml

# Expected output:
# - "5433:5432"  # ❌ INSECURE - Database exposed
# - "6379:6379"  # ❌ INSECURE - Redis exposed
```

**Auto-Fix Insecure Port Bindings:**
```bash
# Fix PostgreSQL port binding
sed -i 's/- "5433:5432"/- "127.0.0.1:5433:5432"/' docker-compose.yml

# Fix Redis port binding
sed -i 's/- "6379:6379"/- "127.0.0.1:6379:6379"/' docker-compose.yml

# Verify changes
grep -E "^\s+- \"127.0.0.1:[0-9]+:[0-9]+\"" docker-compose.yml

# Expected output:
# - "127.0.0.1:5433:5432"  # ✅ SECURE - Localhost only
# - "127.0.0.1:6379:6379"  # ✅ SECURE - Localhost only
```

**Validate Port Security:**
```bash
# Check what's listening on public IP
netstat -tlnp | grep -E ":(5433|6379|5432|8761|8080)"

# Should show:
# 127.0.0.1:5433  # ✅ Localhost only
# 127.0.0.1:6379  # ✅ Localhost only

# Should NOT show:
# 0.0.0.0:5433    # ❌ Exposed to internet
# 0.0.0.0:6379    # ❌ Exposed to internet
```

**Verify Traefik Network Connections:**
```bash
# Check Traefik networks
docker network inspect microservices-overlay | grep -A 5 "traefik"

# Traefik MUST be connected to ALL backend networks:
# - traefik-public (for external access)
# - microservices-overlay (for web apps)
# - gibd-network (for GIBD services)
# - mailcow-network (for Mailcow)

# Add missing network
docker network connect microservices-overlay traefik
```

### 6. Security Monitoring

**Access Grafana Dashboards:**
```
URL: http://10.0.0.84:3002
Username: admin
Password: [from .env or Keycloak OAuth]

Dashboards:
- Security Overview - All Servers (UID: security-overview-all)
- Server 80 Security Dashboard (UID: security-overview-80)
- Server 81 Security Dashboard (UID: security-overview-81)
- Server 84 Security Dashboard (UID: security-overview-84)
```

**View Prometheus Security Alerts:**
```bash
# Check active alerts
curl http://10.0.0.84:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.severity=="critical")'

# Security alerts include:
# - HighFailedLoginAttempts (>100 in 5 min)
# - CriticalDockerVulnerabilities (>5 CVEs)
# - MalwareDetected (>0 files)
# - SuspiciousProcessDetected
# - HighRateLimitRejections (DDoS)
```

**Review Security Scan Logs:**
```bash
# View recent security scan results
tail -100 /mnt/data/security/logs/security_scan.log  # Server 80
tail -100 ~/security/logs/security_scan.log          # Server 84
tail -100 ~/monitoring/security/logs/security_scan.log  # Server 81

# View specific security check
grep "Failed login attempts" /mnt/data/security/logs/security_scan.log

# View malware scan results
grep "ClamAV" ~/security/logs/security_scan.log
```

---

## Example Usage

### Example 1: Deploy fail2ban to Server 80

**User Request:**
```
User: "Deploy fail2ban to server 80"
```

**Skill Actions:**
```bash
# 1. Copy and adapt setup script for server 80
scp scripts/setup-fail2ban-server84.sh wizardsofts@10.0.0.80:~/
ssh wizardsofts@10.0.0.80

# 2. Adapt script for server 80 (change Prometheus config path if needed)
nano ~/setup-fail2ban-server84.sh
# Update PROMETHEUS_CONFIG path if different

# 3. Run setup script
sudo bash ~/setup-fail2ban-server84.sh

# Output:
# [1/6] Installing fail2ban...
# [2/6] Enabling fail2ban service...
# [3/6] Creating /etc/fail2ban/jail.local...
# [4/6] Disabling SSH password authentication...
# [5/8] Deploying fail2ban Prometheus exporter...
# [6/8] Restarting SSH and fail2ban services...
# [7/8] Updating Prometheus configuration...
# [8/8] Verifying installation...
# ✓ fail2ban is running
# ✓ SSH password authentication disabled
# ✓ SSH root login disabled
# ✓ fail2ban Prometheus exporter is running

# 4. Verify fail2ban status
sudo fail2ban-client status sshd

# 5. Check Prometheus exporter
curl http://localhost:9191/metrics | grep fail2ban

# 6. Verify in Grafana
# Navigate to Security Overview dashboard
# Confirm server 80 fail2ban metrics appearing
```

### Example 2: Check Which IPs Are Banned

**User Request:**
```
User: "Check which IPs are banned on server 84"
```

**Skill Actions:**
```bash
# 1. SSH into server 84
ssh wizardsofts@10.0.0.84

# 2. Check fail2ban status
sudo fail2ban-client status

# Output:
# Status
# |- Number of jail:      1
# `- Jail list:   sshd

# 3. Check sshd jail specifically
sudo fail2ban-client status sshd

# Output:
# Status for the jail: sshd
# |- Filter
# |  |- Currently failed: 2
# |  |- Total failed:     127
# |  `- File list:        /var/log/auth.log
# `- Actions
#    |- Currently banned: 3
#    |- Total banned:     45
#    `- Banned IP list:   192.168.1.100 203.0.113.45 198.51.100.22

# 4. Show ban timestamps
sudo grep "Ban" /var/log/fail2ban.log | tail -10

# Output:
# 2026-01-03 10:15:23,456 fail2ban.actions [12345]: NOTICE [sshd] Ban 192.168.1.100
# 2026-01-03 10:30:15,789 fail2ban.actions [12345]: NOTICE [sshd] Ban 203.0.113.45
# 2026-01-03 11:45:02,123 fail2ban.actions [12345]: NOTICE [sshd] Ban 198.51.100.22

# 5. Provide summary
echo "Currently banned IPs: 3"
echo "  - 192.168.1.100 (banned 10:15 AM)"
echo "  - 203.0.113.45 (banned 10:30 AM)"
echo "  - 198.51.100.22 (banned 11:45 AM)"
echo "Ban duration: 1 hour (3600 seconds)"
echo "Will auto-unban after expiration"
```

### Example 3: Fix Insecure Port Bindings

**User Request:**
```
User: "This docker-compose.yml has insecure port bindings"
```

**Skill Actions:**
```bash
# 1. Scan for insecure port bindings
grep -n -E "^\s+- \"[0-9]+:[0-9]+\"" docker-compose.yml

# Output:
# 18:      - "5433:5432"  # PostgreSQL
# 24:      - "6379:6379"  # Redis
# 35:      - "8761:8761"  # Eureka

# 2. Identify which services should be localhost-only
# ✅ Databases (PostgreSQL, Redis) - MUST be localhost
# ❌ Admin interfaces (Eureka) - Should be behind Traefik OR localhost
# ✅ Public services - Only via Traefik (no direct port exposure)

# 3. Auto-fix database port bindings
echo "Fixing PostgreSQL port binding..."
sed -i 's/- "5433:5432"/- "127.0.0.1:5433:5432"/' docker-compose.yml

echo "Fixing Redis port binding..."
sed -i 's/- "6379:6379"/- "127.0.0.1:6379:6379"/' docker-compose.yml

# 4. Verify changes
echo "Verifying changes..."
grep -n -E "^\s+- \"127.0.0.1:[0-9]+:[0-9]+\"" docker-compose.yml

# Output:
# 18:      - "127.0.0.1:5433:5432"  # ✅ PostgreSQL secured
# 24:      - "127.0.0.1:6379:6379"  # ✅ Redis secured

# 5. Validate docker-compose syntax
docker compose config > /dev/null
echo "✓ docker-compose.yml syntax valid"

# 6. Recreate containers with new port bindings
docker compose down
docker compose up -d

# 7. Verify services are accessible only from localhost
echo "Testing port accessibility..."
netstat -tlnp | grep -E ":(5433|6379)"

# Output should show:
# tcp  0  0  127.0.0.1:5433  0.0.0.0:*  LISTEN  12345/docker-proxy
# tcp  0  0  127.0.0.1:6379  0.0.0.0:*  LISTEN  12346/docker-proxy

# 8. Test connectivity
echo "Testing database connection from localhost..."
psql -h localhost -p 5433 -U postgres -c "SELECT 1;" && echo "✓ Database accessible from localhost"

echo "Testing Redis connection from localhost..."
redis-cli -h localhost -p 6379 ping && echo "✓ Redis accessible from localhost"

# 9. Provide security summary
cat <<EOF
Security Fix Summary:
=====================
✅ PostgreSQL now bound to 127.0.0.1:5433 (localhost only)
✅ Redis now bound to 127.0.0.1:6379 (localhost only)
⚠️  Eureka still exposed on 0.0.0.0:8761 (consider adding to Traefik)

Attack Surface Reduction:
- Before: Database accessible from internet
- After: Database accessible ONLY from localhost
- Security Impact: Prevents remote database attacks

Next Steps:
1. Consider adding Eureka dashboard to Traefik with authentication
2. Review other services for port security
3. Update firewall rules if needed
EOF
```

### Example 4: Investigate Suspicious Process

**User Request:**
```
User: "Security scan detected a suspicious process on server 84"
```

**Skill Actions:**
```bash
# 1. SSH into server 84
ssh wizardsofts@10.0.0.84

# 2. Check security scan results
cat ~/security/metrics/security_metrics.prom | grep suspicious

# Output:
# security_suspicious_processes{type="crypto_miner"} 1

# 3. View detailed scan log
grep -A 5 "Suspicious process" ~/security/logs/security_scan.log

# Output:
# Suspicious process detected: xmrig (PID 12345)
# User: www-data
# Command: ./xmrig --url pool.minexmr.com:4444

# 4. Get detailed process information
ps aux | grep 12345

# 5. Check process network connections
sudo netstat -antp | grep 12345

# Output:
# tcp  0  0  10.0.0.84:52341  104.18.32.44:4444  ESTABLISHED  12345/xmrig

# 6. Kill the suspicious process
sudo kill -9 12345
echo "✓ Process 12345 killed"

# 7. Find how it was launched
sudo find / -name xmrig 2>/dev/null

# Output:
# /tmp/xmrig
# /var/www/.local/bin/xmrig

# 8. Remove malicious files
sudo rm -f /tmp/xmrig /var/www/.local/bin/xmrig
echo "✓ Malicious files removed"

# 9. Check for persistence mechanisms
sudo crontab -l -u www-data
sudo systemctl list-units --type=service | grep xmrig
sudo find /etc/systemd/system -name "*xmrig*"

# 10. Run full malware scan
sudo clamscan -r /var/www /tmp /home --infected --remove

# 11. Update security scan
sudo ~/security/security_scanner.sh

# 12. Verify clean
cat ~/security/metrics/security_metrics.prom | grep suspicious

# Output:
# security_suspicious_processes{type="crypto_miner"} 0

# 13. Incident report
cat <<EOF
Security Incident Report
========================
Date: $(date)
Server: 10.0.0.84
Incident: Cryptocurrency miner detected

Details:
- Process: xmrig (PID 12345)
- User: www-data
- Mining pool: pool.minexmr.com:4444
- Location: /tmp/xmrig, /var/www/.local/bin/xmrig

Actions Taken:
1. Process killed (PID 12345)
2. Malicious files removed
3. Full system malware scan completed
4. No persistence mechanisms found
5. System verified clean

Recommendations:
1. Review www-data user permissions
2. Audit web application for vulnerabilities
3. Update all software packages
4. Consider WAF (Web Application Firewall)
5. Enable more aggressive security scanning

Status: RESOLVED
EOF
```

---

## Related Skills

- **DevOps Skill** - For coordinating security deployments
- **Database Admin Skill** - For securing database access

---

## Configuration Files

**fail2ban:**
- `/etc/fail2ban/jail.local` - Main configuration
- `/var/log/fail2ban.log` - Activity logs
- `~/fail2ban-exporter/docker-compose.yml` - Prometheus exporter

**SSH:**
- `/etc/ssh/sshd_config` - SSH daemon configuration
- `/etc/ssh/sshd_config.backup.*` - Automatic backups

**Security Scanning:**
- Server 80: `/mnt/data/security/security_scanner.sh`
- Server 81: `~/monitoring/security/security_scanner.sh`
- Server 84: `~/security/security_scanner.sh`

**Metrics:**
- Server 80: `/mnt/data/security/metrics_server.py`
- Server 81: `~/monitoring/security/metrics_server.py`
- Server 84: `~/security/metrics_server.py`

**Documentation:**
- `docs/FAIL2BAN_SETUP.md` - fail2ban deployment guide
- `docs/SECURITY_MONITORING.md` - Monitoring infrastructure
- `docs/PORT_SECURITY_IMPLEMENTATION.md` - Port security guide
- `docs/TRAEFIK_SECURITY_GUIDE.md` - Traefik security configuration

---

## Security Monitoring Reference

### Security Metrics Exported (Port 9101)

| Metric | Type | Description |
|--------|------|-------------|
| `security_scan_timestamp` | Gauge | Unix timestamp of last scan |
| `security_scan_status` | Gauge | 1=success, 0=failed |
| `security_failed_logins{type}` | Gauge | Failed login attempts by type |
| `security_open_ports{type}` | Gauge | Open port counts by type |
| `security_suspicious_processes{type}` | Gauge | Suspicious process counts |
| `security_world_writable_files` | Gauge | World-writable file count |
| `security_suid_files` | Gauge | SUID file count |
| `security_docker_vulnerabilities{severity}` | Gauge | CVE counts (critical/high/medium/low) |
| `security_malware_detected` | Gauge | Number of infected files |
| `security_docker_config{check}` | Gauge | Docker security check results |
| `security_container_issues` | Gauge | Container configuration issues |

### Grafana Dashboard Panels

**All Servers Security Overview:**
- Failed Login Attempts (all servers)
- fail2ban Banned IPs (all servers)
- Critical CVEs (all servers)
- Suspicious Processes (all servers)

**Server-Specific Dashboards:**
- Failed Login Attempts (24h trend)
- Open Ports (current count)
- Suspicious Processes (current count)
- Docker Vulnerabilities by Severity
- SUID Files (audit trail)
- World-Writable Files (audit trail)
- Malware Detection Status
- Security Scan Health

---

## Best Practices

1. **Deploy fail2ban to ALL servers** - Not just production (Server 84)
2. **Never whitelist external IPs** - Only whitelist local network (10.0.0.0/24)
3. **Monitor ban activity** - Review fail2ban logs weekly
4. **Test SSH key authentication** - Before disabling password auth
5. **Keep backups of sshd_config** - Automatic backups before changes
6. **Use localhost binding for databases** - ALWAYS use `127.0.0.1:PORT:PORT`
7. **Run security scans daily** - Full scan at 4 AM on servers with Docker
8. **Review security metrics** - Check Grafana dashboards daily
9. **Act on critical CVEs immediately** - Update Docker images within 24 hours
10. **Document security incidents** - Create incident reports for all security events

---

## Security Incident Response Workflow

### 1. Detection
- Security scan detects issue
- Prometheus alert fires
- Grafana dashboard shows anomaly
- fail2ban bans suspicious IP

### 2. Investigation
- SSH into affected server
- Review security scan logs
- Check process details (`ps aux`, `netstat`)
- Examine file system (`find`, `ls -la`)
- Run malware scan (ClamAV)

### 3. Containment
- Kill suspicious processes
- Block IP addresses (fail2ban)
- Isolate affected containers
- Disable compromised accounts

### 4. Eradication
- Remove malicious files
- Delete persistence mechanisms
- Update vulnerable software
- Patch security holes

### 5. Recovery
- Restore from clean backups if needed
- Verify system integrity
- Re-enable services
- Monitor for reinfection

### 6. Lessons Learned
- Document incident details
- Update security procedures
- Implement preventive measures
- Train team on new threats

---

## Maintenance Schedule

**Daily:**
- Review fail2ban banned IPs
- Check Grafana security dashboards
- Review Prometheus security alerts
- Quick security scan (every 15 min automated)

**Weekly:**
- Review fail2ban logs for patterns
- Check for new Docker image vulnerabilities
- Audit SSH login attempts
- Review firewall rules

**Monthly:**
- Full security audit
- Update fail2ban configuration if needed
- Test SSH configuration backups
- Review and optimize security scan performance
- Clean up old security logs (keep 30 days)

**Quarterly:**
- Security penetration testing
- Review and update security policies
- Train team on new security threats
- Update security documentation
- Test disaster recovery procedures

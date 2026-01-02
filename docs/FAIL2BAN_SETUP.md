# fail2ban Setup and Configuration Guide

## Overview

fail2ban is an intrusion prevention framework that protects servers from brute-force attacks by monitoring log files and banning IP addresses that show malicious behavior.

## Deployment Status

| Server | Status | Configuration | Notes |
|--------|--------|---------------|-------|
| Server 80 | ⏳ Pending | N/A | To be deployed |
| Server 81 | ⏳ Pending | N/A | To be deployed |
| Server 82 | ⏳ Pending | N/A | To be deployed |
| Server 84 | ✅ Configured | SSH protection | Production server |

## Server 84 Installation

### Quick Setup

```bash
# Copy the setup script to server 84
scp scripts/setup-fail2ban-server84.sh wizardsofts@10.0.0.84:~/

# SSH into server 84
ssh wizardsofts@10.0.0.84

# Run the setup script
sudo bash setup-fail2ban-server84.sh
```

### Manual Installation

If you prefer to install manually:

```bash
# Install fail2ban
sudo apt update
sudo apt install -y fail2ban

# Enable and start the service
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Configuration

### jail.local Configuration

The main configuration file is `/etc/fail2ban/jail.local`. This overrides default settings from `/etc/fail2ban/jail.conf`.

**Location:** `/etc/fail2ban/jail.local`

```ini
[DEFAULT]
# Ban duration (seconds)
bantime = 3600  # 1 hour

# Time window for counting failures (seconds)
findtime = 600  # 10 minutes

# Number of failures before ban
maxretry = 5

# Ignore local network
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/24

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600
```

### Configuration Parameters Explained

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bantime` | 3600 | Seconds an IP is banned (3600 = 1 hour) |
| `findtime` | 600 | Time window to count failures (600 = 10 min) |
| `maxretry` | 5 | Failed attempts before ban |
| `ignoreip` | 127.0.0.1/8 ::1 10.0.0.0/24 | IPs/networks that are never banned |

### Adjusting for Different Scenarios

#### High-Security Environment (Strict)
```ini
[sshd]
bantime = 86400    # 24 hours
findtime = 300     # 5 minutes
maxretry = 3       # 3 attempts only
```

#### Development Server (Lenient)
```ini
[sshd]
bantime = 1800     # 30 minutes
findtime = 1200    # 20 minutes
maxretry = 10      # 10 attempts
```

#### Production with High Traffic (Balanced)
```ini
[sshd]
bantime = 7200     # 2 hours
findtime = 600     # 10 minutes
maxretry = 5       # 5 attempts
```

## SSH Hardening

The setup script also hardens SSH configuration by:

1. **Disabling password authentication** - Forces SSH key usage only
2. **Disabling root login** - Prevents direct root access
3. **Backing up sshd_config** - Creates timestamped backup before changes

### SSH Configuration Changes

**File:** `/etc/ssh/sshd_config`

```bash
# Disabled
PasswordAuthentication no
PermitRootLogin no

# Enabled
PubkeyAuthentication yes
```

### Reverting SSH Changes

If you need to restore password authentication (not recommended):

```bash
# Find the backup
ls -lah /etc/ssh/sshd_config.backup.*

# Restore from backup
sudo cp /etc/ssh/sshd_config.backup.YYYYMMDD_HHMMSS /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd
```

## Common Operations

### Check fail2ban Status

```bash
# Overall status
sudo fail2ban-client status

# SSH jail specific
sudo fail2ban-client status sshd
```

**Example output:**
```
Status for the jail: sshd
|- Filter
|  |- Currently failed: 2
|  |- Total failed:     143
|  `- File list:        /var/log/auth.log
`- Actions
   |- Currently banned: 0
   |- Total banned:     0
   `- Banned IP list:
```

### View Banned IPs

```bash
# List all banned IPs in sshd jail
sudo fail2ban-client status sshd | grep "Banned IP list"
```

### Unban an IP Address

```bash
# Unban specific IP
sudo fail2ban-client set sshd unbanip 10.0.0.12

# Unban all IPs
sudo fail2ban-client unban --all
```

### Ban an IP Manually

```bash
# Ban specific IP
sudo fail2ban-client set sshd banip 192.168.1.100
```

### View fail2ban Logs

```bash
# Real-time logs
sudo tail -f /var/log/fail2ban.log

# Recent bans
sudo grep "Ban" /var/log/fail2ban.log | tail -20

# Recent unbans
sudo grep "Unban" /var/log/fail2ban.log | tail -20
```

### Reload Configuration

```bash
# After editing jail.local
sudo fail2ban-client reload

# Reload specific jail
sudo fail2ban-client reload sshd
```

### Restart fail2ban

```bash
sudo systemctl restart fail2ban
```

## Monitoring Integration

### Prometheus Metrics Exporter

The setup script automatically deploys a fail2ban Prometheus exporter for monitoring.

**Deployed Configuration:**
- **Image:** `registry.gitlab.com/hectorjsmith/fail2ban-prometheus-exporter:latest`
- **Port:** 9191 (localhost only)
- **Metrics Endpoint:** `http://10.0.0.84:9191/metrics`
- **Location:** `~/fail2ban-exporter/docker-compose.yml`

**Available Metrics:**
```
# Number of banned IPs per jail
fail2ban_banned_ips{jail="sshd"} 0

# Total number of failed attempts per jail
fail2ban_failed_total{jail="sshd"} 143

# Total number of bans per jail
fail2ban_banned_total{jail="sshd"} 0

# Jail status (1=enabled, 0=disabled)
fail2ban_jail_status{jail="sshd"} 1
```

**Manual Operations:**

```bash
# View metrics
curl http://localhost:9191/metrics

# Check exporter logs
docker logs fail2ban-exporter

# Restart exporter
cd ~/fail2ban-exporter && docker compose restart

# Stop exporter
cd ~/fail2ban-exporter && docker compose down

# Start exporter
cd ~/fail2ban-exporter && docker compose up -d
```

**Prometheus Configuration:**

The setup script automatically adds the fail2ban exporter to Prometheus configuration:

```yaml
# /home/wizardsofts/prometheus-config/prometheus.yml
scrape_configs:
  - job_name: 'fail2ban-84'
    static_configs:
      - targets: ['10.0.0.84:9191']
        labels:
          server: 'server-84'
          service: 'fail2ban'
```

**Verify in Prometheus:**

1. Open Prometheus: `http://10.0.0.84:9090`
2. Go to Status → Targets
3. Look for `fail2ban-84` target (should be UP)
4. Query: `fail2ban_banned_ips` or `fail2ban_failed_total`

### Grafana Dashboard

Access Grafana at `http://10.0.0.84:3002` and create a dashboard to visualize:

**Recommended Panels:**

1. **Currently Banned IPs (Stat Panel)**
   - Query: `sum(fail2ban_banned_ips)`
   - Shows current number of banned IPs across all jails

2. **Failed Login Attempts (Time Series)**
   - Query: `rate(fail2ban_failed_total{jail="sshd"}[5m])`
   - Shows rate of failed login attempts over time

3. **Total Bans Over Time (Time Series)**
   - Query: `fail2ban_banned_total{jail="sshd"}`
   - Shows cumulative bans

4. **Banned IPs by Jail (Gauge)**
   - Query: `fail2ban_banned_ips`
   - Group by: `jail`

5. **Jail Status (Stat Panel)**
   - Query: `fail2ban_jail_status`
   - Shows which jails are active

**Example Grafana Dashboard JSON:**

```json
{
  "title": "fail2ban Monitoring - Server 84",
  "panels": [
    {
      "title": "Currently Banned IPs",
      "targets": [{"expr": "sum(fail2ban_banned_ips)"}],
      "type": "stat"
    },
    {
      "title": "Failed Login Rate",
      "targets": [{"expr": "rate(fail2ban_failed_total{jail=\"sshd\"}[5m])"}],
      "type": "graph"
    }
  ]
}
```

## Notification Setup (Optional)

### Email Notifications

To receive email alerts when IPs are banned:

1. Install mail utilities:
```bash
sudo apt install -y mailutils
```

2. Update `/etc/fail2ban/jail.local`:
```ini
[DEFAULT]
destemail = admin@wizardsofts.com
sender = fail2ban@wizardsofts.com
action = %(action_mwl)s  # Send email with logs
```

3. Configure mail server (sendmail/postfix)

### Slack/Discord Notifications

Use custom actions to send webhooks:

**File:** `/etc/fail2ban/action.d/slack.conf`

```ini
[Definition]
actionban = curl -X POST -H 'Content-type: application/json' --data '{"text":"Banned IP: <ip>"}' YOUR_WEBHOOK_URL
```

## Whitelisting

### Permanent Whitelist

Add to `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/24 203.0.113.0/24
```

### Temporary Whitelist

```bash
# Add IP to ignore list (runtime only)
sudo fail2ban-client set sshd addignoreip 192.168.1.50
```

## Troubleshooting

### fail2ban Not Starting

```bash
# Check configuration syntax
sudo fail2ban-client -t

# View service status
sudo systemctl status fail2ban

# Check logs
sudo journalctl -u fail2ban -n 50
```

### SSH Jail Not Working

```bash
# Verify log file exists
ls -lah /var/log/auth.log

# Check filter matches
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf

# Verify jail is enabled
sudo fail2ban-client status
```

### Can't SSH After Setup

If you're locked out:

1. Access server via console (physical or virtual)
2. Check if your IP was banned:
   ```bash
   sudo fail2ban-client status sshd
   ```
3. Unban your IP:
   ```bash
   sudo fail2ban-client set sshd unbanip YOUR_IP
   ```
4. Add your IP to whitelist in `/etc/fail2ban/jail.local`

### IP from Whitelist Got Banned

This shouldn't happen, but if it does:

```bash
# Check current ignore list
sudo fail2ban-client get sshd ignoreip

# Verify jail.local is loaded
sudo fail2ban-client reload
```

## Security Best Practices

### ✅ DO

- Use SSH keys instead of passwords
- Whitelist your trusted IP ranges
- Monitor fail2ban logs regularly
- Keep fail2ban updated
- Test configuration changes in staging first
- Use strong ban times for production servers
- Enable logging for audit trails

### ❌ DON'T

- Don't disable fail2ban on public-facing servers
- Don't set `maxretry` too high (>10)
- Don't rely solely on fail2ban for security
- Don't forget to whitelist your own IPs
- Don't ignore fail2ban logs and alerts
- Don't use the same configuration for all servers

## Performance Considerations

### Log Rotation

fail2ban can be CPU-intensive on large log files. Ensure log rotation is configured:

```bash
# Check logrotate configuration
cat /etc/logrotate.d/fail2ban
cat /etc/logrotate.d/rsyslog
```

### Memory Usage

Typical memory usage: 20-50 MB per jail. Monitor with:

```bash
ps aux | grep fail2ban
```

## Multi-Server Deployment

### Deploy to All Servers

```bash
# Server 80
scp scripts/setup-fail2ban-server84.sh wizardsofts@10.0.0.80:~/
ssh wizardsofts@10.0.0.80 "sudo bash setup-fail2ban-server84.sh"

# Server 81
scp scripts/setup-fail2ban-server84.sh wizardsofts@10.0.0.81:~/
ssh wizardsofts@10.0.0.81 "sudo bash setup-fail2ban-server84.sh"

# Server 82
scp scripts/setup-fail2ban-server84.sh wizardsofts@10.0.0.82:~/
ssh wizardsofts@10.0.0.82 "sudo bash setup-fail2ban-server84.sh"
```

### Centralized Ban Management (Advanced)

For centralized IP banning across all servers, consider:
- **fail2ban with database backend** - Share ban lists via MySQL/PostgreSQL
- **Custom sync script** - Sync `/etc/fail2ban/ip.blacklist` across servers
- **Network-level blocking** - Use firewall rules at router/gateway level

## References

- [fail2ban Official Documentation](https://www.fail2ban.org/)
- [fail2ban GitHub](https://github.com/fail2ban/fail2ban)
- [Ubuntu fail2ban Guide](https://help.ubuntu.com/community/Fail2ban)
- [DigitalOcean fail2ban Tutorial](https://www.digitalocean.com/community/tutorials/how-to-protect-ssh-with-fail2ban-on-ubuntu-20-04)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-01 | Initial configuration for Server 84 | Claude Sonnet 4.5 |

---

**Last Updated:** 2026-01-01
**Maintained By:** WizardSofts Infrastructure Team

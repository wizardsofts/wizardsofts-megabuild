# Deploy Grafana Executive Dashboard

## What Was Changed

1. ✅ **Executive Dashboard Created**: `monitoring/grafana/dashboards/executive-dashboard.json`
2. ✅ **Alert Rules Created**: `monitoring/grafana/provisioning/alerting/alerts.yaml`
3. ✅ **Datasource Provisioning**: `monitoring/grafana/provisioning/datasources/prometheus.yaml`
4. ✅ **Grafana Config**: `monitoring/grafana/grafana.ini` (sets executive dashboard as default)
5. ✅ **Docker Compose Updated**: Added new volume mounts

## Deployment Steps

### Option 1: Deploy to Remote Server (Recommended)

If Grafana is running on one of your servers (10.0.0.80-83):

```bash
# 1. Set the target server
SERVER="10.0.0.82"  # Change to your Grafana server

# 2. Copy the updated files to the server
cd infrastructure/auto-scaling
rsync -avz monitoring/ $SERVER:~/auto-scaling/monitoring/
rsync -avz docker-compose.yml $SERVER:~/auto-scaling/

# 3. SSH into the server and restart Grafana
ssh $SERVER
cd ~/auto-scaling
docker-compose restart grafana

# 4. Check logs
docker logs -f grafana
```

### Option 2: Deploy Locally

If running locally:

```bash
cd infrastructure/auto-scaling

# Create .env file if it doesn't exist
echo "GF_SECURITY_ADMIN_PASSWORD=YourSecurePassword123" > .env

# Start/restart the stack
docker-compose up -d grafana

# Check status
docker ps | grep grafana
docker logs grafana
```

## Verification Steps

1. **Access Grafana**: http://localhost:3002 (or http://YOUR_SERVER_IP:3002)
2. **Login**: Username: `admin`, Password: (from env variable)
3. **Check Default Dashboard**: Should automatically show "Executive Server Status"
4. **Verify Alerts**: Go to Alerting → Alert Rules

## Alert Configuration Details

All alerts are pre-configured and will be active after Grafana restart:

| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| High Memory | >85% | 5 min | Warning |
| Critical Memory | >95% | 2 min | Critical |
| High SWAP | >30% | 10 min | Warning |
| High CPU | >80% | 10 min | Warning |
| High Disk | >85% | 5 min | Warning |
| Server Down | Down | 1 min | Critical |
| Container Memory | >90% | 5 min | Warning |

## Executive Dashboard Features

The new default dashboard shows:

- **System Status**: Online/Offline indicator
- **Resource Gauges**: RAM, CPU, Disk usage with color-coded thresholds
- **System Info**: Uptime, Total Memory, CPU Cores, Total Disk
- **Trends**: 24-hour memory and CPU usage graphs
- **Container Monitoring**: Top 5 containers by memory
- **Network Stats**: Inbound/outbound traffic
- **SWAP Monitoring**: Detects memory pressure
- **Load Average**: System load indicator

## Troubleshooting

### Issue: Grafana won't start

```bash
# Check logs
docker logs grafana

# Common fix: permissions on grafana.ini
chmod 644 monitoring/grafana/grafana.ini

# Restart
docker-compose restart grafana
```

### Issue: Dashboard not set as default

```bash
# Verify grafana.ini is mounted
docker exec grafana cat /etc/grafana/grafana.ini | grep default_home

# Should show:
# default_home_dashboard_path = /etc/grafana/provisioning/dashboards/executive-dashboard.json
```

### Issue: Alerts not showing

```bash
# Check alerting config is loaded
docker exec grafana ls -la /etc/grafana/provisioning/alerting/

# Check datasource
docker exec grafana wget -qO- http://prometheus:9090/api/v1/status/config
```

## Next: Configure Alert Notifications

To receive alerts via email/Slack/etc:

1. Go to Grafana → Alerting → Contact Points
2. Add a new contact point (Email, Slack, PagerDuty, etc.)
3. Create notification policies to route alerts

## File Structure

```
monitoring/
├── grafana/
│   ├── dashboards/
│   │   ├── dashboard.yaml              ← Provisioning config
│   │   ├── executive-dashboard.json    ← NEW: Executive dashboard
│   │   └── autoscaling-dashboard.json
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yaml         ← NEW: Datasource config
│   │   └── alerting/
│   │       └── alerts.yaml             ← NEW: Alert rules
│   ├── grafana.ini                     ← NEW: Config (sets default dashboard)
│   └── grafana_data/
└── prometheus/
    └── prometheus.yml
```

## Cleanup Old Next.js Dev Servers

Already completed - killed 4 Next.js dev servers consuming 8.8 GB RAM:
- PID 13005, 20306, 21719, 30971 ✅ Terminated

Production website (`wwwwizardsoftscom-web-1` Docker container) is unaffected.

# Grafana Monitoring Setup

## Overview

This directory contains Grafana monitoring configuration including dashboards, alerts, and provisioning.

## Dashboards

### Executive Server Status (Default)
- **File**: `grafana/dashboards/executive-dashboard.json`
- **UID**: `executive-overview`
- **Description**: High-level executive dashboard showing:
  - System status (Online/Offline)
  - RAM, CPU, and Disk usage gauges
  - Uptime and system specs
  - 24-hour trends for Memory and CPU
  - Top Docker containers by memory
  - Network traffic statistics
  - SWAP usage monitoring
  - Load average

### Auto-Scaling Platform Dashboard
- **File**: `grafana/dashboards/autoscaling-dashboard.json`
- **Description**: Detailed auto-scaling metrics

## Alert Rules

**File**: `grafana/provisioning/alerting/alerts.yaml`

### Configured Alerts:

1. **High Memory Usage** (Warning)
   - Threshold: >85% for 5 minutes
   - Severity: Warning

2. **Critical Memory Usage** (Critical)
   - Threshold: >95% for 2 minutes
   - Severity: Critical

3. **High SWAP Usage** (Warning)
   - Threshold: >30% for 10 minutes
   - Severity: Warning
   - Purpose: Detect possible memory leaks

4. **High CPU Usage** (Warning)
   - Threshold: >80% for 10 minutes
   - Severity: Warning

5. **High Disk Usage** (Warning)
   - Threshold: >85% for 5 minutes
   - Severity: Warning

6. **Server Down** (Critical)
   - Threshold: Node exporter down for 1 minute
   - Severity: Critical

7. **Container High Memory** (Warning)
   - Threshold: >90% of container limit for 5 minutes
   - Severity: Warning

## Access

- **URL**: http://localhost:3002
- **Username**: admin
- **Password**: Set via `GF_SECURITY_ADMIN_PASSWORD` environment variable

## Configuration Files

```
monitoring/
├── grafana/
│   ├── dashboards/
│   │   ├── dashboard.yaml              # Dashboard provisioning config
│   │   ├── executive-dashboard.json    # Executive dashboard (DEFAULT)
│   │   └── autoscaling-dashboard.json  # Auto-scaling dashboard
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yaml         # Prometheus datasource config
│   │   └── alerting/
│   │       └── alerts.yaml             # Alert rules
│   └── grafana.ini                     # Grafana configuration
├── grafana_data/                       # Persistent data
└── prometheus/
    └── prometheus.yml                  # Prometheus scrape config
```

## Restarting Grafana

To apply configuration changes:

```bash
cd infrastructure/auto-scaling
docker-compose restart grafana
```

To fully reload (recommended after adding new dashboards):

```bash
cd infrastructure/auto-scaling
docker-compose down grafana
docker-compose up -d grafana
```

## Customization

### Adding New Dashboards

1. Create a new JSON file in `grafana/dashboards/`
2. Grafana will auto-load it (dashboard.yaml provisioning)

### Modifying Alerts

1. Edit `grafana/provisioning/alerting/alerts.yaml`
2. Restart Grafana to apply changes

### Changing Default Dashboard

Edit `grafana/grafana.ini`:
```ini
[dashboards]
default_home_dashboard_path = /etc/grafana/provisioning/dashboards/your-dashboard.json
```

## Monitoring Best Practices

1. **Memory Alerts**: Review SWAP usage alerts - high SWAP indicates memory pressure
2. **Regular Checks**: Check the executive dashboard daily
3. **Container Memory**: Monitor container memory limits to prevent OOM kills
4. **Disk Space**: Keep disk usage below 80% for optimal performance

## Troubleshooting

### Dashboard Not Loading
```bash
# Check Grafana logs
docker logs grafana

# Verify file permissions
ls -la monitoring/grafana/dashboards/
```

### Alerts Not Firing
```bash
# Check alerting configuration
docker exec grafana cat /etc/grafana/provisioning/alerting/alerts.yaml

# Verify Prometheus datasource
docker exec grafana wget -O- http://prometheus:9090/-/healthy
```

### Default Dashboard Not Set
- Ensure `grafana.ini` is mounted correctly
- Check Grafana logs for configuration errors
- Verify the dashboard JSON is valid

## Validation

Run the automated validation script to verify all components:
```bash
bash monitoring/validate-grafana.sh
```

This checks:
- Container health status
- API endpoints
- Authentication
- Datasources
- Dashboards
- Prometheus connectivity
- Keycloak OAuth integration
- Network connectivity

## Additional Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions and troubleshooting
- **[Retrospective](../../GRAFANA_DEPLOYMENT_RETROSPECTIVE.md)** - Lessons learned from production deployment
- **[Infrastructure Principles](../../infrastructure/INFRASTRUCTURE_PRINCIPLES.md)** - General infrastructure best practices
- **[Deployment Complete](../../GRAFANA_DEPLOYMENT_COMPLETE.md)** - Current system status and access info

## Next Steps

1. Configure alert notification channels (Email, Slack, etc.)
2. Set up long-term metric storage
3. Create custom dashboards for specific services
4. Implement SLO/SLA tracking dashboards

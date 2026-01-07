# Monitoring Implementation Guide

Complete guide for deploying the WizardSofts monitoring infrastructure with Grafana dashboards, Prometheus alerting, and Appwrite integration.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Component Details](#component-details)
5. [Dashboard Deployment](#dashboard-deployment)
6. [Alert Configuration](#alert-configuration)
7. [Appwrite Integration](#appwrite-integration)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     WizardSofts Infrastructure                   │
│                                                                   │
│  Server 80        Server 81         Server 82       Server 84    │
│  (GIBD)          (Database)         (HPR)          (HP Prod)    │
│     │                │                  │               │        │
│     └────────────────┴──────────────────┴───────────────┘        │
│                            │                                      │
│                            ▼                                      │
│                    ┌──────────────┐                              │
│                    │  Prometheus  │ (Server 84)                  │
│                    │   :9090      │                              │
│                    └──────┬───────┘                              │
│                           │                                       │
│              ┌────────────┼────────────┐                         │
│              ▼            ▼            ▼                          │
│      ┌──────────┐  ┌─────────────┐  ┌──────────┐               │
│      │ Grafana  │  │ Alertmanager│  │   Loki   │               │
│      │  :3002   │  │    :9093    │  │  :3100   │               │
│      └──────────┘  └──────┬──────┘  └──────────┘               │
│                           │                                       │
│                           ▼                                       │
│                  ┌────────────────┐                              │
│                  │ Appwrite       │                              │
│                  │ alert-processor│                              │
│                  │ Function       │                              │
│                  └────────┬───────┘                              │
│                           │                                       │
│          ┌────────────────┼────────────────┐                    │
│          ▼                ▼                ▼                     │
│    ┌─────────┐      ┌─────────┐     ┌─────────┐               │
│    │  Email  │      │  Push   │     │   SMS   │               │
│    └─────────┘      └─────────┘     └─────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements

- Docker and Docker Compose installed
- Access to all 4 servers (80, 81, 82, 84)
- Network connectivity between servers (10.0.0.x network)
- Appwrite instance running on Server 84
- Git for version control

### Access Requirements

- SSH access to all servers
- Appwrite admin access
- Gmail account for SMTP (or alternative SMTP server)
- (Optional) Twilio account for SMS alerts
- (Optional) Slack workspace for notifications

## Quick Start

### 1. Clone and Navigate

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
```

### 2. Deploy Monitoring Stack

```bash
# Deploy exporters on all servers first
cd infrastructure/auto-scaling

# Copy environment template
cp .env.alertmanager.example .env
# Edit .env and add your credentials:
# - SMTP_PASSWORD
# - APPWRITE_API_KEY
# - SLACK_WEBHOOK_URL (optional)

# Deploy monitoring stack
docker-compose up -d prometheus alertmanager grafana loki promtail

# Verify services are running
docker-compose ps
```

### 3. Deploy Dashboards

```bash
# Dashboards are auto-loaded from:
# infrastructure/auto-scaling/monitoring/grafana/dashboards/

# Access Grafana: http://10.0.0.81:3002
# Default credentials (if not using Keycloak): admin / <GF_SECURITY_ADMIN_PASSWORD>
```

### 4. Deploy Appwrite Function

```bash
cd infrastructure/appwrite/functions/alert-processor

# Install Appwrite CLI if needed
npm install -g appwrite-cli

# Login to Appwrite
appwrite login

# Deploy function
./deploy.sh
```

### 5. Configure Appwrite

Follow the detailed steps in [Appwrite Integration](#appwrite-integration).

## Component Details

### Prometheus (Metrics Collection)

**Location**: Server 84  
**Port**: 9090  
**Configuration**: `infrastructure/auto-scaling/monitoring/prometheus/prometheus.yml`

**Scrape Targets**:
- `server-80`: node-exporter (9100), cAdvisor (8081), security-metrics (9101)
- `server-81`: node-exporter (9100), security-metrics (9101)
- `server-82`: node-exporter (9100), cAdvisor (8080)
- `server-84`: node-exporter (9100), cAdvisor (8080), security-metrics (9101)

**Alert Rules**:
- `security-alerts.yml`: Security-focused alerts
- `infrastructure-alerts.yml`: Infrastructure monitoring alerts (50+ rules)

### Grafana (Visualization)

**Location**: Server 81  
**Port**: 3002  
**URL**: http://10.0.0.81:3002

**Dashboards**:

1. **All-Servers Executive Dashboard** (`all-servers-executive.json`)
   - Unified view of all 4 servers
   - Server status, CPU, memory, disk, network
   - Critical services health
   - 24-hour performance trends
   - **Panels**: 26

2. **DevOps Dashboard** (`devops-dashboard.json`)
   - SLA tracking (30-day uptime, 99.9% target)
   - Container health and restart monitoring
   - Capacity planning and forecasting
   - System operations metrics
   - **Panels**: 21

3. **DBA Dashboard** (`dba-dashboard.json`)
   - PostgreSQL performance metrics
   - Redis monitoring
   - Connection pools and query performance
   - Database size and growth tracking
   - **Panels**: 28

4. **MLOps Dashboard** (`mlops-dashboard.json`)
   - Model inference latency (P50/P95/P99)
   - Ray cluster monitoring
   - Celery task queue metrics
   - GPU utilization (if available)
   - **Panels**: 28

### Alertmanager (Alert Routing)

**Location**: Server 84  
**Port**: 9093  
**Configuration**: `infrastructure/auto-scaling/monitoring/alertmanager/alertmanager.yml`

**Alert Routing**:

| Severity | Wait Time | Repeat Interval | Receivers |
|----------|-----------|-----------------|-----------|
| emergency | 0s | 30m | critical-team (webhook, email, Slack) |
| critical | 10s | 1h | critical-team (webhook, email, Slack) |
| warning | 5m | 12h | warning-team (email) |
| security | 20s | 2h | security-team (webhook, email) |
| database | 1m | 3h | dba-team (webhook, email) |
| mlops | 1m | 3h | mlops-team (webhook, email) |

**Inhibition Rules**:
- Critical alerts suppress warnings for same alert
- ServerDown suppresses all other alerts from that instance

### Loki (Log Aggregation)

**Location**: Server 84  
**Port**: 3100  
**Log Sources**: All Docker containers via Promtail

### Appwrite Function (Alert Processing)

**Function ID**: `alert-processor`  
**Runtime**: Node.js 18  
**Webhook URL**: `https://appwrite.wizardsofts.com/v1/functions/alert-processor/executions`

**Features**:
- Alert storage with deduplication
- Smart notification routing
- Push notifications for critical alerts
- SMS integration (Twilio)
- Resolved alert tracking

## Dashboard Deployment

### Automatic Provisioning

Grafana automatically loads dashboards from:
```
infrastructure/auto-scaling/monitoring/grafana/dashboards/*.json
```

To add a new dashboard:

1. Create JSON file in the dashboards directory
2. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```

### Manual Import

1. Open Grafana: http://10.0.0.81:3002
2. Navigate to: Dashboards → Import
3. Upload JSON file or paste JSON content
4. Select Prometheus datasource
5. Click "Import"

### Dashboard Customization

Each dashboard supports customization:

- **Time Range**: Top-right corner (default: Last 24 hours)
- **Refresh Rate**: Top-right corner (default: 30s)
- **Server Selection**: Some dashboards have template variables
- **Panel Editing**: Click panel title → Edit

## Alert Configuration

### Alert Rule Categories

1. **Server Availability** (2 rules)
   - ServerDown: Server unreachable for 1 minute
   - ServerUnreachable: Server down for 5+ minutes

2. **CPU Monitoring** (3 rules)
   - HighCPUUsage: >80% for 5 minutes (warning)
   - CriticalCPUUsage: >95% for 2 minutes (critical)
   - HighIOWait: >20% for 5 minutes (warning)

3. **Memory Monitoring** (3 rules)
   - HighMemoryUsage: >85% for 5 minutes (warning)
   - CriticalMemoryUsage: >95% for 2 minutes (critical)
   - HighSwapUsage: >80% for 10 minutes (warning)

4. **Disk Monitoring** (4 rules)
   - HighDiskUsage: <20% free space (warning)
   - CriticalDiskUsage: <10% free space (critical)
   - DiskWillFillIn4Hours: Predictive alert (warning)
   - HighInodeUsage: <20% free inodes (warning)

5. **Network Monitoring** (2 rules)
   - HighNetworkErrors: >10 errors/sec (warning)
   - HighNetworkDrops: >10 drops/sec (warning)

6. **System Health** (3 rules)
   - HighLoadAverage: Load > 2x CPU count (warning)
   - TooManyOpenFiles: >80% file descriptors (warning)
   - ClockSkew: >0.05s time offset (warning)

7. **Container Monitoring** (2 rules)
   - HighContainerRestartRate: Frequent restarts (warning)
   - ContainerDown: cAdvisor unavailable (warning)

8. **Service Health** (3 rules)
   - PrometheusDown: Metrics collection failure (critical)
   - GrafanaDown: Dashboard unavailable (warning)
   - AlertmanagerDown: Alert routing failure (critical)

### Adding Custom Alerts

1. Edit alert rule file:
   ```bash
   vim infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml
   ```

2. Add new alert rule:
   ```yaml
   - alert: MyCustomAlert
     expr: my_metric > threshold
     for: 5m
     labels:
       severity: warning
       category: custom
     annotations:
       summary: "Brief description"
       description: "Detailed description with {{ $value }}"
       runbook: "https://docs.wizardsofts.com/runbooks/my-alert"
       impact: "What is the impact?"
   ```

3. Validate configuration:
   ```bash
   docker exec prometheus promtool check rules /etc/prometheus/infrastructure-alerts.yml
   ```

4. Reload Prometheus:
   ```bash
   curl -X POST http://10.0.0.84:9090/-/reload
   ```

## Appwrite Integration

### Step 1: Create Database

1. Open Appwrite Console: https://appwrite.wizardsofts.com
2. Navigate to Databases → Create Database
3. **Database ID**: `monitoring`
4. Create collection: `alerts`
5. **Collection ID**: `alerts`

**Attributes**:

| Attribute | Type | Size | Required |
|-----------|------|------|----------|
| alertname | string | 255 | Yes |
| instance | string | 255 | Yes |
| severity | enum | [info, warning, critical, emergency] | Yes |
| category | string | 100 | Yes |
| service | string | 255 | No |
| status | enum | [firing, resolved] | Yes |
| startsAt | datetime | - | Yes |
| endsAt | datetime | - | No |
| summary | string | 500 | No |
| description | string | 2000 | No |
| runbook | url | 500 | No |
| impact | string | 1000 | No |
| fingerprint | string | 255 | Yes |
| groupKey | string | 255 | No |
| externalURL | url | - | No |
| rawAlert | string | 65535 | Yes |
| createdAt | datetime | - | Yes |
| updatedAt | datetime | - | Yes |

**Indexes**:
- `fingerprint` (unique, key)
- `status` (key)
- `severity` (key)
- `instance` (key)
- `startsAt` (key, descending)

### Step 2: Create Messaging Topics

1. Navigate to Messaging → Topics
2. Create topics:
   - **Topic ID**: `critical-alerts`
   - **Topic ID**: `monitoring-alerts`

### Step 3: Deploy Function

```bash
cd infrastructure/appwrite/functions/alert-processor
./deploy.sh
```

### Step 4: Configure Environment Variables

In Appwrite Console → Functions → alert-processor → Settings:

```bash
APPWRITE_ENDPOINT=https://appwrite.wizardsofts.com/v1
APPWRITE_PROJECT_ID=wizardsofts-prod
APPWRITE_FUNCTION_API_KEY=<your-api-key>
DATABASE_ID=monitoring
ALERTS_COLLECTION_ID=alerts
# Optional: SMS configuration
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_PHONE_NUMBER=<your-twilio-number>
ONCALL_PHONE_NUMBERS=+1234567890,+0987654321
```

### Step 5: Create API Key

1. Navigate to API Keys → Create API Key
2. **Name**: Alertmanager Webhook
3. **Scopes**: 
   - `functions.read`
   - `functions.execute`
   - `databases.write`
   - `documents.write`
4. Copy API key and add to `.env`:
   ```bash
   APPWRITE_API_KEY=<your-api-key>
   ```

### Step 6: Restart Services

```bash
cd infrastructure/auto-scaling
docker-compose restart alertmanager
```

## Testing

### Test Alertmanager Configuration

```bash
# Validate Alertmanager config
docker exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml

# View active alerts
curl http://10.0.0.84:9093/api/v2/alerts

# View silences
curl http://10.0.0.84:9093/api/v2/silences
```

### Test Prometheus Alerts

```bash
# Validate alert rules
docker exec prometheus promtool check rules /etc/prometheus/infrastructure-alerts.yml

# View active alerts
curl http://10.0.0.84:9090/api/v1/alerts

# Test alert evaluation
curl 'http://10.0.0.84:9090/api/v1/query?query=ALERTS{alertstate="firing"}'
```

### Test Appwrite Function

```bash
curl -X POST https://appwrite.wizardsofts.com/v1/functions/alert-processor/executions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "appwrite-webhook",
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "instance": "test-server",
        "severity": "warning",
        "category": "test"
      },
      "annotations": {
        "summary": "Test alert",
        "description": "Testing alert processor"
      },
      "startsAt": "2024-01-15T10:00:00Z",
      "fingerprint": "test123"
    }],
    "groupKey": "test",
    "externalURL": "http://alertmanager:9093"
  }'
```

### Trigger Test Alert

```bash
# Simulate high CPU alert (set threshold to 0)
# Edit alert rule temporarily to trigger:
docker exec -it prometheus vi /etc/prometheus/infrastructure-alerts.yml

# Change: expr: cpu_usage > 80
# To:     expr: cpu_usage > 0

# Reload Prometheus
curl -X POST http://10.0.0.84:9090/-/reload

# Wait 5 minutes for alert to fire
# Check Alertmanager: http://10.0.0.84:9093
```

## Troubleshooting

### Prometheus Issues

**Problem**: Targets are down
```bash
# Check Prometheus targets
curl http://10.0.0.84:9090/api/v1/targets

# Check node-exporter is running on target server
ssh user@10.0.0.80 "docker ps | grep node-exporter"

# Check network connectivity
ping 10.0.0.80
telnet 10.0.0.80 9100
```

**Problem**: Alert rules not loading
```bash
# Validate rule files
docker exec prometheus promtool check rules /etc/prometheus/*.yml

# Check Prometheus logs
docker logs prometheus

# Verify rule files are mounted
docker exec prometheus ls -la /etc/prometheus/
```

### Grafana Issues

**Problem**: Dashboards not loading
```bash
# Check Grafana logs
docker logs grafana

# Verify Prometheus datasource
curl http://10.0.0.81:3002/api/datasources

# Test Prometheus connectivity from Grafana container
docker exec grafana wget -O- http://prometheus:9090/api/v1/query?query=up
```

**Problem**: "No data" in panels
```bash
# Check if metrics exist in Prometheus
curl 'http://10.0.0.84:9090/api/v1/query?query=up'

# Verify time range in dashboard
# Check datasource configuration in panel
```

### Alertmanager Issues

**Problem**: Alerts not sending
```bash
# Check Alertmanager logs
docker logs alertmanager

# Verify webhook connectivity
docker exec alertmanager wget --spider https://appwrite.wizardsofts.com/v1/functions/alert-processor/executions

# Test SMTP configuration
docker exec alertmanager amtool config routes test
```

**Problem**: Environment variables not loading
```bash
# Check .env file exists
ls -la infrastructure/auto-scaling/.env

# Verify docker-compose loads .env
docker-compose config | grep SMTP_PASSWORD

# Restart with explicit env file
docker-compose --env-file .env up -d alertmanager
```

### Appwrite Function Issues

**Problem**: Function not receiving webhooks
```bash
# Check function logs in Appwrite Console
# Verify API key has correct permissions
# Test webhook URL manually with curl (see Testing section)

# Check function is active
curl https://appwrite.wizardsofts.com/v1/functions/alert-processor
```

**Problem**: Alerts not stored in database
```bash
# Verify database and collection exist
# Check function has database write permissions
# Review function execution logs
# Test database connection manually
```

### Network Issues

**Problem**: Cross-server communication failing
```bash
# Test connectivity from Server 84 to other servers
ssh user@10.0.0.84
ping 10.0.0.80
ping 10.0.0.81
ping 10.0.0.82

# Check firewall rules
sudo iptables -L -n | grep 9100

# Verify Docker network configuration
docker network inspect microservices-overlay
```

## Maintenance

### Log Rotation

Prometheus retains metrics for 7 days (configurable via `--storage.tsdb.retention.time`).

```bash
# Check current storage size
docker exec prometheus du -sh /prometheus

# Adjust retention period
docker-compose down prometheus
# Edit docker-compose.yml: --storage.tsdb.retention.time=30d
docker-compose up -d prometheus
```

### Backup Configurations

```bash
# Backup monitoring configs
tar -czf monitoring-backup-$(date +%Y%m%d).tar.gz \
  infrastructure/auto-scaling/monitoring/ \
  infrastructure/auto-scaling/docker-compose.yml \
  infrastructure/auto-scaling/.env \
  infrastructure/appwrite/functions/alert-processor/

# Backup Grafana dashboards
docker exec grafana tar -czf /var/lib/grafana-backup.tar.gz /var/lib/grafana
docker cp grafana:/var/lib/grafana-backup.tar.gz ./
```

### Updates

```bash
# Update Prometheus
docker-compose pull prometheus
docker-compose up -d prometheus

# Update Grafana (preserves data)
docker-compose pull grafana
docker-compose up -d grafana

# Update Alertmanager
docker-compose pull alertmanager
docker-compose up -d alertmanager
```

## Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **Alertmanager Documentation**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **Appwrite Documentation**: https://appwrite.io/docs
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review function logs in Appwrite Console
- Check Prometheus/Grafana/Alertmanager logs
- Contact DevOps team: devops@wizardsofts.com

# Using Appwrite for Alert Notifications & Multi-Server Dashboards

> **✅ IMPLEMENTATION COMPLETE**  
> This document outlines the architecture and approach for Appwrite integration with monitoring.  
> For complete deployment instructions, see [MONITORING_IMPLEMENTATION_GUIDE.md](docs/MONITORING_IMPLEMENTATION_GUIDE.md)

## 🎯 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| All-Servers Executive Dashboard | ✅ Complete | `infrastructure/auto-scaling/monitoring/grafana/dashboards/all-servers-executive.json` |
| DevOps Dashboard | ✅ Complete | `infrastructure/auto-scaling/monitoring/grafana/dashboards/devops-dashboard.json` |
| DBA Dashboard | ✅ Complete | `infrastructure/auto-scaling/monitoring/grafana/dashboards/dba-dashboard.json` |
| MLOps Dashboard | ✅ Complete | `infrastructure/auto-scaling/monitoring/grafana/dashboards/mlops-dashboard.json` |
| Alertmanager Configuration | ✅ Complete | `infrastructure/auto-scaling/monitoring/alertmanager/alertmanager.yml` |
| Infrastructure Alert Rules | ✅ Complete | `infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml` |
| Appwrite Alert Processor | ✅ Complete | `infrastructure/appwrite/functions/alert-processor/` |

## 📚 Quick Links

- **[Complete Implementation Guide](docs/MONITORING_IMPLEMENTATION_GUIDE.md)** - Full deployment documentation
- **[Appwrite Function README](infrastructure/appwrite/functions/alert-processor/README.md)** - Alert processor setup

## Part 1: Using Appwrite for Alert Notifications

### ✅ YES - Appwrite Can Be Used for Alerts

Appwrite is a **Backend-as-a-Service (BaaS)** platform with built-in capabilities perfect for alert management:

### Appwrite Capabilities for Alert Notifications

#### **1. Messaging (Email, SMS, Push)**
Appwrite provides:
- **Email Service** (via SMTP integration)
- **Push Notifications** (iOS/Android via APNs, FCM)
- **Webhooks** (can trigger external services)

#### **2. Database for Alert Management**
- Store alert history, acknowledgments, silence windows
- Track alert routing rules per user/role
- Manage escalation policies
- Archive resolved incidents

#### **3. Functions (Serverless)**
- Trigger alert workflows automatically
- Process Prometheus webhooks
- Route alerts based on rules
- Format and send notifications

#### **4. Real-time (WebSocket)**
- Push instant notifications to dashboards
- Subscribe to alert channels
- Live update on alert status changes

### Implemented Architecture

```
Prometheus Alerts
       |
       v
Alertmanager (Port 9093)
       |
       v
Appwrite Function (alert-processor)
       |
       +---> Appwrite Database (store alerts)
       |
       +---> Appwrite Messaging
             |
             +---> Email (SMTP - via Alertmanager)
             +---> Push Notifications (critical alerts)
             +---> SMS (Twilio - for emergencies)
```
             +---> Slack/Teams webhook
             +---> PagerDuty API
```

### Implementation Steps

#### **Option A: Minimal Setup (Recommended)**
Use **Prometheus Alertmanager** + **Appwrite Functions** for routing:

1. **Alertmanager** → receives alerts from Prometheus
2. **Webhook to Appwrite Function** → processes and routes
3. **Appwrite sends notifications** → email, push, Slack

#### **Option B: Full Integration**
1. Store alerts in **Appwrite Collections**
2. Create **Appwrite Functions** for:
   - Deduplication
   - Escalation logic
   - User notification preferences
   - On-call scheduling
3. **Grafana** integrates with Appwrite for rich context

### Appwrite Configuration for Alerts

```yaml
# In your .env.appwrite
# SMTP Configuration for Email Alerts
_APP_SMTP_HOST=smtp.your-mail-server.com
_APP_SMTP_PORT=587
_APP_SMTP_SECURE=true
_APP_SMTP_USERNAME=alerts@wizardsofts.com
_APP_SMTP_PASSWORD=<secure-password>

# APNs Configuration for Push Notifications
_APP_APNS_SANDBOX_CERTIFICATE=<certificate>
_APP_APNS_SANDBOX_KEY=<key>

# Webhook Configuration
ALERTMANAGER_WEBHOOK_URL=https://appwrite.wizardsofts.com/v1/functions/process-alerts
ALERTMANAGER_WEBHOOK_SECRET=<secure-token>
```

### Benefits of Using Appwrite

| Feature | Appwrite | Pure Alertmanager |
|---------|----------|------------------|
| Database for alerts | ✅ Native | ❌ Need external DB |
| Email/Push | ✅ Integrated | ❌ Need integrations |
| User management | ✅ Built-in | ❌ Manual |
| Mobile app alerts | ✅ Native | ❌ Custom build |
| Alert history/audit | ✅ Easy | ❌ Complex |
| Cost | Low (self-hosted) | Free |

---

## Part 2: Multi-Server Executive & Role-Based Dashboards

### Current Server Inventory

| Server | IP | Role | Services | Monitoring |
|--------|----|----|----------|-----------|
| **Server 80** | 10.0.0.80 | GIBD Services | Applications, APIs | ✅ node-exporter, cAdvisor, security |
| **Server 81** | 10.0.0.81 | Database | PostgreSQL, Redis, monitoring stack | ✅ node-exporter, monitoring (Prometheus, Grafana, Loki) |
| **Server 82** | 10.0.0.82 | HPR Server | HPR services | ✅ node-exporter, cAdvisor |
| **Server 84** | 10.0.0.84 | HP Production | Appwrite, microservices, Ray, Celery, GitLab | ✅ node-exporter, cAdvisor, security, monitoring |

### Currently Available Dashboards

**Individual Server Dashboards:**
1. ✅ **Server 80 - Executive Dashboard** (`server-80-executive.json`)
   - CPU, Memory, Disk usage (gauges)
   - Network performance
   - Service health

2. ✅ **Server 80 - Security Dashboard** (`server-80-security.json`)
3. ✅ **Server 81 - Security Dashboard** (`server-81-security.json`)
4. ✅ **Server 84 - Security Dashboard** (`server-84-security.json`)

**Combined Dashboards:**
5. ✅ **All Servers Security Overview** (`all-servers-security.json`)
   - Status for all servers in one view
   - Security metrics aggregated

### What's Missing

❌ **All-Servers Executive Dashboard** (unified infrastructure view)
❌ **Role-Specific Dashboards:**
   - DevOps (deployment, uptime, resources)
   - Security (vulnerabilities, access, firewall)
   - DBA (database performance, replication)
   - MLOps (model inference, GPU usage)

---

## Implementation Plan

### Phase 1: Create Executive Dashboard (All Servers)

This dashboard shows leadership-relevant metrics for all 4 servers:

**Metrics to Include:**
```
+----- ROW: System Status -----+
| Server 80: UP | Server 81: UP | Server 82: UP | Server 84: UP |
| CPU: 45% | CPU: 32% | CPU: 28% | CPU: 67% |
| Memory: 62% | Memory: 48% | Memory: 35% | Memory: 78% |
| Disk: 55% | Disk: 42% | Disk: 38% | Disk: 61% |

+----- ROW: Alert Summary -----+
| Total Alerts: 3 (2 Warning, 1 Critical)
| Server 80: 0 alerts
| Server 81: 1 warning (High replication lag)
| Server 82: 1 warning (Disk > 80%)
| Server 84: 1 critical (Error rate > 5%)

+----- ROW: Service Health -----+
| Appwrite: UP | PostgreSQL: UP | Redis: UP | Prometheus: UP |

+----- ROW: Performance Metrics -----+
| Avg Response Time: 245ms (P99: 1.2s)
| Error Rate: 0.8%
| Request Rate: 2.5k req/sec
| Network In: 450 Mbps | Out: 280 Mbps
```

### Phase 2: Create Role-Specific Dashboards

#### **2.1 DevOps Dashboard**
- Uptime/SLA tracking per server
- Deployment history
- Container restart trends
- Resource utilization forecast
- Cost per service
- Backup/restore status

#### **2.2 Security Dashboard**
- Failed authentication attempts across all servers
- Network anomalies/DDoS indicators
- Security scan results
- Vulnerability status
- Certificate expiration
- Port/service exposure

#### **2.3 DBA Dashboard**
- PostgreSQL: Replication lag, query latency, connections
- Redis: Memory usage, eviction rate, key expiration
- Backup status
- Database size trends
- Slow query log

#### **2.4 MLOps Dashboard**
- Ray cluster status
- Celery task queue depth
- Model inference latency (P50, P95, P99)
- GPU utilization
- Training job status

---

## Implementation Instructions

### Step 1: Create All-Servers Executive Dashboard

Location: `infrastructure/auto-scaling/monitoring/grafana/dashboards/all-servers-executive.json`

Key panels:
- **Row 1:** System Status (4 columns, one per server)
- **Row 2:** Alert Summary (auto-populated from alerting rules)
- **Row 3:** Service Health (status of critical services)
- **Row 4:** Performance Overview (aggregate metrics)

**Template Variables:**
```
- instance: multi-select server labels
- time_range: 24h (default)
```

### Step 2: Create Role-Based Dashboards

**For Grafana Provisioning:**
```yaml
# infrastructure/auto-scaling/monitoring/grafana/provisioning/dashboards/dashboards.yaml
providers:
  - name: 'Default'
    type: file
    options:
      path: /var/lib/grafana/dashboards
    allowUiUpdates: true
    # Sync all JSON files in the dashboards directory
```

### Step 3: Implement Appwrite Alert Integration

**Create Appwrite Function:**

```python
# apps/appwrite-functions/process-alerts/
# Triggered by Prometheus Alertmanager webhook

import json
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.messaging import Messaging

def main(req, res):
    """Process Prometheus alerts and route notifications"""
    
    alerts = json.loads(req.body).get('alerts', [])
    
    client = Client()
    client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
    client.set_api_key(os.getenv('APPWRITE_API_KEY'))
    
    databases = Databases(client)
    messaging = Messaging(client)
    
    for alert in alerts:
        # Store alert in database
        databases.create_document(
            database_id='monitoring',
            collection_id='alerts',
            data={
                'alert_name': alert['labels']['alertname'],
                'severity': alert['labels']['severity'],
                'instance': alert['labels']['instance'],
                'message': alert['annotations']['description'],
                'status': alert['status'],
                'timestamp': alert['startsAt'],
            }
        )
        
        # Route notification based on severity
        if alert['labels']['severity'] == 'critical':
            # Send SMS/push notification
            notify_oncall(alert)
        elif alert['labels']['severity'] == 'warning':
            # Send email
            messaging.send_email(
                to=['devops@wizardsofts.com'],
                subject=f"Alert: {alert['labels']['alertname']}",
                html=format_alert_email(alert)
            )
    
    return res.json({'status': 'processed'})
```

---

## Grafana Configuration for Role-Based Access

### RBAC Setup (with Keycloak OAuth2)

You already have Keycloak configured! Add role-based folder access:

```yaml
# In Grafana UI: Configuration > Security > Roles
# Create roles:
- DevOps (can view: deployments, uptime, resource dashboards)
- Security (can view: security dashboards only)
- DBA (can view: database dashboards only)
- Executive (can view: all executive dashboards)
- Admin (can view/edit all)
```

**Grafana Keycloak Groups → Grafana Roles mapping:**
```
keycloak-group: "devops" → grafana-role: "DevOps"
keycloak-group: "security" → grafana-role: "Security"
keycloak-group: "dba" → grafana-role: "DBA"
keycloak-group: "mlops" → grafana-role: "MLOps"
keycloak-group: "executive" → grafana-role: "Executive"
```

---

## File Locations & URLs

| Item | Location | URL |
|------|----------|-----|
| All dashboards | `infrastructure/auto-scaling/monitoring/grafana/dashboards/*.json` | http://10.0.0.81:3002 |
| Prometheus config | `infrastructure/auto-scaling/monitoring/prometheus/prometheus.yml` | http://10.0.0.81:9090 |
| Alert rules | `infrastructure/auto-scaling/monitoring/prometheus/*.yml` | Same |
| Grafana provisioning | `infrastructure/auto-scaling/monitoring/grafana/provisioning/` | Auto-load |
| Loki logs | `infrastructure/auto-scaling/docker-compose.yml` | http://10.0.0.81:3100 |

---

## Next Steps

1. **Create Appwrite Collections** for alert management
2. **Build All-Servers Executive Dashboard**
3. **Deploy Alertmanager** with Appwrite webhook integration
4. **Configure Appwrite email/SMS** for notifications
5. **Create role-based dashboards** for each team
6. **Set up Grafana RBAC** via Keycloak groups
7. **Test alert routing** end-to-end

Would you like me to:
- [ ] Create the all-servers executive dashboard JSON?
- [ ] Build Appwrite Functions for alert processing?
- [ ] Create role-specific dashboard templates?
- [ ] Deploy Alertmanager with Appwrite integration?

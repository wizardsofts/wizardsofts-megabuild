# Quick Reference Guide
## Multi-Server Docker Auto-Scaling Platform

### System Overview
- **Control Server**: 10.0.0.80 (runs HAProxy, Autoscaler, Monitoring)
- **Worker Servers**: 10.0.0.81, 10.0.0.82, 10.0.0.84
- **Primary Service**: Ollama AI model server
- **Business Hours**: 9 AM - 5 PM

### Directory Structure
```
/opt/autoscaler/           # Main application directory
├── config.yaml           # Main configuration
├── docker-compose.yml    # Deploy control plane
├── app/                  # Auto-scaler application
│   ├── main.py           # FastAPI app
│   ├── autoscaler.py     # Scaling logic
│   ├── docker_manager.py # Docker operations
│   ├── haproxy_manager.py # HAProxy integration
│   ├── scheduler.py      # Business hours logic
│   └── requirements.txt  # Python dependencies
├── haproxy/              # HAProxy configuration
├── monitoring/           # Prometheus & Grafana
├── scripts/              # Helper scripts
├── logs/                 # Application logs
└── backup/               # Configuration backups

/data/                    # Persistent data
├── ollama/              # Ollama models
├── prometheus/          # Prometheus data
└── grafana/             # Grafana data
```

### API Endpoints
- **Health Check**: `GET http://10.0.0.80:8000/`
- **System Status**: `GET http://10.0.0.80:8000/status`
- **List Services**: `GET http://10.0.0.80:8000/services`
- **Service Stats**: `GET http://10.0.0.80:8000/services/{service_name}/stats`
- **Manual Scale Up**: `POST http://10.0.0.80:8000/services/{service_name}/scale/up`
- **Manual Scale Down**: `POST http://10.0.0.80:8000/services/{service_name}/scale/down`
- **Restart Service**: `POST http://10.0.0.80:8000/services/{service_name}/restart`
- **Server Info**: `GET http://10.0.0.80:8000/servers`
- **Scaling Events**: `GET http://10.0.0.80:8000/events`
- **Reload Config**: `POST http://10.0.0.80:8000/config/reload`

### Dashboard Access
- **HAProxy Stats**: http://10.0.0.80:8404
- **Autoscaler API**: http://10.0.0.80:8000
- **Prometheus**: http://10.0.0.80:9090
- **Grafana**: http://10.0.0.80:3000 (admin/admin)

### Common Operations

#### Check System Status
```bash
curl http://10.0.0.80:8000/status
```

#### View Services
```bash
curl http://10.0.0.80:8000/services
```

#### Manual Scaling
```bash
# Scale Ollama up by 1
curl -X POST http://10.0.0.80:8000/services/ollama/scale/up

# Scale Ollama down by 1
curl -X POST http://10.0.0.80:8000/services/ollama/scale/down
```

#### View Service Statistics
```bash
curl http://10.0.0.80:8000/services/ollama/stats | jq
```

#### View Server Information
```bash
curl http://10.0.0.80:8000/servers | jq
```

#### Restart Service
```bash
curl -X POST http://10.0.0.80:8000/services/ollama/restart
```

#### Reload Configuration
```bash
curl -X POST http://10.0.0.80:8000/config/reload
```

### Service Management

#### Start Control Plane
```bash
cd /opt/autoscaler
docker-compose up -d
```

#### Stop Control Plane
```bash
cd /opt/autoscaler
docker-compose down
```

#### Restart Specific Service
```bash
cd /opt/autoscaler
docker-compose restart autoscaler
# or
docker-compose restart haproxy
```

#### View Logs
```bash
# Autoscaler logs
docker-compose logs -f autoscaler

# HAProxy logs
docker-compose logs -f haproxy

# All logs
docker-compose logs -f
```

### Configuration Changes

#### Update Configuration
1. Edit `/opt/autoscaler/config.yaml`
2. Reload configuration: `curl -X POST http://10.0.0.80:8000/config/reload`
3. Or restart the autoscaler: `docker-compose restart autoscaler`

#### Add New Service
1. Add service configuration to `config.yaml`
2. Reload configuration via API
3. Service will be automatically deployed based on min_replicas setting

### Maintenance Tasks

#### Manual Backup
```bash
/opt/autoscaler/scripts/backup.sh
```

#### Health Check
```bash
/opt/autoscaler/scripts/health_check.sh
```

#### Check Disk Usage
```bash
df -h /opt/autoscaler /data
```

#### Check Container Status
```bash
cd /opt/autoscaler
docker-compose ps
```

### Configuration Details

#### Timezone Configuration
- Business hours are evaluated in the timezone specified in `config.yaml`
- Default timezone is UTC but can be changed (e.g., US/Eastern, Asia/Dhaka, Europe/London)
- Format: `timezone: "UTC"` in the `autoscaler.business_hours` section
- All servers use the same business hours window defined in the control server config

#### Scaling Aggregation
- CPU threshold is calculated as the average CPU usage across ALL containers of a service
- If a service has 3 containers with CPU usage of 80%, 70%, and 90%, the average is 80%
- Scaling decisions are made per-service, not globally
- Each service can have different scaling thresholds and cooldown periods

### Troubleshooting

#### If Autoscaler Won't Start
```bash
# Check logs
docker-compose logs autoscaler

# Check configuration syntax and validation
yamllint /opt/autoscaler/config.yaml

# Check Python dependencies
cd /opt/autoscaler/app
pip install -r requirements.txt

# Validate config with new schema (run from app directory)
cd /opt/autoscaler/app
python -c "from config_model import load_and_validate_config; load_and_validate_config('/opt/autoscaler/config.yaml')"
```

#### If Containers Aren't Scaling
```bash
# Check business hours settings
curl http://10.0.0.80:8000/ | jq

# Check current thresholds
curl http://10.0.0.80:8000/services/ollama/stats | jq

# Verify SSH connectivity to servers
ssh wizardsofts@10.0.0.81 "docker ps"
ssh wizardsofts@10.0.0.84 "docker ps"
# For server 82 (deploy user, port 2025)
ssh -p 2025 deploy@10.0.0.82 "docker ps"
```

#### If Load Balancer Not Working
```bash
# Check HAProxy configuration
curl http://10.0.0.80:8404/

# Check if containers are registered in HAProxy
# Check backend configuration
docker exec haproxy cat /usr/local/etc/haproxy/haproxy.cfg
```

### Important Notes
- Scaling only occurs during business hours (configurable in config.yaml with timezone support)
- Minimum 1 replica maintained for each service (configurable per-service)
- Cooldown period prevents rapid scaling (60 seconds by default, configurable per-service)
- SSH keys must be properly configured for all servers
- All servers must be accessible via the specified ports
- Health checks run every 10 seconds (configurable per-service) and unhealthy containers are automatically removed
- Timezone for business hours is configurable per-deployment (supports UTC, US/Eastern, Asia/Dhaka, etc.)
# Product Requirements Document (PRD)
## Multi-Server Docker Autoscaling Platform
### Small-Scale Implementation

**Version:** 1.0 - Final  
**Date:** October 17, 2025  
**Status:** Approved for Implementation  
**Target User:** Solo developer managing 4 local servers

---

## 1. Executive Summary

### 1.1 Product Overview
A turnkey autoscaling platform for managing Docker containers across 4 local servers, optimized for business hours traffic with minimal operational overhead.

### 1.2 Primary Use Case
- Deploy and autoscale Ollama (AI model server)
- Support 3-5 additional web applications
- Predictable business hours load pattern
- Weekly deployment cadence
- Solo developer operation

### 1.3 Key Constraints
- **Budget:** $0 (use existing hardware only)
- **Learning Time:** < 10 hours total
- **Setup Time:** < 4 hours
- **Maintenance:** < 2 hours/month
- **Downtime Tolerance:** < 1 hour acceptable

### 1.4 Success Criteria
✅ Deploy in single afternoon  
✅ Autoscaling works without intervention  
✅ Weekly deployments take < 15 minutes  
✅ System overhead < 150MB RAM  
✅ No Kubernetes complexity

---

## 2. System Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────┐
│              Control Server (Server 1)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   HAProxy    │  │  Autoscaler  │  │   Prometheus │  │
│  │     LB       │  │   FastAPI    │  │   + Grafana  │  │
│  │   20MB RAM   │  │   50MB RAM   │  │   80MB RAM   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼─────────────────┬───────────┐
        │                   │                 │           │
┌───────▼────────┐  ┌───────▼────────┐  ┌────▼──────┐ ┌──▼────────┐
│   Server 1     │  │   Server 2     │  │ Server 3  │ │ Server 4  │
│   (Control)    │  │                │  │           │ │           │
│  Ollama x1     │  │  Ollama x2     │  │ Ollama x1 │ │ Ollama x1 │
│  App-A x1      │  │  App-A x1      │  │ App-B x1  │ │ App-C x1  │
└────────────────┘  └────────────────┘  └───────────┘ └───────────┘
```

### 2.2 Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Load Balancer** | HAProxy 2.8 | 20MB RAM, dynamic backends |
| **Autoscaler** | FastAPI + Python 3.11 | Simple, 50MB RAM |
| **Monitoring** | Prometheus + Grafana | Basic dashboards, 80MB RAM |
| **CI/CD** | GitLab CE (existing) | Already have it |
| **Container** | Docker (existing) | Already have it |
| **Config** | Single YAML file | Easy to manage |
| **Auth** | SSH keys | Simple, secure |

**Total Overhead:** ~150MB RAM on Server 1

---

## 3. Functional Requirements

### 3.1 Core Features (MUST HAVE)

**FR1: Autoscaling**
- Monitor CPU every 30 seconds
- Scale up when avg CPU > 75% (business hours)
- Scale down when avg CPU < 25%
- Min 1 replica, max 3 replicas per service per server
- 60-second cooldown between actions

**FR2: Load Balancing**
- Single entry point per service (e.g., :11434 for Ollama)
- Round-robin distribution
- Health checks every 10 seconds
- Auto-remove unhealthy containers

**FR3: Multi-Service Support**
- Ollama + 4 other services
- Per-service configuration (ports, thresholds)
- Independent scaling per service

**FR4: Simple Deployment**
- Push to GitLab main branch → auto-deploy
- Deploy to all 4 servers
- No downtime required (can have brief interruption)
- Deploy completes in < 15 minutes

**FR5: Basic Monitoring**
- Web dashboard showing:
  - Services up/down
  - Container count per server
  - CPU/Memory usage
  - Recent scaling events
- Accessible at http://control-server:3000

**FR6: Configuration**
- Single config.yaml file
- No code changes needed to add services
- Validate config before applying

### 3.2 Nice to Have (SHOULD HAVE)

**FR7: Manual Control**
- API to manually scale up/down
- Restart failed containers
- Reload configuration without restart

**FR8: Logging**
- Keep 7 days of logs
- Scaling decisions logged
- Errors logged with stack traces

---

## 4. Non-Functional Requirements

### 4.1 Performance
- **System Overhead:** ≤ 150MB RAM total
- **Scaling Latency:** < 60 seconds from trigger to live
- **API Response:** < 2 seconds
- **Health Check:** < 5 seconds

### 4.2 Reliability
- **Uptime Target:** 99% (8.7 hours downtime/year acceptable)
- **Recovery Time:** < 30 minutes manual intervention
- **Data Loss:** Config backed up daily

### 4.3 Usability
- **Setup Time:** < 4 hours (including learning)
- **Add New Service:** < 10 minutes
- **Deploy Update:** < 15 minutes
- **Documentation:** Quick start + FAQ only

### 4.4 Scalability
- **Servers:** 4 servers (fixed)
- **Containers:** Up to 12 per server (48 total)
- **Services:** 5 services maximum

### 4.5 Security
- **SSH:** Key-based only (no passwords)
- **HTTPS:** On HAProxy for external access
- **Secrets:** Stored in GitLab CI/CD variables
- **Firewall:** Local network only (192.168.x.x)

### 4.6 Maintainability
- **Monthly Maintenance:** < 2 hours
- **Codebase:** < 1500 lines Python
- **Dependencies:** < 8 Python packages
- **Updates:** Quarterly (Docker, Python packages)

---

## 5. User Stories

**US1:** As a solo developer, I want to set up the entire system in one afternoon, so I can start using it immediately.

**US2:** As a solo developer, I want containers to scale automatically during business hours, so I don't have to monitor load.

**US3:** As a solo developer, I want to deploy updates by just pushing to Git, so deployments are simple and consistent.

**US4:** As a solo developer, I want to see system status in a simple dashboard, so I know if something is wrong.

**US5:** As a solo developer, I want to add a new service by editing one config file, so I can scale more apps easily.

**US6:** As a solo developer, I want the system to use minimal resources, so it doesn't slow down my actual applications.

---

## 6. Technical Specifications

### 6.1 Configuration File

```yaml
# config.yaml - Single source of truth

# Load Balancer
load_balancer:
  stats_port: 8404
  https_enabled: true
  cert_path: /etc/ssl/certs/server.pem

# Server Inventory
servers:
  - host: 192.168.1.10
    name: server1
    ssh_user: admin
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12
    role: control  # Runs HAProxy, Autoscaler, Monitoring
    
  - host: 192.168.1.11
    name: server2
    ssh_user: admin
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12
    
  - host: 192.168.1.12
    name: server3
    ssh_user: admin
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12
    
  - host: 192.168.1.13
    name: server4
    ssh_user: admin
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12

# Services
services:
  ollama:
    image: ollama/ollama:latest
    port: 11434
    min_replicas: 1
    max_replicas: 8  # Up to 2 per server
    scale_up_threshold: 75
    scale_down_threshold: 25
    cooldown_period: 60
    business_hours_only: true  # Only scale during 9-5
    health_check:
      path: /api/tags
      interval: 10
      timeout: 5
    volumes:
      - /data/ollama:/root/.ollama
    environment:
      OLLAMA_HOST: 0.0.0.0
      
  web_app_a:
    image: myregistry/app-a:latest
    port: 8080
    min_replicas: 1
    max_replicas: 4
    scale_up_threshold: 80
    scale_down_threshold: 30
    cooldown_period: 60
    business_hours_only: true
    health_check:
      path: /health
      interval: 5
      timeout: 3
      
  web_app_b:
    image: myregistry/app-b:latest
    port: 8081
    min_replicas: 1
    max_replicas: 4
    scale_up_threshold: 80
    scale_down_threshold: 30
    cooldown_period: 60
    business_hours_only: true
    health_check:
      path: /health
      interval: 5
      timeout: 3

# Monitoring
monitoring:
  prometheus:
    enabled: true
    port: 9090
    retention: 7d
  grafana:
    enabled: true
    port: 3000
    admin_password: ${GRAFANA_PASSWORD}  # From GitLab secrets

# Autoscaler Settings
autoscaler:
  check_interval: 30  # seconds
  business_hours:
    start: "09:00"
    end: "17:00"
    timezone: "UTC"
  log_level: INFO
  backup:
    enabled: true
    path: /backup
    retention_days: 7
```

### 6.2 API Endpoints

```
GET  /                              - Health check
GET  /status                        - Overall status (uptime, services)
GET  /services                      - List all services with container counts
GET  /services/{name}/stats         - CPU, memory, container details
POST /services/{name}/scale/up      - Manual scale up (+1 container)
POST /services/{name}/scale/down    - Manual scale down (-1 container)
POST /services/{name}/restart       - Restart all containers
GET  /servers                       - Server list with load
GET  /events                        - Recent scaling events (last 100)
POST /config/reload                 - Reload config.yaml
GET  /metrics                       - Prometheus format metrics
```

### 6.3 Directory Structure

```
/opt/autoscaler/
├── config.yaml              # Main configuration
├── docker-compose.yml       # Deploy control plane
├── app/
│   ├── main.py             # FastAPI app (300 lines)
│   ├── autoscaler.py       # Scaling logic (400 lines)
│   ├── docker_mgr.py       # Docker operations (300 lines)
│   ├── haproxy_mgr.py      # HAProxy updates (200 lines)
│   └── scheduler.py        # Business hours logic (100 lines)
├── haproxy/
│   ├── haproxy.cfg         # HAProxy config template
│   └── update.sh           # Config update script
├── monitoring/
│   ├── prometheus.yml      # Prometheus config
│   └── dashboards/         # Grafana dashboards (JSON)
├── scripts/
│   ├── setup.sh            # Initial setup script
│   ├── backup.sh           # Daily backup
│   └── health_check.sh     # System health check
├── logs/                   # Application logs
└── backup/                 # Config backups

/data/
├── ollama/                 # Ollama models (shared NFS optional)
├── prometheus/             # Prometheus data
└── grafana/                # Grafana data
```

### 6.4 GitLab CI/CD Pipeline

```yaml
# .gitlab-ci.yml

stages:
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main

deploy:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client curl
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | ssh-add -
  script:
    # Trigger autoscaler to pull new image and rolling update
    - |
      for server in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
        ssh -o StrictHostKeyChecking=no admin@$server "docker pull $CI_REGISTRY_IMAGE:latest"
      done
    # Tell autoscaler to do rolling update
    - curl -X POST http://192.168.1.10:8000/services/myapp/rolling-update
  only:
    - main
```

---

## 7. Implementation Plan

### Phase 1: Setup (Day 1, Hours 1-2)
- [ ] Clone repository to Server 1
- [ ] Edit config.yaml with server IPs
- [ ] Run `setup.sh` script
- [ ] Verify all servers accessible via SSH

### Phase 2: Control Plane (Day 1, Hours 2-3)
- [ ] Deploy HAProxy, Autoscaler, Monitoring on Server 1
- [ ] Verify dashboard accessible
- [ ] Test manual API calls

### Phase 3: Deploy Ollama (Day 1, Hour 3)
- [ ] Add Ollama to config.yaml
- [ ] Deploy to all servers
- [ ] Test load balancing
- [ ] Verify autoscaling with artificial load

### Phase 4: CI/CD (Day 1, Hour 4)
- [ ] Configure GitLab CI/CD variables
- [ ] Test deployment pipeline
- [ ] Verify rolling updates work

### Phase 5: Monitoring (Day 1, Optional)
- [ ] Import Grafana dashboards
- [ ] Set up basic alerts (optional)
- [ ] Test logging

---

## 8. Operational Procedures

### 8.1 Daily Operations
**Nothing required** - system runs autonomously

### 8.2 Weekly Deployment
```bash
# Push code to GitLab
git add .
git commit -m "Weekly update"
git push origin main

# GitLab CI/CD handles the rest
# Takes ~10 minutes total
```

### 8.3 Adding New Service
```bash
# 1. Edit config.yaml (5 minutes)
vim /opt/autoscaler/config.yaml
# Add new service block

# 2. Reload config (1 minute)
curl -X POST http://192.168.1.10:8000/config/reload

# 3. Service automatically deploys (2-3 minutes)
# Total: ~10 minutes
```

### 8.4 Monthly Maintenance
```bash
# Check logs (5 min)
tail -f /opt/autoscaler/logs/autoscaler.log

# Update Docker images (10 min)
docker-compose pull
docker-compose up -d

# Check disk space (2 min)
df -h

# Verify backups exist (2 min)
ls -lh /opt/autoscaler/backup/

# Total: ~20 minutes
```

### 8.5 Troubleshooting

**Problem:** Container won't start
```bash
# Check logs
docker logs <container-name>

# Check resources
docker stats

# Restart manually
curl -X POST http://192.168.1.10:8000/services/ollama/restart
```

**Problem:** Autoscaling not working
```bash
# Check autoscaler logs
docker logs autoscaler

# Check current thresholds
curl http://192.168.1.10:8000/services/ollama/stats

# Manual scale test
curl -X POST http://192.168.1.10:8000/services/ollama/scale/up
```

---

## 9. Success Metrics

### 9.1 Setup Success
✅ Complete setup in < 4 hours  
✅ All 4 servers reporting healthy  
✅ Dashboard accessible  
✅ Ollama responds through load balancer

### 9.2 Operational Success
✅ Zero manual scaling interventions per week  
✅ Deployments complete in < 15 minutes  
✅ System overhead < 150MB RAM  
✅ < 2 hours maintenance per month

### 9.3 Reliability Success
✅ > 99% uptime (business hours)  
✅ Auto-recovery from single server failure  
✅ No data loss from crashes

---

## 10. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| **Server hardware failure** | HAProxy health checks + auto-redistribute load |
| **Disk full on server** | Monitor disk space, 7-day log retention |
| **Network partition** | Manual intervention acceptable (< 1 hour) |
| **Bad deployment** | Keep previous image, manual rollback via GitLab |
| **Autoscaler crash** | Containers keep running, systemd auto-restart |
| **Config error** | Validation before reload, backup previous config |
| **Learning curve too steep** | Comprehensive quick-start guide, simple troubleshooting |

---

## 11. Out of Scope

❌ Kubernetes  
❌ Multi-region  
❌ High availability (99.9%+)  
❌ Advanced monitoring (tracing, APM)  
❌ Auto-healing application bugs  
❌ Cost optimization  
❌ Blue-green deployments  
❌ Canary releases  
❌ Multi-tenancy  
❌ Complex RBAC  
❌ Compliance (HIPAA, SOC2)

---

## 12. Deliverables

### 12.1 Code
- [ ] FastAPI autoscaler application (~1300 lines)
- [ ] HAProxy configuration templates
- [ ] Docker Compose files
- [ ] GitLab CI/CD pipeline
- [ ] Setup scripts

### 12.2 Configuration
- [ ] config.yaml template
- [ ] Prometheus configuration
- [ ] Grafana dashboard JSON

### 12.3 Documentation
- [ ] Quick Start Guide (< 5 pages)
- [ ] Configuration Reference
- [ ] Troubleshooting FAQ
- [ ] API Documentation

### 12.4 Monitoring
- [ ] Grafana dashboard (single page)
- [ ] Basic Prometheus alerts

---

## 13. Acceptance Criteria

**The system is ready for production when:**

✅ **Setup:** Complete setup from scratch in < 4 hours  
✅ **Autoscaling:** Ollama scales up/down automatically based on CPU  
✅ **Load Balancing:** Traffic distributed evenly across all containers  
✅ **Deployment:** Push to GitLab main → deployed to all servers in < 15 min  
✅ **Monitoring:** Dashboard shows current status of all services  
✅ **Reliability:** System runs for 1 week without intervention  
✅ **Resources:** Total overhead < 150MB RAM on control server  
✅ **Documentation:** Solo developer can set up without external help  
✅ **Multi-Service:** At least 2 different services running (Ollama + 1 app)  
✅ **Business Hours:** Scaling only happens 9 AM - 5 PM  

---

## 14. Approval & Next Steps

**PRD Status:** ✅ **APPROVED**

**Next Actions:**
1. Create implementation plan with detailed steps
2. Generate all source code
3. Write setup scripts
4. Create documentation
5. Provide deployment checklist

**Estimated Implementation Time:** 
- PRD → Working System: 1 week development
- Your Setup Time: 4 hours


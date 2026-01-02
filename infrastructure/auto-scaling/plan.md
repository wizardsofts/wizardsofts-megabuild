# Implementation Plan
## Multi-Server Docker Autoscaling Platform

**Version:** 1.0  
**Date:** October 17, 2025  
**Estimated Total Time:** 4 hours setup + 1 week development  
**Target:** 4 servers, solo developer, business hours scaling

---

## Overview

This plan provides step-by-step instructions to implement the autoscaling platform. Follow in order.

**Timeline:**
- **Development (Me):** 1 week to provide all code/configs
- **Setup (You):** 4 hours to deploy and test
- **Go-Live:** Same day as setup completion

---

## Pre-requisites Checklist

Before starting, verify you have:

- [ ] 4 servers on local network (192.168.x.x)
- [ ] Docker installed on all servers
- [ ] GitLab instance accessible
- [ ] SSH access to all servers
- [ ] SSH keys generated (no password auth)
- [ ] sudo/root access on all servers
- [ ] Git installed on Server 1
- [ ] At least 2GB free RAM on Server 1
- [ ] At least 500MB free RAM on other servers
- [ ] Network connectivity between all servers
- [ ] Ports available: 80, 443, 8000, 8404, 9090, 3000, 11434

---

## Phase 1: Environment Preparation (30 minutes)

### Step 1.1: Server Inventory
**Time:** 5 minutes

Document your server details:

```bash
# Create inventory file
cat > servers.txt <<EOF
Server 1 (Control): 192.168.1.10
Server 2: 192.168.1.11
Server 3: 192.168.1.12
Server 4: 192.168.1.13
EOF
```

**Verify connectivity:**
```bash
# Test SSH to each server
for ip in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
  echo "Testing $ip..."
  ssh admin@$ip "echo 'Connected successfully'"
done
```

**Expected Output:** "Connected successfully" for each server

---

### Step 1.2: SSH Key Setup
**Time:** 10 minutes

**On Server 1 (Control Server):**

```bash
# Generate SSH key if not exists
if [ ! -f ~/.ssh/id_rsa ]; then
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
fi

# Copy to all servers (including itself)
for ip in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
  ssh-copy-id admin@$ip
done

# Test passwordless SSH
for ip in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
  ssh admin@$ip "hostname"
done
```

**Verify:** Should connect without password prompt

---

### Step 1.3: Docker Verification
**Time:** 10 minutes

**On each server:**

```bash
# Check Docker is running
docker --version
docker ps

# Check Docker daemon is accessible
docker info

# Test Docker run
docker run --rm hello-world
```

**If Docker not installed:**
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker run --rm hello-world
```

---

### Step 1.4: Create Directory Structure
**Time:** 5 minutes

**On Server 1:**

```bash
# Create base directory
sudo mkdir -p /opt/autoscaler
sudo chown $USER:$USER /opt/autoscaler
cd /opt/autoscaler

# Create subdirectories
mkdir -p app haproxy monitoring/{prometheus,grafana} scripts logs backup

# Create data directories
sudo mkdir -p /data/{ollama,prometheus,grafana}
sudo chown -R $USER:$USER /data
```

**Verify structure:**
```bash
tree /opt/autoscaler -L 2
```

---

## Phase 2: Code Deployment (45 minutes)

### Step 2.1: Clone Repository
**Time:** 5 minutes

```bash
cd /opt/autoscaler

# Option A: Clone from provided repo
git clone <REPOSITORY_URL> .

# Option B: Create from scratch (if providing files individually)
# Files will be created in subsequent steps
```

---

### Step 2.2: Create Configuration File
**Time:** 15 minutes

**Create `/opt/autoscaler/config.yaml`:**

```bash
cat > /opt/autoscaler/config.yaml <<'EOF'
# Load Balancer Configuration
load_balancer:
  stats_port: 8404
  https_enabled: false  # Set true after SSL setup
  
# Server Inventory
servers:
  - host: 192.168.1.10
    name: server1
    ssh_user: admin
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12
    role: control
    
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
    max_replicas: 8
    scale_up_threshold: 75
    scale_down_threshold: 25
    cooldown_period: 60
    business_hours_only: true
    health_check:
      path: /api/tags
      interval: 10
      timeout: 5
    volumes:
      - /data/ollama:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

# Monitoring
monitoring:
  prometheus:
    enabled: true
    port: 9090
    retention: 7d
  grafana:
    enabled: true
    port: 3000

# Autoscaler Settings
autoscaler:
  check_interval: 30
  business_hours:
    start: "09:00"
    end: "17:00"
    timezone: "UTC"
  log_level: INFO
EOF
```

**Edit with your actual values:**
```bash
vim /opt/autoscaler/config.yaml
# Update IP addresses, usernames, SSH key paths
```

---

### Step 2.3: Deploy Application Code
**Time:** 10 minutes

**Files to create** (will be provided as deliverables):

```
/opt/autoscaler/app/
├── main.py              # FastAPI app
├── autoscaler.py        # Scaling logic
├── docker_manager.py    # Docker operations
├── haproxy_manager.py   # HAProxy integration
├── scheduler.py         # Business hours logic
└── requirements.txt     # Python dependencies
```

**Create requirements.txt:**
```bash
cat > /opt/autoscaler/app/requirements.txt <<EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
docker==6.1.3
paramiko==3.3.1
pyyaml==6.0.1
apscheduler==3.10.4
pydantic==2.5.0
python-multipart==0.0.6
EOF
```

**Install dependencies:**
```bash
python3 -m venv /opt/autoscaler/venv
source /opt/autoscaler/venv/bin/activate
pip install -r /opt/autoscaler/app/requirements.txt
```

---

### Step 2.4: HAProxy Configuration
**Time:** 10 minutes

**Create `/opt/autoscaler/haproxy/haproxy.cfg`:**

```bash
cat > /opt/autoscaler/haproxy/haproxy.cfg <<'EOF'
global
    log stdout format raw local0
    maxconn 4096
    stats socket /var/run/haproxy.sock mode 660 level admin expose-fd listeners
    stats timeout 30s

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# Stats page
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats refresh 5s
    stats show-legends
    stats show-node

# Ollama backend
frontend ollama_frontend
    bind *:11434
    default_backend ollama_backend

backend ollama_backend
    balance roundrobin
    option httpchk GET /api/tags
    http-check expect status 200
    # Servers will be added dynamically by autoscaler
EOF
```

---

### Step 2.5: Docker Compose for Control Plane
**Time:** 5 minutes

**Create `/opt/autoscaler/docker-compose.yml`:**

```bash
cat > /opt/autoscaler/docker-compose.yml <<'EOF'
version: '3.8'

services:
  haproxy:
    image: haproxy:2.8-alpine
    container_name: haproxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "8404:8404"
      - "11434:11434"
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - haproxy-socket:/var/run
    networks:
      - autoscaler

  autoscaler:
    build: ./app
    container_name: autoscaler
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
      - ./backup:/app/backup
      - ~/.ssh:/root/.ssh:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - haproxy-socket:/var/run
    networks:
      - autoscaler
    depends_on:
      - haproxy
    environment:
      - PYTHONUNBUFFERED=1

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - /data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
    networks:
      - autoscaler

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - /data/grafana:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - autoscaler

networks:
  autoscaler:
    driver: bridge

volumes:
  haproxy-socket:
EOF
```

**Create Dockerfile for autoscaler:**
```bash
cat > /opt/autoscaler/app/Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends openssh-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

---

## Phase 3: Monitoring Setup (30 minutes)

### Step 3.1: Prometheus Configuration
**Time:** 10 minutes

**Create `/opt/autoscaler/monitoring/prometheus/prometheus.yml`:**

```bash
mkdir -p /opt/autoscaler/monitoring/prometheus
cat > /opt/autoscaler/monitoring/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'autoscaler'
    static_configs:
      - targets: ['autoscaler:8000']

  - job_name: 'haproxy'
    static_configs:
      - targets: ['haproxy:8404']

  - job_name: 'cadvisor'
    static_configs:
      - targets: 
        - '192.168.1.10:8080'
        - '192.168.1.11:8080'
        - '192.168.1.12:8080'
        - '192.168.1.13:8080'
EOF
```

---

### Step 3.2: Deploy cAdvisor on All Servers
**Time:** 15 minutes

**Run on each server (10, 11, 12, 13):**

```bash
docker run -d \
  --name=cadvisor \
  --restart=unless-stopped \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=8080:8080 \
  --privileged \
  --device=/dev/kmsg \
  gcr.io/cadvisor/cadvisor:latest
```

**Verify cAdvisor is running:**
```bash
curl http://192.168.1.10:8080/metrics
```

---

### Step 3.3: Grafana Dashboard
**Time:** 5 minutes

**Create `/opt/autoscaler/monitoring/grafana/dashboards/dashboard.yaml`:**

```bash
mkdir -p /opt/autoscaler/monitoring/grafana/dashboards
cat > /opt/autoscaler/monitoring/grafana/dashboards/dashboard.yaml <<'EOF'
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
```

*Dashboard JSON will be provided as separate deliverable*

---

## Phase 4: Control Plane Deployment (30 minutes)

### Step 4.1: Start Control Plane
**Time:** 10 minutes

**On Server 1:**

```bash
cd /opt/autoscaler

# Build and start services
docker-compose up -d

# Check all services are running
docker-compose ps

# Expected: 4 services running (haproxy, autoscaler, prometheus, grafana)
```

**Check logs:**
```bash
docker-compose logs -f autoscaler
# Should show "Application startup complete"
```

---

### Step 4.2: Verify Control Plane
**Time:** 10 minutes

**Test each component:**

```bash
# HAProxy stats
curl http://192.168.1.10:8404
# Should show HAProxy stats page

# Autoscaler API
curl http://192.168.1.10:8000/
# Should return: {"status":"running"}

# Prometheus
curl http://192.168.1.10:9090/-/healthy
# Should return: Prometheus is Healthy

# Grafana
curl http://192.168.1.10:3000/api/health
# Should return: {"database":"ok"}
```

**Access dashboards in browser:**
- HAProxy: http://192.168.1.10:8404
- Autoscaler API: http://192.168.1.10:8000
- Prometheus: http://192.168.1.10:9090
- Grafana: http://192.168.1.10:3000 (admin/admin)

---

### Step 4.3: Initial Configuration Test
**Time:** 10 minutes

```bash
# Check server connectivity
curl http://192.168.1.10:8000/servers

# Should show all 4 servers

# Check services
curl http://192.168.1.10:8000/services

# Should show configured services (ollama)

# Test manual scale
curl -X POST http://192.168.1.10:8000/services/ollama/scale/up

# Check logs
docker logs autoscaler -f
# Should show scaling activity
```

---

## Phase 5: Ollama Deployment (45 minutes)

### Step 5.1: Deploy Ollama to All Servers
**Time:** 20 minutes

**Autoscaler will handle this, but can also do manually:**

```bash
# On each server (10, 11, 12, 13)
docker run -d \
  --name ollama-$(date +%s) \
  -p 0:11434 \
  -v /data/ollama:/root/.ollama \
  -e OLLAMA_HOST=0.0.0.0 \
  --restart unless-stopped \
  ollama/ollama:latest
```

**Or trigger via API:**
```bash
# Let autoscaler deploy
curl -X POST http://192.168.1.10:8000/services/ollama/deploy
```

---

### Step 5.2: Verify Ollama Deployment
**Time:** 10 minutes

```bash
# Check containers on each server
for ip in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
  echo "Checking $ip..."
  ssh admin@$ip "docker ps | grep ollama"
done

# Test through load balancer
curl http://192.168.1.10:11434/api/tags

# Should return Ollama API response
```

---

### Step 5.3: Load Test Autoscaling
**Time:** 15 minutes

**Install stress testing tool:**
```bash
pip install locust
```

**Create test script `locustfile.py`:**
```python
from locust import HttpUser, task, between

class OllamaUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task
    def health_check(self):
        self.client.get("/api/tags")
```

**Run load test:**
```bash
# Generate load for 5 minutes
locust -f locustfile.py --headless \
  --users 50 --spawn-rate 10 \
  --host http://192.168.1.10:11434 \
  --run-time 5m
```

**Monitor scaling:**
```bash
# Watch autoscaler logs
docker logs -f autoscaler

# Watch container count
watch -n 5 'curl -s http://192.168.1.10:8000/services/ollama/stats'
```

**Expected behavior:**
- CPU rises above 75% → New containers start
- CPU drops below 25% → Containers stop
- Min 1 replica always maintained

---

## Phase 6: CI/CD Setup (30 minutes)

### Step 6.1: GitLab CI/CD Configuration
**Time:** 15 minutes

**Create `.gitlab-ci.yml` in your application repo:**

```yaml
stages:
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2

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
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
  script:
    # Pull new image on all servers
    - |
      for server in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
        ssh -o StrictHostKeyChecking=no admin@$server "docker pull $CI_REGISTRY_IMAGE:latest"
      done
    # Trigger rolling update
    - curl -X POST http://192.168.1.10:8000/services/myapp/rolling-update
  only:
    - main
```

---

### Step 6.2: Configure GitLab Variables
**Time:** 10 minutes

**In GitLab: Settings → CI/CD → Variables, add:**

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `SSH_PRIVATE_KEY` | (content of ~/.ssh/id_rsa) | ✓ | ✓ |
| `CI_REGISTRY` | gitlab.yourdomain.com:5050 | ✓ | - |
| `CI_REGISTRY_USER` | gitlab-ci-token | ✓ | - |
| `CI_REGISTRY_PASSWORD` | (from GitLab) | ✓ | ✓ |

---

### Step 6.3: Test Deployment Pipeline
**Time:** 5 minutes

```bash
# Make a test commit
cd /path/to/your/app
echo "# Test" >> README.md
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin main

# Monitor in GitLab UI
# Jobs should complete: build → deploy

# Verify deployment
curl http://192.168.1.10:8000/services/myapp/stats
```

---

## Phase 7: Documentation & Scripts (15 minutes)

### Step 7.1: Create Helper Scripts
**Time:** 10 minutes

**Create `/opt/autoscaler/scripts/setup.sh`:**

```bash
cat > /opt/autoscaler/scripts/setup.sh <<'EOF'
#!/bin/bash
set -e

echo "=== Autoscaler Setup Script ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker not found"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "docker-compose not found"; exit 1; }

# Create directories
mkdir -p /opt/autoscaler/{app,haproxy,monitoring,scripts,logs,backup}
mkdir -p /data/{ollama,prometheus,grafana}

# Set permissions
chown -R $USER:$USER /opt/autoscaler /data

echo "Setup complete!"
EOF

chmod +x /opt/autoscaler/scripts/setup.sh
```

**Create `/opt/autoscaler/scripts/backup.sh`:**

```bash
cat > /opt/autoscaler/scripts/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/opt/autoscaler/backup
DATE=$(date +%Y%m%d_%H%M%S)

# Backup config
cp /opt/autoscaler/config.yaml $BACKUP_DIR/config_$DATE.yaml

# Backup HAProxy config
cp /opt/autoscaler/haproxy/haproxy.cfg $BACKUP_DIR/haproxy_$DATE.cfg

# Keep last 7 days
find $BACKUP_DIR -name "*.yaml" -mtime +7 -delete
find $BACKUP_DIR -name "*.cfg" -mtime +7 -delete

echo "Backup complete: $DATE"
EOF

chmod +x /opt/autoscaler/scripts/backup.sh
```

**Create daily backup cron:**
```bash
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/autoscaler/scripts/backup.sh") | crontab -
```

---

### Step 7.2: Create Quick Reference
**Time:** 5 minutes

**Create `/opt/autoscaler/QUICKREF.md`:**

```markdown
# Quick Reference

## Check Status
curl http://192.168.1.10:8000/status

## View Services
curl http://192.168.1.10:8000/services

## Manual Scale
curl -X POST http://192.168.1.10:8000/services/ollama/scale/up
curl -X POST http://192.168.1.10:8000/services/ollama/scale/down

## View Logs
docker logs -f autoscaler

## Restart Service
docker-compose restart autoscaler

## Reload Config
curl -X POST http://192.168.1.10:8000/config/reload

## Dashboards
- HAProxy: http://192.168.1.10:8404
- Autoscaler: http://192.168.1.10:8000
- Prometheus: http://192.168.1.10:9090
- Grafana: http://192.168.1.10:3000
```

---

## Phase 8: Testing & Validation (30 minutes)

### Step 8.1: Functionality Tests
**Time:** 15 minutes

```bash
# Test 1: Service status
curl http://192.168.1.10:8000/services | jq

# Test 2: Manual scale up
curl -X POST http://192.168.1.10:8000/services/ollama/scale/up
sleep 10
curl http://192.168.1.10:8000/services/ollama/stats | jq

# Test 3: Manual scale down
curl -X POST http://192.168.1.10:8000/services/ollama/scale/down
sleep 10
curl http://192.168.1.10:8000/services/ollama/stats | jq

# Test 4: Load balancer
for i in {1..10}; do
  curl -s http://192.168.1.10:11434/api/tags
done

# Test 5: Config reload
vim /opt/autoscaler/config.yaml
# Make a small change
curl -X POST http://192.168.1.10:8000/config/reload

# Test 6: Health checks
curl http://192.168.1.10:8000/
curl http://192.168.1.10:8404/
curl http://192.168.1.10:9090/-/healthy
```

---

### Step 8.2: Failure Recovery Tests
**Time:** 15 minutes

**Test 1: Container crash**
```bash
# Kill a container
docker stop ollama-12345

# Wait 10 seconds
sleep 10

# Verify HAProxy removed it
curl http://192.168.1.10:8404/ | grep ollama
```

**Test 2: Server failure simulation**
```bash
# On Server 2, stop Docker
ssh admin@192.168.1.11 "sudo systemctl stop docker"

# Wait 30 seconds
sleep 30

# Check autoscaler redistributed load
curl http://192.168.1.10:8000/services/ollama/stats

# Restore
ssh admin@192.168.1.11 "sudo systemctl start docker"
```

**Test 3: Autoscaler restart**
```bash
# Restart autoscaler
docker restart autoscaler

# Wait for startup
sleep 15

# Verify it synced state
curl http://192.168.1.10:8000/services/ollama/stats
```

---

## Phase 9: Go-Live (15 minutes)

### Step 9.1: Final Configuration
**Time:** 5 minutes

```bash
# Enable business hours scaling
vim /opt/autoscaler/config.yaml
# Verify business_hours_only: true

# Set proper timezone
# Update timezone in config to match your location

# Reload config
curl -X POST http://192.168.1.10:8000/config/reload
```

---

### Step 9.2: Enable Auto-start
**Time:** 5 minutes

**Create systemd service:**
```bash
sudo tee /etc/systemd/system/autoscaler.service <<EOF
[Unit]
Description=Docker Autoscaler Control Plane
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/autoscaler
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable autoscaler.service
```

---

### Step 9.3: Final Checks
**Time:** 5 minutes

```bash
# Verify all services
docker-compose ps

# Check resource usage
docker stats --no-stream

# Verify total RAM usage < 150MB for control plane
docker stats autoscaler haproxy prometheus grafana --no-stream

# Test load balancer endpoint
curl http://192.168.1.10:11434/api/tags

# Access Grafana and verify dashboards
# http://192.168.1.10:3000
```

---

## Post-Implementation Checklist

After completing all phases, verify:

- [ ] All 4 servers accessible via SSH
- [ ] Control plane running on Server 1
- [ ] HAProxy stats accessible
- [ ] Autoscaler API responding
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards visible
- [ ] Ollama deployed on all servers
- [ ] Load balancing working
- [ ] Autoscaling triggers correctly
- [ ] GitLab CI/CD pipeline configured
- [ ] Test deployment successful
- [ ] Backup cron job running
- [ ] Documentation complete
- [ ] System auto-starts on reboot

---

## Troubleshooting Guide

### Issue: Autoscaler won't start

```bash
# Check logs
docker logs autoscaler

# Common causes:
# 1. Config file syntax error
yamllint /opt/autoscaler/config.yaml

# 2. SSH connection failed
ssh admin@192.168.1.10 "hostname"

# 3. Docker socket not accessible
ls -l /var/run/docker.sock
```

### Issue: Containers not scaling

```bash
# Check autoscaler logic
docker logs autoscaler | grep -i scale

# Verify thresholds
curl http://192.168.1.10:8000/services/ollama/stats | jq

# Check business hours
date  # Verify current time
# Make sure it's within business hours if business_hours_only: true
```

### Issue: Load balancer not routing

```bash
# Check HAProxy config
docker exec haproxy cat /usr/local/etc/haproxy/haproxy.cfg

# Check HAProxy stats
curl http://192.168.1.10:8404/

# Verify containers are healthy
for ip in 192.168.1.10 192.168.1.11 192.168.1.12 192.168.1.13; do
  ssh admin@$ip "docker ps | grep ollama"
done
```

### Issue: High resource usage

```bash
# Check which component
docker stats

# If autoscaler high:
# - Reduce check_interval in config
# - Check for log spam

# If Prometheus high:
# - Reduce retention period
# - Reduce scrape frequency
```

---

## Maintenance Schedule

### Daily (Automated)
- Config backup (cron job)
- Log rotation (built-in)

### Weekly (5 minutes)
```bash
# Check system status
curl http://192.168.1.10:8000/status

# Review logs for errors
docker logs autoscaler --since 7d | grep ERROR

# Check disk space
df -h
```

### Monthly (30 minutes)
```bash
# Update Docker images
cd /opt/autoscaler
docker-compose pull
docker-compose up -d

# Update Python dependencies
source venv/bin/activate
pip install --upgrade -r app/requirements.txt

# Review and clean old backups
ls -lh /opt/autoscaler/backup/

# Review Grafana dashboards
# Check for anomalies
```

### Quarterly (1 hour)
```bash
# Full system audit
# - Review all configurations
# - Test disaster recovery
# - Update documentation
# - Review and optimize thresholds
```

---

## Success Metrics

After 1 week of operation, verify:

✅ **Zero manual scaling interventions**  
✅ **All deployments completed successfully**  
✅ **System overhead < 150MB RAM**  
✅ **< 1 hour maintenance time spent**  
✅ **No unplanned downtime**  
✅ **Autoscaling triggered correctly during business hours**

---

## Next Steps After Go-Live

1. **Week 1:** Monitor closely, tune thresholds if needed
2. **Week 2:** Add second service (web app)
3. **Week 3:** Optimize based on actual usage patterns
4. **Week 4:** Document lessons learned
5. **Month 2:** Consider adding HTTPS if needed
6. **Month 3:** Review and optimize resource allocation

---

## Support & Resources

**Logs Location:** `/opt/autoscaler/logs/`  
**Config Location:** `/opt/autoscaler/config.yaml`  
**Backup Location:** `/opt/autoscaler/backup/`  
**Documentation:** `/opt/autoscaler/docs/`

**Quick Commands:**
```bash
# Status
curl http://192.168.1.10:8000/status

# Logs
docker logs -f autoscaler

# Restart
docker-compose restart

# Full restart
docker-compose down && docker-compose up -d
```

---

# Reality Check: Ollama Autoscaling Infrastructure

**Date**: 2026-01-05
**Status**: CRITICAL CORRECTIONS - Infrastructure Review Complete

---

## ✅ **What EXISTS (Reality)**

### 1. **Docker Swarm** ✅ ACTIVE
```bash
ssh wizardsofts@10.0.0.84 "docker info | grep Swarm"
# Output: Swarm: active
```

### 2. **Traefik Reverse Proxy** ✅ RUNNING
**Config**: `/Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/traefik/traefik.yml`

**Key Settings**:
```yaml
providers:
  docker:
    swarmMode: false  # ❌ NOT using Swarm mode!
    exposedByDefault: false
    network: wizardsofts-megabuild_gibd-network
  file:
    filename: /etc/traefik/dynamic_conf.yml
    watch: true

metrics:
  prometheus: {}  # ✅ Prometheus metrics enabled
```

**Load Balancing**: Traefik supports `loadBalancer` with multiple servers per service

### 3. **Custom Autoscaler** ⚠️ EXISTS but FAILING
**Location**: `infrastructure/auto-scaling/`

**Components**:
- `app/autoscaler.py` - Python FastAPI autoscaler
- `app/docker_manager.py` - Docker container management
- `app/haproxy_manager.py` - HAProxy config management
- `config.yaml` - Service definitions

**Current Status**:
```bash
docker ps | grep autoscaler
# Output: Restarting (1) 28 seconds ago ❌ FAILING!
```

**Architecture**:
```
HAProxy (10.0.0.84:8404) ✅ RUNNING
    ↓
Autoscaler (FastAPI) ❌ RESTARTING
    ↓
Docker Manager → Container deployment
```

**Features**:
- CPU-based autoscaling (scale_up_threshold, scale_down_threshold)
- Business hours support
- Health checks
- Prometheus metrics
- HAProxy dynamic backend updates

### 4. **HAProxy Load Balancer** ✅ RUNNING
```bash
docker ps | grep haproxy
# Output: Up 5 hours, Port 8404 ✅ RUNNING
```

**Purpose**: Internal load balancing for autoscaled services

---

## ❌ **What DOES NOT EXIST**

### 1. **Ollama in Autoscaler Config** ❌ NOT CONFIGURED FOR AUTOSCALING

**Current `config.yaml`**:
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    port: 11434
    min_replicas: 1
    max_replicas: 1  # ❌ LOCKED AT 1 REPLICA!
    business_hours_only: true
```

**Problem**: `max_replicas: 1` means autoscaler will **NEVER** scale Ollama!

### 2. **Ollama NOT Managed by Autoscaler** ❌ INDEPENDENT CONTAINER

**Current Deployment**:
```bash
ssh wizardsofts@10.0.0.80 "docker ps | grep ollama"
# Output: hadith-ollama (single instance) ❌ NOT autoscaled
```

**How it's deployed**: Via `docker-compose.yml` in hadith project, **NOT** via autoscaler

### 3. **No NFS Setup** ❌ NOT CONFIGURED

Checked: No `/opt/ollama-models` directory or NFS mounts

### 4. **No Traefik Load Balancer for Ollama** ❌ NOT CONFIGURED

**Current Traefik config** (`traefik/dynamic_conf.yml`): **No Ollama service defined**

---

## 📋 **Ollama JSON Format** ✅ CONFIRMED

**Langchain Documentation**: https://docs.langchain.com/oss/javascript/integrations/chat/ollama

```javascript
const llmJsonMode = new ChatOllama({
  baseUrl: "http://localhost:11434",
  model: "llama3",
  format: "json",  // ✅ Simple flag for JSON mode
});
```

**Our Current Implementation** (`entity_extractor.py:44`):
```python
json={
    "model": self.model,
    "format": "json",  # ✅ CORRECT for JSON mode
    "prompt": prompt
}
```

**HOWEVER**:
According to benchmarking results (JSON_SCHEMA_SUCCESS_REPORT.md), we need **JSON Schema constraint**, not just flag:

```python
PERSON_SCHEMA = {
    "type": "array",
    "items": {...}
}

json={
    "format": PERSON_SCHEMA,  # ✅ Schema constraint for array output
    "prompt": prompt
}
```

---

## 🎯 **What Needs to Happen for Ollama Autoscaling**

### Option A: Use Existing Autoscaler Infrastructure (Recommended)

**Pros**:
- ✅ Infrastructure already exists
- ✅ HAProxy + Prometheus + Grafana ready
- ✅ CPU-based scaling logic implemented
- ✅ Health checks built-in

**Cons**:
- ⚠️ Autoscaler currently failing (needs debugging)
- ⚠️ Requires NFS for shared models
- ⚠️ Ollama config needs updating

**Implementation Steps**:

#### Step 1: Fix Autoscaler (1 hour)
```bash
# Check autoscaler logs
ssh wizardsofts@10.0.0.84 "docker logs autoscaler --tail 100"

# Common issues:
# - Missing /app/id_rsa SSH key
# - Config validation errors
# - Docker socket permissions
```

#### Step 2: Setup NFS for Ollama Models (1 hour)
```bash
# Server 80 (NFS server)
sudo apt install nfs-kernel-server -y
sudo mkdir -p /opt/ollama-models
sudo chown -R 1000:1000 /opt/ollama-models
echo "/opt/ollama-models 10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server

# Server 84 (NFS client)
sudo apt install nfs-common -y
sudo mkdir -p /opt/ollama-models
echo "10.0.0.80:/opt/ollama-models /opt/ollama-models nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
sudo mount -a
```

#### Step 3: Update Autoscaler Config (30 min)

**File**: `infrastructure/auto-scaling/config.yaml`

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    port: 11434
    min_replicas: 1      # ✅ Always 1 instance minimum
    max_replicas: 4      # ✅ Scale up to 4 instances
    scale_up_threshold: 70   # Scale up when CPU > 70%
    scale_down_threshold: 20 # Scale down when CPU < 20%
    cooldown_period: 120     # 2 minutes between scaling
    business_hours_only: false # ✅ Always available
    health_check:
      path: /api/tags
      interval: 10
      timeout: 5
    volumes:
      - /opt/ollama-models:/root/.ollama:ro  # ✅ Read-only NFS mount
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_MODELS=/root/.ollama
```

#### Step 4: Pull mistral:7b on NFS (Server 80 only)
```bash
# Create temporary RW Ollama container on Server 80
docker run -d --name ollama-temp \
  -v /opt/ollama-models:/root/.ollama \
  ollama/ollama:latest

# Pull model
docker exec ollama-temp ollama pull mistral:7b

# Verify
docker exec ollama-temp ollama list
# mistral:7b should appear

# Stop temp container
docker stop ollama-temp && docker rm ollama-temp
```

#### Step 5: Deploy via Autoscaler API (30 min)
```bash
# Reload config
curl -X POST http://10.0.0.84:8000/config/reload

# Check service status
curl http://10.0.0.84:8000/services/ollama/stats

# Manually scale up to test
curl -X POST http://10.0.0.84:8000/services/ollama/scale/up

# Verify containers deployed
curl http://10.0.0.84:8000/services/ollama/stats
# Should show 2 containers now
```

#### Step 6: Traefik Load Balancer Config (30 min)

**File**: `traefik/dynamic_conf.yml`

**Add Ollama service**:
```yaml
http:
  routers:
    ollama:
      rule: "Host(`ollama.local`) || PathPrefix(`/api/`)"
      service: ollama
      entryPoints:
        - web

  services:
    ollama:
      loadBalancer:
        servers:
          # HAProxy will manage these dynamically via autoscaler
          - url: "http://10.0.0.84:8404"  # HAProxy frontend
        healthCheck:
          path: /api/version
          interval: "10s"
          timeout: "3s"
```

**OR** use HAProxy directly:
```yaml
# HAProxy managed by autoscaler
# Traefik → HAProxy → Ollama containers (1-4 instances)
```

---

### Option B: Simple Docker Compose Scaling (Quick & Dirty)

**If autoscaler is too complex**, use `docker-compose scale`:

**File**: `infrastructure/ollama/docker-compose.yml`

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - /opt/ollama-models:/root/.ollama:ro
    environment:
      - OLLAMA_HOST=0.0.0.0
    deploy:
      replicas: 2  # ✅ Deploy 2 instances initially
      resources:
        limits:
          memory: 16G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 10s
      timeout: 5s
```

**Manual Scaling**:
```bash
# Scale to 4 instances
docker-compose up -d --scale ollama=4

# Scale down to 1
docker-compose up -d --scale ollama=1
```

**Traefik Auto-Discovery**:
```yaml
# Add labels to docker-compose.yml
services:
  ollama:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ollama.rule=PathPrefix(`/api/`)"
      - "traefik.http.services.ollama.loadbalancer.server.port=11434"
      - "traefik.http.services.ollama.loadbalancer.healthcheck.path=/api/version"
```

**Traefik will automatically**:
- Discover all ollama containers
- Add them to load balancer
- Remove unhealthy instances

---

### Option C: Docker Swarm Native Scaling (Most Integrated)

**Since Swarm is ACTIVE**, use native Swarm scaling:

```bash
# Enable Swarm mode in Traefik (change config)
# traefik.yml:
providers:
  docker:
    swarmMode: true  # ✅ Enable Swarm

# Deploy as Swarm service
docker service create \
  --name ollama \
  --replicas 2 \
  --mount type=bind,source=/opt/ollama-models,target=/root/.ollama,readonly \
  --publish 11434:11434 \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.ollama.rule=PathPrefix(`/api/`)" \
  --label "traefik.http.services.ollama.loadbalancer.server.port=11434" \
  ollama/ollama:latest

# Scale dynamically
docker service scale ollama=4  # Scale to 4
docker service scale ollama=1  # Scale to 1

# Swarm handles:
# - Load balancing (ingress network)
# - Health checks
# - Rolling updates
# - Auto-restart
```

**Traefik + Swarm**:
- Traefik discovers Swarm services automatically
- Load balances across all replicas
- Updates routing on scale up/down

---

## 🏆 **Recommended Approach**

### **Option C: Docker Swarm** (Best for your setup)

**Why**:
1. ✅ Swarm already active
2. ✅ Traefik supports Swarm mode (just enable it)
3. ✅ Native autoscaling via `docker service scale`
4. ✅ No custom autoscaler complexity
5. ✅ Built-in health checks and load balancing

**Implementation** (30 min):

```bash
# 1. Enable Swarm mode in Traefik
sed -i 's/swarmMode: false/swarmMode: true/' traefik/traefik.yml
docker restart traefik

# 2. Create overlay network
docker network create --driver overlay --attachable ollama-network

# 3. Deploy Ollama as Swarm service
docker service create \
  --name ollama \
  --replicas 1 \
  --network ollama-network \
  --mount type=bind,source=/opt/ollama-models,target=/root/.ollama \
  --label "traefik.enable=true" \
  --label "traefik.docker.network=ollama-network" \
  --label "traefik.http.routers.ollama.rule=PathPrefix(`/api/`)" \
  --label "traefik.http.services.ollama.loadbalancer.server.port=11434" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.path=/api/version" \
  --constraint 'node.labels.ollama==true' \
  ollama/ollama:latest

# 4. Test autoscaling
docker service scale ollama=4

# 5. Monitor
docker service ps ollama
curl http://10.0.0.84/api/tags  # Traefik load balances across replicas
```

**Autoscaling Trigger** (CPU-based, requires metrics):
- Use Prometheus + custom script
- OR use Docker Swarm mode constraints
- OR manual scaling via CLI/API

---

## 📊 **Comparison Matrix**

| Aspect | Option A (Custom Autoscaler) | Option B (Compose) | Option C (Swarm) ⭐ |
|--------|------------------------------|--------------------|--------------------|
| **Setup Time** | 4 hours | 1 hour | 30 min |
| **Complexity** | High | Low | Medium |
| **Auto-scaling** | Yes (CPU) | Manual only | Manual + scripted |
| **Load Balancing** | HAProxy + Traefik | Traefik only | Traefik + Swarm Ingress |
| **Health Checks** | Custom | Docker | Docker + Swarm |
| **Monitoring** | Prometheus + Grafana | Basic | Swarm metrics + Prometheus |
| **Maintainability** | Complex | Simple | Moderate |
| **Current Status** | ❌ Broken | N/A | ✅ Ready (Swarm active) |

---

## 🎯 **Final Recommendation**

### **Immediate**: Use Option C (Docker Swarm)
- Swarm already active
- Traefik supports it (1-line config change)
- Native load balancing
- Simple scaling commands

### **Medium-term**: Fix Option A (Custom Autoscaler)
- Debug autoscaler restart issue
- Implement full CPU-based autoscaling
- Add business hours logic

### **Long-term**: Evaluate Kubernetes
- If scaling needs grow beyond 10+ services
- If multi-cluster management needed
- If advanced scheduling required

---

## ✅ **Updated Action Plan**

### Phase 0: Swarm-Based Ollama Scaling (30 min)
1. Enable Traefik Swarm mode
2. Deploy Ollama as Swarm service (1 replica)
3. Setup NFS (parallel task)
4. Pull mistral:7b to NFS
5. Scale to 4 replicas
6. Test load balancing

### Phase 1: Hadith Extraction Setup (2 hours)
1. Update model to mistral:7b in configs
2. Implement JSON schema constraint (not just flag)
3. Remove Arabic fields
4. Fix evaluation metrics (entity matching)

### Phase 2: Testing (2 hours)
1. Single hadith test
2. 10-hadith batch
3. Verify Ollama load distribution

### Phase 3: Full Extraction (3 hours)
1. Ray distributed extraction (200 hadiths)
2. Monitor Ollama autoscaling
3. Evaluate results

---

**Document Owner**: Claude Sonnet 4.5
**Last Updated**: 2026-01-05
**Status**: Reality Check Complete - Swarm Recommended

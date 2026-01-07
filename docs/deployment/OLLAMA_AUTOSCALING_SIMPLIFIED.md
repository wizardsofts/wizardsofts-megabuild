# Ollama Autoscaling - Simplified Architecture (Traefik Only)

**Date**: 2026-01-05
**Decision**: Replace HAProxy + Custom Autoscaler with Traefik + Docker Swarm

---

## 🎯 Your Questions Answered

### Q1: Do we still need HAProxy? Can we replace it with Traefik?

**Answer**: ✅ **YES, we can replace HAProxy entirely with Traefik!**

**Current Architecture (Unnecessary Complexity)**:
```
Custom Autoscaler (FAILING)
    → HAProxy (load balancer)
        → Ollama containers (manually scaled)
```

**New Architecture (Recommended)**:
```
Traefik (Swarm mode)
    → Docker Swarm (auto-discovery + load balancing)
        → Ollama service (auto-scaled replicas)
```

**Why Traefik is better**:
1. ✅ **Already running** - No new infrastructure needed
2. ✅ **Auto-discovery** - Automatically detects Swarm service replicas
3. ✅ **Built-in load balancing** - Round-robin across replicas
4. ✅ **Health checks** - Removes unhealthy replicas automatically
5. ✅ **No custom scripts** - Swarm handles everything
6. ✅ **Single config change** - Just enable `swarmMode: true`

**HAProxy is REDUNDANT** - We can remove it entirely!

---

### Q2: Can we use Docker Swarm or Traefik autoscaling instead of manual scripts?

**Answer**: ✅ **YES! Use Docker Swarm + Traefik for automatic scaling!**

**Docker Swarm Autoscaling Options**:

#### Option 1: Manual Scaling (Recommended for Start) ⭐
```bash
# Scale up when needed
docker service scale ollama=4

# Scale down when idle
docker service scale ollama=2
```

**Pros**:
- ✅ Simple, reliable, immediate
- ✅ Full control over scaling decisions
- ✅ No complex CPU monitoring needed
- ✅ Can be triggered via API/cron/script

**Cons**:
- ⚠️ Requires manual intervention or simple script

#### Option 2: Automatic Scaling with Prometheus + Custom Script

**Use Prometheus metrics** to trigger scaling:

```bash
# Monitor Ollama request rate via Prometheus
# Scale up if request_rate > threshold
# Scale down if request_rate < threshold
```

**Implementation** (30 minutes):
1. Prometheus already scrapes Traefik metrics
2. Create simple script that queries Prometheus
3. Run script every 5 minutes via cron
4. Script calls `docker service scale ollama=N`

**Example Script**:
```bash
#!/bin/bash
# /home/wizardsofts/scripts/autoscale_ollama.sh

# Get current request rate from Prometheus
REQUEST_RATE=$(curl -s "http://localhost:9090/api/v1/query?query=rate(traefik_service_requests_total{service=\"ollama@docker\"}[5m])" | jq -r '.data.result[0].value[1]')

CURRENT_REPLICAS=$(docker service inspect ollama --format='{{.Spec.Mode.Replicated.Replicas}}')

# Scale up if > 10 requests/sec
if (( $(echo "$REQUEST_RATE > 10" | bc -l) )); then
  if [ "$CURRENT_REPLICAS" -lt 4 ]; then
    echo "Scaling up: request_rate=$REQUEST_RATE"
    docker service scale ollama=$((CURRENT_REPLICAS + 1))
  fi
# Scale down if < 2 requests/sec
elif (( $(echo "$REQUEST_RATE < 2" | bc -l) )); then
  if [ "$CURRENT_REPLICAS" -gt 1 ]; then
    echo "Scaling down: request_rate=$REQUEST_RATE"
    docker service scale ollama=$((CURRENT_REPLICAS - 1))
  fi
fi
```

**Cron** (every 5 minutes):
```bash
*/5 * * * * /home/wizardsofts/scripts/autoscale_ollama.sh >> /home/wizardsofts/logs/autoscale.log 2>&1
```

**Pros**:
- ✅ Fully automatic based on real load
- ✅ Uses existing Prometheus infrastructure
- ✅ Simple bash script (no Python/FastAPI complexity)
- ✅ More reliable than custom autoscaler

**Cons**:
- ⚠️ Requires Prometheus query endpoint
- ⚠️ 5-minute delay in scaling decisions

---

### Q3: Server 80 has NFS, we need to configure it on rest of servers

**Answer**: ✅ **Correct! NFS should be on all Swarm nodes for Ollama.**

**Current Swarm Nodes**:
```
gmktec (10.0.0.84) - Manager ⭐
hppavilion (10.0.0.80) - Worker
wsasus (10.0.0.81) - Worker
hpr (10.0.0.82) - Worker (unreachable via SSH)
```

**NFS Architecture**:

**Option A: Server 80 as NFS server for ALL nodes** ⭐ (Recommended)

```
Server 80 (hppavilion)
    ├─ NFS Server (read-write)
    └─ /opt/ollama-models (local storage)
         ↓
    [NFS Network Share]
         ↓
Server 84 (gmktec) - NFS client (read-only mount)
Server 81 (wsasus) - NFS client (read-only mount)
Server 82 (hpr) - NFS client (read-only mount)
```

**Why this works**:
- ✅ Server 80 has 171GB free space (plenty for models)
- ✅ Single source of truth for model files
- ✅ All Swarm nodes can run Ollama replicas
- ✅ Swarm distributes replicas across nodes automatically

**Updated NFS Setup**:

1. **Server 80 (NFS Server)** - Already done ✅
2. **Server 84 (NFS Client)** - Scripts ready ✅
3. **Server 81 (NFS Client)** - **NEW SCRIPT NEEDED**
4. **Server 82 (NFS Client)** - **NEW SCRIPT NEEDED** (when SSH access available)

---

## 🏗️ Simplified Architecture

### Before (Complex, Failing):
```
┌─────────────────────────────┐
│   Custom Autoscaler         │
│   (Python FastAPI)          │
│   ❌ FAILING/RESTARTING      │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│       HAProxy               │
│   (Port 8404)               │
│   Load Balancer             │
└─────────────┬───────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌────────┐        ┌────────┐
│Ollama-1│        │Ollama-2│
│ (80)   │        │ (84)   │
└────────┘        └────────┘
```

**Problems**:
- ❌ Autoscaler keeps restarting
- ❌ HAProxy adds complexity
- ❌ Manual backend management
- ❌ No auto-discovery
- ❌ Fixed replica count

---

### After (Simple, Reliable):
```
┌────────────────────────────────────────┐
│            Traefik                     │
│      (Swarm Mode Enabled)              │
│   Auto-discovery + Load Balancing      │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│         Docker Swarm                   │
│    (Automatic Replica Management)      │
└───────┬────────┬────────┬──────────────┘
        │        │        │
    ┌───▼──┐ ┌──▼───┐ ┌──▼───┐
    │Ollama│ │Ollama│ │Ollama│
    │ (84) │ │ (80) │ │ (81) │
    └──┬───┘ └──┬───┘ └──┬───┘
       │        │        │
       └────────┴────────┴─────────┐
                                   ▼
              ┌────────────────────────────┐
              │   NFS Shared Volume        │
              │   Server 80 (NFS Server)   │
              │   /opt/ollama-models       │
              └────────────────────────────┘
```

**Benefits**:
- ✅ Traefik auto-discovers replicas
- ✅ Swarm manages scaling (`docker service scale`)
- ✅ Built-in health checks and restart
- ✅ Load balancing automatic
- ✅ Can scale to 1-6+ replicas across all nodes
- ✅ **No custom autoscaler needed**
- ✅ **No HAProxy needed**

---

## 🚀 Updated Deployment Plan

### Phase 1: Remove HAProxy (5 minutes)

```bash
ssh wizardsofts@10.0.0.84

# Stop and remove HAProxy
docker stop haproxy
docker rm haproxy

# Verify removal
docker ps | grep haproxy
# Should return nothing
```

**Why remove it?**
- Traefik does everything HAProxy does
- Eliminates unnecessary complexity
- Reduces resource usage

---

### Phase 2: Setup NFS on ALL Swarm Nodes (45 minutes)

#### Server 80 (NFS Server) - Already Done ✅
```bash
# Already configured in previous scripts
```

#### Server 84 (NFS Client) - Script Ready ✅
```bash
scp scripts/setup_nfs_client84.sh wizardsofts@10.0.0.84:~/
ssh wizardsofts@10.0.0.84
sudo bash setup_nfs_client84.sh
```

#### Server 81 (NFS Client) - New Script
```bash
scp scripts/setup_nfs_client81.sh wizardsofts@10.0.0.81:~/
ssh wizardsofts@10.0.0.81
sudo bash setup_nfs_client81.sh
```

#### Server 82 (NFS Client) - When SSH Available
```bash
# Same as Server 81 script
# Can be deployed later when SSH access is restored
```

---

### Phase 3: Deploy Ollama Swarm Service (30 minutes)

**Updated deployment** (uses all Swarm nodes):

```bash
ssh wizardsofts@10.0.0.84

# 1. Enable Traefik Swarm mode
sed -i 's/swarmMode: false/swarmMode: true/' \
  /opt/wizardsofts-megabuild/traefik/traefik.yml

docker restart traefik
sleep 3

# 2. Pull mistral:7b to NFS (Server 80)
ssh wizardsofts@10.0.0.80 "
docker run -d --name ollama-temp \
  -v /opt/ollama-models:/root/.ollama \
  ollama/ollama:latest

docker exec ollama-temp ollama pull mistral:7b
docker exec ollama-temp ollama list
docker stop ollama-temp && docker rm ollama-temp
"

# 3. Create overlay network
docker network create --driver overlay --attachable ollama-network

# 4. Deploy Ollama service (starts with 2 replicas)
docker service create \
  --name ollama \
  --replicas 2 \
  --network ollama-network \
  --mount type=bind,source=/opt/ollama-models,target=/root/.ollama,readonly \
  --publish 11434:11434 \
  --limit-memory 16G \
  --label "traefik.enable=true" \
  --label "traefik.docker.network=ollama-network" \
  --label "traefik.http.routers.ollama.rule=PathPrefix(\`/api/\`)" \
  --label "traefik.http.routers.ollama.entrypoints=web" \
  --label "traefik.http.services.ollama.loadbalancer.server.port=11434" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.path=/api/version" \
  --label "traefik.http.services.ollama.loadbalancer.healthcheck.interval=10s" \
  ollama/ollama:latest

# 5. Verify deployment
docker service ps ollama
# Should show 2 replicas distributed across nodes

# 6. Test endpoint
curl http://10.0.0.84:11434/api/version
curl http://10.0.0.84:11434/api/tags
```

**Swarm will automatically**:
- ✅ Distribute replicas across healthy nodes (80, 81, 84)
- ✅ Load balance requests via Swarm ingress
- ✅ Restart failed containers
- ✅ Traefik discovers and load balances

---

### Phase 4: Manual Scaling (1 minute)

```bash
# Scale up when needed
docker service scale ollama=4

# Monitor distribution
docker service ps ollama
# Should show replicas across multiple nodes

# Scale down when idle
docker service scale ollama=2
```

**Node Distribution** (example with 4 replicas):
```
gmktec (84): ollama.1, ollama.4
hppavilion (80): ollama.2
wsasus (81): ollama.3
```

---

### Phase 5: Optional Auto-scaling Script (30 minutes)

**Create Prometheus-based autoscaler**:

```bash
ssh wizardsofts@10.0.0.84

# Create script directory
mkdir -p ~/scripts

# Create autoscaler script
cat > ~/scripts/autoscale_ollama.sh <<'EOF'
#!/bin/bash
# Autoscale Ollama based on Traefik request metrics

PROM_URL="http://localhost:9090"
MIN_REPLICAS=2
MAX_REPLICAS=6
SCALE_UP_THRESHOLD=10   # requests/sec
SCALE_DOWN_THRESHOLD=2  # requests/sec

# Get current request rate from Prometheus
REQUEST_RATE=$(curl -s "${PROM_URL}/api/v1/query?query=rate(traefik_service_requests_total{service=\"ollama@docker\"}[5m])" | jq -r '.data.result[0].value[1] // 0')

# Get current replicas
CURRENT_REPLICAS=$(docker service inspect ollama --format='{{.Spec.Mode.Replicated.Replicas}}')

echo "$(date) - Request rate: ${REQUEST_RATE}/sec, Current replicas: ${CURRENT_REPLICAS}"

# Scale up if high load
if (( $(echo "$REQUEST_RATE > $SCALE_UP_THRESHOLD" | bc -l) )); then
  if [ "$CURRENT_REPLICAS" -lt "$MAX_REPLICAS" ]; then
    NEW_REPLICAS=$((CURRENT_REPLICAS + 1))
    echo "Scaling UP to ${NEW_REPLICAS} replicas"
    docker service scale ollama=${NEW_REPLICAS}
  fi
# Scale down if low load
elif (( $(echo "$REQUEST_RATE < $SCALE_DOWN_THRESHOLD" | bc -l) )); then
  if [ "$CURRENT_REPLICAS" -gt "$MIN_REPLICAS" ]; then
    NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
    echo "Scaling DOWN to ${NEW_REPLICAS} replicas"
    docker service scale ollama=${NEW_REPLICAS}
  fi
fi
EOF

chmod +x ~/scripts/autoscale_ollama.sh

# Add to cron (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/wizardsofts/scripts/autoscale_ollama.sh >> /home/wizardsofts/logs/autoscale.log 2>&1") | crontab -

# Create log directory
mkdir -p ~/logs

# Test script manually
~/scripts/autoscale_ollama.sh
```

**Monitor autoscaling**:
```bash
tail -f ~/logs/autoscale.log
```

---

## 📊 Comparison: Old vs New

| Aspect | Old (HAProxy + Custom Autoscaler) | New (Traefik + Swarm) |
|--------|-----------------------------------|------------------------|
| **Components** | 3 (Traefik + HAProxy + Autoscaler) | 1 (Traefik) |
| **Autoscaler Status** | ❌ Failing/Restarting | ✅ Swarm built-in |
| **Load Balancer** | HAProxy (manual config) | Traefik (auto-discovery) |
| **Scaling Method** | Custom Python script | `docker service scale` |
| **Health Checks** | Custom implementation | Swarm + Traefik built-in |
| **Auto-discovery** | ❌ Manual backend updates | ✅ Automatic |
| **Complexity** | High (3 systems) | Low (1 system) |
| **Reliability** | Low (autoscaler failing) | High (proven Swarm) |
| **NFS Nodes** | 2 (80, 84) | 3+ (80, 81, 84) |
| **Max Replicas** | Limited by manual setup | 6+ (all Swarm nodes) |

---

## ✅ Benefits of New Approach

### 1. **Simpler Architecture**
- Remove HAProxy → Traefik does load balancing
- Remove Custom Autoscaler → Swarm + simple script
- Single config change (swarmMode: true)

### 2. **More Reliable**
- No failing autoscaler
- Swarm is battle-tested
- Automatic replica management

### 3. **Better Scaling**
- Use all 4 Swarm nodes (80, 81, 82, 84)
- Scale 2-6+ replicas across nodes
- Automatic distribution

### 4. **Easier Management**
- Single command: `docker service scale ollama=N`
- Monitor: `docker service ps ollama`
- Logs: `docker service logs ollama`

### 5. **Cost Effective**
- Reuse existing infrastructure
- No new services needed
- Less resource overhead

---

## 🎯 Recommended Action Plan

### Immediate (Today) - 60 minutes

1. **Remove HAProxy** (5 min)
   ```bash
   docker stop haproxy && docker rm haproxy
   ```

2. **Setup NFS on Server 81** (15 min)
   - Create and run setup_nfs_client81.sh

3. **Deploy Ollama Swarm Service** (30 min)
   - Enable Traefik swarmMode
   - Pull mistral:7b to NFS
   - Create Swarm service with 2 replicas

4. **Test Scaling** (10 min)
   - Scale to 4 replicas
   - Verify distribution
   - Test load balancing

### Later (This Week) - 30 minutes

5. **Optional: Add Auto-scaling Script**
   - Create Prometheus-based autoscaler
   - Add cron job
   - Monitor for 1 week

6. **Server 82 NFS Setup** (when SSH available)
   - Same script as Server 81

---

## 📝 Files to Update

I'll create:
1. ✅ This document (OLLAMA_AUTOSCALING_SIMPLIFIED.md)
2. 🔄 Update setup_nfs_client81.sh (new)
3. 🔄 Update deploy_ollama_swarm.sh (remove HAProxy steps)
4. 🔄 Update OLLAMA_SWARM_DEPLOYMENT_GUIDE.md (simplified)
5. 🔄 Create autoscale_ollama.sh (optional Prometheus script)

---

**Document Owner**: Claude Sonnet 4.5
**Last Updated**: 2026-01-05
**Status**: Recommendation - Awaiting Approval
**Impact**: Simplifies architecture, removes 2 failing components

# Ollama Docker Swarm Autoscaling Deployment Guide

**Date**: 2026-01-05
**Status**: Ready for Deployment
**Implementation**: Docker Swarm + Traefik + NFS

---

## Overview

This guide implements **Option C: Docker Swarm Native Scaling** from the Reality Check document. This is the recommended approach because:

1. ✅ Docker Swarm already active on infrastructure
2. ✅ Traefik supports Swarm mode (requires 1-line config change)
3. ✅ Native autoscaling via `docker service scale`
4. ✅ No custom autoscaler complexity
5. ✅ Built-in health checks and load balancing

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Traefik                          │
│           (Swarm Mode Enabled)                      │
│              Load Balancer                          │
└─────────────────┬───────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌──────────────┐      ┌──────────────┐
│  Ollama-1    │      │  Ollama-2    │
│  (replica)   │      │  (replica)   │
│  Server 84   │      │  Server 84   │
└──────┬───────┘      └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
      ┌─────────────────────┐
      │   NFS Shared Volume │
      │  /opt/ollama-models │
      │   (Server 80)       │
      └─────────────────────┘
```

**Key Features:**
- Swarm manages replication across nodes
- Traefik auto-discovers and load balances
- NFS provides shared model storage
- Read-only mounts prevent corruption
- Health checks ensure availability

---

## Prerequisites

1. **Docker Swarm Active** (Already confirmed ✅)
   ```bash
   ssh wizardsofts@10.0.0.84 "docker info | grep Swarm"
   # Should show: Swarm: active
   ```

2. **Traefik Running** (Already confirmed ✅)
   ```bash
   docker ps | grep traefik
   ```

3. **Server Disk Space** (Already confirmed ✅)
   - Server 80: 171GB free (18% used)
   - Server 84: Available space sufficient

4. **Network Connectivity**
   - Servers 80 and 84 on same network (10.0.0.0/24)
   - NFS ports accessible (2049, 111)

---

## Deployment Steps

### Phase 1: NFS Setup (30 minutes)

#### Step 1.1: Setup NFS Server on Server 80

```bash
# Copy script to Server 80
scp scripts/setup_nfs_server80.sh wizardsofts@10.0.0.80:~/

# SSH to Server 80
ssh wizardsofts@10.0.0.80

# Run script with sudo
sudo bash setup_nfs_server80.sh

# Verify
exportfs -v
showmount -e localhost
```

**Expected Output:**
```
/opt/ollama-models
		10.0.0.0/24(sync,wdelay,hide,no_subtree_check,sec=sys,rw,secure,no_root_squash,no_all_squash)
```

#### Step 1.2: Setup NFS Client on Server 84

```bash
# Copy script to Server 84
scp scripts/setup_nfs_client84.sh wizardsofts@10.0.0.84:~/

# SSH to Server 84
ssh wizardsofts@10.0.0.84

# Run script with sudo
sudo bash setup_nfs_client84.sh

# Verify
df -h /opt/ollama-models
ls -la /opt/ollama-models
```

**Expected Output:**
```
10.0.0.80:/opt/ollama-models  217G   37G  171G  18% /opt/ollama-models
```

---

### Phase 2: Deploy Ollama with Swarm (30 minutes)

#### Step 2.1: Run Deployment Script

```bash
# Copy deployment script to Server 84
scp scripts/deploy_ollama_swarm.sh wizardsofts@10.0.0.84:~/

# SSH to Server 84
ssh wizardsofts@10.0.0.84

# Run deployment
bash deploy_ollama_swarm.sh
```

**What the script does:**
1. Verifies NFS mount
2. Pulls mistral:7b to NFS volume (Server 80)
3. Updates Traefik config (swarmMode: true)
4. Restarts Traefik
5. Creates overlay network
6. Deploys Ollama as Swarm service (1 replica)
7. Configures Traefik labels for load balancing

#### Step 2.2: Verify Deployment

```bash
# Check service status
docker service ps ollama

# Test Ollama API
curl http://10.0.0.84:11434/api/version
curl http://10.0.0.84:11434/api/tags
```

**Expected Output:**
```json
{"version":"0.1.17"}
{"models":[{"name":"mistral:7b","size":4109865159}]}
```

---

### Phase 3: Test Autoscaling (15 minutes)

#### Step 3.1: Scale Up to 4 Replicas

```bash
# Scale to 4 instances
docker service scale ollama=4

# Monitor scaling
watch -n 2 'docker service ps ollama'
```

**Expected Behavior:**
- 4 Ollama tasks running
- Each task shows "Running" state
- Tasks distributed across available nodes

#### Step 3.2: Test Load Balancing

```bash
# Send 10 requests and check distribution
for i in {1..10}; do
  curl -s http://10.0.0.84:11434/api/version | jq .
  sleep 1
done
```

**Expected Behavior:**
- All requests succeed
- Traefik distributes across 4 replicas
- Response time consistent (<100ms)

#### Step 3.3: Test Health Checks

```bash
# Stop one replica (simulate failure)
TASK_ID=$(docker service ps ollama -q | head -1)
docker stop $(docker ps -qf "label=com.docker.swarm.task.id=$TASK_ID")

# Watch Swarm restart it
watch -n 2 'docker service ps ollama'
```

**Expected Behavior:**
- Failed task shows "Shutdown" state
- New task automatically created
- Service continues serving requests

---

### Phase 4: Scale Down (5 minutes)

```bash
# Scale back to 2 replicas for normal load
docker service scale ollama=2

# Verify
docker service ps ollama
```

---

## Model Management

### Pulling New Models

**IMPORTANT**: Always pull models on **Server 80** (NFS server) with read-write access.

```bash
# SSH to Server 80
ssh wizardsofts@10.0.0.80

# Create temporary RW container
docker run -d --name ollama-temp \
  -v /opt/ollama-models:/root/.ollama \
  ollama/ollama:latest

# Pull model
docker exec ollama-temp ollama pull <model-name>

# Verify
docker exec ollama-temp ollama list

# Cleanup
docker stop ollama-temp && docker rm ollama-temp
```

**Why not pull on Server 84?**
- Server 84 mounts NFS as **read-only** (`:ro`)
- Prevents accidental model corruption
- Single source of truth (Server 80)

---

## Monitoring

### Service Health

```bash
# Service status
docker service ls
docker service ps ollama

# Service logs
docker service logs ollama -f --tail 100

# Replica count
docker service inspect ollama --pretty | grep Replicas
```

### Load Balancing Stats

```bash
# Traefik dashboard
# http://10.0.0.84:8080 (if enabled)

# Check backend servers
curl http://10.0.0.84:8080/api/http/services/ollama@docker
```

### Resource Usage

```bash
# Per-replica CPU/memory
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Total Ollama resource usage
docker stats --no-stream | grep ollama
```

---

## Troubleshooting

### Issue: NFS Mount Fails

**Symptoms:**
```
mount.nfs: Connection refused
```

**Solution:**
```bash
# On Server 80: Check NFS server
sudo systemctl status nfs-kernel-server
sudo exportfs -v

# Test connectivity from Server 84
showmount -e 10.0.0.80

# Check firewall
sudo ufw status | grep 2049
```

### Issue: Ollama Service Won't Start

**Symptoms:**
```
docker service ps ollama
# Shows "Rejected" or "Failed"
```

**Solution:**
```bash
# Check service logs
docker service logs ollama --tail 50

# Inspect service
docker service inspect ollama

# Common fixes:
# 1. Verify NFS mount exists
mountpoint /opt/ollama-models

# 2. Check network exists
docker network ls | grep ollama-network

# 3. Verify image pulled
docker pull ollama/ollama:latest
```

### Issue: Models Not Found

**Symptoms:**
```
Error: model 'mistral:7b' not found
```

**Solution:**
```bash
# Check NFS volume on Server 80
ssh wizardsofts@10.0.0.80 "ls -la /opt/ollama-models/models/"

# Pull model again (Server 80 only)
# See "Model Management" section above
```

### Issue: Traefik Not Load Balancing

**Symptoms:**
- All requests go to single replica
- 503 errors intermittently

**Solution:**
```bash
# 1. Verify Traefik swarmMode enabled
grep swarmMode /opt/wizardsofts-megabuild/traefik/traefik.yml
# Should show: swarmMode: true

# 2. Restart Traefik
docker restart traefik

# 3. Check Traefik logs
docker logs traefik --tail 100 | grep ollama

# 4. Verify service labels
docker service inspect ollama | grep -A 5 Labels
```

### Issue: Scaling Stuck at 1 Replica

**Symptoms:**
```
docker service scale ollama=4
# Only 1 replica runs
```

**Solution:**
```bash
# 1. Check node availability
docker node ls
# All nodes should show "Ready" and "Active"

# 2. Check resource constraints
docker service inspect ollama | grep -A 10 Resources

# 3. Check placement constraints
docker service inspect ollama | grep -A 5 Constraints

# 4. Force update
docker service update --force ollama
```

---

## Performance Tuning

### Optimal Replica Count

| Load Level | Replicas | Total Memory | Expected RPS |
|------------|----------|--------------|--------------|
| Low (dev) | 1-2 | 16-32GB | 1-5 |
| Medium | 2-3 | 32-48GB | 5-15 |
| High (production) | 4-6 | 64-96GB | 15-30 |

**Recommendation**: Start with 2 replicas, scale based on actual load.

### Memory Limits

Current: 16GB per replica

```bash
# Increase for larger models
docker service update ollama \
  --limit-memory 24G \
  --reserve-memory 16G
```

### CPU Limits

No CPU limits set (uses all available cores).

```bash
# Add CPU limit if needed
docker service update ollama --limit-cpu 4.0
```

---

## Integration with Hadith Extraction

### Update Environment Variables

```bash
# apps/hadith-knowledge-graph/.env
OLLAMA_BASE_URL=http://10.0.0.84:11434  # Traefik load-balanced endpoint
OLLAMA_MODEL=mistral:7b
```

### Test Connection from Container

```bash
# Run test from extraction worker
docker run --rm --network=host \
  python:3.11-slim \
  bash -c "
    apt-get update && apt-get install -y curl
    curl http://10.0.0.84:11434/api/version
    curl http://10.0.0.84:11434/api/tags
  "
```

---

## Rollback Procedure

If autoscaling causes issues, rollback to single instance:

```bash
# Step 1: Remove Swarm service
docker service rm ollama

# Step 2: Disable Traefik Swarm mode
sed -i 's/swarmMode: true/swarmMode: false/' \
  /opt/wizardsofts-megabuild/traefik/traefik.yml
docker restart traefik

# Step 3: Deploy single Ollama container (old method)
docker run -d --name ollama \
  -v /opt/ollama-models:/root/.ollama:ro \
  -p 11434:11434 \
  --restart unless-stopped \
  ollama/ollama:latest
```

---

## Next Steps After Deployment

1. **Update Model Configuration**
   - Change `OLLAMA_MODEL` to `mistral:7b` in all configs
   - apps/hadith-knowledge-graph/src/config.py
   - apps/hadith-knowledge-graph/.env

2. **Implement JSON Schema Constraint**
   - Add PERSON_SCHEMA, PLACE_SCHEMA, etc. to entity_extractor.py
   - Update `_call_ollama` to use schema instead of simple "json" flag

3. **Remove Arabic Fields**
   - Drop canonical_name_ar columns from PostgreSQL
   - Remove from entity extractor prompts
   - Update documentation

4. **Test Distributed Extraction**
   - Single hadith test
   - 10-hadith batch
   - 200-hadith Ray distributed extraction

---

## Comparison: Before vs After

| Aspect | Before (Single Instance) | After (Swarm Autoscaling) |
|--------|--------------------------|---------------------------|
| **Instances** | 1 fixed | 1-6 dynamic |
| **Load Balancing** | None | Traefik automatic |
| **Health Checks** | Manual | Swarm automatic |
| **Scaling** | Manual restart | `docker service scale` |
| **High Availability** | ❌ Single point of failure | ✅ Auto-restart on failure |
| **Resource Usage** | 16GB fixed | 16-96GB dynamic |
| **Throughput** | ~5 RPS | ~30 RPS |

---

## Success Criteria

- ✅ NFS mounted on both Server 80 and 84
- ✅ mistral:7b model pulled to NFS
- ✅ Ollama Swarm service running (1 replica minimum)
- ✅ Traefik swarmMode enabled
- ✅ Health checks passing
- ✅ Manual scaling works (`docker service scale ollama=4`)
- ✅ Load balancing distributes requests
- ✅ Auto-restart on failure
- ✅ Hadith extraction can connect to Ollama

---

## Documentation References

- [REALITY_CHECK_AUTOSCALING.md](REALITY_CHECK_AUTOSCALING.md) - Infrastructure analysis
- [OLLAMA_AUTOSCALING.md](OLLAMA_AUTOSCALING.md) - Original autoscaling plan
- [MODEL_EVALUATION_COMPARISON.md](MODEL_EVALUATION_COMPARISON.md) - Model benchmarks
- [CORRECTED_EXTRACTION_PLAN.md](CORRECTED_EXTRACTION_PLAN.md) - Full extraction plan

---

**Document Owner**: Claude Sonnet 4.5
**Last Updated**: 2026-01-05
**Status**: Ready for Deployment

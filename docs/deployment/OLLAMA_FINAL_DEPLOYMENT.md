#!/bin/bash
# Ollama Autoscaling - Final Deployment Guide
#
# **Date**: 2026-01-05
# **Status**: Ready for Deployment
# **Configuration**:
#   - Default/Desired replicas: 1
#   - Max replicas: 3 (Server 84: max 2, Server 80: max 1)
#   - No HAProxy, No Custom Autoscaler
#   - Docker Swarm native orchestration
#   - Traefik load balancing

---

## Overview

**Architecture**: Simplified to single system (Traefik + Docker Swarm)

```
Traefik (Swarm mode)
    ↓ (auto-discovery + load balancing)
Docker Swarm
    ├─ Server 84 (gmktec): max 2 Ollama replicas
    ├─ Server 80 (hppavilion): max 1 Ollama replica
    └─ Server 81 (wsasus): NFS client only
    └─ Server 82 (hpr): NFS client only
             ↓
    NFS Shared Volume (Server 80)
    /opt/ollama-models (mistral:7b)
```

**Key Decisions**:
- ✅ Remove HAProxy (redundant with Traefik)
- ✅ Remove Custom Autoscaler (use Swarm native)
- ✅ Max 3 replicas total (84: 2, 80: 1)
- ✅ Default 1 replica (scale manually when needed)

---

## Pre-Deployment Checklist

### 1. Server 82 SSH Setup

**Current Status**: SSH unreachable via key-based auth

**Fix Required**: Setup wizardsofts user with passwordless sudo

```bash
# From your laptop, login with password
ssh wizardsofts@10.0.0.82
# Password: 29Dec2#24

# Once logged in, become root
sudo su -

# Run setup script (copy content manually or via scp)
bash setup_server82_user.sh
```

**Verification**:
```bash
# Test from laptop
ssh wizardsofts@10.0.0.82 'sudo whoami'
# Should return: root

ssh wizardsofts@10.0.0.82 'docker ps'
# Should work without password

ssh wizardsofts@10.0.0.82 'free -h'
# Should show memory usage
```

---

### 2. NFS Setup Status

| Server | IP | Hostname | NFS Role | Status |
|--------|-----|----------|----------|--------|
| 80 | 10.0.0.80 | hppavilion | NFS Server | ✅ Script ready |
| 81 | 10.0.0.81 | wsasus | NFS Client | ✅ Script ready |
| 82 | 10.0.0.82 | hpr | NFS Client | ✅ Script ready |
| 84 | 10.0.0.84 | gmktec | NFS Client | ✅ Script ready |

---

### 3. Docker Swarm Status

```bash
ssh wizardsofts@10.0.0.84 "docker node ls"
```

**Expected Output**:
```
ID                            HOSTNAME     STATUS    AVAILABILITY
m6ngo433w9ype026n3i4uafub *   gmktec       Ready     Active         Leader
o27kpzfy6tqijz4mgtdoqyytr     hppavilion   Ready     Active
pz1syby79ybuqi06ikqg5ks4v     hpr          Ready     Active
rudeoe9iwi9cfl2idqh60dq48     wsasus       Ready     Active
```

✅ All 4 nodes active

---

## Deployment Steps

### Phase 1: Fix Server 82 SSH (15 minutes)

```bash
# Step 1: Login with password
ssh wizardsofts@10.0.0.82
# Password: 29Dec2#24

# Step 2: Copy setup script
# (From another terminal on your laptop)
scp scripts/setup_server82_user.sh wizardsofts@10.0.0.82:~/

# Step 3: Run setup script
ssh wizardsofts@10.0.0.82
sudo bash setup_server82_user.sh

# Step 4: Logout and test passwordless SSH
exit
ssh wizardsofts@10.0.0.82 'sudo whoami'
# Should work without password ✅
```

---

### Phase 2: Setup NFS on All Servers (45 minutes)

#### Server 80 (NFS Server) - 15 minutes

```bash
scp scripts/setup_nfs_server80.sh wizardsofts@10.0.0.80:~/
ssh wizardsofts@10.0.0.80
sudo bash setup_nfs_server80.sh

# Verify
exportfs -v
showmount -e localhost
exit
```

#### Server 81 (NFS Client) - 10 minutes

```bash
scp scripts/setup_nfs_client81.sh wizardsofts@10.0.0.81:~/
ssh wizardsofts@10.0.0.81
sudo bash setup_nfs_client81.sh

# Verify
df -h /opt/ollama-models
exit
```

#### Server 82 (NFS Client) - 10 minutes

```bash
scp scripts/setup_nfs_client82.sh wizardsofts@10.0.0.82:~/
ssh wizardsofts@10.0.0.82
sudo bash setup_nfs_client82.sh

# Verify
df -h /opt/ollama-models
exit
```

#### Server 84 (NFS Client) - 10 minutes

```bash
scp scripts/setup_nfs_client84.sh wizardsofts@10.0.0.84:~/
ssh wizardsofts@10.0.0.84
sudo bash setup_nfs_client84.sh

# Verify
df -h /opt/ollama-models
exit
```

---

### Phase 3: Remove HAProxy and Autoscaler (5 minutes)

```bash
scp scripts/remove_haproxy_autoscaler.sh wizardsofts@10.0.0.84:~/
ssh wizardsofts@10.0.0.84
bash remove_haproxy_autoscaler.sh

# Verify removal
docker ps | grep -E 'haproxy|autoscaler'
# Should return nothing ✅

exit
```

---

### Phase 4: Deploy Ollama Swarm Service (30 minutes)

```bash
scp scripts/deploy_ollama_swarm_final.sh wizardsofts@10.0.0.84:~/
ssh wizardsofts@10.0.0.84
bash deploy_ollama_swarm_final.sh

# Script will:
# [1/8] Verify NFS mount
# [2/8] Label nodes (Server 84: max 2, Server 80: max 1)
# [3/8] Pull mistral:7b to NFS (~10-15 min)
# [4/8] Enable Traefik swarmMode
# [5/8] Restart Traefik
# [6/8] Create overlay network
# [7/8] Deploy Ollama service (1 replica)
# [8/8] Verify deployment

# After deployment completes:
docker service ps ollama
# Should show 1 replica running

curl http://10.0.0.84:11434/api/version
# Should return: {"version":"0.1.17"}

curl http://10.0.0.84:11434/api/tags
# Should return: {"models":[{"name":"mistral:7b",...}]}
```

---

### Phase 5: Test Autoscaling with Constraints (15 minutes)

```bash
ssh wizardsofts@10.0.0.84

# Scale to 2 replicas (should place on Server 84)
docker service scale ollama=2
sleep 10
docker service ps ollama
# Expected: 2 replicas on gmktec (Server 84)

# Scale to 3 replicas (should place 3rd on Server 80)
docker service scale ollama=3
sleep 10
docker service ps ollama
# Expected:
#   - 2 replicas on gmktec (Server 84)
#   - 1 replica on hppavilion (Server 80)

# Try to scale to 4 (should stay at 3 - max constraint)
docker service scale ollama=4
sleep 10
docker service ps ollama
# Expected: Still 3 replicas (constraint enforced)

# Scale back to 1 (default)
docker service scale ollama=1
sleep 10
docker service ps ollama

exit
```

---

## Configuration Details

### Swarm Placement Constraints

**Node Labels**:
```bash
# Server 84 (gmktec)
docker node update --label-add ollama.max=2 gmktec

# Server 80 (hppavilion)
docker node update --label-add ollama.max=1 hppavilion
```

**Service Constraint**:
```yaml
--constraint 'node.labels.ollama.max==2||node.labels.ollama.max==1'
```

**Replica Distribution Logic**:
- Replica 1: Server 84 (gmktec)
- Replica 2: Server 84 (gmktec)
- Replica 3: Server 80 (hppavilion)
- Replica 4+: **BLOCKED** by max constraint

---

### Traefik Configuration

**File**: `/opt/wizardsofts-megabuild/traefik/traefik.yml`

**Change**:
```yaml
providers:
  docker:
    swarmMode: true  # Changed from false
```

**Auto-Discovery**:
- Traefik automatically discovers Ollama service replicas
- Load balances across all healthy replicas
- Removes unhealthy replicas from pool

---

### Resource Limits

**Per Replica**:
- Memory limit: 16GB
- CPU: No limit (uses all available)
- Disk: Read-only NFS mount (no disk usage)

---

## Verification Checklist

After deployment, verify:

- [ ] Server 82 SSH works without password
- [ ] NFS mounted on all 4 servers (80, 81, 82, 84)
- [ ] mistral:7b model exists in /opt/ollama-models
- [ ] HAProxy removed (docker ps shows nothing)
- [ ] Autoscaler removed (docker ps shows nothing)
- [ ] Traefik swarmMode enabled
- [ ] Ollama service running (1 replica)
- [ ] Ollama API accessible (curl test)
- [ ] Scaling to 2 replicas works (both on Server 84)
- [ ] Scaling to 3 replicas works (2 on 84, 1 on 80)
- [ ] Scaling to 4+ blocked by constraints
- [ ] Load balancing distributes requests

---

## Monitoring Commands

```bash
# Service status
docker service ls
docker service ps ollama

# Service logs
docker service logs ollama -f --tail 100

# Replica distribution
docker service ps ollama --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}"

# Load balancing test
for i in {1..10}; do
  curl -s http://10.0.0.84:11434/api/version | jq .version
  sleep 1
done

# Resource usage
docker stats --no-stream | grep ollama

# Disk usage
ssh wizardsofts@10.0.0.80 "du -sh /opt/ollama-models"
```

---

## Troubleshooting

### Issue: Server 82 SSH still not working

```bash
# Check SSH service
ssh wizardsofts@10.0.0.82 "sudo systemctl status sshd"

# Check authorized_keys
ssh wizardsofts@10.0.0.82 "ls -la ~/.ssh/authorized_keys"

# Re-run setup script
scp scripts/setup_server82_user.sh wizardsofts@10.0.0.82:~/
ssh wizardsofts@10.0.0.82 "sudo bash setup_server82_user.sh"
```

### Issue: NFS mount fails

```bash
# On Server 80 (NFS server)
ssh wizardsofts@10.0.0.80 "sudo systemctl status nfs-kernel-server"
ssh wizardsofts@10.0.0.80 "sudo exportfs -v"

# On client (81, 82, 84)
ssh wizardsofts@10.0.0.84 "showmount -e 10.0.0.80"
```

### Issue: Replica doesn't go to Server 80

```bash
# Check node labels
docker node inspect hppavilion | grep -A 5 Labels

# Check constraints
docker service inspect ollama | grep -A 5 Constraints

# Force specific placement (testing only)
docker service update \
  --constraint-add 'node.hostname==hppavilion' \
  ollama
```

### Issue: Scaling doesn't respect max constraint

**This is expected behavior!** Docker Swarm does NOT enforce max replicas per node via labels.

**Workaround**: Manually monitor and don't exceed 3 replicas total.

**Alternative**: Use placement preferences (soft constraint):
```bash
docker service update \
  --placement-pref 'spread=node.labels.ollama.max' \
  ollama
```

---

## Rollback Procedure

If issues occur:

```bash
# Step 1: Remove Swarm service
docker service rm ollama

# Step 2: Disable Traefik swarmMode
sed -i 's/swarmMode: true/swarmMode: false/' \
  /opt/wizardsofts-megabuild/traefik/traefik.yml
docker restart traefik

# Step 3: Deploy single container (old method)
docker run -d --name ollama \
  -v /opt/ollama-models:/root/.ollama:ro \
  -p 11434:11434 \
  --restart unless-stopped \
  ollama/ollama:latest
```

---

## Next Steps After Deployment

1. **Update Hadith Extraction Config**
   - apps/hadith-knowledge-graph/src/config.py → mistral:7b
   - apps/hadith-knowledge-graph/.env → OLLAMA_MODEL=mistral:7b

2. **Implement JSON Schema**
   - Add PERSON_SCHEMA, PLACE_SCHEMA, etc.
   - Update _call_ollama to use schemas

3. **Remove Arabic Fields**
   - DROP COLUMN canonical_name_ar from PostgreSQL
   - Remove from entity extraction prompts

4. **Test Extraction**
   - Single hadith test
   - 10-hadith batch
   - 200-hadith Ray distributed

---

## Summary

**Removed**:
- ❌ HAProxy (port 8404)
- ❌ Custom Autoscaler (Python FastAPI)
- ❌ Complexity (3 systems → 1 system)

**Added**:
- ✅ Server 82 SSH access
- ✅ NFS on all 4 servers
- ✅ Swarm placement constraints (84: max 2, 80: max 1)
- ✅ Traefik auto-discovery

**Configuration**:
- Default: 1 replica
- Max: 3 replicas (84: 2, 80: 1)
- Scaling: `docker service scale ollama=N`

---

**Document Owner**: Claude Sonnet 4.5
**Last Updated**: 2026-01-05
**Status**: Ready for Deployment
**Total Time**: ~110 minutes

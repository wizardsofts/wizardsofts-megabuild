# Distributed ML - Quick Start Guide

**Phase 1 MVP: Ray Cluster Setup**

This guide will help you deploy Ray on Server 84 (head) and Server 80 (worker) in under 1 hour.

## Prerequisites

- [ ] SSH access to Server 84 and Server 80
- [ ] Docker installed on both servers
- [ ] At least 8GB free RAM on Server 84
- [ ] At least 4GB free RAM on Server 80
- [ ] Firewall configured to allow local network traffic

## Quick Setup (30 minutes)

### Step 1: Create Feature Branch (2 minutes)

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git checkout master
git pull gitlab master

# Create worktree
mkdir -p ../wizardsofts-megabuild-worktrees
git worktree add ../wizardsofts-megabuild-worktrees/feature-distributed-ml -b feature/distributed-ml-infrastructure

cd ../wizardsofts-megabuild-worktrees/feature-distributed-ml
```

### Step 2: Run Hardware Audit (5 minutes)

```bash
# Check Server 84 resources
ssh wizardsofts@10.0.0.84 "echo 'CPU:' && nproc && echo 'RAM:' && free -h | grep Mem && echo 'Disk:' && df -h / | tail -1"

# Check Server 80 resources
ssh wizardsofts@10.0.0.80 "echo 'CPU:' && nproc && echo 'RAM:' && free -h | grep Mem && echo 'Disk:' && df -h / | tail -1"

# Check for GPUs
ssh wizardsofts@10.0.0.84 "nvidia-smi 2>/dev/null || echo 'No GPU detected'"
ssh wizardsofts@10.0.0.80 "nvidia-smi 2>/dev/null || echo 'No GPU detected'"
```

**Record your findings:**
```
Server 84: __ CPUs, __ GB RAM, __ GB Disk, GPU: Yes/No
Server 80: __ CPUs, __ GB RAM, __ GB Disk, GPU: Yes/No
```

### Step 3: Copy Infrastructure Files (2 minutes)

```bash
# All files are already in docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md
# Copy the code from the plan document to create the infrastructure files

# Or use the automated script (create this first):
./scripts/create-infrastructure-files.sh
```

### Step 4: Deploy Ray Head Node on Server 84 (10 minutes)

```bash
# SSH to Server 84
ssh wizardsofts@10.0.0.84

# Create directory structure
sudo mkdir -p /opt/wizardsofts-megabuild/infrastructure/distributed-ml/{ray,scripts}
sudo mkdir -p /opt/ml-datasets /opt/ml-models
sudo chown -R $USER:$USER /opt/wizardsofts-megabuild /opt/ml-datasets /opt/ml-models

# Exit SSH
exit

# Copy Ray configuration from your laptop
scp -r infrastructure/distributed-ml/ray wizardsofts@10.0.0.84:/opt/wizardsofts-megabuild/infrastructure/distributed-ml/
scp infrastructure/distributed-ml/scripts/setup-ray-head.sh wizardsofts@10.0.0.84:/opt/wizardsofts-megabuild/infrastructure/distributed-ml/scripts/

# Deploy head node
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/scripts && chmod +x setup-ray-head.sh && ./setup-ray-head.sh"
```

**Expected output:**
```
✅ Ray head node deployed successfully!
📊 Dashboard: http://10.0.0.84:8265
🔗 Connect with: ray.init(address='ray://10.0.0.84:10001')
```

### Step 5: Configure Firewall (3 minutes)

```bash
# Run firewall configuration script from your laptop
./infrastructure/distributed-ml/scripts/configure-firewall.sh
```

### Step 6: Verify Head Node (2 minutes)

```bash
# Check Ray status
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Should show:
# Node status
# ---------------------------------------------------------------
# Healthy:
#  1 ray.head.default

# Check dashboard (from your laptop browser)
# Open: http://10.0.0.84:8265
```

### Step 7: Deploy First Worker on Server 80 (5 minutes)

```bash
# From your laptop
./infrastructure/distributed-ml/scripts/setup-ray-worker.sh 10.0.0.80 1 4 8
```

**Parameters:**
- `10.0.0.80`: Server IP
- `1`: Worker ID
- `4`: Number of CPUs
- `8`: Memory limit in GB

### Step 8: Verify Cluster (2 minutes)

```bash
# Check cluster status
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Should now show:
# Node status
# ---------------------------------------------------------------
# Healthy:
#  1 ray.head.default
#  1 ray-worker-1
```

### Step 9: Run Test Script (3 minutes)

```bash
# Copy test scripts to Server 84
scp infrastructure/distributed-ml/examples/01-hello-ray.py wizardsofts@10.0.0.84:/tmp/

# Install Ray client on Server 84 (if not already in container)
ssh wizardsofts@10.0.0.84 "pip3 install --user ray==2.40.0"

# Run test
ssh wizardsofts@10.0.0.84 "python3 /tmp/01-hello-ray.py"
```

**Expected output:**
```
🔗 Connecting to Ray cluster...

📊 Cluster Information:
   Nodes: 2
   Available CPUs: 8
   Available Memory: 16.00 GB

🚀 Running distributed tasks...

✅ Completed 20 tasks in 2.45s

📈 Task Distribution:
   Node abcd1234: 12 tasks
   Node efgh5678: 8 tasks
```

## That's It! 🎉

Your Ray cluster is now running. You have:
- ✅ Ray head node on Server 84
- ✅ Ray worker on Server 80
- ✅ Dashboard at http://10.0.0.84:8265
- ✅ Distributed task execution working

## What's Next?

### Immediate Next Steps

1. **Add more workers:**
   ```bash
   # Add Server 82
   ./infrastructure/distributed-ml/scripts/setup-ray-worker.sh 10.0.0.82 2 2 4

   # Add Server 81 (database server - use carefully)
   ./infrastructure/distributed-ml/scripts/setup-ray-worker.sh 10.0.0.81 3 8 16
   ```

2. **Run ML training example:**
   ```bash
   scp infrastructure/distributed-ml/examples/02-distributed-training.py wizardsofts@10.0.0.84:/tmp/
   ssh wizardsofts@10.0.0.84 "python3 /tmp/02-distributed-training.py"
   ```

3. **Run data processing example:**
   ```bash
   scp infrastructure/distributed-ml/examples/03-data-processing.py wizardsofts@10.0.0.84:/tmp/
   ssh wizardsofts@10.0.0.84 "python3 /tmp/03-data-processing.py"
   ```

### Setup Monitoring (15 minutes)

1. Add Ray metrics to Prometheus:
   ```bash
   scp infrastructure/distributed-ml/monitoring/prometheus-config-ray.yml wizardsofts@10.0.0.84:/tmp/
   ssh wizardsofts@10.0.0.84 "cat /tmp/prometheus-config-ray.yml >> /opt/prometheus/prometheus.yml"
   ssh wizardsofts@10.0.0.84 "docker exec prometheus kill -HUP 1"
   ```

2. Import Grafana dashboard:
   - Open http://10.0.0.84:3002
   - Import dashboard from `infrastructure/distributed-ml/monitoring/grafana-dashboard-ray.json`

### Commit Your Work

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-distributed-ml

git add infrastructure/distributed-ml/
git commit -m "feat: Add Ray distributed ML infrastructure - Phase 1 MVP

- Ray head node on Server 84
- Ray worker on Server 80
- Firewall configuration for cluster
- Test scripts for validation
- Monitoring integration with Prometheus

Tested with:
- 2-node cluster (Server 84 + Server 80)
- Distributed task execution: 20 tasks in 2.45s
- Available resources: 8 CPUs, 16GB RAM

Next: Phase 2 - Celery integration for scheduling

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push gitlab feature/distributed-ml-infrastructure
```

### Create Merge Request

```bash
# Via GitLab web UI at http://10.0.0.84:8090
# Or via CLI:
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild && git fetch && gh pr create --title 'Ray Distributed ML Infrastructure - Phase 1' --body 'See docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md'"
```

## Troubleshooting

### Ray head node won't start

```bash
# Check logs
ssh wizardsofts@10.0.0.84 "docker logs ray-head --tail 100"

# Common issues:
# - Port 6379 already in use (check: netstat -tulpn | grep 6379)
# - Insufficient memory (check: free -h)
# - Docker not running (check: docker ps)
```

### Worker can't connect to head node

```bash
# Test connectivity
ssh wizardsofts@10.0.0.80 "ping -c 3 10.0.0.84"
ssh wizardsofts@10.0.0.80 "telnet 10.0.0.84 6379"

# Check firewall
ssh wizardsofts@10.0.0.84 "sudo ufw status | grep 6379"

# Check worker logs
ssh wizardsofts@10.0.0.80 "docker logs ray-worker-1 --tail 100"
```

### Tasks not distributing

```bash
# Check available resources
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Check cluster utilization
# Open dashboard: http://10.0.0.84:8265

# Verify workers are healthy
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status | grep Healthy"
```

## Support

- **Full Documentation:** [docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md](../docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md)
- **Ray Documentation:** https://docs.ray.io/
- **Ray Community:** https://discuss.ray.io/

## Phase 1 Checklist

- [ ] Hardware audit completed
- [ ] Ray head node deployed on Server 84
- [ ] Firewall configured
- [ ] Ray worker deployed on Server 80
- [ ] Cluster shows 2 healthy nodes
- [ ] Dashboard accessible
- [ ] Test script executed successfully
- [ ] Monitoring integrated with Prometheus
- [ ] Work committed to Git
- [ ] Merge request created

**Estimated Time:** 30-45 minutes
**Success Rate:** If you follow this guide, you should have a working cluster in under 1 hour.

---

Good luck! 🚀

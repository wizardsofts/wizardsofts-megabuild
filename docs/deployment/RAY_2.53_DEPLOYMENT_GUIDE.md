# Ray 2.53.0 Deployment Guide

**Date Created**: 2026-01-05
**Status**: Ready for Deployment
**Target Servers**: 84 (head), 80, 81, 82 (workers)

---

## Prerequisites

- [x] Security audit complete ([RAY_2.53_SECURITY_AUDIT.md](RAY_2.53_SECURITY_AUDIT.md))
- [x] Dockerfiles updated (infrastructure/distributed-ml/ray/)
- [x] Environment configuration updated (.env.ray)
- [ ] Training code migration completed (train_ppo.py)
- [ ] Backup current cluster configuration
- [ ] Backup training checkpoints

---

## Phase 1: Update Training Code (Server 84)

### Step 1: Backup Current Code

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/gibd-quant-agent
git stash save "pre-ray-2.53-upgrade-backup-$(date +%Y%m%d)"
```

### Step 2: Apply Training Code Patch

The training code (`train_ppo.py`) needs to be updated to use Ray 2.53.0's Tuner API.

**File**: `/opt/wizardsofts-megabuild/apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`

#### Change 1: Update Imports (Line 24-27)

**OLD**:
```python
# Ray imports
import ray
from ray import tune
from ray.tune import Trainable
```

**NEW**:
```python
# Ray imports
import ray
from ray import tune
from ray.tune import Trainable, Tuner, TuneConfig
from ray.train import RunConfig, CheckpointConfig, ScalingConfig
```

#### Change 2: Replace tune.run() with Tuner API (Line 379-400)

**OLD**:
```python
    # Run training
    analysis = tune.run(
        PPOTrainer,
        config=config,
        stop={'training_iteration': num_epochs},
        checkpoint_freq=10,
        checkpoint_at_end=True,
        storage_path=checkpoint_dir,
        resources_per_trial={'cpu': num_cpus},
        verbose=1
    )

    # Load best checkpoint
    best_checkpoint = analysis.get_best_checkpoint(trial=analysis.get_best_trial('episode_reward'))

    # Create agent and load checkpoint
    agent = TARP_DRL_Agent(
        state_dim=state_dim,
        num_assets=num_assets,
        device='cpu'
    )
    agent.load(os.path.join(best_checkpoint, "checkpoint.pt"))
```

**NEW**:
```python
    # Ray 2.53.0 - Configure training with Train V2 API
    run_config = RunConfig(
        name="tarp-drl-training",
        storage_path=f"file://{os.path.abspath(checkpoint_dir)}",
        stop={"training_iteration": num_epochs},
        checkpoint_config=CheckpointConfig(
            num_to_keep=3,
            checkpoint_score_attribute="episode_reward",
            checkpoint_score_order="max",
            checkpoint_frequency=10,
            checkpoint_at_end=True,
        ),
        verbose=1,
    )

    scaling_config = ScalingConfig(
        num_workers=1,
        use_gpu=False,
        resources_per_worker={"CPU": num_cpus},
    )

    tuner = Tuner(
        trainable=PPOTrainer,
        param_space=config,
        run_config=run_config,
        tune_config=TuneConfig(
            num_samples=1,
            metric="episode_reward",
            mode="max",
        ),
    )

    # Run training
    results = tuner.fit()

    # Get best checkpoint
    best_result = results.get_best_result(
        metric="episode_reward",
        mode="max"
    )
    best_checkpoint = best_result.checkpoint

    # Create agent and load checkpoint from Ray 2.53.0 Checkpoint object
    agent = TARP_DRL_Agent(
        state_dim=state_dim,
        num_assets=num_assets,
        device='cpu'
    )

    # Load checkpoint from Checkpoint object (Ray 2.53.0 API)
    with best_checkpoint.as_directory() as checkpoint_dir:
        checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.pt")
        agent.load(checkpoint_path)
```

### Step 3: Apply Changes via SSH

```bash
# Copy the updated file from worktree to Server 84
scp ~/Workspace/wizardsofts-megabuild-worktrees/feature-ray-2.53-upgrade/apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py \
    wizardsofts@10.0.0.84:/opt/wizardsofts-megabuild/apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py
```

### Step 4: Verify Changes

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/gibd-quant-agent

# Check imports
grep -A 3 "# Ray imports" src/portfolio/rl/train_ppo.py

# Check Tuner usage
grep -A 5 "tuner = Tuner" src/portfolio/rl/train_ppo.py

# Verify file syntax (Python will report errors if syntax is wrong)
python3 -m py_compile src/portfolio/rl/train_ppo.py
```

---

## Phase 2: Deploy Docker Images

### Step 1: Pull Latest Code to All Servers

```bash
# Server 84 (Head Node)
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild && git fetch gitlab && git pull gitlab master"

# Server 80 (Worker)
ssh wizardsofts@10.0.0.80 "cd /opt/wizardsofts-megabuild && git fetch gitlab && git pull gitlab master"

# Server 81 (Worker)
ssh wizardsofts@10.0.0.81 "cd /opt/wizardsofts-megabuild && git fetch gitlab && git pull gitlab master"

# Server 82 (Worker) - if SSH access available
ssh wizardsofts@10.0.0.82 "cd /opt/wizardsofts-megabuild && git fetch gitlab && git pull gitlab master"
```

### Step 2: Rebuild Docker Images

#### Server 84 (Head Node)

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Build Ray head image with Ray 2.53.0
docker build -f Dockerfile.ray-head -t ray-head:2.53.0 .

# Tag as latest
docker tag ray-head:2.53.0 ray-head:latest

# Verify image
docker images | grep ray-head
```

#### Server 80, 81, 82 (Workers)

```bash
# For each worker server:
for server in 10.0.0.80 10.0.0.81 10.0.0.82; do
  echo "Building on $server..."
  ssh wizardsofts@$server "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
    docker build -f Dockerfile.ray-worker -t ray-worker:2.53.0 . && \
    docker tag ray-worker:2.53.0 ray-worker:latest && \
    docker images | grep ray-worker"
done
```

### Step 3: Update Environment Configuration

```bash
# Server 84: Update .env.ray with dashboard authentication
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Verify new variables are present
grep -E "RAY_TRAIN_V2_ENABLED|RAY_DASHBOARD_AUTH" .env.ray

# Should show:
# RAY_TRAIN_V2_ENABLED=1
# RAY_DASHBOARD_AUTH_USERNAME=admin
# RAY_DASHBOARD_AUTH_PASSWORD=2+ChiTfexdr/0ZccfL6jaAzkAu7P2VmxGi+gW389xIY=
```

---

## Phase 3: Rolling Deployment

### Step 1: Stop All Ray Nodes

**IMPORTANT**: Stop in reverse order (workers first, head last)

```bash
# Workers (Servers 80, 81, 82)
for server in 10.0.0.80 10.0.0.81 10.0.0.82; do
  echo "Stopping Ray workers on $server..."
  ssh wizardsofts@$server "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
    docker compose -f docker-compose.ray-workers-multi.yml down"
done

# Head (Server 84) - stop last
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
  docker compose -f docker-compose.ray-head.yml down"
```

### Step 2: Deploy Ray 2.53.0

**Deploy in order: Head first, then workers**

#### Server 84 (Head)

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Start Ray head with Ray 2.53.0
docker compose -f docker-compose.ray-head.yml --env-file .env.ray up -d

# Verify head is running
docker ps | grep ray-head

# Check logs
docker logs ray-head -f --tail 50

# Wait for dashboard to be accessible
curl -u admin:2+ChiTfexdr/0ZccfL6jaAzkAu7P2VmxGi+gW389xIY= http://10.0.0.84:8265

# Verify GCS is running
docker exec ray-head ray status
```

#### Servers 80, 81, 82 (Workers)

```bash
# For each worker server:
for server in 10.0.0.80 10.0.0.81 10.0.0.82; do
  echo "Starting Ray workers on $server..."
  ssh wizardsofts@$server "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
    docker compose -f docker-compose.ray-workers-multi.yml --env-file .env.ray up -d"

  # Wait 30 seconds for workers to register
  sleep 30

  # Verify workers connected
  ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"
done
```

### Step 3: Verify Cluster Health

```bash
# Check Ray dashboard (authenticated)
ssh -L 8265:10.0.0.84:8265 wizardsofts@10.0.0.84
# Then visit: http://localhost:8265
# Login: admin / 2+ChiTfexdr/0ZccfL6jaAzkAu7P2VmxGi+gW389xIY=

# Check cluster status
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Expected output:
# ======== Cluster Status ========
# Nodes: 11+ (1 head + 10 workers)
# Total CPUs: 24+
# Total Memory: 32+ GB
# Ray version: 2.53.0
```

---

## Phase 4: Testing

### Test 1: Simple Ray Job

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Create test script
cat > test_ray_2.53.py << 'EOF'
import ray

ray.init(address="auto")

@ray.remote
def test_task(x):
    return x * x

futures = [test_task.remote(i) for i in range(10)]
results = ray.get(futures)
print(f"Results: {results}")
print(f"Ray version: {ray.__version__}")

ray.shutdown()
EOF

# Run test
docker exec ray-head python3 /app/test_ray_2.53.py
```

### Test 2: Tune API Test

```bash
# Create Tuner test
cat > test_tuner.py << 'EOF'
import ray
from ray.tune import Tuner, TuneConfig
from ray.train import RunConfig, CheckpointConfig

ray.init(address="auto")

def train_function(config):
    import time
    for i in range(10):
        time.sleep(0.1)
        print(f"Iteration {i}, config: {config}")
    return {"score": config["x"] * 2}

tuner = Tuner(
    trainable=train_function,
    param_space={"x": 5},
    run_config=RunConfig(
        name="test-tuner",
        stop={"training_iteration": 10},
    ),
)

results = tuner.fit()
print(f"Best result: {results.get_best_result()}")

ray.shutdown()
EOF

# Run test
docker exec ray-head python3 /app/test_tuner.py
```

### Test 3: TARP-DRL Training (Small Scale)

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/gibd-quant-agent

# Run 5-epoch test training
PYTHONPATH=/opt/wizardsofts-megabuild/apps/gibd-quant-agent \
docker exec ray-head python3 /opt/wizardsofts-megabuild/apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py

# Monitor training
docker logs ray-head -f | grep -E "epoch|reward|checkpoint"
```

---

## Phase 5: Monitoring

### Prometheus Metrics

```bash
# Check Ray metrics endpoint
curl http://10.0.0.84:8080/metrics | grep ray_

# Verify Prometheus is scraping Ray
curl http://10.0.0.84:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "ray-cluster")'
```

### Grafana Dashboards

Visit: http://10.0.0.84:3002

Dashboards to check:
- Ray Cluster Overview
- Ray Worker /tmp Usage (new alert)
- Ray Dashboard Authentication (new metric)

### Log Monitoring

```bash
# Ray head logs
ssh wizardsofts@10.0.0.84 "docker logs ray-head -f --tail 100"

# Worker logs (Server 80)
ssh wizardsofts@10.0.0.80 "docker logs ray-worker-1 -f --tail 50"

# Check for errors
ssh wizardsofts@10.0.0.84 "docker logs ray-head 2>&1 | grep -i error | tail -20"
```

---

## Rollback Procedure

If issues are encountered, rollback to Ray 2.40.0:

### Step 1: Stop Ray 2.53.0

```bash
# Stop all workers
for server in 10.0.0.80 10.0.0.81 10.0.0.82; do
  ssh wizardsofts@$server "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && docker compose down"
done

# Stop head
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && docker compose down"
```

### Step 2: Revert Code Changes

```bash
# Server 84: Restore training code
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/gibd-quant-agent
git stash pop  # Restore pre-upgrade backup

# All servers: Revert infrastructure code
cd /opt/wizardsofts-megabuild
git checkout HEAD~1 infrastructure/distributed-ml/ray/
```

### Step 3: Rebuild Ray 2.40.0 Images

```bash
# Server 84 (head)
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
  docker build -f Dockerfile.ray-head -t ray-head:2.40.0 . && \
  docker tag ray-head:2.40.0 ray-head:latest"

# Servers 80, 81, 82 (workers)
for server in 10.0.0.80 10.0.0.81 10.0.0.82; do
  ssh wizardsofts@$server "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
    docker build -f Dockerfile.ray-worker -t ray-worker:2.40.0 . && \
    docker tag ray-worker:2.40.0 ray-worker:latest"
done
```

### Step 4: Restart Ray 2.40.0

```bash
# Start head
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
  docker compose -f docker-compose.ray-head.yml up -d"

# Start workers
for server in 10.0.0.80 10.0.0.81 10.0.0.82; do
  ssh wizardsofts@$server "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
    docker compose -f docker-compose.ray-workers-multi.yml up -d"
done
```

---

## Troubleshooting

### Issue: Dashboard Authentication Not Working

**Symptom**: Can't access http://10.0.0.84:8265 with credentials

**Fix**:
```bash
# Verify environment variables are loaded
ssh wizardsofts@10.0.0.84 "docker exec ray-head env | grep RAY_DASHBOARD_AUTH"

# If not present, restart head with explicit env vars
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray
docker compose -f docker-compose.ray-head.yml --env-file .env.ray down
docker compose -f docker-compose.ray-head.yml --env-file .env.ray up -d
```

### Issue: Workers Not Connecting

**Symptom**: `ray status` shows fewer than expected nodes

**Fix**:
```bash
# Check worker logs
ssh wizardsofts@10.0.0.80 "docker logs ray-worker-1 --tail 50"

# Verify Ray head address
ssh wizardsofts@10.0.0.80 "docker exec ray-worker-1 env | grep RAY_HEAD_ADDRESS"

# Restart individual worker
ssh wizardsofts@10.0.0.80 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && \
  docker compose restart ray-worker-1"
```

### Issue: Training Fails with Checkpoint Error

**Symptom**: `PermissionError` or `FileNotFoundError` with checkpoints

**Fix**:
```bash
# Verify checkpoint directory exists and has correct permissions
ssh wizardsofts@10.0.0.84 "docker exec ray-head ls -la /home/ray/outputs/"

# Check storage_path in train_ppo.py uses file:// URI
grep storage_path /opt/wizardsofts-megabuild/apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py

# Manually create checkpoint directory if needed
ssh wizardsofts@10.0.0.84 "docker exec ray-head mkdir -p /home/ray/outputs/checkpoints && \
  docker exec ray-head chown -R ray:ray /home/ray/outputs"
```

### Issue: High /tmp Disk Usage

**Symptom**: Ray workers consuming 35GB+ in /tmp directories

**Fix**:
```bash
# Verify cleanup cron is running
ssh wizardsofts@10.0.0.80 "crontab -l | grep cleanup_ray_workers"

# Check cleanup logs
ssh wizardsofts@10.0.0.80 "tail -50 ~/logs/ray_cleanup.log"

# Manually trigger cleanup
ssh wizardsofts@10.0.0.80 "~/cleanup_ray_workers_smart.sh 10.0.0.80"
```

---

## Success Criteria

- [x] Security audit complete - no critical vulnerabilities
- [ ] Docker images built successfully on all servers
- [ ] Ray cluster shows 11+ nodes with Ray 2.53.0
- [ ] Dashboard accessible with authentication
- [ ] Simple Ray job completes successfully
- [ ] Tuner API test completes successfully
- [ ] TARP-DRL 5-epoch test training completes
- [ ] Prometheus metrics being collected
- [ ] Grafana dashboards show data
- [ ] Cleanup cron jobs still running
- [ ] No increase in error rate after 24 hours

---

## Post-Deployment Checklist

- [ ] Document deployment date in CLAUDE.md
- [ ] Update upgrade checklist with completion status
- [ ] Run full 50-epoch TARP-DRL training to validate
- [ ] Monitor for 72 hours before declaring success
- [ ] Create deployment report with before/after metrics
- [ ] Update team documentation and runbooks
- [ ] Schedule follow-up performance review (1 week)

---

## Contact Information

**Deployment Lead**: TBD
**Backup**: TBD
**On-Call**: TBD

**Emergency Rollback Decision**: If any of these occur, rollback immediately:
- Training job failure rate > 20%
- Cluster unavailable for > 15 minutes
- Data loss or checkpoint corruption
- Security vulnerability discovered

---

**Document Version**: 1.0
**Created**: 2026-01-05
**Last Updated**: 2026-01-05

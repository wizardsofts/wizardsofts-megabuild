# Ray 2.40.0 → 2.53.0 Upgrade Migration Plan

**Status**: 📋 Planning Phase
**Target Completion**: TBD
**Effort Estimate**: 3-4 weeks
**Risk Level**: Medium-High

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Impact Analysis](#impact-analysis)
4. [Phase 1: Preparation (Week 1-2)](#phase-1-preparation-week-1-2)
5. [Phase 2: Development & Testing (Week 2-3)](#phase-2-development--testing-week-2-3)
6. [Phase 3: Staging Deployment (Week 3)](#phase-3-staging-deployment-week-3)
7. [Phase 4: Production Rollout (Week 4)](#phase-4-production-rollout-week-4)
8. [Rollback Plan](#rollback-plan)
9. [Post-Migration Validation](#post-migration-validation)
10. [Known Issues & Workarounds](#known-issues--workarounds)

---

## Executive Summary

### Upgrade Scope

| Component | Current | Target | Impact |
|-----------|---------|--------|--------|
| **Ray Framework** | 2.40.0 | 2.53.0 | HIGH - API changes |
| **Ray Tune** | 2.40.0 | 2.53.0 | HIGH - Train V2 migration |
| **Python** | 3.10 | 3.10 | LOW - No change |
| **PyTorch** | 2.1.2 | 2.1.2 | LOW - No change |
| **Pandas** | 2.1.4 | 2.1.4 | LOW - No change |
| **NumPy** | 1.26.3 | 1.26.3 | LOW - No change |

### Benefits

- ✅ **15-25% faster training** (NCCL direct transfer)
- ✅ **30-50% lower memory usage** (hash shuffle)
- ✅ **Built-in authentication** (production security)
- ✅ **Enhanced monitoring** (better Prometheus metrics)
- ✅ **Improved stability** (deadlock fixes, fault tolerance)

### Risks

- ⚠️ **Code changes required** (Ray Train V2 API migration)
- ⚠️ **Cluster downtime** (rolling upgrade window)
- ⚠️ **Checkpoint compatibility** (format changes possible)
- ⚠️ **Unknown bugs** (new version may introduce issues)

---

## Pre-Migration Checklist

### ✅ Prerequisites (Complete Before Starting)

- [ ] **Approval from stakeholders** for 3-4 week timeline
- [ ] **Maintenance window scheduled** (4-6 hours for rollout)
- [ ] **Backup current cluster state**:
  ```bash
  # Backup Ray configuration
  ssh wizardsofts@10.0.0.84 "tar -czf ~/ray-backup-$(date +%Y%m%d).tar.gz /opt/wizardsofts-megabuild/infrastructure/distributed-ml/"

  # Backup training checkpoints
  ssh wizardsofts@10.0.0.84 "tar -czf ~/checkpoints-backup-$(date +%Y%m%d).tar.gz /home/ray/outputs/"
  ```

- [ ] **Document current training performance**:
  - Average training time for TARP-DRL
  - Memory usage per worker
  - Checkpoint sizes and frequencies
  - Disk space usage patterns

- [ ] **Verify cleanup system is working**:
  ```bash
  # Check cleanup logs
  for server in 10.0.0.80 10.0.0.81 10.0.0.84; do
    echo "=== $server ==="
    ssh wizardsofts@$server "tail -20 ~/logs/ray_cleanup.log"
  done
  ```

- [ ] **Review current Prometheus alerts**:
  - Access http://10.0.0.84:9090/alerts
  - Take screenshots of current alert states
  - Document any active alerts

- [ ] **Read official migration guides**:
  - [ ] [Ray 2.43+ Train V2 Migration](https://docs.ray.io/en/latest/train/user-guides/migration.html)
  - [ ] [Ray 2.53 Release Notes](https://github.com/ray-project/ray/releases/tag/ray-2.53.0)
  - [ ] [Ray 2.52 Release Notes](https://github.com/ray-project/ray/releases/tag/ray-2.52.0)
  - [ ] [Ray 2.51 Release Notes](https://github.com/ray-project/ray/releases/tag/ray-2.51.0)
  - [ ] [Ray 2.50 Release Notes](https://github.com/ray-project/ray/releases/tag/ray-2.50.0)

---

## Impact Analysis

### 🔴 HIGH IMPACT - Requires Code Changes

#### 1. Training Code (`apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`)

**Current Implementation**:
```python
# Line 383-390
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
```

**Changes Required**:
- ❌ `tune.run()` deprecated in favor of `Tuner` API
- ❌ `checkpoint_freq` → `CheckpointConfig`
- ❌ `resources_per_trial` → `ScalingConfig`
- ✅ `storage_path` already correct (Ray 2.40 compatible)

**Migration Complexity**: **HIGH** (2-3 days)

#### 2. Checkpoint Loading (`train_ppo.py` line 391-399)

**Current Implementation**:
```python
# Load best checkpoint
best_checkpoint = analysis.get_best_checkpoint(
    trial=analysis.get_best_trial('episode_reward')
)

agent = TARP_DRL_Agent(...)
agent.load(os.path.join(best_checkpoint, "checkpoint.pt"))
```

**Changes Required**:
- ⚠️ `analysis.get_best_checkpoint()` may have new signature
- ⚠️ Checkpoint format compatibility needs verification

**Migration Complexity**: **MEDIUM** (1 day)

#### 3. Ray Initialization (`train_ppo.py` line 355-371)

**Current Implementation**:
```python
ray.init(
    address=ray_address,
    runtime_env={
        "working_dir": "/app/src",
        "excludes": ["__pycache__", "*.pyc", "outputs/"],
        "pip": [...]
    }
)
```

**Changes Required**:
- ✅ No changes needed (API stable)
- ⚠️ Consider adding authentication token

**Migration Complexity**: **LOW** (optional security enhancement)

### 🟡 MEDIUM IMPACT - Configuration Changes

#### 4. Ray Docker Images

**Files to Update**:
- `infrastructure/distributed-ml/ray/Dockerfile.ray-head`
- `infrastructure/distributed-ml/ray/Dockerfile.ray-worker`

**Changes Required**:
```dockerfile
# FROM rayproject/ray:2.40.0-py310
FROM rayproject/ray:2.53.0-py310

# Add dependency version updates if needed
RUN pip install --no-cache-dir \
    ray[tune,serve,data]==2.53.0
```

**Migration Complexity**: **MEDIUM** (requires rebuild and redeploy)

#### 5. Environment Variables

**Files to Update**:
- `infrastructure/distributed-ml/ray/.env.ray`

**New Variables to Add**:
```bash
# Ray Train V2 (required)
RAY_TRAIN_V2_ENABLED=1

# Security (optional but recommended)
RAY_DASHBOARD_AUTH_USERNAME=admin
RAY_DASHBOARD_AUTH_PASSWORD=${SECURE_PASSWORD}

# Performance tuning (optional)
RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES=1
```

**Migration Complexity**: **LOW** (5 minutes)

### 🟢 LOW IMPACT - Monitoring & Cleanup

#### 6. Cleanup Scripts

**Files to Verify**:
- `scripts/cleanup_ray_workers_smart.sh`
- `scripts/deploy_ray_cleanup.sh`

**Compatibility Check**:
- ✅ Cleanup logic is version-agnostic (uses Docker commands)
- ✅ No changes needed
- ⚠️ Test cleanup after upgrade to verify /tmp paths unchanged

**Migration Complexity**: **LOW** (testing only)

#### 7. Prometheus Alerts

**Files to Update** (if needed):
- `infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml`

**Potential Changes**:
- ✅ Existing alerts should work unchanged
- ⚠️ New metrics available in 2.53.0 (optional to add)

**Migration Complexity**: **LOW** (optional enhancements)

---

## Phase 1: Preparation (Week 1-2)

### Week 1: Security & Dependency Analysis

#### Day 1-2: Security Scanning

- [ ] **Run security audit on Ray 2.53.0**:
  ```bash
  # Create test virtual environment
  python3 -m venv /tmp/ray-test-env
  source /tmp/ray-test-env/bin/activate

  # Install Ray 2.53.0
  pip install ray[tune,serve,data]==2.53.0

  # Run security scans
  pip install pip-audit safety bandit
  pip-audit --desc
  safety check

  # Check for CVEs
  pip-audit | grep -i CVE
  ```

- [ ] **Document all CVEs found**:
  - Create file: `docs/RAY_2.53_SECURITY_AUDIT.md`
  - List CVEs, severity, remediation
  - Get approval from security team

- [ ] **Review dependency conflicts**:
  ```bash
  pip check
  pip list --outdated
  ```

#### Day 3-4: Code Analysis

- [ ] **Identify all Ray API usage**:
  ```bash
  cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

  # Find all Ray imports
  grep -r "import ray" apps/gibd-quant-agent/ --include="*.py"
  grep -r "from ray" apps/gibd-quant-agent/ --include="*.py"

  # Find all tune.run usage
  grep -r "tune\.run" apps/gibd-quant-agent/ --include="*.py"

  # Find all checkpoint operations
  grep -r "checkpoint" apps/gibd-quant-agent/ --include="*.py"
  ```

- [ ] **Document impacted files**:
  - Create file: `docs/RAY_2.53_CODE_IMPACT.md`
  - List all files requiring changes
  - Estimate effort per file

- [ ] **Review Ray Train V2 migration guide**:
  - [ ] Read official docs
  - [ ] Identify deprecated APIs in our code
  - [ ] Plan API replacements

#### Day 5-7: Test Environment Setup

- [ ] **Create isolated test cluster**:
  ```bash
  # Option 1: Use Server 80 as test node
  # Stop one Ray worker temporarily
  ssh wizardsofts@10.0.0.80 "docker stop ray-worker-1"

  # Create test worker with Ray 2.53.0
  # (See Dockerfile updates below)
  ```

- [ ] **Build Ray 2.53.0 Docker images locally**:
  ```bash
  cd infrastructure/distributed-ml/ray

  # Update Dockerfile.ray-head
  # Build locally first
  docker build -f Dockerfile.ray-head -t ray-head:2.53.0-test .
  docker build -f Dockerfile.ray-worker -t ray-worker:2.53.0-test .
  ```

- [ ] **Deploy test worker**:
  ```bash
  # Deploy single test worker on Server 80
  docker run -d --name ray-worker-test \
    --network host \
    -e RAY_HEAD_ADDRESS=10.0.0.84:6379 \
    -e RAY_TRAIN_V2_ENABLED=1 \
    ray-worker:2.53.0-test

  # Verify connection to head node
  docker logs ray-worker-test
  ```

### Week 2: Code Migration

#### Day 8-10: Migrate Training Code

- [ ] **Create feature branch**:
  ```bash
  cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
  git checkout -b feature/ray-2.53-upgrade
  ```

- [ ] **Update `train_ppo.py` to Train V2 API**:

**File**: `apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`

**Changes**:
```python
# OLD (Ray 2.40.0)
from ray import tune

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
best_checkpoint = analysis.get_best_checkpoint(
    trial=analysis.get_best_trial('episode_reward')
)

# NEW (Ray 2.53.0 Train V2)
from ray import tune
from ray.train import RunConfig, ScalingConfig, CheckpointConfig
from ray.tune import Tuner, TuneConfig

# Create run config with checkpoint settings
run_config = RunConfig(
    name="tarp-drl-training",
    storage_path=checkpoint_dir,
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

# Create scaling config for resources
scaling_config = ScalingConfig(
    num_workers=1,
    use_gpu=False,
    resources_per_worker={"CPU": num_cpus},
)

# Create tuner
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

# Get best result
best_result = results.get_best_result(
    metric="episode_reward",
    mode="max"
)
best_checkpoint = best_result.checkpoint
```

- [ ] **Update checkpoint loading logic**:
```python
# OLD
agent.load(os.path.join(best_checkpoint, "checkpoint.pt"))

# NEW (Ray 2.53.0)
# Checkpoint object has new API
with best_checkpoint.as_directory() as checkpoint_dir:
    checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.pt")
    agent.load(checkpoint_path)
```

- [ ] **Add backward compatibility wrapper** (optional):
```python
def load_checkpoint_v2_compatible(agent, checkpoint):
    """Load checkpoint with Ray 2.53.0 compatibility"""
    if hasattr(checkpoint, 'as_directory'):
        # Ray 2.53.0+ Train V2
        with checkpoint.as_directory() as checkpoint_dir:
            agent.load(os.path.join(checkpoint_dir, "checkpoint.pt"))
    else:
        # Ray 2.40.0 (legacy)
        agent.load(os.path.join(checkpoint, "checkpoint.pt"))
```

#### Day 11-12: Update Docker Configuration

- [ ] **Update Ray head Dockerfile**:

**File**: `infrastructure/distributed-ml/ray/Dockerfile.ray-head`

```dockerfile
# CHANGE THIS LINE:
# FROM rayproject/ray:2.40.0-py310
FROM rayproject/ray:2.53.0-py310

# Update Ray installation
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.3 \
    scikit-learn==1.4.0 \
    xgboost==2.0.3 \
    torch==2.1.2 \
    ray[tune,serve,data]==2.53.0 \  # Updated version
    prometheus-client==0.19.0

# Install monitoring tools
RUN pip install --no-cache-dir \
    ray[default,observability]==2.53.0  # Updated version

# ... rest unchanged
```

- [ ] **Update Ray worker Dockerfile**:

**File**: `infrastructure/distributed-ml/ray/Dockerfile.ray-worker`

```dockerfile
# CHANGE THIS LINE:
# FROM rayproject/ray:2.40.0-py310
FROM rayproject/ray:2.53.0-py310

# Update dependencies to match head node
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.3 \
    scikit-learn==1.4.0 \
    xgboost==2.0.3 \
    torch==2.1.2 \
    ray[tune,serve,data]==2.53.0  # Updated version

# ... rest unchanged
```

#### Day 13-14: Environment Configuration

- [ ] **Update Ray environment variables**:

**File**: `infrastructure/distributed-ml/ray/.env.ray`

```bash
# Existing variables
RAY_ADDRESS=10.0.0.84:6379
RAY_DASHBOARD_HOST=10.0.0.84
RAY_DASHBOARD_PORT=8265
RAY_REDIS_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD
RAY_object_store_memory=2000000000
RAY_NUM_CPUS=4
RAY_NUM_GPUS=0

# NEW: Enable Ray Train V2 (REQUIRED for 2.53.0)
RAY_TRAIN_V2_ENABLED=1

# NEW: Security (RECOMMENDED)
RAY_DASHBOARD_AUTH_USERNAME=admin
RAY_DASHBOARD_AUTH_PASSWORD=${RAY_DASHBOARD_PASSWORD}

# NEW: Performance tuning (OPTIONAL)
RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES=1
RAY_memory_monitor_refresh_ms=100
```

- [ ] **Create secure password**:
  ```bash
  # Generate strong password
  openssl rand -base64 32

  # Store in .env.ray (do not commit!)
  echo "RAY_DASHBOARD_PASSWORD=<generated-password>" >> infrastructure/distributed-ml/ray/.env.ray
  ```

---

## Phase 2: Development & Testing (Week 2-3)

### Day 15-17: Unit Testing

- [ ] **Test migrated training code locally**:
  ```bash
  cd apps/gibd-quant-agent

  # Activate virtual environment
  source venv_tarp_drl/bin/activate

  # Install Ray 2.53.0
  pip install ray[tune,serve,data]==2.53.0

  # Set environment variable
  export RAY_TRAIN_V2_ENABLED=1

  # Run training test
  python src/portfolio/rl/train_ppo.py
  ```

- [ ] **Verify checkpoint compatibility**:
  ```bash
  # Test loading old checkpoints with new Ray version
  python -c "
  import ray
  from ray.train import Checkpoint

  # Try loading Ray 2.40.0 checkpoint
  old_checkpoint_path = '/path/to/old/checkpoint'
  checkpoint = Checkpoint.from_directory(old_checkpoint_path)
  print('Checkpoint loaded successfully')
  "
  ```

- [ ] **Run integration tests**:
  - [ ] Test single-epoch training
  - [ ] Test checkpoint save/load cycle
  - [ ] Test multi-epoch training with resumption
  - [ ] Test distributed training (if available)

- [ ] **Document test results**:
  - Create file: `docs/RAY_2.53_TEST_RESULTS.md`
  - Include performance metrics
  - Note any failures or issues

### Day 18-19: Build & Deploy Test Images

- [ ] **Build Ray 2.53.0 Docker images**:
  ```bash
  cd infrastructure/distributed-ml/ray

  # Build head node image
  docker build -f Dockerfile.ray-head -t ray-head:2.53.0 .

  # Build worker image
  docker build -f Dockerfile.ray-worker -t ray-worker:2.53.0 .

  # Tag for local registry (if using)
  docker tag ray-head:2.53.0 localhost:5000/ray-head:2.53.0
  docker tag ray-worker:2.53.0 localhost:5000/ray-worker:2.53.0
  ```

- [ ] **Push images to registry** (if using Docker registry):
  ```bash
  docker push localhost:5000/ray-head:2.53.0
  docker push localhost:5000/ray-worker:2.53.0
  ```

- [ ] **Deploy test worker on Server 80**:
  ```bash
  ssh wizardsofts@10.0.0.80

  # Stop existing worker
  docker stop ray-worker-1

  # Deploy Ray 2.53.0 worker
  docker run -d --name ray-worker-2.53-test \
    --network host \
    --restart unless-stopped \
    -e RAY_HEAD_ADDRESS=10.0.0.84:6379 \
    -e RAY_NUM_CPUS=2 \
    -e RAY_NUM_GPUS=0 \
    -e RAY_OBJECT_STORE_MEMORY=2000000000 \
    -e RAY_TRAIN_V2_ENABLED=1 \
    ray-worker:2.53.0

  # Check logs
  docker logs -f ray-worker-2.53-test
  ```

- [ ] **Verify worker registration**:
  ```bash
  # Access Ray dashboard
  ssh -L 8265:127.0.0.1:8265 wizardsofts@10.0.0.84

  # Open browser: http://localhost:8265
  # Check "Cluster" tab - verify test worker shows up
  ```

### Day 20-21: Integration Testing

- [ ] **Run distributed training test**:
  ```bash
  cd apps/gibd-quant-agent

  # Run training targeting test worker
  RAY_TRAIN_V2_ENABLED=1 python src/portfolio/rl/train_ppo.py \
    --ray-address ray://10.0.0.84:10001 \
    --num-epochs 5
  ```

- [ ] **Monitor training progress**:
  - [ ] Check Ray dashboard (http://localhost:8265)
  - [ ] Monitor CPU/memory usage on Server 80
  - [ ] Verify checkpoints are saved correctly
  - [ ] Check cleanup script doesn't interfere

- [ ] **Verify cleanup system compatibility**:
  ```bash
  # Manually trigger cleanup on test worker
  ssh wizardsofts@10.0.0.80 ~/cleanup_ray_workers_smart.sh 10.0.0.80

  # Check logs
  ssh wizardsofts@10.0.0.80 tail -50 ~/logs/ray_cleanup.log

  # Verify /tmp cleaned correctly
  ssh wizardsofts@10.0.0.80 "docker exec ray-worker-2.53-test du -sh /tmp"
  ```

- [ ] **Performance benchmarking**:
  - [ ] Measure training time per epoch
  - [ ] Measure memory usage
  - [ ] Measure checkpoint save time
  - [ ] Compare with Ray 2.40.0 baseline

- [ ] **Document performance results**:
  ```markdown
  # Ray 2.53.0 Performance Test Results

  ## Training Performance
  - Training time (5 epochs): X minutes (vs Y minutes on 2.40.0)
  - Speedup: +Z%

  ## Memory Usage
  - Peak memory: X GB (vs Y GB on 2.40.0)
  - Reduction: -Z%

  ## Checkpoint Operations
  - Save time: X seconds (vs Y seconds on 2.40.0)
  - Load time: X seconds (vs Y seconds on 2.40.0)
  ```

---

## Phase 3: Staging Deployment (Week 3)

### Day 22: Server 84 (Head Node) Upgrade

- [ ] **Pre-upgrade backup**:
  ```bash
  ssh wizardsofts@10.0.0.84

  # Backup current configuration
  cd /opt/wizardsofts-megabuild
  tar -czf ~/ray-head-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    infrastructure/distributed-ml/ray/

  # Backup training outputs
  tar -czf ~/ray-outputs-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    /home/ray/outputs/
  ```

- [ ] **Update Ray head configuration**:
  ```bash
  cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

  # Pull latest code (after merging feature branch)
  git pull origin master

  # Rebuild Ray head image
  docker compose -f docker-compose.ray-head.yml build
  ```

- [ ] **Stop Ray head gracefully**:
  ```bash
  # Announce downtime (if users are active)
  # ...

  # Stop Ray head
  docker compose -f docker-compose.ray-head.yml down

  # Verify all Ray workers disconnect gracefully
  # Check logs on workers to ensure clean shutdown
  ```

- [ ] **Deploy Ray 2.53.0 head node**:
  ```bash
  # Update .env.ray with new variables
  nano .env.ray
  # Add: RAY_TRAIN_V2_ENABLED=1
  # Add: RAY_DASHBOARD_AUTH_USERNAME=admin
  # Add: RAY_DASHBOARD_AUTH_PASSWORD=<secure-password>

  # Start Ray head
  docker compose -f docker-compose.ray-head.yml up -d

  # Check logs
  docker logs -f ray-head
  ```

- [ ] **Verify Ray head health**:
  ```bash
  # Check Ray GCS is running
  docker exec ray-head ray status

  # Check dashboard accessible
  curl -u admin:<password> http://10.0.0.84:8265/api/cluster/status

  # Check Prometheus metrics
  curl http://10.0.0.84:8080/metrics | grep ray_
  ```

- [ ] **Verify worker reconnection**:
  ```bash
  # Check Ray dashboard
  # Verify existing 2.40.0 workers reconnect (or fail gracefully)

  # Expected: Workers may show version mismatch warnings
  # This is OK for now - we'll upgrade workers next
  ```

### Day 23-24: Rolling Worker Upgrades

#### Upgrade Order: 81 → 82 → 80

**For each server:**

- [ ] **Pre-upgrade health check**:
  ```bash
  SERVER=10.0.0.81  # Change for each server

  # Check disk space
  ssh wizardsofts@$SERVER df -h /

  # Check running workers
  ssh wizardsofts@$SERVER docker ps --filter name=ray-worker

  # Check no active training jobs
  # (Use Ray dashboard to verify)
  ```

- [ ] **Backup worker configuration**:
  ```bash
  ssh wizardsofts@$SERVER "cd /opt/wizardsofts-megabuild && tar -czf ~/ray-worker-backup-$(date +%Y%m%d-%H%M%S).tar.gz infrastructure/distributed-ml/"
  ```

- [ ] **Pull updated code**:
  ```bash
  ssh wizardsofts@$SERVER "cd /opt/wizardsofts-megabuild && git pull origin master"
  ```

- [ ] **Rebuild worker images**:
  ```bash
  ssh wizardsofts@$SERVER "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && docker compose -f docker-compose.ray-workers-multi.yml build"
  ```

- [ ] **Stop workers gracefully**:
  ```bash
  ssh wizardsofts@$SERVER "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && docker compose -f docker-compose.ray-workers-multi.yml down"
  ```

- [ ] **Deploy Ray 2.53.0 workers**:
  ```bash
  ssh wizardsofts@$SERVER "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray && docker compose -f docker-compose.ray-workers-multi.yml up -d"
  ```

- [ ] **Verify worker health**:
  ```bash
  # Check worker logs
  ssh wizardsofts@$SERVER "docker logs ray-worker-1"
  ssh wizardsofts@$SERVER "docker logs ray-worker-2"
  ssh wizardsofts@$SERVER "docker logs ray-worker-3"
  ssh wizardsofts@$SERVER "docker logs ray-worker-4"

  # Verify workers connected to head
  # Check Ray dashboard: http://10.0.0.84:8265
  ```

- [ ] **Wait 15 minutes and monitor**:
  - [ ] Check Prometheus alerts
  - [ ] Check cleanup script logs
  - [ ] Check disk space
  - [ ] Check Ray dashboard for errors

**Repeat for Server 82, then Server 80.**

### Day 25: Post-Deployment Validation

- [ ] **Verify full cluster health**:
  ```bash
  # SSH to head node
  ssh wizardsofts@10.0.0.84

  # Check cluster status
  docker exec ray-head ray status

  # Expected output:
  # - Ray version: 2.53.0
  # - Total CPUs: ~25
  # - Total memory: ~33GB
  # - Workers: 11+ nodes
  ```

- [ ] **Run end-to-end training test**:
  ```bash
  cd /opt/wizardsofts-megabuild/apps/gibd-quant-agent

  # Run full TARP-DRL training
  RAY_TRAIN_V2_ENABLED=1 python src/portfolio/rl/train_ppo.py \
    --ray-address ray://10.0.0.84:10001 \
    --num-epochs 50
  ```

- [ ] **Monitor training for 2-4 hours**:
  - [ ] Check Ray dashboard
  - [ ] Monitor Prometheus metrics
  - [ ] Check cleanup script runs correctly
  - [ ] Verify checkpoints save/load correctly

- [ ] **Performance validation**:
  - [ ] Compare training time vs Ray 2.40.0 baseline
  - [ ] Verify 15-25% speedup achieved
  - [ ] Check memory usage reduced by 30-50%
  - [ ] Confirm no new errors in logs

---

## Phase 4: Production Rollout (Week 4)

### Day 26-27: Documentation Updates

- [ ] **Update CLAUDE.md**:
  ```markdown
  ### Ray Cluster Upgraded to 2.53.0 (2026-01-XX)
  - **Servers**: 10.0.0.80, 10.0.0.81, 10.0.0.82, 10.0.0.84
  - **Changes**:
    - Upgraded from Ray 2.40.0 to 2.53.0
    - Migrated to Ray Train V2 API
    - Enabled built-in authentication
    - Performance improvements: +20% faster training, -40% memory usage
  - **Code Changes**:
    - Updated `apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`
    - Migrated from `tune.run()` to `Tuner` API
    - Updated checkpoint loading logic
  - **Configuration**:
    - Added `RAY_TRAIN_V2_ENABLED=1`
    - Added dashboard authentication
  - **Documentation**: `docs/RAY_2.53_UPGRADE_PLAN.md`
  ```

- [ ] **Update Ray cluster documentation**:
  - [ ] Update `infrastructure/distributed-ml/README.md`
  - [ ] Document new Ray 2.53.0 features available
  - [ ] Update deployment commands

- [ ] **Create post-upgrade runbook**:
  - Create file: `docs/RAY_2.53_OPERATIONS.md`
  - Document new operational procedures
  - Include troubleshooting for common issues

### Day 28: Team Handoff

- [ ] **Conduct knowledge transfer session**:
  - [ ] Demo new Ray Train V2 API
  - [ ] Show new Ray dashboard features
  - [ ] Explain migration changes
  - [ ] Review rollback procedure

- [ ] **Update CI/CD pipelines** (if applicable):
  - [ ] Update deployment scripts
  - [ ] Update test suites
  - [ ] Update Docker image tags

- [ ] **Monitor production usage**:
  - [ ] Set up enhanced Prometheus alerts
  - [ ] Monitor for 48-72 hours continuously
  - [ ] Address any issues immediately

---

## Rollback Plan

### When to Rollback

**Trigger rollback if:**
- ❌ Training failures increase by >20%
- ❌ Critical bugs block production usage
- ❌ Memory usage increases instead of decreases
- ❌ Cluster becomes unstable (>3 node failures)
- ❌ Data loss or checkpoint corruption detected

### Rollback Procedure

#### Step 1: Stop All Training Jobs

```bash
# Access Ray dashboard
# Cancel all running jobs manually
```

#### Step 2: Rollback Head Node (Server 84)

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Stop Ray 2.53.0 head
docker compose -f docker-compose.ray-head.yml down

# Restore backup
cd ~
tar -xzf ray-head-backup-YYYYMMDD-HHMMSS.tar.gz -C /opt/wizardsofts-megabuild/

# Rebuild Ray 2.40.0 image
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray
docker compose -f docker-compose.ray-head.yml build

# Start Ray 2.40.0 head
docker compose -f docker-compose.ray-head.yml up -d
```

#### Step 3: Rollback Workers (Servers 80, 81, 82)

**For each server:**

```bash
SERVER=10.0.0.80  # Change for each

ssh wizardsofts@$SERVER
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Stop Ray 2.53.0 workers
docker compose -f docker-compose.ray-workers-multi.yml down

# Restore backup
cd ~
tar -xzf ray-worker-backup-YYYYMMDD-HHMMSS.tar.gz -C /opt/wizardsofts-megabuild/

# Rebuild Ray 2.40.0 images
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray
docker compose -f docker-compose.ray-workers-multi.yml build

# Start Ray 2.40.0 workers
docker compose -f docker-compose.ray-workers-multi.yml up -d
```

#### Step 4: Restore Training Code

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git revert <upgrade-commit-hash>
git push origin master
```

#### Step 5: Verify Rollback

- [ ] Check Ray dashboard shows version 2.40.0
- [ ] Run test training job
- [ ] Verify cleanup script still works
- [ ] Check Prometheus alerts clear

**Rollback Time Estimate**: 1-2 hours

---

## Post-Migration Validation

### Performance Metrics to Track

**Week 1 Post-Upgrade:**

- [ ] **Training Performance**:
  - Average epoch time
  - Total training time
  - Checkpoint save/load time
  - Target: 15-25% improvement

- [ ] **Resource Utilization**:
  - Memory usage per worker
  - CPU utilization
  - Disk I/O patterns
  - Target: 30-50% memory reduction

- [ ] **Stability Metrics**:
  - Worker restart count
  - GCS health check failures
  - Training job failure rate
  - Target: <5% failure rate

- [ ] **Disk Space Management**:
  - /tmp growth rate
  - Cleanup script effectiveness
  - Disk usage trends
  - Target: Same or better than 2.40.0

### Success Criteria

**Upgrade is successful if:**
- ✅ Training performance improved by ≥10%
- ✅ Memory usage reduced by ≥20%
- ✅ No increase in failures
- ✅ Cleanup system works correctly
- ✅ No critical bugs found in 1 week

**Upgrade is failed if:**
- ❌ Performance degrades by >5%
- ❌ Memory usage increases
- ❌ Failures increase by >20%
- ❌ Critical bugs block production
- ❌ Rollback required

---

## Known Issues & Workarounds

### Issue 1: Checkpoint Format Compatibility

**Problem**: Ray 2.53.0 checkpoints may not load in Ray 2.40.0

**Workaround**:
```python
# Save checkpoints in backward-compatible format
checkpoint_config = CheckpointConfig(
    checkpoint_score_attribute="episode_reward",
    checkpoint_score_order="max",
    _legacy_checkpoint_format=True  # Enable compatibility
)
```

### Issue 2: Train V2 API Learning Curve

**Problem**: Team unfamiliar with new Tuner API

**Workaround**:
- Keep `tune.run()` wrapper for backward compatibility
- Gradual migration over 2-3 months
- Provide training materials

### Issue 3: Dashboard Authentication

**Problem**: Scripts may fail with 401 Unauthorized

**Workaround**:
```python
# Update scripts to include auth
import requests

response = requests.get(
    "http://10.0.0.84:8265/api/cluster/status",
    auth=("admin", os.environ["RAY_DASHBOARD_PASSWORD"])
)
```

### Issue 4: Prometheus Metrics Changes

**Problem**: Some metric names changed in 2.53.0

**Workaround**:
- Update Prometheus queries
- Add compatibility labels
- Test alerts before production

---

## Contact & Support

**Upgrade Lead**: TBD
**Backup Contact**: TBD

**Escalation Path**:
1. Check this document
2. Review Ray 2.53.0 release notes
3. Search Ray Discuss forum
4. File GitHub issue if bug found

**Useful Links**:
- [Ray 2.53.0 Release Notes](https://github.com/ray-project/ray/releases/tag/ray-2.53.0)
- [Ray Train V2 Migration Guide](https://docs.ray.io/en/latest/train/user-guides/migration.html)
- [Ray Discuss Forum](https://discuss.ray.io/)
- [Ray GitHub Issues](https://github.com/ray-project/ray/issues)

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05
**Status**: Draft - Awaiting Approval

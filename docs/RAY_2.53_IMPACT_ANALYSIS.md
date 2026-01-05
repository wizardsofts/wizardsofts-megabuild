# Ray 2.53.0 Upgrade Impact Analysis

**Created**: 2026-01-05
**Status**: Planning Phase

---

## Summary

This document analyzes all components impacted by the Ray 2.40.0 → 2.53.0 upgrade.

---

## 🔴 HIGH IMPACT - Code Changes Required

### 1. TARP-DRL Training Code

**File**: `apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`
**Location**: Server 84 (`/opt/wizardsofts-megabuild/apps/gibd-quant-agent/`)
**Lines Impacted**: 355-400 (approximately)

#### Current Ray 2.40.0 API Usage:

```python
# Imports
from ray import tune

# Training execution (line ~383-390)
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

# Checkpoint retrieval (line ~391-399)
best_checkpoint = analysis.get_best_checkpoint(
    trial=analysis.get_best_trial('episode_reward')
)
agent.load(os.path.join(best_checkpoint, "checkpoint.pt"))
```

#### Required Changes for Ray 2.53.0:

```python
# NEW imports
from ray import tune
from ray.train import RunConfig, ScalingConfig, CheckpointConfig
from ray.tune import Tuner, TuneConfig

# NEW training execution
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

results = tuner.fit()

# NEW checkpoint retrieval
best_result = results.get_best_result(
    metric="episode_reward",
    mode="max"
)
best_checkpoint = best_result.checkpoint

# NEW checkpoint loading
with best_checkpoint.as_directory() as checkpoint_dir:
    checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.pt")
    agent.load(checkpoint_path)
```

**Effort**: 2-3 days
**Risk**: Medium-High (core training functionality)
**Testing Required**: Full regression suite

---

### 2. Checkpoint Save/Load Logic

**File**: `apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`
**Class**: `PPOTrainer`
**Methods**: `save_checkpoint()`, `load_checkpoint()`

#### Current Implementation (line ~287-309):

```python
def save_checkpoint(self, checkpoint_dir: str) -> str:
    checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.pt")
    self.agent.save(checkpoint_path)
    return checkpoint_dir

def load_checkpoint(self, checkpoint_path: str):
    self.agent.load(checkpoint_path)
```

#### Compatibility Considerations:

- ✅ `save_checkpoint()` signature unchanged (compatible)
- ⚠️ `load_checkpoint()` may receive Checkpoint object instead of string path
- ⚠️ Need to verify checkpoint directory structure compatibility

**Effort**: 1 day
**Risk**: Medium (potential checkpoint incompatibility)
**Testing Required**: Save/load cycle tests

---

## 🟡 MEDIUM IMPACT - Configuration Changes

### 3. Ray Docker Images

#### Ray Head Node

**File**: `infrastructure/distributed-ml/ray/Dockerfile.ray-head`

**Current**:
```dockerfile
FROM rayproject/ray:2.40.0-py310
RUN pip install ray[tune,serve,data]==2.40.0
```

**Updated**:
```dockerfile
FROM rayproject/ray:2.53.0-py310
RUN pip install ray[tune,serve,data]==2.53.0
```

**Effort**: 30 minutes
**Risk**: Low (straightforward change)
**Testing Required**: Build verification

#### Ray Workers

**File**: `infrastructure/distributed-ml/ray/Dockerfile.ray-worker`

**Current**:
```dockerfile
FROM rayproject/ray:2.40.0-py310
RUN pip install ray[tune,serve,data]==2.40.0
```

**Updated**:
```dockerfile
FROM rayproject/ray:2.53.0-py310
RUN pip install ray[tune,serve,data]==2.53.0
```

**Effort**: 30 minutes
**Risk**: Low (straightforward change)
**Testing Required**: Build verification

---

### 4. Environment Configuration

**File**: `infrastructure/distributed-ml/ray/.env.ray`

**Current Variables**:
```bash
RAY_ADDRESS=10.0.0.84:6379
RAY_DASHBOARD_HOST=10.0.0.84
RAY_DASHBOARD_PORT=8265
RAY_REDIS_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD
RAY_object_store_memory=2000000000
RAY_NUM_CPUS=4
RAY_NUM_GPUS=0
```

**New Variables to Add**:
```bash
# REQUIRED for Ray 2.53.0
RAY_TRAIN_V2_ENABLED=1

# RECOMMENDED for production security
RAY_DASHBOARD_AUTH_USERNAME=admin
RAY_DASHBOARD_AUTH_PASSWORD=${SECURE_PASSWORD}

# OPTIONAL performance tuning
RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES=1
RAY_memory_monitor_refresh_ms=100
```

**Effort**: 15 minutes
**Risk**: Low (additive changes)
**Testing Required**: Environment variable verification

---

### 5. Docker Compose Files

**Files Potentially Impacted**:
- `infrastructure/distributed-ml/ray/docker-compose.ray-head.yml`
- `infrastructure/distributed-ml/ray/docker-compose.ray-workers-multi.yml`

**Changes Required**:
- Update image tags if using explicit versions
- Add new environment variables
- No structural changes expected

**Effort**: 30 minutes per file
**Risk**: Low (configuration only)
**Testing Required**: Deployment verification

---

## 🟢 LOW IMPACT - Verification Only

### 6. Cleanup Scripts

**Files**:
- `scripts/cleanup_ray_workers_smart.sh`
- `scripts/deploy_ray_cleanup.sh`

**Impact Analysis**:
- ✅ Scripts use Docker API, not Ray API (version-agnostic)
- ✅ /tmp directory paths unlikely to change
- ✅ Container naming conventions unchanged
- ⚠️ Should verify after upgrade as sanity check

**Effort**: 1 hour (testing only)
**Risk**: Very Low
**Testing Required**: Run cleanup manually after upgrade

---

### 7. Prometheus Monitoring

**File**: `infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml`

**Current Alerts**:
- `RayWorkerLargeTmpDirectory`
- `RayWorkerCriticalTmpDirectory`
- `RayWorkerDiskUsageHigh`
- `RayWorkerDiskCritical`

**Impact Analysis**:
- ✅ Alerts use cAdvisor metrics (version-agnostic)
- ✅ Node exporter metrics unchanged
- ⚠️ Ray 2.53.0 adds new metrics (optional to use)

**New Metrics Available** (optional to add):
- `ray_serve_deployment_request_counter`
- `ray_serve_deployment_replica_starts`
- `ray_data_spilled_bytes_total`
- `ray_data_cpu_usage_cores`

**Effort**: 2 hours (optional enhancements)
**Risk**: Very Low
**Testing Required**: Alert verification in Grafana

---

## 📊 Dependency Matrix

### Direct Dependencies

| Dependency | Current | Compatible with Ray 2.53.0? | Action Required |
|------------|---------|------------------------------|-----------------|
| **Python** | 3.10 | ✅ Yes (3.10, 3.11, 3.12 supported) | None |
| **PyTorch** | 2.1.2 | ✅ Yes (no strict requirement) | None |
| **Pandas** | 2.1.4 | ✅ Yes (≥1.3 required) | None |
| **NumPy** | 1.26.3 | ✅ Yes (≥1.20 required) | None |
| **scikit-learn** | 1.4.0 | ✅ Yes | None |
| **xgboost** | 2.0.3 | ✅ Yes | None |

### Ray-Specific Dependencies

| Component | Ray 2.40.0 | Ray 2.53.0 | Breaking Change? |
|-----------|------------|------------|------------------|
| **tune.run()** | Supported | ⚠️ Deprecated | Yes - migrate to Tuner |
| **Checkpoint API** | String paths | Checkpoint objects | Yes - update loading |
| **storage_path** | Supported | Supported | No |
| **runtime_env** | Supported | Supported | No |

---

## 🔧 Testing Requirements

### Unit Tests

- [ ] Test `train_ppo.py` training loop
- [ ] Test checkpoint save
- [ ] Test checkpoint load
- [ ] Test agent initialization
- [ ] Test environment creation

### Integration Tests

- [ ] Single-epoch distributed training
- [ ] Multi-epoch training with checkpoints
- [ ] Checkpoint resumption after failure
- [ ] Worker failure recovery
- [ ] Cleanup script execution during training

### Performance Tests

- [ ] Baseline training time (Ray 2.40.0)
- [ ] Upgraded training time (Ray 2.53.0)
- [ ] Memory usage comparison
- [ ] Disk space usage comparison
- [ ] Checkpoint save/load time

### Regression Tests

- [ ] Verify training results unchanged
- [ ] Verify checkpoint format compatibility
- [ ] Verify cleanup system still works
- [ ] Verify Prometheus metrics correct
- [ ] Verify Ray dashboard accessible

---

## 📝 Documentation Updates Required

### Code Documentation

- [ ] Update `apps/gibd-quant-agent/README.md` (if exists)
- [ ] Add docstrings for new Train V2 API usage
- [ ] Document checkpoint format changes
- [ ] Update inline comments

### Infrastructure Documentation

- [ ] Update `infrastructure/distributed-ml/README.md`
- [ ] Document new Ray 2.53.0 features
- [ ] Update deployment commands
- [ ] Update troubleshooting guide

### Operational Documentation

- [ ] Update `CLAUDE.md` with upgrade summary
- [ ] Create `docs/RAY_2.53_OPERATIONS.md`
- [ ] Update runbooks for common issues
- [ ] Document rollback procedure

---

## ⏱️ Effort Estimates

### By Phase

| Phase | Effort | Calendar Time |
|-------|--------|---------------|
| **Preparation** | 40 hours | Week 1-2 |
| **Development** | 32 hours | Week 2-3 |
| **Testing** | 24 hours | Week 2-3 |
| **Deployment** | 16 hours | Week 3-4 |
| **Documentation** | 16 hours | Week 4 |
| **Monitoring** | 8 hours | Week 4+ |
| **TOTAL** | **136 hours** | **4 weeks** |

### By Role

| Role | Effort | Tasks |
|------|--------|-------|
| **ML Engineer** | 64 hours | Code migration, testing, tuning |
| **DevOps Engineer** | 48 hours | Deployment, monitoring, rollback |
| **QA Engineer** | 24 hours | Test planning, execution, validation |
| **TOTAL** | **136 hours** | |

---

## 🚨 Risk Assessment

### Critical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Checkpoint incompatibility** | Medium | High | Test load/save cycle extensively |
| **Training failures** | Medium | High | Thorough testing, rollback plan ready |
| **Performance degradation** | Low | Medium | Benchmark before/after |
| **Cluster downtime** | Low | High | Rolling upgrade, maintenance window |
| **Code bugs** | Medium | Medium | Extensive unit/integration tests |

### Medium Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **API learning curve** | High | Low | Training materials, documentation |
| **Cleanup script issues** | Low | Medium | Test after upgrade |
| **Prometheus metric changes** | Low | Low | Verify alerts work |
| **Team resistance** | Medium | Low | Show performance benefits |

---

## ✅ Success Criteria

### Performance Targets

- ✅ Training time reduced by ≥10%
- ✅ Memory usage reduced by ≥20%
- ✅ Checkpoint save/load ≤10% slower
- ✅ No increase in failure rate

### Stability Targets

- ✅ Zero data loss
- ✅ Zero checkpoint corruption
- ✅ <5% failure rate in first week
- ✅ Cleanup system maintains disk usage

### Operational Targets

- ✅ Rollout completed in 4 weeks
- ✅ Zero production downtime
- ✅ Team trained on new API
- ✅ Documentation complete

---

## 📞 Contacts

**Code Owner**: ML Engineering Team
**Infrastructure Owner**: DevOps Team
**Decision Maker**: TBD

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05

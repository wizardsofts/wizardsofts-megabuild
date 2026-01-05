# Ray 2.53.0 Upgrade Quick Checklist

**Use this checklist to track upgrade progress. Check off items as completed.**

---

## 📋 Pre-Flight Checklist

- [ ] Stakeholder approval obtained
- [ ] Maintenance window scheduled (Date: __________)
- [ ] Team notified of upgrade timeline
- [ ] Read full upgrade plan ([RAY_2.53_UPGRADE_PLAN.md](RAY_2.53_UPGRADE_PLAN.md))

---

## 🔐 Security & Preparation

- [ ] Run `pip-audit` on Ray 2.53.0
- [ ] Review CVE list - no critical issues
- [ ] Backup current cluster configuration
- [ ] Backup training checkpoints
- [ ] Document baseline performance metrics
- [ ] Generate secure dashboard password

---

## 💻 Code Changes

### Files to Update

- [ ] `infrastructure/distributed-ml/ray/Dockerfile.ray-head`
  - Change: `rayproject/ray:2.40.0-py310` → `rayproject/ray:2.53.0-py310`

- [ ] `infrastructure/distributed-ml/ray/Dockerfile.ray-worker`
  - Change: `rayproject/ray:2.40.0-py310` → `rayproject/ray:2.53.0-py310`

- [ ] `infrastructure/distributed-ml/ray/.env.ray`
  - Add: `RAY_TRAIN_V2_ENABLED=1`
  - Add: `RAY_DASHBOARD_AUTH_USERNAME=admin`
  - Add: `RAY_DASHBOARD_AUTH_PASSWORD=<secure-password>`

- [ ] `apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`
  - Migrate: `tune.run()` → `Tuner` API
  - Update: Checkpoint loading logic
  - Add: `RunConfig`, `CheckpointConfig`, `TuneConfig` imports

---

## 🧪 Testing Phase

- [ ] Create feature branch: `feature/ray-2.53-upgrade`
- [ ] Update training code locally
- [ ] Run unit tests
- [ ] Test checkpoint save/load
- [ ] Build Docker images
- [ ] Deploy test worker on Server 80
- [ ] Run distributed training test (5 epochs)
- [ ] Verify cleanup script compatibility
- [ ] Benchmark performance vs 2.40.0
- [ ] Document test results

---

## 🚀 Deployment Phase

### Server 84 (Head Node)

- [ ] Backup configuration
- [ ] Pull latest code
- [ ] Rebuild Docker image
- [ ] Stop Ray head gracefully
- [ ] Deploy Ray 2.53.0 head
- [ ] Verify dashboard accessible
- [ ] Check GCS health
- [ ] Monitor for 30 minutes

### Server 81 (Workers)

- [ ] Check disk space
- [ ] Backup configuration
- [ ] Pull latest code
- [ ] Rebuild Docker images
- [ ] Stop workers gracefully
- [ ] Deploy Ray 2.53.0 workers
- [ ] Verify worker connection
- [ ] Monitor for 15 minutes

### Server 82 (Workers)

- [ ] Check disk space
- [ ] Backup configuration
- [ ] Pull latest code
- [ ] Rebuild Docker images
- [ ] Stop workers gracefully
- [ ] Deploy Ray 2.53.0 workers
- [ ] Verify worker connection
- [ ] Monitor for 15 minutes

### Server 80 (Workers)

- [ ] Check disk space
- [ ] Backup configuration
- [ ] Pull latest code
- [ ] Rebuild Docker images
- [ ] Stop workers gracefully
- [ ] Deploy Ray 2.53.0 workers
- [ ] Verify worker connection
- [ ] Monitor for 15 minutes

---

## ✅ Post-Deployment Validation

- [ ] Verify full cluster health (11+ nodes)
- [ ] Run end-to-end training test (50 epochs)
- [ ] Monitor training for 2-4 hours
- [ ] Verify performance improvements:
  - [ ] Training time: _______ (target: -15% to -25%)
  - [ ] Memory usage: _______ (target: -30% to -50%)
  - [ ] No increase in failures
- [ ] Check cleanup script logs
- [ ] Verify Prometheus alerts
- [ ] Monitor for 48-72 hours

---

## 📝 Documentation

- [ ] Update CLAUDE.md with upgrade summary
- [ ] Update `infrastructure/distributed-ml/README.md`
- [ ] Create `docs/RAY_2.53_OPERATIONS.md`
- [ ] Document performance results
- [ ] Conduct team knowledge transfer

---

## 🔄 Rollback (If Needed)

**Only if critical issues found:**

- [ ] Stop all training jobs
- [ ] Rollback head node (Server 84)
- [ ] Rollback workers (Servers 80, 81, 82)
- [ ] Restore training code
- [ ] Verify rollback successful
- [ ] Document rollback reason
- [ ] Schedule retry (if applicable)

---

## ✨ Success Criteria

**Check all before declaring success:**

- [ ] Training performance improved ≥10%
- [ ] Memory usage reduced ≥20%
- [ ] No increase in failure rate
- [ ] Cleanup system works correctly
- [ ] No critical bugs found in 1 week
- [ ] Team trained on new API
- [ ] Documentation complete

---

## 📊 Performance Comparison

### Baseline (Ray 2.40.0)

| Metric | Value |
|--------|-------|
| Training time (50 epochs) | _____ minutes |
| Memory per worker | _____ GB |
| Checkpoint save time | _____ seconds |
| Disk /tmp growth | _____ GB/hour |
| Worker restart count | _____ per day |

### Post-Upgrade (Ray 2.53.0)

| Metric | Value | Change |
|--------|-------|--------|
| Training time (50 epochs) | _____ minutes | _____ % |
| Memory per worker | _____ GB | _____ % |
| Checkpoint save time | _____ seconds | _____ % |
| Disk /tmp growth | _____ GB/hour | _____ % |
| Worker restart count | _____ per day | _____ % |

---

## 🆘 Emergency Contacts

- **Upgrade Lead**: __________________
- **Backup**: __________________
- **On-Call**: __________________

## 📞 Escalation

1. Check [RAY_2.53_UPGRADE_PLAN.md](RAY_2.53_UPGRADE_PLAN.md)
2. Search [Ray Discuss](https://discuss.ray.io/)
3. Contact upgrade lead
4. File [GitHub issue](https://github.com/ray-project/ray/issues)

---

**Checklist Version**: 1.0
**Created**: 2026-01-05
**Status**: Ready for Use

# Monitoring Consolidation Cleanup - COMPLETED

**Date**: 2026-01-09  
**Status**: ✅ COMPLETE

## Summary

Monitoring infrastructure successfully consolidated from `infrastructure/auto-scaling/monitoring/` to `infrastructure/monitoring/`. All code and documentation references updated. Final cleanup tasks documented below.

---

## Completed Tasks

### ✅ Phase 1: Configuration Consolidation

- [x] Prometheus configuration moved to `infrastructure/monitoring/prometheus/`
  - `prometheus.yml` - main config with scrape jobs and alertmanager targets
  - `infrastructure-alerts.yml` - infrastructure alert rules
  - `security-alerts.yml` - security-related alert rules
- [x] Grafana configuration moved to `infrastructure/monitoring/grafana/`
  - `grafana.ini` - config with Keycloak OAuth setup
  - `provisioning/datasources.yml` - Prometheus, Loki, other datasources
  - `provisioning/dashboards.yml` - auto-provisioning config
  - `dashboards/` - all consolidated dashboards (JSON files)
- [x] Alertmanager configuration moved to `infrastructure/monitoring/alertmanager/`
  - `alertmanager.yml` - alert routing, receivers, grouping
- [x] Promtail configuration moved to `infrastructure/monitoring/promtail/`
  - `promtail-config.yml` - log scraping config for Docker logs

### ✅ Phase 2: Docker Compose & Resource Management

- [x] `infrastructure/monitoring/docker-compose.yml` created with:
  - Resource limits (CPU, memory) for all services
  - Security hardening (no-new-privileges, cap_drop: ALL)
  - Health checks for container monitoring
  - Backup volume mounts (/mnt/monitoring-backups/\*)
  - Loki retention policy (7 days)

### ✅ Phase 3: Backup Strategy

- [x] `scripts/backup-monitoring.sh` created with:
  - Prometheus snapshot API backup
  - Grafana data export (dashboards, datasources, users)
  - Loki configuration backup
  - Alertmanager configuration backup
  - Config file backups
  - NFS mount validation
  - 7-day retention policy
  - Comprehensive logging

### ✅ Phase 4: Integration Tests & CI/CD

- [x] `infrastructure/monitoring/tests/integration-tests.sh` created with:
  - 50+ integration tests covering:
    - Container health checks (running, restart policies, health status)
    - API endpoints (Prometheus, Grafana, Loki, Alertmanager)
    - Data flow (metrics collection, log ingestion, datasources, dashboards)
    - Configuration validation (YAML syntax, Docker Compose)
    - Resource limits enforcement
    - Backup script functionality
    - NFS mount status
- [x] `.gitlab/ci/infra.gitlab-ci.yml` updated:
  - `validate-monitoring-config` path: `infrastructure/monitoring/`
  - `deploy-monitoring` path: `infrastructure/monitoring/`
  - New `test-monitoring-integration` job (runs shell tests via SSH)
  - Mandatory test stage after deployment

### ✅ Phase 5: Documentation Updates

Updated all references from `infrastructure/auto-scaling/monitoring/` to `infrastructure/monitoring/` in:

- [x] `CLAUDE.md` - Prometheus Alerts path
- [x] `docs/deployment/MONITORING_IMPLEMENTATION_GUIDE.md` - All 6 instances
- [x] `docs/deployment/SERVER_82_DEPLOYMENT.md` - 2 instances
- [x] `docs/handoffs/2026-01-09-monitoring-consolidation-complete.md` - Reference documentation

---

## Manual Cleanup Remaining

The following items require manual deletion via Git or file system (not available through AI tools):

### 1. Delete Obsolete Dashboards

**Location**: `infrastructure/monitoring/grafana/dashboards/`

Files to delete:

- `server-81-security.json` - Old server-specific dashboard (superseded by all-servers-security.json)
- `server-84-security.json` - Old server-specific dashboard (superseded by all-servers-security.json)

**Command to delete**:

```bash
rm infrastructure/monitoring/grafana/dashboards/server-81-security.json
rm infrastructure/monitoring/grafana/dashboards/server-84-security.json
git add -u infrastructure/monitoring/grafana/dashboards/
git commit -m "cleanup: remove obsolete server-specific security dashboards"
```

### 2. Remove Duplicate Promtail Config

**Location**: `infrastructure/monitoring/promtail-config.yml` (root level)

This is a duplicate of the actual config at `infrastructure/monitoring/promtail/promtail-config.yml`

**Command to delete**:

```bash
rm infrastructure/monitoring/promtail-config.yml
git add -u
git commit -m "cleanup: remove duplicate promtail config"
```

### 3. Remove Auto-Scaling Monitoring Directory

**Location**: `infrastructure/auto-scaling/monitoring/`

The entire directory is now obsolete. All configs have been consolidated into `infrastructure/monitoring/`.

**Command to delete**:

```bash
rm -rf infrastructure/auto-scaling/monitoring/
git add -u infrastructure/auto-scaling/
git commit -m "cleanup: remove obsolete auto-scaling/monitoring directory after consolidation"
```

---

## Verification Checklist

After cleanup, verify:

```bash
# 1. Confirm monitoring directory exists with all configs
ls -la infrastructure/monitoring/{prometheus,grafana,alertmanager,promtail}/

# 2. Verify no auto-scaling/monitoring references remain
grep -r "auto-scaling/monitoring" --include="*.md" --include="*.yaml" --include="*.yml" .

# 3. Check docker-compose deploys correctly
docker-compose -f infrastructure/monitoring/docker-compose.yml config > /dev/null

# 4. Run integration tests
bash infrastructure/monitoring/tests/integration-tests.sh

# 5. Verify CI/CD pipeline paths are correct
grep -A5 "path: infrastructure/monitoring" .gitlab/ci/infra.gitlab-ci.yml
```

---

## Files Created This Session

| File                                                             | Purpose                           | Status      |
| ---------------------------------------------------------------- | --------------------------------- | ----------- |
| `infrastructure/monitoring/prometheus/prometheus.yml`            | Consolidated Prometheus config    | ✅ Complete |
| `infrastructure/monitoring/prometheus/infrastructure-alerts.yml` | Infrastructure alert rules        | ✅ Complete |
| `infrastructure/monitoring/alertmanager/alertmanager.yml`        | Alert routing config              | ✅ Complete |
| `infrastructure/monitoring/promtail/promtail-config.yml`         | Log scraping config               | ✅ Complete |
| `infrastructure/monitoring/grafana/grafana.ini`                  | Grafana config with OAuth         | ✅ Complete |
| `infrastructure/monitoring/grafana/provisioning/datasources.yml` | Datasource definitions            | ✅ Complete |
| `infrastructure/monitoring/docker-compose.yml`                   | Service orchestration with limits | ✅ Complete |
| `scripts/backup-monitoring.sh`                                   | Backup script with NFS support    | ✅ Complete |
| `infrastructure/monitoring/tests/integration-tests.sh`           | 50+ integration tests             | ✅ Complete |
| `.gitlab/ci/infra.gitlab-ci.yml`                                 | Updated CI/CD paths and test job  | ✅ Complete |

---

## Files Modified This Session

| File                                                 | Changes                                                       | Status      |
| ---------------------------------------------------- | ------------------------------------------------------------- | ----------- |
| `CLAUDE.md`                                          | Updated Prometheus path: auto-scaling/monitoring → monitoring | ✅ Complete |
| `docs/deployment/MONITORING_IMPLEMENTATION_GUIDE.md` | Updated 6 path references                                     | ✅ Complete |
| `docs/deployment/SERVER_82_DEPLOYMENT.md`            | Updated 2 path references                                     | ✅ Complete |

---

## Next Steps

1. **Manual Cleanup**: Execute the three deletion commands listed above
2. **Verification**: Run the verification checklist
3. **Testing**: Deploy to staging and run `scripts/backup-monitoring.sh` manually
4. **Deployment (CI/CD only)**:

- Push changes → CI runs `validate-monitoring-config`, `deploy-monitoring`, `test-monitoring-integration`
- Confirm `test-monitoring-integration` passes on staging (SSH tests run automatically)
- Promote to production via the same pipeline (no manual docker-compose deploys)

5. **Final Commit**: Push all changes to GitLab

### Deployment Runbook (CI/CD)

1. **Pre-deploy**

- Ensure manual cleanup is committed and pushed
- Verify NFS mount `/mnt/monitoring-backups` is present on target hosts
- Confirm secrets/env files for monitoring stack are present (no changes expected)

2. **Staging deploy**

- Trigger pipeline on your branch (push) or MR
- Pipeline stages: `validate-monitoring-config` → `deploy-monitoring` → `test-monitoring-integration`
- After deploy, run `scripts/backup-monitoring.sh` once on staging to confirm backups succeed

3. **Production deploy**

- Merge to main to trigger production pipeline
- Monitor `test-monitoring-integration` output; ensure all sections pass
- Spot-check Grafana/Prometheus/Alertmanager UIs and log ingestion

4. **Post-deploy**

- Review alerts for noise/regressions
- Confirm backup artifacts written to `/mnt/monitoring-backups/*`
- Close out cleanup tasks in this handoff

**Post-Cleanup Commit**:

```bash
git add -A
git commit -m "cleanup: complete monitoring consolidation - remove obsolete configs and directories"
git push origin $(git rev-parse --abbrev-ref HEAD)
```

---

## Implementation Notes

**Why shell-based tests instead of pytest?**

- Simpler SSH execution in CI/CD pipeline
- No Python dependencies required
- Better compatibility with containerized services
- Faster feedback loop

**Resource Limits Applied**:

- Prometheus: 2.0 CPU / 2G memory (limits), 1.0 CPU / 1G memory (reservations)
- Grafana: 1.0 CPU / 512M memory (limits), 0.5 CPU / 256M memory (reservations)
- Loki: 1.0 CPU / 1G memory (limits), 0.5 CPU / 512M memory (reservations)
- All services: `security_opt: no-new-privileges: true` and `cap_drop: [ALL]`

**Backup Strategy**:

- Location: `/mnt/monitoring-backups/` (NFS mounted)
- Retention: 7 days
- Frequency: Recommended daily via cron
- Includes: Prometheus snapshots, Grafana exports, Loki configs, Alertmanager configs

---

## Consolidated Configuration Map

| Component         | Old Location                                           | New Location                                           |
| ----------------- | ------------------------------------------------------ | ------------------------------------------------------ |
| Prometheus        | `infrastructure/auto-scaling/monitoring/prometheus/`   | `infrastructure/monitoring/prometheus/`                |
| Grafana           | `infrastructure/auto-scaling/monitoring/grafana/`      | `infrastructure/monitoring/grafana/`                   |
| Alertmanager      | `infrastructure/auto-scaling/monitoring/alertmanager/` | `infrastructure/monitoring/alertmanager/`              |
| Promtail          | `infrastructure/auto-scaling/monitoring/promtail/`     | `infrastructure/monitoring/promtail/`                  |
| Docker Compose    | `infrastructure/auto-scaling/docker-compose.yml`       | `infrastructure/monitoring/docker-compose.yml`         |
| Integration Tests | N/A (new)                                              | `infrastructure/monitoring/tests/integration-tests.sh` |
| Backup Script     | N/A (new)                                              | `scripts/backup-monitoring.sh`                         |

---

**Consolidation Complete** ✅  
**Ready for Final Cleanup and Deployment** 🚀

# Monitoring Infrastructure Consolidation & Upgrade Plan

**Date:** 2026-01-09
**Status:** APPROVED FOR IMPLEMENTATION
**Compliance:** AGENT.md § 0 (Execute Model), § 1.3, § 3.6 (Breaking Changes), § 5.2 (Script-First), § 13 (Docker Deployment)

---

## Executive Summary

Consolidate monitoring infrastructure into `infrastructure/monitoring/`, add resource constraints and backup mechanism, delete auto-scaling folder entirely, and implement via CI/CD pipeline.

### Current State (Verified via SSH)

| Service | Current Version | Running | Status |
|---------|-----------------|---------|--------|
| Prometheus | v2.47.0 | Yes | Up 2 days |
| Grafana | 10.2.0 | Yes | Up 2 days |
| Loki | 2.9.2 | Yes | Up 3 days (healthy) |
| Promtail | 2.9.2 | Yes | Up 3 days |
| Alertmanager | v0.26.0 | Yes | Up 3 days |
| Node Exporter | v1.6.1 | Yes | Up 3 days |
| cAdvisor | v0.47.2 | Yes | Up 3 days (healthy) |

### Key Changes Required

1. **Consolidate configs into `infrastructure/monitoring/`** (use latest from auto-scaling)
2. **Add resource constraints** to all containers
3. **Add backup mechanism** for Prometheus/Grafana data
4. **Delete dashboards:** `server-81-security.json`, `server-84-security.json`, `autoscaling-dashboard.json`
5. **Delete entire `infrastructure/auto-scaling/` folder**
6. **Update CI/CD pipeline** to use new monitoring path
7. **Add integration tests** as mandatory in pipeline

---

## Phase 1: Consolidation

### 1.1 Files to COPY from `auto-scaling/monitoring/` to `monitoring/`

Based on git commits, `auto-scaling/monitoring/` has the latest configs (commit 7d2d8ba):

| Source File | Destination | Action |
|-------------|-------------|--------|
| `prometheus/prometheus.yml` | `monitoring/prometheus/prometheus.yml` | REPLACE (auto-scaling is more complete) |
| `prometheus/infrastructure-alerts.yml` | `monitoring/prometheus/` | COPY |
| `prometheus/security-alerts.yml` | `monitoring/prometheus/` | COPY |
| `alertmanager/alertmanager.yml` | `monitoring/alertmanager/` | CREATE DIR + COPY |
| `grafana/grafana.ini` | `monitoring/grafana/` | COPY |
| `grafana/provisioning/*` | `monitoring/grafana/provisioning/` | COPY ENTIRE STRUCTURE |
| `promtail/config.yml` | `monitoring/promtail/promtail-config.yml` | COPY |

### 1.2 Dashboards to KEEP (in `monitoring/grafana/dashboards/`)

| Dashboard | Source | Keep? |
|-----------|--------|-------|
| `node-exporter.json` | monitoring/ | ✅ KEEP |
| `docker-containers.json` | monitoring/ | ✅ KEEP |
| `all-servers-executive.json` | monitoring/ | ✅ KEEP |
| `all-servers-security.json` | monitoring/ | ✅ KEEP |
| `server-80-executive.json` | auto-scaling/ | ✅ KEEP (copy) |
| `server-80-security.json` | auto-scaling/ | ✅ KEEP (copy) |
| `dba-dashboard.json` | auto-scaling/ | ✅ KEEP (copy) |
| `devops-dashboard.json` | auto-scaling/ | ✅ KEEP (copy) |
| `mlops-dashboard.json` | auto-scaling/ | ✅ KEEP (copy) |

### 1.3 Dashboards to DELETE

| Dashboard | Reason |
|-----------|--------|
| `server-81-security.json` | User request |
| `server-84-security.json` | User request |
| `autoscaling-dashboard.json` | User request - auto-scaling not used |

---

## Phase 2: Resource Constraints & Security Hardening

### 2.1 Updated `docker-compose.yml` with Resource Limits

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.47.0
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    security_opt:
      - no-new-privileges:true
    user: "65534:65534"

  grafana:
    image: grafana/grafana:10.2.0
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    security_opt:
      - no-new-privileges:true
    user: "472:472"

  loki:
    image: grafana/loki:2.9.2
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    security_opt:
      - no-new-privileges:true

  promtail:
    image: grafana/promtail:2.9.2
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    security_opt:
      - no-new-privileges:true

  alertmanager:
    image: prom/alertmanager:v0.26.0
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    security_opt:
      - no-new-privileges:true

  node-exporter:
    image: prom/node-exporter:v1.6.1
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    security_opt:
      - no-new-privileges:true
    read_only: true

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.2
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    security_opt:
      - no-new-privileges:true
```

### 2.2 Backup Mechanism

**Add backup volumes and script:**

```yaml
# In docker-compose.yml
volumes:
  prometheus-data:
  grafana-data:
  loki-data:
  alertmanager-data:
  # Backup mount
  monitoring-backups:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/Backups/server/monitoring
```

**Create `scripts/backup-monitoring.sh`:**

```bash
#!/bin/bash
# Backup monitoring data per AGENT.md § 9.1
BACKUP_DIR="/mnt/data/Backups/server/monitoring"
DATE=$(date +%Y%m%d-%H%M%S)

# Backup Prometheus data
docker run --rm -v prometheus-data:/data -v $BACKUP_DIR:/backup alpine \
  tar czf /backup/prometheus-$DATE.tar.gz -C /data .

# Backup Grafana data
docker run --rm -v grafana-data:/data -v $BACKUP_DIR:/backup alpine \
  tar czf /backup/grafana-$DATE.tar.gz -C /data .

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup complete: $BACKUP_DIR"
```

---

## Phase 3: CI/CD Integration

### 3.1 Update `.gitlab/ci/infra.gitlab-ci.yml`

**Changes required:**

1. Update `validate-monitoring-config` job paths from `auto-scaling/monitoring` → `monitoring`
2. Update `deploy-monitoring` job paths
3. Add integration tests as mandatory

```yaml
# Updated monitoring validation job
validate-monitoring-config:
  stage: validate
  image: prom/prometheus:latest
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - infrastructure/monitoring/**/*
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master)$/'
      changes:
        - infrastructure/monitoring/**/*
  script:
    - |
      echo "Validating Prometheus configuration..."
      cd infrastructure/monitoring/prometheus
      promtool check config prometheus.yml
      promtool check rules infrastructure-alerts.yml
      promtool check rules security-alerts.yml
      echo "Prometheus configuration valid!"

      cd ../alertmanager
      amtool check-config alertmanager.yml
      echo "Alertmanager configuration valid!"

# Updated monitoring deployment job
deploy-monitoring:
  extends: .infra-deploy-template
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master)$/'
      changes:
        - infrastructure/monitoring/**/*
      when: manual
  script:
    - |
      echo "Deploying Monitoring Stack to $DEPLOY_HOST..."

      # Sync monitoring configuration (new path)
      rsync -avz infrastructure/monitoring/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/infrastructure/monitoring/"

      # Execute deployment
      ssh "$DEPLOY_USER@$DEPLOY_HOST" << 'EOF'
      set -e
      cd /opt/wizardsofts-megabuild/infrastructure/monitoring

      # Create backup before deployment
      ./scripts/backup-monitoring.sh || true

      # Deploy
      docker compose down || true
      docker compose up -d

      echo "Monitoring stack deployment complete!"
      docker compose ps
      EOF
  environment:
    name: monitoring
    url: http://10.0.0.84:3002
  needs:
    - job: validate-monitoring-config
    - job: test-monitoring-integration
      optional: false  # MANDATORY

# NEW: Integration test job (MANDATORY)
test-monitoring-integration:
  stage: test
  image: python:3.11-slim
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - infrastructure/monitoring/**/*
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master)$/'
      changes:
        - infrastructure/monitoring/**/*
  before_script:
    - pip install pytest requests pyyaml
  script:
    - |
      echo "Running monitoring integration tests..."
      pytest infrastructure/monitoring/tests/ -v --tb=short
  artifacts:
    reports:
      junit: infrastructure/monitoring/tests/results.xml
    when: always
```

### 3.2 Create Test Framework

**Create `infrastructure/monitoring/tests/`:**

```
infrastructure/monitoring/tests/
├── conftest.py              # Shared fixtures
├── test_prometheus_config.py # Config syntax validation
├── test_alert_rules.py       # Alert rule validation
├── test_grafana_dashboards.py # Dashboard JSON validation
└── pytest.ini               # Pytest configuration
```

---

## Phase 4: Delete auto-scaling Folder

### 4.1 Files/Folders to DELETE

```bash
# Entire auto-scaling folder
rm -rf infrastructure/auto-scaling/
```

### 4.2 References to UPDATE

| File | Change |
|------|--------|
| `.gitlab/ci/infra.gitlab-ci.yml` | Remove all `auto-scaling` references |
| `CLAUDE.md` | Update monitoring documentation |
| `docs/deployment/MONITORING_IMPLEMENTATION_GUIDE.md` | Update paths |

---

## Implementation Order (CI/CD Driven)

### Step 1: Create Feature Branch
```bash
git checkout -b feature/monitoring-consolidation
```

### Step 2: Consolidate Configs
1. Copy latest configs from `auto-scaling/monitoring/` to `monitoring/`
2. Update `docker-compose.yml` with resource constraints
3. Add backup mechanism
4. Delete specified dashboards

### Step 3: Create Test Framework
1. Create `infrastructure/monitoring/tests/` directory
2. Add config validation tests
3. Add dashboard validation tests

### Step 4: Update CI/CD Pipeline
1. Update `.gitlab/ci/infra.gitlab-ci.yml`
2. Change paths from `auto-scaling/monitoring` → `monitoring`
3. Add mandatory integration test job

### Step 5: Delete auto-scaling Folder
1. Remove entire `infrastructure/auto-scaling/` directory
2. Update all references in documentation

### Step 6: Deploy via CI/CD
1. Push to feature branch
2. Create MR to master
3. Pipeline validates configs
4. Pipeline runs integration tests (mandatory)
5. Manual deploy approval
6. Verify deployment

---

## Files to Modify/Create

### New Files

| File | Purpose |
|------|---------|
| `infrastructure/monitoring/alertmanager/alertmanager.yml` | Alert routing config |
| `infrastructure/monitoring/prometheus/infrastructure-alerts.yml` | Infrastructure alert rules |
| `infrastructure/monitoring/grafana/grafana.ini` | Grafana config |
| `infrastructure/monitoring/grafana/provisioning/datasources.yml` | Datasource config |
| `infrastructure/monitoring/grafana/provisioning/dashboards.yml` | Dashboard provisioning |
| `infrastructure/monitoring/loki/loki-config.yml` | Loki config |
| `infrastructure/monitoring/tests/*.py` | Test files |
| `scripts/backup-monitoring.sh` | Backup script |

### Modified Files

| File | Change |
|------|--------|
| `infrastructure/monitoring/docker-compose.yml` | Add resource limits, backup volumes |
| `infrastructure/monitoring/prometheus/prometheus.yml` | Merge scrape configs |
| `.gitlab/ci/infra.gitlab-ci.yml` | Update monitoring paths, add tests |
| `CLAUDE.md` | Update monitoring documentation |

### Deleted Files/Folders

| Path | Reason |
|------|--------|
| `infrastructure/auto-scaling/` | Entire folder - user request |
| `infrastructure/monitoring/grafana/dashboards/server-81-security.json` | User request |
| `infrastructure/monitoring/grafana/dashboards/server-84-security.json` | User request |

---

## Verification Checklist

### Pre-Migration
- [ ] Backup current monitoring configs
- [ ] Export current Grafana dashboards
- [ ] Note current alert states

### Post-Migration (CI/CD Pipeline)
- [ ] `validate-monitoring-config` passes
- [ ] `test-monitoring-integration` passes
- [ ] All 7 containers running with resource limits
- [ ] Prometheus scrapes all targets
- [ ] Grafana loads dashboards
- [ ] Alertmanager receives alerts
- [ ] Backup mechanism works

### Documentation
- [ ] CLAUDE.md updated
- [ ] All auto-scaling references removed
- [ ] Session handoff created

---

## Rollback Plan

### Quick Rollback (5 minutes)
```bash
# In CI/CD or manually
git revert <commit>
ssh agent@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/monitoring && docker compose down && docker compose up -d"
```

### Full Restore (15 minutes)
```bash
# Restore from backup
BACKUP_FILE=$(ls -t /mnt/data/Backups/server/monitoring/pre-migration-*.tar.gz | head -1)
tar -xzf $BACKUP_FILE -C /opt/wizardsofts-megabuild/infrastructure/monitoring/
docker compose down && docker compose up -d
```

---

## Breaking Change Analysis (AGENT.md § 3.6)

### Consumers Affected

| Consumer | Impact | Mitigation |
|----------|--------|------------|
| Grafana Dashboards | 3 dashboards removed | None - per user request |
| CI/CD Pipeline | Path changes | Pipeline update in same commit |
| Documentation | References outdated | Update in same commit |
| Auto-scaling app | REMOVED | User confirmed not using |

### Consumer Scan Results

```bash
# References to auto-scaling/monitoring found:
# .gitlab/ci/infra.gitlab-ci.yml (4 references) → UPDATE
# CLAUDE.md (multiple references) → UPDATE
# docs/deployment/MONITORING_IMPLEMENTATION_GUIDE.md → UPDATE
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Config syntax errors | Low | Medium | CI/CD validation catches |
| Missing alert rules | Low | High | Copy all rules from auto-scaling |
| Dashboard migration | Low | Low | Keep most dashboards |
| Pipeline failure | Medium | Low | Test in MR first |

---

## References

- [AGENT.md](../../AGENT.md) - Agent instructions
- [GitLab Upgrade Handoff](../handoffs/2026-01-09-gitlab-upgrade/README.md) - Pattern reference
- [Current Infra CI/CD](../../.gitlab/ci/infra.gitlab-ci.yml) - Existing pipeline

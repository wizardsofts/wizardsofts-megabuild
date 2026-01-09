# GitLab Blocker Analysis & Resolution Plan

**Created:** 2026-01-08  
**Based on:** Ground truth investigation of GitLab infrastructure  
**Follows:** AGENT.md v1.6.1 conventions

---

## Goal

Resolve all GitLab integration blockers identified in ground truth investigation. Correct documentation mismatches and establish reliable monitoring/backup/security configuration.

---

## Ground Truth Reminders (from investigation)

**What docs said vs reality:**

| Component  | Documentation Claim                   | Actual Reality                               | Impact                          |
| ---------- | ------------------------------------- | -------------------------------------------- | ------------------------------- |
| Grafana    | "Down" / "Not accessible"             | UP 39 hours, listening :::3002               | Firewall blocks external access |
| Prometheus | "Down" / "Not accessible"             | UP 39 hours, listening :::9090               | Firewall blocks external access |
| NFS Backup | Mount at `/mnt/gitlab-backups`        | Should be `/mnt/data/Backups/server/gitlab/` | Non-standard path               |
| Test URLs  | Grafana at .80:3000, Prom at .80:9090 | Actually .84:3002 and .84:9090               | False negatives                 |

**Root causes:**

1. Services ARE running, firewall rules missing
2. Backup path doesn't follow standard convention
3. Test script checking wrong hosts
4. Security hardening not applied (SSH, rate limiting)

---

## Backup Convention (AGENT.md Section 9.1)

**All service backups MUST use:**

```
/mnt/data/Backups/server/<service-name>/
```

**For GitLab:**

```
/mnt/data/Backups/server/gitlab/
├── YYYY-MM-DD/           # Date-based subfolders (recommended for volume/retention)
│   ├── config/           # gitlab.rb, secrets
│   ├── database/         # PostgreSQL dumps
│   ├── repositories/     # Git repos
│   └── uploads/          # User uploads
```

**Why date-based subfolders:**

- Retention policy clarity (keep last 7 daily, 4 weekly, 12 monthly)
- Volume management (GitLab backups are large)
- Easy restore point selection

---

## Major Findings Summary

### 1. Monitoring Access (Grafana/Prometheus)

- **Severity:** Medium (was incorrectly marked Critical)
- **Root Cause:** UFW firewall blocks ports 3002, 9090
- **Current State:** Services UP and healthy on 10.0.0.84
- **Effort:** Low (firewall rules + test script update)

### 2. NFS Backup Configuration

- **Severity:** Low
- **Root Cause:** Non-standard backup path used
- **Current State:** /mnt/data exported from 10.0.0.80, accessible
- **Effort:** Low (mount + config update)

### 3. SSH Restrictions

- **Severity:** Medium
- **Root Cause:** Missing security hardening
- **Current State:** SSH allows password auth, no key restrictions
- **Effort:** Low (config changes)

### 4. Rate Limiting

- **Severity:** Low
- **Root Cause:** Not configured
- **Current State:** No rate limits on API/web
- **Effort:** Low (gitlab.rb setting)

---

## Action Plan

### Phase 1: Immediate Fixes (Effort: ~55min actual work)

#### 1.1 Open Monitoring Access

**Task:** Enable external access to Grafana and Prometheus

```bash
# On 10.0.0.84
ssh agent@10.0.0.84 << 'EOF'
# Open Grafana port
sudo ufw allow 3002/tcp comment 'Grafana web interface'

# Open Prometheus port
sudo ufw allow 9090/tcp comment 'Prometheus API'

# Verify rules applied
sudo ufw status numbered | grep -E "3002|9090"
EOF
```

**Verification:**

```bash
# From local machine
curl -s http://10.0.0.84:3002 | grep -q "Grafana"
curl -s http://10.0.0.84:9090/api/v1/query?query=up | jq '.status'
```

**Effort:** 5min (command execution + verification)

---

#### 1.2 Align NFS Backup with Standard Convention

**Task:** Mount NFS to standard backup path and configure GitLab

**On GitLab host (10.0.0.84):**

```bash
ssh agent@10.0.0.84 << 'EOF'
# Create mount point for standard backup path
sudo mkdir -p /mnt/gitlab-backups

# Mount NFS export to backup directory
sudo mount -t nfs 10.0.0.80:/mnt/data /mnt/data

# Create GitLab backup directory following convention
sudo mkdir -p /mnt/data/Backups/server/gitlab
sudo chown 998:998 /mnt/data/Backups/server/gitlab  # git user UID:GID

# Add to /etc/fstab for persistence
echo "10.0.0.80:/mnt/data /mnt/data nfs defaults 0 0" | sudo tee -a /etc/fstab

# Verify mount
mount | grep nfs
ls -la /mnt/data/Backups/server/gitlab/
EOF
```

**Update GitLab configuration:**

```bash
ssh agent@10.0.0.84 << 'EOF'
# Update docker-compose.yml volume mapping
# Map /mnt/data/Backups/server/gitlab to /var/opt/gitlab/backups in container
# This will be done via docker-compose edit (next step)
EOF
```

**Update infrastructure/gitlab/docker-compose.yml:**

```yaml
volumes:
  - /mnt/data/Backups/server/gitlab:/var/opt/gitlab/backups
```

**Configure backup path in gitlab.rb:**

```ruby
gitlab_rails['backup_path'] = '/var/opt/gitlab/backups'
gitlab_rails['backup_keep_time'] = 604800  # 7 days
```

**Effort:** 20min (mount setup + config + verification)

---

#### 1.3 Update Integration Test Script

**Task:** Fix test script to check actual Grafana/Prometheus URLs

**File:** `scripts/gitlab-integration-test.sh`

**Changes needed:**

```bash
# Current (WRONG):
curl -s http://10.0.0.80:3000 | grep -q "Grafana"
curl -s 'http://10.0.0.80:9090/api/v1/targets' | jq '.data.activeTargets | length'

# Corrected:
curl -s http://10.0.0.84:3002 | grep -q "Grafana"
curl -s 'http://10.0.0.84:9090/api/v1/targets' | jq '.data.activeTargets | length'
```

**Effort:** 5min (URL updates)

---

#### 1.4 Apply SSH Security Hardening

**Task:** Restrict SSH access and enforce key-based auth

```bash
ssh agent@10.0.0.84 << 'EOF'
# Backup current SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Apply restrictions
sudo tee -a /etc/ssh/sshd_config << 'SSHEOF'

# Security hardening (added 2026-01-08)
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
MaxSessions 5
AllowUsers agent deploy
SSHEOF

# Test config before reload
sudo sshd -t

# Reload SSH service
sudo systemctl reload sshd

# Verify
sudo sshd -T | grep -E "PasswordAuthentication|PermitRootLogin|PubkeyAuthentication"
EOF
```

**Effort:** 15min (config + testing + verification)

---

#### 1.5 Enable Rate Limiting

**Task:** Configure GitLab rate limiting to prevent abuse

**Update GITLAB_OMNIBUS_CONFIG in docker-compose.yml:**

```ruby
gitlab_rails['rate_limit_requests_per_period'] = 300
gitlab_rails['rate_limit_period'] = 60  # seconds
gitlab_rails['throttle_unauthenticated_enabled'] = true
gitlab_rails['throttle_unauthenticated_requests_per_period'] = 100
gitlab_rails['throttle_unauthenticated_period_in_seconds'] = 60
gitlab_rails['throttle_authenticated_web_enabled'] = true
gitlab_rails['throttle_authenticated_web_requests_per_period'] = 300
gitlab_rails['throttle_authenticated_web_period_in_seconds'] = 60
```

**Apply changes:**

```bash
ssh agent@10.0.0.84 << 'EOF'
cd /opt/gitlab
docker-compose restart gitlab
docker exec gitlab gitlab-ctl reconfigure
EOF
```

**Verification:**

```bash
docker exec gitlab gitlab-rails console -e production << 'EOF'
puts "Rate limit requests: #{Gitlab::CurrentSettings.rate_limit_requests_per_period}"
puts "Throttle unauth enabled: #{Gitlab::CurrentSettings.throttle_unauthenticated_enabled}"
EOF
```

**Effort:** 10min (config + restart + verification)

---

### Phase 2: Post-Change Verification (Effort: ~20min)

#### 2.1 Monitoring Visibility Check

```bash
# Verify Grafana accessible externally
curl -s http://10.0.0.84:3002 | grep "Grafana" && echo "✅ Grafana accessible"

# Verify Prometheus API responding
curl -s 'http://10.0.0.84:9090/api/v1/query?query=up' | jq '.status' | grep "success" && echo "✅ Prometheus API working"

# Check Prometheus scrape targets
curl -s http://10.0.0.84:9090/api/v1/targets | jq '.data.activeTargets | length'

# Verify Loki receiving GitLab logs
curl -s 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}' | jq '.data.result | length'
```

#### 2.2 Backup Test

```bash
# Create test backup
docker exec gitlab gitlab-backup create BACKUP=test-integration-$(date +%s)

# Verify backup appears in NFS
ssh agent@10.0.0.80 "ls -lh /mnt/data/Backups/server/gitlab/ | tail -5"

# Test restore in staging (if available)
# docker cp /mnt/data/Backups/server/gitlab/test_backup.tar.gz staging-gitlab:/var/opt/gitlab/backups/
# docker exec staging-gitlab gitlab-backup restore BACKUP=test_backup
```

#### 2.3 Security Verification

```bash
# Test SSH restrictions (should fail password auth)
ssh -o PreferredAuthentications=password agent@10.0.0.84 echo "test"  # Should deny

# Test rate limiting
for i in {1..350}; do curl -s http://10.0.0.84:8090/-/health; done | grep -c "429"  # Should see 429 responses after 300 requests
```

#### 2.4 Integration Test Suite

```bash
# Run updated integration test script
cd /opt/wizardsofts-megabuild/scripts
./gitlab-integration-test.sh
```

**Expected results:**

- ✅ PostgreSQL connection
- ✅ GitLab database checks
- ✅ Redis connectivity
- ✅ Keycloak SSO configured
- ✅ Loki service ready
- ✅ GitLab logs in Loki
- ✅ NFS backup directory accessible
- ✅ GitLab backup creation
- ✅ Prometheus scrape targets
- ✅ Grafana accessibility

---

### Phase 3: Optional Enhancements (Future Improvements)

#### 3.1 GitLab Prometheus Exporters

**Goal:** Enable GitLab's built-in Prometheus exporters for better observability

**gitlab.rb configuration:**

```ruby
prometheus['enable'] = true
prometheus['listen_address'] = '0.0.0.0:9090'
prometheus_monitoring['enable'] = true

# Enable exporters
gitlab_exporter['enable'] = true
gitlab_exporter['listen_address'] = '0.0.0.0'
gitlab_exporter['listen_port'] = 9168

node_exporter['enable'] = true
redis_exporter['enable'] = true
postgres_exporter['enable'] = true
```

**Add scrape targets to Prometheus:**

```yaml
# In infrastructure/monitoring/prometheus/prometheus.yml
scrape_configs:
  - job_name: "gitlab"
    static_configs:
      - targets: ["10.0.0.84:9168"] # GitLab exporter
      - targets: ["10.0.0.84:9100"] # Node exporter
```

**Effort:** Medium (requires GitLab reconfigure + Prometheus restart)

---

#### 3.2 Promtail for GitLab Log Shipping

**Goal:** Ship GitLab logs to Loki via Promtail instead of Docker logs

**Deploy Promtail on GitLab host:**

```yaml
# infrastructure/monitoring/promtail/docker-compose.yml
services:
  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - /var/log/gitlab:/var/log/gitlab:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring
```

**Promtail configuration:**

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://10.0.0.80:3100/loki/api/v1/push

scrape_configs:
  - job_name: gitlab
    static_configs:
      - targets:
          - localhost
        labels:
          job: gitlab
          host: 10.0.0.84
          __path__: /var/log/gitlab/**/*.log
```

**Effort:** Medium (Promtail deployment + config + testing)

---

#### 3.3 Grafana Dashboard Imports

**Goal:** Import pre-built GitLab dashboards for instant observability

**Recommended dashboards:**

- GitLab Omnibus (Dashboard ID: 17138)
- GitLab Performance (Dashboard ID: 14731)
- PostgreSQL Database (Dashboard ID: 9628)
- Redis (Dashboard ID: 11835)

**Import via Grafana UI or API:**

```bash
# Via API
curl -X POST http://admin:admin@10.0.0.84:3002/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "uid": null,
      "title": "GitLab Omnibus"
    },
    "inputs": [
      {
        "name": "DS_PROMETHEUS",
        "type": "datasource",
        "pluginId": "prometheus",
        "value": "Prometheus"
      }
    ],
    "overwrite": true,
    "folderId": 0,
    "pluginId": "grafana-simple-json-datasource"
  }'
```

**Effort:** Low (dashboard imports via UI or script)

---

## Success Criteria

### Immediate (Phase 1 + 2)

- [ ] Grafana accessible at http://10.0.0.84:3002
- [ ] Prometheus API responding at http://10.0.0.84:9090
- [ ] GitLab backups stored in `/mnt/data/Backups/server/gitlab/` with date-based subfolders
- [ ] NFS mount persists across reboots (in /etc/fstab)
- [ ] Integration test script passes all checks
- [ ] SSH password auth disabled, key-only access
- [ ] Rate limiting active (429 responses after threshold)
- [ ] Backup/restore tested successfully

### Optional (Phase 3)

- [ ] GitLab Prometheus exporters enabled and scraped
- [ ] Promtail shipping logs to Loki
- [ ] Grafana dashboards imported and displaying data

---

## Future Enhancements (Post-Implementation)

### 4.1 Encrypt Sensitive Backup Files

**Context:** The backup script at `/usr/local/bin/gitlab-backup.sh` already copies `gitlab.rb` and `gitlab-secrets.json` to NFS automatically (the GitLab warning is generic). However, these files contain **sensitive data** (database passwords, secret keys, OAuth tokens) and are stored **unencrypted** on NFS.

**Current State:**

- ✅ Files ARE being backed up automatically via docker cp
- ❌ Files stored in plaintext on `/mnt/data/Backups/server/gitlab/`
- ❌ No encryption at rest on NFS

**Recommended Solution:**

```bash
# In /usr/local/bin/gitlab-backup.sh, after copying files:
# Encrypt sensitive files with GPG
sudo gpg --batch --yes --passphrase-file /root/.backup-passphrase \
    -c "${BACKUP_DIR}/gitlab.rb"
sudo gpg --batch --yes --passphrase-file /root/.backup-passphrase \
    -c "${BACKUP_DIR}/gitlab-secrets.json"

# Remove plaintext versions
sudo rm "${BACKUP_DIR}/gitlab.rb"
sudo rm "${BACKUP_DIR}/gitlab-secrets.json"

# Keep encrypted versions: gitlab.rb.gpg, gitlab-secrets.json.gpg
```

**Restore Process:**

```bash
# Decrypt before restoration
gpg --batch --yes --passphrase-file /root/.backup-passphrase \
    -d backup/gitlab.rb.gpg > gitlab.rb
gpg --batch --yes --passphrase-file /root/.backup-passphrase \
    -d backup/gitlab-secrets.json.gpg > gitlab-secrets.json
```

**Security Considerations:**

- Store passphrase in `/root/.backup-passphrase` (root-only access, chmod 400)
- Or use key-based encryption (gpg --encrypt --recipient backup@wizardsofts.com)
- Consider hardware security module (HSM) for production
- Implement key rotation policy (quarterly)

**Effort:** Low (~30 min)  
**Priority:** Medium (nice-to-have, not critical for initial deployment)  
**Related:** [AGENT.md Section 13.7 - Security Scanning](../../AGENT.md#137-security-scanning)

### 4.2 Adjust Rate Limiting for Production Load

**Context:** Initial deployment uses conservative rate limits (300 requests/60 seconds). After monitoring actual usage patterns, these should be tuned for production load.

**Current Settings:**

```ruby
gitlab_rails['rate_limit_requests_per_period'] = 300
gitlab_rails['rate_limit_period'] = 60
```

**Recommended Production Settings:**

```ruby
gitlab_rails['rate_limit_requests_per_period'] = 180
gitlab_rails['rate_limit_period'] = 30
```

**Rationale:**

- Shorter period (30s) provides more responsive protection
- Lower total (180/30s = 6 req/s) prevents abuse while allowing normal usage
- Aligns with industry standards for API rate limiting
- Monitor first, then adjust based on legitimate traffic patterns

**Implementation:**

```bash
# Update docker-compose.yml GITLAB_OMNIBUS_CONFIG section
# Then: docker-compose down && docker-compose up -d
# Verify: docker exec gitlab gitlab-ctl reconfigure
```

**Effort:** Minimal (~10 min)  
**Priority:** Low (tune after production monitoring)  
**Related:** [Phase 2.4 - Rate Limiting Configuration](#24-configure-rate-limiting)

### 4.3 Reduce Backup Retention Period

**Context:** Initial backup retention is 7 days for safety during deployment. Production should use shorter retention to conserve NFS storage.

**Current Setting:**

```ruby
gitlab_rails['backup_keep_time'] = 604800  # 7 days
```

**Recommended Production Setting:**

```ruby
gitlab_rails['backup_keep_time'] = 259200  # 3 days
```

**Backup Strategy:**

- **Daily backups**: Keep last 3 days on fast NFS storage
- **Weekly backups**: Archive to cold storage (S3/Glacier)
- **Monthly backups**: Archive to cold storage (S3/Glacier Deep Archive)

**Storage Calculation:**

```
Backup size: ~6.4 MB (current, will grow)
Daily (3 days): 3 × 6.4 MB = 19.2 MB
Weekly (4 weeks): 4 × 6.4 MB = 25.6 MB (archived)
Monthly (12 months): 12 × 6.4 MB = 76.8 MB (archived)
Total fast storage: ~20 MB (negligible)
```

**Implementation:**

```bash
# Update docker-compose.yml GITLAB_OMNIBUS_CONFIG section
# Update backup script retention logic
# Then: docker-compose down && docker-compose up -d
```

**Effort:** Minimal (~10 min)  
**Priority:** Low (storage not critical yet, implement when backups grow)  
**Related:** [Phase 2.3 - Backup Configuration](#23-configure-backups-with-nfs)

### 4.4 Global Backup Orchestrator Script

**Context:** Currently each service has its own backup script (`/usr/local/bin/gitlab-backup.sh`). As infrastructure grows, managing multiple service backups becomes complex.

**Problem:**

- Multiple cron jobs to manage
- No centralized backup status/monitoring
- Difficult to coordinate backup windows
- No unified retention policy enforcement
- No backup verification/health checks

**Proposed Solution:**

```bash
/usr/local/bin/backup-orchestrator.sh
```

**Features:**

- Discovers and executes all service backup scripts
- Enforces backup windows (e.g., 2-4 AM)
- Parallel execution with configurable concurrency
- Centralized logging and monitoring
- Health checks and verification
- Unified retention policy management
- Backup status dashboard (via Prometheus metrics)

**Architecture:**

```
/usr/local/bin/
├── backup-orchestrator.sh          # Main orchestrator
├── backup-lib.sh                   # Shared functions
└── backups/
    ├── gitlab-backup.sh            # Service-specific
    ├── postgres-backup.sh          # Service-specific
    ├── redis-backup.sh             # Service-specific
    └── nexus-backup.sh             # Service-specific

/etc/backup-orchestrator/
├── config.yaml                     # Global config
└── services.d/
    ├── gitlab.yaml                 # Per-service config
    ├── postgres.yaml
    └── redis.yaml
```

**Configuration Example:**

```yaml
# /etc/backup-orchestrator/config.yaml
backup_window:
  start: "02:00"
  end: "04:00"
  timezone: "UTC"

retention:
  daily: 3
  weekly: 4
  monthly: 12

storage:
  local: "/mnt/data/Backups/server"
  remote: "s3://wizardsofts-backups"

monitoring:
  prometheus_pushgateway: "http://10.0.0.80:9091"
  alert_webhook: "https://slack.com/webhooks/..."

concurrency: 2 # Max parallel backups
```

**Service Config Example:**

```yaml
# /etc/backup-orchestrator/services.d/gitlab.yaml
name: gitlab
enabled: true
script: /usr/local/bin/backups/gitlab-backup.sh
priority: 1 # Lower number = higher priority
timeout: 3600 # 1 hour max
verify_command: "docker exec gitlab gitlab-rake gitlab:check"
metrics:
  - backup_size_bytes
  - backup_duration_seconds
  - backup_file_count
```

**Orchestrator Features:**

```bash
# List all configured backups
backup-orchestrator list

# Run all backups
backup-orchestrator run --all

# Run specific service backup
backup-orchestrator run --service gitlab

# Verify all backups
backup-orchestrator verify --all

# Check backup status
backup-orchestrator status

# Generate backup report
backup-orchestrator report --last 7d
```

**Monitoring Integration:**

```bash
# Prometheus metrics exposed
backup_last_success_timestamp{service="gitlab"} 1767843778
backup_last_duration_seconds{service="gitlab"} 180
backup_last_size_bytes{service="gitlab"} 6710886
backup_failures_total{service="gitlab"} 0
```

**Alerting:**

```yaml
# Alert if backup fails
groups:
  - name: backups
    rules:
      - alert: BackupFailed
        expr: time() - backup_last_success_timestamp > 86400
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Backup failed for {{ $labels.service }}"
```

**Effort:** Medium (~2-3 hours)  
**Priority:** Medium (implement when managing 5+ services)  
**Dependencies:** Prometheus/Grafana for monitoring  
**Related:** [AGENT.md Section 5.2 - Script-First Policy](../../AGENT.md#52-script-first-policy)

---

## Documentation Updates Needed

After implementation, update:

1. **infrastructure/gitlab/GITLAB_INTEGRATION_BLOCKERS.md**

   - Correct severity levels based on ground truth
   - Update root causes (firewall vs service down)
   - Revise effort estimates (remove time, use effort-only)

2. **scripts/gitlab-integration-test.sh**

   - Update Grafana URL: 10.0.0.84:3002
   - Update Prometheus URL: 10.0.0.84:9090

3. **infrastructure/gitlab/README.md**

   - Document NFS backup path: `/mnt/data/Backups/server/gitlab/`
   - Add SSH hardening details
   - Add rate limiting configuration

4. **docs/operations/troubleshooting/gitlab.md**
   - Add firewall troubleshooting section
   - Document monitoring access procedure
   - Add backup/restore guide using standard paths

---

## Lessons Learned

1. **Ground truth verification is critical** - Services were UP but firewall blocked access
2. **Documentation lags reality** - Always verify actual state before planning
3. **Test assumptions** - Test script was checking wrong hosts
4. **Standardize paths** - Non-standard backup path caused confusion
5. **Effort vs time** - Original 5+ hour estimate reduced to 55min actual work

---

_Plan follows AGENT.md v1.6.1 conventions: ground truth verification, effort-only estimates, standardized backup paths, comprehensive blocker coverage._

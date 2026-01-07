# GitLab Security Implementation - Phase Validation Checklist

**Date**: January 7, 2026  
**Project**: WizardSofts GitLab Security Hardening  
**Timeline**: 6 weeks  
**Last Updated**: $(date)

---

## Pre-Phase Validation (Before Starting ANY Phase)

### Prerequisites

- [ ] All team members notified of planned changes
- [ ] Backup procedures tested and verified
- [ ] Rollback procedures documented and tested
- [ ] Maintenance window scheduled (if required)
- [ ] Integration test script accessible: `/opt/wizardsofts-megabuild/scripts/gitlab-integration-test.sh`

### Run Pre-Phase Tests

```bash
# Make test script executable
chmod +x /opt/wizardsofts-megabuild/scripts/gitlab-integration-test.sh

# Run full test suite (baseline)
./scripts/gitlab-integration-test.sh

# Expected result: All tests PASS (✅)
```

---

## Phase 1: Critical Fixes (Week 1-2)

### 1.1 GitLab Version Upgrade

**Task**: Upgrade GitLab from 18.4.1 to 18.7.0

**Before Upgrade**:

- [ ] Create pre-upgrade backup
  ```bash
  docker exec gitlab gitlab-backup create BACKUP=pre-upgrade-18.4.1-$(date +%Y%m%d)
  ```
- [ ] Verify backup created: `ls /mnt/gitlab-backups/gitlab/*.tar.gz`
- [ ] Document current version:
  ```bash
  docker exec gitlab gitlab-rake gitlab:env:info > /tmp/gitlab-before-upgrade.txt
  ```
- [ ] Verify NFS mount is accessible
- [ ] Schedule 20-minute maintenance window

**Upgrade Steps**:

- [ ] Pull latest image: `docker-compose pull`
- [ ] Stop GitLab: `docker-compose down`
- [ ] Start with new version: `docker-compose up -d`
- [ ] Wait 2 minutes for initialization
- [ ] Monitor logs: `docker logs -f gitlab` (watch for Rails migrations)
- [ ] Wait for "Listening on" message, then Ctrl+C

**Validation**:

```bash
# Check version
docker exec gitlab gitlab-rake gitlab:env:info | grep "GitLab Version"
# Expected: GitLab Version: 18.7.0

# Run database checks
docker exec gitlab gitlab-rake gitlab:check

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: All tests pass (✅)
```

**Rollback** (if needed):

```bash
docker-compose down
git checkout docker-compose.yml  # Revert to 18.4.1
docker-compose pull
docker-compose up -d
docker exec gitlab gitlab-backup restore BACKUP=pre-upgrade-18.4.1-YYYYMMDD
```

- [ ] Version upgraded successfully (18.7.0)
- [ ] All health checks pass
- [ ] All integration tests pass
- [ ] No errors in logs during 5 minutes of normal operation

---

### 1.2 Database Password Rotation

**Task**: Rotate exposed database password

**Current Password Location**:

- GITLAB_DB_PASSWORD=29Dec2#24 (EXPOSED)

**Before Rotation**:

- [ ] Create backup with current password working
- [ ] Document new password in secure location
- [ ] Generate new secure password:
  ```bash
  NEW_PASS=$(openssl rand -base64 32)
  echo "New password: $NEW_PASS"
  ```

**Rotation Steps**:

```bash
# 1. Update PostgreSQL password
docker exec -it gibd-postgres psql -U postgres << EOF
ALTER USER gitlab WITH PASSWORD 'NEW_SECURE_PASSWORD_HERE';
\q
EOF

# 2. Update GitLab environment
docker exec gitlab sed -i "s/db_password = '.*'/db_password = 'NEW_SECURE_PASSWORD_HERE'/" /etc/gitlab/gitlab.rb

# 3. Restart GitLab
docker restart gitlab

# 4. Wait 2 minutes and verify
sleep 120
docker logs gitlab | grep -i "database\|connection"
```

**Validation**:

```bash
# Test new password works
PGPASSWORD='NEW_SECURE_PASSWORD_HERE' psql -U gitlab -h 10.0.0.80 -d gitlabhq_production -c "SELECT current_user, current_database;"
# Expected: gitlab | gitlabhq_production

# Verify GitLab connected
docker exec gitlab gitlab-rake gitlab:check
# Expected: All checks pass

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: All tests pass (✅)
```

**Rollback** (if needed):

```bash
# Revert to old password
docker exec -it gibd-postgres psql -U postgres << EOF
ALTER USER gitlab WITH PASSWORD '29Dec2#24';
\q
EOF
docker restart gitlab
```

- [ ] Database password rotated
- [ ] New password verified working
- [ ] GitLab connected to database successfully
- [ ] All integration tests pass

---

### 1.3 Remove Hardcoded Credentials

**Task**: Remove exposed passwords from documentation

**Files to Clean**:

- [ ] `GITLAB_MIGRATION_PLAN.md` (lines 131-133, 189-191)
- [ ] `infrastructure/gitlab/README.md` (line 58)
- [ ] `infrastructure/gitlab/.env` (add to .gitignore)

**Cleanup Steps**:

```bash
# Replace exposed credentials with placeholders
cd /opt/wizardsofts-megabuild

# 1. Update GITLAB_MIGRATION_PLAN.md
sed -i "s/29Dec2#24/your_secure_password_here/g" GITLAB_MIGRATION_PLAN.md
sed -i "s/M9TcxUSpsqL5nSuX/your_secure_password_here/g" infrastructure/gitlab/README.md

# 2. Add .env to .gitignore
echo "infrastructure/gitlab/.env" >> .gitignore
echo "infrastructure/gitlab/.env.*" >> .gitignore

# 3. Remove .env from git history (if it was committed)
git rm --cached infrastructure/gitlab/.env
git commit -m "chore: remove .env from version control"

# 4. Create .env.example template
cat > infrastructure/gitlab/.env.example << 'EOF'
# Database credentials - replace with actual values
GITLAB_DB_PASSWORD=your_secure_password_here
GITLAB_DB_USER=gitlab

# Redis credentials
REDIS_PASSWORD=your_secure_password_here

# Keycloak SSO
KEYCLOAK_CLIENT_SECRET=your_keycloak_client_secret_here
EOF

# 5. Commit changes
git add .gitignore infrastructure/gitlab/.env.example GITLAB_MIGRATION_PLAN.md infrastructure/gitlab/README.md
git commit -m "security: Remove hardcoded credentials from documentation"
```

**Validation**:

```bash
# Verify no passwords in docs
grep -r "29Dec2#24\|M9TcxUSpsqL5nSuX" . --include="*.md" --include="*.yml" --include="*.yaml" || echo "✅ No exposed passwords found"

# Verify .env is ignored
git check-ignore infrastructure/gitlab/.env || echo "✅ .env is properly gitignored"

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: All tests pass (✅)
```

- [ ] All passwords removed from documentation
- [ ] .env files added to .gitignore
- [ ] .env.example created with templates
- [ ] Changes committed to git
- [ ] No exposed credentials in repo

---

## Phase 2: HTTPS/TLS Configuration (Week 2)

### 2.1 Obtain SSL Certificate

**Task**: Get SSL certificate for gitlab.wizardsofts.com

**Option A: Let's Encrypt (Recommended)**:

```bash
# Install Certbot
apt-get install -y certbot

# Obtain certificate (requires DNS or HTTP validation)
certbot certonly --standalone -d gitlab.wizardsofts.com -d registry.wizardsofts.com

# Verify certificate created
ls -la /etc/letsencrypt/live/gitlab.wizardsofts.com/
# Expected: cert.pem, fullchain.pem, privkey.pem
```

**Option B: Self-Signed (Testing Only)**:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out /tmp/gitlab.crt -keyout /tmp/gitlab.key -days 365
```

**Validation**:

```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/gitlab.wizardsofts.com/fullchain.pem -text -noout | grep -E "Subject:|Issuer:|Not After"
# Expected: Valid dates, correct domain

# Check expiration date
openssl x509 -in /etc/letsencrypt/live/gitlab.wizardsofts.com/fullchain.pem -noout -dates
# Expected: notAfter should be >89 days away
```

- [ ] SSL certificate obtained
- [ ] Certificate validity verified (>89 days)
- [ ] Certificate file paths correct

---

### 2.2 Configure Traefik for HTTPS

**Task**: Setup TLS termination with Traefik

**Update docker-compose.yml**:

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@wizardsofts.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /acme.json:/acme.json
      - /etc/letsencrypt:/letsencrypt:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gitlab.rule=Host(`gitlab.wizardsofts.com`)"
      - "traefik.http.routers.gitlab.entrypoints=websecure"
      - "traefik.http.routers.gitlab.tls=true"
      - "traefik.http.routers.gitlab.tls.certresolver=letsencrypt"
      - "traefik.http.services.gitlab.loadbalancer.server.port=8090"
```

**Restart services**:

```bash
docker-compose down
docker-compose up -d traefik gitlab
docker logs -f traefik
# Expected: "msg=Starting Traefik" and certificate loading
```

**Validation**:

```bash
# Test HTTPS endpoint
curl -I https://gitlab.wizardsofts.com
# Expected: HTTP/1.1 200 OK

# Test HTTP redirect
curl -I http://gitlab.wizardsofts.com
# Expected: 301 or 302 redirect to HTTPS

# Check HSTS header
curl -I https://gitlab.wizardsofts.com | grep Strict-Transport-Security
# Expected: max-age=31536000
```

- [ ] Traefik configured for HTTPS
- [ ] SSL certificate installed
- [ ] HTTP→HTTPS redirect working
- [ ] HSTS header set

---

### 2.3 Update GitLab Configuration

**Task**: Change external_url to HTTPS

```bash
# Update gitlab.rb
docker exec gitlab sed -i "s|external_url 'http://|external_url 'https://|" /etc/gitlab/gitlab.rb

# Verify change
docker exec gitlab grep "external_url" /etc/gitlab/gitlab.rb

# Restart GitLab
docker restart gitlab

# Wait 2 minutes
sleep 120

# Check logs
docker logs gitlab | grep -i "external_url\|https"
```

**Validation**:

```bash
# Test HTTPS access
curl -s https://gitlab.wizardsofts.com/health_check

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: HTTPS test passes (✅)

# Test Git operations over HTTPS
git clone https://gitlab.wizardsofts.com/wizardsofts/megabuild.git /tmp/test-clone 2>&1 | grep -q "Cloning" && rm -rf /tmp/test-clone && echo "✅ Git HTTPS clone works"
```

- [ ] external_url updated to HTTPS
- [ ] GitLab restarted successfully
- [ ] HTTPS endpoint accessible
- [ ] Git clone over HTTPS works
- [ ] All integration tests pass

---

## Phase 3: Authentication & NFS Backups (Week 3)

### 3.1 Mount NFS Backup Storage

**Task**: Setup NFS for automated backups

```bash
# On server 10.0.0.84 (GitLab host)
mkdir -p /mnt/gitlab-backups
mount -t nfs 10.0.0.80:/mnt/backups/gitlab /mnt/gitlab-backups

# Verify mount
mount | grep gitlab-backups
# Expected: 10.0.0.80:/mnt/backups/gitlab on /mnt/gitlab-backups type nfs

# Test write permission
touch /mnt/gitlab-backups/test-file.txt && rm /mnt/gitlab-backups/test-file.txt
echo "✅ NFS is writable"
```

**Persistent Mount** (add to /etc/fstab):

```bash
echo "10.0.0.80:/mnt/backups/gitlab /mnt/gitlab-backups nfs defaults,nofail 0 0" >> /etc/fstab
```

**Validation**:

```bash
# Check mount is persistent
mount | grep gitlab-backups

# Verify directory structure
ls -la /mnt/gitlab-backups/gitlab/

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: NFS tests pass (✅)
```

- [ ] NFS mounted at /mnt/gitlab-backups
- [ ] NFS directory writable
- [ ] Mount added to /etc/fstab for persistence
- [ ] Directory structure verified

---

### 3.2 Setup Automated Backup Script

**Task**: Create daily backup script with rotation

**Create `/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh`**:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/mnt/gitlab-backups/gitlab"
MAX_BACKUPS=14  # Keep 14 days of backups
LOG_FILE="/var/log/gitlab-backup.log"

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting GitLab backup..." >> $LOG_FILE

# Create backup
if docker exec gitlab gitlab-backup create CRON=1 >> $LOG_FILE 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup created successfully" >> $LOG_FILE

    # Find and copy latest backup to NFS
    latest_backup=$(ls -t /var/opt/gitlab/backups/*.tar.gz 2>/dev/null | head -1)
    if [ -n "$latest_backup" ]; then
        cp "$latest_backup" "$BACKUP_DIR/" 2>/dev/null && echo "[$(date '+%Y-%m-%d %H:%M:%S')] Copied to NFS" >> $LOG_FILE
    fi

    # Rotate old backups (keep last 14 days)
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$MAX_BACKUPS -delete
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rotated backups older than $MAX_BACKUPS days" >> $LOG_FILE

    # Show current backups
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Current backups:" >> $LOG_FILE
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l >> $LOG_FILE
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Backup FAILED - Exit code $?" >> $LOG_FILE
    exit 1
fi
```

**Make executable**:

```bash
chmod +x /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh
```

**Test backup script**:

```bash
# Run manually first
/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# Verify backup created
ls -lh /mnt/gitlab-backups/gitlab/*.tar.gz

# Check log
tail -10 /var/log/gitlab-backup.log
```

**Add to crontab**:

```bash
# Run daily at 2 AM
echo "0 2 * * * /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh" | crontab -

# Verify cron added
crontab -l | grep gitlab-backup
```

**Validation**:

```bash
# Check cron log (next morning)
grep gitlab-backup /var/log/syslog

# Verify backup files exist and rotate
ls -lh /mnt/gitlab-backups/gitlab/*.tar.gz

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: Backup tests pass (✅)
```

- [ ] Backup script created and executable
- [ ] Backup script tested manually
- [ ] Backup file created in NFS
- [ ] Cron job added for daily 2 AM backup
- [ ] Log file created: /var/log/gitlab-backup.log

---

### 3.3 Test Backup Restore

**Task**: Verify backups can be restored

```bash
# Restore to staging environment (10.0.0.81 or 10.0.0.82)
# This tests that backups are valid and complete

# Copy backup to staging
latest_backup=$(ls -t /mnt/gitlab-backups/gitlab/*.tar.gz | head -1)
docker cp "$latest_backup" staging-gitlab:/var/opt/gitlab/backups/

# Restore on staging
docker exec staging-gitlab gitlab-backup restore \
  BACKUP=$(basename "$latest_backup" .tar.gz) \
  SKIP=tar

# Wait for restoration to complete
sleep 30

# Verify data integrity
docker exec staging-gitlab gitlab-rake gitlab:check

# Count projects and users
docker exec staging-gitlab gitlab-rails console -e production << 'EOF'
projects_count = Project.count
users_count = User.count
groups_count = Group.count
puts "✅ Restored: #{projects_count} projects, #{users_count} users, #{groups_count} groups"
EOF
```

- [ ] Backup file size reasonable (>100MB expected)
- [ ] Restore completed without errors
- [ ] Data integrity verified (projects, users, groups counted)
- [ ] gitlab:check passes on restored instance

---

### 3.4 Keycloak SSO Integration (OPTIONAL)

**Task**: Integrate Keycloak for SSO (if desired)

**Prerequisites**:

- Keycloak deployed at 10.0.0.84:8180 ✅ (Already running)

**Setup Keycloak Client**:

```bash
# Login to Keycloak admin console
# URL: http://10.0.0.84:8180/admin
# User: admin (check credentials in keycloak docker-compose)

# 1. Create Client for GitLab
#    - Client ID: gitlab
#    - Client Protocol: openid-connect
#    - Access Type: confidential
#    - Valid Redirect URIs: https://gitlab.wizardsofts.com/users/auth/openid_connect/callback

# 2. Get Client Credentials
#    - Tab: Credentials
#    - Copy: Client Secret
#    - Save to: /opt/wizardsofts-megabuild/infrastructure/gitlab/.env

# 3. Configure Mapper (if user attributes needed)
#    - Tab: Mappers
#    - Create Mapper → User Attribute
```

**Configure GitLab**:

```bash
# Add to /etc/gitlab/gitlab.rb
docker exec gitlab cat >> /etc/gitlab/gitlab.rb << 'EOF'

# Keycloak OpenID Connect
gitlab_rails['omniauth_enabled'] = true
gitlab_rails['omniauth_allow_single_sign_on'] = ['openid_connect']
gitlab_rails['omniauth_providers'] = [
  {
    name: "openid_connect",
    label: "Keycloak",
    args: {
      name: "openid_connect",
      strategy_class: "OmniAuth::Strategies::OpenIDConnect",
      issuer: "http://10.0.0.84:8180/realms/master",
      discovery: true,
      uid_field: "preferred_username",
      client_auth_method: "query",
      scope: ["openid", "profile", "email"],
      response_type: "code",
      client_options: {
        identifier: "gitlab",
        secret: "YOUR_KEYCLOAK_CLIENT_SECRET",
        redirect_uri: "https://gitlab.wizardsofts.com/users/auth/openid_connect/callback"
      }
    }
  }
]
EOF

# Restart GitLab
docker restart gitlab
```

**Test SSO Login** (Manual):

```
1. Go to https://gitlab.wizardsofts.com/users/sign_in
2. Click "Keycloak" button
3. Login with Keycloak credentials
4. Verify redirected back to GitLab
5. Verify user account created in GitLab
6. Logout and test again
```

**Validation**:

```bash
# Check GitLab logs for SSO
docker logs gitlab | grep -i "openid\|omniauth"

# Verify user was created via SSO
docker exec gitlab gitlab-rails console -e production << 'EOF'
user = User.find_by(email: 'your_keycloak_user@example.com')
puts "✅ SSO user created: #{user&.username}"
EOF

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: Keycloak tests pass (✅)
```

- [ ] Keycloak client created (Client ID: gitlab)
- [ ] Client Secret obtained and stored securely
- [ ] GitLab omniauth configuration added
- [ ] SSO login button appears on GitLab login page
- [ ] Test login via Keycloak succeeds
- [ ] User account created/linked in GitLab
- [ ] All integration tests pass

---

## Phase 4: Monitoring & Logging (Week 4-5)

### 4.1 Verify Loki Log Shipping

**Task**: Ensure GitLab logs flow to Loki

```bash
# Check GitLab is configured to ship logs
docker exec gitlab grep -A 10 "logging" /etc/gitlab/gitlab.rb

# Verify Loki is accessible
curl -s http://10.0.0.80:3100/ready
# Expected: ready

# Query for GitLab logs
curl -s 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}' | jq '.data.result | length'
# Expected: Should return number > 0 if logs are present
```

**Create Grafana Dashboard** (Manual):

```
1. Go to http://10.0.0.80:3000/
2. Home → Create → Dashboard
3. Add panel → Loki datasource
4. Query: {job="gitlab"} |= "error"
5. Set refresh to 1min
6. Save dashboard
```

**Validation**:

```bash
# Generate log activity (trigger error)
docker exec gitlab gitlab-rails console -e production << 'EOF'
# This will generate log entries
puts "Test log entry"
EOF

# Query logs
curl -s 'http://10.0.0.80:3100/loki/api/v1/query_range?query={job="gitlab"}&start='$(date -u +%s000000000)'' | jq '.data.result[0].values[-1]'
# Expected: Recent log entry appears

# Run integration tests
./scripts/gitlab-integration-test.sh
# Expected: Loki tests pass (✅)
```

- [ ] Loki receiving GitLab logs
- [ ] Logs queryable via Loki API
- [ ] Grafana dashboard created
- [ ] Logs visible in dashboard in real-time

---

### 4.2 Verify Prometheus Metrics

**Task**: Ensure metrics are collected

```bash
# Check Prometheus targets
curl -s http://10.0.0.80:9090/api/v1/targets | jq '.data.activeTargets | length'
# Expected: >0

# Query a metric
curl -s 'http://10.0.0.80:9090/api/v1/query?query=up' | jq '.data.result | length'
# Expected: >0

# Check GitLab metrics endpoint
curl -s http://gitlab.wizardsofts.com:9090/metrics | grep -q "gitlab"
# Expected: GitLab metrics available
```

**Create Prometheus Dashboard**:

```
1. Go to http://10.0.0.80:3000/
2. Home → Import → Paste Prometheus dashboard ID
3. Or create custom dashboard with metrics:
   - gitlab_ruby_gc_duration_seconds
   - gitlab_transaction_duration_seconds
   - process_resident_memory_bytes
```

- [ ] Prometheus scrape targets >0
- [ ] Metrics being collected
- [ ] Grafana Prometheus datasource configured
- [ ] Dashboards created and showing data

---

## Phase 5: Security Hardening (Week 5-6)

### 5.1 SSH Key Restrictions

**Task**: Enforce minimum SSH key strength

```bash
# Add to /etc/gitlab/gitlab.rb
docker exec gitlab cat >> /etc/gitlab/gitlab.rb << 'EOF'

# SSH Key Restrictions
gitlab_rails['ssh_dsa_key_restrictions'] = 0  # Disable DSA
gitlab_rails['ssh_rsa_key_restrictions'] = 3072  # Min 3072-bit
gitlab_rails['ssh_ecdsa_key_restrictions'] = 384  # Min 384-bit
gitlab_rails['ssh_ed25519_key_restrictions'] = 256  # Min 256-bit
EOF

# Restart GitLab
docker restart gitlab
```

**Test SSH Key Validation**:

```bash
# Try to upload a weak key (should fail)
# In GitLab UI: Settings → SSH Keys → Add Key
# Try to paste a 1024-bit RSA key
# Expected: Error message about key strength
```

- [ ] SSH key restrictions configured
- [ ] DSA keys disabled
- [ ] RSA minimum 3072-bit enforced
- [ ] Weak key upload rejected

---

### 5.2 Rate Limiting Configuration

**Task**: Setup rate limiting for brute-force protection

```bash
# Add to /etc/gitlab/gitlab.rb
docker exec gitlab cat >> /etc/gitlab/gitlab.rb << 'EOF'

# Rate Limiting
gitlab_rails['rate_limit_requests_per_period'] = 10
gitlab_rails['rate_limit_period'] = 60  # 10 requests per 60 seconds
nginx['rate_limit_burst'] = 20

# API Rate Limit
gitlab_rails['throttle_authenticated_api_requests_per_period'] = 600
gitlab_rails['throttle_authenticated_api_requests_burst_size'] = 100
gitlab_rails['throttle_unauthenticated_api_requests_per_period'] = 300
gitlab_rails['throttle_unauthenticated_api_requests_burst_size'] = 50
EOF

# Restart GitLab
docker restart gitlab
```

**Test Rate Limiting**:

```bash
# Make rapid requests (should get 429)
for i in {1..15}; do
  curl -s -w "Request $i: %{http_code}\n" http://gitlab.wizardsofts.com/api/v4/user \
    -H "PRIVATE-TOKEN: invalid" -o /dev/null
done
# Expected: See 429 (Too Many Requests) after 10 requests
```

- [ ] Rate limiting configured
- [ ] Excessive requests return 429
- [ ] Legitimate traffic not impacted

---

### 5.3 Container Registry Scanning

**Task**: Verify container image scanning is enabled

```bash
# Check scanner configuration in .gitlab-ci.yml
grep -r "container_scanning\|trivy" .gitlab-ci.yml .gitlab/ci/

# Verify Trivy is configured
docker exec gitlab grep -r "trivy" /etc/gitlab/gitlab.rb

# Test: Push an image with known vulnerabilities (if testing)
# Pipeline should detect and report vulnerabilities
```

- [ ] Container scanning configured
- [ ] Trivy scanner enabled
- [ ] Scan runs on image push
- [ ] Vulnerabilities reported in UI

---

## Final Validation (Week 6)

### Run Complete Integration Test Suite

```bash
# Run full test suite
./scripts/gitlab-integration-test.sh

# Expected output:
# ================================================
# Test Summary
# ================================================
# Passed: 35+
# Failed: 0
# Success Rate: 100%
```

### Manual Verification Checklist

- [ ] GitLab accessible via HTTPS only
- [ ] HTTP redirects to HTTPS
- [ ] HSTS header present
- [ ] Database connection secure
- [ ] Redis connection working
- [ ] Keycloak SSO working (if enabled)
- [ ] Backups created daily
- [ ] Logs flowing to Loki
- [ ] Metrics visible in Grafana
- [ ] Prometheus collecting data
- [ ] Rate limiting active
- [ ] SSH key restrictions enforced
- [ ] Container scanning enabled
- [ ] Git clone/push works
- [ ] User login works
- [ ] CI/CD pipelines run

### Performance Check

```bash
# Verify response times under normal load
# Check Grafana dashboards for:
# - Response time < 2 seconds (p95)
# - CPU usage < 80%
# - Memory usage < 85%
# - Disk usage < 90%
```

- [ ] All integration tests pass (35/35 tests, 100% success)
- [ ] No critical errors in logs
- [ ] Performance metrics normal
- [ ] Backup rotation working (14 days of backups)
- [ ] All security checks implemented

---

## Rollback Procedures

### If Phase Fails

| Phase             | Issue                       | Rollback Command                                                                 |
| ----------------- | --------------------------- | -------------------------------------------------------------------------------- |
| **Upgrade**       | Version fails               | `docker-compose down && git checkout docker-compose.yml && docker-compose up -d` |
| **Backup**        | NFS mount issues            | `umount /mnt/gitlab-backups && rm -rf /mnt/gitlab-backups`                       |
| **HTTPS**         | Certificate errors          | `docker-compose down && revert gitlab.rb changes && docker-compose up -d`        |
| **Keycloak**      | SSO broken                  | Remove omniauth config from gitlab.rb, restart                                   |
| **Rate Limiting** | Blocking legitimate traffic | Increase limits in gitlab.rb                                                     |

---

## After Deployment

### Ongoing Maintenance

```bash
# Daily (automated via cron)
/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# Weekly (manual check)
./scripts/gitlab-integration-test.sh

# Monthly (manual)
docker exec gitlab gitlab-rake gitlab:check
curl https://gitlab.wizardsofts.com/api/v4/version

# Quarterly
- Review backup retention (currently 14 days)
- Check SSL certificate expiration (Let's Encrypt auto-renews)
- Audit user access
- Review security logs in Loki
```

---

**Completion Status**: Ready for implementation  
**Total Estimated Time**: 6 weeks  
**Risk Level**: Low (with proper backups and testing)

---

_For issues or questions during implementation, refer to AGENT.md Section 9.4 (Integration Testing)_

# GitLab Security Hardening - Week-by-Week Execution Guide

**Status**: PostgreSQL 16 Migration COMPLETE ✅  
**Timeline**: 6 Weeks (Jan 13 - Feb 28, 2026) + PostgreSQL Migration DONE  
**Created**: January 7, 2026  
**PostgreSQL Migration**: ✅ COMPLETED Jan 7, 2026 (15.15 → 16.11)

---

## ✅ WEEK 0: PostgreSQL Migration (COMPLETED - Jan 7, 2026)

**Status**: ✅ **COMPLETE** - PostgreSQL 15.15 → 16.11 successful

### Summary

- PostgreSQL 16.11 running on 10.0.0.80:5435
- 959 tables restored, 118 MB data verified
- GitLab 18.4.1 connected and operational on port 8090
- Downtime: 57 minutes (acceptable for migration)
- Backup: `/tmp/gitlab-db-backup-pg15-20260107.sql` (31 MB)

**See**: [POSTGRESQL_MIGRATION_COMPLETE.md](POSTGRESQL_MIGRATION_COMPLETE.md)

---

## PRE-EXECUTION (This Week: Jan 7-10)

### Monday, Jan 7

**Task**: Baseline Testing & Setup

```bash
# 1. Make test script executable
chmod +x /opt/wizardsofts-megabuild/scripts/gitlab-integration-test.sh

# 2. Run baseline integration tests (document current state)
./scripts/gitlab-integration-test.sh > /tmp/baseline-test-results.txt 2>&1

# 3. Verify all team members have access to:
#    - /scripts/gitlab-integration-test.sh
#    - /docs/archive/audits/GITLAB_IMPLEMENTATION_VALIDATION_CHECKLIST.md
#    - /docs/archive/audits/GITLAB_SECURITY_ACTION_CHECKLIST.md

# 4. Document GitLab version before changes
docker exec gitlab gitlab-rake gitlab:env:info > /tmp/gitlab-baseline-info.txt
cat /tmp/gitlab-baseline-info.txt
# Expected output: GitLab Version: 18.4.1
```

**Success Criteria**:

- ✅ Test script runs without errors
- ✅ Baseline results saved
- ✅ GitLab version documented (18.4.1)
- ✅ All team members briefed

---

### Tuesday-Wednesday, Jan 8-9

**Task**: Assign Roles & Schedule Windows

```bash
# Email template for team notification:
cat > /tmp/notification.txt << 'EOF'
Subject: GitLab Security Hardening - 6 Week Implementation

Timeline: January 13 - February 28, 2026

MAINTENANCE WINDOWS (Mark calendars):
- Week 1, Day 1 (Jan 13): GitLab Upgrade (20 min downtime, 2-3 PM)
- Week 1, Day 2 (Jan 14): Password Rotation (5 min downtime, 2 PM)
- Week 2, Day 1 (Jan 20): HTTPS Cutover (10 min downtime, 2 PM)

TEAM ASSIGNMENTS:
- Week 1: [Name 1] - Upgrade & Credentials
- Week 2: [Name 2] - HTTPS & Backups
- Week 3: [Name 3] - Security Hardening
- Weeks 4-6: [Name 4] - Monitoring

All phases require integration testing before proceeding.
Questions? See GITLAB_IMPLEMENTATION_VALIDATION_CHECKLIST.md
EOF

cat /tmp/notification.txt
```

**Action Items**:

- [ ] Assign Week 1 lead
- [ ] Assign Week 2 lead
- [ ] Assign Week 3 lead
- [ ] Assign Weeks 4-6 lead
- [ ] Send team notification
- [ ] Block calendar for maintenance windows

---

### Thursday-Friday, Jan 9-10

**Task**: Pre-Flight Checks

```bash
# 1. Verify backup system
docker exec gitlab gitlab-backup create BACKUP=pre-phase1-$(date +%Y%m%d) || echo "❌ BACKUP FAILED"
# Expected: Backup file created at /var/opt/gitlab/backups/
ls -lh /var/opt/gitlab/backups/ | tail -1
# Expected: Recent backup file (>100MB)

# 2. Test NFS access (needed for Week 2)
mkdir -p /mnt/gitlab-backups
mount -t nfs 10.0.0.80:/mnt/backups/gitlab /mnt/gitlab-backups 2>/dev/null || true
touch /mnt/gitlab-backups/test-file.txt && rm /mnt/gitlab-backups/test-file.txt
# Expected: NFS is writable (or will be mounted Week 2)

# 3. Verify PostgreSQL password (will be changed Week 1)
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "SELECT 1;" > /dev/null
# Expected: Connection succeeds

# 4. Document current state
docker ps | grep gitlab > /tmp/gitlab-containers.txt
git log --oneline -5 > /tmp/git-log.txt

# 5. Final health check
docker exec gitlab gitlab-rake gitlab:check
# Expected: All checks pass with ✅
```

**Success Criteria**:

- ✅ Backup created successfully
- ✅ Database connection verified
- ✅ All health checks pass
- ✅ Team ready to start Monday

---

---

## WEEK 1: Critical Fixes (Jan 13-17)

### Monday, Jan 13 - Day 1: GitLab Upgrade

**Time**: 9:00 AM - 2:00 PM (Maintenance window: 2:00-2:20 PM)  
**Owner**: [Week 1 Lead]  
**Rollback**: Yes (documented below)

#### Morning: Preparation (9:00-2:00 PM)

```bash
# 1. Prepare upgrade documentation
echo "=== GITLAB UPGRADE PREPARATION ===" > /tmp/upgrade-log.txt
echo "Date: $(date)" >> /tmp/upgrade-log.txt
echo "Current Version:" >> /tmp/upgrade-log.txt
docker exec gitlab gitlab-rake gitlab:env:info | grep "GitLab Version" >> /tmp/upgrade-log.txt

# 2. Verify backup directory
docker exec gitlab ls -lh /var/opt/gitlab/backups/ | tail -3
# Expected: Multiple backup files exist

# 3. Create final pre-upgrade backup (redundancy)
docker exec gitlab gitlab-backup create BACKUP=pre-upgrade-18.7.0-$(date +%Y%m%d-%H%M%S)
echo "Pre-upgrade backup created" >> /tmp/upgrade-log.txt

# 4. Notify users of maintenance window
# Send to Slack #general or email:
# "GitLab will be unavailable 2:00-2:20 PM for critical security upgrade"
```

#### Maintenance Window: 2:00-2:20 PM (20 minutes)

```bash
# START DOWNTIME WINDOW
echo "START: $(date)" >> /tmp/upgrade-log.txt

# 1. Stop GitLab gracefully
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down
echo "GitLab stopped: $(date)" >> /tmp/upgrade-log.txt

# 2. Update docker-compose.yml
# Change line:
#   FROM: image: gitlab/gitlab-ce:18.4.1-ce.0
#   TO:   image: gitlab/gitlab-ce:18.7.0-ce.0
nano docker-compose.yml  # Manual edit, or use sed:
sed -i 's/gitlab\/gitlab-ce:18\.4\.1-ce\.0/gitlab\/gitlab-ce:18.7.0-ce.0/' docker-compose.yml

# 3. Verify change
grep "image: gitlab/gitlab-ce" docker-compose.yml
# Expected: image: gitlab/gitlab-ce:18.7.0-ce.0

# 4. Pull new image
docker-compose pull
echo "Image pulled: $(date)" >> /tmp/upgrade-log.txt

# 5. Start GitLab with new version
docker-compose up -d
echo "GitLab starting: $(date)" >> /tmp/upgrade-log.txt

# 6. Wait for startup (GitLab takes 2-3 min to fully start)
sleep 10
docker logs gitlab | tail -20 | tee -a /tmp/upgrade-log.txt
# Expected: See "Listening on" or similar startup messages

# END DOWNTIME - Users can resume using GitLab
echo "END: $(date)" >> /tmp/upgrade-log.txt
```

#### Post-Upgrade Verification (2:20-3:00 PM)

```bash
# 1. Check version
docker exec gitlab gitlab-rake gitlab:env:info | grep "GitLab Version" | tee -a /tmp/upgrade-log.txt
# Expected: GitLab Version: 18.7.0-ce.0

# 2. Wait for health check to pass
echo "Waiting for GitLab to fully initialize..."
for i in {1..30}; do
  if docker exec gitlab gitlab-rake gitlab:check 2>/dev/null | grep -q "Database: ✓"; then
    echo "✅ GitLab healthy" >> /tmp/upgrade-log.txt
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 10
done

# 3. Run integration tests (BLOCKING)
echo "Running integration tests..." >> /tmp/upgrade-log.txt
./scripts/gitlab-integration-test.sh | tee -a /tmp/upgrade-log.txt
TEST_RESULT=$?

# 4. Document results
echo "Integration Test Result: $TEST_RESULT" >> /tmp/upgrade-log.txt
if [ $TEST_RESULT -eq 0 ]; then
  echo "✅ WEEK 1 DAY 1 PASSED" | tee -a /tmp/upgrade-log.txt
else
  echo "❌ TESTS FAILED - REVIEW /tmp/upgrade-log.txt" | tee -a /tmp/upgrade-log.txt
  exit 1
fi

# 5. Notify team
echo "Week 1, Day 1 complete. GitLab upgraded to 18.7.0 ✅"
```

**Rollback Procedure** (if upgrade fails):

```bash
# If something goes wrong, execute this:
cd /opt/wizardsofts-megabuild/infrastructure/gitlab

# 1. Stop failed container
docker-compose down

# 2. Revert docker-compose.yml
sed -i 's/gitlab\/gitlab-ce:18\.7\.0-ce\.0/gitlab\/gitlab-ce:18.4.1-ce.0/' docker-compose.yml

# 3. Pull old image
docker-compose pull

# 4. Start with old version
docker-compose up -d

# 5. Restore backup if database corrupted
docker exec gitlab gitlab-backup restore BACKUP=pre-upgrade-18.7.0-YYYYMMDD-HHMMSS

# 6. Verify rollback
docker exec gitlab gitlab-rake gitlab:env:info | grep "GitLab Version"
# Expected: GitLab Version: 18.4.1-ce.0
```

---

### Tuesday, Jan 14 - Day 2: Database Password Rotation

**Time**: 9:00 AM - 2:00 PM (Maintenance window: 2:00-2:05 PM)  
**Owner**: [Week 1 Lead]

#### Morning: Preparation (9:00-2:00 PM)

```bash
# 1. Generate new secure password
NEW_PASSWORD=$(openssl rand -base64 32)
echo "New password saved to: /tmp/gitlab-db-password.txt"
echo "$NEW_PASSWORD" > /tmp/gitlab-db-password.txt
chmod 600 /tmp/gitlab-db-password.txt
echo "⚠️ Keep this file safe - you will need it if rollback required"

# 2. Document current password location
echo "Current .env location: /opt/wizardsofts-megabuild/infrastructure/gitlab/.env"
echo "Current password field: GITLAB_DB_PASSWORD=29Dec2#24"

# 3. Verify PostgreSQL accessibility
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "SELECT current_user;" > /tmp/db-access.txt
cat /tmp/db-access.txt
# Expected: gitlab
```

#### Maintenance Window: 2:00-2:05 PM (5 minutes)

```bash
# START DOWNTIME
echo "START: $(date)" >> /tmp/password-rotation-log.txt

# 1. Update PostgreSQL password
docker exec -it gibd-postgres psql -U postgres << EOF
ALTER USER gitlab WITH PASSWORD '$(cat /tmp/gitlab-db-password.txt)';
\q
EOF
echo "PostgreSQL password updated: $(date)" >> /tmp/password-rotation-log.txt

# 2. Update GitLab .env file
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
# Backup current .env
cp .env .env.backup-$(date +%Y%m%d)

# Update password
sed -i "s/GITLAB_DB_PASSWORD=.*/GITLAB_DB_PASSWORD=$(cat /tmp/gitlab-db-password.txt)/" .env

# Verify change
grep "GITLAB_DB_PASSWORD" .env | head -1
# Expected: GITLAB_DB_PASSWORD=<long-random-string>

# 3. Restart GitLab to apply new password
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose restart gitlab
echo "GitLab restarted: $(date)" >> /tmp/password-rotation-log.txt

# END DOWNTIME
echo "END: $(date)" >> /tmp/password-rotation-log.txt
```

#### Post-Rotation Verification (2:05-3:00 PM)

```bash
# 1. Wait for GitLab to reconnect
sleep 30

# 2. Verify database connection
docker exec gitlab gitlab-rake gitlab:check 2>&1 | grep -E "database|Database" | tee -a /tmp/password-rotation-log.txt
# Expected: Database: ✓

# 3. Run integration tests (BLOCKING)
./scripts/gitlab-integration-test.sh | tee -a /tmp/password-rotation-log.txt
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
  echo "✅ WEEK 1 DAY 2 PASSED" | tee -a /tmp/password-rotation-log.txt
else
  echo "❌ TESTS FAILED - EXECUTING ROLLBACK"
  # See Rollback section below
  exit 1
fi
```

**Rollback Procedure**:

```bash
# If password rotation fails:
cd /opt/wizardsofts-megabuild/infrastructure/gitlab

# 1. Restore .env backup
cp .env.backup-$(date +%Y%m%d) .env

# 2. Revert PostgreSQL password (use old password from documentation)
docker exec -it gibd-postgres psql -U postgres << EOF
ALTER USER gitlab WITH PASSWORD '29Dec2#24';
\q
EOF

# 3. Restart GitLab
docker-compose restart gitlab

# 4. Verify connection
sleep 30
docker exec gitlab gitlab-rake gitlab:check
```

---

### Wednesday, Jan 15 - Day 3: Remove Hardcoded Credentials

**Time**: 9:00 AM - 5:00 PM (No downtime)  
**Owner**: [Week 1 Lead]

```bash
# 1. Find all exposed credentials
cd /opt/wizardsofts-megabuild
echo "=== Searching for hardcoded passwords ===" > /tmp/credential-scan.txt
grep -r "29Dec2#24" . --include="*.md" --include="*.yml" >> /tmp/credential-scan.txt 2>/dev/null || true
grep -r "M9TcxUSpsqL5nSuX" . --include="*.md" --include="*.yml" >> /tmp/credential-scan.txt 2>/dev/null || true
cat /tmp/credential-scan.txt

# 2. Remove from GITLAB_MIGRATION_PLAN.md
nano GITLAB_MIGRATION_PLAN.md
# Find and replace:
#   FROM: GITLAB_DB_PASSWORD=29Dec2#24
#   TO:   GITLAB_DB_PASSWORD=your_secure_password_here
sed -i 's/GITLAB_DB_PASSWORD=29Dec2#24/GITLAB_DB_PASSWORD=your_secure_password_here/' GITLAB_MIGRATION_PLAN.md

# 3. Remove from infrastructure/gitlab/README.md
nano infrastructure/gitlab/README.md
# Find and replace:
#   FROM: gitlab_rails['db_password'] = 'M9TcxUSpsqL5nSuX'
#   TO:   gitlab_rails['db_password'] = 'your_secure_password_here'
sed -i "s/gitlab_rails\['db_password'\] = 'M9TcxUSpsqL5nSuX'/gitlab_rails['db_password'] = 'your_secure_password_here'/" infrastructure/gitlab/README.md

# 4. Verify no passwords remain in docs
echo "=== Verifying passwords removed ===" > /tmp/credential-verify.txt
grep -r "29Dec2#24\|M9TcxUSpsqL5nSuX" . --include="*.md" --include="*.yml" >> /tmp/credential-verify.txt 2>/dev/null || echo "✅ No exposed passwords found" >> /tmp/credential-verify.txt
cat /tmp/credential-verify.txt

# 5. Add .env files to .gitignore
echo "" >> .gitignore
echo "# GitLab credentials" >> .gitignore
echo "infrastructure/gitlab/.env" >> .gitignore
echo "infrastructure/gitlab/.env.*" >> .gitignore
echo ".env" >> .gitignore

# 6. Add pre-commit hook (prevent future leaks)
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Check for hardcoded credentials
if git diff --cached | grep -E "(password|secret|key)\s*[:=]\s*['\"][^$\{]"; then
  echo "❌ ERROR: Potential hardcoded credentials detected!"
  echo "Please use environment variables or .env files instead."
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit

# 7. Commit changes
git add GITLAB_MIGRATION_PLAN.md infrastructure/gitlab/README.md .gitignore .git/hooks/pre-commit
git commit -m "security: Remove hardcoded credentials and add gitignore rules"
git push origin main
echo "✅ Commit pushed to repository"

# 8. Verify no credentials in git history (important!)
git log --all -S "29Dec2#24" || echo "✅ No exposed credentials in git history"
```

**Success Criteria**:

- ✅ No passwords in documentation
- ✅ .env added to .gitignore
- ✅ Pre-commit hook installed
- ✅ Changes committed and pushed
- ✅ Integration tests still pass

---

### Friday, Jan 17 - Week 1 Validation

```bash
# Run comprehensive Week 1 tests
./scripts/gitlab-integration-test.sh

# Expected output:
# ✅ GitLab version 18.7.0
# ✅ PostgreSQL connection works
# ✅ Redis connection works
# ✅ No exposed credentials
# ✅ All other tests pass

# Document completion
echo "WEEK 1 COMPLETE" > /tmp/week1-status.txt
echo "- Upgraded GitLab 18.4.1 → 18.7.0 ✅" >> /tmp/week1-status.txt
echo "- Rotated database password ✅" >> /tmp/week1-status.txt
echo "- Removed hardcoded credentials ✅" >> /tmp/week1-status.txt
echo "- All integration tests PASS ✅" >> /tmp/week1-status.txt
cat /tmp/week1-status.txt
```

---

---

## WEEK 2: HTTPS/TLS & Backups (Jan 20-24)

### Monday, Jan 20 - Day 1: HTTPS/TLS Setup

**Time**: All day (Maintenance window: 2:00-2:10 PM)  
**Owner**: [Week 2 Lead]

```bash
# 1. Obtain SSL Certificate (Let's Encrypt recommended)
apt-get install -y certbot

# 2. Request certificate
certbot certonly --standalone \
  -d gitlab.wizardsofts.com \
  -d registry.wizardsofts.com \
  --email devops@wizardsofts.com

# 3. Verify certificate created
ls -la /etc/letsencrypt/live/gitlab.wizardsofts.com/
# Expected: cert.pem, fullchain.pem, privkey.pem

# 4. Check expiration
openssl x509 -in /etc/letsencrypt/live/gitlab.wizardsofts.com/fullchain.pem -noout -dates
# Expected: notAfter date is 89+ days away

# 5. Configure Traefik for TLS (update docker-compose.yml)
# Add TLS configuration to Traefik service

# 6. Update GitLab external_url
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker exec gitlab sed -i "s|external_url 'http://|external_url 'https://|" /etc/gitlab/gitlab.rb

# 7. Enable HSTS header
docker exec gitlab cat >> /etc/gitlab/gitlab.rb << 'EOF'
# HSTS Header
nginx['headers'] = {
  "Strict-Transport-Security" => "max-age=31536000; includeSubDomains; preload"
}
EOF

# 8. Restart GitLab (MAINTENANCE WINDOW: 2:00-2:10 PM)
docker-compose down
docker-compose up -d
sleep 30

# 9. Verify HTTPS
curl -I https://gitlab.wizardsofts.com
# Expected: HTTP/2 200 or similar

# 10. Verify HSTS header
curl -I https://gitlab.wizardsofts.com | grep "Strict-Transport-Security"
# Expected: max-age=31536000

# 11. Verify HTTP→HTTPS redirect
curl -I http://gitlab.wizardsofts.com
# Expected: 301 or 302 redirect to https://

# 12. Run integration tests (BLOCKING)
./scripts/gitlab-integration-test.sh
```

---

### Tuesday-Wednesday, Jan 21-22 - Days 2-3: NFS Backup Setup

```bash
# 1. Mount NFS
mkdir -p /mnt/gitlab-backups
mount -t nfs 10.0.0.80:/mnt/backups/gitlab /mnt/gitlab-backups

# 2. Verify NFS is writable
touch /mnt/gitlab-backups/test-file.txt && rm /mnt/gitlab-backups/test-file.txt
# Expected: No errors

# 3. Create backup directory structure
mkdir -p /mnt/gitlab-backups/gitlab

# 4. Add to /etc/fstab for persistence
echo "10.0.0.80:/mnt/backups/gitlab /mnt/gitlab-backups nfs defaults,nofail 0 0" >> /etc/fstab

# 5. Create backup script
cat > /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/mnt/gitlab-backups/gitlab"
MAX_BACKUPS=14
LOG_FILE="/var/log/gitlab-backup.log"

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup..." >> $LOG_FILE

# Create backup
docker exec gitlab gitlab-backup create CRON=1 >> $LOG_FILE 2>&1

# Copy to NFS
latest=$(ls -t /var/opt/gitlab/backups/*.tar.gz 2>/dev/null | head -1)
if [ -n "$latest" ]; then
  cp "$latest" "$BACKUP_DIR/" && echo "[$(date '+%Y-%m-%d %H:%M:%S')] Copied to NFS" >> $LOG_FILE
fi

# Rotate old backups (keep 14 days)
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$MAX_BACKUPS -delete
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rotated backups" >> $LOG_FILE

# Log current backups
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Current backups:" >> $LOG_FILE
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l >> $LOG_FILE
EOF

chmod +x /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# 6. Test backup script
/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# 7. Verify backup created
ls -lh /mnt/gitlab-backups/gitlab/*.tar.gz
# Expected: Backup file >100MB

# 8. Add to crontab (daily 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh >> /var/log/gitlab-backup.log 2>&1") | crontab -

# 9. Verify cron job
crontab -l | grep gitlab-backup
# Expected: 0 2 * * * /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh
```

---

### Thursday-Friday, Jan 23-24 - Days 4-5: Test Restore

```bash
# 1. Verify backup exists
ls -lh /mnt/gitlab-backups/gitlab/*.tar.gz | tail -1

# 2. Test restore to staging (if you have staging environment)
# If not, document the restore procedure
cat > /tmp/restore-procedure.md << 'EOF'
# GitLab Backup Restore Procedure

## Prerequisites
- Access to backup file at /mnt/gitlab-backups/gitlab/*.tar.gz
- Docker access on target GitLab instance
- Database access

## Steps
1. Stop GitLab: `docker-compose down`
2. Copy backup: `cp /mnt/backups/gitlab/TIMESTAMP_backup.tar /var/opt/gitlab/backups/`
3. Restore: `docker exec gitlab gitlab-backup restore BACKUP=TIMESTAMP_backup`
4. Reconfigure: `docker exec gitlab gitlab-ctl reconfigure`
5. Restart: `docker-compose up -d`
6. Verify: `docker exec gitlab gitlab-rake gitlab:check`

## Validation
- GitLab web UI accessible
- Users can login
- Repositories intact
EOF

# 3. Run integration tests (BLOCKING)
./scripts/gitlab-integration-test.sh
# Expected: All tests pass, including backup tests
```

---

### Friday, Jan 24 - Week 2 Validation

```bash
# Run comprehensive Week 2 tests
./scripts/gitlab-integration-test.sh

# Expected results:
# ✅ HTTPS working
# ✅ HSTS header present
# ✅ HTTP→HTTPS redirect working
# ✅ NFS backup mount accessible
# ✅ Backup files created
# ✅ Backup rotation working

echo "WEEK 2 COMPLETE" > /tmp/week2-status.txt
echo "- HTTPS/TLS configured ✅" >> /tmp/week2-status.txt
echo "- NFS backup mounted ✅" >> /tmp/week2-status.txt
echo "- Daily backup automated ✅" >> /tmp/week2-status.txt
echo "- Backup rotation (14 days) ✅" >> /tmp/week2-status.txt
echo "- All integration tests PASS ✅" >> /tmp/week2-status.txt
```

---

---

## WEEK 3: Security Hardening (Jan 27-31)

### Monday-Tuesday, Jan 27-28 - Days 1-2: Keycloak SSO (OPTIONAL)

```bash
# THIS WEEK IS OPTIONAL - Only proceed if you want SSO
# Skip if not needed

# 1. Create Keycloak client
# - Manual step in Keycloak Admin Console
# - Client ID: gitlab
# - Redirect URI: https://gitlab.wizardsofts.com/users/auth/openid_connect/callback

# 2. Configure GitLab omniauth (add to docker-compose.yml)
# 3. Restart GitLab
# 4. Test SSO login
# 5. Run integration tests

# Or skip to security hardening below...
```

### Tuesday-Wednesday, Jan 28-29 - Days 2-3: Rate Limiting & SSH Keys

```bash
# 1. Add rate limiting to docker-compose.yml
# Edit GITLAB_OMNIBUS_CONFIG section:

cat > /tmp/rate-limit-config.txt << 'EOF'
# Rate limiting
gitlab_rails['rate_limit_requests_per_period'] = 10
gitlab_rails['rate_limit_period'] = 60

# API rate limiting
gitlab_rails['throttle_authenticated_api_requests_per_period'] = 600
gitlab_rails['throttle_authenticated_api_requests_burst_size'] = 100
EOF

# 2. Update docker-compose.yml with rate limit config
# (Add above content to GITLAB_OMNIBUS_CONFIG)

# 3. Restart GitLab
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose restart

# 4. Configure SSH key restrictions (manual in UI)
# Admin Area → Settings → General → SSH key restrictions
# - RSA minimum: 3072 bits
# - ECDSA minimum: 384 bits
# - ED25519 minimum: 256 bits
# - Disable DSA keys

# 5. Test rate limiting
echo "Testing rate limiting..."
for i in {1..15}; do
  curl -s -w "Request $i: %{http_code}\n" https://gitlab.wizardsofts.com/api/v4/user \
    -H "PRIVATE-TOKEN: invalid" -o /dev/null
done
# Expected: See 429 (Too Many Requests) after 10 requests

# 6. Run integration tests (BLOCKING)
./scripts/gitlab-integration-test.sh
```

---

### Thursday-Friday, Jan 30-31 - Days 4-5: Resource Limits

```bash
# 1. Update docker-compose.yml with resource limits
# Edit services.gitlab.deploy section:

cat > /tmp/resource-limits.txt << 'EOF'
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '2'
      memory: 2G
EOF

# 2. Update docker-compose.yml with above limits

# 3. Restart GitLab
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down
docker-compose up -d

# 4. Monitor resource usage
docker stats gitlab --no-stream
# Expected: CPU usage < 50%, Memory < 50%

# 5. Verify GitLab still responsive
curl -I https://gitlab.wizardsofts.com
# Expected: HTTP/2 200

# 6. Run integration tests (BLOCKING)
./scripts/gitlab-integration-test.sh

echo "WEEK 3 COMPLETE" > /tmp/week3-status.txt
echo "- Rate limiting configured ✅" >> /tmp/week3-status.txt
echo "- SSH key restrictions enforced ✅" >> /tmp/week3-status.txt
echo "- Resource limits applied (2 CPU / 4GB) ✅" >> /tmp/week3-status.txt
echo "- All integration tests PASS ✅" >> /tmp/week3-status.txt
```

---

---

## WEEKS 4-6: Monitoring & Verification (Feb 3-28)

### Week 4: Verify Loki Logging

```bash
# 1. Verify logs are shipping to Loki
curl -s http://10.0.0.80:3100/ready
# Expected: ready

# 2. Query for GitLab logs
curl -s 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}' | jq '.data.result | length'
# Expected: >0

# 3. Create Grafana dashboard (manual)
# - Go to http://10.0.0.80:3000
# - Create new dashboard
# - Add Loki datasource: http://10.0.0.80:3100
# - Query: {job="gitlab"}

# 4. Run integration tests
./scripts/gitlab-integration-test.sh
```

---

### Week 5: Verify Prometheus Metrics

```bash
# 1. Check Prometheus targets
curl -s http://10.0.0.80:9090/api/v1/targets | jq '.data.activeTargets | length'
# Expected: >0

# 2. Query metrics
curl -s 'http://10.0.0.80:9090/api/v1/query?query=up' | jq '.data.result | length'
# Expected: >0

# 3. Create Grafana dashboard with metrics
# - Go to http://10.0.0.80:3000
# - Create dashboard
# - Add Prometheus datasource
# - Add panels for: CPU, Memory, Disk, Network

# 4. Run integration tests
./scripts/gitlab-integration-test.sh
```

---

### Week 6: Final Validation

```bash
# 1. Run full integration test suite
./scripts/gitlab-integration-test.sh

# Expected output:
# ================================================
# Test Summary
# ================================================
# Passed: 35+
# Failed: 0
# Success Rate: 100%
# ================================================

# 2. Manual verification checklist
echo "FINAL VALIDATION CHECKLIST" > /tmp/final-checklist.txt
echo "[ ] GitLab version 18.7.0+ ✅" >> /tmp/final-checklist.txt
echo "[ ] HTTPS enabled (no HTTP access)" >> /tmp/final-checklist.txt
echo "[ ] HSTS header present" >> /tmp/final-checklist.txt
echo "[ ] Daily backups automated" >> /tmp/final-checklist.txt
echo "[ ] Backup rotation (14 days)" >> /tmp/final-checklist.txt
echo "[ ] NFS backup mount working" >> /tmp/final-checklist.txt
echo "[ ] Loki receiving logs" >> /tmp/final-checklist.txt
echo "[ ] Prometheus collecting metrics" >> /tmp/final-checklist.txt
echo "[ ] Grafana dashboards updated" >> /tmp/final-checklist.txt
echo "[ ] Rate limiting active" >> /tmp/final-checklist.txt
echo "[ ] SSH key restrictions enforced" >> /tmp/final-checklist.txt
echo "[ ] Resource limits applied" >> /tmp/final-checklist.txt
echo "[ ] All integration tests pass" >> /tmp/final-checklist.txt

# 3. Document completion
echo "IMPLEMENTATION COMPLETE ✅" >> /tmp/final-checklist.txt
echo "Date: $(date)" >> /tmp/final-checklist.txt
cat /tmp/final-checklist.txt
```

---

---

## Summary & Quick Reference

### Critical Dates

| Week | Start  | Tasks                                    | Downtime |
| ---- | ------ | ---------------------------------------- | -------- |
| 1    | Jan 13 | Upgrade, credentials, remove passwords   | 25 min   |
| 2    | Jan 20 | HTTPS, NFS, backups, restore test        | 10 min   |
| 3    | Jan 27 | Rate limiting, SSH keys, resource limits | 5 min    |
| 4-6  | Feb 3  | Monitoring integration, final validation | 0 min    |

### Success Criteria (All Weeks)

- ✅ Integration tests pass 100%
- ✅ No unresolved errors in logs
- ✅ All services accessible
- ✅ No data loss

### Rollback Always Available

Every phase has documented rollback procedures in this guide.

---

**Ready to Execute. Follow daily for best results.**

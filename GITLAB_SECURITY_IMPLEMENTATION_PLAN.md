# GitLab Security Implementation Plan

**Date**: January 7, 2026  
**Based On**: GITLAB_SECURITY_AUDIT_REPORT.md  
**Status**: ✅ APPROVED FOR IMPLEMENTATION  
**Timeline**: 8 weeks  

---

## Quick Reference: What's Being Fixed

| Issue | Current State | Target State | When |
|-------|---------------|--------------|------|
| GitLab Version | 18.4.1 (outdated) | Latest stable | Week 1 |
| Hardcoded Secrets | In .env and README ❌ | Removed, rotated ✅ | Week 1 |
| 2FA | Not enforced ❌ | All users required ✅ | Week 2 |
| Backups | Manual only ❌ | Automated daily ✅ | Week 2 |
| Keycloak SSO | Not integrated ❌ | Full SSO ✅ | Week 3 |
| Container Limits | None ❌ | 2 CPU / 4GB ✅ | Week 3 |
| Container Scanning | Already configured ✅ | Verify working | Week 4 |

**Note**: HTTPS deferred - GitLab is local network only (10.0.0.0/24), no public exposure planned.

---

## Phase 1: Critical Security Fixes (Week 1-2)

### Week 1: Version Update & Credential Rotation

#### Task 1.1: Upgrade GitLab to 18.7.0

**Why**: 18.4.1 is 3+ months old, missing critical security patches

**Steps**:
```bash
# 1. Create backup FIRST
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker exec gitlab gitlab-backup create BACKUP=pre-upgrade-$(date +%Y%m%d)

# 2. Stop GitLab
docker-compose down

# 3. Update docker-compose.yml
nano docker-compose.yml
# Change: image: gitlab/gitlab-ce:18.4.1-ce.0
# To:     image: gitlab/gitlab-ce:18.7.0-ce.0

# 4. Pull new image
docker-compose pull

# 5. Start GitLab
docker-compose up -d

# 6. Monitor upgrade (takes 10-15 minutes)
docker logs -f gitlab

# 7. Verify version
docker exec gitlab gitlab-rake gitlab:env:info | grep "GitLab information"

# 8. Test login and core functionality
curl -I http://10.0.0.84:8090
```

**Rollback Plan** (if upgrade fails):
```bash
# Revert image version in docker-compose.yml
nano docker-compose.yml
# Change back to: image: gitlab/gitlab-ce:18.4.1-ce.0
docker-compose up -d
# Restore backup if needed
docker exec gitlab gitlab-backup restore BACKUP=pre-upgrade-20260107
```

**Success Criteria**:
- ✅ GitLab version shows 18.7.0
- ✅ Web UI accessible
- ✅ Users can login
- ✅ Pipelines still run

**Time Estimate**: 2 hours (including monitoring)

---

#### Task 1.2: Rotate Database Passwords & Remove from Docs

**Why**: Passwords exposed in multiple files - MUST be removed entirely from documentation

**Current Exposed Passwords**:
- `GITLAB_DB_PASSWORD=29Dec2#24` (in .env - acceptable location)
- `M9TcxUSpsqL5nSuX` (in README.md - **MUST REMOVE**)

**⚠️ CRITICAL**: Passwords should NEVER appear in README or documentation files.

**Steps**:
```bash
# 1. Generate new secure password
NEW_PASSWORD=$(openssl rand -base64 32)
echo "New password: $NEW_PASSWORD" > /tmp/gitlab-new-password.txt
chmod 600 /tmp/gitlab-new-password.txt

# 2. Update PostgreSQL database user password
ssh wizardsofts@10.0.0.80
docker exec -it gibd-postgres psql -U postgres
postgres=# ALTER USER gitlab WITH PASSWORD 'NEW_PASSWORD_HERE';
postgres=# \q
exit

# 3. Update GitLab environment file
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
nano .env
# Update: GITLAB_DB_PASSWORD=NEW_PASSWORD_HERE

# 4. Restart GitLab to apply new password
docker-compose restart

# 5. Verify database connection
docker exec gitlab gitlab-rake gitlab:check

# 6. Clean up exposed passwords from documentation
cd /opt/wizardsofts-megabuild
# Remove or replace with placeholders
nano GITLAB_MIGRATION_PLAN.md
nano infrastructure/gitlab/README.md
```

**Files to Update** (remove ALL hardcoded passwords):
- `infrastructure/gitlab/README.md` (line 58) - **REMOVE entire password line, use placeholder**
- `GITLAB_MIGRATION_PLAN.md` (lines 131-133, 189-191) - **Replace with placeholders**
- Replace with: `GITLAB_DB_PASSWORD=${GITLAB_DB_PASSWORD}` or `your_secure_password_here`
- **Never commit actual passwords to documentation**

**Success Criteria**:
- ✅ Database password changed in PostgreSQL
- ✅ GitLab .env file updated
- ✅ GitLab connects to database successfully
- ✅ No hardcoded passwords in documentation
- ✅ New password stored securely

**Time Estimate**: 1 hour

---

#### Task 1.3: Remove Hardcoded Credentials from All Files

**Why**: Prevents accidental credential leaks if repository is exposed

**Files to Update**:
```bash
cd /opt/wizardsofts-megabuild

# 1. Find all potential hardcoded credentials
git grep -r "password\s*=\s*['\"]" . | grep -v ".git"
git grep -r "GITLAB_DB_PASSWORD=" . | grep -v ".git"

# 2. Update each file found:
# infrastructure/gitlab/README.md
sed -i "s/gitlab_rails\['db_password'\] = 'M9TcxUSpsqL5nSuX'/gitlab_rails['db_password'] = 'your_secure_password_here'/" infrastructure/gitlab/README.md

# GITLAB_MIGRATION_PLAN.md
sed -i 's/GITLAB_DB_PASSWORD=29Dec2#24/GITLAB_DB_PASSWORD=your_secure_password_here/' GITLAB_MIGRATION_PLAN.md

# 3. Add .env to .gitignore (if not already)
echo "infrastructure/gitlab/.env" >> .gitignore

# 4. Commit changes
git add .gitignore infrastructure/gitlab/README.md GITLAB_MIGRATION_PLAN.md
git commit -m "security: Remove hardcoded GitLab database credentials from documentation"
git push origin main
```

**Add Pre-Commit Hook** (prevent future leaks):
```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Check for potential credentials in staged files
if git diff --cached --name-only | xargs grep -E "(password|secret|key)\s*[:=]\s*['\"][^$\{]" 2>/dev/null | grep -vE "(your_|placeholder|example|changeme)" | head -5; then
    echo "ERROR: Potential hardcoded credentials detected!"
    echo "Please use GitLab CI/CD Variables or environment variables instead."
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

**Success Criteria**:
- ✅ No hardcoded passwords in any .md files
- ✅ .env files added to .gitignore
- ✅ Pre-commit hook installed
- ✅ Documentation uses placeholders

**Time Estimate**: 1 hour

---

### Week 2: Authentication & Backup Setup

> **Note**: HTTPS/TLS is **DEFERRED** - GitLab is local network only (10.0.0.0/24).
> UFW firewall restricts access. No public DNS exposure planned.
> Revisit HTTPS if public access is needed in the future.

#### Task 2.1: Enforce Two-Factor Authentication (2FA)

**Steps**:
1. Login to GitLab as admin
2. Navigate to: **Admin Area** → **Settings** → **General**
3. Expand: **Sign-in restrictions**
4. Check: **Require two-factor authentication**
5. Set: **Grace period**: 7 days
6. Click: **Save changes**

**User Communication**:
```markdown
Subject: MANDATORY: Enable 2FA for GitLab Access by [DATE]

All GitLab users must enable Two-Factor Authentication (2FA) within 7 days.

Setup Instructions:
1. Login to GitLab at http://10.0.0.84:8090
2. Click your avatar → Settings
3. Navigate to Account → Two-factor Authentication
4. Scan QR code with Google Authenticator or Authy
5. Enter 6-digit code to confirm
6. Save recovery codes securely

Questions? Contact devops@wizardsofts.com
```

**Success Criteria**:
- ✅ 2FA enforcement enabled
- ✅ All users notified
- ✅ 100% compliance within 7 days

**Time Estimate**: 2 hours (including user support)

---

#### Task 2.2: Setup Automated Backups

**Why**: Current backups are manual only, no disaster recovery capability

**Integration with Existing Backup**:
Your existing backup script is at: `/home/agent/gitlab-backups/backup-gitlab-db.sh`

**Steps**:
```bash
# 1. Create comprehensive backup script
ssh agent@10.0.0.84
cat > /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/mnt/backups/gitlab"
GITLAB_CONTAINER="gitlab"
RETENTION_DAYS=30

# Create backup
echo "[$(date)] Starting GitLab backup..."
docker exec -t $GITLAB_CONTAINER gitlab-backup create CRON=1

# Get backup filename
BACKUP_FILE=$(docker exec $GITLAB_CONTAINER ls -t /var/opt/gitlab/backups/ | head -1)
TIMESTAMP=$(echo $BACKUP_FILE | cut -d'_' -f1)

# Copy backup to backup directory
echo "[$(date)] Copying backup to $BACKUP_DIR..."
mkdir -p $BACKUP_DIR
docker cp $GITLAB_CONTAINER:/var/opt/gitlab/backups/$BACKUP_FILE $BACKUP_DIR/

# Backup configuration files (secrets!)
echo "[$(date)] Backing up configuration files..."
docker cp $GITLAB_CONTAINER:/etc/gitlab/gitlab.rb $BACKUP_DIR/gitlab.rb.$TIMESTAMP
docker cp $GITLAB_CONTAINER:/etc/gitlab/gitlab-secrets.json $BACKUP_DIR/gitlab-secrets.json.$TIMESTAMP

# Cleanup old backups
echo "[$(date)] Cleaning up backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR -name "*.tar" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "gitlab.rb.*" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "gitlab-secrets.json.*" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup complete: $BACKUP_FILE"
EOF

chmod +x /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# 2. Create backup directory
sudo mkdir -p /mnt/backups/gitlab
sudo chown agent:agent /mnt/backups/gitlab

# 3. Test backup script
/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# 4. Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh >> /var/log/gitlab-backup.log 2>&1") | crontab -

# 5. Verify cron job
crontab -l | grep gitlab-backup
```

**Success Criteria**:
- ✅ Backup script runs successfully
- ✅ Backup files created in /mnt/backups/gitlab
- ✅ Cron job configured
- ✅ Configuration files backed up

**Time Estimate**: 2 hours

---

#### Task 2.3: Test Backup Restoration

**Why**: Backups are useless if restoration doesn't work

**Steps** (on staging/test environment):
```bash
# 1. Stop GitLab services
docker exec gitlab gitlab-ctl stop puma
docker exec gitlab gitlab-ctl stop sidekiq

# 2. Restore backup (replace TIMESTAMP with actual)
docker exec gitlab gitlab-backup restore BACKUP=TIMESTAMP_gitlab_backup

# 3. Restore configuration
docker cp /mnt/backups/gitlab/gitlab-secrets.json.TIMESTAMP gitlab:/etc/gitlab/gitlab-secrets.json

# 4. Reconfigure and restart
docker exec gitlab gitlab-ctl reconfigure
docker exec gitlab gitlab-ctl restart

# 5. Verify restoration
docker exec gitlab gitlab-rake gitlab:check SANITIZE=true
```

**Success Criteria**:
- ✅ Backup restores without errors
- ✅ All data accessible after restoration
- ✅ Users can login
- ✅ Repositories intact

**Time Estimate**: 2 hours

---

## Phase 2: High Priority Improvements (Week 3-4)

### Week 3: Keycloak SSO Integration & Resource Limits

#### Task 3.1: Integrate Keycloak SSO (REQUIRED)

**Why**: Centralized authentication with existing Keycloak at 10.0.0.84:8180

**Prerequisites**:
- Keycloak running at http://10.0.0.84:8180
- Admin access to Keycloak
- Admin access to GitLab

**Step 1: Create GitLab Client in Keycloak**:
```bash
# Login to Keycloak Admin Console
# http://10.0.0.84:8180/admin

# 1. Select or create realm (e.g., "wizardsofts")
# 2. Go to Clients → Create Client
# 3. Configure:
#    - Client ID: gitlab
#    - Client Protocol: openid-connect
#    - Root URL: http://10.0.0.84:8090
#    - Valid Redirect URIs: http://10.0.0.84:8090/users/auth/openid_connect/callback
#    - Web Origins: http://10.0.0.84:8090
# 4. Save and note the Client Secret from Credentials tab
```

**Step 2: Configure GitLab for OIDC**:
```bash
ssh agent@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/gitlab

# Update docker-compose.yml environment section
nano docker-compose.yml
```

**Add to GITLAB_OMNIBUS_CONFIG**:
```ruby
# Keycloak OIDC Configuration
gitlab_rails['omniauth_enabled'] = true
gitlab_rails['omniauth_allow_single_sign_on'] = ['openid_connect']
gitlab_rails['omniauth_sync_email_from_provider'] = 'openid_connect'
gitlab_rails['omniauth_sync_profile_from_provider'] = ['openid_connect']
gitlab_rails['omniauth_sync_profile_attributes'] = ['name', 'email']
gitlab_rails['omniauth_auto_link_user'] = ['openid_connect']
gitlab_rails['omniauth_block_auto_created_users'] = false
gitlab_rails['omniauth_providers'] = [
  {
    name: "openid_connect",
    label: "Keycloak",
    args: {
      name: "openid_connect",
      scope: ["openid", "profile", "email"],
      response_type: "code",
      issuer: "http://10.0.0.84:8180/realms/wizardsofts",
      discovery: true,
      client_auth_method: "query",
      uid_field: "preferred_username",
      pkce: true,
      client_options: {
        identifier: "gitlab",
        secret: "${KEYCLOAK_CLIENT_SECRET}",
        redirect_uri: "http://10.0.0.84:8090/users/auth/openid_connect/callback"
      }
    }
  }
]
```

**Step 3: Add Keycloak Secret to .env**:
```bash
echo "KEYCLOAK_CLIENT_SECRET=your_keycloak_client_secret_here" >> .env
```

**Step 4: Restart GitLab**:
```bash
docker-compose down
docker-compose up -d
docker logs -f gitlab | grep -i "omniauth\|keycloak"
```

**Step 5: Test SSO Login**:
1. Go to http://10.0.0.84:8090
2. Click "Keycloak" button on login page
3. Authenticate with Keycloak credentials
4. Verify user is created/linked in GitLab

**Success Criteria**:
- ✅ Keycloak button appears on GitLab login page
- ✅ SSO authentication works
- ✅ User accounts auto-linked
- ✅ Profile synced from Keycloak

**Time Estimate**: 4 hours

---

#### Task 3.2: Configure Resource Limits

**Why**: Prevent GitLab from consuming all host resources

**Update docker-compose.yml**:
```yaml
services:
  gitlab:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

**Apply and verify**:
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down
docker-compose up -d

# Verify limits applied
docker stats gitlab --no-stream
```

**Success Criteria**:
- ✅ Container limited to 2 CPU cores
- ✅ Container limited to 4GB RAM
- ✅ GitLab functions normally within limits

**Time Estimate**: 30 minutes

---

#### Task 3.3: Configure Rate Limiting

**Why**: Prevent brute force attacks, DDoS, credential stuffing

**Steps**:
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab

# Add to docker-compose.yml environment section
nano docker-compose.yml
```

**Add Rate Limiting Config**:
```yaml
environment:
  GITLAB_OMNIBUS_CONFIG: |
    # ... existing config ...
    
    # Rate limiting
    gitlab_rails['rate_limit_requests_per_period'] = 10
    gitlab_rails['rate_limit_period'] = 60
    
    # Rack Attack (bruteforce protection)
    gitlab_rails['rack_attack_git_basic_auth'] = {
      'enabled' => true,
      'ip_whitelist' => ["10.0.0.0/24"],
      'maxretry' => 10,
      'findtime' => 60,
      'bantime' => 3600
    }
    
    # Nginx rate limiting
    nginx['rate_limit_burst'] = 20
```

**Restart GitLab**:
```bash
docker-compose restart
```

**Success Criteria**:
- ✅ Rate limits applied
- ✅ Test with excessive requests (should get 429 Too Many Requests)

**Time Estimate**: 1 hour

---

#### Task 3.3: Configure SSH Key Restrictions

**Steps**:
1. Login as admin
2. Navigate to: **Admin Area** → **Settings** → **General**
3. Expand: **SSH key restrictions**
4. Configure:
   - Minimum RSA key length: **3072 bits**
   - Minimum ECDSA key length: **384 bits**
   - Minimum ED25519 key length: **256 bits**
   - ✅ Disallow DSA keys
   - ✅ Disallow RSA keys shorter than minimum
5. Click: **Save changes**

**Success Criteria**:
- ✅ Weak SSH keys rejected on upload
- ✅ Existing weak keys flagged for rotation

**Time Estimate**: 30 minutes

---

### Week 4: Backup & Disaster Recovery

#### Task 4.1: Setup Automated Backups

**Why**: Current backups are manual only, no disaster recovery capability

**Steps**:
```bash
# 1. Create backup script
cat > /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/mnt/backups/gitlab"
GITLAB_CONTAINER="gitlab"
RETENTION_DAYS=30
S3_BUCKET="s3://wizardsofts-backups/gitlab"  # Optional: remote backup

# Create backup
echo "[$(date)] Starting GitLab backup..."
docker exec -t $GITLAB_CONTAINER gitlab-backup create CRON=1

# Get backup filename
BACKUP_FILE=$(docker exec $GITLAB_CONTAINER ls -t /var/opt/gitlab/backups/ | head -1)
TIMESTAMP=$(echo $BACKUP_FILE | cut -d'_' -f1)

# Copy backup to backup directory
echo "[$(date)] Copying backup to $BACKUP_DIR..."
mkdir -p $BACKUP_DIR
docker cp $GITLAB_CONTAINER:/var/opt/gitlab/backups/$BACKUP_FILE $BACKUP_DIR/

# Backup configuration files (secrets!)
echo "[$(date)] Backing up configuration files..."
docker cp $GITLAB_CONTAINER:/etc/gitlab/gitlab.rb $BACKUP_DIR/gitlab.rb.$TIMESTAMP
docker cp $GITLAB_CONTAINER:/etc/gitlab/gitlab-secrets.json $BACKUP_DIR/gitlab-secrets.json.$TIMESTAMP

# Optional: Upload to S3
if command -v aws &> /dev/null; then
    echo "[$(date)] Uploading to S3..."
    aws s3 sync $BACKUP_DIR/ $S3_BUCKET/ --exclude "*" --include "*$TIMESTAMP*"
fi

# Cleanup old backups
echo "[$(date)] Cleaning up backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR -name "*.tar" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "gitlab.rb.*" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "gitlab-secrets.json.*" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup complete: $BACKUP_FILE"
EOF

chmod +x /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# 2. Create backup directory
sudo mkdir -p /mnt/backups/gitlab
sudo chown wizardsofts:wizardsofts /mnt/backups/gitlab

# 3. Test backup script
/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh

# 4. Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh >> /var/log/gitlab-backup.log 2>&1") | crontab -

# 5. Verify cron job
crontab -l | grep gitlab-backup
```

**Success Criteria**:
- ✅ Backup script runs successfully
- ✅ Backup files created in /mnt/backups/gitlab
- ✅ Cron job configured
- ✅ Configuration files backed up

**Time Estimate**: 3 hours

---

#### Task 4.2: Test Backup Restoration

**Why**: Backups are useless if restoration doesn't work

**Steps** (on staging/test environment):
```bash
# 1. Stop GitLab services
docker exec gitlab gitlab-ctl stop unicorn
docker exec gitlab gitlab-ctl stop puma
docker exec gitlab gitlab-ctl stop sidekiq

# 2. Restore backup (replace TIMESTAMP with actual)
docker exec gitlab gitlab-backup restore BACKUP=TIMESTAMP_gitlab_backup

# 3. Restore configuration
docker cp /mnt/backups/gitlab/gitlab-secrets.json.TIMESTAMP gitlab:/etc/gitlab/gitlab-secrets.json

# 4. Reconfigure and restart
docker exec gitlab gitlab-ctl reconfigure
docker exec gitlab gitlab-ctl restart

# 5. Verify restoration
docker exec gitlab gitlab-rake gitlab:check SANITIZE=true
```

**Success Criteria**:
- ✅ Backup restores without errors
- ✅ All data accessible after restoration
- ✅ Users can login
- ✅ Repositories intact

**Time Estimate**: 2 hours

---

## Phase 3: Medium Priority Enhancements (Week 4-6)

### Week 4: Verify Existing Security & Performance Tuning

#### Task 4.1: Verify Container Registry Vulnerability Scanning

**Status**: Container scanning already configured in `.gitlab/ci/security.gitlab-ci.yml`

**Verification Steps**:
```bash
# Check existing security pipeline configuration
cat /opt/wizardsofts-megabuild/.gitlab/ci/security.gitlab-ci.yml | grep -A20 "trivy\|container"

# Verify pipeline runs
# Go to GitLab → CI/CD → Pipelines → Check for security stage

# Manual scan test
docker run --rm aquasec/trivy image \
  --severity HIGH,CRITICAL \
  10.0.0.84:5050/wizardsofts/app:latest
```

**Success Criteria**:
- ✅ Trivy scans running in pipelines
- ✅ High/Critical vulnerabilities reported
- ✅ No configuration changes needed (already done)

**Time Estimate**: 1 hour (verification only)

---

#### Task 4.2: Tune Puma and Sidekiq Workers

**Add to GITLAB_OMNIBUS_CONFIG**:
```yaml
# Performance tuning
puma['worker_processes'] = 4
puma['max_threads'] = 8
puma['worker_timeout'] = 60

sidekiq['concurrency'] = 25

# Database connection pooling
gitlab_rails['db_pool'] = 10
gitlab_rails['db_prepared_statements'] = true
```

**Time Estimate**: 4 hours

---

### Week 8: Integration & Final Steps

#### Task 8.1: Integrate with Grafana Loki (Logging)

**Steps**:
```bash
# Configure GitLab to send logs to Loki
# Add to docker-compose.yml
logging:
  driver: loki
  options:
    loki-url: "http://loki:3100/loki/api/v1/push"
    loki-external-labels: "service=gitlab,environment=production"
```

#### Task 8.2: Setup Keycloak SSO Integration

**Time Estimate**: 6 hours

---

## Progress Tracking

### Weekly Checkpoints (Updated Timeline)

| Week | Focus | Key Deliverables | Status |
|------|-------|------------------|--------|
| 1 | Critical Fixes | Version upgrade, credential rotation, remove passwords from docs | 🔲 Not Started |
| 2 | Auth & Backups | 2FA enforcement, automated backups, DR testing | 🔲 Not Started |
| 3 | SSO & Limits | Keycloak SSO integration, resource limits (2 CPU/4GB), rate limiting | 🔲 Not Started |
| 4 | Security & Perf | Verify container scanning, Puma/Sidekiq tuning | 🔲 Not Started |
| 5-6 | Monitoring | Grafana Loki integration, SSH key restrictions | 🔲 Not Started |

**Changes from Original Plan**:
- ❌ HTTPS/TLS: Deferred (local network only, no public exposure)
- ⬆️ Keycloak SSO: Moved from Week 8 to Week 3 (required)
- ✅ Container Scanning: Already configured, verify only
- 📉 Resource Limits: Reduced from 4 CPU/8GB to 2 CPU/4GB

---

## Post-Implementation Validation

After completing all phases, run this validation script:

```bash
#!/bin/bash
# gitlab-security-validation.sh

echo "=== GitLab Security Validation ==="

# Check version
echo "1. GitLab Version:"
docker exec gitlab gitlab-rake gitlab:env:info | grep "GitLab information"

# Check HTTPS
echo "2. HTTPS Enabled:"
curl -I https://gitlab.wizardsofts.com 2>/dev/null | grep "HTTP/2 200" && echo "✅ HTTPS working"

# Check 2FA enforcement
echo "3. 2FA Enforcement:"
docker exec gitlab gitlab-rails runner "puts ApplicationSetting.current.require_two_factor_authentication" | grep "true" && echo "✅ 2FA enforced"

# Check backups
echo "4. Automated Backups:"
crontab -l | grep gitlab-backup && echo "✅ Backup cron configured"

# Check last backup
ls -lht /mnt/backups/gitlab/*.tar | head -1

echo "=== Validation Complete ==="
```

---

## Support & Escalation

**Issues During Implementation**:
- Technical Lead: devops@wizardsofts.com
- Emergency: +880-XXX-XXXXX

**Rollback Decision Matrix**:
| Scenario | Rollback? | Action |
|----------|-----------|--------|
| GitLab won't start after upgrade | YES | Revert to 18.4.1, restore backup |
| Database connection fails | YES | Restore previous credentials |
| SSL certificate errors | NO | Fix certificates, don't rollback |
| Minor UI glitches | NO | Log issue, fix in next sprint |

---

**Status**: ✅ READY FOR IMPLEMENTATION  
**Approval Required**: DevOps Lead, Security Team  
**Start Date**: [TO BE SCHEDULED]

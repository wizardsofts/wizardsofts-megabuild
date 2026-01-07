# GitLab Security Audit - Quick Action Checklist

**Date**: January 7, 2026  
**Purpose**: Quick reference for implementation

---

## 🔴 IMMEDIATE ACTIONS (Do First)

### [ ] 1. Review Audit Report

- **File**: `GITLAB_SECURITY_AUDIT_REPORT.md`
- **Time**: 30 minutes
- **Focus**: Section 2 (Security Vulnerabilities)

### [ ] 2. Backup Current GitLab

```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker exec gitlab gitlab-backup create BACKUP=pre-security-audit-$(date +%Y%m%d)
```

- **Time**: 10 minutes
- **Location**: `/var/opt/gitlab/backups/` (inside container)

### [ ] 3. Rotate Database Password

```bash
# Generate new password
NEW_PASS=$(openssl rand -base64 32)
echo $NEW_PASS > /tmp/gitlab-new-password.txt
chmod 600 /tmp/gitlab-new-password.txt

# Update PostgreSQL
ssh wizardsofts@10.0.0.80
docker exec -it gibd-postgres psql -U postgres
# ALTER USER gitlab WITH PASSWORD 'NEW_PASSWORD';
```

- **Time**: 15 minutes
- **Impact**: 5-minute GitLab restart required

### [ ] 4. Remove Hardcoded Credentials

**Files to clean**:

- [ ] `infrastructure/gitlab/README.md` (line 58)
- [ ] `GITLAB_MIGRATION_PLAN.md` (lines 131-133, 189-191)
- [ ] `infrastructure/gitlab/.env` (add to .gitignore)

```bash
cd /opt/wizardsofts-megabuild
# Replace passwords with placeholders
sed -i "s/29Dec2#24/your_secure_password_here/" GITLAB_MIGRATION_PLAN.md
sed -i "s/M9TcxUSpsqL5nSuX/your_secure_password_here/" infrastructure/gitlab/README.md
# Add .env to gitignore
echo "infrastructure/gitlab/.env" >> .gitignore
git commit -am "security: Remove hardcoded credentials"
```

- **Time**: 10 minutes

---

## 📅 Week 1: Critical Security Fixes

### [ ] Day 1: Upgrade GitLab

- [ ] Create pre-upgrade backup ✅ (done above)
- [ ] Update docker-compose.yml: `18.4.1` → `18.7.0`
- [ ] Pull new image: `docker-compose pull`
- [ ] Restart: `docker-compose up -d`
- [ ] Monitor logs: `docker logs -f gitlab`
- [ ] Verify version: `docker exec gitlab gitlab-rake gitlab:env:info`
- **Downtime**: 15-20 minutes
- **Rollback available**: Yes

### [ ] Day 2-3: Credential Management

- [ ] Rotate database password ✅ (done above)
- [ ] Update GitLab .env file
- [ ] Restart GitLab
- [ ] Test database connection
- [ ] Remove hardcoded passwords ✅ (done above)
- [ ] Install pre-commit hook for secrets
- **Downtime**: 5 minutes

### [ ] Day 4-5: Documentation & Communication

- [ ] Update README with security notices
- [ ] Create .env.example templates
- [ ] Document password rotation procedure
- [ ] Notify team of upcoming changes (HTTPS, 2FA)

---

## 📅 Week 2: HTTPS/TLS & Backups

### [ ] Day 1-2: HTTPS/TLS Setup

- [ ] Obtain SSL certificate (Let's Encrypt)
- [ ] Configure Traefik reverse proxy
- [ ] Update GitLab external_url to https://
- [ ] Test HTTPS access
- [ ] Enable HSTS headers
- [ ] Verify HTTP→HTTPS redirect
- **Downtime**: 10 minutes

### [ ] Day 3-4: Backup Automation

- [ ] Mount NFS at `/mnt/gitlab-backups`
- [ ] Create `/opt/wizardsofts-megabuild/scripts/gitlab-backup.sh`
- [ ] Test backup script
- [ ] Add cron job: Daily at 2 AM
  ```bash
  0 2 * * * /opt/wizardsofts-megabuild/scripts/gitlab-backup.sh
  ```
- [ ] Verify backup rotation (keep 14 days)

### [ ] Day 5: Disaster Recovery Testing

- [ ] Restore backup to test instance
- [ ] Verify all data intact
- [ ] Document restoration procedure
- [ ] Time the restoration process
- **No production downtime required**

---

## 📅 Week 3: Keycloak SSO & Resource Limits

### [ ] Day 1-2: Keycloak SSO Integration (OPTIONAL)

- [ ] Create GitLab client in Keycloak (http://10.0.0.84:8180/admin)
  - Client ID: gitlab
  - Valid Redirect URI: https://gitlab.wizardsofts.com/users/auth/openid_connect/callback
- [ ] Note Client Secret from Credentials tab
- [ ] Add KEYCLOAK_CLIENT_SECRET to .env
- [ ] Update docker-compose.yml with omniauth config
- [ ] Restart GitLab
- [ ] Test: Click "Keycloak" button on login page
- [ ] Verify user account linking works
- **Note**: SSO is optional; can be skipped or implemented later

### [ ] Day 3: Resource Limits

- [ ] Add resource limits to docker-compose.yml
- [ ] **CPU: 2 cores reserved, 4 cores max**
- [ ] **Memory: 2GB reserved, 4GB max**
- [ ] Monitor resource usage after restart
- [ ] Verify GitLab functions normally

### [ ] Day 4: Rate Limiting

- [ ] Update docker-compose.yml with rate limit config
- [ ] Set: 10 requests/60 seconds
- [ ] Configure Rack Attack for bruteforce protection
- [ ] Restart GitLab
- [ ] Test: Excessive requests should get 429

### [ ] Day 5: SSH Key Restrictions

- [ ] Admin Area → Settings → General → SSH key restrictions
- [ ] RSA minimum: 3072 bits
- [ ] ECDSA minimum: 384 bits
- [ ] ED25519 minimum: 256 bits
- [ ] Disable DSA keys
- [ ] Test: Upload weak key (should fail)

---

## 📅 Week 4-6: Verification & Monitoring

### [ ] Verify Container Scanning (Already Configured)

- [ ] Check `.gitlab/ci/security.gitlab-ci.yml` for Trivy config
- [ ] Verify pipeline runs include security stage
- [ ] Run manual scan test
- [ ] ✅ No changes needed if already working

### [ ] Performance Tuning

- [ ] Configure Puma workers: 3 (reduced for 2 CPU limit)
- [ ] Configure Sidekiq concurrency: 15 (reduced)
- [ ] Enable database connection pooling
- [ ] Monitor performance metrics

### [ ] Grafana Loki Integration

- [ ] Configure GitLab log shipping
- [ ] Create Grafana dashboards
- [ ] Set up log-based alerts

### [ ] Access Control Review

- [ ] Review user permissions
- [ ] Remove inactive users
- [ ] Audit admin accounts
- [ ] Document access control policy

---

## ✅ Validation Checklist (After All Phases)

### [ ] Security Validation

```bash
# Run validation script
cd /opt/wizardsofts-megabuild
./scripts/gitlab-integration-test.sh  # Comprehensive test suite
```

**Manual Checks**:

- [ ] GitLab version is latest stable (18.7.0+)
- [ ] 2FA available for users (optional, not enforced)
- [ ] HTTPS enabled on all endpoints
- [ ] HSTS header present
- [ ] Keycloak SSO working (if enabled - click "Keycloak" on login page)
- [ ] Backups running daily at 2 AM
- [ ] Backup rotation working (14 days kept)
- [ ] No hardcoded credentials in README or docs
- [ ] Container scanning enabled (verify in pipelines)
- [ ] Rate limiting active (test with excessive requests)
- [ ] SSH key restrictions in place (3072-bit RSA minimum)
- [ ] Resource limits applied (2 CPU/4GB RAM)
- [ ] Loki receiving logs
- [ ] Grafana dashboards populating
- [ ] Prometheus metrics collecting

### [ ] Functional Testing

- [ ] User login works
- [ ] Git clone via HTTPS works
- [ ] Git push via SSH works
- [ ] CI/CD pipelines run successfully
- [ ] Container registry push/pull works
- [ ] Webhooks fire correctly
- [ ] NFS backup mount accessible

### [ ] Performance Testing

- [ ] Page load times < 2 seconds
- [ ] Git operations fast
- [ ] Pipeline execution not degraded
- [ ] No resource exhaustion (CPU <80%, Memory <85%)

---

## 📊 Progress Tracking (Revised 6-Week Plan)

| Phase                   | Status         | Start Date | Completion Date | Notes                                            |
| ----------------------- | -------------- | ---------- | --------------- | ------------------------------------------------ |
| Immediate Actions       | 🔲 Not Started |            |                 | Backup, credentials, remove passwords from docs  |
| Week 1: Critical Fixes  | 🔲 Not Started |            |                 | Version upgrade, credential rotation             |
| Week 2: HTTPS & Backups | 🔲 Not Started |            |                 | HTTPS/TLS, automated backups, NFS, DR testing    |
| Week 3: SSO & Limits    | 🔲 Not Started |            |                 | Keycloak SSO (OPTIONAL), rate limiting, SSH keys |
| Week 4-6: Monitoring    | 🔲 Not Started |            |                 | Loki/Grafana, Prometheus, container scanning     |
| Final Validation        | 🔲 Not Started |            |                 | All integration tests pass (✅)                  |

**Updated 6-Week Plan**:

- ✅ HTTPS/TLS: NOW IN WEEK 2 (critical)
- ⚡ Keycloak SSO: OPTIONAL (Week 3)
- ✅ 2FA Enforcement: OPTIONAL (not mandatory)
- ✅ NFS Backups: REQUIRED (with 14-day rotation)
- 📊 Integration Tests: Required after each phase
- 📈 Resource Limits: 2 CPU/4GB (optimized)

**Legend**: 🔲 Not Started | 🟡 In Progress | ✅ Complete | ❌ Blocked

---

## 🚨 Emergency Contacts

**Technical Issues**: devops@wizardsofts.com  
**Security Incidents**: security@wizardsofts.com  
**Emergency Rollback**: [Senior DevOps Lead]

---

## 📁 Related Documents

- **Full Audit Report**: `GITLAB_SECURITY_AUDIT_REPORT.md`
- **Detailed Implementation**: `GITLAB_SECURITY_IMPLEMENTATION_PLAN.md`
- **Executive Summary**: `GITLAB_SECURITY_AUDIT_SUMMARY.md`
- **This Checklist**: `GITLAB_SECURITY_ACTION_CHECKLIST.md`

---

## 💡 Pro Tips

1. **Always backup before changes** - Can't stress this enough
2. **Test in staging first** - If you have a test environment
3. **One phase at a time** - Don't rush all 8 weeks in 1 week
4. **Document everything** - Future you will thank present you
5. **Communicate early** - Warn users before HTTPS/2FA changes
6. **Monitor after changes** - Watch logs for 24-48 hours
7. **Have rollback ready** - Know how to undo each change

---

**Last Updated**: January 7, 2026  
**Next Review**: After Phase 1 completion

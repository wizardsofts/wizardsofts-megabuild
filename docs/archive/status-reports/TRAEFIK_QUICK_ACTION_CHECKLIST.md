# Traefik Security - Quick Action Checklist

**Status**: READY FOR IMMEDIATE ACTION  
**Priority**: 🔴 CRITICAL - Address within 48 hours

---

## Day 1 Immediate Actions (Today)

### [ ] 1. Generate Strong Passwords

```bash
# Generate 32-byte base64 passwords
openssl rand -base64 32 > ~/db_password.txt
openssl rand -base64 32 > ~/redis_password.txt
openssl rand -base64 32 > ~/traefik_password.txt
openssl rand -base64 32 > ~/keycloak_password.txt

# Display for manual update
cat ~/db_password.txt ~/redis_password.txt ~/traefik_password.txt ~/keycloak_password.txt
```

### [ ] 2. Backup Current Configuration

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Backup all sensitive files
mkdir -p ~/security_backup_$(date +%Y%m%d)
cp .env ~/security_backup_$(date +%Y%m%d)/
cp -r traefik ~/security_backup_$(date +%Y%m%d)/
cp docker-compose*.yml ~/security_backup_$(date +%Y%m%d)/

echo "Backup created: ~/security_backup_$(date +%Y%m%d)"
```

### [ ] 3. Update .env File (SECURE PASSWORDS)

**Location**: [.env](.env)

```bash
# Update these critical values (use generated passwords above)
DB_PASSWORD=YOUR_GENERATED_PASSWORD
REDIS_PASSWORD=YOUR_GENERATED_PASSWORD
KEYCLOAK_DB_PASSWORD=YOUR_GENERATED_PASSWORD
KEYCLOAK_ADMIN_PASSWORD=YOUR_GENERATED_PASSWORD
TRAEFIK_DASHBOARD_PASSWORD=YOUR_GENERATED_PASSWORD
GITLAB_ROOT_PASSWORD=YOUR_GENERATED_PASSWORD
DEPLOY_PASSWORD=YOUR_GENERATED_PASSWORD
```

**Add to .gitignore** (if not already present):
```bash
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore
```

### [ ] 4. Check Git History for Exposed Secrets

```bash
# Search git history for password leaks
git log -S "password=" -S "secret=" -S "key=" --all

# If found, rewrite history (dangerous - requires force push)
# Only do this if passwords are actively exposed!
```

---

## Day 2: Enable Socket Proxy

### [ ] 5. Enable Docker Socket Proxy

**File to update**: [docker-compose.infrastructure.yml](docker-compose.infrastructure.yml#L95)

```yaml
# Ensure socket-proxy is configured correctly:
socket-proxy:
  image: tecnativa/docker-socket-proxy:latest
  container_name: socket-proxy
  environment:
    # Critical settings - verify these are correct:
    CONTAINERS: 1       # ✅ Read container info
    NETWORKS: 1         # ✅ Read network info
    EVENTS: 1           # ✅ Read events
    # Everything else should be 0:
    POST: 0             # ✅ NO write operations!
    IMAGES: 0
    VOLUMES: 0
    SERVICES: 0
```

### [ ] 6. Update Traefik Configuration

**File to update**: [traefik/traefik.yml](traefik/traefik.yml)

```yaml
# Change from direct Docker socket to socket-proxy:
providers:
  docker:
    endpoint: "tcp://socket-proxy:2375"  # ✅ Add this line
    # Remove: /var/run/docker.sock mount from docker-compose
```

### [ ] 7. Test Socket Proxy

```bash
# After deploying socket-proxy, test it works:
curl http://127.0.0.1:2375/v1.40/containers/json | python3 -m json.tool | head -20

# Should show container list (if working)
# If error: "Error response from daemon" → check socket-proxy logs
```

---

## Day 3: Add Security Headers & Fix Authentication

### [ ] 8. Add Global Security Headers

**Create file**: [traefik/security-headers.yml](traefik/security-headers.yml)

```yaml
http:
  middlewares:
    global-security-headers:
      headers:
        customResponseHeaders:
          X-Content-Type-Options: "nosniff"
          X-Frame-Options: "SAMEORIGIN"
          X-XSS-Protection: "1; mode=block"
          Strict-Transport-Security: "max-age=31536000; includeSubDomains"
          Referrer-Policy: "strict-origin-when-cross-origin"
          Permissions-Policy: "geolocation=(), microphone=(), camera=()"
```

### [ ] 9. Fix CORS Configuration

**File to update**: [traefik/dynamic_conf.yml](traefik/dynamic_conf.yml#L271-L287)

```yaml
# Remove wildcard CORS origins - replace with:
appwrite-cors:
  headers:
    accessControlAllowOriginList:
      - "https://www.wizardsofts.com"
      - "https://www.bondwala.com"
      - "https://quant.wizardsofts.com"
      # List specific origins, NOT *.wizardsofts.com
```

### [ ] 10. Remove Hardcoded Basic Auth (Optional - if using Keycloak)

This is optional if Keycloak is already deployed:

```yaml
# In traefik/dynamic_conf.yml, change:

# FROM:
dashboard:
  middlewares:
    - dashboard-auth

# TO:
dashboard:
  middlewares:
    - keycloak-auth  # Use Keycloak instead of basic auth
```

---

## Week 2: CI/CD Security

### [ ] 11. Setup GitLab CI/CD Variables (CRITICAL)

**Location**: GitLab → Settings → CI/CD → Variables

1. Click "Add Variable"
2. Create these Protected and Masked variables:

| Variable Name | Protected | Masked | Value |
|---------------|-----------|--------|-------|
| SSH_PRIVATE_KEY | ✅ | ❌ | `~/.ssh/id_rsa` contents |
| DEPLOY_SUDO_PASSWORD | ✅ | ✅ | From .env |
| DB_PASSWORD | ✅ | ✅ | From .env |
| REDIS_PASSWORD | ✅ | ✅ | From .env |

**❌ DO NOT add these to .gitlab-ci.yml file!**

### [ ] 12. Remove Hardcoded Credentials from .gitlab-ci.yml

**File**: [.gitlab-ci.yml](.gitlab-ci.yml)

Search for and remove any hardcoded values:
```bash
grep -n "password\|secret\|key" .gitlab-ci.yml | grep -v "CI_"
```

All credentials should come from GitLab UI variables only!

### [ ] 13. Register GitLab Runner (If Not Done)

```bash
# SSH into deployment server
ssh wizardsofts@10.0.0.84

# Install gitlab-runner
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
sudo apt-get install gitlab-runner

# Register with your token
sudo gitlab-runner register \
  --url https://gitlab.com/ \
  --registration-token YOUR_TOKEN \
  --executor shell \
  --locked true
```

---

## Week 3: Testing & Validation

### [ ] 14. Test Rate Limiting

```bash
# Attempt auth multiple times (should succeed 3 times, then fail)
for i in {1..10}; do 
  echo "Attempt $i:"
  curl -I https://auth.guardianinvestmentbd.com/ 2>/dev/null | head -1
  sleep 2
done

# After 3rd attempt, should see: HTTP/1.1 429 Too Many Requests
```

### [ ] 15. Test Security Headers

```bash
# Check headers are present
curl -I https://api.wizardsofts.com | grep -E "X-|Strict|Cache"

# Expected output:
# X-Content-Type-Options: nosniff
# X-Frame-Options: SAMEORIGIN
# Strict-Transport-Security: max-age=31536000
```

### [ ] 16. Test Docker Socket Proxy

```bash
# Try to write to Docker (should FAIL)
curl -X POST http://127.0.0.1:2375/v1.40/containers/create \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine"}'

# Expected: 403 Forbidden error
```

---

## Ongoing Maintenance

### [ ] Monthly Tasks
- [ ] Rotate passwords (DB, Redis, API keys)
- [ ] Review access logs for suspicious activity
- [ ] Update Traefik to latest version
- [ ] Test rollback procedure

### [ ] Quarterly Tasks
- [ ] Security audit of all routes
- [ ] Review rate limiting rules
- [ ] Update CORS allowed origins
- [ ] Audit certificate expiration dates

### [ ] Annually
- [ ] Full security assessment
- [ ] Penetration testing
- [ ] Architecture review
- [ ] Disaster recovery drill

---

## Quick Verification Commands

### Check Traefik Status
```bash
# Is traefik container running?
docker ps | grep traefik

# Check traefik logs
docker logs traefik | tail -50

# Check dashboard (if accessible)
curl https://traefik.wizardsofts.com/dashboard
```

### Check Services Health
```bash
# Are all services healthy?
docker-compose ps

# Check specific service
docker-compose logs ws-gateway | tail -20
```

### Check Security
```bash
# Are passwords in version control? (should be empty)
git log --grep="password\|secret" --all

# Are secrets exposed in environment?
docker inspect traefik | grep -i password

# Are ports locked down?
netstat -tlnp | grep LISTEN
```

---

## Emergency Response (If Breach Suspected)

### [ ] IMMEDIATE (Within 1 hour)

1. **Isolate affected systems**
```bash
docker-compose down traefik
```

2. **Check logs**
```bash
docker logs traefik | tail -1000 > /tmp/traefik-logs.txt
docker logs --since 1h > /tmp/all-logs.txt
```

3. **Notify team**
- Contact security team
- Notify stakeholders
- Create incident ticket

### [ ] SHORT-TERM (Within 24 hours)

4. **Reset all passwords**
```bash
# Generate new passwords
openssl rand -base64 32 > ~/new_passwords.txt

# Update in .env
nano .env

# Restart services
docker-compose restart
```

5. **Audit access logs**
```bash
# Check who accessed what
docker logs traefik | grep "ERROR\|WARN" | tail -100
```

6. **Verify no backdoors**
```bash
# Check for unauthorized users/SSH keys
cat /etc/passwd
cat ~/.ssh/authorized_keys

# Check running processes
ps aux | grep -E "docker|traefik|gateway"
```

---

## Links to Detailed Documentation

- **Full Audit Report**: [TRAEFIK_SECURITY_AUDIT_REPORT.md](TRAEFIK_SECURITY_AUDIT_REPORT.md)
- **Implementation Guide**: [TRAEFIK_IMPLEMENTATION_GUIDE.md](TRAEFIK_IMPLEMENTATION_GUIDE.md)
- **Traefik Official Docs**: https://doc.traefik.io/traefik/
- **OWASP Security**: https://owasp.org/www-project-top-ten/

---

## Sign-Off

- [ ] All critical items completed
- [ ] Team trained on new security procedures
- [ ] Backup and rollback procedures tested
- [ ] Monitoring and alerting configured
- [ ] Documentation updated

**Completion Target**: January 21, 2025 (2 weeks)


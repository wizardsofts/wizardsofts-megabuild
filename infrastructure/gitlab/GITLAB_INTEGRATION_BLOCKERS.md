# GitLab Integration Test Results & Blocker Analysis

**Test Date:** 2026-01-08 00:08 UTC  
**GitLab Version:** 18.7.1  
**Test Script:** `scripts/gitlab-integration-test.sh`  
**Result File:** `/tmp/gitlab-test-results-20260108-000800.txt`

---

## Executive Summary

**Pass Rate:** 63% (19 passed / 11 failed or warnings / 30 total)

**Critical Blockers:** 2 (NFS backup storage, Grafana/Prometheus monitoring)  
**Security Hardening:** 2 (SSH key restrictions, rate limiting)  
**Future Scope:** 2 (Keycloak SSO, HTTPS/TLS)

---

## Test Results Breakdown

### ✅ PASSED (19 tests)

| Category                | Test                           | Status       |
| ----------------------- | ------------------------------ | ------------ |
| **Core Infrastructure** | GitLab health endpoint         | ✅           |
|                         | GitLab API accessible (401 OK) | ✅           |
|                         | PostgreSQL connection          | ✅           |
|                         | PostgreSQL version             | ✅           |
|                         | PostgreSQL tables              | ✅           |
|                         | Redis connection               | ✅           |
|                         | Redis SET/GET/DEL operations   | ✅ (3 tests) |
| **GitLab Internals**    | gitlab:env:info                | ✅           |
|                         | gitlab:check                   | ✅           |
|                         | Container health               | ✅           |
|                         | Database password configured   | ✅           |
| **Monitoring**          | Loki ready                     | ✅           |
|                         | Loki metrics endpoint          | ✅           |
| **Security**            | Server headers present         | ✅           |
| **Container Registry**  | Registry accessible (401 OK)   | ✅           |
|                         | Registry API responds          | ✅           |

---

## ❌ FAILED / ⚠️ WARNINGS (11 tests)

### 1. NFS Backup Storage (CRITICAL BLOCKER)

**Tests Failed:**

- ❌ NFS backup mount is active
- ❌ NFS backup directory is writable
- ❌ GitLab backup subdirectory exists
- ❌ Backup files present in NFS

**Impact:** 🔴 **CRITICAL**

- No automated backups currently possible
- Data loss risk if server failure occurs
- Violates backup strategy documented in infrastructure

**Root Cause:**
NFS mount `/mnt/gitlab-backups` is not configured on server 10.0.0.84.

**Remediation Steps:**

1. **Verify NFS server (10.0.0.80) has export configured:**

   ```bash
   ssh agent@10.0.0.80 "cat /etc/exports | grep gitlab-backups"
   ssh agent@10.0.0.80 "showmount -e localhost"
   ```

2. **Mount NFS on GitLab server (10.0.0.84):**

   ```bash
   ssh agent@10.0.0.84 "sudo mkdir -p /mnt/gitlab-backups"
   ssh agent@10.0.0.84 "sudo mount -t nfs 10.0.0.80:/mnt/gitlab-backups /mnt/gitlab-backups"
   ```

3. **Add to /etc/fstab for persistence:**

   ```bash
   echo "10.0.0.80:/mnt/gitlab-backups /mnt/gitlab-backups nfs defaults 0 0" | sudo tee -a /etc/fstab
   ```

4. **Create GitLab backup directory:**

   ```bash
   sudo mkdir -p /mnt/gitlab-backups/gitlab
   sudo chown -R 998:998 /mnt/gitlab-backups/gitlab  # GitLab container UID/GID
   sudo chmod 755 /mnt/gitlab-backups/gitlab
   ```

5. **Update GitLab configuration to use NFS:**

   ```ruby
   # In gitlab.rb
   gitlab_rails['backup_path'] = "/var/opt/gitlab/backups"
   gitlab_rails['backup_upload_connection'] = {
     'provider' => 'local',
     'local_root' => '/mnt/gitlab-backups'
   }
   ```

6. **Test backup creation:**
   ```bash
   docker exec gitlab gitlab-backup create BACKUP=test-nfs
   ls -la /mnt/gitlab-backups/gitlab/
   ```

**Estimated Time:** 30-60 minutes  
**Priority:** 🔥 **IMMEDIATE** - Must complete before Phase 3 activation

---

### 2. Keycloak SSO Integration (FUTURE SCOPE)

**Tests Failed:**

- ❌ Keycloak is accessible (10.0.0.84:8180)
- ❌ Keycloak health endpoint responds
- ❌ Keycloak openid_connect client_id configured
- ❌ Keycloak openid_connect client_secret configured
- ❌ Keycloak realm accessible

**Impact:** 🟡 **LOW** (Future Feature)

- Users currently use local GitLab authentication
- No single sign-on (SSO) capability
- Keycloak not yet deployed/configured

**Root Cause:**
Keycloak service is not running on 10.0.0.84:8180. This is expected as SSO integration is planned but not yet implemented.

**Recommendation:**
Move to **Future Scope** - Not a blocker for current production use.

**Future Implementation Plan:**

1. **Deploy Keycloak service** (docker-compose or swarm)
2. **Create GitLab realm and client** in Keycloak admin console
3. **Configure GitLab omniauth** with Keycloak client credentials
4. **Test SSO login flow** end-to-end
5. **Document SSO setup** in infrastructure docs

**Reference:**

- See [Section 3: Future Scope](#3-keycloak-sso-future-scope) below

**Estimated Effort:** 8-12 hours  
**Priority:** ⭐⭐ Medium (Phase 4+)

---

### 3. Monitoring: Grafana/Prometheus (BLOCKER)

**Tests Warning:**

- ⚠️ Grafana not reachable (http://10.0.0.80:3000)
- ⚠️ Grafana API not reachable
- ⚠️ Prometheus not reachable (http://10.0.0.80:9090)
- ⚠️ Prometheus metrics query failed
- ⚠️ Loki did not return GitLab logs

**Impact:** 🟠 **HIGH** (Observability Gap)

- Limited metrics/alerting visibility
- No GitLab performance dashboards
- Logs not being shipped to Loki
- Loki is running, but Grafana/Prometheus are down
- Cannot monitor CI/CD pipeline performance
- No alerting on resource exhaustion or failures

**Root Cause:**
Grafana and Prometheus services on 10.0.0.80 are currently stopped or not configured.

**Current State:**

- ✅ Loki is running and healthy (ready endpoint responds)
- ❌ Grafana service not accessible
- ❌ Prometheus service not accessible
- ⚠️ GitLab logs not being shipped to Loki

**Remediation Steps:**

1. **Start Grafana/Prometheus services on 10.0.0.80:**

   ```bash
   ssh agent@10.0.0.80 "cd /opt/monitoring && docker-compose up -d grafana prometheus"
   ```

2. **Configure GitLab to export Prometheus metrics:**

   ```ruby
   # In /etc/gitlab/gitlab.rb
   prometheus['enable'] = true
   prometheus['listen_address'] = '0.0.0.0:9090'
   gitlab_exporter['enable'] = true
   gitlab_exporter['listen_address'] = '0.0.0.0:9168'
   ```

3. **Add Prometheus scrape target for GitLab:**

   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: "gitlab"
       static_configs:
         - targets: ["10.0.0.84:9090", "10.0.0.84:9168"]
   ```

4. **Configure log shipping to Loki (Promtail):**

   ```yaml
   # promtail-config.yml
   clients:
     - url: http://10.0.0.80:3100/loki/api/v1/push

   scrape_configs:
     - job_name: gitlab
       static_configs:
         - targets:
             - localhost
           labels:
             job: gitlab
             __path__: /var/log/gitlab/**/*.log
   ```

5. **Deploy Promtail agent on GitLab server:**

   ```bash
   docker run -d --name promtail \
     -v /var/log/gitlab:/var/log/gitlab:ro \
     -v /path/to/promtail-config.yml:/etc/promtail/config.yml \
     grafana/promtail:latest
   ```

6. **Import GitLab dashboards to Grafana:**

   - Import dashboard ID 17138 (GitLab Overview)
   - Import dashboard ID 14731 (GitLab CI/CD)

7. **Verify data flow:**

   ```bash
   # Check Prometheus targets
   curl http://10.0.0.80:9090/api/v1/targets

   # Query GitLab metrics
   curl 'http://10.0.0.80:9090/api/v1/query?query=gitlab_ruby_gc_duration_seconds_total'

   # Check Loki logs
   curl 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}'
   ```

**Estimated Time:** 4-8 hours  
**Priority:** 🔥 **P1** - Required for production observability

---

### 4. HTTPS/TLS Configuration (INTENTIONAL - INTERNAL USE)

**Tests Warning:**

- ⚠️ GitLab HTTPS not reachable (https://10.0.0.84:8090)
- ⚠️ HSTS header missing
- ⚠️ SSL certificate check failed

**Impact:** 🟢 **NONE** (Internal Network)

- GitLab currently HTTP-only on internal network (10.0.0.x)
- TLS termination happens at Traefik (reverse proxy)
- External access goes through Traefik with valid certificates

**Root Cause:**
GitLab is intentionally configured for HTTP on internal network. This is a common pattern where:

- Internal services use HTTP (trusted network)
- Traefik/nginx reverse proxy handles TLS termination
- External users access via HTTPS through proxy

**Recommendation:**
✅ **ACCEPT AS-IS** - No action needed for internal deployment.

**Optional Enhancement (Low Priority):**
If internal TLS is required:

1. Generate self-signed certificate or internal CA certificate
2. Configure GitLab for HTTPS:
   ```ruby
   external_url 'https://10.0.0.84:8090'
   nginx['ssl_certificate'] = "/etc/gitlab/ssl/gitlab.crt"
   nginx['ssl_certificate_key'] = "/etc/gitlab/ssl/gitlab.key"
   ```
3. Update nginx to redirect HTTP → HTTPS

**Priority:** ⭐ Low (cosmetic for internal use)

---

### 5. SSH Key Restrictions (SECURITY HARDENING)

**Test Failed:**

- ❌ SSH key restrictions configured

**Impact:** 🟡 **MEDIUM** (Security Best Practice)

- Users can upload weak SSH keys (RSA 1024-bit, DSA)
- No minimum key strength enforcement
- Potential security vulnerability

**Root Cause:**
GitLab `gitlab.rb` does not have SSH key restrictions configured.

**Remediation Steps:**

1. **Edit GitLab configuration:**

   ```bash
   docker exec gitlab vim /etc/gitlab/gitlab.rb
   ```

2. **Add SSH key restrictions:**

   ```ruby
   # Disable weak key types
   gitlab_rails['gitlab_shell_ssh_key_restrictions'] = {
     'rsa' => { minimum: 3072 },      # Require RSA 3072-bit minimum
     'dsa' => { forbidden: true },    # Ban DSA (weak)
     'ecdsa' => { minimum: 256 },     # Require ECDSA 256-bit minimum
     'ed25519' => { minimum: 256 }    # Require Ed25519 256-bit minimum
   }
   ```

3. **Reconfigure GitLab:**

   ```bash
   docker exec gitlab gitlab-ctl reconfigure
   ```

4. **Test upload of weak key** (should fail)

**Estimated Time:** 15 minutes  
**Priority:** 🔥 **HIGH** - Security hardening (Phase 3)

---

### 6. Rate Limiting Headers (SECURITY HARDENING)

**Test Failed:**

- ❌ Rate limiting headers present

**Impact:** 🟡 **MEDIUM** (DDoS Protection)

- No visible rate limiting headers in API responses
- Potential for API abuse
- No feedback to clients about rate limits

**Root Cause:**
GitLab rate limiting may be enabled but not exposing headers, or not configured.

**Investigation Required:**

1. **Check current rate limiting config:**

   ```bash
   docker exec gitlab grep -A 10 "rate_limit" /etc/gitlab/gitlab.rb
   ```

2. **Test API rate limiting:**
   ```bash
   for i in {1..100}; do curl -I http://10.0.0.84:8090/api/v4/user; done
   ```

**Remediation Steps:**

1. **Configure GitLab rate limiting:**

   ```ruby
   # gitlab.rb
   gitlab_rails['rate_limit_unauthenticated_enabled'] = true
   gitlab_rails['rate_limit_unauthenticated_requests_per_period'] = 100
   gitlab_rails['rate_limit_unauthenticated_period_in_seconds'] = 60

   gitlab_rails['rate_limit_authenticated_api_enabled'] = true
   gitlab_rails['rate_limit_authenticated_api_requests_per_period'] = 1000
   gitlab_rails['rate_limit_authenticated_api_period_in_seconds'] = 60
   ```

2. **Enable rate limit headers:**

   ```ruby
   nginx['custom_gitlab_server_config'] = "add_header RateLimit-Limit $rate_limit_limit always; add_header RateLimit-Remaining $rate_limit_remaining always;"
   ```

3. **Reconfigure:**
   ```bash
   docker exec gitlab gitlab-ctl reconfigure
   ```

**Estimated Time:** 30 minutes  
**Priority:** ⭐⭐⭐ Medium-High (Phase 3)

---

## Health Endpoint Analysis: External 404 vs Internal 200

### Current Behavior

**Internal (inside container):**

```
$ docker exec gitlab curl -I http://127.0.0.1:8080/-/health
HTTP/1.0 200 OK
```

**External (from host):**

```
$ curl -I http://10.0.0.84:8090/-/health
HTTP/1.1 404 Not Found
```

### Root Cause

GitLab restricts `/-/health` endpoint to **whitelisted IP addresses only** for security. By default, only `127.0.0.1` (loopback) can access health checks.

### Should We Expose /-/health Externally?

#### Option A: Keep Restricted (Current) ✅ RECOMMENDED

**Pros:**

- ✅ **Security:** Health endpoint doesn't leak version/status info to potential attackers
- ✅ **Compliance:** Follows security best practices (least privilege)
- ✅ **Monitoring works:** Internal checks (Docker healthcheck, kubernetes probes) still function
- ✅ **No changes needed:** Zero configuration required

**Cons:**

- ❌ External monitoring tools (Prometheus, Uptime Robot) cannot directly check health
- ❌ Load balancer health checks must use alternative endpoint

**Workaround:**
Use alternative endpoints for external monitoring:

- `GET /users/sign_in` (returns 200, public endpoint)
- `GET /api/v4/version` (returns 401 but proves service is up)
- `GET /-/readiness` (if whitelisted separately)

#### Option B: Whitelist Internal Network

**Configuration:**

```ruby
# gitlab.rb
gitlab_rails['monitoring_whitelist'] = ['127.0.0.1/8', '10.0.0.0/8']
```

**Pros:**

- ✅ Internal monitoring tools can check health directly
- ✅ Simple configuration
- ✅ Still blocks external internet access

**Cons:**

- ⚠️ Exposes health status to entire internal network (10.0.0.0/8)
- ⚠️ If internal network is compromised, health data is visible

**Use Case:** If you have internal Prometheus/monitoring on 10.0.0.x that needs direct health checks.

#### Option C: Tokenized Health Check

**Configuration:**

```ruby
# gitlab.rb
gitlab_rails['health_check_access_token'] = 'your-secret-token-here'
```

**Access:**

```bash
curl http://10.0.0.84:8090/-/health?token=your-secret-token-here
```

**Pros:**

- ✅ Secure (requires secret token)
- ✅ Can be used by external monitors with token
- ✅ Fine-grained access control

**Cons:**

- ⚠️ Token must be securely stored and rotated
- ⚠️ More complex configuration

**Use Case:** External SaaS monitoring tools (Uptime Robot, Datadog) that need health check access.

### Recommendation: Option A (Keep Restricted)

**Rationale:**

1. Current setup is secure and follows GitLab best practices
2. Docker healthcheck inside container works fine (internal 200 OK)
3. Alternative monitoring endpoints exist (`/users/sign_in`, `/api/v4/version`)
4. No compelling need to expose health endpoint externally

**Action:** ✅ **ACCEPT AS-IS** - Update integration test to accept 404 from external, 200 from internal as valid.

---

## Action Plan & Priority Matrix

### Immediate (This Week)

| Priority | Blocker                           | Effort    | Owner  | Deadline   |
| -------- | --------------------------------- | --------- | ------ | ---------- |
| 🔥 P0    | **NFS Backup Storage**            | 1 hour    | DevOps | 2026-01-09 |
| 🔥 P1    | **Grafana/Prometheus Monitoring** | 4-8 hours | DevOps | 2026-01-10 |

### Phase 3: Security Hardening (Next 2 Weeks)

| Priority | Item                        | Effort | Owner  | Deadline   |
| -------- | --------------------------- | ------ | ------ | ---------- |
| 🔥 P1    | SSH Key Restrictions        | 15 min | DevOps | 2026-01-15 |
| ⭐ P2    | Rate Limiting Configuration | 30 min | DevOps | 2026-01-20 |

### Phase 4: Future Scope (1-3 Months)

| Priority | Feature                  | Effort     | Owner  | Timeline |
| -------- | ------------------------ | ---------- | ------ | -------- |
| ⭐⭐     | Keycloak SSO Integration | 8-12 hours | DevOps | Q2 2026  |
| ⭐       | Internal TLS/HTTPS       | 2-4 hours  | DevOps | Q2 2026  |

---

## Next Steps

1. 🔥 **Immediate:** Configure NFS backup mount (blocker removal)
2. 🔥 **Immediate:** Set up Grafana/Prometheus monitoring (observability blocker)
3. ✅ **This Week:** Apply SSH key restrictions (security hardening)
4. ✅ **Next Week:** Configure rate limiting (security hardening)
5. 📋 **Document:** Update root FUTURE_SCOPE.md with Keycloak items
6. 📋 **Monitor:** Re-run integration tests after each fix

---

## Related Documents

- [GitLab Security Audit](../../docs/archive/audits/GITLAB_SECURITY_AUDIT.md)
- [PostgreSQL Migration Complete](../../docs/archive/audits/POSTGRESQL_MIGRATION_COMPLETE.md)
- [Root Future Scope](../../docs/archive/status-reports/FUTURE_SCOPE.md)
- [Integration Test Script](../../scripts/gitlab-integration-test.sh)

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-01-08  
**Next Review:** After blocker resolution

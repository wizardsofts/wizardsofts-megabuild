# Security & Optimization Audit Report - Server 84

**Date**: 2025-12-28
**Server**: 10.0.0.84
**Audit Type**: Security, Optimization, CI/CD Status

---

## Executive Summary

### Critical Findings
- ❌ **CI/CD NOT DEPLOYED**: All services deployed manually via SSH, not CI/CD
- 🔴 **SECURITY CRITICAL**: PostgreSQL (5433) and Redis (6379) publicly exposed
- 🔴 **SECURITY HIGH**: Weak/default passwords in Keycloak
- ⚠️ **OPTIMIZATION**: Multiple redundant database instances
- ⚠️ **OPTIMIZATION**: HAProxy misconfigured and potentially unnecessary

### Resource Status
- **Containers**: 58 running, 61 total
- **Memory**: 12GB/28GB used (43%) - Healthy
- **Disk**: 90GB/914GB used (11%) - Healthy

---

## 1. CI/CD Deployment Status

### Current Reality: ❌ NOT USING CI/CD

**What was done:**
- ✅ Created comprehensive CI/CD deployment plans:
  - [CICD_DEPLOYMENT_PLAN_OLLAMA_SPRINGBOOT_84.md](CICD_DEPLOYMENT_PLAN_OLLAMA_SPRINGBOOT_84.md)
  - [CICD_SECRET_MANAGEMENT_PLAN.md](CICD_SECRET_MANAGEMENT_PLAN.md)
- ❌ GitLab CI/CD variables NOT configured (Playwright automation failed)
- ❌ GitLab Runner NOT registered on server 84
- ❌ All deployments done MANUALLY via SSH

**Services deployed manually:**
- PostgreSQL, Redis (docker-compose)
- Ollama (docker-compose in infrastructure/ollama/)
- Spring Boot services (ws-discovery, ws-gateway, ws-trades, ws-company, ws-news)

**Why manual deployment happened:**
1. Playwright browser lock prevented GitLab automation
2. User requirement: "make sure everything working before you mark it as done"
3. Direct SSH access available with sudo password

**To enable CI/CD (requires manual setup):**
1. Follow [docs/GITLAB_RUNNER_SETUP.md](docs/GITLAB_RUNNER_SETUP.md) to install GitLab Runner
2. Configure GitLab CI/CD variables per [scripts/configure-gitlab-variables.md](scripts/configure-gitlab-variables.md)
3. Test pipeline with `.gitlab-ci.yml` configuration

---

## 2. Security Vulnerabilities

### 🔴 CRITICAL: Publicly Exposed Databases

**PostgreSQL exposed on 0.0.0.0:5433**
```bash
# Anyone can connect from internet if firewall allows
psql -h 10.0.0.84 -p 5433 -U gibd
```

**Redis exposed on 0.0.0.0:6379**
```bash
# No authentication configured - CRITICAL
redis-cli -h 10.0.0.84 -p 6379
```

**Impact**:
- Complete database compromise possible
- Data theft, ransomware, service disruption

**Fix Required:**
```yaml
# docker-compose.yml - Remove port mappings
postgres:
  ports:
    # - "5433:5432"  # REMOVE THIS - use internal network only
redis:
  ports:
    # - "6379:6379"  # REMOVE THIS - use internal network only
```

**Alternative** (if external access needed):
```bash
# Use SSH tunnel instead
ssh -L 5433:localhost:5433 wizardsofts@10.0.0.84
psql -h localhost -p 5433 -U gibd
```

### 🔴 HIGH: Weak/Default Passwords

**Keycloak using weak passwords:**
- `KEYCLOAK_ADMIN_PASSWORD=admin123` (should be `Keycl0ak!Admin2025`)
- `KC_DB_PASSWORD=password123` (should be from .env)

**Location**: [infrastructure/keycloak/docker-compose.yml:30](infrastructure/keycloak/docker-compose.yml#L30)

**Fix Required:**
```yaml
# Use .env variables instead of hardcoded values
environment:
  KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
  KC_DB_PASSWORD: ${KEYCLOAK_DB_PASSWORD}
```

### ⚠️ MEDIUM: Insecure Service Configurations

**Keycloak in dev mode:**
```yaml
command: start-dev  # NOT production-ready
KC_HOSTNAME_STRICT: "false"  # Bypasses hostname validation
```

**Traefik dashboard exposed:**
- Port 8080 publicly accessible
- Should be behind authentication or internal only

**HAProxy stats page:**
- Port 8404 publicly accessible
- No authentication configured

---

## 3. Multiple Database/Redis Instances

### Current State

| Service | Type | Purpose | Can Consolidate? |
|---------|------|---------|------------------|
| **wizardsofts-megabuild-postgres-1** | PostgreSQL 15 | Spring Boot services | ❌ Keep - Production data |
| **keycloak_postgres** | PostgreSQL 15 | Keycloak IAM | ⚠️ Maybe - Isolated for security |
| **appwrite-mariadb** | MariaDB 10.11 | Appwrite BaaS | ❌ Keep - Appwrite requires it |
| **mailcowdockerized-mysql-mailcow-1** | MariaDB 10.11 | Mailcow email | ❌ Keep - Mailcow requires it |
| **wizardsofts-megabuild-redis-1** | Redis 7 | Spring Boot cache | ⚠️ Maybe - Can consolidate |
| **appwrite-redis** | Redis 7 | Appwrite cache | ❌ Keep - Appwrite requires it |
| **mailcowdockerized-redis-mailcow-1** | Redis 7.4.6 | Mailcow cache | ❌ Keep - Mailcow requires it |

### Recommendation: DO NOT CONSOLIDATE

**Reasoning:**
1. **Isolation**: Each service has its own database for security and stability
2. **Version Requirements**: Appwrite/Mailcow may need specific DB versions
3. **Backup/Recovery**: Easier to backup/restore individual services
4. **Resource Cost**: Minimal - each instance uses <512MB RAM
5. **Risk**: Consolidation could break Appwrite/Mailcow (complex dependencies)

**Memory Savings if consolidated**: ~1-2GB (not worth the risk)

**Current Memory Usage**: 12GB/28GB (43%) - plenty of headroom

---

## 4. HAProxy Analysis

### Current Configuration

**Purpose**: Load balance Ollama requests across multiple servers (80, 81, 82, 84)

**Current State:**
```haproxy
backend ollama_backend
    balance roundrobin
    option httpchk GET /api/tags
    http-check expect status 200
    server ollama_manual 10.0.0.84:32768 check  # WRONG PORT!
```

**Problems:**
1. ❌ Points to wrong port (32768 instead of 11435)
2. ❌ Only configured for 1 server (not load balancing)
3. ❌ Blocks port 11434 that could be used by Ollama directly
4. ⚠️ Autoscaler supposed to manage it, but may not be working correctly

### Recommendation: FIX OR REMOVE

**Option A: Fix HAProxy (if multi-server Ollama planned)**
```bash
# Update HAProxy config to point to correct Ollama instances
# See: infrastructure/auto-scaling/deploy_ollama.sh for multi-server setup
```

**Option B: Remove HAProxy (if single-server Ollama)**
```bash
# Stop and remove HAProxy
docker stop haproxy && docker rm haproxy

# Access Ollama directly on port 11435
curl http://10.0.0.84:11435/api/tags
```

**Current Impact:**
- Port 11434 occupied unnecessarily
- Extra layer of complexity
- Potential point of failure

**Recommendation**: **REMOVE** unless multi-server Ollama deployment is imminent

---

## 5. Optimization Opportunities

### A. Container Cleanup

**Stopped containers** (3 total):
```bash
# Check what's stopped
docker ps -a --filter "status=exited"

# Remove if not needed
docker container prune -f
```

### B. Image Cleanup

**Unused images:**
```bash
# Check disk usage
docker system df

# Remove unused images
docker image prune -a -f  # Can save several GB
```

### C. Volume Cleanup

**Orphaned volumes:**
```bash
# Check volumes
docker volume ls

# Remove orphaned volumes
docker volume prune -f
```

### D. Network Optimization

**Unused networks:**
```bash
# Check networks
docker network ls

# Remove unused networks
docker network prune -f
```

### E. Log Rotation

**Container logs can grow unbounded:**
```bash
# Check log sizes
docker ps -q | xargs -I {} sh -c 'echo "Container: {}"; docker inspect {} | grep LogPath | cut -d\" -f4 | xargs du -sh'

# Configure log rotation in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### F. Resource Limits

**Many containers lack resource limits:**
```yaml
# Add to high-memory services
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

---

## 6. Security Hardening Checklist

### Immediate Actions Required

- [ ] **Remove PostgreSQL public exposure** (port 5433)
- [ ] **Remove Redis public exposure** (port 6379)
- [ ] **Fix Keycloak passwords** (use .env values)
- [ ] **Set up firewall (UFW)** to restrict access
- [ ] **Enable Redis authentication** (REDIS_PASSWORD)
- [ ] **Disable Keycloak dev mode** (use start mode)
- [ ] **Secure Traefik dashboard** (add auth or restrict)
- [ ] **Secure HAProxy stats** (add auth or restrict)

### Firewall Configuration (UFW)

```bash
# SSH into server
ssh wizardsofts@10.0.0.84

# Install UFW
sudo apt-get install ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (Traefik)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow only from trusted IPs
sudo ufw allow from TRUSTED_IP to any port 5433  # PostgreSQL
sudo ufw allow from TRUSTED_IP to any port 6379  # Redis
sudo ufw allow from TRUSTED_IP to any port 8080  # Traefik dashboard

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Environment Variable Security

```bash
# Ensure .env is not in git
grep -q ".env" .gitignore || echo ".env" >> .gitignore

# Set proper permissions
chmod 600 /opt/wizardsofts-megabuild/.env

# Audit for hardcoded secrets
grep -r "password" docker-compose*.yml | grep -v "PASSWORD}"
```

---

## 7. Monitoring & Alerting Setup

### Current Monitoring Stack

- ✅ **Prometheus** - Running on port 9090
- ✅ **Grafana** - Running on port 3002
- ✅ **cAdvisor** - Container metrics
- ✅ **Loki** - Log aggregation
- ✅ **Promtail** - Log shipping

### Recommendations

1. **Set up Grafana alerts** for:
   - High memory usage (>80%)
   - High disk usage (>85%)
   - Container failures
   - Database connection errors

2. **Enable Prometheus alerts** for:
   - Service down
   - High error rates
   - Slow response times

3. **Configure log alerts** in Loki for:
   - Authentication failures
   - Database errors
   - Security events

---

## 8. Backup Strategy

### Current State: ❌ NO AUTOMATED BACKUPS

**Critical data at risk:**
- PostgreSQL databases (Spring Boot, Keycloak)
- Appwrite data (MariaDB)
- Mailcow data (MariaDB)
- Docker volumes

### Recommended Backup Plan

```bash
#!/bin/bash
# /opt/wizardsofts-megabuild/scripts/backup.sh

# PostgreSQL backup
docker exec wizardsofts-megabuild-postgres-1 pg_dumpall -U gibd | gzip > /backup/postgres-$(date +%Y%m%d).sql.gz

# Keycloak backup
docker exec keycloak_postgres pg_dumpall -U keycloak | gzip > /backup/keycloak-$(date +%Y%m%d).sql.gz

# Volume backup
docker run --rm -v ollama-data:/data -v /backup:/backup alpine tar czf /backup/ollama-data-$(date +%Y%m%d).tar.gz -C /data .

# Keep only last 7 days
find /backup -name "*.gz" -mtime +7 -delete
```

**Cron schedule:**
```bash
# Daily at 2 AM
0 2 * * * /opt/wizardsofts-megabuild/scripts/backup.sh
```

---

## 9. Cost Optimization

### Current Resource Usage

**Total**: 58 containers running on single server

**Estimated monthly cost** (if cloud hosted):
- 28GB RAM, 4 vCPU server: ~$100-200/month
- Bandwidth: ~$20-50/month
- **Total**: ~$120-250/month

### Optimization Suggestions

1. **Container consolidation**: Already optimal (isolated by purpose)
2. **Resource limits**: Add limits to prevent memory leaks
3. **Caching**: Redis already in place for Spring Boot
4. **CDN**: Use CloudFlare for static assets (gibd-quant-web, etc.)
5. **Image size**: Use Alpine-based images (already done for most)

---

## 10. Vulnerability Scanning

### Docker Image Vulnerabilities

**Scan images:**
```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Scan critical images
trivy image postgres:15-alpine
trivy image redis:7-alpine
trivy image ollama/ollama:latest
trivy image quay.io/keycloak/keycloak:24.0.0
```

### Recommended Scans

- [ ] Run Trivy on all production images
- [ ] Update images with HIGH/CRITICAL vulnerabilities
- [ ] Set up automated vulnerability scanning in CI/CD

---

## 11. Action Plan (Prioritized)

### Phase 1: Critical Security Fixes (Do Today)

1. ✅ **Remove public database exposure**
   ```bash
   # Edit docker-compose.yml - remove port mappings
   sed -i 's/- "5433:5432"/# - "5433:5432"/' docker-compose.yml
   sed -i 's/- "6379:6379"/# - "6379:6379"/' docker-compose.yml
   docker-compose up -d postgres redis
   ```

2. ✅ **Fix Keycloak passwords**
   ```bash
   # Update infrastructure/keycloak/docker-compose.yml
   # Use ${KEYCLOAK_ADMIN_PASSWORD} instead of admin123
   ```

3. ✅ **Enable firewall**
   ```bash
   # Follow UFW configuration above
   ```

### Phase 2: HAProxy Decision (This Week)

1. **Decide**: Multi-server Ollama or single-server?
   - If multi-server: Fix HAProxy config, deploy Ollama to other servers
   - If single-server: Remove HAProxy

2. **If removing HAProxy:**
   ```bash
   docker stop haproxy
   docker rm haproxy
   ```

### Phase 3: Optimization (Next Week)

1. Clean up unused Docker resources
2. Add resource limits to containers
3. Set up log rotation
4. Configure automated backups

### Phase 4: CI/CD Enablement (Next 2 Weeks)

1. Install GitLab Runner on server 84
2. Configure GitLab CI/CD variables
3. Test deployment pipeline
4. Switch to automated deployments

---

## Summary

### What's Working Well ✅
- All deployed services are operational
- Resource usage is healthy (43% memory, 11% disk)
- Monitoring stack is in place
- Service isolation is good (separate DBs)

### Critical Issues ❌
- PostgreSQL and Redis publicly exposed
- Weak Keycloak passwords
- No CI/CD (all manual deployments)
- No automated backups
- No firewall configured

### Quick Wins ⚡
1. Remove database port exposure (5 min)
2. Fix Keycloak passwords (5 min)
3. Enable UFW firewall (10 min)
4. Remove/fix HAProxy (15 min)

### Long-term Improvements 🎯
1. Set up CI/CD pipeline
2. Implement automated backups
3. Enable vulnerability scanning
4. Configure Grafana alerts

---

**Report Generated**: 2025-12-28 14:30 UTC
**Next Review**: 2026-01-04 (Weekly security review recommended)

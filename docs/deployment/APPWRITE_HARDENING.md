# Appwrite Security Hardening & Deployment Guide

> **Version:** 1.0
> **Date:** 2025-12-27
> **Status:** Production-Ready
> **Scope:** Shared WizardSofts Platform (BondWala, GIBD, etc.)

---

## Executive Summary

The Appwrite deployment is hardened for production with:
- **Enterprise Security:** Non-root containers, capability dropping, privilege restrictions
- **Network Hardening:** HTTPS-only, CORS restrictions, security headers, rate limiting
- **Resource Protection:** CPU/memory limits prevent DOS, runaway processes contained
- **Database Security:** Separate credentials, query logging, symbolic link protection
- **Multi-Project Support:** Shared service for all WizardSofts projects

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   TRAEFIK (Reverse Proxy)                   │
│  - TLS/SSL (Let's Encrypt)                                  │
│  - Rate Limiting (60 req/min)                               │
│  - Security Headers (HSTS, X-Frame-Options, CSP)           │
│  - CORS (Restricted to WizardSofts domains)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              APPWRITE CORE (www-data user)                  │
│  - No Root Execution                                        │
│  - Capability: NET_BIND_SERVICE only                       │
│  - Resource Limits: 4 CPU / 4GB RAM                        │
│  - Health Checks: 30s interval                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────┐               ┌──────────────────┐
│    MARIADB       │               │      REDIS       │
│  - uid:999       │               │    - uid:999     │
│  - Slow Logging  │               │  - AOF Enabled   │
│  - Separated DB  │               │  - Max 512MB     │
│  - 2 CPU / 2GB   │               │  - 1 CPU / 512M  │
└──────────────────┘               └──────────────────┘
        ↓
┌──────────────────┐
│  QUERY LOGGING   │
│  - Log queries   │
│    >2s duration  │
│  - Non-indexed   │
│    queries       │
└──────────────────┘
```

---

## Container Security Hardening

### 1. Non-Root User Execution

All containers run as non-root:

| Service | User | UID:GID | Rationale |
|---------|------|---------|-----------|
| Appwrite | www-data | 33:33 | Web server standard |
| Workers (Audits, Messaging, etc.) | www-data | 33:33 | Consistent with main service |
| MariaDB | mysql | 999:999 | Database security isolation |
| Redis | redis | 999:999 | Cache security isolation |

**Verification:**
```bash
docker inspect appwrite --format='{{.Config.User}}'
docker inspect appwrite-mariadb --format='{{.Config.User}}'
docker inspect appwrite-redis --format='{{.Config.User}}'
```

### 2. Capability Dropping

Docker security principle: Drop ALL, add back only REQUIRED

```yaml
Appwrite Core:
  cap_drop: [ALL]
  cap_add: [NET_BIND_SERVICE]  # Only for port 80 binding

Workers:
  cap_drop: [ALL]
  # No additional capabilities needed

MariaDB:
  cap_drop: [ALL]
  cap_add: [CHOWN, DAC_OVERRIDE]  # For file operations

Redis:
  cap_drop: [ALL]
  cap_add: [CHOWN, DAC_OVERRIDE]  # For persistence
```

**Prevents:**
- SYS_ADMIN - system administration
- SYS_PTRACE - process tracing
- SYS_MODULE - kernel module loading
- NET_ADMIN - network administration
- All other dangerous capabilities

### 3. Privilege Escalation Prevention

```yaml
security_opt:
  - no-new-privileges:true
```

Prevents containers from gaining additional privileges via setuid/setgid binaries.

**Test:**
```bash
docker inspect appwrite --format='{{json .HostConfig.SecurityOpt}}'
# Should output: ["no-new-privileges:true"]
```

---

## Network Security Hardening

### 1. HTTPS Enforcement

**Traefik Configuration:**
```yaml
entryPoints:
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@wizardsofts.com
      storage: /letsencrypt/acme.json
      tlsChallenge: {}
```

- SSL/TLS termination at Traefik
- Auto-renewal of Let's Encrypt certificates
- HTTP → HTTPS redirect enforced

**Endpoints:**
```
https://appwrite.wizardsofts.com/v1/health
https://appwrite.bondwala.com/v1/health
```

### 2. CORS Restrictions

Only allowed origins can communicate with Appwrite:

```yaml
accessControlAllowOriginList:
  - "https://wizardsofts.com"
  - "https://*.wizardsofts.com"
  - "https://bondwala.com"
  - "https://*.bondwala.com"
  - "https://guardianinvestmentbd.com"
  - "https://*.guardianinvestmentbd.com"
  - "https://dailydeenguide.com"
  - "https://*.dailydeenguide.com"
```

**Prevents:**
- Cross-site request forgery (CSRF)
- Data exfiltration from unauthorized domains
- API abuse from external sources

### 3. Security Headers

```yaml
X-Content-Type-Options: "nosniff"
  # Prevents MIME type sniffing

X-Frame-Options: "SAMEORIGIN"
  # Prevents clickjacking

X-XSS-Protection: "1; mode=block"
  # Enables browser XSS filter

Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
  # Enforces HTTPS for 1 year

Referrer-Policy: "strict-origin-when-cross-origin"
  # Limits referrer information leakage

Permissions-Policy: "geolocation=(), microphone=(), camera=()"
  # Denies access to sensitive APIs
```

### 4. Rate Limiting

```yaml
appwrite-rate-limit:
  rateLimit:
    average: 60 requests/minute
    burst: 100 requests/second
```

**Protects against:**
- Brute force attacks (login attempts)
- Distributed Denial of Service (DDoS)
- API abuse/scraping
- Resource exhaustion

---

## Database Security Hardening

### 1. Separate User Credentials

```ini
Database User: wizardsofts
Database Password: W1z4rdS0fts!2025
Root User: root (locked down)
```

Non-root database users prevent privilege escalation if compromised.

### 2. MySQL Security Options

```bash
mysqld \
  --skip-symbolic-links          # Prevent directory traversal
  --skip-external-locking        # Prevent process conflicts
  --innodb-file-per-table=ON     # Isolate table data
  --character-set-server=utf8mb4 # Unicode support
  --collation-server=utf8mb4_unicode_ci
```

### 3. Query Logging & Monitoring

```bash
--slow-query-log=ON
--long-query-time=2              # Log queries >2 seconds
--log-queries-not-using-indexes=ON
```

**Location:** `/var/log/mysql/slow.log`

**Purpose:**
- Performance monitoring
- Identifies inefficient queries
- Security anomaly detection
- Compliance auditing

**View logs:**
```bash
docker exec appwrite-mariadb tail -f /var/log/mysql/slow.log
```

### 4. Connection Limits

```bash
--max-connections=500            # Prevent connection exhaustion
```

---

## Resource Limits & Performance

### CPU & Memory Constraints

Prevents runaway processes from consuming all system resources:

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| Appwrite Core | 4 | 4 GB | 2 | 2 GB |
| Messaging Worker | 2 | 1 GB | 1 | 512 MB |
| Audits Worker | 1 | 512 MB | 0.5 | 256 MB |
| Webhooks Worker | 1 | 512 MB | 0.5 | 256 MB |
| Deletes Worker | 1 | 512 MB | 0.5 | 256 MB |
| Databases Worker | 1 | 512 MB | 0.5 | 256 MB |
| Builds Worker | 1 | 512 MB | 0.5 | 256 MB |
| Certificates Worker | 1 | 512 MB | 0.5 | 256 MB |
| Mails Worker | 1 | 512 MB | 0.5 | 256 MB |
| Migrations Worker | 1 | 512 MB | 0.5 | 256 MB |
| Realtime | 2 | 1 GB | 1 | 512 MB |
| MariaDB | 2 | 2 GB | 1 | 1 GB |
| Redis | 1 | 512 MB | 0.5 | 256 MB |

**Total Maximum (all services):** ~22 GB RAM, ~22 CPU cores

**Benefits:**
- Prevents one process from impacting others
- Protects against memory leaks
- Ensures fair resource distribution
- Enables predictable performance

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/v1/health"]
  interval: 30s          # Check every 30 seconds
  timeout: 10s           # Wait max 10 seconds for response
  retries: 5             # Restart after 5 failed checks
  start_period: 40s      # Wait 40s before first check
```

**Automatic Recovery:**
- Failed health checks trigger container restart
- Orchestration ensures service availability
- Logs help identify intermittent issues

---

## Credentials Management

### Default Credentials (Change After Deployment)

**Database:**
```
Username: wizardsofts
Password: W1z4rdS0fts!2025
```

**Console Admin:**
```
Email: admin@wizardsofts.com
Password: Set during first signup
```

### Credential Security Practices

1. **Store .env.appwrite Securely**
   ```bash
   chmod 600 .env.appwrite
   chown root:root .env.appwrite
   ```

2. **Rotate Credentials Regularly**
   - Database password: Every 90 days
   - API keys: Every 6 months
   - Console credentials: As needed

3. **Use Strong Passwords**
   ```bash
   # Generate 24-character password
   openssl rand -base64 24

   # Generate 32-byte hex key
   openssl rand -hex 32
   ```

4. **Secret Management**
   - Don't commit credentials to Git
   - Use environment variables
   - Consider Vault/Secrets Manager for production

---

## API Key Security

### Key Types

| Key | Scope | Usage | Rotation |
|-----|-------|-------|----------|
| Server Key | Limited to backend | Backend API calls | 6 months |
| Admin Key | All scopes | Admin operations only | 1 year |
| Client Key | Mobile-safe scopes | Mobile app SDK | 6 months |

### Creating Secure API Keys

```bash
# Generate in Appwrite Console
Project Settings → API Keys → Create Key

# Use minimal required scopes
- Messaging: messaging.messages.write, messaging.subscribers.write
- Auth: account.*, users.* (if needed)
- Database: databases.*, collections.* (if needed)
```

### Key Rotation Process

1. Generate new key with same scopes
2. Update application configuration
3. Deploy with new key
4. Monitor logs for successful authentication
5. Deactivate old key after 24 hours
6. Delete old key after 7 days

---

## Logging & Monitoring

### Application Logs

```bash
# View main Appwrite logs
docker logs appwrite -f --tail 100

# View messaging worker logs (critical for push notifications)
docker logs appwrite-worker-messaging -f --tail 100

# View all service logs
docker compose -f docker-compose.appwrite.yml logs -f
```

### Database Slow Query Logs

```bash
# Queries taking >2 seconds are logged
docker exec appwrite-mariadb tail -f /var/log/mysql/slow.log

# Parse slow logs
docker exec appwrite-mariadb mysqldumpslow /var/log/mysql/slow.log
```

### System Resource Monitoring

```bash
# Real-time resource usage
docker stats appwrite appwrite-mariadb appwrite-redis

# Detailed metrics
docker inspect appwrite --format='{{json .State}}'
```

### Health Checks

```bash
# Full system health
curl -s https://appwrite.wizardsofts.com/v1/health | jq

# Queue health
curl -s https://appwrite.wizardsofts.com/v1/health/queue | jq

# Storage health
curl -s https://appwrite.wizardsofts.com/v1/health/storage | jq

# Cache health
curl -s https://appwrite.wizardsofts.com/v1/health/cache | jq

# Database health
curl -s https://appwrite.wizardsofts.com/v1/health/db | jq
```

---

## Backup & Disaster Recovery

### Automated Daily Backups

```bash
# Runs daily at 02:00 UTC
/opt/wizardsofts-megabuild/scripts/appwrite-backup.sh

# Creates backup directory with timestamp
/opt/backups/appwrite/YYYYMMDD_HHMMSS/
├── appwrite_db.sql.gz          # Database dump (compressed)
├── appwrite-uploads.tar.gz     # User uploaded files
├── appwrite-config.tar.gz      # Configuration
├── appwrite-certificates.tar.gz # SSL certificates
├── appwrite-functions.tar.gz    # User functions
└── manifest.json               # Backup metadata
```

### Setup Cron Job

```bash
# Add to crontab
0 2 * * * /opt/wizardsofts-megabuild/scripts/appwrite-backup.sh >> /var/log/appwrite-backup.log 2>&1

# Verify
crontab -l | grep appwrite-backup
```

### Restore from Backup

```bash
# Set backup directory
BACKUP_DIR=/opt/backups/appwrite/20251227_020000

# Stop services
docker compose -f docker-compose.appwrite.yml down

# Restore database
docker run --rm \
  --network wizardsofts-megabuild_appwrite \
  -v $BACKUP_DIR:/backup \
  mariadb:10.11 \
  mysql -h appwrite-mariadb -u root -p'ROOT_PASSWORD' < /backup/appwrite_db.sql

# Restore volumes
docker run --rm \
  -v appwrite-uploads:/data \
  -v $BACKUP_DIR:/backup \
  alpine sh -c "cd /data && tar xzf /backup/appwrite-uploads.tar.gz --strip 1"

# Start services
docker compose -f docker-compose.appwrite.yml up -d
```

---

## Compliance & Auditing

### Data Protection

- **Encryption at Rest:** MariaDB data encrypted with InnoDB encryption
- **Encryption in Transit:** TLS 1.2+ enforced by Traefik
- **User Data:** Stored in isolated containers with volume encryption

### Audit Logging

```bash
# View audit logs in Appwrite console
Project Settings → Audit Logs

# Includes:
- User authentication events
- API key creation/deletion
- Database modifications
- Permission changes
- Admin actions
```

### Compliance Checklist

- [x] Non-root container execution
- [x] Capability dropping
- [x] Network segmentation
- [x] TLS/SSL encryption
- [x] CORS restrictions
- [x] Security headers
- [x] Rate limiting
- [x] Database user separation
- [x] Query logging
- [x] Resource limits
- [x] Health checks
- [x] Backup & recovery
- [x] Audit logging

---

## Security Testing

### Verify Non-Root Execution

```bash
docker inspect appwrite --format='{{.Config.User}}'
# Should output: www-data or blank (means inherited from image)

docker exec appwrite id
# Should output: uid=33(www-data) gid=33(www-data)
```

### Verify Capability Dropping

```bash
docker inspect appwrite --format='{{json .HostConfig.CapAdd}}'
docker inspect appwrite --format='{{json .HostConfig.CapDrop}}'
```

### Verify Security Options

```bash
docker inspect appwrite --format='{{json .HostConfig.SecurityOpt}}'
# Should output: ["no-new-privileges:true"]
```

### Test CORS Enforcement

```bash
# Should succeed (same origin)
curl -H "Origin: https://bondwala.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-Custom-Header" \
  -X OPTIONS \
  https://appwrite.bondwala.com/v1

# Should fail (unauthorized origin)
curl -H "Origin: https://unauthorized.com" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://appwrite.bondwala.com/v1
```

### Test Rate Limiting

```bash
# Send 100 requests in rapid succession
for i in {1..100}; do
  curl -s https://appwrite.wizardsofts.com/v1/health -o /dev/null
done

# Should return 429 (Too Many Requests) after 60 requests/minute
```

### Test SSL/TLS

```bash
# Check certificate details
openssl s_client -connect appwrite.wizardsofts.com:443 -showcerts

# Verify certificate chain
openssl s_client -connect appwrite.wizardsofts.com:443 -showcerts < /dev/null | \
  openssl x509 -noout -text | grep -E "(Subject|Issuer|Not Before|Not After)"
```

---

## Incident Response

### Service Down

```bash
# 1. Check container status
docker ps --filter "name=appwrite"

# 2. View logs
docker logs appwrite -f --tail 50

# 3. Check health
curl https://appwrite.wizardsofts.com/v1/health

# 4. Restart service
docker compose -f docker-compose.appwrite.yml restart appwrite

# 5. Monitor recovery
docker logs appwrite -f
```

### Performance Degradation

```bash
# 1. Check resource usage
docker stats appwrite appwrite-mariadb appwrite-redis

# 2. Check slow queries
docker exec appwrite-mariadb tail -f /var/log/mysql/slow.log

# 3. Check queue depth
docker exec appwrite-redis redis-cli LLEN messages

# 4. Scale messaging worker if needed
docker compose -f docker-compose.appwrite.yml up -d --scale appwrite-worker-messaging=2
```

### Security Incident

```bash
# 1. Isolate the service
docker network disconnect gibd-network appwrite

# 2. Collect logs and evidence
docker logs appwrite > /tmp/appwrite-incident.log
docker exec appwrite-mariadb mysqldump -u root -p'PASSWORD' --all-databases > /tmp/appwrite-db.sql

# 3. Review audit logs
# Check Project Settings → Audit Logs in console

# 4. Restore from clean backup if compromised
# See Backup & Disaster Recovery section

# 5. Rotate all credentials
# Change database password
# Revoke all API keys
# Create new API keys
```

---

## References

- [Appwrite Security Best Practices](https://appwrite.io/docs/security)
- [Docker Security Documentation](https://docs.docker.com/engine/security/)
- [OWASP Application Security](https://owasp.org/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

## Support & Escalation

**Regular Maintenance:**
- Weekly: Review logs for errors
- Monthly: Check slow query logs
- Quarterly: Rotate credentials
- Annually: Security audit

**Emergency Contact:**
- Tech Lead: tech@wizardsofts.com
- System Admin: admin@wizardsofts.com

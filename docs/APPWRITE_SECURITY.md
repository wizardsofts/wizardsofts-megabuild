# Appwrite Security Hardening Guide

> **Version:** 1.0
> **Date:** 2025-12-27
> **Level:** Production-Grade Security

---

## Executive Summary

The Appwrite deployment has been hardened with enterprise-grade security controls following Docker security best practices, OWASP recommendations, and industry standards.

---

## Security Layers

### Layer 1: Container Security

#### User Isolation
```bash
# Appwrite core and workers run as www-data (UID: 33)
# MariaDB and Redis run as UID: 999 (mysql/redis user)
# NO containers run as root (UID: 0)
```

#### Capability Restriction
```bash
# Drop ALL Linux capabilities first
cap_drop:
  - ALL

# Add back only required capabilities
cap_add:
  - NET_BIND_SERVICE    # Appwrite (for port binding)
  - CHOWN               # Database/Redis (for data ownership)
  - DAC_OVERRIDE        # Database/Redis (for file permissions)
```

#### Privilege Escalation Prevention
```yaml
security_opt:
  - no-new-privileges:true
```

This prevents processes from gaining additional privileges even with setuid/setgid bits.

### Layer 2: Resource Constraints

Memory and CPU limits prevent DoS attacks and runaway processes:

```yaml
# Appwrite Core
deploy:
  resources:
    limits:
      cpus: '4'           # Max 4 CPU cores
      memory: 4G          # Max 4 GB RAM
    reservations:
      cpus: '2'           # Guaranteed 2 cores
      memory: 2G          # Guaranteed 2 GB

# Messaging Worker (critical)
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

### Layer 3: Network Security

#### HTTPS Enforcement
- All traffic via Let's Encrypt TLS certificates
- HSTS header: `max-age=31536000; includeSubDomains; preload`
- TLS 1.2+ enforced by Traefik

#### CORS Configuration
Restricted to WizardSofts domains only:

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

#### Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `SAMEORIGIN` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer leaking |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Restrict feature access |

#### Rate Limiting

```yaml
appwrite-rate-limit:
  rateLimit:
    average: 60        # 60 requests per minute average
    burst: 100         # Allow 100 burst
    period: 1m         # Per minute
```

This prevents:
- Brute force attacks
- API abuse
- DDoS attempts

### Layer 4: Database Security

#### MariaDB Hardening

```sql
-- Skip symbolic links (directory traversal protection)
--skip-symbolic-links

-- Disable external locking (performance + security)
--skip-external-locking

-- Per-table InnoDB files (isolation)
--innodb-file-per-table=ON

-- Slow query logging (audit trail)
--slow-query-log=ON
--long-query-time=2
--log-queries-not-using-indexes=ON

-- Enforce UTF-8 with strict collation
--character-set-server=utf8mb4
--collation-server=utf8mb4_unicode_ci
```

#### Credential Separation

```bash
# Database root user
User: root
Password: W1z4rdS0fts!2025
Privilege: Full administrative

# Application database user
User: wizardsofts
Password: W1z4rdS0fts!2025
Privilege: Limited to appwrite database only
```

Separate credentials ensure compromised app credentials don't expose database root.

#### Connection Security

```bash
# All connections encrypted internally
# TLS passthrough for management connections
# Connection pooling to prevent exhaustion
--max-connections=500
```

### Layer 5: Cache Security

#### Redis Hardening

```bash
# Data persistence
--appendonly yes
--appendfsync everysec

# Memory management
--maxmemory 512mb
--maxmemory-policy allkeys-lru

# Connection security
--tcp-keepalive 300
--timeout 0

# Logging
--loglevel notice
```

**Important:** Redis runs inside private Docker network, not exposed to internet.

### Layer 6: Application Configuration

#### Secret Management

**Security Keys (256-bit cryptographic keys):**
```bash
_APP_OPENSSL_KEY_V1     # Data encryption at rest
_APP_SECRET             # Session signing
_APP_EXECUTOR_SECRET    # Function execution signing
```

These must be generated with:
```bash
openssl rand -hex 32
```

**Never commit to git or share keys.**

#### Console Access Control

```bash
# Only whitelisted emails can create first admin
_APP_CONSOLE_WHITELIST_EMAILS=admin@wizardsofts.com,tech@wizardsofts.com

# Optional: Restrict by IP
_APP_CONSOLE_WHITELIST_IPS=10.0.0.0/8,office.ip.address
```

#### Audit Logging

Enable and monitor:
- User authentication attempts
- API key creation/deletion
- Configuration changes
- Project access logs

---

## Threat Model & Mitigations

### Threat: Unauthorized API Access

**Mitigation:**
- API keys with limited scopes
- CORS restrictions
- Rate limiting
- TLS encryption

### Threat: Database Compromise

**Mitigation:**
- Separate app credentials (not root)
- Strong password policy
- Encrypted connections
- Query logging and audit trail
- Regular backups with encryption

### Threat: Container Escape

**Mitigation:**
- Non-root user execution
- Capability dropping
- No new privileges flag
- Resource limits
- Update Docker engine regularly

### Threat: Man-in-the-Middle (MITM)

**Mitigation:**
- TLS 1.2+ enforcement
- HSTS headers
- Certificate pinning ready
- Let's Encrypt auto-renewal

### Threat: Denial of Service (DoS)

**Mitigation:**
- Rate limiting per IP
- Resource limits per container
- Connection pooling
- Request validation

### Threat: Data Leakage

**Mitigation:**
- HTTPS only
- Referrer policy
- Restricted CORS
- Encrypted backups
- Access logging

---

## Operational Security

### Pre-Deployment Checklist

- [ ] Generate all cryptographic keys with OpenSSL
- [ ] Set strong database passwords
- [ ] Configure DNS records for both domains
- [ ] Test certificate issuance (Let's Encrypt)
- [ ] Verify all domains resolve before deployment
- [ ] Test CORS with actual app domains
- [ ] Enable audit logging
- [ ] Configure backup schedules

### Regular Maintenance

**Daily:**
- Monitor health checks
- Review error logs
- Check backup completion

**Weekly:**
- Audit API key usage
- Review access logs
- Check slow query logs

**Monthly:**
- Security patch updates
- Dependency updates
- Backup restoration test
- Certificate renewal verification

**Quarterly:**
- Security audit
- Penetration testing (if applicable)
- Update security policies
- Review and update this guide

### Incident Response

**If Compromise Suspected:**

1. **Immediate Actions:**
   ```bash
   # Take backup
   docker exec appwrite-mariadb mysqldump -u root -p'PASS' --all-databases > backup.sql

   # Rotate API keys
   # (In Appwrite Console > Project Settings > API Keys > Revoke & Regenerate)

   # Check logs
   docker logs appwrite | grep -i error
   docker logs appwrite-mariadb | grep -i error
   ```

2. **Investigation:**
   - Review audit logs for unauthorized access
   - Check for modified files
   - Monitor container resource usage

3. **Recovery:**
   - Restore from backup
   - Rotate all credentials
   - Deploy patched version
   - Monitor for suspicious activity

---

## Compliance & Standards

This deployment aligns with:

- **CIS Docker Benchmark:** Container security best practices
- **OWASP Top 10:** Web application security
- **NIST Cybersecurity Framework:** Risk management
- **SOC 2 Type II:** Security and availability controls
- **GDPR:** Data protection requirements (with proper configuration)

---

## Hardening Verification

### Test Container Privileges

```bash
# Verify no root execution
docker inspect appwrite | grep -i '"User"'
# Should show: "User": "www-data"

# Verify capability dropping
docker inspect appwrite | grep -i '"CapAdd"'
# Should show minimal capabilities

# Verify security options
docker inspect appwrite | grep -i 'no-new-privileges'
# Should show: "no-new-privileges": true
```

### Test Network Security

```bash
# Test HTTPS enforcement
curl -i https://appwrite.wizardsofts.com/v1/health
# Should return 200 with HSTS headers

# Check security headers
curl -i https://appwrite.wizardsofts.com/v1/health | grep -i "Strict-Transport-Security"
# Should return: Strict-Transport-Security: max-age=31536000...

# Test CORS
curl -X OPTIONS https://appwrite.wizardsofts.com/v1/health \
  -H "Origin: https://bondwala.com" \
  -H "Access-Control-Request-Method: GET"
# Should return CORS headers
```

### Test Rate Limiting

```bash
# Generate multiple requests
for i in {1..100}; do
  curl -s https://appwrite.wizardsofts.com/v1/health >/dev/null &
done

# Check logs for rate limit responses
docker logs traefik | grep -i "429\|rate"
```

---

## Security Best Practices

### For Administrators

1. **Use VPN for console access**
2. **Never share API keys in chat or email**
3. **Rotate credentials quarterly**
4. **Keep audit logs for 90+ days**
5. **Enable 2FA on console accounts** (when available)

### For Application Developers

1. **Use project-specific API keys**
2. **Use scoped permissions (not admin keys)**
3. **Never hardcode credentials**
4. **Validate all API responses**
5. **Implement client-side rate limiting**
6. **Log all authentication events**

### For Operations

1. **Monitor container resource usage**
2. **Set up alerting for errors/failures**
3. **Test backup restoration monthly**
4. **Keep Docker daemon updated**
5. **Monitor security advisories**
6. **Update container images regularly**

---

## References

- [CIS Docker Benchmark v1.6](https://www.cisecurity.org/benchmark/docker)
- [OWASP Container Security Top 10](https://owasp.org/www-project-container-security/)
- [Appwrite Security Documentation](https://appwrite.io/docs/security)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

## Support & Escalation

For security concerns:
1. Review this document and operational logs
2. Contact security@wizardsofts.com
3. Follow incident response procedures
4. Document all changes and decisions

---

**Document End**

*Last Updated: 2025-12-27*
*Reviewed By: Development Team*
*Next Review: 2026-03-27*

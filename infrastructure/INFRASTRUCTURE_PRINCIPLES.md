# Infrastructure Deployment Principles

This document captures key principles and patterns learned from production deployments to guide future infrastructure work.

---

## Docker and Containerization

### Principle 1: Know Your Docker Installation Method

**Problem**: Docker Snap has different security restrictions than Docker from apt/yum

**Guideline**:
- Check installation method: `which docker` and `snap list docker`
- Docker Snap: Use `~/` for bind mounts, avoid `/opt`, `/root`, `/var`
- Docker apt/yum: More flexible mount paths
- When blocked by AppArmor: Check `/var/log/syslog` for denials

**Example**:
```yaml
# ✅ Works with Docker Snap
volumes:
  - ~/configs/app.conf:/etc/app/app.conf:ro

# ❌ Fails with Docker Snap
volumes:
  - /opt/configs/app.conf:/etc/app/app.conf:ro
```

---

### Principle 2: Named Volumes for Data, Bind Mounts for Config

**Problem**: Data needs persistence, configs need version control

**Guideline**:
- Data (databases, uploads, logs): Use named volumes
- Configs (app.conf, etc.): Use bind mounts from version control
- Named volumes survive container recreation
- Bind mounts allow config changes without rebuilding

**Example**:
```yaml
volumes:
  - app-data:/var/lib/app          # Named volume - data
  - ~/configs/app.conf:/etc/app/app.conf:ro  # Bind mount - config
```

---

### Principle 3: Multi-Network Containers Are Common

**Problem**: Services need to talk to different groups of containers

**Guideline**:
- One network per logical grouping (monitoring, backend, frontend)
- Connect containers to multiple networks when needed
- DNS only works within same network
- Runtime `docker network connect` is non-destructive

**Example**:
```yaml
grafana:
  networks:
    - monitoring     # Can talk to Prometheus, Loki
    - backend        # Can talk to Keycloak, databases
```

---

## Configuration Management

### Principle 4: Check Breaking Changes in Major Versions

**Problem**: Major version updates often remove deprecated features

**Guideline**:
- Always read release notes for major versions
- Test in staging before production
- Search deprecation warnings in current version logs
- Plan migration path for removed features

**Example**:
- Grafana 12.0: Legacy alerting removed → must use unified alerting
- PostgreSQL 14: Removed `wal_keep_segments` → use `wal_keep_size`

---

### Principle 5: External vs Internal URLs

**Problem**: OAuth redirects go through browser, API calls go server-to-server

**Guideline**:
- Browser-facing URLs: Use public IP/domain
- Server-to-server URLs: Use container names
- Document which is which in configs
- Test both paths

**Example**:
```ini
# Browser redirect (external)
auth_url = http://10.0.0.84:8180/auth

# Server API call (internal)
token_url = http://keycloak:8080/auth
```

---

## Troubleshooting

### Principle 6: Logs First, Assumptions Second

**Problem**: Fixing based on assumptions wastes time

**Guideline**:
1. Check container logs: `docker logs <container> --tail 50`
2. Check system logs: `journalctl -xe` or `/var/log/syslog`
3. Check application logs inside container
4. Look for exact error messages
5. Search for error message + version number

**Example**:
```bash
# Don't assume the issue
# ❌ "Container won't start, must be networking"

# Check logs first
# ✅ docker logs grafana --tail 50
# Found: "invalid setting [alerting].enabled"
```

---

### Principle 7: Test Connectivity at Each Layer

**Problem**: "Container can't connect" is too vague

**Guideline**:
1. Network layer: `docker exec <container> ping <target>`
2. DNS layer: `docker exec <container> nslookup <target>`
3. Port layer: `docker exec <container> nc -zv <target> <port>`
4. HTTP layer: `docker exec <container> curl http://<target>:<port>`
5. Application layer: Check app-specific endpoints

---

### Principle 8: Validate After Every Change

**Problem**: Multiple changes make it hard to identify what fixed/broke things

**Guideline**:
- Make one change at a time
- Validate after each change
- Use automated validation scripts
- Document what worked

**Example**:
```bash
# Change config
vim ~/grafana-config/grafana.ini

# Restart
docker restart grafana

# Validate immediately
bash monitoring/validate-grafana.sh

# If broken, you know exactly what changed
```

---

## Security

### Principle 9: Change Default Credentials Immediately

**Problem**: Default credentials are public knowledge

**Guideline**:
- Change defaults before production deployment
- Use environment variables or secrets management
- Document where credentials are stored
- Rotate regularly

**Example**:
```bash
# Development: OK
admin / admin

# Production: Required
admin / <strong-random-password>
# Store in vault/secrets manager
```

---

### Principle 10: Principle of Least Privilege

**Problem**: Over-permissive access increases blast radius

**Guideline**:
- Run containers as non-root user when possible
- Use `security_opt: no-new-privileges:true`
- Limit network exposure (localhost-only where possible)
- Use firewall rules (UFW, iptables)
- Grant minimum required permissions

**Example**:
```yaml
grafana:
  user: "472:472"  # grafana user
  security_opt:
    - no-new-privileges:true
  ports:
    - "127.0.0.1:3002:3000"  # localhost-only
```

---

## Deployment

### Principle 11: Infrastructure as Code

**Problem**: Manual changes aren't reproducible or auditable

**Guideline**:
- All configs in version control
- Use docker-compose.yml for orchestration
- Document deployment steps in README/DEPLOYMENT_GUIDE
- Script common operations
- Keep deployment scripts idempotent

---

### Principle 12: Observability from Day One

**Problem**: Can't fix what you can't see

**Guideline**:
- Add health checks to all containers
- Configure logging before deployment
- Set up monitoring dashboards early
- Create validation scripts
- Document normal vs abnormal states

**Example**:
```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "http://localhost:3000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

### Principle 13: Fail Fast and Loud

**Problem**: Silent failures lead to data loss or security issues

**Guideline**:
- Don't ignore errors in startup scripts
- Use `set -e` in bash scripts
- Exit with non-zero on validation failures
- Alert on health check failures
- Log all errors with context

**Example**:
```bash
#!/bin/bash
set -e  # Exit on any error
set -o pipefail  # Exit if any command in pipe fails

# Validate critical files exist
[ -f ~/grafana-config/grafana.ini ] || {
  echo "ERROR: grafana.ini not found"
  exit 1
}
```

---

### Principle 14: Document as You Go

**Problem**: Future you won't remember why you did something

**Guideline**:
- Write README for each component
- Comment complex config sections
- Create retrospectives after incidents
- Update docs when you fix issues
- Include "why" not just "what"

---

## Provisioning and Automation

### Principle 15: Provision Infrastructure, Not Just Containers

**Problem**: Application works but can't connect to dependencies

**Guideline**:
- Provision networks before containers
- Create volumes before mounting
- Ensure DNS resolution works
- Check network policies/firewalls
- Verify connectivity before deploying app

---

### Principle 16: Idempotent Operations

**Problem**: Re-running scripts breaks things or duplicates resources

**Guideline**:
- Check if resource exists before creating
- Use `docker network connect` (safe to re-run)
- Use `||true` or check exit codes
- Document safe vs unsafe operations

**Example**:
```bash
# ❌ Not idempotent
docker network create my-network

# ✅ Idempotent
docker network create my-network 2>/dev/null || true

# ✅ Even better
docker network inspect my-network >/dev/null 2>&1 || \
  docker network create my-network
```

---

## Patterns and Anti-Patterns

### ✅ DO:
- Use health checks
- Log to stdout/stderr (Docker captures)
- Use named volumes for persistence
- Test in staging first
- Document deployment steps
- Version control all configs
- Use environment variables for secrets
- Create validation scripts
- Multi-network when needed
- Read release notes for major updates

### ❌ DON'T:
- Hardcode secrets in configs
- Use `:latest` tag in production
- Skip health checks
- Deploy without backups
- Make multiple changes without validation
- Assume error messages
- Use bind mounts from system directories (with Docker Snap)
- Keep deprecated configs "just in case"
- Deploy without testing connectivity
- Ignore deprecation warnings

---

## Incident Response

### When Things Break:

1. **Stabilize**: Get system to known-good state
2. **Investigate**: Collect logs, check configs
3. **Fix**: Make minimal change to resolve
4. **Validate**: Run tests to confirm fix
5. **Document**: Write retrospective
6. **Prevent**: Update validation scripts, add monitoring

### After Resolution:

- Write retrospective (what, why, how, prevention)
- Update deployment docs
- Add validation for the failure mode
- Share learnings with team
- Update infrastructure principles

---

## Version-Specific Learnings

### Grafana 12.x
- Legacy alerting removed → use unified alerting only
- Panel datasources must be explicit
- Provisioning paths must be absolute
- OAuth callback URLs must be exact

### Docker Snap
- Mount from `~/` not `/opt` or `/root`
- Check AppArmor logs for denials
- Named volumes work normally
- Consider using Docker from apt instead

### Keycloak
- Master realm for admin operations
- Separate realms for applications
- Client secrets should be generated, not guessed
- Redirect URIs must include all paths

---

## References

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Grafana Retrospective](../GRAFANA_DEPLOYMENT_RETROSPECTIVE.md)

---

*Principles compiled from production incidents and deployments*
*Last Updated: 2025-12-30*

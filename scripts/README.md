# Deployment and Validation Scripts

This directory contains scripts for validating configurations, deploying services, and verifying deployments.

## Scripts Overview

### 1. validate-config.sh

**Purpose**: Validates YAML files, Docker configurations, and Traefik setup before deployment.

**Usage**:

```bash
# Normal mode (warnings don't fail)
./scripts/validate-config.sh

# Strict mode (warnings cause failure)
./scripts/validate-config.sh --strict
```

**What it checks**:

- ✅ YAML syntax validation (all .yml and .yaml files)
- ✅ Docker Compose configuration validation
- ✅ Traefik configuration completeness
- ✅ Environment variable placeholders
- ✅ Network configuration
- ✅ ACME email configuration
- ✅ Required sections presence

**CI/CD Integration**:

```yaml
validate:
  stage: test
  script:
    - chmod +x scripts/validate-config.sh
    - ./scripts/validate-config.sh --strict
  only:
    - merge_requests
    - master
```

---

### 2. pre-deploy.sh

**Purpose**: Creates backups and prepares the server environment before deployment.

**Usage**:

```bash
# Prepare for deployment of all services
./scripts/pre-deploy.sh 10.0.0.84

# Prepare for specific service deployment
./scripts/pre-deploy.sh 10.0.0.84 ws-wizardsofts-web
```

**What it does**:

- ✅ Creates timestamped backups of Traefik configuration
- ✅ Backs up Docker Compose files
- ✅ Checks disk space availability
- ✅ Verifies Docker daemon is accessible
- ✅ Lists running containers
- ✅ Creates deployment snapshot
- ✅ Optional: Cleans up unused Docker resources

**Backups Created**:

- `traefik.yml.backup.YYYYMMDD_HHMMSS`
- `docker-compose.yml.backup.YYYYMMDD_HHMMSS`
- Deployment snapshots in `/home/wizardsofts/deployment-snapshots/`

**Retention**: Keeps last 10 backups per file, last 20 deployment snapshots

**CI/CD Integration**:

```yaml
pre-deploy:
  stage: pre-deploy
  script:
    - chmod +x scripts/pre-deploy.sh
    - ./scripts/pre-deploy.sh $DEPLOY_SERVER all
  only:
    - master
```

---

### 3. verify-deployment.sh

**Purpose**: Verifies that deployed services are healthy and HTTPS certificates are working.

**Usage**:

```bash
# Full verification including HTTPS
./scripts/verify-deployment.sh 10.0.0.84

# Skip HTTPS checks (for staging/dev)
./scripts/verify-deployment.sh 10.0.0.84 --skip-https
```

**What it checks**:

- ✅ Server connectivity (ping)
- ✅ Docker service health status
- ✅ HTTP endpoint accessibility (direct ports)
- ✅ Traefik routing (HTTP to HTTPS redirect)
- ✅ HTTPS certificate validity
- ✅ Certificate expiration dates
- ✅ Certificate issuer (Let's Encrypt vs self-signed)
- ✅ HTTPS endpoint responsiveness

**Verified Services**:

- Traefik
- ws-wizardsofts-web (www.wizardsofts.com)
- pf-padmafoods-web (www.mypadmafoods.com)
- gibd-quant-web (www.guardianinvestmentbd.com)

**CI/CD Integration**:

```yaml
verify:
  stage: verify
  script:
    - chmod +x scripts/verify-deployment.sh
    - ./scripts/verify-deployment.sh $DEPLOY_SERVER --skip-https
  after_script:
    - echo "Manual HTTPS verification required"
  only:
    - master
```

---

## CI/CD Pipeline Integration

### Complete Pipeline Example

```yaml
# .gitlab-ci.yml

stages:
  - test
  - build
  - pre-deploy
  - deploy
  - verify

variables:
  DEPLOY_SERVER: "10.0.0.84"

# Stage 1: Validate configurations
validate-config:
  stage: test
  script:
    - chmod +x scripts/validate-config.sh
    - ./scripts/validate-config.sh --strict
  only:
    - merge_requests
    - master

# Stage 2: Build (existing)
build:
  stage: build
  script:
    -  # Your build steps here
  only:
    - master

# Stage 3: Pre-deployment preparation
prepare-deployment:
  stage: pre-deploy
  script:
    - chmod +x scripts/pre-deploy.sh
    - ./scripts/pre-deploy.sh $DEPLOY_SERVER all
  environment:
    name: production
  only:
    - master
  when: manual # Require manual approval

# Stage 4: Deploy (existing)
deploy:
  stage: deploy
  script:
    -  # Your deployment steps here
  environment:
    name: production
  only:
    - master

# Stage 5: Verify deployment
verify-deployment:
  stage: verify
  script:
    - chmod +x scripts/verify-deployment.sh
    - ./scripts/verify-deployment.sh $DEPLOY_SERVER --skip-https
  after_script:
    - |
      echo "============================================"
      echo "IMPORTANT: Manual HTTPS Verification Required"
      echo "============================================"
      echo ""
      echo "Run the following commands to verify HTTPS:"
      echo ""
      echo "openssl s_client -connect www.wizardsofts.com:443 -servername www.wizardsofts.com 2>/dev/null | openssl x509 -noout -dates"
      echo "curl -I https://www.wizardsofts.com"
      echo "curl -I https://www.mypadmafoods.com"
      echo "curl -I https://www.guardianinvestmentbd.com"
      echo ""
      echo "See AGENT_GUIDELINES.md for full HTTPS verification steps"
  environment:
    name: production
  only:
    - master
```

---

## Workflow

### 1. Development

```bash
# Before committing changes
./scripts/validate-config.sh

# If changes to Traefik or Docker Compose
./scripts/validate-config.sh --strict
```

### 2. Pre-Deployment

```bash
# SSH to your local machine (where you can SSH to server)
./scripts/pre-deploy.sh 10.0.0.84 all

# This creates backups and prepares the environment
```

### 3. Deployment

```bash
# Use GitLab CI/CD pipeline
# Trigger deployment from GitLab UI
```

### 4. Post-Deployment Verification

```bash
# Automated verification
./scripts/verify-deployment.sh 10.0.0.84

# Manual HTTPS verification (always required)
openssl s_client -connect www.wizardsofts.com:443 -servername www.wizardsofts.com 2>/dev/null | openssl x509 -noout -dates
curl -I https://www.wizardsofts.com
```

---

## Emergency Recovery

If deployment fails, use backups created by pre-deploy.sh:

```bash
# SSH to server
ssh wizardsofts@10.0.0.84

# List backups
ls -la /home/wizardsofts/traefik/traefik.yml.backup.*

# Restore latest backup
cd /home/wizardsofts/traefik
cp traefik.yml.backup.YYYYMMDD_HHMMSS traefik.yml
docker-compose restart traefik

# Verify recovery
docker ps | grep traefik
docker exec traefik traefik healthcheck
```

---

## Prerequisites

### Required Tools

- **bash** (version 4+)
- **ssh** with key-based authentication
- **curl**
- **openssl**
- **docker** and **docker-compose** (for validation)
- **python3** with PyYAML (for YAML validation)

### Install Python YAML library

```bash
# On Ubuntu/Debian
sudo apt-get install python3-yaml

# On macOS
pip3 install pyyaml

# Or using system package
brew install python3
```

### SSH Configuration

Ensure SSH key-based authentication is set up:

```bash
ssh-copy-id wizardsofts@10.0.0.84
```

---

## Environment Variables

Scripts can use the following environment variables:

- `DEPLOY_SERVER` - Target deployment server IP
- `SSH_USER` - SSH username (default: wizardsofts)
- `SKIP_HTTPS_CHECK` - Set to "true" to skip HTTPS verification

---

## Troubleshooting

### validate-config.sh fails

```
Error: YAML syntax invalid
```

**Solution**: Check the file mentioned in the error for syntax issues. Use a YAML validator or Python:

```bash
python3 -c "import yaml; yaml.safe_load(open('file.yml'))"
```

### pre-deploy.sh SSH connection fails

```
Error: Cannot connect to server via SSH
```

**Solution**:

1. Verify SSH key is added: `ssh-add -l`
2. Test SSH manually: `ssh wizardsofts@10.0.0.84`
3. Check SSH config: `~/.ssh/config`

### verify-deployment.sh HTTPS checks fail

```
Error: Could not retrieve certificate
```

**Solution**:

1. Check DNS resolution: `nslookup www.wizardsofts.com`
2. Verify domain points to correct server
3. Check Traefik logs: `docker logs traefik | grep -i certificate`
4. For dev/staging servers, use `--skip-https` flag

---

## Related Documentation

- [AGENT_GUIDELINES.md](../AGENT_GUIDELINES.md) - Deployment procedures and HTTPS verification
- [HTTPS_INCIDENT_RETROSPECTIVE.md](../HTTPS_INCIDENT_RETROSPECTIVE.md) - Lessons learned from HTTPS incident
- [CONSTITUTION.md](../CONSTITUTION.md) - Project standards and security rules

---

## Script Permissions

Make scripts executable:

```bash
chmod +x scripts/validate-config.sh
chmod +x scripts/pre-deploy.sh
chmod +x scripts/verify-deployment.sh
```

Or use the helper:

```bash
chmod +x scripts/*.sh
```

---

## Infrastructure Validation & Setup Scripts

### 4. validate-service-infrastructure.sh

**Purpose**: Ground truth verification for service infrastructure. Validates actual system state vs documentation assumptions.

**Usage**:

```bash
# Basic validation
./scripts/validate-service-infrastructure.sh gitlab 10.0.0.84

# Strict mode (fail on any error)
./scripts/validate-service-infrastructure.sh keycloak 10.0.0.84 --strict

# Generate report file
./scripts/validate-service-infrastructure.sh nexus 10.0.0.84 --report /tmp/nexus-validation.txt

# Skip external connectivity and logs
./scripts/validate-service-infrastructure.sh gitlab 10.0.0.84 --skip-external --skip-logs
```

**What it checks**:

- ✅ Container status (running/stopped)
- ✅ Container health (health check status)
- ✅ Port bindings (internal and external)
- ✅ NFS mounts (presence and permissions)
- ✅ Configuration files (accessibility)
- ✅ Internal connectivity (listening ports)
- ✅ Recent logs analysis (error detection)
- ✅ External connectivity (HTTP endpoints)

**Based on**: GitLab hardening session (2026-01-08), AGENT.md Section 9.0

**When to use**:

- Before planning infrastructure changes (ground truth verification)
- After service deployment/migration
- When documentation conflicts with reality
- Regular health checks (cron job)
- Troubleshooting service issues

**CI/CD Integration**:

```yaml
validate-infrastructure:
  stage: validate
  script:
    - chmod +x scripts/validate-service-infrastructure.sh
    - ./scripts/validate-service-infrastructure.sh $SERVICE_NAME $DEPLOY_SERVER --strict
  after_script:
    - cat validation-report.txt
  artifacts:
    paths:
      - validation-report.txt
    when: always
```

---

### 5. setup-service-backups.sh

**Purpose**: Automate NFS backup configuration for services following AGENT.md Section 9.1 convention.

**Usage**:

```bash
# Auto-detect UID/GID from container
./scripts/setup-service-backups.sh gitlab 10.0.0.84 10.0.0.80

# Specify UID/GID manually
./scripts/setup-service-backups.sh keycloak 10.0.0.84 10.0.0.80 --uid 1000 --gid 1000

# Custom retention period
./scripts/setup-service-backups.sh nexus 10.0.0.84 10.0.0.80 --retention 30

# Dry run (show what would be done)
./scripts/setup-service-backups.sh gitlab 10.0.0.84 10.0.0.80 --dry-run
```

**What it does**:

- ✅ Auto-detects service UID/GID from running container
- ✅ Creates backup directory on NFS server: `/mnt/data/Backups/server/<service>/`
- ✅ Sets correct ownership (UID:GID)
- ✅ Verifies NFS export configuration
- ✅ Creates mount point on service host
- ✅ Mounts NFS share
- ✅ Adds to /etc/fstab for persistence
- ✅ Provides docker-compose configuration snippet

**Based on**: GitLab backup setup (2026-01-08), AGENT.md Section 9.1

**Standard backup path**: `/mnt/data/Backups/server/<service-name>/`

**When to use**:

- Setting up new service backups
- Migrating backup storage to NFS
- Standardizing backup infrastructure

**After running**:

1. Update `docker-compose.yml` with volume mount
2. Restart service
3. Test backup creation
4. Verify backups appear in mount point

---

### 6. test-service-integration.sh

**Purpose**: Run integration tests for service infrastructure. Validates APIs, databases, cache, monitoring, backups.

**Usage**:

```bash
# Run all tests
./scripts/test-service-integration.sh gitlab 10.0.0.84

# Generate report
./scripts/test-service-integration.sh gitlab 10.0.0.84 --report /tmp/gitlab-integration-tests.txt

# Strict mode (exit on first failure)
./scripts/test-service-integration.sh keycloak 10.0.0.84 --strict

# Skip specific tests
./scripts/test-service-integration.sh nexus 10.0.0.84 --skip backup-directory --skip cache-connection
```

**Test Suites**:

1. **Container Health Tests**

   - Container running status
   - Health check status

2. **Network Connectivity Tests**

   - Internal ports listening
   - External connectivity

3. **Database Tests**

   - Database connection
   - Query execution

4. **Cache Tests**

   - Redis/cache connection
   - Cache operations

5. **Storage Tests**

   - NFS mount accessibility
   - Write/read permissions

6. **Backup Tests**

   - Backup directory exists
   - Backup creation capability

7. **Monitoring Tests**

   - Metrics endpoint availability
   - Prometheus scraping

8. **Log Analysis Tests**
   - Recent error detection
   - Log level validation

**Based on**: GitLab integration testing (2026-01-08), AGENT.md Section 9.4

**When to use**:

- After infrastructure changes (MANDATORY before activation)
- Before production deployment
- Regular health validation (daily cron)
- After service upgrades
- Troubleshooting integration issues

**CI/CD Integration**:

```yaml
integration-tests:
  stage: test
  script:
    - chmod +x scripts/test-service-integration.sh
    - ./scripts/test-service-integration.sh $SERVICE_NAME $DEPLOY_SERVER --report integration-tests.txt
  artifacts:
    reports:
      junit: integration-tests.xml
    paths:
      - integration-tests.txt
    when: always
  only:
    - merge_requests
    - master
```

**Example Output**:

```
═══════════════════════════════════════════════════════════
  Integration Tests: gitlab @ 10.0.0.84
═══════════════════════════════════════════════════════════

[Suite 1] Container Health Tests
  ✅ PASS [container-running] Container is running
  ✅ PASS [container-health] Container health check
       Status: healthy

[Suite 2] Network Connectivity Tests
  ✅ PASS [port-listening] Service port listening
       3 port(s) listening
  ✅ PASS [external-connectivity] External connectivity
       HTTP 200 on port 8090

...

═══════════════════════════════════════════════════════════
  Test Summary
═══════════════════════════════════════════════════════════

  Total Tests:    15
  ✅ Passed:      13
  ❌ Failed:      0
  ⏭️  Skipped:     2

  Pass Rate:      87%

✅ Tests PASSED - All tests successful
```

---

## Script Maintenance Policy

**IMPORTANT**: Keep these scripts updated as infrastructure evolves.

**When to update scripts**:

- ✅ Adding new services → Add service-specific tests/validation
- ✅ Changing infrastructure patterns → Update validation logic
- ✅ Discovering new failure modes → Add corresponding checks
- ✅ Updating conventions → Align scripts with new standards
- ✅ Security improvements → Add security validation tests

**Maintenance checklist** (see AGENT.md Section 9.4.7):

1. After each infrastructure change, verify scripts still work
2. When adding new services, extend test coverage
3. Document new test patterns in script comments
4. Version control all script changes with clear commit messages
5. Test scripts in staging before using in production

**See also**: AGENT.md Section 5.2 (Script-First Policy)

---

**Last Updated**: January 8, 2026
**Maintained by**: WizardSofts DevOps Team

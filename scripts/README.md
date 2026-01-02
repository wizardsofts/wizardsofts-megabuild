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
    - # Your build steps here
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
  when: manual  # Require manual approval

# Stage 4: Deploy (existing)
deploy:
  stage: deploy
  script:
    - # Your deployment steps here
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

**Last Updated**: December 30, 2025
**Maintained by**: WizardSofts DevOps Team

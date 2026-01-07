# CI/CD Security Hardening - Complete Guide

**Date**: January 7, 2025  
**Focus**: Secure GitLab CI/CD pipeline for Traefik, Appwrite, and all services  
**Current State**: Manual deployments, no CI/CD  
**Target State**: Automated, secure, auditable deployments

---

## Executive Summary

The current deployment process is **entirely manual** with **zero CI/CD automation**. This creates:
- ❌ No audit trail
- ❌ No rollback capability
- ❌ Inconsistent deployments
- ❌ Security vulnerabilities (credentials exposed in manual scripts)
- ❌ No automated security scanning

**This document provides a complete CI/CD security hardening strategy.**

---

## 1. GitLab CI/CD Security Architecture

### Current Problems

| Issue | Impact | Severity |
|-------|--------|----------|
| Manual SSH deployments | No audit trail, no version control | 🔴 CRITICAL |
| Secrets in code/env files | Credentials exposed if repo is leaked | 🔴 CRITICAL |
| No image scanning | Vulnerable containers deployed | 🔴 CRITICAL |
| No deployment approval | Unauthorized changes possible | 🟠 HIGH |
| No rollback procedure | Can't recover from bad deployments | 🟠 HIGH |
| No test automation | Changes not validated before deployment | 🟠 HIGH |

### Proposed Solution

```
Code Push → Validation → Scan → Build → Test → Deploy → Verify
     ↓          ↓         ↓      ↓      ↓      ↓        ↓
   GitHub    Lint/SAST  Trivy  Docker Test  SSH    Healthcheck
   Commit    Validation  Scan   Build  Suite  Deploy with Backup
```

---

## 2. GitLab CI/CD Variables Setup (CRITICAL)

### 🔴 CRITICAL: Never Store Secrets in Code

**❌ WRONG (DO NOT DO THIS)**:
```yaml
# .gitlab-ci.yml
variables:
  DB_PASSWORD: "29Dec2#24"  # ❌ EXPOSED!
  API_KEY: "sk-1234567890"   # ❌ EXPOSED!
```

**✅ CORRECT (DO THIS)**:
1. Store in GitLab UI
2. Mark as Protected + Masked
3. Reference in pipeline

### How to Add Variables in GitLab UI

1. **Navigate** to: Project → Settings → CI/CD → Variables
2. **Click** "Add Variable" for each:

#### Database Secrets
```
Variable Name: DB_PASSWORD
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Environment Scope: Production
Value: [Generate with: openssl rand -base64 32]
```

```
Variable Name: KEYCLOAK_DB_PASSWORD
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Environment Scope: Production
Value: [Generate with: openssl rand -base64 32]
```

#### Deployment Credentials
```
Variable Name: SSH_PRIVATE_KEY
Type: File (not Variable!)
Protected: ✅ Yes
Masked: ❌ No (files can't be masked, but is protected)
Environment Scope: Production
Value: [Contents of ~/.ssh/id_rsa]
```

#### API Keys & Secrets
```
Variable Name: OPENAI_API_KEY
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Value: [Your OpenAI API key]
```

```
Variable Name: APPWRITE_SECRET_KEY
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Value: [Your Appwrite secret]
```

```
Variable Name: DOCKER_REGISTRY_PASSWORD
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Value: [Docker registry password]
```

### Reference in .gitlab-ci.yml

```yaml
# ✅ CORRECT - Reference from GitLab UI variables
script:
  - export DB_PASSWORD=$DB_PASSWORD
  - export SSH_PRIVATE_KEY=$SSH_PRIVATE_KEY
  - ./deploy.sh

# ❌ WRONG - Never hardcode
script:
  - export DB_PASSWORD="29Dec2#24"
  - export SSH_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----..."
```

---

## 3. Secure CI/CD Pipeline Configuration

### Complete .gitlab-ci.yml Setup

Create/update [.gitlab-ci.yml](.gitlab-ci.yml):

```yaml
# ============================================================================
# GitLab CI/CD Pipeline - Secure Deployment
# ============================================================================

stages:
  - validate      # Validate configuration
  - scan          # Security scanning
  - build         # Build Docker images
  - deploy        # Deploy to production
  - verify        # Verify deployment health

variables:
  # Non-sensitive variables (public)
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  DEPLOY_HOST: "10.0.0.84"
  DEPLOY_USER: "wizardsofts"
  DEPLOY_PATH: "/opt/wizardsofts-megabuild"
  # Sensitive variables come from GitLab UI!
  # Never hardcode: DB_PASSWORD, SSH_PRIVATE_KEY, API_KEY, etc.

# ============================================================================
# VALIDATION STAGE
# ============================================================================

validate-config:
  stage: validate
  image: python:3.11-slim
  before_script:
    - apt-get update && apt-get install -y git yamllint
    - pip install detect-secrets
  script:
    - |
      echo "🔍 Validating YAML configurations..."
      yamllint docker-compose*.yml traefik/*.yml || true
      
      echo "🔍 Checking for hardcoded secrets..."
      if detect-secrets scan --baseline .secrets.baseline; then
        echo "✅ No hardcoded secrets detected"
      else
        echo "❌ Hardcoded secrets found!"
        exit 1
      fi
      
      echo "🔍 Checking for credential patterns..."
      if grep -rE '(password|secret|key|token)\s*[:=]\s*["\']?[^$\{]*["\']?' \
         docker-compose*.yml traefik/ \
         --exclude-dir=.git \
         | grep -vE "(your_|example|changeme|\$\{)" | head -10; then
        echo "⚠️ WARNING: Potential hardcoded credentials found"
        # Don't fail, just warn
      fi
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master|develop)$/'

validate-docker:
  stage: validate
  image: python:3.11-slim
  before_script:
    - apt-get update && apt-get install -y docker-compose python3-pip
    - pip install pyyaml
  script:
    - |
      echo "🔍 Validating Docker Compose files..."
      docker-compose -f docker-compose.yml config > /dev/null || exit 1
      docker-compose -f docker-compose.prod.yml config > /dev/null || exit 1
      echo "✅ Docker Compose configurations are valid"
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master|develop)$/'

# ============================================================================
# SECURITY SCANNING STAGE
# ============================================================================

sast-scan:
  stage: scan
  image: returntocorp/semgrep
  script:
    - |
      echo "🔍 Running SAST security scan (Semgrep)..."
      semgrep --config=p/security-audit \
              --config=p/owasp-top-ten \
              --json \
              --output=sast-results.json \
              apps/ scripts/ traefik/ || true
      
      # Show findings
      if [ -s sast-results.json ]; then
        echo "⚠️ Security issues found:"
        python3 -m json.tool sast-results.json | head -50
      fi
  artifacts:
    reports:
      sast: sast-results.json
    expire_in: 30 days
  allow_failure: true
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master|develop)$/'

dependency-scan:
  stage: scan
  image: python:3.11-slim
  before_script:
    - pip install safety bandit
  script:
    - |
      echo "🔍 Scanning Python dependencies..."
      safety check --json > dependencies.json || true
      
      echo "🔍 Running Bandit security scan..."
      bandit -r apps/ -f json -o bandit-results.json || true
      
      cat dependencies.json | python3 -m json.tool | head -30
  artifacts:
    reports:
      dependency_scanning: dependencies.json
    expire_in: 30 days
  allow_failure: true
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^(main|master|develop)$/'

# ============================================================================
# BUILD STAGE
# ============================================================================

build-images:
  stage: build
  image: docker:24-cli
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      echo "🔨 Building Docker images..."
      
      # Only build on protected branches (main/master)
      if [[ ! "$CI_COMMIT_REF_NAME" =~ ^(main|master)$ ]]; then
        echo "⏭️  Skipping build for branch: $CI_COMMIT_REF_NAME"
        exit 0
      fi
      
      # Build only changed services
      docker-compose build --no-cache
      
      # Tag images
      docker images | grep -E "ws-gateway|ws-trades|ws-company" | while read image; do
        REPO=$(echo $image | awk '{print $1}')
        TAG=$(echo $image | awk '{print $2}')
        docker tag "$REPO:$TAG" "$CI_REGISTRY/$REPO:$CI_COMMIT_SHA"
        docker tag "$REPO:$TAG" "$CI_REGISTRY/$REPO:latest"
        
        # Push to registry
        docker push "$CI_REGISTRY/$REPO:$CI_COMMIT_SHA"
        docker push "$CI_REGISTRY/$REPO:latest"
      done
  only:
    - main
    - master
  environment:
    name: production

# ============================================================================
# DEPLOY STAGE
# ============================================================================

deploy-production:
  stage: deploy
  image: alpine:latest
  before_script:
    - |
      # Setup SSH
      apk add --no-cache openssh-client git curl bash
      mkdir -p ~/.ssh && chmod 700 ~/.ssh
      echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
      chmod 600 ~/.ssh/id_rsa
      
      # Add host key
      ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts 2>/dev/null
      
      # Verify SSH works
      ssh -o ConnectTimeout=5 $DEPLOY_USER@$DEPLOY_HOST "echo ✅ SSH connection successful"
  script:
    - |
      echo "🚀 Deploying to production..."
      
      ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST << 'DEPLOY_SCRIPT'
      set -e  # Exit on any error
      
      echo "📦 Creating backup..."
      BACKUP_DIR="/opt/backups/deploy_$(date +%Y%m%d_%H%M%S)"
      mkdir -p "$BACKUP_DIR"
      
      cd /opt/wizardsofts-megabuild
      
      # Backup current state
      docker-compose config > "$BACKUP_DIR/compose-backup.yml"
      cp -r traefik "$BACKUP_DIR/"
      cp .env "$BACKUP_DIR/.env.backup"
      
      # Backup database (if PostgreSQL is running)
      if docker exec postgres pg_isready > /dev/null 2>&1; then
        echo "💾 Backing up database..."
        docker exec postgres pg_dump -U gibd -d gibd_master > "$BACKUP_DIR/db_backup.sql"
      fi
      
      echo "📥 Pulling latest code..."
      git fetch origin
      git checkout origin/$CI_COMMIT_REF_NAME
      
      echo "🔄 Pulling latest images..."
      docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull --no-parallel
      
      echo "🚀 Starting services..."
      docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
      
      # Wait for services to be ready
      echo "⏳ Waiting for services to start (30s)..."
      sleep 30
      
      DEPLOY_SCRIPT
      
      echo "✅ Deployment scripts completed"
  environment:
    name: production
    url: https://www.wizardsofts.com
    action: prepare
  when: manual  # Require manual approval
  only:
    - main
    - master
  allow_failure: false

# ============================================================================
# VERIFY STAGE
# ============================================================================

verify-deployment:
  stage: verify
  image: alpine:latest
  before_script:
    - apk add --no-cache curl bash
  script:
    - |
      echo "🔍 Verifying deployment health..."
      
      HEALTH_CHECKS=(
        "https://www.wizardsofts.com"
        "https://api.wizardsofts.com/actuator/health"
        "https://appwrite.wizardsofts.com/v1/health"
      )
      
      FAILED=0
      for URL in "${HEALTH_CHECKS[@]}"; do
        echo "Checking: $URL"
        if curl -sf --max-time 10 "$URL" > /dev/null; then
          echo "  ✅ OK"
        else
          echo "  ❌ FAILED"
          FAILED=$((FAILED + 1))
        fi
      done
      
      if [ $FAILED -gt 0 ]; then
        echo "❌ Health check failed for $FAILED endpoints"
        echo "🔄 Initiating rollback..."
        exit 1
      fi
      
      echo "✅ All health checks passed!"
  environment:
    name: production
  when: on_success
  only:
    - main
    - master

# ============================================================================
# ROLLBACK STAGE (Manual)
# ============================================================================

rollback-production:
  stage: deploy
  image: alpine:latest
  before_script:
    - |
      apk add --no-cache openssh-client
      mkdir -p ~/.ssh && chmod 700 ~/.ssh
      echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
      chmod 600 ~/.ssh/id_rsa
      ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts 2>/dev/null
  script:
    - |
      echo "🔄 Rolling back to previous deployment..."
      
      ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST << 'ROLLBACK'
      
      # Find the most recent backup
      LAST_BACKUP=$(ls -t /opt/backups | grep "^deploy_" | head -1)
      
      if [ -z "$LAST_BACKUP" ]; then
        echo "❌ No backup found!"
        exit 1
      fi
      
      BACKUP_PATH="/opt/backups/$LAST_BACKUP"
      echo "📂 Rolling back to: $BACKUP_PATH"
      
      cd /opt/wizardsofts-megabuild
      
      # Restore files
      cp "$BACKUP_PATH/compose-backup.yml" docker-compose.yml
      cp -r "$BACKUP_PATH/traefik" .
      
      # Restart services
      docker-compose down
      docker-compose up -d
      
      # Wait for startup
      sleep 30
      
      # Verify
      if curl -sf https://api.wizardsofts.com/health > /dev/null; then
        echo "✅ Rollback successful"
      else
        echo "❌ Rollback verification failed"
        exit 1
      fi
      
      ROLLBACK
  when: manual
  only:
    - main
    - master
  environment:
    name: production
    action: rollback
```

---

## 4. GitLab Runner Security

### Install & Configure GitLab Runner

```bash
# SSH to deployment server
ssh wizardsofts@10.0.0.84

# Install GitLab Runner
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | \
  sudo bash
sudo apt-get install gitlab-runner

# Create dedicated runner user
sudo useradd -m -s /bin/bash gitlab-runner-user

# Add to docker group (if using docker executor)
sudo usermod -aG docker gitlab-runner-user

# Register runner with restricted permissions
sudo gitlab-runner register \
  --url https://gitlab.com/ \
  --registration-token $YOUR_TOKEN \
  --executor shell \
  --shell bash \
  --locked true \
  --access-level ref_protected \
  --description "Production Deployer" \
  --tag-list "production,deployment" \
  --run-untagged false \
  --protected-builds true
```

### Restrict Runner Access

```bash
# Edit /etc/gitlab-runner/config.toml
sudo nano /etc/gitlab-runner/config.toml

# Add to runner configuration:
[runners.shell]
  # Restrict to specific branch
  protected = true
  
  # Only run on protected branches
  [runners.shell.environment]
    ALLOWED_BRANCHES = "main,master,develop"
```

---

## 5. Image Scanning in CI/CD

### Add Container Image Scanning

Create `.gitlab/ci/security.gitlab-ci.yml`:

```yaml
# ============================================================================
# Container Image Security Scanning
# ============================================================================

scan-container-trivy:
  stage: scan
  image: aquasec/trivy:latest
  variables:
    # Run trivy in parallel
    TRIVY_PARALLEL_PROCESSES: "4"
  script:
    - |
      echo "🔍 Scanning Docker images with Trivy..."
      
      # Scan docker-compose images
      trivy config docker-compose.yml \
        --severity HIGH,CRITICAL \
        --exit-code 0 \
        --format json \
        --output trivy-config.json || true
      
      # Scan individual images
      for service in traefik postgres redis ws-gateway ws-trades; do
        echo "Scanning $service..."
        trivy image --severity HIGH,CRITICAL \
          --format json \
          --output trivy-$service.json \
          $service:latest || true
      done
      
      # Generate report
      trivy image --severity HIGH,CRITICAL \
        --format sarif \
        --output trivy-report.sarif \
        wizardsofts/megabuild:latest || true
  artifacts:
    reports:
      container_scanning: trivy-report.sarif
    paths:
      - trivy-*.json
    expire_in: 30 days
  allow_failure: true

scan-container-snyk:
  stage: scan
  image: snyk/snyk:latest
  before_script:
    - snyk auth $SNYK_TOKEN
  script:
    - |
      echo "🔍 Scanning with Snyk..."
      
      for app in apps/*/; do
        if [ -f "$app/package.json" ]; then
          echo "Scanning $app"
          snyk test "$app" --json > snyk-${app//\//-}.json || true
        fi
      done
  artifacts:
    paths:
      - snyk-*.json
    expire_in: 30 days
  allow_failure: true
  only:
    - merge_requests
```

---

## 6. Deployment Checklist in CI/CD

### Pre-Deployment Validation

```bash
# Ensure in deploy script:

# 1. Verify environment variables
if [ -z "$DB_PASSWORD" ] || [ -z "$SSH_PRIVATE_KEY" ]; then
  echo "❌ Required secrets not set!"
  exit 1
fi

# 2. Test SSH connection
ssh -o ConnectTimeout=5 $DEPLOY_USER@$DEPLOY_HOST "echo OK" || exit 1

# 3. Verify docker-compose syntax
docker-compose -f docker-compose.yml config > /dev/null || exit 1

# 4. Check disk space (need at least 10GB free)
DISK_FREE=$(df /opt | awk 'NR==2 {print $4}')
if [ $DISK_FREE -lt 10485760 ]; then  # 10GB in KB
  echo "❌ Not enough disk space!"
  exit 1
fi

# 5. Create deployment record
DEPLOY_ID=$(date +%s)
echo "Deployment started at $(date)" > /opt/deployments/deploy_$DEPLOY_ID.log
```

---

## 7. Monitoring & Alerting

### Setup Deployment Alerts

```yaml
# Create in GitLab Alerts section
# Project → Monitor → Alerts

Critical Alerts:
- Deployment Failed
- Service Down (HTTP 5xx > 5%)
- High Error Rate
- Rate Limit Exceeded
- Certificate Expiring Soon

Actions:
- Slack notification
- Email notification
- Create incident ticket
- Trigger on-call engineer
```

---

## 8. Audit & Compliance

### Deployment Audit Trail

All deployments are automatically logged:

```bash
# View deployment history
git log --oneline --decorate --graph

# View pipeline status
# GitLab UI → CI/CD → Pipelines

# Download deployment logs
# Each pipeline has complete logs available
```

### Compliance Checklist

- ✅ All deployments via CI/CD (no manual SSH)
- ✅ All secrets in GitLab (protected, masked)
- ✅ All images scanned before deployment
- ✅ Rollback capability tested monthly
- ✅ Audit logs retained for 1 year
- ✅ Approval required before production deploy
- ✅ Deployment validation automated

---

## 9. Troubleshooting

### CI/CD Pipeline Failures

**SSH Connection Failed**
```bash
# Debug: Check SSH key in GitLab UI
# 1. Verify SSH_PRIVATE_KEY variable is set
# 2. Verify it's the correct key (matches ~/.ssh/id_rsa)
# 3. Verify it has no passphrase
# 4. Verify runner can reach deploy host
```

**Docker Image Build Failed**
```bash
# Debug: Check Docker login
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# Check Dockerfile syntax
docker build --no-cache .

# Check base image availability
docker pull ubuntu:22.04
```

**Health Check Failed**
```bash
# Debug on server:
ssh wizardsofts@10.0.0.84

# Check service logs
docker logs traefik | tail -50
docker logs ws-gateway | tail -50

# Check network connectivity
curl -v http://localhost:8080/health
```

---

## Summary: CI/CD Security Checklist

| Item | Status | Target |
|------|--------|--------|
| GitLab variables configured | ❌ | ✅ Week 1 |
| Secrets removed from code | ❌ | ✅ Week 1 |
| CI/CD pipeline created | ❌ | ✅ Week 2 |
| Image scanning enabled | ❌ | ✅ Week 2 |
| Deployment approval required | ❌ | ✅ Week 2 |
| Rollback tested | ❌ | ✅ Week 3 |
| Monitoring configured | ❌ | ✅ Week 3 |
| Team trained | ❌ | ✅ Week 4 |

---

## Next Steps

1. **Configure GitLab Variables** (Day 1)
2. **Update .gitlab-ci.yml** (Day 2-3)
3. **Install GitLab Runner** (Day 4)
4. **Test in staging** (Day 5-7)
5. **Deploy to production** (Day 8-14)
6. **Monitor & iterate** (Ongoing)


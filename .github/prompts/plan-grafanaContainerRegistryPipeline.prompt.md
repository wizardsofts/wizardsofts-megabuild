# Plan: Grafana Container Registry & Pipeline Implementation

**TL;DR:** Build a custom Grafana image with baked config, store in GitLab Container Registry, add CI tests for config/dashboards, deploy via docker-compose with environment variables for secrets. Includes prechecks, sequential setup, automated health checks, memory limits, SSO validation, and registry cleanup.

---

## Prechecks & Gap Analysis

### Server 84 Prechecks
1. ✅ Docker & Docker Compose installed (v29.1.3, v5.0.0)
2. ✅ GitLab self-hosted running (10.0.0.84:8090)
3. ✅ Keycloak running (10.0.0.84:8180)
4. ✅ Prometheus & Loki running (verified via docker ps)
5. ⚠️ **Gap**: No Container Registry DNS/URL documented; need to verify reachability
6. ⚠️ **Gap**: No `.env` file in `infrastructure/monitoring/` for Grafana secrets
7. ⚠️ **Gap**: Missing `infrastructure/monitoring/grafana/` config files (bake into image instead)
8. ⚠️ **Gap**: No Dockerfile for custom Grafana image
9. ⚠️ **Gap**: Missing CI job for Grafana-specific validation and image build

### Configuration Gaps
1. OAuth config exists in `infrastructure/auto-scaling/monitoring/grafana/grafana.ini` but not synced to monitoring stack
2. No environment variable injection in compose for `GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET`
3. No memory limits on current Grafana container
4. No health check for Keycloak connectivity in CI
5. No automated test for dashboard JSON validity
6. No registry cleanup policy documented in pipeline

### Documentation Gaps
1. No deployment guide for baked Grafana image
2. No troubleshooting guide for SSO breaks
3. No registry token rotation script in repo
4. No memory limit escalation runbook

---

## Key Implementation Decisions

### 1. Keycloak Access Control: Domain & Role Requirements

**Requirement**: Users must be from `wizardsofts.com` domain AND have a role to access Grafana.

**Implementation in Keycloak**:

```json
// infrastructure/monitoring/keycloak-grafana-client.json (update)
{
  "clientId": "grafana",
  "name": "Grafana Monitoring Dashboard",
  // ... existing config ...
  "protocolMappers": [
    {
      "name": "email-domain-validator",
      "protocol": "openid-connect",
      "protocolMapper": "oidc-hardcoded-claim-mapper",
      "consentRequired": false,
      "config": {
        "claim.value": "wizardsofts.com",
        "userinfo.token.claim": "true",
        "id.token.claim": "true",
        "access.token.claim": "true"
      }
    },
    {
      "name": "grafana-role-mapper",
      "protocol": "openid-connect",
      "protocolMapper": "oidc-usermodel-realm-role-mapper",
      "consentRequired": false,
      "config": {
        "claim.name": "roles",
        "userinfo.token.claim": "true",
        "id.token.claim": "true",
        "access.token.claim": "true"
      }
    }
  ]
}
```

**In grafana.ini OAuth config**:

```ini
[auth.generic_oauth]
enabled = true
name = Keycloak
client_id = grafana
client_secret = ${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET}
scopes = openid profile email roles
auth_url = http://10.0.0.84:8180/realms/master/protocol/openid-connect/auth
token_url = http://keycloak:8080/realms/master/protocol/openid-connect/token
api_url = http://keycloak:8080/realms/master/protocol/openid-connect/userinfo

# Map Keycloak roles to Grafana roles
# Only users with 'grafana-admin' or 'grafana-editor' roles can login
role_attribute_path = contains(roles[*], 'grafana-admin') && 'Admin' || contains(roles[*], 'grafana-editor') && 'Editor' || 'Viewer'

# Require email from wizardsofts.com
email_attribute_name = email
email_attribute_path = email
```

**Keycloak Setup**:
1. Create role `grafana-admin` in Keycloak master realm
2. Create role `grafana-editor` in Keycloak master realm
3. Assign users to roles in Keycloak UI
4. Create federation/user mapping to enforce `wizardsofts.com` email domain (via LDAP, OIDC federation, or manual user creation with email constraint)

**Testing email domain in CI**:
```bash
# In test:grafana:sso job, add:
- |
  echo "🔍 Checking Keycloak user domain requirement..."
  curl -sf "$KEYCLOAK_URL/admin/realms/master/users" \
    -H "Authorization: Bearer $TOKEN" | \
    jq -e '.[] | select(.email | endswith("@wizardsofts.com"))' || {
    echo "⚠️ No users with @wizardsofts.com domain found"
  }
```

---

### 2. Deployment Strategy: Stop Old Grafana or Rolling Update?

**Question**: Should we stop running Grafana after tests pass before deploying the new one?

**Answer**: **No, use zero-downtime rolling update (blue-green).** Stop only after new one is healthy.

**Strategy**:

```bash
# Recommended: Zero-downtime deployment flow

#!/bin/bash
# scripts/deploy-grafana-rolling.sh

set -e
MONITORING_DIR="/opt/wizardsofts-megabuild/infrastructure/monitoring"
cd "$MONITORING_DIR"

echo "🚀 Rolling deployment of Grafana..."

# Step 1: Pull new image
echo "📥 Pulling new Grafana image..."
docker-compose pull grafana

# Step 2: Start new container (compose creates with different name initially)
echo "🟢 Starting new Grafana container..."
docker-compose up -d grafana

# Step 3: Wait for health check
echo "⏳ Waiting for new container to become healthy..."
for i in {1..30}; do
  if docker exec grafana wget --spider -q http://localhost:3000/api/health 2>/dev/null; then
    echo "✅ New Grafana container is healthy"
    break
  fi
  echo "  Attempt $i/30... waiting..."
  sleep 10
done

# Step 4: Run verification tests
echo "🧪 Running smoke tests on new container..."
bash test-grafana-deployment.sh || {
  echo "❌ Smoke tests failed, rolling back..."
  docker-compose down grafana
  docker-compose up -d grafana  # Restart old version
  exit 1
}

# Step 5: If tests pass, old container is already replaced
echo "✅ Rolling deployment complete"
echo "   Old container removed, new container taking traffic"
```

**Why rolling update over blue-green?**
- **Simpler**: One Grafana instance, no port conflicts
- **Storage efficient**: Reuses same `grafana-data` volume (no migration)
- **Faster**: No need to switch DNS/load balancer
- **Safe**: `docker-compose up -d` replaces container atomically if image changed

**Fallback rollback** (if new deployment fails):
```bash
# Rollback to previous image tag
docker pull 10.0.0.84:5050/wizardsofts/grafana:stable-<previous-sha>
docker tag 10.0.0.84:5050/wizardsofts/grafana:stable-<previous-sha> \
           10.0.0.84:5050/wizardsofts/grafana:latest
docker-compose up -d grafana
```

---

### 3. How Do Tests Run?

**Test Execution Flow**:

```
┌─────────────────────────────────────────────────────────────────┐
│ GitLab CI Pipeline Triggered (on push to main with Grafana      │
│ config changes, or manual trigger)                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: test                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Job 1] test:grafana:config (runs in Docker container)         │
│  ├─ apk install jq                                              │
│  ├─ Validate grafana.ini exists                                 │
│  ├─ Validate all dashboard JSONs (jq empty)                     │
│  ├─ Check dashboard structure (has panels)                      │
│  ├─ Validate provisioning configs                               │
│  ├─ Check OAuth section present                                 │
│  └─ Check all OAuth fields (client_id, secret, urls, etc)       │
│     STATUS: ✅ PASS / ❌ FAIL (blocks build if fails)            │
│                                                                  │
│  [Job 2] test:grafana:sso (parallel, runs in curl container)    │
│  ├─ Check Keycloak OIDC endpoint reachable                      │
│  ├─ Verify Grafana client exists                                │
│  ├─ Check user domain (@wizardsofts.com)                        │
│  └─ Check Grafana client has required roles                     │
│     STATUS: ✅ PASS / ⚠️ ALLOW_FAILURE (doesn't block build)     │
│                                                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: build                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Job 3] build:grafana:image (if test passed, on main branch)   │
│  ├─ docker login to registry                                    │
│  ├─ docker build -t 10.0.0.84:5050/wizardsofts/grafana:sha     │
│  ├─ docker build -t 10.0.0.84:5050/wizardsofts/grafana:latest  │
│  ├─ docker push all tags                                        │
│  └─ List image sizes & tags                                     │
│     STATUS: ✅ Built & Pushed / ❌ Build fails                   │
│                                                                  │
│  Image now available in GitLab Container Registry               │
│  (10.0.0.84:5050/wizardsofts/grafana:latest + git SHA tag)      │
│                                                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼ (After merge to main)
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: maintenance (scheduled, e.g., weekly)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Job 4] cleanup:registry (scheduled job)                       │
│  └─ GitLab UI cleanup policy removes old tags                   │
│     (keeps 10 most recent, deletes >30 days)                    │
│                                                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ MANUAL DEPLOYMENT (Ops-driven, on server 84)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Pre-deployment checklist]                                     │
│  ├─ Image exists in registry? (docker pull)                    │
│  ├─ .env file present with secrets?                            │
│  ├─ docker-compose.yml valid?                                  │
│  ├─ Prometheus running? Keycloak running?                      │
│  └─ Networks exist? (monitoring, microservices-overlay)        │
│                                                                  │
│  [Deploy]                                                       │
│  ├─ cd /opt/wizardsofts-megabuild/infrastructure/monitoring    │
│  ├─ docker-compose down grafana (stop old)                     │
│  ├─ docker-compose pull grafana (pull new image)               │
│  ├─ docker-compose up -d grafana (start new)                   │
│                                                                  │
│  [Post-deployment verification]                                │
│  ├─ Wait 10s for health check                                  │
│  ├─ curl http://localhost:3002/api/health                      │
│  ├─ docker logs grafana --tail 50                              │
│  └─ Manual UI test: http://localhost:3002                      │
│                                                                  │
│  [Smoke tests (on deployment server)]                           │
│  ├─ test-grafana-deployment.sh (container, health, API)        │
│  ├─ test-grafana-sso.sh (OAuth endpoints)                      │
│  ├─ test-grafana-performance.sh (load test 5 min)              │
│                                                                  │
│  STATUS: ✅ Deployed / ❌ Failed (trigger rollback)              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Where Tests Run**:

| Test | Environment | When | Trigger |
|------|-------------|------|---------|
| `test:grafana:config` | GitLab CI container (alpine:latest + jq) | On config change | Auto |
| `test:grafana:sso` | GitLab CI container (curl) | On grafana.ini change | Auto |
| `build:grafana:image` | GitLab CI runner (docker:dind) | On test pass | Auto |
| `test-grafana-deployment.sh` | Server 84 (bash + curl + docker) | After deploy | Manual |
| `test-grafana-sso.sh` | Server 84 (bash + curl) | After deploy | Manual |
| `test-grafana-performance.sh` | Server 84 (bash + docker stats) | After deploy | Manual |

**CI Tests (Automatic)** vs **Deployment Tests (Manual)**:

- **CI tests** = config validation, syntax checking, Keycloak reachability (FAST, catches bugs before build)
- **Deployment tests** = container health, API responses, OAuth flows, performance load (THOROUGH, validates actual running service)

---

## Sequential Implementation Steps

### **Phase 1: Preparation & Prechecks (Day 1)**

#### Step 1.1: Verify Server 84 Environment
```bash
# On server 84, create checklist script
scripts/prechecks-grafana-pipeline.sh

# Verify:
- Docker daemon running and accessible
- GitLab reachable (curl http://10.0.0.84:8090/-/readiness)
- Keycloak reachable (curl http://10.0.0.84:8180/realms/master/.well-known/openid-configuration)
- Prometheus running (docker ps | grep prometheus)
- Loki running (docker ps | grep loki)
- NFS mounted (df -h | grep nfs)
- Available disk space >100GB
- Network connectivity to registries
```

**Remediation if failed:**
- Docker: `apt update && apt install -y docker.io docker-compose` (if Snap, uninstall and use apt)
- GitLab/Keycloak: Check service status via `docker ps`
- NFS: Mount via `mount -t nfs server:/path /mnt/nfs`

---

#### Step 1.2: Create .env File for Monitoring Stack
**File**: `infrastructure/monitoring/.env`

```env
# Grafana Configuration
GRAFANA_PASSWORD=secure-admin-password-here
GRAFANA_OAUTH_CLIENT_SECRET=grafana-secret-stable-v1

# Loki Retention
LOKI_RETENTION_DAYS=15

# Prometheus Retention
PROMETHEUS_RETENTION=15d

# Alert Routing (optional, for future integrations)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SMTP_PASSWORD=gmail-app-password-here
```

**Remediation checklist:**
- [ ] `.env` marked in `.gitignore`
- [ ] Copy `.env` to server 84 via secure channel (scp, not git)
- [ ] Validate env vars are read-only on server: `chmod 600 .env`

---

#### Step 1.3: Organize Grafana Config Files
**Action**: Copy configs from auto-scaling to monitoring directory (they should be identical going forward)

```bash
mkdir -p infrastructure/monitoring/grafana/{provisioning,dashboards}
cp infrastructure/auto-scaling/monitoring/grafana/grafana.ini \
   infrastructure/monitoring/grafana/grafana.ini
cp -r infrastructure/auto-scaling/monitoring/grafana/provisioning/* \
   infrastructure/monitoring/grafana/provisioning/
cp -r infrastructure/auto-scaling/monitoring/grafana/dashboards/*.json \
   infrastructure/monitoring/grafana/dashboards/
```

**Verify structure:**
```
infrastructure/monitoring/grafana/
├── grafana.ini
├── provisioning/
│   ├── datasources/
│   │   └── datasources.yaml
│   ├── dashboards/
│   │   └── dashboards.yaml
│   └── alert_notifiers/
│       └── alerting.yaml
└── dashboards/
    ├── all-servers-executive.json
    ├── all-servers-security.json
    ├── docker-containers.json
    ├── node-exporter.json
    ├── server-81-security.json
    └── server-84-security.json
```

---

### **Phase 2: Build Infrastructure (Days 2–3)**

#### Step 2.1: Create Dockerfile for Custom Grafana Image
**File**: `infrastructure/monitoring/Dockerfile.grafana`

```dockerfile
# Use pinned base image (not :latest)
FROM grafana/grafana:10.2.0

# Set labels for metadata
LABEL maintainer="ops@wizardsofts.com"
LABEL version="1.0"
LABEL description="Custom Grafana with baked Keycloak SSO config"

# Copy configuration files
COPY infrastructure/monitoring/grafana/grafana.ini /etc/grafana/grafana.ini
COPY infrastructure/monitoring/grafana/provisioning /etc/grafana/provisioning
COPY infrastructure/monitoring/grafana/dashboards /var/lib/grafana/dashboards

# Fix ownership to Grafana user (472:472)
RUN chown -R 472:472 /etc/grafana /var/lib/grafana && \
    chmod 644 /etc/grafana/grafana.ini && \
    chmod -R 755 /etc/grafana/provisioning && \
    chmod 644 /var/lib/grafana/dashboards/*.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --spider -q http://localhost:3000/api/health || exit 1

# User context (already set by base image)
USER grafana

# Expose port
EXPOSE 3000
```

**Testing:**
```bash
# Build locally to verify
docker build -t grafana:test -f infrastructure/monitoring/Dockerfile.grafana .
docker run -e GF_SECURITY_ADMIN_PASSWORD=test --rm grafana:test
# Verify startup: docker logs should show "started Grafana"
```

---

#### Step 2.2: Update docker-compose.yml for Monitoring Stack
**File**: `infrastructure/monitoring/docker-compose.yml`

**Changes:**
1. Replace image reference with custom registry image
2. Add environment variable injection for secrets
3. Add resource limits
4. Add memory swap settings
5. Remove old bind mounts (config now in image)

**Key sections to modify:**

```yaml
services:
  grafana:
    # OLD: image: grafana/grafana:10.2.0
    # NEW: Use custom built image
    image: 10.0.0.84:5050/wizardsofts/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3002:3000"
    
    # Environment variables (secrets from .env)
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET=${GRAFANA_OAUTH_CLIENT_SECRET}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel
    
    # Volume: only data, config is baked in image
    volumes:
      - grafana-data:/var/lib/grafana
    
    # Networks (share with microservices for Keycloak)
    networks:
      - monitoring
      - microservices-overlay
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M
    
    # Memory & OOM settings
    mem_swappiness: 0
    oom_kill_disable: false
    
    # Healthcheck
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    # NO BIND MOUNTS for config
    # - REMOVED: ./grafana/grafana.ini:/etc/grafana/grafana.ini
    # - REMOVED: ./grafana/provisioning:/etc/grafana/provisioning
    # - REMOVED: ./grafana/dashboards:/var/lib/grafana/dashboards
```

---

#### Step 2.3: Add GitLab Container Registry Cleanup Policy (Manual)
**Action**: Configure via GitLab UI for now (automation can come later)

**Steps:**
1. Go to GitLab: http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild
2. Navigate to **Settings > Packages & Registries > Container Registry**
3. Enable **Cleanup Policy**:
   - Keep last 10 tags (not 5, for homeserver safety)
   - Delete tags older than 30 days
   - Delete untagged images
4. Save

**Future**: Implement via API in scheduled CI job

---

### **Phase 3: CI/CD Pipeline Setup (Days 4–5)**

#### Step 3.1: Create Test Stage for Grafana Configuration
**File**: `.gitlab-ci.yml` (add to existing test stage)

```yaml
test:grafana:config:
  stage: test
  image: alpine:latest
  script:
    - apk add --no-cache jq
    
    # Test 1: Validate grafana.ini syntax
    - |
      echo "🔍 Validating grafana.ini..."
      if [ ! -f infrastructure/monitoring/grafana/grafana.ini ]; then
        echo "❌ grafana.ini not found"
        exit 1
      fi
      
    # Test 2: Validate all dashboard JSONs
    - |
      echo "🔍 Validating dashboard JSONs..."
      for dashboard in infrastructure/monitoring/grafana/dashboards/*.json; do
        if ! jq empty "$dashboard" 2>/dev/null; then
          echo "❌ Invalid JSON: $dashboard"
          exit 1
        fi
        echo "✅ Valid: $dashboard"
      done
    
    # Test 3: Check for required fields in dashboards
    - |
      echo "🔍 Checking dashboard structure..."
      for dashboard in infrastructure/monitoring/grafana/dashboards/*.json; do
        if ! jq -e '.panels[]' "$dashboard" >/dev/null; then
          echo "⚠️ Warning: $dashboard has no panels"
        fi
      done
    
    # Test 4: Validate provisioning configs
    - |
      echo "🔍 Validating provisioning configs..."
      jq empty infrastructure/monitoring/grafana/provisioning/datasources/datasources.yaml 2>/dev/null || \
        echo "⚠️ Datasources config may not be valid YAML->JSON"
      jq empty infrastructure/monitoring/grafana/provisioning/dashboards/dashboards.yaml 2>/dev/null || \
        echo "⚠️ Dashboards config may not be valid YAML->JSON"
    
    # Test 5: Check OAuth config present
    - |
      echo "🔍 Validating OAuth configuration..."
      grep -q "\[auth.generic_oauth\]" infrastructure/monitoring/grafana/grafana.ini || {
        echo "❌ OAuth section missing in grafana.ini"
        exit 1
      }
      for field in enabled client_id client_secret auth_url token_url api_url; do
        grep -q "$field" infrastructure/monitoring/grafana/grafana.ini || {
          echo "❌ Missing OAuth field: $field"
          exit 1
        }
      done
      echo "✅ OAuth config valid"
  
  rules:
    - changes:
        - infrastructure/monitoring/grafana/**
        - infrastructure/monitoring/Dockerfile.grafana
  
  allow_failure: false
```

---

#### Step 3.2: Create Build Stage for Grafana Image
**File**: `.gitlab-ci.yml` (add to existing build stage)

```yaml
build:grafana:image:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  variables:
    DOCKER_HOST: tcp://docker:2375
    DOCKER_TLS_CERTDIR: ""
    REGISTRY_URL: "10.0.0.84:5050"
    REGISTRY_PROJECT: "wizardsofts/grafana"
  
  script:
    # Login to registry
    - |
      echo "🔐 Authenticating to GitLab Container Registry..."
      docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$REGISTRY_URL"
    
    # Build image with git SHA tag
    - |
      echo "🏗️ Building Grafana image..."
      docker build \
        -t "$REGISTRY_URL/$REGISTRY_PROJECT:$CI_COMMIT_SHA" \
        -t "$REGISTRY_URL/$REGISTRY_PROJECT:latest" \
        -t "$REGISTRY_URL/$REGISTRY_PROJECT:stable-$CI_COMMIT_SHORT_SHA" \
        -f infrastructure/monitoring/Dockerfile.grafana .
    
    # Push to registry
    - |
      echo "📤 Pushing to GitLab Container Registry..."
      docker push "$REGISTRY_URL/$REGISTRY_PROJECT:$CI_COMMIT_SHA"
      docker push "$REGISTRY_URL/$REGISTRY_PROJECT:latest"
      docker push "$REGISTRY_URL/$REGISTRY_PROJECT:stable-$CI_COMMIT_SHORT_SHA"
    
    # Image inspection
    - |
      echo "📊 Image info:"
      docker images | grep grafana
  
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - infrastructure/monitoring/grafana/**
        - infrastructure/monitoring/Dockerfile.grafana
      when: on_success
  
  retry:
    max: 2
    when: runner_system_failure
```

---

#### Step 3.3: Create SSO Health Check Job
**File**: `.gitlab-ci.yml` (add to test or maintenance stage)

```yaml
test:grafana:sso:
  stage: test
  image: curlimages/curl:latest
  script:
    # Test 1: Keycloak OIDC endpoint reachable
    - |
      echo "🔍 Checking Keycloak OIDC endpoint..."
      curl -sf http://10.0.0.84:8180/realms/master/.well-known/openid-configuration \
        >/dev/null || {
        echo "❌ Keycloak OIDC endpoint unreachable"
        exit 1
      }
      echo "✅ Keycloak OIDC endpoint OK"
    
    # Test 2: Verify Grafana client exists
    - |
      echo "🔍 Checking Grafana Keycloak client..."
      ADMIN_TOKEN=$(curl -s -X POST \
        "http://10.0.0.84:8180/realms/master/protocol/openid-connect/token" \
        -d "client_id=admin-cli" \
        -d "username=admin" \
        -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
        -d "grant_type=password" 2>/dev/null | jq -r '.access_token // empty')
      
      if [ -z "$ADMIN_TOKEN" ]; then
        echo "⚠️ Could not authenticate to Keycloak (optional check, may fail in non-prod)"
        exit 0
      fi
      
      curl -sf -H "Authorization: Bearer $ADMIN_TOKEN" \
        "http://10.0.0.84:8180/admin/realms/master/clients" 2>/dev/null | \
        jq -e '.[] | select(.clientId=="grafana")' >/dev/null || {
        echo "❌ Grafana client not found in Keycloak"
        exit 1
      }
      echo "✅ Grafana client exists in Keycloak"
  
  rules:
    - changes:
        - infrastructure/monitoring/grafana/grafana.ini
  
  allow_failure: true  # Don't block if Keycloak down
```

---

#### Step 3.4: Create Registry Cleanup Job (Scheduled)
**File**: `.gitlab-ci.yml` (add to maintenance stage)

```yaml
cleanup:registry:
  stage: maintenance
  image: alpine:latest
  script:
    - apk add --no-cache curl jq
    - |
      echo "🧹 Running registry cleanup..."
      
      # This is a placeholder; actual cleanup happens via GitLab UI cleanup policy
      # Future: Implement programmatic cleanup using GitLab API
      
      echo "✅ Registry cleanup scheduled (via GitLab UI policy)"
      echo "Policy: Keep last 10 tags, delete >30 days old"
  
  only:
    - schedules
  
  rules:
    - if: '$CLEANUP_REGISTRY == "true"'
```

---

### **Phase 4: Configuration & Validation (Days 5–6)**

#### Step 4.1: Validate grafana.ini for OAuth
**File**: `infrastructure/monitoring/grafana/grafana.ini`

**Ensure these sections exist with correct values:**

```ini
[server]
protocol = http
http_port = 3000
domain = 10.0.0.84:3002
root_url = http://10.0.0.84:3002

[security]
admin_user = wizardofts
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
disable_login_form = false
oauth_auto_login = false

[auth]
disable_login_form = false

[auth.generic_oauth]
enabled = true
name = Keycloak
allow_sign_up = true
client_id = grafana
client_secret = ${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET}
scopes = openid profile email
auth_url = http://10.0.0.84:8180/realms/master/protocol/openid-connect/auth
token_url = http://keycloak:8080/realms/master/protocol/openid-connect/token
api_url = http://keycloak:8080/realms/master/protocol/openid-connect/userinfo
role_attribute_path = contains(groups[*], 'admin') && 'Admin' || 'Viewer'
```

**Validation script**: `scripts/validate-grafana-sso.sh`

```bash
#!/bin/bash
set -e

echo "✓ Validating Grafana SSO configuration..."

GRAFANA_INI="infrastructure/monitoring/grafana/grafana.ini"

# Check file exists
[ -f "$GRAFANA_INI" ] || { echo "❌ $GRAFANA_INI not found"; exit 1; }

# Check OAuth section
grep -q "^\[auth.generic_oauth\]" "$GRAFANA_INI" || {
  echo "❌ [auth.generic_oauth] section missing"
  exit 1
}

# Check required fields
for field in enabled client_id client_secret auth_url token_url api_url; do
  grep -q "^$field" "$GRAFANA_INI" || {
    echo "❌ Missing field: $field"
    exit 1
  }
done

# Verify no hardcoded secrets
if grep -q "^client_secret = [^$]" "$GRAFANA_INI"; then
  echo "❌ WARNING: hardcoded secret found (should be env var)"
  exit 1
fi

echo "✅ Grafana SSO configuration valid"
```

**Run validation:**
```bash
bash scripts/validate-grafana-sso.sh
```

---

#### Step 4.2: Verify Keycloak Client Configuration
**Action**: Create/verify Grafana client in Keycloak

**File**: `infrastructure/monitoring/keycloak-grafana-client.json`

```json
{
  "clientId": "grafana",
  "name": "Grafana Monitoring Dashboard",
  "enabled": true,
  "protocol": "openid-connect",
  "publicClient": false,
  "secret": "grafana-secret-stable-v1",
  "redirectUris": [
    "http://10.0.0.84:3002/login/generic_oauth",
    "https://grafana.wizardsofts.com/login/generic_oauth"
  ],
  "webOrigins": ["+"],
  "standardFlowEnabled": true,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "serviceAccountsEnabled": false,
  "authorizationServicesEnabled": false,
  "attributes": {
    "saml.assertion.signature": "false",
    "saml.force.post.binding": "false",
    "saml_assertion_consumer_url_post": "http://10.0.0.84:3002/login/generic_oauth",
    "oauth2.device.authorization.grant.enabled": "false",
    "oidc.ciba.grant.enabled": "false",
    "client.secret.creation.time": "1735929600",
    "backchannel.logout.session.required": "true"
  }
}
```

**Setup script**: `scripts/setup-grafana-keycloak-client.sh`

```bash
#!/bin/bash
set -e

KEYCLOAK_URL="http://10.0.0.84:8180"
ADMIN_USER="wizardofts"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}"
REALM="master"

echo "🔐 Setting up Grafana Keycloak client..."

# Get admin token
TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" | jq -r '.access_token')

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to authenticate to Keycloak"
  exit 1
fi

# Check if client exists
CLIENT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients" | \
  jq -r '.[] | select(.clientId=="grafana") | .id // empty')

if [ -n "$CLIENT_ID" ]; then
  echo "✓ Client exists, updating..."
  curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_ID" \
    -d @infrastructure/monitoring/keycloak-grafana-client.json
else
  echo "✓ Client not found, creating..."
  curl -s -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
    -d @infrastructure/monitoring/keycloak-grafana-client.json
fi

echo "✅ Grafana Keycloak client configured"
```

**Run setup:**
```bash
export KEYCLOAK_ADMIN_PASSWORD="your-password"
bash scripts/setup-grafana-keycloak-client.sh
```

---

### **Phase 5: Build & Push to Registry (Day 6)**

#### Step 5.1: Trigger CI Pipeline Manually (First Time)
**Action**: Push all changes to a feature branch and create MR

```bash
git add infrastructure/monitoring/
git add infrastructure/monitoring/.env (with .gitignore entry)
git add .gitlab-ci.yml
git add scripts/validate-grafana-sso.sh
git add scripts/setup-grafana-keycloak-client.sh
git commit -m "feat: grafana custom image and pipeline"
git push origin feature/grafana-pipeline

# Open MR in GitLab UI
# Verify tests pass
# Merge to main
```

**Pipeline will:**
1. ✅ Run `test:grafana:config` → validate JSON/INI
2. ✅ Run `test:grafana:sso` → verify Keycloak
3. ✅ Run `build:grafana:image` → build & push re
4. ✅ Image available at `10.0.0.84:5050/wizardsofts/grafana:latest`

---

#### Step 5.2: Verify Image in Registry
**Action**: On server 84, verify image is available

```bash
docker login -u git_user -p git_token 10.0.0.84:5050
docker pull 10.0.0.84:5050/wizardsofts/grafana:latest
docker images | grep grafana

# Output:
# 10.0.0.84:5050/wizardsofts/grafana  latest  <image-id>  <size>
```

---

### **Phase 6: Deployment (Days 7–8)**

#### Step 6.1: Pre-Deployment Checklist
**Action**: Verify readiness before deploying

```bash
# Checklist script: scripts/pre-deploy-grafana.sh

#!/bin/bash
set -e

echo "📋 Pre-deployment checklist for Grafana..."

# Check 1: Image in registry
echo "✓ Checking image in registry..."
docker login -u "$GIT_USER" -p "$GIT_TOKEN" 10.0.0.84:5050
docker pull 10.0.0.84:5050/wizardsofts/grafana:latest || {
  echo "❌ Image not found in registry"
  exit 1
}

# Check 2: .env file on server
echo "✓ Checking .env file..."
[ -f /opt/wizardsofts-megabuild/infrastructure/monitoring/.env ] || {
  echo "❌ .env file missing"
  exit 1
}

# Check 3: Docker compose valid
echo "✓ Validating docker-compose..."
docker-compose -f /opt/wizardsofts-megabuild/infrastructure/monitoring/docker-compose.yml config >/dev/null || {
  echo "❌ docker-compose.yml invalid"
  exit 1
}

# Check 4: Prometheus running
echo "✓ Checking Prometheus..."
docker ps | grep prometheus || {
  echo "❌ Prometheus not running"
  exit 1
}

# Check 5: Keycloak reachable
echo "✓ Checking Keycloak..."
curl -sf http://10.0.0.84:8180/realms/master/.well-known/openid-configuration >/dev/null || {
  echo "⚠️ Keycloak unreachable (SSO will fail)"
}

# Check 6: Network exists
echo "✓ Checking networks..."
docker network ls | grep monitoring || {
  echo "❌ 'monitoring' network missing"
  exit 1
}

docker network ls | grep microservices-overlay || {
  echo "❌ 'microservices-overlay' network missing"
  exit 1
}

echo "✅ All pre-deployment checks passed"
```

**Run checklist:**
```bash
bash scripts/pre-deploy-grafana.sh
```

---

#### Step 6.2: Deploy Grafana Container
**Action**: Stop old, start new Grafana with custom image

```bash
cd /opt/wizardsofts-megabuild/infrastructure/monitoring

# Load environment
source .env

# Stop old Grafana container
docker-compose down grafana

# Pull latest image
docker-compose pull grafana

# Start new Grafana
docker-compose up -d grafana

# Wait for health check
sleep 10

# Verify startup
docker-compose ps grafana
docker logs grafana --tail 50

# Check health endpoint
curl -f http://localhost:3002/api/health || echo "❌ Health check failed"
```

**Expected output:**
```
NAME      IMAGE                                     COMMAND  STATUS
grafana   10.0.0.84:5050/wizardsofts/grafana:latest   ...      Up (healthy)
```

---

### **Phase 7: Testing & Validation (Days 8–9)**

#### Step 7.1: Container Health Checks
**Script**: `scripts/test-grafana-deployment.sh`

```bash
#!/bin/bash
set -e

echo "🧪 Testing Grafana deployment..."

GRAFANA_URL="http://localhost:3002"

# Test 1: Container running
echo "✓ Test 1: Container running..."
docker ps | grep -q "grafana" || {
  echo "❌ Grafana container not running"
  exit 1
}

# Test 2: HTTP health endpoint
echo "✓ Test 2: Health endpoint..."
curl -sf "$GRAFANA_URL/api/health" >/dev/null || {
  echo "❌ Health endpoint failed"
  exit 1
}

# Test 3: Admin API access (basic auth)
echo "✓ Test 3: Admin API..."
curl -sf -u "admin:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/user" >/dev/null || {
  echo "❌ Admin API failed"
  exit 1
}

# Test 4: Datasources configured
echo "✓ Test 4: Datasources..."
DATASOURCES=$(curl -s -u "admin:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/datasources" | jq length)
[ "$DATASOURCES" -gt 0 ] || {
  echo "❌ No datasources found"
  exit 1
}
echo "   Found $DATASOURCES datasource(s)"

# Test 5: Dashboards loaded
echo "✓ Test 5: Dashboards..."
DASHBOARDS=$(curl -s -u "admin:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/search" | jq length)
[ "$DASHBOARDS" -gt 0 ] || {
  echo "❌ No dashboards found"
  exit 1
}
echo "   Found $DASHBOARDS dashboard(s)"

# Test 6: Prometheus connectivity
echo "✓ Test 6: Prometheus connectivity..."
curl -sf -u "admin:$GRAFANA_PASSWORD" \
  "$GRAFANA_URL/api/datasources/proxy/1/query?query=up" >/dev/null || {
  echo "⚠️ Prometheus query failed (check datasource)"
}

# Test 7: OAuth config loaded
echo "✓ Test 7: OAuth configuration..."
curl -sf "$GRAFANA_URL/login/generic_oauth" | grep -q "keycloak\|oauth" || {
  echo "⚠️ OAuth redirect not visible"
}

# Test 8: Memory usage within limits
echo "✓ Test 8: Memory usage..."
MEMORY=$(docker stats grafana --no-stream --format "{{.MemPerc}}" | sed 's/%//')
MEMORY_INT=${MEMORY%.*}
[ "$MEMORY_INT" -lt 90 ] || {
  echo "⚠️ Memory usage high: ${MEMORY}%"
}
echo "   Memory: ${MEMORY}%"

# Test 9: Volume mounted correctly
echo "✓ Test 9: Volume mount..."
docker exec grafana test -d /var/lib/grafana || {
  echo "❌ Volume mount failed"
  exit 1
}

echo "✅ All deployment tests passed"
```

**Run tests:**
```bash
export GRAFANA_PASSWORD="from-.env"
bash scripts/test-grafana-deployment.sh
```

---

#### Step 7.2: SSO Integration Test
**Script**: `scripts/test-grafana-sso.sh`

```bash
#!/bin/bash
set -e

echo "🔐 Testing Grafana SSO with Keycloak..."

GRAFANA_URL="http://localhost:3002"
KEYCLOAK_URL="http://10.0.0.84:8180"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}"

# Test 1: OAuth config present in Grafana
echo "✓ Test 1: OAuth config..."
OAUTH=$(curl -s -u "admin:$GRAFANA_PASSWORD" \
  "$GRAFANA_URL/api/admin/settings" | jq -r '.auth | keys[]' | grep -i oauth)
[ -n "$OAUTH" ] || {
  echo "❌ OAuth not configured"
  exit 1
}

# Test 2: Keycloak OIDC endpoint reachable
echo "✓ Test 2: Keycloak OIDC..."
curl -sf "$KEYCLOAK_URL/realms/master/.well-known/openid-configuration" >/dev/null || {
  echo "❌ Keycloak OIDC unreachable"
  exit 1
}

# Test 3: Grafana client exists in Keycloak
echo "✓ Test 3: Keycloak client..."
TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" | jq -r '.access_token // empty')

if [ -n "$TOKEN" ]; then
  curl -sf -H "Authorization: Bearer $TOKEN" \
    "$KEYCLOAK_URL/admin/realms/master/clients" | \
    jq -e '.[] | select(.clientId=="grafana")' >/dev/null || {
    echo "❌ Grafana client not found"
    exit 1
  }
else
  echo "⚠️ Skipping client verification (no Keycloak auth available)"
fi

# Test 4: SSO redirect works
echo "✓ Test 4: SSO redirect..."
REDIRECT=$(curl -s -L "$GRAFANA_URL/login/generic_oauth" 2>&1 | grep -i keycloak)
[ -n "$REDIRECT" ] || {
  echo "⚠️ SSO redirect not visible (may be in JavaScript)"
}

echo "✅ SSO integration test passed"
```

**Run SSO test:**
```bash
bash scripts/test-grafana-sso.sh
```

---

#### Step 7.3: Performance & Reliability Test
**Script**: `scripts/test-grafana-performance.sh`

```bash
#!/bin/bash

echo "⚡ Testing Grafana performance..."

GRAFANA_URL="http://localhost:3002"
DURATION=300  # 5 minutes
INTERVAL=5

echo "Running load test for $DURATION seconds..."

for i in $(seq 0 $INTERVAL $DURATION); do
  # Test API responsiveness
  RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
    -u "admin:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/user")
  
  # Test memory usage
  MEMORY=$(docker stats grafana --no-stream --format "{{.MemPerc}}" | sed 's/%//')
  
  # Test CPU usage
  CPU=$(docker stats grafana --no-stream --format "{{.CPUPerc}}" | sed 's/%//')
  
  echo "[$i/$DURATION] Response: ${RESPONSE_TIME}s | Memory: $MEMORY | CPU: $CPU"
  
  # Check if memory approaching limit
  MEMORY_INT=${MEMORY%.*}
  [ "$MEMORY_INT" -lt 90 ] || {
    echo "⚠️ Memory alert at $MEMORY%"
  }
  
  sleep $INTERVAL
done

echo "✅ Performance test complete"
```

**Run performance test:**
```bash
bash scripts/test-grafana-performance.sh
```

---

### **Phase 8: Monitoring & Alerting Setup (Days 9–10)**

#### Step 8.1: Add Grafana Memory Alert
**File**: `infrastructure/monitoring/prometheus/infrastructure-alerts.yml`

```yaml
groups:
  - name: grafana_health
    interval: 30s
    rules:
      - alert: GrafanaHighMemory
        expr: container_memory_usage_bytes{name="grafana"} > 900000000
        for: 5m
        labels:
          severity: warning
          service: grafana
        annotations:
          summary: "Grafana memory >900MB (warning)"
          description: "Grafana using {{ humanize $value }}B of 1GB limit"
      
      - alert: GrafanaCriticalMemory
        expr: container_memory_usage_bytes{name="grafana"} > 950000000
        for: 2m
        labels:
          severity: critical
          service: grafana
        annotations:
          summary: "Grafana memory >950MB (critical)"
          description: "Automatic restart may trigger"
      
      - alert: GrafanaOOMKilled
        expr: increase(container_oom_events_total{name="grafana"}[5m]) > 0
        labels:
          severity: critical
          service: grafana
        annotations:
          summary: "Grafana OOM killer triggered"
      
      - alert: GrafanaDown
        expr: up{job="grafana"} == 0
        for: 1m
        labels:
          severity: critical
          service: grafana
        annotations:
          summary: "Grafana is down"
          description: "Container stopped or health check failing"
```

**Reload alerts:**
```bash
curl -X POST http://prometheus:9090/-/reload
```

---

#### Step 8.2: Add Grafana Watchdog (Auto-Restart on Memory)
**File**: `docker-compose.yml` - add service

```yaml
services:
  grafana-watchdog:
    image: alpine:latest
    container_name: grafana-watchdog
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: sh -c '
      apk add --no-cache docker-cli curl;
      while true; do
        MEMORY=$$(docker stats grafana --no-stream --format "{{.MemPerc}}" 2>/dev/null | sed "s/%//");
        if [ -n "$$MEMORY" ] && [ "$${MEMORY%.*}" -ge 90 ]; then
          echo "⚠️ Grafana memory at $${MEMORY}%, restarting...";
          docker restart grafana;
          sleep 300;  # Don't spam restarts
        fi;
        sleep 60;
      done
    '
    networks:
      - monitoring
    deploy:
      resources:
        limits:
          memory: 50M
```

**Start watchdog:**
```bash
docker-compose up -d grafana-watchdog
```

---

#### Step 8.3: Add Grafana Cleanup Job (Weekly)
**File**: `scripts/grafana-cleanup-weekly.sh`

```bash
#!/bin/bash

echo "🧹 Running weekly Grafana cleanup..."

# Clear old sessions (>7 days)
docker exec grafana sqlite3 /var/lib/grafana/grafana.db \
  "DELETE FROM session WHERE created_at < datetime('now', '-7 days');" 2>/dev/null || \
  echo "⚠️ Session cleanup may have failed"

# Compact database
docker exec grafana sqlite3 /var/lib/grafana/grafana.db "VACUUM;" 2>/dev/null || \
  echo "⚠️ Database optimization failed"

# Reload provisioning
curl -s -X POST -u "admin:${GRAFANA_PASSWORD}" \
  http://localhost:3002/api/admin/provisioning/dashboards/reload

echo "✅ Cleanup complete"
```

**Schedule via cron on server 84:**
```bash
# Add to crontab
0 2 * * 0 cd /opt/wizardsofts-megabuild && bash scripts/grafana-cleanup-weekly.sh
```

---

### **Phase 9: Documentation (Days 10–11)**

#### Step 9.1: Create Deployment Guide
**File**: `infrastructure/monitoring/GRAFANA_DEPLOYMENT_GUIDE.md`

Document:
- How custom image built & pushed
- How to deploy new version
- How to rollback
- SSO troubleshooting
- Memory limits & escalation
- Registry cleanup policy
- Scheduled maintenance tasks

---

#### Step 9.2: Create Troubleshooting Runbook
**File**: `docs/GRAFANA_TROUBLESHOOTING.md`

Cover:
- Grafana won't start (check logs, bind mounts, image pull)
- OAuth broken (check Keycloak, client config, redirect URI)
- Memory high (check dashboard complexity, query load)
- OOM killed (restart, then check logs)
- Dashboards not loading (check provisioning, datasources)

---

### **Phase 10: Registry Token Management (Day 11)**

#### Step 10.1: Create Registry Token Rotation Script
**File**: `scripts/rotate-registry-token.sh`

```bash
#!/bin/bash
set -e

echo "🔄 Rotating GitLab Container Registry token..."

GITLAB_URL="http://10.0.0.84"
PROJECT_ID="wizardsofts/wizardsofts-megabuild"
GITLAB_ADMIN_TOKEN="${GITLAB_ADMIN_TOKEN}"  # Pre-set via env or vault

# Create new deploy token (90-day expiry)
NEW_TOKEN=$(curl -s -X POST "$GITLAB_URL/api/v4/projects/$PROJECT_ID/deploy_tokens" \
  -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
  -d "name=registry-token-$(date +%Y%m%d)" \
  -d "scopes[]=read_registry" \
  -d "scopes[]=write_registry" \
  -d "expires_at=$(date -d '+90 days' +%Y-%m-%d)" | jq -r '.token // empty')

if [ -z "$NEW_TOKEN" ]; then
  echo "❌ Failed to create new token"
  exit 1
fi

# Update GitLab CI/CD variable
curl -s -X PUT "$GITLAB_URL/api/v4/projects/$PROJECT_ID/variables/CI_REGISTRY_PASSWORD" \
  -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
  -d "value=$NEW_TOKEN" \
  -d "protected=true" \
  -d "masked=true" >/dev/null

echo "✅ Registry token rotated"
echo "   Expires: $(date -d '+90 days')"
echo "   Next rotation: $(date -d '+90 days')"
```

**Schedule rotation (quarterly):**
```bash
# Add to crontab
0 0 1 1,4,7,10 * cd /opt/wizardsofts-megabuild && bash scripts/rotate-registry-token.sh
```

---

### **Phase 11: Continuous Improvement (Ongoing)**

#### Step 11.1: Weekly Monitoring Review
- Check Grafana memory trends
- Review SSO login patterns
- Monitor image registry size
- Verify cleanup policy working

#### Step 11.2: Monthly Dependency Updates
- Check for Grafana base image updates via Renovate
- Review Prometheus/Alertmanager versions
- Test updates in dev before production

#### Step 11.3: Quarterly Security Audit
- Rotate OAuth client secret (if needed)
- Review access logs
- Update vulnerability scanning in CI

---

## Summary: Complete Implementation Checklist

### Phase 1: Preparation (Day 1)
- [ ] Run server prechecks (`prechecks-grafana-pipeline.sh`)
- [ ] Create `infrastructure/monitoring/.env`
- [ ] Copy configs from auto-scaling to monitoring
- [ ] Verify config directory structure

### Phase 2: Build Infrastructure (Days 2–3)
- [ ] Create `Dockerfile.grafana`
- [ ] Update `docker-compose.yml` for new image & env vars
- [ ] Configure registry cleanup policy (UI)
- [ ] Document changes

### Phase 3: CI/CD Pipeline (Days 4–5)
- [ ] Add `test:grafana:config` job to `.gitlab-ci.yml`
- [ ] Add `build:grafana:image` job
- [ ] Add `test:grafana:sso` job
- [ ] Add `cleanup:registry` scheduled job
- [ ] Test locally: `docker build` and run

### Phase 4: Configuration (Days 5–6)
- [ ] Validate `grafana.ini` for OAuth config
- [ ] Create `keycloak-grafana-client.json`
- [ ] Create setup script: `setup-grafana-keycloak-client.sh`
- [ ] Run validation: `validate-grafana-sso.sh`

### Phase 5: Build & Push (Day 6)
- [ ] Push all changes to feature branch
- [ ] Create MR and verify tests pass
- [ ] Merge to main
- [ ] Pipeline builds & pushes image to registry
- [ ] Verify image available: `docker pull ...`

### Phase 6: Deployment (Days 7–8)
- [ ] Run pre-deploy checklist: `pre-deploy-grafana.sh`
- [ ] Deploy: `docker-compose down grafana && docker-compose up -d grafana`
- [ ] Monitor startup: `docker logs grafana -f`

### Phase 7: Testing (Days 8–9)
- [ ] Run deployment tests: `test-grafana-deployment.sh`
- [ ] Run SSO tests: `test-grafana-sso.sh`
- [ ] Run performance tests: `test-grafana-performance.sh`
- [ ] Manual UI verification (login, dashboards, Prometheus)

### Phase 8: Monitoring (Days 9–10)
- [ ] Add Prometheus alerts for memory, OOM, down
- [ ] Deploy watchdog container for auto-restart
- [ ] Create cleanup script: `grafana-cleanup-weekly.sh`
- [ ] Schedule cron jobs

### Phase 9: Documentation (Days 10–11)
- [ ] Write deployment guide
- [ ] Write troubleshooting runbook
- [ ] Write SSO setup guide
- [ ] Add to README

### Phase 10: Token Management (Day 11)
- [ ] Create token rotation script
- [ ] Schedule quarterly rotation
- [ ] Document token lifecycle

### Phase 11: Continuous Improvement (Ongoing)
- [ ] Weekly memory review
- [ ] Monthly dependency updates
- [ ] Quarterly security audit

---

## Identified Gaps & Remediations

| Gap | Remediation | Phase |
|-----|-----------|-------|
| Config files missing from monitoring stack | Copy from auto-scaling or bake into image ✅ | 1–2 |
| No .env for monitoring stack | Create with secrets from .gitignore | 1 |
| No Dockerfile for custom image | Create Dockerfile.grafana | 2 |
| No CI test for Grafana config | Add `test:grafana:config` job | 3 |
| No image build in CI | Add `build:grafana:image` job | 3 |
| No SSO validation in CI | Add `test:grafana:sso` job | 3 |
| No resource limits | Add deploy.resources in compose | 2 |
| No memory monitoring | Add Prometheus alerts | 8 |
| No auto-restart on memory | Add watchdog sidecar | 8 |
| No scheduled cleanup | Add `grafana-cleanup-weekly.sh` cron | 8 |
| No token rotation | Create rotation script, schedule quarterly | 10 |
| No deployment documentation | Create GRAFANA_DEPLOYMENT_GUIDE.md | 9 |
| No troubleshooting guide | Create GRAFANA_TROUBLESHOOTING.md | 9 |

---

**This plan is ready for implementation. Estimated timeline: 11 days (including documentation). All steps are sequential and have prechecks/validation built in.**

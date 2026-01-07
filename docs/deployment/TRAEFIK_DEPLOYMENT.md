# Traefik Deployment & Security Guide

> **Version:** 2.0
> **Last Updated:** 2026-01-07
> **Status:** Production Configuration

**Related Documentation:**
- [Traefik Security Concepts](TRAEFIK_SECURITY_GUIDE.md) - Why Traefik is better than direct port exposure
- [Traefik Migration](../archive/migrations/TRAEFIK_CONFIG_MIGRATION.md) - Historical migration notes

---

## Quick Reference

```bash
# Restart Traefik
ssh agent@10.0.0.84 "sudo docker restart traefik"

# View logs
ssh agent@10.0.0.84 "docker logs traefik -f --tail 100"

# Check routing
ssh agent@10.0.0.84 "docker exec traefik traefik healthcheck"
```

---

## Phase 1: Critical Fixes

### Step 1.1: Secure Password Management

**Goal**: Move passwords out of .env file

#### Option A: Using Docker Secrets (Recommended for Swarm)

```bash
# Create secrets directory
mkdir -p /opt/wizardsofts-megabuild/secrets
chmod 700 /opt/wizardsofts-megabuild/secrets

# Generate strong passwords
openssl rand -base64 32 > /opt/wizardsofts-megabuild/secrets/db_password.txt
openssl rand -base64 32 > /opt/wizardsofts-megabuild/secrets/redis_password.txt
openssl rand -base64 32 > /opt/wizardsofts-megabuild/secrets/traefik_dashboard_password.txt

# Generate Traefik auth hashes
# For Basic Auth
docker run --rm httpd htpasswd -Bbc /dev/stdout admin $(openssl rand -base64 12) | \
  awk '{print $1}' > /opt/wizardsofts-megabuild/secrets/traefik_admin_auth.txt

# Update docker-compose.yml
cat >> docker-compose.prod.yml << 'EOF'

secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
  traefik_dashboard_auth:
    file: ./secrets/traefik_dashboard_auth.txt
  traefik_dashboard_password:
    file: ./secrets/traefik_dashboard_password.txt

services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

  redis:
    command: redis-server --requirepass $(cat /run/secrets/redis_password)
    secrets:
      - redis_password

  traefik:
    secrets:
      - traefik_dashboard_auth
    environment:
      TRAEFIK_API_DASHBOARD_PASSWORD_FILE: /run/secrets/traefik_dashboard_password
EOF

# Add secrets to .gitignore
echo "secrets/" >> .gitignore
```

#### Option B: Using HashiCorp Vault (Recommended for Complex Deployments)

```bash
# Install Vault on server
curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
apt-get update && apt-get install vault

# Initialize Vault
vault server -dev &
export VAULT_ADDR='http://127.0.0.1:8200'
vault login

# Store secrets
vault kv put secret/wizardsofts/db \
  password="$(openssl rand -base64 32)" \
  username="gibd"

vault kv put secret/wizardsofts/redis \
  password="$(openssl rand -base64 32)"

vault kv put secret/wizardsofts/traefik \
  admin_user="admin" \
  admin_password="$(openssl rand -base64 32)" \
  dashboard_password="$(openssl rand -base64 32)"

# Access in application
vault kv get -field=password secret/wizardsofts/db
```

#### Option C: AWS Secrets Manager (If running on AWS)

```bash
# Store secrets in AWS
aws secretsmanager create-secret \
  --name wizardsofts/db/postgres \
  --secret-string '{"username":"gibd","password":"'$(openssl rand -base64 32)'"}'

aws secretsmanager create-secret \
  --name wizardsofts/redis/password \
  --secret-string $(openssl rand -base64 32)

# Retrieve in deployment script
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id wizardsofts/db/postgres \
  --query SecretString --output text | jq -r '.password')
```

---

### Step 1.2: Enable Docker Socket Proxy

**Goal**: Restrict Traefik's Docker socket access

#### Update traefik/traefik.yml

```yaml
# Before:
providers:
  docker:
    swarmMode: false
    exposedByDefault: false
    network: wizardsofts-megabuild_gibd-network

# After:
providers:
  docker:
    swarmMode: false
    exposedByDefault: false
    network: wizardsofts-megabuild_gibd-network
    endpoint: "tcp://socket-proxy:2375"  # ✅ Use socket-proxy
    watch: true
```

#### Verify Socket Proxy Configuration

In [docker-compose.infrastructure.yml](docker-compose.infrastructure.yml):

```yaml
socket-proxy:
  image: tecnativa/docker-socket-proxy:latest
  container_name: socket-proxy
  environment:
    # Read-only access ONLY
    CONTAINERS: 1       # Allow container info
    NETWORKS: 1         # Allow network info
    EVENTS: 1           # Allow event stream
    # Deny everything else
    POST: 0             # ✅ Critical - no write operations
    IMAGES: 0
    VOLUMES: 0
    SERVICES: 0
    NODES: 0
    SWARM: 0
    SECRETS: 0
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
  read_only: true
  tmpfs:
    - /run
```

#### Test Socket Proxy

```bash
# Test read access (should work)
curl -s http://localhost:2375/v1.40/containers/json | python3 -m json.tool

# Test write access (should FAIL)
curl -X POST http://localhost:2375/v1.40/containers/create \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine"}'
# Expected: 403 Forbidden
```

---

### Step 1.3: Replace Basic Auth with OAuth2/Keycloak

**Goal**: Implement secure authentication for admin endpoints

#### Option A: OAuth2 Proxy

```yaml
# docker-compose.infrastructure.yml

oauth2-proxy:
  image: oauth2-proxy/oauth2-proxy:latest
  container_name: oauth2-proxy
  ports:
    - "127.0.0.1:4180:4180"  # Localhost only
  environment:
    OAUTH2_PROXY_PROVIDER: "oidc"
    OAUTH2_PROXY_OIDC_ISSUER_URL: "https://keycloak.wizardsofts.com/realms/master"
    OAUTH2_PROXY_CLIENT_ID: ${OAUTH2_CLIENT_ID}
    OAUTH2_PROXY_CLIENT_SECRET: ${OAUTH2_CLIENT_SECRET}
    OAUTH2_PROXY_COOKIE_SECRET: $(python3 -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())')
    OAUTH2_PROXY_REDIRECT_URL: "https://traefik.wizardsofts.com/oauth2/callback"
    OAUTH2_PROXY_UPSTREAMS: "http://127.0.0.1:8080"
    OAUTH2_PROXY_REVERSE_PROXY: "true"
    OAUTH2_PROXY_COOKIE_SECURE: "true"
    OAUTH2_PROXY_COOKIE_HTTPONLY: "true"
    OAUTH2_PROXY_COOKIE_SAMESITE: "Lax"
  networks:
    - traefik-public
    - backend
  depends_on:
    - keycloak
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.oauth2.rule=Host(`traefik.wizardsofts.com`)"
    - "traefik.http.routers.oauth2.entrypoints=websecure"
    - "traefik.http.routers.oauth2.tls.certresolver=letsencrypt"
    - "traefik.http.services.oauth2.loadbalancer.server.port=4180"
```

#### Update traefik/dynamic_conf.yml

```yaml
# Remove basic auth for dashboard
routers:
  dashboard:
    rule: Host(`traefik.wizardsofts.com`) || Host(`traefik.localhost`) || Host(`10.0.0.84`)
    service: api@internal
    entryPoints:
      - websecure
    tls:
      certResolver: letsencrypt
    middlewares:
      - oauth-auth  # ✅ Use OAuth instead of basicAuth

middlewares:
  oauth-auth:
    forwardAuth:
      address: "http://oauth2-proxy:4180"
      trustForwardHeader: true
      authResponseHeaders:
        - Authorization
        - X-Auth-Request-User
        - X-Auth-Request-Email
```

#### Option B: Keycloak Forward Auth

```yaml
# traefik/dynamic_conf.yml

middlewares:
  keycloak-auth:
    forwardAuth:
      address: "http://keycloak:8080/realms/master/protocol/openid-connect/userinfo"
      trustForwardHeader: true
      authResponseHeaders:
        - Authorization
        - X-Remote-User
        - X-Remote-Groups
      authRequestHeaders:
        - Authorization

routers:
  dashboard:
    middlewares:
      - keycloak-auth
      - global-security-headers
```

---

### Step 1.4: Add Global Security Headers

**Goal**: Implement security headers across all routes

Create [traefik/security-headers.yml](traefik/security-headers.yml):

```yaml
# Traefik security headers configuration
http:
  middlewares:
    global-security-headers:
      headers:
        customResponseHeaders:
          # Prevent MIME type sniffing
          X-Content-Type-Options: "nosniff"
          
          # Clickjacking protection
          X-Frame-Options: "SAMEORIGIN"
          
          # XSS protection
          X-XSS-Protection: "1; mode=block"
          
          # HSTS (enable after testing)
          Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
          
          # Referrer policy
          Referrer-Policy: "strict-origin-when-cross-origin"
          
          # Permissions policy
          Permissions-Policy: "geolocation=(), microphone=(), camera=(), payment=(), usb=(), accelerometer=(), ambient-light-sensor=(), autoplay=(), gyroscope=(), magnetometer=(), midi=(), picture-in-picture=(), sync-xhr=(), vr=()"
          
          # Disable caching for sensitive data
          Cache-Control: "public, max-age=3600, must-revalidate"
          Pragma: "no-cache"
          Expires: "0"
        
        customRequestHeaders:
          X-Forwarded-Proto: "https"
          X-Forwarded-For: "${REMOTE_ADDR}"
          X-Real-IP: "${REMOTE_ADDR}"

    # Strict CSP for applications (adjust as needed)
    csp-strict:
      headers:
        customResponseHeaders:
          Content-Security-Policy: "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' api.wizardsofts.com; frame-ancestors 'none'"

# Apply to all routes
routers:
  wizardsofts-web:
    middlewares:
      - global-security-headers
      - rate-limit

  api-gateway:
    middlewares:
      - global-security-headers
      - api-rate-limit

  traefik-dashboard:
    middlewares:
      - global-security-headers
      - oauth-auth
```

Update [traefik/traefik.yml](traefik/traefik.yml) to include this:

```yaml
providers:
  file:
    filename: /etc/traefik/dynamic_conf.yml
    watch: true
  # Add security headers config
  file:
    directory: /etc/traefik
    watch: true
```

---

## Phase 2: Fix Configuration Issues (Week 2-3)

### Step 2.1: Fix CORS Configuration

**Goal**: Remove wildcard domains

Update [traefik/dynamic_conf.yml](traefik/dynamic_conf.yml):

```yaml
# Before:
appwrite-cors:
  headers:
    accessControlAllowOriginList:
      - "https://*.wizardsofts.com"  # ❌ Too permissive

# After:
appwrite-cors:
  headers:
    accessControlAllowOriginList:
      - "https://www.wizardsofts.com"
      - "https://app.wizardsofts.com"
      - "https://admin.wizardsofts.com"
      - "https://www.bondwala.com"
      - "https://app.bondwala.com"
      - "https://quant.wizardsofts.com"
      # Explicitly list all allowed origins
    accessControlAllowMethods:
      - GET
      - POST
      - PUT
      - DELETE
      - PATCH
      - OPTIONS
    accessControlAllowHeaders:
      - Content-Type
      - X-Appwrite-Project
      - X-Appwrite-Key
      - X-Appwrite-Response-Format
      - Authorization
    accessControlExposeHeaders:
      - X-Total-Count
      - X-Total-Time
    accessControlMaxAge: 3600  # ✅ Reduced from 86400
    accessControlAllowCredentials: true
```

---

### Step 2.2: Implement Strict Rate Limiting

**Goal**: Protect authentication endpoints from brute force

Update [traefik/dynamic_conf.yml](traefik/dynamic_conf.yml):

```yaml
middlewares:
  # Strict rate limiting for authentication
  auth-rate-limit:
    rateLimit:
      average: 5           # 5 requests per second
      burst: 2             # Maximum 2 burst requests
      period: 1m           # Per minute
      sourceStrategy: "ip"
      
  # Keycloak login protection
  keycloak-login-limit:
    rateLimit:
      average: 3           # 3 attempts per minute
      burst: 1             # No burst allowed
      period: 1m
      
  # Dashboard protection
  dashboard-rate-limit:
    rateLimit:
      average: 30          # 30 requests per minute
      burst: 5
      period: 1m
      
  # API rate limiting
  api-rate-limit:
    rateLimit:
      average: 100         # 100 requests per second
      burst: 20
      period: 1s

routers:
  # Apply strict limits to auth
  keycloak-guardian:
    rule: Host(`auth.guardianinvestmentbd.com`)
    service: keycloak
    entryPoints:
      - websecure
    tls:
      certResolver: letsencrypt
    middlewares:
      - keycloak-login-limit       # ✅ Strict limit
      - keycloak-security-headers

  # Apply to dashboard
  dashboard:
    rule: Host(`traefik.wizardsofts.com`)
    service: api@internal
    entryPoints:
      - websecure
    tls:
      certResolver: letsencrypt
    middlewares:
      - dashboard-rate-limit       # ✅ Strict limit
      - oauth-auth
      - global-security-headers

  # Standard APIs
  api-gateway:
    rule: Host(`api.wizardsofts.com`)
    service: api-gateway
    entryPoints:
      - websecure
    middlewares:
      - api-rate-limit
      - global-security-headers
```

---

### Step 2.3: Add Health Check Monitoring

**Goal**: Ensure services are ready before routing traffic

Update [docker-compose.yml](docker-compose.yml):

```yaml
ws-gateway:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 30s    # ✅ Wait for startup

  labels:
    - "traefik.enable=true"
    - "traefik.http.services.gateway.loadbalancer.healthcheck.path=/actuator/health"
    - "traefik.http.services.gateway.loadbalancer.healthcheck.interval=10s"

ws-trades:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8182/actuator/health"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 30s

ws-company:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8183/actuator/health"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 30s

ws-news:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8184/actuator/health"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 30s
```

---

## Phase 3: Implement CI/CD Security (Week 3-4)

### Step 3.1: Setup Secure GitLab CI/CD

**Goal**: Automate deployments with security scanning

#### Create .gitlab-ci.yml overrides:

```yaml
include:
  - local: '.gitlab/ci/security.gitlab-ci.yml'
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml

stages:
  - validate
  - scan
  - build
  - deploy
  - verify

# Scan for hardcoded credentials
validate-config:
  stage: validate
  image: python:3.11-slim
  script:
    - pip install detect-secrets
    - detect-secrets scan --baseline .secrets.baseline
    - |
      if [ $? -ne 0 ]; then
        echo "Hardcoded secrets detected!"
        exit 1
      fi
  allow_failure: false

# Container image scanning
scan-images:
  stage: scan
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1
  allow_failure: true

# SAST scanning
sast-scan:
  stage: scan
  image: returntocorp/semgrep
  script:
    - semgrep --config=p/security-audit --json --output=sast-results.json
  artifacts:
    reports:
      sast: sast-results.json

# Secure deployment
deploy-production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client git curl
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts
  script:
    - |
      ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST << 'DEPLOY'
      set -e
      cd /opt/wizardsofts-megabuild
      
      # Backup current state
      BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"
      mkdir -p "$BACKUP_DIR"
      docker-compose config > "$BACKUP_DIR/compose-backup.yml"
      
      # Pull latest code
      git pull origin $CI_COMMIT_REF_NAME
      
      # Deploy
      docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
      docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
      
      # Health check
      sleep 20
      if ! curl -f https://api.wizardsofts.com/health; then
        echo "Health check failed - rolling back"
        exit 1
      fi
      
      echo "Deployment successful at $BACKUP_DIR"
      DEPLOY
  environment:
    name: production
    url: https://www.wizardsofts.com
  when: manual
  only:
    - main
```

#### Register GitLab Runner:

```bash
# On deployment server
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | bash
apt-get install gitlab-runner

# Register with restricted permissions
sudo gitlab-runner register \
  --url https://gitlab.com/ \
  --registration-token $YOUR_TOKEN \
  --executor shell \
  --shell bash \
  --locked true \
  --access-level ref_protected \
  --description "Production Deployer"

# Configure runner security
sudo usermod -aG docker gitlab-runner
```

---

### Step 3.2: Setup Secrets Management

**Goal**: Secure credential storage in GitLab

In GitLab UI:
1. Go to **Settings → CI/CD → Variables**
2. Add these Protected and Masked variables:

```
Variable Name                  | Type    | Protected | Masked | Value
-------------------------------|---------|-----------|--------|--------
SSH_PRIVATE_KEY               | File    | Yes       | No     | [private key]
DEPLOY_SUDO_PASSWORD          | Var     | Yes       | Yes    | [password]
DB_PASSWORD                   | Var     | Yes       | Yes    | [db password]
REDIS_PASSWORD                | Var     | Yes       | Yes    | [redis password]
TRAEFIK_ADMIN_PASSWORD        | Var     | Yes       | Yes    | [traefik password]
KEYCLOAK_ADMIN_PASSWORD       | Var     | Yes       | Yes    | [keycloak password]
APPWRITE_SECRET_KEY           | Var     | Yes       | Yes    | [secret key]
OPENAI_API_KEY                | Var     | Yes       | Yes    | [api key]
DOCKER_REGISTRY_PASSWORD      | Var     | Yes       | Yes    | [docker pwd]
```

Never store in `.gitlab-ci.yml`!

---

## Phase 4: Advanced Security (Month 2+)

### Step 4.1: Implement mTLS Between Services

**Goal**: Encrypt service-to-service communication

```yaml
# Update services to use HTTPS
services:
  ws-gateway:
    environment:
      SERVER_SSL_ENABLED: "true"
      SERVER_SSL_KEY_STORE: "/etc/ssl/certs/keystore.jks"
      SERVER_SSL_KEY_STORE_PASSWORD: "${SSL_KEYSTORE_PASSWORD}"
      SERVER_SSL_KEY_STORE_TYPE: "JKS"

  traefik:
    volumes:
      - ./certs:/etc/traefik/certs:ro
    environment:
      - TLS_KEY=/etc/traefik/certs/traefik-key.pem
      - TLS_CERT=/etc/traefik/certs/traefik-cert.pem
```

Generate certificates:
```bash
# Generate CA
openssl genrsa -out ca-key.pem 2048
openssl req -new -x509 -days 3650 -key ca-key.pem -out ca.pem

# Generate service certificates
openssl genrsa -out traefik-key.pem 2048
openssl req -new -key traefik-key.pem -out traefik.csr
openssl x509 -req -days 365 -in traefik.csr \
  -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out traefik-cert.pem
```

---

### Step 4.2: Add Intrusion Detection

**Goal**: Monitor for suspicious activity

```yaml
# Use Falco for container runtime security
falco:
  image: falcosecurity/falco:latest
  container_name: falco
  privileged: true
  volumes:
    - /var/run/docker.sock:/host/var/run/docker.sock:ro
    - /etc:/host/etc:ro
    - /lib:/host/lib:ro
    - /usr:/host/usr:ro
    - /var:/host/var:ro
    - /proc:/host/proc:ro
  command: [
    "falco",
    "-o", "file_output.enabled=true",
    "-o", "file_output.filename=/var/log/falco/alerts.log"
  ]
  volumes:
    - falco-logs:/var/log/falco
```

---

## Testing & Validation

### Test Security Headers

```bash
# Check security headers
curl -I https://api.wizardsofts.com | grep -E "X-|Strict|Content-Security"

# Expected output:
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

### Test Rate Limiting

```bash
# Trigger rate limit (should succeed)
for i in {1..5}; do curl https://auth.wizardsofts.com/login; done

# Continue past limit (should get 429)
for i in {1..100}; do curl https://auth.wizardsofts.com/login; done
# Should see: HTTP/1.1 429 Too Many Requests
```

### Test Authentication

```bash
# Try to access dashboard without auth (should fail)
curl -v https://traefik.wizardsofts.com/dashboard
# Should redirect to OAuth login

# With auth token (should succeed)
curl -H "Authorization: Bearer $TOKEN" https://traefik.wizardsofts.com/dashboard
```

---

## Rollback Procedures

### Restore from Backup

```bash
# List backups
ls -lh /opt/backups/

# Restore specific backup
BACKUP_DIR="/opt/backups/20250107_120000"
cd /opt/wizardsofts-megabuild
cp "$BACKUP_DIR/docker-compose.yml" .
cp "$BACKUP_DIR/docker-compose.prod.yml" .
cp -r "$BACKUP_DIR/traefik" .

# Redeploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
docker-compose ps
```

---

## Monitoring & Alerting

### Setup Prometheus Alerts

```yaml
# prometheus/rules/traefik-alerts.yml
groups:
  - name: traefik
    rules:
      - alert: TraefikHighErrorRate
        expr: |
          (rate(traefik_entrypoint_requests_total{code=~"5.."}[5m]) / 
           rate(traefik_entrypoint_requests_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "Traefik high error rate"
          
      - alert: TraefikServiceDown
        expr: up{job="traefik"} == 0
        for: 1m
        annotations:
          summary: "Traefik service is down"

      - alert: RateLimitExceeded
        expr: increase(traefik_middleware_ratelimit_exceeded_total[5m]) > 100
        annotations:
          summary: "Rate limit exceeded for {{ $labels.middleware }}"
```

---

## Maintenance Checklist

- [ ] Rotate secrets quarterly
- [ ] Update Traefik version monthly
- [ ] Review security headers quarterly
- [ ] Audit access logs monthly
- [ ] Test rollback procedures monthly
- [ ] Update certificate expiry notifications
- [ ] Review rate limiting rules monthly
- [ ] Backup configuration weekly


# Security & CI/CD Implementation Checklist

**Date**: 2025-12-28
**Server**: 10.0.0.84
**Strategy**: Security First → Remove HAProxy → Enable CI/CD → Verify

---

## Phase 1: Critical Security Fixes (IMMEDIATE)

### 1.1 Network Security - Port Restrictions

**Goal**: Only ports 22, 25, 80, 443 accessible externally. All others local-only.

**Current Exposed Ports (PUBLIC)**:
- ✅ Port 22 (SSH) - Keep public
- ✅ Port 25 (SMTP/Mailcow) - Keep public
- ✅ Port 80 (HTTP/Traefik) - Keep public
- ✅ Port 443 (HTTPS/Traefik) - Keep public
- ❌ Port 5433 (PostgreSQL) - Make local-only
- ❌ Port 6379 (Redis) - Make local-only
- ❌ Port 8080 (Traefik Dashboard) - Make local-only
- ❌ Port 8081 (Gateway) - Make local-only
- ❌ Port 8180 (Keycloak) - Make local-only
- ❌ Port 8182-8184 (Business services) - Make local-only
- ❌ Port 8404 (HAProxy stats) - Will be removed
- ❌ Port 8762 (Eureka) - Make local-only
- ❌ Port 9090 (Prometheus) - Make local-only
- ❌ Port 11434 (HAProxy Ollama) - Will be removed
- ❌ Port 11435 (Ollama) - Make local-only

**Implementation Tasks**:

- [ ] **1.1.1** Update docker-compose.yml - Remove PostgreSQL port mapping
  ```yaml
  # Change from:
  ports:
    - "5433:5432"
  # To:
  # ports:
  #   - "5433:5432"  # Access via SSH tunnel only
  ```

- [ ] **1.1.2** Update docker-compose.yml - Remove Redis port mapping
  ```yaml
  # Change from:
  ports:
    - "6379:6379"
  # To:
  # ports:
  #   - "6379:6379"  # Access via SSH tunnel only
  ```

- [ ] **1.1.3** Update docker-compose.yml - Change all Spring Boot services to localhost-only
  ```yaml
  # Change from:
  ports:
    - "8762:8761"  # Eureka
    - "8081:8080"  # Gateway
    - "8182:8182"  # ws-trades
    - "8183:8183"  # ws-company
    - "8184:8184"  # ws-news
  # To:
  ports:
    - "127.0.0.1:8762:8761"  # Eureka - localhost only
    - "127.0.0.1:8081:8080"  # Gateway - localhost only
    - "127.0.0.1:8182:8182"  # ws-trades - localhost only
    - "127.0.0.1:8183:8183"  # ws-company - localhost only
    - "127.0.0.1:8184:8184"  # ws-news - localhost only
  ```

- [ ] **1.1.4** Update infrastructure/ollama/docker-compose.yml - Localhost-only
  ```yaml
  # Change from:
  ports:
    - "11435:11434"
  # To:
  ports:
    - "127.0.0.1:11435:11434"  # Ollama - localhost only
  ```

- [ ] **1.1.5** Update infrastructure/keycloak/docker-compose.yml - Localhost-only
  ```yaml
  # Change from:
  ports:
    - "8180:8080"
  # To:
  ports:
    - "127.0.0.1:8180:8080"  # Keycloak - localhost only (use Traefik for external)
  ```

- [ ] **1.1.6** Update docker-compose.infrastructure.yml - Localhost-only for Traefik dashboard
  ```yaml
  # Traefik dashboard should be:
  ports:
    - "80:80"
    - "443:443"
    - "127.0.0.1:8080:8080"  # Dashboard - localhost only
  ```

- [ ] **1.1.7** Apply changes - Restart affected services
  ```bash
  cd /opt/wizardsofts-megabuild
  docker-compose up -d postgres redis
  docker-compose up -d ws-discovery ws-gateway ws-trades ws-company ws-news
  cd infrastructure/ollama && docker-compose up -d
  cd ../keycloak && docker-compose up -d
  ```

- [ ] **1.1.8** Configure UFW firewall
  ```bash
  # Install UFW
  sudo apt-get update && sudo apt-get install -y ufw

  # Default policies
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  # Allow public ports
  sudo ufw allow 22/tcp comment 'SSH'
  sudo ufw allow 25/tcp comment 'SMTP'
  sudo ufw allow 80/tcp comment 'HTTP'
  sudo ufw allow 443/tcp comment 'HTTPS'

  # Enable firewall
  sudo ufw --force enable

  # Verify status
  sudo ufw status verbose
  ```

- [ ] **1.1.9** Verify external access blocked
  ```bash
  # From external machine, these should FAIL:
  nc -zv 10.0.0.84 5433   # PostgreSQL - should timeout
  nc -zv 10.0.0.84 6379   # Redis - should timeout
  nc -zv 10.0.0.84 8080   # Traefik dashboard - should timeout

  # From server itself, these should WORK:
  ssh wizardsofts@10.0.0.84 'nc -zv localhost 5433'  # Should succeed
  ssh wizardsofts@10.0.0.84 'nc -zv localhost 6379'  # Should succeed
  ```

- [ ] **1.1.10** Test SSH tunnel access
  ```bash
  # Setup SSH tunnel for PostgreSQL access
  ssh -L 5433:localhost:5433 wizardsofts@10.0.0.84
  # In another terminal:
  psql -h localhost -p 5433 -U gibd  # Should work
  ```

### 1.2 Password Security

- [ ] **1.2.1** Update infrastructure/keycloak/docker-compose.yml - Fix passwords
  ```yaml
  # File: infrastructure/keycloak/docker-compose.yml
  # Change line 28-30 from:
  KC_DB_PASSWORD: password123
  KEYCLOAK_ADMIN: admin
  KEYCLOAK_ADMIN_PASSWORD: admin123

  # To:
  KC_DB_PASSWORD: ${KEYCLOAK_DB_PASSWORD}
  KEYCLOAK_ADMIN: admin
  KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
  ```

- [ ] **1.2.2** Update .env file with strong passwords
  ```bash
  # On server 84:
  cd /opt/wizardsofts-megabuild

  # Add to .env if not exists:
  echo "KEYCLOAK_DB_PASSWORD=W1z4rdS0fts!2025" >> .env
  echo "KEYCLOAK_ADMIN_PASSWORD=W1z4rdS0fts!2025" >> .env

  # Secure .env file
  chmod 600 .env
  ```

- [ ] **1.2.3** Restart Keycloak with new passwords
  ```bash
  cd /opt/wizardsofts-megabuild/infrastructure/keycloak
  docker-compose down
  docker-compose up -d

  # Wait 30s for startup
  sleep 30

  # Verify health
  docker logs keycloak | tail -20
  ```

- [ ] **1.2.4** Enable Redis authentication
  ```yaml
  # docker-compose.yml - Add to redis service:
  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD}
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
  ```

  ```bash
  # .env - Add Redis password
  echo "REDIS_PASSWORD=W1z4rdS0fts!2025" >> .env

  # Restart Redis
  docker-compose up -d redis
  ```

- [ ] **1.2.5** Update Spring Boot services to use Redis password
  ```yaml
  # docker-compose.yml - Add to ws-* services:
  environment:
    - SPRING_REDIS_PASSWORD=${REDIS_PASSWORD}
  ```

### 1.3 Security Hardening

- [ ] **1.3.1** Disable Keycloak dev mode
  ```yaml
  # infrastructure/keycloak/docker-compose.yml
  # Change from:
  command: start-dev
  # To:
  command: start

  # Update environment:
  KC_HOSTNAME_STRICT: "true"
  KC_HTTP_ENABLED: "false"  # HTTPS only via Traefik
  ```

- [ ] **1.3.2** Add container resource limits
  ```yaml
  # docker-compose.yml - Add to high-memory services:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
  ```

- [ ] **1.3.3** Enable log rotation
  ```yaml
  # docker-compose.yml - Add to all services:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  ```

- [ ] **1.3.4** Verify .env not in git
  ```bash
  git check-ignore .env || echo ".env" >> .gitignore
  git add .gitignore
  git commit -m "chore: Ensure .env is gitignored"
  ```

**Phase 1 Verification**:
- [ ] All services still healthy after port changes
- [ ] External access blocked (ports 5433, 6379, 8080, 8180, etc.)
- [ ] Internal access works (localhost connections)
- [ ] Keycloak accessible with new password
- [ ] UFW firewall enabled and configured

---

## Phase 2: Remove HAProxy

### 2.1 HAProxy Removal

- [ ] **2.1.1** Stop HAProxy container
  ```bash
  ssh wizardsofts@10.0.0.84 'docker stop haproxy'
  ```

- [ ] **2.1.2** Verify Ollama still accessible
  ```bash
  ssh wizardsofts@10.0.0.84 'curl -s http://localhost:11435/api/tags'
  # Should return: {"models":[]}
  ```

- [ ] **2.1.3** Remove HAProxy container
  ```bash
  ssh wizardsofts@10.0.0.84 'docker rm haproxy'
  ```

- [ ] **2.1.4** Update documentation
  ```markdown
  # DEPLOYMENT_STATUS_REPORT_84.md
  # Update HAProxy status:
  - HAProxy (Ollama LB) | - | 11434 | TCP | ❌ Removed (single-server deployment)
  ```

- [ ] **2.1.5** Check if HAProxy has docker-compose file
  ```bash
  ssh wizardsofts@10.0.0.84 'find /opt -name "*haproxy*" -type f 2>/dev/null'
  ```

- [ ] **2.1.6** Remove HAProxy docker-compose if exists
  ```bash
  # If found, remove the directory
  ssh wizardsofts@10.0.0.84 'rm -rf /opt/wizardsofts-megabuild/infrastructure/haproxy'
  ```

**Phase 2 Verification**:
- [ ] HAProxy container removed
- [ ] Port 11434 no longer in use
- [ ] Ollama accessible on localhost:11435
- [ ] All other services unaffected

---

## Phase 3: Enable CI/CD Pipeline

### 3.1 GitLab Runner Setup

- [ ] **3.1.1** Install GitLab Runner on server 84
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  # Download GitLab Runner
  sudo curl -L --output /usr/local/bin/gitlab-runner \
    https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64

  # Make executable
  sudo chmod +x /usr/local/bin/gitlab-runner

  # Create GitLab Runner user
  sudo useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash

  # Install as service
  sudo gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner

  # Add to docker group
  sudo usermod -aG docker gitlab-runner

  # Start service
  sudo gitlab-runner start

  # Verify installation
  gitlab-runner --version
  EOF
  ```

- [ ] **3.1.2** Get GitLab registration token
  ```
  Manual step:
  1. Go to http://10.0.0.80/wizardsofts/wizardsofts-megabuild
  2. Settings → CI/CD → Runners → Expand
  3. Copy registration token (starts with GR1348...)

  Token: ___________________ (save this)
  ```

- [ ] **3.1.3** Register GitLab Runner (Interactive)
  ```bash
  ssh wizardsofts@10.0.0.84 'sudo gitlab-runner register'

  # Enter when prompted:
  # GitLab URL: http://10.0.0.80/
  # Token: [paste from 3.1.2]
  # Description: wizardsofts-megabuild-runner-84
  # Tags: deploy,docker,production,84-server
  # Executor: docker
  # Default image: alpine:latest
  ```

- [ ] **3.1.4** Configure runner for Docker-in-Docker
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  sudo tee /etc/gitlab-runner/config.toml > /dev/null <<'CONFIG'
concurrent = 4

[[runners]]
  name = "wizardsofts-megabuild-runner-84"
  url = "http://10.0.0.80/"
  token = "WILL_BE_SET_BY_REGISTER"
  executor = "docker"
  [runners.docker]
    tls_verify = false
    image = "alpine:latest"
    privileged = true
    disable_entrypoint_overwrite = false
    oom_kill_disable = false
    disable_cache = false
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
    shm_size = 0
  [runners.cache]
    [runners.cache.s3]
    [runners.cache.gcs]
    [runners.cache.azure]
CONFIG

  # Restart runner
  sudo gitlab-runner restart
  EOF
  ```

- [ ] **3.1.5** Verify runner is online in GitLab
  ```
  Manual check:
  1. Go to http://10.0.0.80/wizardsofts/wizardsofts-megabuild
  2. Settings → CI/CD → Runners
  3. Verify runner shows green status
  ```

### 3.2 SSH Key Setup for CI/CD

- [ ] **3.2.1** Generate SSH key for GitLab CI
  ```bash
  # On local machine or server 84
  ssh-keygen -t rsa -b 4096 -C "gitlab-ci@wizardsofts-megabuild" \
    -f ~/.ssh/gitlab_ci_rsa -N ""

  # Display private key (copy this for GitLab variable)
  cat ~/.ssh/gitlab_ci_rsa

  # Display public key
  cat ~/.ssh/gitlab_ci_rsa.pub
  ```

- [ ] **3.2.2** Add public key to server 84
  ```bash
  ssh wizardsofts@10.0.0.84 'mkdir -p ~/.ssh && chmod 700 ~/.ssh'

  # Copy public key to server
  cat ~/.ssh/gitlab_ci_rsa.pub | ssh wizardsofts@10.0.0.84 \
    'cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'

  # Test SSH key
  ssh -i ~/.ssh/gitlab_ci_rsa wizardsofts@10.0.0.84 'echo "SSH key works!"'
  ```

### 3.3 GitLab CI/CD Variables

- [ ] **3.3.1** Configure GitLab CI/CD variables (Manual - Playwright failed)
  ```
  Go to: http://10.0.0.80/wizardsofts/wizardsofts-megabuild/-/settings/ci_cd

  Add these variables (Settings → CI/CD → Variables → Add variable):

  Key: SSH_PRIVATE_KEY
  Value: [Paste private key from 3.2.1]
  Type: File
  Protected: ✓
  Masked: ✓

  Key: DEPLOY_HOST
  Value: 10.0.0.84
  Type: Variable
  Protected: ✓

  Key: DEPLOY_USER
  Value: wizardsofts
  Type: Variable
  Protected: ✓

  Key: DEPLOY_PATH
  Value: /opt/wizardsofts-megabuild
  Type: Variable
  Protected: ✓

  Key: DB_PASSWORD
  Value: 29Dec2#24
  Type: Variable
  Protected: ✓
  Masked: ✓

  Key: OPENAI_API_KEY
  Value: sk-... (actual key)
  Type: Variable
  Protected: ✓
  Masked: ✓

  Key: KEYCLOAK_ADMIN_PASSWORD
  Value: W1z4rdS0fts!2025
  Type: Variable
  Protected: ✓
  Masked: ✓

  Key: KEYCLOAK_DB_PASSWORD
  Value: W1z4rdS0fts!2025
  Type: Variable
  Protected: ✓
  Masked: ✓

  Key: REDIS_PASSWORD
  Value: W1z4rdS0fts!2025
  Type: Variable
  Protected: ✓
  Masked: ✓

  Key: OLLAMA_MODEL
  Value: llama3.1
  Type: Variable
  ```

- [ ] **3.3.2** Verify variables are set
  ```
  Manual check:
  1. Go to Settings → CI/CD → Variables
  2. Verify all variables listed above are present
  3. Verify Protected and Masked flags are set correctly
  ```

### 3.4 CI/CD Pipeline Configuration

- [ ] **3.4.1** Create/update .gitlab-ci.yml
  ```bash
  # This should already exist from CICD_DEPLOYMENT_PLAN_OLLAMA_SPRINGBOOT_84.md
  # Verify it's in the repo
  ls -la .gitlab-ci.yml
  ```

- [ ] **3.4.2** Update .gitlab-ci.yml with correct tags
  ```yaml
  # Ensure all jobs use the correct tag:
  tags:
    - 84-server  # Must match the tag from runner registration
  ```

- [ ] **3.4.3** Commit and push .gitlab-ci.yml (if changes made)
  ```bash
  git add .gitlab-ci.yml
  git commit -m "ci: Update GitLab CI/CD pipeline for server 84"
  git push origin main
  ```

### 3.5 Test CI/CD Pipeline

- [ ] **3.5.1** Create test pipeline
  ```yaml
  # Add test job to .gitlab-ci.yml
  test-runner:
    stage: test
    script:
      - echo "Testing GitLab Runner on server 84"
      - docker --version
      - docker compose version
      - ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST "echo 'SSH works!'"
    tags:
      - 84-server
  ```

- [ ] **3.5.2** Trigger test pipeline
  ```bash
  git add .gitlab-ci.yml
  git commit -m "ci: Add runner test job"
  git push origin main
  ```

- [ ] **3.5.3** Monitor test pipeline in GitLab
  ```
  Manual check:
  1. Go to http://10.0.0.80/wizardsofts/wizardsofts-megabuild/-/pipelines
  2. Check latest pipeline status
  3. Verify test-runner job succeeds
  4. Check job logs for any errors
  ```

- [ ] **3.5.4** Fix any test pipeline errors
  ```
  Common issues:
  - Runner not picking up jobs: Check runner tags match job tags
  - SSH failures: Verify SSH key added to authorized_keys
  - Docker errors: Verify gitlab-runner in docker group
  ```

### 3.6 Deploy via CI/CD

- [ ] **3.6.1** Trigger full deployment pipeline
  ```bash
  # Make a small change to trigger pipeline
  echo "# CI/CD Deployment - $(date)" >> README.md
  git add README.md
  git commit -m "ci: Trigger full deployment pipeline"
  git push origin main
  ```

- [ ] **3.6.2** Monitor deployment pipeline
  ```
  Manual check:
  1. Go to CI/CD → Pipelines
  2. Monitor stages: detect → test → build → deploy-infra → deploy-apps → verify
  3. Click "Play" on manual jobs when prompted
  ```

- [ ] **3.6.3** Approve deploy-to-84 job
  ```
  Manual action:
  1. Wait for build stage to complete
  2. Click "Play" button on deploy-to-84 job
  3. Monitor deployment logs
  ```

- [ ] **3.6.4** Check deployment logs for errors
  ```
  Manual check:
  1. View deploy-to-84 job logs
  2. Look for any red errors or failures
  3. Verify all services deployed successfully
  ```

**Phase 3 Verification**:
- [ ] GitLab Runner installed and registered
- [ ] Runner shows online in GitLab
- [ ] SSH key authentication works
- [ ] CI/CD variables configured
- [ ] Test pipeline succeeds
- [ ] Full deployment pipeline succeeds
- [ ] All services deployed via CI/CD

---

## Phase 4: Final Verification & Cleanup

### 4.1 Service Health Checks

- [ ] **4.1.1** Verify all Spring Boot services healthy
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  echo "=== Service Health Checks ==="
  curl -s http://localhost:8762/actuator/health | jq .  # Eureka
  curl -s http://localhost:8081/actuator/health | jq .  # Gateway
  curl -s http://localhost:8182/actuator/health | jq .  # ws-trades
  curl -s http://localhost:8183/actuator/health | jq .  # ws-company
  curl -s http://localhost:8184/actuator/health | jq .  # ws-news
  EOF
  ```

- [ ] **4.1.2** Verify database connectivity
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  docker exec wizardsofts-megabuild-postgres-1 pg_isready -U gibd
  docker exec wizardsofts-megabuild-redis-1 redis-cli -a W1z4rdS0fts!2025 ping
  EOF
  ```

- [ ] **4.1.3** Verify Ollama service
  ```bash
  ssh wizardsofts@10.0.0.84 'curl -s http://localhost:11435/api/tags'
  ```

- [ ] **4.1.4** Test Keycloak with new password
  ```bash
  # Try to login to Keycloak admin console
  # http://id.wizardsofts.com/admin
  # Username: admin
  # Password: W1z4rdS0fts!2025
  ```

### 4.2 DNS & Website Checks

- [ ] **4.2.1** Verify all websites accessible
  ```bash
  for domain in "www.guardianinvestmentbd.com" "www.wizardsofts.com" \
                "www.dailydeenguide.com" "www.padmafoods.com"; do
    echo -n "$domain: "
    curl -I -s -m 5 "https://$domain" 2>/dev/null | head -1
  done
  ```

- [ ] **4.2.2** Test Keycloak via Traefik
  ```bash
  curl -I -s "https://id.wizardsofts.com" | head -1
  ```

### 4.3 Security Verification

- [ ] **4.3.1** Verify firewall active
  ```bash
  ssh wizardsofts@10.0.0.84 'sudo ufw status verbose'
  ```

- [ ] **4.3.2** Verify external ports blocked
  ```bash
  # From external machine (should timeout):
  nc -zv -w 3 10.0.0.84 5433   # PostgreSQL
  nc -zv -w 3 10.0.0.84 6379   # Redis
  nc -zv -w 3 10.0.0.84 8080   # Traefik dashboard
  nc -zv -w 3 10.0.0.84 8180   # Keycloak direct
  ```

- [ ] **4.3.3** Verify local ports accessible
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  nc -zv localhost 5433  # PostgreSQL - should work
  nc -zv localhost 6379  # Redis - should work
  nc -zv localhost 8080  # Traefik dashboard - should work
  EOF
  ```

- [ ] **4.3.4** Check for exposed credentials
  ```bash
  # Search for hardcoded passwords
  grep -r "password123" docker-compose*.yml infrastructure/
  grep -r "admin123" docker-compose*.yml infrastructure/
  # Should return NO results
  ```

### 4.4 CI/CD Validation

- [ ] **4.4.1** Make a small code change
  ```bash
  # Update a service and trigger CI/CD
  echo "# Test CI/CD - $(date)" >> apps/ws-news/README.md
  git add apps/ws-news/README.md
  git commit -m "test: Verify CI/CD deployment"
  git push origin main
  ```

- [ ] **4.4.2** Verify pipeline triggers automatically
  ```
  Manual check:
  1. Go to CI/CD → Pipelines
  2. Verify new pipeline started automatically
  3. Verify only ws-news is detected as changed
  ```

- [ ] **4.4.3** Verify selective deployment
  ```
  Manual check:
  1. Check pipeline logs
  2. Verify only ws-news service is rebuilt
  3. Verify deployment only updates ws-news
  ```

### 4.5 Cleanup

- [ ] **4.5.1** Remove test files
  ```bash
  # Remove test commits if needed
  git reset --soft HEAD~2  # If added test commits
  git push origin main --force  # Only if needed
  ```

- [ ] **4.5.2** Clean Docker resources
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  # Remove stopped containers
  docker container prune -f

  # Remove unused images
  docker image prune -a -f

  # Remove unused volumes
  docker volume prune -f

  # Remove unused networks
  docker network prune -f
  EOF
  ```

- [ ] **4.5.3** Remove temporary SSH key (if generated on server)
  ```bash
  rm -f ~/.ssh/gitlab_ci_rsa ~/.ssh/gitlab_ci_rsa.pub
  ```

### 4.6 Documentation Updates

- [ ] **4.6.1** Update DEPLOYMENT_STATUS_REPORT_84.md
  ```markdown
  # Mark deployment as CI/CD enabled
  - CI/CD Pipeline: ✅ ENABLED
  - GitLab Runner: ✅ REGISTERED
  - HAProxy: ❌ REMOVED (single-server)
  - Security: ✅ HARDENED (UFW, localhost-only ports)
  ```

- [ ] **4.6.2** Update SECURITY_OPTIMIZATION_AUDIT_84.md
  ```markdown
  # Update security status:
  - PostgreSQL/Redis public exposure: ✅ FIXED
  - Keycloak passwords: ✅ FIXED (W1z4rdS0fts!2025)
  - UFW firewall: ✅ ENABLED
  - HAProxy: ✅ REMOVED
  - CI/CD: ✅ ENABLED
  ```

- [ ] **4.6.3** Create final implementation report
  ```bash
  # Document what was done
  ```

### 4.7 Backup

- [ ] **4.7.1** Create backup of current state
  ```bash
  ssh wizardsofts@10.0.0.84 << 'EOF'
  sudo mkdir -p /backup

  # Backup PostgreSQL
  docker exec wizardsofts-megabuild-postgres-1 pg_dumpall -U gibd | \
    gzip > /backup/postgres-post-security-$(date +%Y%m%d).sql.gz

  # Backup Keycloak
  docker exec keycloak_postgres pg_dumpall -U keycloak | \
    gzip > /backup/keycloak-post-security-$(date +%Y%m%d).sql.gz

  # Backup .env
  sudo cp /opt/wizardsofts-megabuild/.env \
    /backup/.env-post-security-$(date +%Y%m%d)
  EOF
  ```

- [ ] **4.7.2** Verify backups created
  ```bash
  ssh wizardsofts@10.0.0.84 'ls -lh /backup/'
  ```

---

## Rollback Plan (If Needed)

### Rollback Phase 1 (Security)
```bash
# Restore original docker-compose.yml
git checkout HEAD~1 docker-compose.yml
docker-compose up -d

# Disable UFW
sudo ufw disable

# Restore original Keycloak config
cd infrastructure/keycloak
git checkout HEAD~1 docker-compose.yml
docker-compose up -d
```

### Rollback Phase 2 (HAProxy)
```bash
# Restart HAProxy if removed
docker start haproxy  # If not removed yet
```

### Rollback Phase 3 (CI/CD)
```bash
# Unregister runner
sudo gitlab-runner unregister --all-runners

# Stop runner service
sudo gitlab-runner stop
```

---

## Success Criteria

All items must be ✅ before marking complete:

- [ ] All critical security vulnerabilities fixed
- [ ] Only ports 22, 25, 80, 443 accessible externally
- [ ] UFW firewall enabled and configured
- [ ] Keycloak using strong password (W1z4rdS0fts!2025)
- [ ] HAProxy removed successfully
- [ ] GitLab Runner installed and registered
- [ ] CI/CD pipeline functional and tested
- [ ] All services deployed via CI/CD
- [ ] All services healthy after changes
- [ ] All websites accessible via DNS
- [ ] Documentation updated
- [ ] Backups created

---

## Estimated Timeline

- **Phase 1 (Security)**: 45-60 minutes
- **Phase 2 (HAProxy)**: 10-15 minutes
- **Phase 3 (CI/CD)**: 60-90 minutes
- **Phase 4 (Verification)**: 30-45 minutes

**Total**: 2.5-3.5 hours

---

## Notes

- Use sudo password: `29Dec2#24` for server 84 operations
- All changes should be committed to git after verification
- Test each phase before proceeding to next
- Keep old configurations commented out (don't delete)
- Document any deviations from this checklist

---

**Checklist Created**: 2025-12-28
**Ready for Implementation**: ✅ YES
**Requires User Approval**: ✅ YES

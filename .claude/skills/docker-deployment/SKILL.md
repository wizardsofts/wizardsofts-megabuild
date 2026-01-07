---
name: docker-deployment
description: Deploy services using Docker with CI/CD pipeline (no direct deployment)
version: 1.0.0
created: 2026-01-07
updated: 2026-01-07
---

# Docker Deployment Skill

## When to Use

Invoke this skill when:
- Deploying a new service to staging or production
- Updating an existing service deployment
- Creating or modifying Dockerfiles
- Setting up CI/CD pipelines for Docker services
- Reviewing Docker configurations for security/performance

## Prerequisites

- [ ] Service has a valid Dockerfile following best practices
- [ ] CI/CD pipeline configured (GitLab CI or equivalent)
- [ ] Docker registry access configured
- [ ] Target environment (staging/production) is accessible
- [ ] Traefik or load balancer configured for the service

## CRITICAL: No Direct Deployment

**NEVER deploy services directly. ALL deployments MUST go through CI/CD.**

```
FORBIDDEN                           REQUIRED
---------                           --------
docker run ...                      git push -> CI/CD -> Deploy
docker-compose up -d                Merge Request -> Pipeline -> Deploy
docker service create               Automated testing + security scan
Manual SSH + docker commands        Rollback on failure
```

## Automation Users

| Context | User | Purpose |
|---------|------|---------|
| SSH (general ops) | `agent` | General server operations (`ssh agent@10.0.0.84`) |
| SSH (deployments) | `deploy` | CI/CD deployment operations (`ssh deploy@10.0.0.84`) |
| GitLab CI/CD | `agent` | Pipeline execution, MR creation, variable management |
| GitLab Admin | `mashfiqur.rahman` | Manual administration only |

**Note:** The `deploy` user exists on all servers (80, 81, 82, 84) with Docker group access. Use `deploy` for CI/CD deployment scripts.

## Procedure

### Step 1: Verify Dockerfile

Check the Dockerfile follows best practices:

```dockerfile
# Required elements checklist:
# [ ] Specific base image tag (no :latest)
# [ ] Multi-stage build (if applicable)
# [ ] Non-root user
# [ ] HEALTHCHECK instruction
# [ ] Minimal layers
# [ ] .dockerignore present
```

**Verification command:**
```bash
# Check Dockerfile exists
ls -la apps/<service>/Dockerfile

# Verify no :latest tag
grep -n "FROM.*:latest" apps/<service>/Dockerfile && echo "ERROR: :latest found" || echo "OK: No :latest"

# Check for USER instruction
grep -n "^USER" apps/<service>/Dockerfile || echo "WARNING: No USER instruction"

# Check for HEALTHCHECK
grep -n "^HEALTHCHECK" apps/<service>/Dockerfile || echo "WARNING: No HEALTHCHECK"
```

### Step 2: Verify Docker Compose

Check docker-compose.yml for production readiness:

```yaml
# Required elements checklist:
# [ ] Image uses variable (${VERSION}), not :latest
# [ ] Resource limits defined
# [ ] Health check configured
# [ ] Security options (no-new-privileges, cap_drop)
# [ ] Logging configured
# [ ] Networks properly configured
```

**Verification command:**
```bash
# Validate compose file
docker-compose -f docker-compose.production.yml config

# Check for :latest
grep -n ":latest" docker-compose.production.yml && echo "ERROR: :latest found"

# Check for resource limits
grep -A5 "limits:" docker-compose.production.yml
```

### Step 3: Verify CI/CD Pipeline

Ensure `.gitlab-ci.yml` (or equivalent) includes:

```yaml
# Required stages:
stages:
  - build       # Build Docker image
  - test        # Run tests in container
  - security    # Security scan (trivy)
  - deploy      # Deploy via docker stack/service
```

**Verification:**
```bash
# Check pipeline file exists
ls -la .gitlab-ci.yml

# Check for security stage
grep -n "security" .gitlab-ci.yml || echo "WARNING: No security stage"

# Check for trivy scan
grep -n "trivy" .gitlab-ci.yml || echo "WARNING: No trivy scan"
```

### Step 4: Deploy via CI/CD

**For new deployment:**
```bash
# 1. Create feature branch
git checkout -b deploy/<service>-<version>

# 2. Update version in docker-compose or package.json
# 3. Commit changes
git add .
git commit -m "deploy(<service>): update to version X.Y.Z"

# 4. Push to trigger pipeline
git push origin deploy/<service>-<version>

# 5. Create merge request
# Pipeline will: build -> test -> security scan -> deploy to staging
```

**For production deployment:**
```bash
# 1. Create git tag (triggers production pipeline)
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# 2. Pipeline deploys to staging automatically
# 3. Manual approval required for production
# (Click "Play" button in GitLab CI for production job)
```

### Step 5: Verify Deployment

```bash
# Check service health (via monitoring, NOT SSH)
curl https://<service>.wizardsofts.com/health

# Check metrics
curl https://<service>.wizardsofts.com/metrics | head -20

# Check logs via centralized logging (Grafana/Loki)
# NOT via SSH + docker logs
```

### Step 6: Rollback (If Needed)

**Automated rollback (preferred):**
Pipeline automatically rolls back on health check failure.

**Manual rollback via CI/CD:**
```bash
# Trigger rollback pipeline
curl -X POST \
  -F "token=${TRIGGER_TOKEN}" \
  -F "ref=master" \
  -F "variables[ROLLBACK_VERSION]=1.2.2" \
  https://gitlab.wizardsofts.com/api/v4/projects/<id>/trigger/pipeline
```

**Emergency rollback (last resort):**
```bash
# Via GitLab CI trigger or Swarm rollback job
# NOT direct SSH commands
```

## Verification

After deployment, verify:
- [ ] Health endpoint returns 200 OK
- [ ] Metrics endpoint accessible
- [ ] Logs appearing in centralized logging
- [ ] No errors in Prometheus/Grafana alerts
- [ ] Response times within acceptable range

## Troubleshooting

### Pipeline fails at build stage

```bash
# Check build logs in GitLab CI
# Common issues:
# - Missing dependencies in Dockerfile
# - Incorrect base image
# - Build context too large (check .dockerignore)
```

### Pipeline fails at security stage

```bash
# Check trivy scan results
# Options:
# 1. Update base image to patched version
# 2. Update vulnerable dependency
# 3. If false positive, add to .trivyignore
```

### Service not starting after deployment

```bash
# Check via monitoring dashboard (NOT SSH)
# 1. Review deployment logs in GitLab CI
# 2. Check Grafana/Loki for container logs
# 3. Verify environment variables in GitLab CI/CD settings
```

### Health check failing

```bash
# Common causes:
# - Service not ready in time (increase start_period)
# - Wrong health check endpoint
# - Database/dependencies not available
# - Resource limits too low
```

## Templates

### Dockerfile Template (Node.js)

```dockerfile
# Build stage
FROM node:20.11-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20.11-alpine AS production
RUN addgroup -g 1001 -S app && adduser -u 1001 -S app -G app
WORKDIR /app
COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
COPY --from=builder --chown=app:app /app/package.json ./
USER app
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### Dockerfile Template (Java Spring Boot)

```dockerfile
# Build stage
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY pom.xml mvnw ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline
COPY src src
RUN ./mvnw package -DskipTests

# Production stage
FROM eclipse-temurin:21-jre-alpine AS production
RUN addgroup -g 1001 -S app && adduser -u 1001 -S app -G app
WORKDIR /app
COPY --from=builder --chown=app:app /app/target/*.jar app.jar
USER app
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Dockerfile Template (Python FastAPI)

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY . .

# Production stage
FROM python:3.11-slim AS production
RUN useradd -m -u 1001 app
WORKDIR /app
COPY --from=builder --chown=app:app /root/.local /home/app/.local
COPY --from=builder --chown=app:app /app .
ENV PATH=/home/app/.local/bin:$PATH
USER app
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.production.yml Template

```yaml
version: '3.8'

services:
  app:
    image: ${REGISTRY:-registry.wizardsofts.com}/${SERVICE_NAME}:${VERSION}
    container_name: ${SERVICE_NAME}
    restart: unless-stopped

    user: "1001:1001"
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

    environment:
      - NODE_ENV=production
    env_file:
      - .env.production

    networks:
      - traefik-network

    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.${SERVICE_NAME}.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.${SERVICE_NAME}.entrypoints=websecure"
      - "traefik.http.routers.${SERVICE_NAME}.tls.certresolver=letsencrypt"
      - "traefik.http.services.${SERVICE_NAME}.loadbalancer.server.port=3000"

    tmpfs:
      - /tmp:size=100M

networks:
  traefik-network:
    external: true
```

### .gitlab-ci.yml Template

```yaml
stages:
  - build
  - test
  - security
  - deploy-staging
  - deploy-production

variables:
  DOCKER_IMAGE: ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t ${DOCKER_IMAGE} .
    - docker push ${DOCKER_IMAGE}
  rules:
    - if: $CI_COMMIT_BRANCH == "master" || $CI_COMMIT_TAG

test:
  stage: test
  image: ${DOCKER_IMAGE}
  script:
    - npm run test:ci
  rules:
    - if: $CI_COMMIT_BRANCH == "master" || $CI_COMMIT_TAG

security:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL ${DOCKER_IMAGE}
  rules:
    - if: $CI_COMMIT_BRANCH == "master" || $CI_COMMIT_TAG

deploy-staging:
  stage: deploy-staging
  image: docker:24
  environment:
    name: staging
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker stack deploy -c docker-compose.staging.yml --with-registry-auth app
  rules:
    - if: $CI_COMMIT_BRANCH == "master"

deploy-production:
  stage: deploy-production
  image: docker:24
  environment:
    name: production
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker stack deploy -c docker-compose.production.yml --with-registry-auth app
  rules:
    - if: $CI_COMMIT_TAG
  when: manual
```

## Examples

### Example 1: Deploy ws-gateway to staging

```bash
# 1. Update version
cd apps/ws-gateway
# Edit pom.xml to update version

# 2. Commit and push
git add pom.xml
git commit -m "deploy(ws-gateway): update to version 2.1.0"
git push origin master

# 3. Monitor pipeline in GitLab CI
# Pipeline: build -> test -> security -> deploy-staging (auto)

# 4. Verify deployment
curl https://staging-gateway.wizardsofts.com/actuator/health
```

### Example 2: Deploy to production with tag

```bash
# 1. Create release tag
git tag -a v2.1.0 -m "Release v2.1.0 - OAuth2 improvements"
git push origin v2.1.0

# 2. Pipeline runs: build -> test -> security
# 3. Manual approval for production
# 4. Click "Play" on deploy-production job in GitLab

# 5. Verify production
curl https://gateway.wizardsofts.com/actuator/health
```

### Example 3: Emergency rollback

```bash
# Via GitLab API (NOT direct commands)
curl -X POST \
  -F "token=${ROLLBACK_TOKEN}" \
  -F "ref=master" \
  -F "variables[ROLLBACK_VERSION]=2.0.5" \
  https://gitlab.wizardsofts.com/api/v4/projects/1/trigger/pipeline
```

## Changelog

- v1.0.0 (2026-01-07): Initial version

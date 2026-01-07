# DevOps Skill - User-Level Claude Code Skill

**Skill Type:** User-level
**Storage Location:** `~/.claude/skills/devops/`
**Trigger phrases:** "deploy", "ci/cd", "gitlab pipeline", "rollback", "docker compose", "health check", "deployment verification"

---

## Overview

This skill provides comprehensive DevOps automation for WizardSofts infrastructure, covering GitLab CI/CD pipeline management, multi-server deployments, and infrastructure orchestration.

---

## What This Skill Has

### GitLab CI/CD Pipeline Knowledge

**7-Stage Pipeline:**
1. **validate** - Configuration validation, credential detection
2. **detect** - Change detection (incremental builds)
3. **test** - Automated testing
4. **build** - Docker image building
5. **pre-deploy** - Backup creation
6. **deploy** - Service deployment
7. **verify** - Health checks and validation

**Features:**
- Change detection (only rebuild modified services)
- Automated Docker image building
- Manual deployment approval gates
- Emergency rollback procedures
- Health check automation
- Artifact management

### Infrastructure Deployment

**Supported Services:**
- Spring Boot microservices (ws-gateway, ws-discovery, ws-company, ws-trades, ws-news)
- Python FastAPI services (signal, nlq, calibration, agent)
- Next.js frontends (gibd-quant-web, ws-wizardsofts-web, ws-daily-deen-web, pf-padmafoods-web)
- Appwrite BaaS platform
- Monitoring stack (Prometheus, Grafana, Node Exporter, cAdvisor)

**Docker Compose Management:**
- Profile management (gibd-quant, shared, all)
- Network creation and validation
- Service orchestration
- Volume management

### Security-First Deployment

**Credential Management:**
- GitLab CI/CD Variables (masked, protected)
- SSH key-based authentication only
- No hardcoded secrets detection
- Environment variable injection

**Security Validations:**
- Pre-deployment configuration validation
- HTTPS verification post-deployment
- Health check verification
- Rollback capability

---

## What This Skill Will Do

### 1. Deployment Assistance

**Pipeline Setup:**
```bash
# Create .gitlab-ci.yml with proper stages
# Configure CI/CD variables in GitLab
# Set up deployment keys
# Configure manual approval gates
```

**Service Deployment:**
- Deploy to Server 80 (10.0.0.80) - GIBD Services + Ray Worker
- Deploy to Server 81 (10.0.0.81) - Database Server + Ray Worker
- Deploy to Server 82 (10.0.0.82) - HPR Server (Monitoring) + Ray Worker
- Deploy to Server 84 (10.0.0.84) - HP Production (Appwrite, microservices, GitLab, monitoring, Ray + Celery)

**Deployment Process:**
1. Validate configuration files
2. Detect changed services
3. Build Docker images
4. Create pre-deployment backup
5. Deploy via SSH with credential injection
6. Verify health checks
7. Confirm HTTPS certificate validity

### 2. Troubleshooting

**CI/CD Pipeline Diagnostics:**
- Analyze failed pipeline stages
- Check GitLab runner connectivity
- Validate CI/CD variable configuration
- Review build logs

**Container Health:**
- Check Docker container status
- Verify network connectivity between services
- Analyze deployment logs
- Test health endpoints

**Network Diagnostics:**
- Verify Docker networks exist
- Check Traefik network connections
- Test service-to-service connectivity
- Validate DNS resolution

### 3. Configuration Management

**Validation:**
- Validate docker-compose.yml syntax
- Check for hardcoded credentials
- Verify environment variable references
- Ensure proper network configuration

**Change Detection:**
- Detect which services need rebuilding
- Analyze git diff for affected services
- Skip unchanged services (incremental builds)

**Profile Management:**
- Switch between deployment profiles (dev, staging, prod)
- Manage environment-specific configurations
- Handle multi-environment deployments

### 4. Rollback Operations

**Emergency Rollback:**
```bash
# SSH into target server
git reset --hard HEAD~1
docker compose --profile <profile> down
docker compose --profile <profile> up -d
# Verify health endpoints
```

**Backup Restoration:**
- Restore from pre-deployment backups
- Recover configuration files
- Restore database state (coordinate with Database Admin skill)

### 5. Multi-Server Deployment

**Server-Specific Operations:**

**Server 80 (GIBD Services):**
- Deploy GIBD microservices
- Deploy Ray worker node
- Configure distributed ML infrastructure

**Server 81 (Database Server):**
- Deploy PostgreSQL containers
- Deploy Ray worker node
- No Docker metrics (lightweight monitoring)

**Server 82 (HPR Monitoring):**
- Deploy Node Exporter
- Deploy cAdvisor
- Configure UFW firewall for local network access
- Deploy Ray worker node
- Verify metrics exporters are accessible from Prometheus (Server 84)

**Server 84 (HP Production):**
- Deploy Appwrite BaaS
- Deploy Spring Boot microservices
- Deploy Next.js frontends
- Deploy GitLab CE
- Deploy Traefik reverse proxy
- Deploy monitoring stack (Prometheus, Grafana)
- Deploy Ray head node + Celery workers
- Coordinate all infrastructure components

---

## Example Usage

### Example 1: Deploy Frontend to Production

**User Request:**
```
User: "Deploy gibd-quant-web to production"
```

**Skill Actions:**
1. Validates GitLab pipeline is configured for gibd-quant-web
2. Checks if manual deployment approval is set
3. Verifies docker-compose.yml has correct configuration
4. Guides user through GitLab pipeline trigger
5. Monitors deployment progress
6. Runs health check verification
7. Confirms HTTPS certificate is valid post-deploy
8. Provides deployment summary with URLs

### Example 2: Deploy Monitoring to Server 82

**User Request:**
```
User: "Deploy monitoring stack to server 82"
```

**Skill Actions:**
1. SSH into 10.0.0.82 (hpr server)
2. Create ~/server-82 directory structure
3. Deploy Node Exporter container
4. Deploy cAdvisor container
5. Configure UFW firewall rules:
   ```bash
   sudo ufw allow from 10.0.0.0/24 to any port 9100 proto tcp
   sudo ufw allow from 10.0.0.0/24 to any port 8080 proto tcp
   sudo ufw deny 9100/tcp
   sudo ufw deny 8080/tcp
   ```
6. Verify exporters are accessible from Prometheus (server 84)
7. Update Prometheus configuration to scrape server 82
8. Check Grafana dashboard shows server 82 metrics
9. Verify health checks pass

### Example 3: Emergency Rollback

**User Request:**
```
User: "Rollback the last deployment on server 84"
```

**Skill Actions:**
1. SSH into wizardsofts@10.0.0.84
2. Navigate to /opt/wizardsofts-megabuild
3. Check current commit: `git log -1 --oneline`
4. Create emergency backup: `docker compose config > /tmp/pre-rollback-$(date +%s).yml`
5. Stop services: `docker compose --profile gibd-quant down`
6. Rollback: `git reset --hard HEAD~1`
7. Restart services: `docker compose --profile gibd-quant up -d`
8. Wait 30 seconds for initialization
9. Verify health endpoints:
   - Eureka: `curl http://10.0.0.84:8761/actuator/health`
   - Gateway: `curl http://10.0.0.84:8080/actuator/health`
   - Frontends: `curl http://10.0.0.84:3001`
10. Provide rollback summary with previous commit hash

### Example 4: Troubleshoot Failed Pipeline

**User Request:**
```
User: "The GitLab pipeline is failing at the build stage"
```

**Skill Actions:**
1. Check GitLab runner status:
   ```bash
   docker ps | grep runner
   docker logs gitlab-runner --tail 50
   ```
2. Verify CI/CD variables are set:
   - SSH_PRIVATE_KEY (File type, Protected)
   - DEPLOY_SUDO_PASSWORD (Masked)
   - Check other required variables
3. Analyze build logs for error patterns
4. Check Docker daemon connectivity
5. Verify docker-compose.yml syntax
6. Test build locally:
   ```bash
   docker compose build <service>
   ```
7. Provide diagnosis with specific fix recommendations

### Example 5: Multi-Service Deployment

**User Request:**
```
User: "Deploy all GIBD services to server 80"
```

**Skill Actions:**
1. Detect changed services in GitLab pipeline
2. Build Docker images for changed services:
   - ws-company (Spring Boot)
   - ws-trades (Spring Boot)
   - ws-news (Spring Boot)
   - gibd-signal-service (Python)
   - gibd-nlq-service (Python)
3. Create pre-deployment backup on server 80
4. Deploy services in correct order:
   - Infrastructure first (Redis, PostgreSQL)
   - Backend services (Spring Boot microservices)
   - Python ML services
   - Frontend (gibd-quant-web)
5. Verify network connectivity between services
6. Run health checks on all services
7. Verify Eureka service discovery
8. Confirm API Gateway is routing correctly
9. Provide deployment report with all service URLs

---

## Related Skills

- **Database Admin Skill** - For database backup/restore during deployments
- **Server Security Skill** - For firewall configuration and security hardening

---

## Configuration Files

**GitLab CI/CD:**
- `.gitlab-ci.yml` - Main pipeline configuration
- `.gitlab/ci/security.gitlab-ci.yml` - Security scanning
- `.gitlab/ci/apps.gitlab-ci.yml` - Application pipeline
- `.gitlab/ci/infra.gitlab-ci.yml` - Infrastructure pipeline

**Docker Compose:**
- `docker-compose.yml` - Main services
- `docker-compose.appwrite.yml` - Appwrite BaaS
- `infrastructure/gitlab/docker-compose.yml` - GitLab CE
- `infrastructure/distributed-ml/docker-compose.*.yml` - Ray + Celery

**Documentation:**
- `docs/GITLAB_DEPLOYMENT.md` - GitLab deployment guide
- `docs/DEPLOYMENT_SUMMARY_84.md` - Server 84 deployment
- `docs/SERVER_82_DEPLOYMENT.md` - Server 82 monitoring setup

---

## Server Infrastructure

| Server | IP | Role | Deployment Types |
|--------|-----|------|------------------|
| Server 80 | 10.0.0.80 | GIBD Services + Ray Worker | Microservices, ML services, databases |
| Server 81 | 10.0.0.81 | Database Server + Ray Worker | PostgreSQL, Ray worker |
| Server 82 | 10.0.0.82 | HPR Server (Monitoring) + Ray Worker | Node Exporter, cAdvisor, Ray worker |
| Server 84 | 10.0.0.84 | HP Production | Appwrite, microservices, frontends, GitLab, monitoring, Ray head, Celery |

---

## Common Deployment Workflows

### Standard Deployment Flow

1. **Local Changes** → Push to GitLab
2. **GitLab Pipeline** → Validate → Build → Test
3. **Manual Approval** → Trigger deployment
4. **Pre-Deploy** → Create backup
5. **Deploy** → SSH + rsync + docker compose
6. **Verify** → Health checks + HTTPS validation
7. **Monitor** → Check Grafana dashboards

### Emergency Deployment Flow

1. **Hotfix Branch** → Create feature/hotfix-*
2. **Fast-Track Build** → Skip long tests
3. **Manual Approval** → Deploy to production
4. **Immediate Verification** → Health checks only
5. **Post-Deploy** → Full testing after deployment

### Rollback Flow

1. **Detect Issue** → Health checks fail
2. **Emergency Backup** → Capture current state
3. **Git Rollback** → `git reset --hard HEAD~1`
4. **Service Restart** → `docker compose up -d`
5. **Verify** → Health checks pass
6. **Investigate** → Analyze what went wrong

---

## Security Considerations

**Never Include in CI/CD Pipelines:**
- ❌ Hardcoded passwords
- ❌ API keys in code
- ❌ Database credentials in docker-compose.yml
- ❌ SSH private keys in repository

**Always Use:**
- ✅ GitLab CI/CD Variables (masked, protected)
- ✅ Environment variable references (${VAR})
- ✅ SSH key authentication (no passwords)
- ✅ Pre-deployment validation
- ✅ Health check verification

**Port Security:**
- ✅ Databases: `127.0.0.1:5433:5432` (localhost only)
- ✅ Redis: `127.0.0.1:6379:6379` (localhost only)
- ✅ Admin interfaces: Behind Traefik with authentication
- ✅ Public services: Only via Traefik (ports 80, 443)

---

## Troubleshooting Guide

### Pipeline Fails at Validate Stage

**Symptom:** Configuration validation fails

**Diagnosis:**
1. Check for hardcoded credentials
2. Verify docker-compose.yml syntax
3. Run local validation: `docker compose config`

**Fix:**
- Replace hardcoded values with `${ENV_VAR}`
- Add missing environment variables to GitLab

### Pipeline Fails at Build Stage

**Symptom:** Docker image build fails

**Diagnosis:**
1. Check Dockerfile syntax
2. Verify base image availability
3. Check Docker daemon connectivity

**Fix:**
- Fix Dockerfile errors
- Update base image versions
- Restart GitLab runner

### Deployment Fails - SSH Connection

**Symptom:** Cannot SSH into target server

**Diagnosis:**
1. Check SSH_PRIVATE_KEY variable in GitLab
2. Verify SSH key is added to server's authorized_keys
3. Test SSH connectivity manually

**Fix:**
- Re-add SSH_PRIVATE_KEY to GitLab CI/CD variables
- Ensure key is in File type format (not Variable)
- Verify server firewall allows SSH (port 22)

### Services Not Starting After Deployment

**Symptom:** `docker compose ps` shows services as exited

**Diagnosis:**
1. Check logs: `docker logs <container> --tail 100`
2. Verify environment variables are set
3. Check network connectivity
4. Verify volumes exist

**Fix:**
- Fix configuration errors in .env files
- Create missing Docker networks
- Recreate volumes if corrupted

### Health Checks Failing

**Symptom:** Verify stage reports health check failures

**Diagnosis:**
1. Check if services are running: `docker ps`
2. Test health endpoints manually: `curl http://localhost:8761/actuator/health`
3. Check service logs for errors

**Fix:**
- Increase health check timeout in verify stage
- Fix application errors causing health check failures
- Verify health endpoint paths are correct

---

## Best Practices

1. **Always create pre-deployment backups** - Use pre-deploy-backup job
2. **Use manual approval for production** - Never auto-deploy to production
3. **Verify HTTPS certificates** - Run HTTPS validation after frontend deployments
4. **Monitor deployments** - Watch Grafana dashboards during deployment
5. **Test rollback procedures** - Practice rollback in staging first
6. **Document custom deployments** - Update deployment guides for special cases
7. **Use incremental builds** - Only rebuild changed services
8. **Keep credentials in GitLab** - Never commit secrets to repository

---

## Maintenance

**Weekly:**
- Review failed pipelines and fix issues
- Update base Docker images for security patches
- Clean up old Docker images: `docker image prune -a --filter "until=168h"`

**Monthly:**
- Review and optimize pipeline performance
- Update GitLab Runner to latest version
- Audit CI/CD variable usage

**Quarterly:**
- Full infrastructure security audit
- Update all service versions
- Test disaster recovery procedures

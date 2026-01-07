# GitLab Deployment Guide

## Overview

GitLab CE is deployed on HP Server (10.0.0.84) as the source control and CI/CD platform for WizardSofts projects.

## Configuration

- **Location:** `/opt/wizardsofts-megabuild/infrastructure/gitlab/`
- **Docker Compose:** `docker-compose.yml`
- **Data Volumes:**
  - Config: `/mnt/data/docker/gitlab/config`
  - Logs: `/mnt/data/docker/gitlab/logs`
  - Data: `/mnt/data/docker/gitlab/data`

## Access Points

| Service | URL/Port |
|---------|----------|
| Web UI | http://10.0.0.84:8090 |
| Container Registry | http://10.0.0.84:5050 |
| SSH | 10.0.0.84:2222 |
| HTTPS (if configured) | http://10.0.0.84:8443 |

## Dependencies

GitLab relies on external services (not bundled PostgreSQL/Redis):

- **PostgreSQL:** `gibd-postgres` container on gibd-network
- **Redis:** `gibd-redis` container on gibd-network

Ensure these containers are running before starting GitLab.

## Deployment Commands

### Start GitLab
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose up -d
```

### Stop GitLab
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down
```

### Restart GitLab
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down && docker-compose up -d
```

### View Logs
```bash
docker logs gitlab -f --tail 100
```

## Health Monitoring

### Check Container Health
```bash
docker ps | grep gitlab
# Should show (healthy) status
```

### Check Internal Services
```bash
docker exec gitlab gitlab-ctl status
```

Expected output (all should show "run"):
- alertmanager
- gitaly
- gitlab-exporter
- gitlab-kas
- gitlab-workhorse
- logrotate
- nginx
- prometheus
- puma
- registry
- sidekiq
- sshd

### Health Endpoints
```bash
# Readiness (returns {"status":"ok"})
curl http://10.0.0.84:8090/-/readiness

# Liveness (returns {"status":"ok"})
curl http://10.0.0.84:8090/-/liveness

# Health (used by Docker healthcheck)
curl http://10.0.0.84:8090/-/health
```

## Configuration Details

### GITLAB_OMNIBUS_CONFIG

Key settings in docker-compose.yml:

```yaml
environment:
  GITLAB_OMNIBUS_CONFIG: |
    external_url 'http://10.0.0.84:8090'
    registry_external_url 'http://10.0.0.84:5050'
    gitlab_rails['registry_enabled'] = true
    gitlab_rails['gitlab_shell_ssh_port'] = 2222

    # External PostgreSQL
    postgresql['enable'] = false
    gitlab_rails['db_adapter'] = 'postgresql'
    gitlab_rails['db_host'] = 'gibd-postgres'
    gitlab_rails['db_port'] = 5432

    # External Redis
    redis['enable'] = false
    gitlab_rails['redis_host'] = 'gibd-redis'
    gitlab_rails['redis_port'] = 6379
```

### Health Check Configuration

**CRITICAL:** When using non-standard ports, the health check must match the `external_url` port:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8090/-/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Troubleshooting

### Container Shows "unhealthy"

1. **Check health check output:**
   ```bash
   docker inspect --format='{{json .State.Health}}' gitlab | python3 -m json.tool
   ```

2. **Verify port configuration:**
   - If `external_url` uses port 8090, health check must use `localhost:8090`
   - Default health check (`localhost/-/health`) assumes port 80

3. **Check internal services:**
   ```bash
   docker exec gitlab gitlab-ctl status
   ```

### GitLab Not Accessible

1. **Verify container is running:**
   ```bash
   docker ps | grep gitlab
   ```

2. **Check nginx status:**
   ```bash
   docker exec gitlab gitlab-ctl status nginx
   ```

3. **Test from inside container:**
   ```bash
   docker exec gitlab curl -s http://localhost:8090/-/readiness
   ```

4. **Check firewall:**
   ```bash
   sudo ufw status | grep 8090
   ```

### Database Connection Issues

1. **Check PostgreSQL container:**
   ```bash
   docker ps | grep postgres
   ```

2. **Test database connection:**
   ```bash
   docker exec gitlab gitlab-rake gitlab:check
   ```

3. **Verify network connectivity:**
   ```bash
   docker exec gitlab ping -c 2 gibd-postgres
   ```

### GitLab Runner Not Connecting

1. **Check runner configuration:**
   - Ensure runner is registered with correct URL: `http://10.0.0.84:8090`

2. **Verify runner container:**
   ```bash
   docker ps | grep runner
   docker logs gitlab-runner --tail 50
   ```

## Incident History

### 2025-12-31: Health Check Failure

**Symptoms:**
- Container showing "unhealthy" with 1500+ failing streak
- GitLab was actually working (API responding, runners connecting)

**Root Cause:**
- Health check was using `http://localhost/-/health` (default port 80)
- GitLab was configured with `external_url 'http://10.0.0.84:8090'` (port 8090)
- Internal nginx was listening on 8090, not 80

**Resolution:**
- Updated health check to `http://localhost:8090/-/health`
- Recreated container with `docker-compose down && docker-compose up -d`

**Prevention:**
- Always verify health check port matches `external_url` port
- Document custom port configurations clearly
- Test health endpoint manually after configuration changes

## Backup and Recovery

### Backup GitLab Data
```bash
docker exec gitlab gitlab-backup create
```

Backups are stored in `/mnt/data/docker/gitlab/data/backups/`

### Restore from Backup
```bash
docker exec gitlab gitlab-backup restore BACKUP=timestamp_gitlab_backup
```

## Updates

### Upgrade GitLab Version

1. Update image tag in docker-compose.yml
2. Pull new image: `docker-compose pull`
3. Recreate container: `docker-compose down && docker-compose up -d`
4. Monitor logs: `docker logs gitlab -f`

**Note:** Always check GitLab upgrade paths - some versions require sequential upgrades.

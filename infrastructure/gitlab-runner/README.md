```markdown
# GitLab Runner Setup

Multi-project GitLab Runner configuration for self-hosted CI/CD pipelines.

## Overview

This setup runs three isolated GitLab Runners, one for each project:
- **dailydeenguide-runner** - Daily Deen Guide project
- **wizardsofts-runner** - Wizardsofts project  
- **gibd-runner** - GIBD project

Each runner has its own configuration directory and operates independently while sharing the same Docker daemon and network.

## Architecture

```
/mnt/data/docker/gitlab-runner/
├── dailydeenguide/
│   └── config/
│       └── config.toml
├── wizardsofts/
│   └── config/
│       └── config.toml
└── gibd/
└── config/
└── config.toml
```

All runners:
- Share the Docker socket (`/var/run/docker.sock`)
- Connect to the `gibd-network` for service communication
- Use Docker executor with `alpine:latest` as default image

## Prerequisites

- Docker and Docker Compose installed
- GitLab instance accessible at `http://10.0.0.80`
- `gibd-network` Docker network created
- Runner registration tokens from GitLab

## Initial Setup

### 1. Create Directory Structure

```bash
sudo mkdir -p /mnt/data/docker/gitlab-runner/{dailydeenguide,wizardsofts,gibd}/config
sudo chown -R root:root /mnt/data/docker/gitlab-runner
```

### 2. Deploy Runners

```bash
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check all runners are running
docker-compose ps

# Check logs
docker-compose logs -f
```

## Registering Runners

### Get Registration Token

1. Navigate to your GitLab project
2. Go to **Settings > CI/CD > Runners**
3. Click **"New project runner"**
4. Configure and create runner
5. Copy the runner authentication token (starts with `glrt-`)

### Register Each Runner

**Daily Deen Guide Runner:**
```bash
docker exec -it gitlab-runner-dailydeenguide gitlab-runner register \
  --non-interactive \
  --url "http://10.0.0.80" \
  --token "YOUR_TOKEN_HERE" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "dailydeenguide-runner" \
  --tag-list "docker,dailydeen,linux" \
  --docker-volumes "/var/run/docker.sock:/var/run/docker.sock" \
  --docker-network-mode "gibd-network"
```

**Wizardsofts Runner:**
```bash
docker exec -it gitlab-runner-wizardsofts gitlab-runner register \
  --non-interactive \
  --url "http://10.0.0.80" \
  --token "glrt-JovLhe8NEaVKAHTPIagi82c6NQpvOjEKdDoyCnU6Mw8.01.171xp833b" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "wizardsofts-runner" \
  --tag-list "docker,wizardsofts,linux" \
  --docker-volumes "/var/run/docker.sock:/var/run/docker.sock" \
  --docker-network-mode "gibd-network"
```

**GIBD Runner:**
```bash
docker exec -it gitlab-runner-gibd gitlab-runner register \
  --non-interactive \
  --url "http://10.0.0.80" \
  --token "YOUR_TOKEN_HERE" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "gibd-runner" \
  --tag-list "docker,gibd,linux" \
  --docker-volumes "/var/run/docker.sock:/var/run/docker.sock" \
  --docker-network-mode "gibd-network"
```

### Interactive Registration

If you prefer step-by-step prompts:

```bash
docker exec -it gitlab-runner-dailydeenguide gitlab-runner register
```

Follow the prompts:
1. **GitLab instance URL**: `http://10.0.0.80`
2. **Registration token**: `glrt-xxxxx`
3. **Runner description**: `dailydeenguide-runner`
4. **Runner tags**: `docker,dailydeen,linux`
5. **Executor**: `docker`
6. **Default Docker image**: `alpine:latest`

## Management Commands

### View Runner Status

```bash
# List all registered runners
docker exec -it gitlab-runner-dailydeenguide gitlab-runner list
docker exec -it gitlab-runner-wizardsofts gitlab-runner list
docker exec -it gitlab-runner-gibd gitlab-runner list

# Verify runner connection
docker exec -it gitlab-runner-dailydeenguide gitlab-runner verify
```

### View Configuration

```bash
# View config file
cat /mnt/data/docker/gitlab-runner/dailydeenguide/config/config.toml

# Or from inside container
docker exec -it gitlab-runner-dailydeenguide cat /etc/gitlab-runner/config.toml
```

### Restart Runners

```bash
# Restart all runners
docker-compose restart

# Restart specific runner
docker restart gitlab-runner-dailydeenguide
```

### View Logs

```bash
# All runners
docker-compose logs -f

# Specific runner
docker logs -f gitlab-runner-dailydeenguide
```

### Unregister Runner

```bash
# Unregister all runners from a container
docker exec -it gitlab-runner-dailydeenguide gitlab-runner unregister --all-runners

# Unregister specific runner by name
docker exec -it gitlab-runner-dailydeenguide gitlab-runner unregister --name dailydeenguide-runner
```

## Configuration Tuning

### Adjust Concurrent Jobs

Edit the configuration file:

```bash
nano /mnt/data/docker/gitlab-runner/dailydeenguide/config/config.toml
```

Change:
```toml
concurrent = 4  # Number of jobs that can run simultaneously
```

Restart the runner:
```bash
docker restart gitlab-runner-dailydeenguide
```

### Example config.toml

```toml
concurrent = 4
check_interval = 0

[session_server]
  session_timeout = 1800

[[runners]]
  name = "dailydeenguide-runner"
  url = "http://10.0.0.80"
  token = "glrt-xxxxx"
  executor = "docker"
  [runners.docker]
    tls_verify = false
    image = "alpine:latest"
    privileged = false
    disable_entrypoint_overwrite = false
    oom_kill_disable = false
    disable_cache = false
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
    network_mode = "gibd-network"
    shm_size = 0
```

## Using Runners in GitLab CI/CD

### .gitlab-ci.yml Example

```yaml
stages:
  - build
  - test
  - deploy

build-job:
  stage: build
  tags:
    - dailydeen  # Use the runner with this tag
  script:
    - echo "Building application..."
    - docker --version

test-job:
  stage: test
  tags:
    - dailydeen
  image: node:18-alpine
  script:
    - echo "Running tests..."
    - npm --version

deploy-job:
  stage: deploy
  tags:
    - dailydeen
  only:
    - main
  script:
    - echo "Deploying to production..."
```

### Docker Build Example

```yaml
build-docker-image:
  stage: build
  tags:
    - dailydeen
  image: docker:24-cli
  script:
    - docker build -t myapp:latest .
    - docker images
```

### Access Other Services

Since runners are on `gibd-network`, they can access other services:

```yaml
integration-test:
  stage: test
  tags:
    - dailydeen
  image: curlimages/curl:latest
  script:
    - curl http://gitlab:80
    - curl http://postgres:5432
```

## Backup and Restore

### Backup Configuration

```bash
# Backup all runner configs
sudo tar -czf gitlab-runner-backup-$(date +%Y%m%d).tar.gz \
  /mnt/data/docker/gitlab-runner/
```

### Restore Configuration

```bash
# Stop runners
docker-compose down

# Restore from backup
sudo tar -xzf gitlab-runner-backup-YYYYMMDD.tar.gz -C /

# Start runners
docker-compose up -d
```

## Troubleshooting

### Runner Not Appearing in GitLab

```bash
# Verify runner is registered
docker exec -it gitlab-runner-dailydeenguide gitlab-runner verify

# Check GitLab connectivity
docker exec -it gitlab-runner-dailydeenguide curl http://10.0.0.80

# Restart runner
docker restart gitlab-runner-dailydeenguide
```

### Jobs Failing with Docker Errors

```bash
# Check Docker socket permissions
ls -la /var/run/docker.sock

# Test Docker access from runner
docker exec -it gitlab-runner-dailydeenguide docker ps
```

### Runner Using Wrong Network

Check the config.toml file:
```bash
cat /mnt/data/docker/gitlab-runner/dailydeenguide/config/config.toml | grep network
```

Should show: `network_mode = "gibd-network"`

### Permission Denied Errors

```bash
# Ensure proper ownership
sudo chown -R root:root /mnt/data/docker/gitlab-runner

# Check socket permissions
sudo chmod 666 /var/run/docker.sock  # Use with caution
```

## Security Considerations

### Docker Socket Access

**⚠️ Warning**: All runners share the Docker socket, which means:
- Jobs can access and control all containers on the host
- Untrusted code in CI jobs could be dangerous
- Only run trusted code in these runners

### Recommendations

1. Use different runners for untrusted projects
2. Consider Docker-in-Docker for isolation
3. Audit CI/CD pipeline configurations regularly
4. Restrict runner tags to specific projects
5. Use protected branches and environments

## Maintenance

### Update Runners

```bash
# Pull latest image
docker-compose pull

# Recreate containers
docker-compose up -d

# Verify
docker-compose ps
```

### Clean Up Docker Resources

```bash
# Remove unused images (run from host)
docker system prune -a

# Or from a runner container
docker exec -it gitlab-runner-dailydeenguide docker system prune -f
```

### Monitor Disk Usage

```bash
# Check config directory sizes
du -sh /mnt/data/docker/gitlab-runner/*

# Check Docker disk usage
docker system df
```

## Support

- **GitLab Documentation**: https://docs.gitlab.com/runner/
- **Docker Documentation**: https://docs.docker.com/
- **GitLab Instance**: http://10.0.0.80

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start all runners |
| `docker-compose down` | Stop all runners |
| `docker-compose ps` | Check runner status |
| `docker-compose logs -f` | View live logs |
| `docker exec -it <container> gitlab-runner list` | List registered runners |
| `docker exec -it <container> gitlab-runner verify` | Verify runner connection |
| `docker restart <container>` | Restart specific runner |

## Tags Summary

| Runner | Tags | Purpose |
|--------|------|---------|
| dailydeenguide | `docker`, `dailydeen`, `linux` | Daily Deen Guide CI/CD |
| wizardsofts | `docker`, `wizardsofts`, `linux` | Wizardsofts CI/CD |
| gibd | `docker`, `gibd`, `linux` | GIBD CI/CD |
```
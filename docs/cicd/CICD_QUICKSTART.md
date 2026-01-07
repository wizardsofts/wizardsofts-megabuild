# CI/CD Quick Start Guide

**Target Server**: 10.0.0.84
**Deployment Method**: GitLab CI/CD with GitLab Runner
**Sudo Password**: `29Dec2#24`

---

## Overview

This guide will help you set up automated deployments from GitLab to the 84 server in **less than 30 minutes**.

```
GitLab Push → GitLab CI/CD → GitLab Runner (84 server) → Docker Compose Deploy
```

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] GitLab account with project access
- [ ] SSH access to 10.0.0.84 server
- [ ] sudo password: `29Dec2#24`
- [ ] Git installed on your local machine
- [ ] SSH key pair generated

---

## Quick Setup (30 Minutes)

### Step 1: Server Setup (10 minutes)

#### Option A: Automated Setup (Recommended)

```bash
# From your local machine
ssh deploy@10.0.0.84

# Download and run setup script
curl -o setup.sh https://raw.githubusercontent.com/your-repo/wizardsofts-megabuild/main/scripts/setup-server-84.sh
chmod +x setup.sh
./setup.sh
```

#### Option B: Manual Setup

```bash
ssh deploy@10.0.0.84

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# Install GitLab Runner
sudo curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
sudo chmod +x /usr/local/bin/gitlab-runner
sudo useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
sudo gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
sudo gitlab-runner start
sudo usermod -aG docker gitlab-runner

# Create deployment directory
sudo mkdir -p /opt/wizardsofts-megabuild
sudo chown -R deploy:deploy /opt/wizardsofts-megabuild
```

### Step 2: Register GitLab Runner (5 minutes)

```bash
# On the 84 server
sudo gitlab-runner register
```

When prompted:
- **GitLab URL**: `https://gitlab.com/` (or your GitLab URL)
- **Registration token**: Get from GitLab → Settings → CI/CD → Runners
- **Description**: `wizardsofts-megabuild-runner-84`
- **Tags**: `deploy,docker,production,84-server`
- **Executor**: `docker`
- **Default image**: `alpine:latest`

Configure for Docker-in-Docker:
```bash
sudo nano /etc/gitlab-runner/config.toml
```

Update `[[runners]]` section:
```toml
[[runners]]
  [runners.docker]
    privileged = true
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
```

Restart runner:
```bash
sudo gitlab-runner restart
```

### Step 3: Set GitLab CI/CD Variables (5 minutes)

In GitLab project → Settings → CI/CD → Variables:

| Variable | Value | Protected | Masked |
|----------|-------|-----------|--------|
| `SSH_PRIVATE_KEY` | [Your SSH private key] | ✓ | ✓ |
| `DB_PASSWORD` | [Your PostgreSQL password] | ✓ | ✓ |
| `OPENAI_API_KEY` | [Your OpenAI key] | ✓ | ✓ |

#### Generate SSH Key (if needed):
```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gitlab_ci_rsa
cat ~/.ssh/gitlab_ci_rsa  # Copy to SSH_PRIVATE_KEY variable
cat ~/.ssh/gitlab_ci_rsa.pub  # Copy to server
```

Add public key to server:
```bash
ssh deploy@10.0.0.84
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys  # Paste public key
chmod 600 ~/.ssh/authorized_keys
```

### Step 4: Initial Deployment (10 minutes)

```bash
# On the 84 server
cd /opt/wizardsofts-megabuild
git clone https://gitlab.com/your-username/wizardsofts-megabuild.git .

# Create .env
cp .env.example .env
nano .env  # Update with actual values

# First deployment
docker compose --profile gibd-quant up -d
```

### Step 5: Trigger Pipeline

```bash
# On your local machine
cd /path/to/wizardsofts-megabuild
git add .
git commit -m "Configure CI/CD for 84 server"
git push origin main
```

In GitLab:
1. Go to **CI/CD** → **Pipelines**
2. Wait for build to complete
3. Click **"Play"** on `deploy-to-84` job
4. Monitor deployment logs

---

## Usage

### Automatic Deployment

1. Make changes to code
2. Commit and push to `main` branch
3. GitLab CI/CD automatically runs tests and builds
4. Click **"Play"** on `deploy-to-84` job in pipeline
5. Deployment happens automatically

### Manual Deployment (Local Script)

```bash
# From your local machine
./scripts/deploy-to-84.sh
```

This script:
- Syncs files to 84 server
- Builds and restarts Docker services
- Runs health checks

### Rollback

If deployment fails:
```bash
# In GitLab pipeline
Click "Play" on the "rollback" job
```

Or manually on server:
```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild
git reset --hard HEAD~1
docker compose --profile gibd-quant up -d --build
```

---

## Verification

### Check Services

```bash
# Eureka Dashboard
open http://10.0.0.84:8761

# Frontend
open http://10.0.0.84:3001

# Health checks
curl http://10.0.0.84:8761/actuator/health  # Eureka
curl http://10.0.0.84:8080/actuator/health  # Gateway
curl http://10.0.0.84:5001/health           # Signal
curl http://10.0.0.84:5002/health           # NLQ
curl http://10.0.0.84:5003/health           # Calibration
curl http://10.0.0.84:5004/health           # Agent
```

### View Logs

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild

# All services
docker compose logs -f

# Specific service
docker compose logs -f gibd-quant-signal
```

---

## Troubleshooting

### Runner Not Picking Up Jobs

```bash
# On 84 server
sudo gitlab-runner restart
sudo journalctl -u gitlab-runner -f
```

Verify runner is online in GitLab: Settings → CI/CD → Runners

### Deployment Fails

Check pipeline logs in GitLab for errors.

Common fixes:
```bash
# On 84 server

# Restart Docker
sudo systemctl restart docker

# Check disk space
df -h

# Clean old images
docker system prune -a -f

# Check permissions
sudo chown -R deploy:deploy /opt/wizardsofts-megabuild
```

### Service Won't Start

```bash
# Check service logs
docker compose logs gibd-quant-signal

# Check .env file
cat .env

# Manually restart
docker compose restart gibd-quant-signal
```

---

## CI/CD Pipeline Stages

1. **Detect Changes**: Identifies which services changed
2. **Test**: Runs tests for changed services
3. **Build**: Builds Docker images
4. **Deploy**: Deploys to 84 server (manual trigger)
5. **Health Check**: Verifies all services are running

### Pipeline Flow

```
Push to main
    ↓
Detect changed services
    ↓
Run tests (Spring Boot + Python)
    ↓
Build Docker images
    ↓
[Manual Approval]
    ↓
Deploy to 84 server
    ↓
Health checks
```

---

## Deployment Profiles

The system supports multiple deployment profiles:

```bash
# Shared services only (infrastructure)
docker compose --profile shared up -d

# GIBD Quant-Flow (includes shared)
docker compose --profile gibd-quant up -d

# Everything
docker compose --profile all up -d
```

Current CI/CD uses: `gibd-quant`

---

## Security Notes

1. **Never commit** `.env` file or secrets
2. **Mark variables** as "Protected" and "Masked" in GitLab
3. **Rotate SSH keys** regularly
4. **Use HTTPS** for production
5. **Firewall rules**: Only allow necessary ports
6. **Regular updates**: Keep server and Docker updated

---

## Monitoring

### GitLab Pipeline Status

- Green: All tests passed, ready to deploy
- Yellow/Running: Tests or build in progress
- Red: Tests failed or build error
- Manual: Waiting for manual deployment approval

### Server Health

```bash
# CPU and Memory
ssh deploy@10.0.0.84 'htop'

# Docker stats
ssh deploy@10.0.0.84 'docker stats'

# Disk usage
ssh deploy@10.0.0.84 'df -h'
```

---

## Advanced Configuration

### Change Deployment Profile

Edit `.gitlab-ci.yml`:
```yaml
variables:
  COMPOSE_PROFILE: "all"  # or "shared"
```

### Add Deployment Environments

Create staging environment:
```yaml
deploy-to-staging:
  stage: deploy
  variables:
    DEPLOY_HOST: "10.0.0.85"
  script:
    - # Same deployment script
  environment:
    name: staging
```

### Enable Automatic Deployment

Remove `when: manual` from `.gitlab-ci.yml`:
```yaml
deploy-to-84:
  stage: deploy
  # Remove: when: manual
  only:
    - main
```

---

## Quick Reference

### Useful Commands

```bash
# SSH to server
ssh deploy@10.0.0.84

# View runner status
sudo gitlab-runner list

# Restart runner
sudo gitlab-runner restart

# View logs
docker compose logs -f

# Rebuild service
docker compose up -d --build gibd-quant-signal

# Check Eureka registration
curl http://localhost:8761/eureka/apps
```

### Important Files

- `.gitlab-ci.yml` - CI/CD pipeline configuration
- `docker-compose.yml` - Service definitions
- `.env` - Environment variables (on server)
- `scripts/deploy-to-84.sh` - Manual deployment script
- `scripts/setup-server-84.sh` - Server setup script

### Ports

| Service | Port |
|---------|------|
| Frontend | 3001 |
| Gateway | 8080 |
| Eureka | 8761 |
| Signal | 5001 |
| NLQ | 5002 |
| Calibration | 5003 |
| Agent | 5004 |
| Trades API | 8182 |
| Company API | 8183 |
| News API | 8184 |

---

## Support

For detailed setup instructions: `docs/GITLAB_RUNNER_SETUP.md`
For deployment guide: `DEPLOYMENT.md`

Need help? Check:
1. GitLab pipeline logs
2. Server logs: `docker compose logs -f`
3. Runner logs: `sudo journalctl -u gitlab-runner -f`

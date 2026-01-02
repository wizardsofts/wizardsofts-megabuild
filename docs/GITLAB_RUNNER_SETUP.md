# GitLab Runner Setup for 10.0.0.84 Server

This guide explains how to set up GitLab Runner on the 84 server for automated deployments.

## Prerequisites

- Ubuntu/Debian server at 10.0.0.84
- sudo access (password: `29Dec2#24`)
- GitLab project with admin access
- Docker installed on the server

---

## Part 1: Server Setup

### 1. SSH into the Server

```bash
ssh deploy@10.0.0.84
# Enter password when prompted
```

### 2. Install Docker (if not already installed)

```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker compose version
```

### 3. Install GitLab Runner

```bash
# Download the binary for your system
sudo curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64

# Give it permissions to execute
sudo chmod +x /usr/local/bin/gitlab-runner

# Create a GitLab Runner user
sudo useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash

# Install and run as service
sudo gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
sudo gitlab-runner start

# Verify installation
gitlab-runner --version
```

### 4. Add GitLab Runner User to Docker Group

```bash
sudo usermod -aG docker gitlab-runner
sudo systemctl restart docker
```

### 5. Create Deployment Directory

```bash
sudo mkdir -p /opt/wizardsofts-megabuild
sudo chown -R deploy:deploy /opt/wizardsofts-megabuild
```

---

## Part 2: Register GitLab Runner

### 1. Get Registration Token

In your GitLab project:
1. Go to **Settings** → **CI/CD** → **Runners**
2. Click **"Expand"** next to **"Specific runners"**
3. Note the **registration token** (starts with `GR1348...`)

### 2. Register the Runner

```bash
sudo gitlab-runner register
```

You'll be prompted for:

1. **GitLab instance URL**:
   ```
   https://gitlab.com/
   ```
   (or your self-hosted GitLab URL)

2. **Registration token**:
   ```
   [Paste the token from GitLab]
   ```

3. **Description**:
   ```
   wizardsofts-megabuild-runner-84
   ```

4. **Tags**:
   ```
   deploy,docker,production,84-server
   ```

5. **Executor**:
   ```
   docker
   ```

6. **Default Docker image**:
   ```
   alpine:latest
   ```

### 3. Verify Registration

In GitLab:
1. Go to **Settings** → **CI/CD** → **Runners**
2. You should see your runner listed under **"Specific runners"**
3. The status should be **green** (online)

On the server:
```bash
sudo gitlab-runner list
```

---

## Part 3: Configure Runner for Docker-in-Docker

Edit the GitLab Runner config to enable Docker-in-Docker:

```bash
sudo nano /etc/gitlab-runner/config.toml
```

Update the `[[runners]]` section:

```toml
[[runners]]
  name = "wizardsofts-megabuild-runner-84"
  url = "https://gitlab.com/"
  token = "YOUR_RUNNER_TOKEN"
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
```

**Important changes**:
- `privileged = true` - Required for Docker-in-Docker
- `volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]` - Mount Docker socket

Restart the runner:
```bash
sudo gitlab-runner restart
```

---

## Part 4: Set Up GitLab CI/CD Variables

In your GitLab project:

1. Go to **Settings** → **CI/CD** → **Variables**
2. Click **"Add variable"** for each of the following:

### Required Variables

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `SSH_PRIVATE_KEY` | [Your SSH private key] | ✓ | ✓ |
| `DB_PASSWORD` | [PostgreSQL password] | ✓ | ✓ |
| `OPENAI_API_KEY` | [OpenAI API key] | ✓ | ✓ |
| `DEPLOY_HOST` | `10.0.0.84` | ✓ | - |
| `DEPLOY_USER` | `deploy` | ✓ | - |
| `DEPLOY_PATH` | `/opt/wizardsofts-megabuild` | ✓ | - |

### Optional Variables (Analytics)

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `GA_MEASUREMENT_ID` | `G-XXXXXXXXXX` | - | - |
| `ADSENSE_CLIENT_ID` | `ca-pub-XXXXXXXXXXXXXXXX` | - | - |

### Generating SSH Key Pair

On your local machine or the 84 server:

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "gitlab-ci@wizardsofts-megabuild" -f ~/.ssh/gitlab_ci_rsa

# Display private key (copy this to SSH_PRIVATE_KEY variable)
cat ~/.ssh/gitlab_ci_rsa

# Display public key
cat ~/.ssh/gitlab_ci_rsa.pub
```

Add the public key to the server:
```bash
# On the 84 server
ssh deploy@10.0.0.84
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Paste the public key
chmod 600 ~/.ssh/authorized_keys
```

---

## Part 5: Initial Deployment Setup

### 1. SSH into the Server

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild
```

### 2. Clone the Repository (First Time Only)

```bash
# Clone your GitLab repository
git clone https://gitlab.com/your-username/wizardsofts-megabuild.git .

# Or if using SSH
git clone git@gitlab.com:your-username/wizardsofts-megabuild.git .
```

### 3. Create .env File

```bash
cp .env.example .env
nano .env
```

Update with actual values:
```bash
DB_PASSWORD=your_actual_postgres_password
OPENAI_API_KEY=sk-your-actual-openai-key
GA_MEASUREMENT_ID=G-XXXXXXXXXX
ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
```

### 4. Initial Docker Compose Setup

```bash
# Build all images
docker compose build

# Start services
docker compose --profile gibd-quant up -d

# Check status
docker compose ps
```

### 5. Verify Services

```bash
# Check Eureka
curl http://localhost:8761/actuator/health

# Check Gateway
curl http://localhost:8080/actuator/health

# Check Python services
curl http://localhost:5001/health  # Signal
curl http://localhost:5002/health  # NLQ
curl http://localhost:5003/health  # Calibration
curl http://localhost:5004/health  # Agent

# Check Frontend
curl http://localhost:3001
```

---

## Part 6: Trigger Deployment from GitLab

### Automatic Deployment (on push to main)

1. Push to the `main` branch
2. GitLab CI/CD pipeline will automatically:
   - Detect changed services
   - Run tests
   - Build Docker images
   - Wait for manual approval
3. Click **"Play"** button on the `deploy-to-84` job
4. Monitor deployment logs
5. Automatic health checks run after deployment

### Manual Deployment

1. Go to **CI/CD** → **Pipelines**
2. Click **"Run pipeline"**
3. Select branch: `main`
4. Click **"Run pipeline"**
5. Wait for build stage to complete
6. Click **"Play"** on `deploy-to-84` job

### Rollback

If deployment fails:
1. Go to the failed pipeline
2. Click **"Play"** on the `rollback` job
3. This will revert to the previous commit and redeploy

---

## Part 7: Monitoring and Troubleshooting

### View Runner Logs

```bash
# On the 84 server
sudo gitlab-runner --debug run

# Or check service logs
sudo journalctl -u gitlab-runner -f
```

### View Deployment Logs

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild

# View all logs
docker compose logs -f

# View specific service
docker compose logs -f gibd-quant-signal
```

### Common Issues

#### Runner Not Picking Up Jobs
```bash
# Restart runner
sudo gitlab-runner restart

# Verify runner is online in GitLab UI
# Settings → CI/CD → Runners
```

#### Docker Permission Denied
```bash
# Add gitlab-runner to docker group
sudo usermod -aG docker gitlab-runner
sudo systemctl restart docker
```

#### Deployment Fails on rsync
```bash
# Install rsync on server
sudo apt-get install rsync
```

#### SSH Connection Fails
```bash
# Verify SSH key is correct
ssh -i ~/.ssh/gitlab_ci_rsa deploy@10.0.0.84

# Check authorized_keys on server
cat ~/.ssh/authorized_keys
```

---

## Part 8: Advanced Configuration

### Enable Concurrent Jobs

Edit `/etc/gitlab-runner/config.toml`:
```toml
concurrent = 4  # Allow 4 concurrent jobs
```

### Set Up Caching

Add to `config.toml`:
```toml
[[runners]]
  [runners.cache]
    Type = "s3"
    Shared = true
    [runners.cache.s3]
      ServerAddress = "s3.amazonaws.com"
      BucketName = "your-cache-bucket"
      BucketLocation = "us-east-1"
```

### Set Resource Limits

Add to `config.toml`:
```toml
[[runners]]
  [runners.docker]
    cpus = "2"
    memory = "4g"
```

---

## Testing the Setup

Run this test pipeline to verify everything works:

```yaml
# Add to .gitlab-ci.yml
test-runner:
  stage: test
  script:
    - echo "GitLab Runner is working!"
    - docker --version
    - docker compose version
  tags:
    - 84-server
```

---

## Security Best Practices

1. **Rotate Tokens**: Regularly rotate runner registration tokens
2. **Limit Access**: Use protected branches and environments
3. **Secure Variables**: Mark sensitive variables as "Masked" and "Protected"
4. **SSH Keys**: Use separate SSH keys for CI/CD (not your personal key)
5. **Firewall**: Restrict access to port 22 (SSH) to known IPs
6. **HTTPS**: Use HTTPS for GitLab communications
7. **Audit Logs**: Regularly review GitLab audit logs

---

## Maintenance

### Update GitLab Runner

```bash
sudo gitlab-runner stop
sudo curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
sudo chmod +x /usr/local/bin/gitlab-runner
sudo gitlab-runner start
```

### Cleanup Old Docker Images

```bash
# On the 84 server
docker system prune -a -f
docker volume prune -f
```

### Backup

```bash
# Backup GitLab Runner config
sudo cp /etc/gitlab-runner/config.toml /etc/gitlab-runner/config.toml.backup

# Backup deployment directory
sudo tar -czf /tmp/megabuild-backup.tar.gz /opt/wizardsofts-megabuild
```

---

## Support

For issues:
1. Check runner logs: `sudo journalctl -u gitlab-runner -f`
2. Check Docker logs: `docker compose logs -f`
3. Verify runner status in GitLab: Settings → CI/CD → Runners
4. Test SSH connection: `ssh deploy@10.0.0.84`

## References

- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [Docker Executor Documentation](https://docs.gitlab.com/runner/executors/docker.html)
- [GitLab CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/)

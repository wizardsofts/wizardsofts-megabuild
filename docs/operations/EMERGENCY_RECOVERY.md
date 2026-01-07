# Emergency Service Recovery Guide

## Current Status: Services Down ❌

**Date**: December 27, 2025
**Server**: 10.0.0.84
**Issue**: Backend services and/or Traefik reverse proxy not responding

### Symptoms:
- ❌ HTTP requests to 10.0.0.84 timeout or fail
- ❌ All service ports (3000, 8080, 8761, etc.) closed
- ❌ Traefik dashboard (8080) not accessible
- ❌ API endpoints not responding

---

## Root Cause Analysis

### Likely Causes:

1. **Services Crashed/Stopped**
   - Docker containers stopped unexpectedly
   - Out of disk space on server
   - Out of memory (OOM killed)
   - Service dependencies failed to start

2. **Deployment Issues**
   - `docker-compose --profile gibd-quant up -d` command failed silently
   - Missing .env file or environment variables
   - Docker daemon crashed or stopped
   - Volume mount issues

3. **Network Issues**
   - Network adapter stopped
   - Firewall rules blocking services
   - Docker network corrupted

---

## Emergency Recovery Steps

### Step 1: SSH Into Server

```bash
# Using password authentication (key-based may not work)
ssh wizardsofts@10.0.0.84
# When prompted for password, enter: 29Dec2#24

# Alternative if SSH password fails:
ssh -o PubkeyAuthentication=no wizardsofts@10.0.0.84
```

### Step 2: Check Docker Status

Once SSH'd into server, run:

```bash
# Check if Docker daemon is running
sudo systemctl status docker

# If Docker is stopped, start it
sudo systemctl start docker

# Check Docker containers
docker ps -a

# Check for errors
docker logs traefik
docker logs gibd-quant-web
```

### Step 3: Navigate to Deployment Directory

```bash
cd /opt/wizardsofts-megabuild
# OR
cd /home/wizardsofts/wizardsofts-megabuild

# Check if directory exists
ls -la
```

### Step 4: Verify Environment Configuration

```bash
# Check if .env file exists
ls -la .env

# Check required variables
grep "DB_PASSWORD\|OPENAI_API_KEY" .env

# If .env missing, check for example
ls -la .env.example

# Copy example to .env if needed
cp .env.example .env
# Then edit .env with actual values
```

### Step 5: Clean Up and Restart

```bash
# Stop all containers
docker-compose down

# Remove volumes if corrupted (WARNING: deletes data)
docker-compose down -v

# Pull latest code
git pull origin master

# Rebuild images
docker-compose build traefik
docker-compose build gibd-quant-web

# Start with gibd-quant profile (includes all backend services)
docker-compose --profile gibd-quant up -d

# Wait for services to start (2-5 minutes)
sleep 120

# Check status
docker-compose ps
```

### Step 6: Verify Services Are Healthy

```bash
# Check Traefik
curl http://localhost:80/

# Check API Gateway
curl http://localhost:8080/actuator/health

# Check Eureka
curl http://localhost:8761/actuator/health

# Check frontend
curl http://localhost:3000/
```

---

## Quick Recovery Script

Copy and paste this on the server to recover quickly:

```bash
#!/bin/bash
set -e

DEPLOY_PATH="/opt/wizardsofts-megabuild"
SUDO_PASSWORD="${SUDO_PASSWORD:?Set SUDO_PASSWORD environment variable}"

echo "=== Emergency Recovery Script ==="

# Navigate to deployment directory
cd $DEPLOY_PATH || { echo "Directory not found"; exit 1; }

# Verify Docker is running
echo "Checking Docker status..."
sudo systemctl status docker || sudo systemctl start docker

# Check for .env
if [ ! -f ".env" ]; then
    echo "ERROR: .env not found!"
    echo "Please create .env with required variables:"
    echo "  DB_PASSWORD=<your-password>"
    echo "  OPENAI_API_KEY=sk-<your-key>"
    exit 1
fi

# Stop existing containers
echo "Stopping containers..."
docker-compose down || true

# Pull latest code
echo "Pulling latest code..."
git pull origin master

# Rebuild critical images
echo "Rebuilding Docker images..."
docker-compose build --no-cache traefik
docker-compose build --no-cache gibd-quant-web

# Start all services
echo "Starting services with gibd-quant profile..."
docker-compose --profile gibd-quant up -d

# Wait for services
echo "Waiting for services to start..."
sleep 120

# Check status
echo "=== Service Status ==="
docker-compose ps

echo "=== Recovery Complete ==="
echo "Test endpoints:"
echo "  Frontend: curl http://localhost:3000/"
echo "  API Gateway: curl http://localhost:8080/actuator/health"
echo "  Eureka: curl http://localhost:8761/actuator/health"
```

---

## Preventing Future Issues

### 1. Monitor Container Status

```bash
# Create a monitoring script that checks every 5 minutes
# Add to crontab: */5 * * * * /opt/check-services.sh

#!/bin/bash
REQUIRED_CONTAINERS=("traefik" "gibd-quant-web" "ws-gateway" "ws-discovery")
NOTIFY_EMAIL="admin@wizardsofts.com"

for container in "${REQUIRED_CONTAINERS[@]}"; do
    if ! docker ps | grep -q "$container"; then
        echo "Container $container is down!" | mail -s "Alert: $container down" $NOTIFY_EMAIL
        # Auto-restart
        cd /opt/wizardsofts-megabuild
        docker-compose up -d $container
    fi
done
```

### 2. Set Up Log Rotation

```bash
# Check Docker logs
docker logs -f traefik
docker logs -f gibd-quant-web

# Set up log rotation in /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10"
  }
}
```

### 3. Configure Auto-Restart

Update docker-compose.yml services:

```yaml
services:
  traefik:
    restart: unless-stopped

  gibd-quant-web:
    restart: unless-stopped

  ws-gateway:
    restart: unless-stopped
```

### 4. Set Up Health Checks

All services should have health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Disk Space Issues

If services won't start due to disk space:

```bash
# Check disk usage
df -h

# Check Docker usage
docker system df

# Clean up dangling images and containers
docker system prune -a --volumes

# Check specific directory sizes
du -sh /var/lib/docker/*
du -sh /opt/wizardsofts-megabuild/*
```

---

## Memory Issues

If Docker containers are being killed:

```bash
# Check system memory
free -h

# Check Docker memory limits
docker inspect <container-name> | grep -A 10 "Memory"

# Check OOM events
sudo dmesg | grep -i oom

# Increase memory limits in docker-compose.yml
services:
  gibd-quant-web:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

---

## Network Issues

If network is the problem:

```bash
# Check Docker networks
docker network ls

# Check network connectivity between containers
docker exec gibd-quant-web ping ws-gateway

# Rebuild networks if corrupted
docker network prune

# Restart Docker daemon
sudo systemctl restart docker
```

---

## Firewall Issues

If firewall is blocking ports:

```bash
# Check firewall status
sudo ufw status

# Allow Docker ports if needed
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp

# If using iptables
sudo iptables -L -n
```

---

## Database Issues

If postgres won't start:

```bash
# Check postgres container logs
docker logs postgres

# Verify postgres volume
docker inspect postgres | grep -A 10 "Mounts"

# If data corrupted, backup and recover
docker exec postgres pg_dump -U gibd ws_gibd_dse_daily_trades > backup.sql

# Rebuild postgres
docker-compose down postgres
docker volume rm <postgres-volume>
docker-compose up -d postgres
```

---

## Rollback to Last Working Version

If current deployment is broken:

```bash
cd /opt/wizardsofts-megabuild

# Check git log
git log --oneline -10

# Rollback to previous commit
git reset --hard HEAD~1

# Or rollback to specific commit
git reset --hard 0aafcb3

# Rebuild and restart
docker-compose build
docker-compose --profile gibd-quant down
docker-compose --profile gibd-quant up -d
```

---

## Contact Information

If recovery fails, contact:
- **Admin**: admin@wizardsofts.com
- **DevOps**: devops@wizardsofts.com
- **Server**: 10.0.0.84
- **SSH User**: wizardsofts
- **SSH Password**: 29Dec2#24

---

## Documentation References

- [COMING_SOON_DEPLOYMENT_GUIDE.md](./COMING_SOON_DEPLOYMENT_GUIDE.md)
- [docs/DEPLOYMENT_SUMMARY_84.md](./docs/DEPLOYMENT_SUMMARY_84.md)
- [docker-compose.yml](./docker-compose.yml)
- [traefik/dynamic_conf.yml](./traefik/dynamic_conf.yml)

---

## Last Known Good State

- **Commit**: 611c721 - docs: Add Coming Soon deployment guide
- **Date**: December 27, 2025
- **Status**: Code complete, deployment pending
- **Services**: Not running (requires manual start with full environment setup)

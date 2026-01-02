# GIBD News Server Deployment Guide

**Target Server:** 10.0.0.84
**Date:** December 31, 2025
**Status:** Production Deployment Instructions

---

## Overview

This guide explains how to deploy and run GIBD News scrapers on server 10.0.0.84 after local testing is complete.

**Deployment Options:**
1. **Docker Compose** (Simple, good for single server)
2. **Kubernetes CronJobs** (Production, scalable, recommended)
3. **Traditional Cron** (Legacy, not recommended)

---

## Prerequisites

### Server Access

```bash
# SSH into production server
ssh username@10.0.0.84

# Verify Docker is installed
docker --version
docker-compose --version

# Verify Git is installed
git --version
```

### Required Software on Server

- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Git**: 2.0+
- **Kubernetes** (if using CronJobs): v1.28+

---

## Option 1: Docker Compose Deployment (Recommended for Testing)

### Step 1: Clone Repository

```bash
# SSH into server
ssh username@10.0.0.84

# Clone megabuild repository
cd /opt/apps  # or your preferred location
git clone https://gitlab.wizardsofts.com/wizardsofts/megabuild.git
cd megabuild

# Or if already cloned, pull latest changes
git pull origin master
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.gibd-news .env.gibd-news.local

# Edit with production values
nano .env.gibd-news.local
```

**Production Configuration:**
```bash
# ==========================================
# Production Configuration for 10.0.0.84
# ==========================================

# API Keys
GIBD_DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
GIBD_OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx  # Optional

# Email Configuration
GIBD_EMAIL_SENDER=gibd-news@guardianinvestmentbd.com
GIBD_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Gmail app password
GIBD_EMAIL_RECIPIENTS=team@guardianinvestmentbd.com,alerts@guardianinvestmentbd.com
GIBD_EMAIL_ADMIN=admin@guardianinvestmentbd.com

# Database Configuration (Local on 10.0.0.84)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ws_gibd_news_database
POSTGRES_USER=ws_gibd
POSTGRES_PASSWORD=your-secure-postgres-password

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=ws_gibd_dse_daily_trades
MYSQL_USER=ws_gibd
MYSQL_PASSWORD=your-secure-mysql-password

# Service URLs (Local services on 10.0.0.84)
GIBD_API_BASE_URL=http://localhost:8080/GIBD-NEWS-SERVICE
GIBD_TRADES_API_BASE_URL=http://localhost:8080/GIBD-TRADES

# OR if using Docker services:
# GIBD_API_BASE_URL=http://ws-news:8184
# GIBD_TRADES_API_BASE_URL=http://ws-trades:8185

# Application Profile
ACTIVE_PROFILE=docker

# File Paths
GIBD_DATA_PATH=/app/data
GIBD_LOGS_PATH=/app/logs
```

**Secure the file:**
```bash
chmod 600 .env.gibd-news.local
chown root:root .env.gibd-news.local
```

### Step 3: Build Docker Images

```bash
# Build all GIBD News images (takes 15-20 min first time)
docker-compose --profile gibd-news build

# Or build specific service
docker-compose build gibd-fetch-financialexpress

# Verify images built
docker images | grep gibd
```

**Speed up future builds:**
```bash
# Option A: Save images to registry (recommended)
docker tag gibd-news:latest registry.wizardsofts.com/gibd/gibd-news:latest
docker push registry.wizardsofts.com/gibd/gibd-news:latest

# Option B: Save to local tar file (backup)
docker save gibd-news:latest | gzip > /backup/gibd-news-$(date +%Y%m%d).tar.gz
```

### Step 4: Test Individual Services

```bash
# Test Financial Express scraper
docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-financialexpress

# Check logs
docker-compose logs --tail=100 gibd-fetch-financialexpress

# Verify data was saved
docker volume inspect wizardsofts-megabuild_gibd-news-data
ls -la /var/lib/docker/volumes/wizardsofts-megabuild_gibd-news-data/_data/
```

### Step 5: Run All Services

```bash
# Run news scrapers in sequence
docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-tbsnews
docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-financialexpress
docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-dailystar
docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-news-details

# Run stock scrapers
docker-compose --env-file .env.gibd-news.local run --rm gibd-scrape-share-price
docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-stock-data

# Run AI processing
docker-compose --env-file .env.gibd-news.local run --rm gibd-news-summarizer
docker-compose --env-file .env.gibd-news.local run --rm gibd-sentiment-analyzer
```

---

## Option 2: Kubernetes CronJob Deployment (Production Recommended)

### Architecture

```
Kubernetes Cluster
├── Namespace: gibd-news
├── ConfigMap: gibd-news-config
├── Secret: gibd-news-secrets
└── CronJobs (8 total)
    ├── fetch-tbsnews (0 * * * *) - hourly
    ├── fetch-financialexpress (0 * * * *) - hourly
    ├── fetch-dailystar (0 * * * *) - hourly
    ├── fetch-news-details (5 * * * *) - hourly at :05
    ├── scrape-share-price (* 4-7 * * 0-4) - every min during market hours
    ├── fetch-stock-data (0 11 * * 0-4) - daily at 11am weekdays
    ├── news-summarizer (0 17 * * *) - daily at 5pm
    └── sentiment-analyzer (30 17 * * *) - daily at 5:30pm
```

### Step 1: Create Namespace

```bash
kubectl create namespace gibd-news
kubectl config set-context --current --namespace=gibd-news
```

### Step 2: Create Secrets

```bash
# Create from environment file
kubectl create secret generic gibd-news-secrets \
  --from-env-file=.env.gibd-news.local \
  --namespace=gibd-news

# Or create manually
kubectl create secret generic gibd-news-secrets \
  --from-literal=GIBD_DEEPSEEK_API_KEY='sk-xxxx' \
  --from-literal=GIBD_EMAIL_PASSWORD='xxxx xxxx xxxx xxxx' \
  --from-literal=POSTGRES_PASSWORD='your-password' \
  --from-literal=MYSQL_PASSWORD='your-password' \
  --namespace=gibd-news

# Verify
kubectl get secrets -n gibd-news
kubectl describe secret gibd-news-secrets -n gibd-news
```

### Step 3: Create ConfigMap

Create `k8s/configmaps/gibd-news-config.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gibd-news-config
  namespace: gibd-news
data:
  GIBD_EMAIL_SENDER: "gibd-news@guardianinvestmentbd.com"
  GIBD_EMAIL_RECIPIENTS: "team@guardianinvestmentbd.com"
  GIBD_EMAIL_ADMIN: "admin@guardianinvestmentbd.com"

  POSTGRES_HOST: "postgres.default.svc.cluster.local"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "ws_gibd_news_database"
  POSTGRES_USER: "ws_gibd"

  MYSQL_HOST: "mysql.default.svc.cluster.local"
  MYSQL_PORT: "3306"
  MYSQL_DB: "ws_gibd_dse_daily_trades"
  MYSQL_USER: "ws_gibd"

  GIBD_API_BASE_URL: "http://ws-news.default.svc.cluster.local:8184"
  GIBD_TRADES_API_BASE_URL: "http://ws-trades.default.svc.cluster.local:8185"

  ACTIVE_PROFILE: "docker"
  GIBD_DATA_PATH: "/app/data"
  GIBD_LOGS_PATH: "/app/logs"
```

Apply:
```bash
kubectl apply -f k8s/configmaps/gibd-news-config.yaml
```

### Step 4: Create CronJobs

Create `k8s/cronjobs/gibd-news/fetch-financialexpress.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-fetch-financialexpress
  namespace: gibd-news
spec:
  schedule: "0 * * * *"  # Every hour
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: scraper
            image: registry.wizardsofts.com/gibd/gibd-news:latest
            command: ["python", "scripts/fetch_urls_financial_express.py"]
            envFrom:
            - configMapRef:
                name: gibd-news-config
            - secretRef:
                name: gibd-news-secrets
            volumeMounts:
            - name: data
              mountPath: /app/data
            - name: logs
              mountPath: /app/logs
            resources:
              requests:
                memory: "512Mi"
                cpu: "250m"
              limits:
                memory: "1Gi"
                cpu: "500m"
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: gibd-news-data-pvc
          - name: logs
            persistentVolumeClaim:
              claimName: gibd-news-logs-pvc
```

Create similar files for all 8 scrapers with appropriate schedules.

### Step 5: Create Persistent Volume Claims

Create `k8s/pvcs/gibd-news-storage.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gibd-news-data-pvc
  namespace: gibd-news
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs-storage  # Or your storage class
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gibd-news-logs-pvc
  namespace: gibd-news
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs-storage
  resources:
    requests:
      storage: 5Gi
```

Apply:
```bash
kubectl apply -f k8s/pvcs/gibd-news-storage.yaml
```

### Step 6: Deploy All CronJobs

```bash
# Apply all CronJobs
kubectl apply -f k8s/cronjobs/gibd-news/

# Verify
kubectl get cronjobs -n gibd-news
kubectl get jobs -n gibd-news

# Test run manually (don't wait for schedule)
kubectl create job --from=cronjob/gibd-fetch-financialexpress test-run-1 -n gibd-news

# Check logs
kubectl logs -f job/test-run-1 -n gibd-news
```

### Step 7: Monitor CronJobs

```bash
# Watch jobs
kubectl get jobs -n gibd-news --watch

# Check specific job logs
kubectl logs -l job-name=gibd-fetch-financialexpress-1234567890 -n gibd-news

# Describe CronJob
kubectl describe cronjob gibd-fetch-financialexpress -n gibd-news

# Check resource usage
kubectl top pods -n gibd-news
```

---

## Option 3: Traditional Cron (Legacy)

**Not recommended**, but here's how to replicate the old cron setup:

### Step 1: Create Shell Scripts

Create `/opt/gibd-news/scripts/run_fetch_financialexpress.sh`:

```bash
#!/bin/bash
set -e

cd /opt/apps/megabuild

docker-compose --env-file .env.gibd-news.local run --rm gibd-fetch-financialexpress >> /var/log/gibd-news/fetch-fe.log 2>&1
```

Make executable:
```bash
chmod +x /opt/gibd-news/scripts/run_fetch_financialexpress.sh
```

### Step 2: Add to Crontab

```bash
crontab -e
```

Add:
```cron
# GIBD News Scrapers

# News URL Scrapers (hourly)
0 * * * * /opt/gibd-news/scripts/run_fetch_tbsnews.sh
0 * * * * /opt/gibd-news/scripts/run_fetch_financialexpress.sh
0 * * * * /opt/gibd-news/scripts/run_fetch_dailystar.sh

# News Details Fetcher (hourly, 5 min after URL scrapers)
5 * * * * /opt/gibd-news/scripts/run_fetch_news_details.sh

# Stock Price Scraper (every minute during market hours: 4-7am, 8:00-8:30am, weekdays)
* 4-7 * * 0-4 /opt/gibd-news/scripts/run_scrape_share_price.sh
0-30 8 * * 0-4 /opt/gibd-news/scripts/run_scrape_share_price.sh

# Daily Stock Data (11am weekdays)
0 11 * * 0-4 /opt/gibd-news/scripts/run_fetch_stock_data.sh

# News Summarizer (5pm daily)
0 17 * * * /opt/gibd-news/scripts/run_news_summarizer.sh

# Sentiment Analyzer (5:30pm daily)
30 17 * * * /opt/gibd-news/scripts/run_sentiment_analyzer.sh
```

---

## Monitoring & Logging

### Logs Location

**Docker Compose:**
```bash
# Container logs
docker-compose logs -f gibd-fetch-financialexpress

# Volume logs
ls -la /var/lib/docker/volumes/wizardsofts-megabuild_gibd-news-logs/_data/

# Tail logs
tail -f /var/lib/docker/volumes/wizardsofts-megabuild_gibd-news-logs/_data/scraper.log
```

**Kubernetes:**
```bash
# Pod logs
kubectl logs -f deployment/gibd-fetch-financialexpress -n gibd-news

# PVC logs
kubectl exec -it <pod-name> -n gibd-news -- tail -f /app/logs/scraper.log
```

### Prometheus Metrics (Future Enhancement)

Add to scrapers:
```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
scrape_duration = Histogram('scrape_duration_seconds', 'Time spent scraping')
scrape_success = Counter('scrape_success_total', 'Successful scrapes')
scrape_failures = Counter('scrape_failures_total', 'Failed scrapes')

# In main():
start_http_server(8000)  # Expose metrics on :8000/metrics
```

### Grafana Dashboards

Create dashboard with panels:
- **Scrape Success Rate**: `scrape_success / (scrape_success + scrape_failures)`
- **Scrape Duration**: `scrape_duration_seconds`
- **News Articles Collected**: `news_articles_total`
- **Stock Prices Scraped**: `stock_prices_total`

### Alerting

**AlertManager rules:**
```yaml
groups:
- name: gibd-news
  interval: 5m
  rules:
  - alert: ScraperFailed
    expr: scrape_failures_total > 5
    for: 10m
    annotations:
      summary: "GIBD News scraper failing repeatedly"

  - alert: NoDataCollected
    expr: rate(news_articles_total[1h]) == 0
    for: 2h
    annotations:
      summary: "No news articles collected in 2 hours"
```

---

## Troubleshooting

### Issue 1: Container Can't Connect to Database

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**
1. Verify database is running:
   ```bash
   # Check PostgreSQL
   docker-compose ps postgres
   psql -h localhost -U ws_gibd -d ws_gibd_news_database

   # Check MySQL
   docker-compose ps mysql
   mysql -h localhost -u ws_gibd -p ws_gibd_dse_daily_trades
   ```

2. Check network connectivity:
   ```bash
   docker-compose run --rm gibd-fetch-financialexpress ping -c 3 postgres
   ```

3. Verify credentials in `.env.gibd-news.local`

### Issue 2: Selenium WebDriver Error

**Symptoms:**
```
selenium.common.exceptions.WebDriverException: Message: chrome not found
```

**Solutions:**
1. Verify Chrome installed in container:
   ```bash
   docker-compose run --rm gibd-fetch-tbsnews which google-chrome
   docker-compose run --rm gibd-fetch-tbsnews google-chrome --version
   ```

2. Check shm_size is set (should be 2GB):
   ```bash
   docker inspect gibd-fetch-tbsnews | grep -i shm
   ```

3. Rebuild image with Chrome:
   ```bash
   docker-compose build --no-cache gibd-fetch-tbsnews
   ```

### Issue 3: API Connection Timeout

**Symptoms:**
```
requests.exceptions.ConnectionError: HTTPConnectionPool(...): Max retries exceeded
```

**Solutions:**
1. Verify ws-news service is running:
   ```bash
   docker-compose ps ws-news
   curl http://localhost:8184/actuator/health
   ```

2. Check service URLs in `.env.gibd-news.local`:
   ```bash
   # Should be:
   GIBD_API_BASE_URL=http://ws-news:8184  # Docker network
   # OR
   GIBD_API_BASE_URL=http://localhost:8080/GIBD-NEWS-SERVICE  # Host network
   ```

3. Test connectivity:
   ```bash
   docker-compose run --rm gibd-fetch-financialexpress \
     curl -v http://ws-news:8184/actuator/health
   ```

### Issue 4: Out of Memory

**Symptoms:**
```
Killed
```

**Solutions:**
1. Check Docker resource limits:
   ```bash
   docker stats
   ```

2. Increase memory limits in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

3. For Kubernetes, update resources:
   ```yaml
   resources:
     limits:
       memory: "2Gi"
   ```

### Issue 5: Permission Denied Writing to Volumes

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/data/news.json'
```

**Solutions:**
1. Fix volume permissions:
   ```bash
   docker run --rm -v wizardsofts-megabuild_gibd-news-data:/data alpine \
     chown -R 1000:1000 /data
   ```

2. Or run container as root (not recommended):
   ```yaml
   user: "0:0"
   ```

---

## Health Checks

### Manual Health Check Script

Create `/opt/gibd-news/scripts/health_check.sh`:

```bash
#!/bin/bash

echo "=== GIBD News Health Check ==="
echo "Date: $(date)"
echo ""

# Check Docker
echo "1. Docker Status:"
docker info > /dev/null 2>&1 && echo "✓ Docker running" || echo "✗ Docker not running"

# Check Images
echo -e "\n2. Docker Images:"
docker images | grep gibd-news || echo "✗ No images found"

# Check Volumes
echo -e "\n3. Docker Volumes:"
docker volume ls | grep gibd-news || echo "✗ No volumes found"

# Check Database
echo -e "\n4. Database Connectivity:"
PGPASSWORD=your-password psql -h localhost -U ws_gibd -d ws_gibd_news_database -c "SELECT 1" > /dev/null 2>&1 \
  && echo "✓ PostgreSQL accessible" \
  || echo "✗ PostgreSQL not accessible"

# Check APIs
echo -e "\n5. API Endpoints:"
curl -s http://localhost:8080/GIBD-NEWS-SERVICE/actuator/health | grep UP > /dev/null \
  && echo "✓ ws-news API healthy" \
  || echo "✗ ws-news API unhealthy"

curl -s http://localhost:8080/GIBD-TRADES/actuator/health | grep UP > /dev/null \
  && echo "✓ ws-trades API healthy" \
  || echo "✗ ws-trades API unhealthy"

# Check Recent Scrapes
echo -e "\n6. Recent Data:"
LATEST_DATA=$(docker run --rm -v wizardsofts-megabuild_gibd-news-data:/data alpine \
  find /data -type f -name "*.json" -mtime -1 | wc -l)
echo "Files created in last 24h: $LATEST_DATA"

echo -e "\n=== Health Check Complete ==="
```

Run:
```bash
chmod +x /opt/gibd-news/scripts/health_check.sh
/opt/gibd-news/scripts/health_check.sh
```

---

## Backup & Recovery

### Backup Script

Create `/opt/gibd-news/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/gibd-news"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup data volume
docker run --rm \
  -v wizardsofts-megabuild_gibd-news-data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/gibd-news-data-$DATE.tar.gz /data

# Backup logs volume
docker run --rm \
  -v wizardsofts-megabuild_gibd-news-logs:/logs \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/gibd-news-logs-$DATE.tar.gz /logs

# Backup configuration
cp .env.gibd-news.local $BACKUP_DIR/env-$DATE.backup

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
ls -lh $BACKUP_DIR/*$DATE*
```

### Recovery

```bash
# Restore data volume
docker run --rm \
  -v wizardsofts-megabuild_gibd-news-data:/data \
  -v /backup/gibd-news:/backup \
  alpine sh -c "cd / && tar xzf /backup/gibd-news-data-20251231_120000.tar.gz"

# Restore logs volume
docker run --rm \
  -v wizardsofts-megabuild_gibd-news-logs:/logs \
  -v /backup/gibd-news:/backup \
  alpine sh -c "cd / && tar xzf /backup/gibd-news-logs-20251231_120000.tar.gz"
```

---

## Performance Optimization

### 1. Use Pre-built Base Image

See [DOCKER_IMAGE_MANAGEMENT.md](apps/gibd-news/DOCKER_IMAGE_MANAGEMENT.md)

### 2. Enable Parallel Scraping

Update scripts to run in parallel:
```python
from concurrent.futures import ThreadPoolExecutor

def scrape_url(url):
    # Your scraping logic
    pass

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(scrape_url, urls)
```

### 3. Implement Caching

Add Redis for caching:
```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

In Python:
```python
import redis
r = redis.Redis(host='redis', port=6379)

# Cache API responses
cached = r.get(f'news:{url}')
if cached:
    return json.loads(cached)
else:
    data = fetch_news(url)
    r.setex(f'news:{url}', 3600, json.dumps(data))
    return data
```

---

## Security Best Practices

### 1. Secrets Management

**Use Docker Secrets (Swarm mode):**
```bash
echo "sk-your-api-key" | docker secret create deepseek_api_key -
```

In docker-compose.yml:
```yaml
secrets:
  deepseek_api_key:
    external: true

services:
  gibd-fetch-financialexpress:
    secrets:
      - deepseek_api_key
```

**Use Kubernetes Secrets:**
```bash
kubectl create secret generic api-keys \
  --from-literal=deepseek-key='sk-xxxx' \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Network Isolation

```yaml
networks:
  gibd-internal:
    driver: bridge
    internal: true  # No external access
  gibd-external:
    driver: bridge
```

### 3. Read-only Root Filesystem

```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /app/data
```

---

## Rollback Plan

If deployment fails:

### 1. Stop New Services
```bash
docker-compose --profile gibd-news down
# OR
kubectl delete -f k8s/cronjobs/gibd-news/
```

### 2. Restore Old Cron
```bash
# On 10.0.0.84
crontab -e
# Restore old cron entries from backup
```

### 3. Verify Old System
```bash
# Run old scripts manually
/bin/bash /mnt/data/scheduled_tasks/tasks/scrape_news/run_scrape_dse_latest_share_price.sh
```

---

## Deployment Checklist

- [ ] **Pre-Deployment**
  - [ ] Repository cloned on server
  - [ ] `.env.gibd-news.local` configured with production values
  - [ ] Secrets secured (chmod 600)
  - [ ] Database credentials verified
  - [ ] API keys tested

- [ ] **Docker Compose**
  - [ ] Images built successfully
  - [ ] Test run completed (manual execution)
  - [ ] Volumes created and accessible
  - [ ] Logs directory writable
  - [ ] Health checks passing

- [ ] **Kubernetes** (if using)
  - [ ] Namespace created
  - [ ] Secrets and ConfigMaps applied
  - [ ] PVCs bound
  - [ ] CronJobs created
  - [ ] Manual job test successful

- [ ] **Monitoring**
  - [ ] Logs accessible
  - [ ] Health check script works
  - [ ] Metrics endpoint exposed (if using Prometheus)
  - [ ] Alerting configured

- [ ] **Backup**
  - [ ] Backup script tested
  - [ ] Restore procedure verified
  - [ ] Backup retention policy set

- [ ] **Documentation**
  - [ ] Runbook updated
  - [ ] Team trained on new system
  - [ ] Rollback plan documented
  - [ ] On-call rotation updated

---

## Quick Reference

### Common Commands

```bash
# Build
docker-compose build gibd-fetch-financialexpress

# Test
docker-compose run --rm gibd-fetch-financialexpress

# Logs
docker-compose logs -f gibd-fetch-financialexpress

# Clean up
docker-compose down
docker system prune -af

# Kubernetes
kubectl get cronjobs -n gibd-news
kubectl logs -f job/test-run-1 -n gibd-news
kubectl delete cronjob gibd-fetch-financialexpress -n gibd-news
```

### Important Files

- `/opt/apps/megabuild/docker-compose.yml` - Service definitions
- `/opt/apps/megabuild/.env.gibd-news.local` - Environment config
- `/opt/gibd-news/scripts/` - Helper scripts
- `/var/log/gibd-news/` - Application logs
- `/backup/gibd-news/` - Backup files

### Important URLs

- **Server**: 10.0.0.84
- **ws-news API**: http://10.0.0.84:8080/GIBD-NEWS-SERVICE
- **ws-trades API**: http://10.0.0.84:8080/GIBD-TRADES
- **PostgreSQL**: 10.0.0.84:5432
- **MySQL**: 10.0.0.84:3306

---

## Support

**Questions?** Contact:
- DevOps Team: devops@guardianinvestmentbd.com
- On-call Engineer: +880-xxx-xxx-xxxx

**Documentation:**
- [Integration Plan](GIBD_NEWS_MEGABUILD_INTEGRATION_PLAN.md)
- [Migration Guide](GIBD_NEWS_MIGRATION_GUIDE.md)
- [Docker Image Management](apps/gibd-news/DOCKER_IMAGE_MANAGEMENT.md)

---

**Last Updated:** December 31, 2025
**Maintained By:** DevOps Team

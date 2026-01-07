# GIBD News - Production to Megabuild Migration Guide

**Source Environment**: Server 10.0.0.84 (bare metal/VM with cron)
**Target Environment**: WizardSofts Megabuild (Docker Compose / Kubernetes)
**Date**: December 30, 2025

---

## ⚠️ PRE-MIGRATION CRITICAL ACTIONS

### 1. IMMEDIATE: Rotate Exposed API Key

Your OpenAI API key is exposed in `application-hp.properties`. **Do this first**:

```bash
# 1. Rotate the key at OpenAI
# Visit: https://platform.openai.com/api-keys
# - Revoke: [REDACTED]
# - Create new key

# 2. Store in GitLab CI/CD Variables
# GitLab → Settings → CI/CD → Variables
# Add: GIBD_OPENAI_API_KEY = [new-key]
# Protected: Yes, Masked: Yes

# 3. Update .env file (local/staging)
echo "GIBD_OPENAI_API_KEY=sk-new-key-here" >> .env

# 4. Remove from application-hp.properties
sed -i '/OPENAI_API_KEY/d' config/application-hp.properties
```

### 2. Audit for Other Exposed Secrets

```bash
# Search for potential secrets in config files
cd /Users/mashfiqurrahman/Workspace/guardianinvestmentbd/gibd-news
grep -r "password\|api_key\|secret\|token" config/ --ignore-case

# Expected findings that need migration to env vars:
# - Database passwords
# - Email passwords
# - DeepSeek API key
# - Any other API keys
```

---

## 📊 Current Production Environment

### Server: 10.0.0.84

**Databases:**
```
PostgreSQL (5432)
├── ws_gibd_news_database  # Main news database (used by ws-news API)
└── ws_gibd_news           # Alternative/backup DB?

MySQL (3306)
└── ws_gibd_dse_daily_trades  # Stock trading data
```

**User:** `ws_gibd` (for both PostgreSQL and MySQL)

**Services Running:**
- `ws-news` API (Spring Boot) - Port 8080
- `ws-trades` API (Spring Boot?) - Port 8080 (same port, different path)
- Likely behind Nginx/Tomcat reverse proxy

**File System:**
- Data: `/mnt/data/scheduled_tasks/data/raw`
- Logs: `/mnt/data/scheduled_tasks/logs`
- Output: `/mnt/data/scheduled_tasks/data`

**Cron Jobs:**
- Running as user on 10.0.0.84
- Executing shell scripts that invoke Docker Compose or Python directly

---

## 🎯 Target Megabuild Environment

### Network Configuration

```yaml
networks:
  gibd-network:
    driver: bridge

# All services connect to gibd-network
# Service discovery via DNS: http://ws-news:8184, http://ws-trades:8185
```

### Service URLs (Internal)

| Current (Production) | Megabuild (Docker) | Notes |
|----------------------|-------------------|-------|
| `http://localhost:8080/GIBD-NEWS-SERVICE` | `http://ws-news:8184` | ws-news API |
| `http://localhost:8080/GIBD-TRADES` | `http://ws-trades:8185` | ws-trades API |
| `10.0.0.84:5432` (PostgreSQL) | `postgres:5432` | Database server |
| `10.0.0.84:3306` (MySQL) | `mysql:3306` | MySQL server (if needed) |

### Database Strategy

**Option A: Keep External Database (Recommended for Phase 1)**
- Point services to `10.0.0.84:5432` and `10.0.0.84:3306`
- No data migration needed
- Services in containers, data stays on 10.0.0.84

**Option B: Migrate to Megabuild Database Container**
- Dump data from 10.0.0.84
- Import to containerized PostgreSQL/MySQL
- Update connection strings
- More complex but fully containerized

**Recommendation:** Use **Option A** initially, then migrate to **Option B** later.

---

## 📋 Step-by-Step Migration

### Phase 1: Prepare Megabuild Environment (2-3 hours)

#### 1.1 Copy Repository to Megabuild

```bash
# On your local machine
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Copy gibd-news folder
cp -r /Users/mashfiqurrahman/Workspace/guardianinvestmentbd/gibd-news \
      /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/apps/

# Verify
ls -la apps/gibd-news/
```

#### 1.2 Create Environment Configuration

**Create `.env.gibd-news` in megabuild root:**

```bash
# ===========================================
# GIBD News - Megabuild Environment
# ===========================================

# ---- API Keys (CRITICAL - Never commit!) ----
GIBD_DEEPSEEK_API_KEY=your-deepseek-key-here
GIBD_OPENAI_API_KEY=your-NEW-rotated-openai-key-here

# ---- Email Configuration ----
GIBD_EMAIL_SENDER=your-sender@gmail.com
GIBD_EMAIL_PASSWORD=your-gmail-app-password
GIBD_EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
GIBD_EMAIL_ADMIN=admin@example.com

# ---- Database Configuration (External) ----
# Using existing database on 10.0.0.84
POSTGRES_HOST=10.0.0.84
POSTGRES_PORT=5432
POSTGRES_DB=ws_gibd_news_database
POSTGRES_USER=ws_gibd
POSTGRES_PASSWORD=your-postgres-password-here

MYSQL_HOST=10.0.0.84
MYSQL_PORT=3306
MYSQL_DB=ws_gibd_dse_daily_trades
MYSQL_USER=ws_gibd
MYSQL_PASSWORD=your-mysql-password-here

# ---- Service URLs (Internal Docker) ----
GIBD_API_BASE_URL=http://ws-news:8184
GIBD_TRADES_API_BASE_URL=http://ws-trades:8185

# ---- LLM Configuration ----
GIBD_LLM_PROVIDER=deepseek
GIBD_DEEPSEEK_API_URL=https://api.deepseek.com
GIBD_OLLAMA_URL=http://ollama:11434
GIBD_OLLAMA_MODEL=llama3:8b

# ---- Application Profile ----
ACTIVE_PROFILE=docker

# ---- File Paths (Docker Volumes) ----
# These will be mounted from host
GIBD_DATA_PATH=/app/data
GIBD_LOGS_PATH=/app/logs
```

**Add to main `.env`:**
```bash
# At the bottom of megabuild .env
source .env.gibd-news
```

#### 1.3 Update Configuration Files

**Edit `apps/gibd-news/config/application-docker.properties`:**

```properties
[DEFAULT]
# Remove these - use environment variables instead
# OPENAI_API_KEY=  # REMOVED - Now in .env

# File paths (inside container)
base_file_path=/app/data/raw
log_file_path=/app/logs
output_file_path=/app/data

# API URLs (use env vars, these are fallbacks)
api_url_news_post=${GIBD_API_BASE_URL}/api/news
api_url_news_latest_by_tags=${GIBD_API_BASE_URL}/api/news/latest-by-tags
dse_daily_prices=${GIBD_TRADES_API_BASE_URL}/api/v1/dse-daily-prices
latest_price_date=${GIBD_TRADES_API_BASE_URL}/api/v1/dse-daily-prices/latest-price-date

[POSTGRES]
host=${POSTGRES_HOST:-10.0.0.84}
dbname=${POSTGRES_DB:-ws_gibd_news_database}
user=${POSTGRES_USER:-ws_gibd}
# password from env var only

[MYSQL]
host=${MYSQL_HOST:-10.0.0.84}
database=${MYSQL_DB:-ws_gibd_dse_daily_trades}
user=${MYSQL_USER:-ws_gibd}
port=${MYSQL_PORT:-3306}
# password from env var only

[LATEST_SHARE_PRICE_SCROLL]
base_url=https://www.dsebd.org/latest_share_price_scroll_l.php
latest_trades_url=${GIBD_TRADES_API_BASE_URL}/api/latest-trades

[DSEBD_NEWS_ARCHIEVE]
base_url=https://www.dsebd.org/old_news.php
news_url=${GIBD_API_BASE_URL}/api/news/dsebd

[UPDATE_SENTIMENT_SCORE]
PAGINATED_API_URL=${GIBD_API_BASE_URL}/api/news/search?minSentimentScore=-2&page={page}&size={size}
UPDATE_API_URL=${GIBD_API_BASE_URL}/api/news

# Keep other sections unchanged (THEDAILYSTAR, FINANCIALEXPRESS, etc.)
```

#### 1.4 Verify ws-trades Service Exists

```bash
# Check if ws-trades is in megabuild
ls -la apps/ws-trades/

# If not found, check docker-compose.yml
grep -n "ws-trades" docker-compose.yml

# If missing, you'll need to either:
# 1. Add ws-trades to megabuild (preferred)
# 2. Point to external ws-trades at 10.0.0.84:8080
# 3. Disable stock scraping features
```

**If ws-trades is missing**, temporarily point to external server:

```bash
# In .env.gibd-news
GIBD_TRADES_API_BASE_URL=http://10.0.0.84:8080/GIBD-TRADES
```

---

### Phase 2: Add Services to Docker Compose (3-4 hours)

#### 2.1 Update `docker-compose.yml`

Add these services to the megabuild `docker-compose.yml`:

```yaml
# ===========================================
# GIBD News Services
# ===========================================

# News URL Scrapers
gibd-fetch-tbsnews:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-tbsnews
  command: python scripts/fetch_urls_tbsnews.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  shm_size: '2gb'
  restart: "no"

gibd-fetch-financialexpress:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-fe
  command: python scripts/fetch_urls_financialexpress.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  restart: "no"

gibd-fetch-dailystar:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-dailystar
  command: python scripts/fetch_urls_thedailystar.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  shm_size: '2gb'
  restart: "no"

gibd-fetch-news-details:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-details
  command: python scripts/fetch_news_details.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  shm_size: '2gb'
  restart: "no"

# Stock Price Scrapers
gibd-scrape-share-price:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-scrape-price
  command: python scripts/scrape_dse_latest_share_price.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    - ws-news
    # Uncomment if ws-trades is in megabuild:
    # ws-trades:
    #   condition: service_healthy
  networks:
    - gibd-network
  shm_size: '2gb'
  restart: "no"

gibd-fetch-stock-data:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-stock
  command: python scripts/fetch_dse_daily_stock_data.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    - ws-news
  networks:
    - gibd-network
  restart: "no"

# AI Processing
gibd-news-summarizer:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-summarizer
  command: python scripts/news_summarizer.py --parallel --workers 3
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  restart: "no"

gibd-sentiment-analyzer:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-sentiment
  command: python scripts/update_sentiment_scores.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  restart: "no"

# Add to volumes section at bottom
volumes:
  gibd-news-data:
    driver: local
  gibd-news-logs:
    driver: local
```

#### 2.2 Build and Test

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Build gibd-news image
docker-compose build gibd-fetch-tbsnews

# Test single service
docker-compose run --rm gibd-fetch-tbsnews

# Check logs
docker-compose logs gibd-fetch-tbsnews

# Verify data was created
docker volume inspect wizardsofts-megabuild_gibd-news-data
```

---

### Phase 3: Cron Job Migration (4-5 hours)

You have two options: **Kubernetes CronJobs** (production) or **APScheduler** (simpler).

#### Option A: Kubernetes CronJobs (Recommended)

**Create `k8s/cronjobs/gibd-news/` directory:**

```bash
mkdir -p k8s/cronjobs/gibd-news
```

**1. Stock Price Scraper (Pre-market)**

`k8s/cronjobs/gibd-news/scrape-price-premarket.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-scrape-price-premarket
  namespace: gibd
spec:
  schedule: "* 4-7 * * 0-4"
  timeZone: "Asia/Dhaka"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 120  # 2 minutes max
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: scraper
            image: registry.wizardsofts.com/gibd-news:latest
            command: ["python", "scripts/scrape_dse_latest_share_price.py"]
            envFrom:
            - secretRef:
                name: gibd-news-secrets
            - configMapRef:
                name: gibd-news-config
            resources:
              requests:
                memory: "1Gi"
                cpu: "500m"
              limits:
                memory: "2Gi"
                cpu: "1"
            volumeMounts:
            - name: data
              mountPath: /app/data
            - name: logs
              mountPath: /app/logs
            - name: shm
              mountPath: /dev/shm
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: gibd-news-data
          - name: logs
            persistentVolumeClaim:
              claimName: gibd-news-logs
          - name: shm
            emptyDir:
              medium: Memory
              sizeLimit: 2Gi
```

**2. Stock Price Scraper (Market Open)**

`k8s/cronjobs/gibd-news/scrape-price-marketopen.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-scrape-price-marketopen
  namespace: gibd
spec:
  schedule: "0-30 8 * * 0-4"
  timeZone: "Asia/Dhaka"
  # ... rest same as premarket
```

**3. Daily Stock Data**

`k8s/cronjobs/gibd-news/fetch-stock-data.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-fetch-stock-data
  namespace: gibd
spec:
  schedule: "0 11 * * 0-4"
  timeZone: "Asia/Dhaka"
  # ... similar structure
```

**4. News Scrapers**

`k8s/cronjobs/gibd-news/scrape-news.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-scrape-news
  namespace: gibd
spec:
  schedule: "0 * * * *"
  timeZone: "Asia/Dhaka"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          # Run all 3 scrapers in sequence
          - name: fetch-tbsnews
            image: registry.wizardsofts.com/gibd-news:latest
            command: ["python", "scripts/fetch_urls_tbsnews.py"]
            # ... env and volumes
          - name: fetch-fe
            image: registry.wizardsofts.com/gibd-news:latest
            command: ["python", "scripts/fetch_urls_financialexpress.py"]
          - name: fetch-dailystar
            image: registry.wizardsofts.com/gibd-news:latest
            command: ["python", "scripts/fetch_urls_thedailystar.py"]
          - name: fetch-details
            image: registry.wizardsofts.com/gibd-news:latest
            command: ["python", "scripts/fetch_news_details.py"]
```

**5. News Summarizer**

`k8s/cronjobs/gibd-news/summarize-news.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-summarize-news
  namespace: gibd
spec:
  schedule: "0 17 * * *"
  timeZone: "Asia/Dhaka"
  # ... similar structure
```

**Deploy:**
```bash
kubectl apply -f k8s/cronjobs/gibd-news/

# Verify
kubectl get cronjobs -n gibd
kubectl get jobs -n gibd
```

#### Option B: APScheduler (Docker Compose Only)

If not using Kubernetes, create a scheduler service:

**Create `apps/gibd-news/scripts/scheduler.py`:**

```python
"""
APScheduler-based cron job scheduler for GIBD News.
Runs all scheduled tasks within a single container.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import subprocess
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone='Asia/Dhaka')

def run_script(script_name, description):
    """Execute a Python script and log results."""
    logger.info(f"Starting: {description}")
    try:
        result = subprocess.run(
            ['python', f'scripts/{script_name}'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        if result.returncode == 0:
            logger.info(f"✓ {description} completed successfully")
            if result.stdout:
                logger.debug(result.stdout)
        else:
            logger.error(f"✗ {description} failed (exit {result.returncode})")
            logger.error(result.stderr)
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {description} timed out after 10 minutes")
    except Exception as e:
        logger.error(f"✗ {description} raised exception: {e}")

def job_listener(event):
    """Listen to job events for monitoring."""
    if event.exception:
        logger.error(f"Job {event.job_id} failed with exception")
    else:
        logger.info(f"Job {event.job_id} executed successfully")

# Add listener
scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# ============================================
# SCHEDULE DEFINITION
# ============================================

# Stock price scraping (every minute, 4-7 AM, Mon-Fri)
scheduler.add_job(
    lambda: run_script('scrape_dse_latest_share_price.py', 'Stock Price Scrape (Pre-market)'),
    CronTrigger(minute='*', hour='4-7', day_of_week='mon-fri'),
    id='scrape_price_premarket',
    max_instances=1,
    misfire_grace_time=30
)

# Stock price scraping (every minute, 8:00-8:30 AM, Mon-Fri)
scheduler.add_job(
    lambda: run_script('scrape_dse_latest_share_price.py', 'Stock Price Scrape (Market Open)'),
    CronTrigger(minute='0-30', hour='8', day_of_week='mon-fri'),
    id='scrape_price_marketopen',
    max_instances=1,
    misfire_grace_time=30
)

# Daily stock data (11 AM, Mon-Fri)
scheduler.add_job(
    lambda: run_script('fetch_dse_daily_stock_data.py', 'Daily Stock Data Fetch'),
    CronTrigger(minute='0', hour='11', day_of_week='mon-fri'),
    id='fetch_daily_stock',
    max_instances=1
)

# News scraping pipeline (every hour)
def scrape_news_pipeline():
    """Run all news scrapers in sequence."""
    run_script('fetch_urls_tbsnews.py', 'TBS News URL Fetch')
    run_script('fetch_urls_financialexpress.py', 'Financial Express URL Fetch')
    run_script('fetch_urls_thedailystar.py', 'Daily Star URL Fetch')
    run_script('fetch_news_details.py', 'News Details Fetch')

scheduler.add_job(
    scrape_news_pipeline,
    CronTrigger(minute='0'),  # Every hour
    id='scrape_news',
    max_instances=1
)

# News summarization (5 PM daily)
scheduler.add_job(
    lambda: run_script('news_summarizer.py', 'News Summarization'),
    CronTrigger(minute='0', hour='17'),
    id='summarize_news',
    max_instances=1
)

# Sentiment analysis (6 PM daily, after summarization)
scheduler.add_job(
    lambda: run_script('update_sentiment_scores.py', 'Sentiment Analysis'),
    CronTrigger(minute='0', hour='18'),
    id='sentiment_analysis',
    max_instances=1
)

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("GIBD News Scheduler Starting")
    logger.info("=" * 60)
    logger.info(f"Loaded {len(scheduler.get_jobs())} jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.id}: {job.trigger}")
    logger.info("=" * 60)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down...")
```

**Add scheduler service to `docker-compose.yml`:**

```yaml
gibd-news-scheduler:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-scheduler
  command: python scripts/scheduler.py
  env_file:
    - .env
    - .env.gibd-news
  environment:
    - ACTIVE_PROFILE=docker
  volumes:
    - gibd-news-data:/app/data
    - gibd-news-logs:/app/logs
  depends_on:
    ws-news:
      condition: service_healthy
  networks:
    - gibd-network
  shm_size: '2gb'
  restart: unless-stopped  # Keep running!
  healthcheck:
    test: ["CMD", "pgrep", "-f", "scheduler.py"]
    interval: 60s
    timeout: 10s
    retries: 3
```

**Start scheduler:**
```bash
docker-compose up -d gibd-news-scheduler

# Monitor
docker-compose logs -f gibd-news-scheduler
```

---

### Phase 4: Parallel Run & Validation (1-2 weeks)

**Run old and new systems in parallel to ensure data consistency:**

```bash
# Week 1: Parallel run
# - Keep old cron jobs running on 10.0.0.84
# - Start new scheduler/cronjobs in megabuild
# - Compare outputs daily

# Check data consistency
diff /mnt/data/scheduled_tasks/data/news_$(date +%Y%m%d).json \
     /path/to/docker/volume/gibd-news-data/news_$(date +%Y%m%d).json

# Monitor error rates
tail -f /mnt/data/scheduled_tasks/logs/error_log_*.log
docker-compose logs gibd-scheduler | grep ERROR

# Week 2: Gradual cutover
# - Disable non-critical old cron jobs
# - Monitor new system for 3-5 days
# - If stable, disable all old cron jobs

# Final cutover
crontab -e  # On 10.0.0.84
# Comment out all GIBD news cron jobs
```

---

### Phase 5: Cleanup (After successful cutover)

```bash
# On server 10.0.0.84

# 1. Archive old data
tar -czf gibd-news-archive-$(date +%Y%m%d).tar.gz \
    /mnt/data/scheduled_tasks/data \
    /mnt/data/scheduled_tasks/logs

# 2. Move to backup location
mv gibd-news-archive-*.tar.gz /backup/archives/

# 3. Remove old cron scripts (after 30-day verification period)
# rm -rf /mnt/data/scheduled_tasks/tasks/scrape_news/
# rm -rf /mnt/data/scheduled_tasks/tasks/llm_tasks/

# 4. Keep database running (if external)
# PostgreSQL and MySQL on 10.0.0.84 remain active
```

---

## 🔒 Security Checklist

- [ ] Rotate OpenAI API key
- [ ] Move all secrets to environment variables
- [ ] Remove secrets from `application-hp.properties`
- [ ] Add `.env*` to `.gitignore`
- [ ] Use GitLab CI/CD variables for production secrets
- [ ] Enable secret masking in GitLab
- [ ] Audit all config files for exposed credentials
- [ ] Set up secret scanning in CI/CD pipeline

---

## 📊 Validation Tests

After migration, verify:

```bash
# 1. News scraping works
docker-compose run --rm gibd-fetch-tbsnews
# Expected: JSON files in data/tbsnews/

# 2. Data reaches ws-news API
curl http://localhost:8184/api/news/search?tags=tbsnews&size=1
# Expected: Recent articles returned

# 3. Stock scraper works
docker-compose run --rm gibd-scrape-share-price
# Expected: Data posted to ws-trades API

# 4. Summarizer works
docker-compose run --rm gibd-news-summarizer
# Expected: PDF report generated, email sent

# 5. Scheduler is running
docker-compose ps gibd-scheduler
# Expected: Status "Up"

docker-compose logs gibd-scheduler | grep "Job.*executed"
# Expected: Job execution logs
```

---

## 🆘 Rollback Plan

If migration fails:

```bash
# 1. Stop megabuild services
docker-compose down gibd-news-scheduler
# OR
kubectl delete cronjobs -n gibd -l app=gibd-news

# 2. Re-enable old cron jobs on 10.0.0.84
crontab -e
# Uncomment all GIBD news cron lines

# 3. Verify old system resumes
tail -f /mnt/data/scheduled_tasks/logs/error_log_*.log

# 4. Investigate issues in megabuild
docker-compose logs gibd-fetch-tbsnews
# Fix issues and retry migration
```

---

## 📞 Support Contacts

- **Primary**: Platform Team (#gibd-news Slack)
- **Database**: DBA Team (for 10.0.0.84 access)
- **Infrastructure**: DevOps Team (for K8s/Docker issues)

---

## ✅ Migration Checklist

### Pre-Migration
- [ ] Rotate exposed OpenAI API key
- [ ] Audit and secure all secrets
- [ ] Backup production data (tar.gz archive)
- [ ] Verify ws-trades service availability
- [ ] Get database credentials from secure vault

### Phase 1: Prepare
- [ ] Copy gibd-news to megabuild apps/
- [ ] Create `.env.gibd-news` with all secrets
- [ ] Update `application-docker.properties`
- [ ] Build Docker image successfully
- [ ] Test single service run

### Phase 2: Integration
- [ ] Add all services to docker-compose.yml
- [ ] Create Docker volumes
- [ ] Test each service individually
- [ ] Verify network connectivity
- [ ] Confirm database access from containers

### Phase 3: Scheduling
- [ ] Create K8s CronJobs OR APScheduler
- [ ] Deploy scheduler
- [ ] Verify first cron execution
- [ ] Monitor for 24 hours

### Phase 4: Validation
- [ ] Run parallel for 1 week
- [ ] Compare outputs daily
- [ ] Monitor error rates
- [ ] Gradual cutover
- [ ] Full production cutover

### Phase 5: Cleanup
- [ ] Archive old data
- [ ] Disable old cron jobs
- [ ] Remove old scripts (after 30 days)
- [ ] Update documentation
- [ ] Team training on new system

---

**END OF MIGRATION GUIDE**

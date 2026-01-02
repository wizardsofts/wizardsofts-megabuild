# GIBD News System - Megabuild Integration Plan

**Date:** December 30, 2025
**Status:** Draft
**Owner:** DevOps/Platform Team

---

## Executive Summary

This document provides a comprehensive analysis of the GIBD News system and a detailed plan for its integration into the WizardSofts megabuild infrastructure. The system consists of two main components:

1. **ws-news**: A Spring Boot REST API service (already partially integrated)
2. **gibd-intelligence**: Python-based news scraping and processing scripts (currently running via cron)

The integration aims to containerize all components, optimize scheduling, improve reliability, and align with the megabuild's infrastructure standards.

---

## 1. Current System Architecture

### 1.1 ws-news Service (Spring Boot)

**Location:** `apps/ws-news/`

**Technology Stack:**
- Framework: Spring Boot 3.4.1
- Java Version: 17
- Database: PostgreSQL
- Dependencies: Spring Cloud (Config, Eureka), Spring Data JPA, Actuator

**Key Features:**
- RESTful API for news management
- Port: 8184
- Database: `ws_gibd_news_database` (PostgreSQL on 10.0.0.84:5432)
- Service Discovery: Eureka Client
- Configuration: Spring Cloud Config

**API Endpoints:**
```
POST   /api/news                 - Create single news item
POST   /api/news/dsebd           - Bulk create DSEBD news
GET    /api/news/{id}            - Get news by ID
GET    /api/news/search          - Search news (with pagination, filtering)
GET    /api/news/latest-by-tags  - Get latest news grouped by tags
PUT    /api/news                 - Update news items (batch)
```

**Data Model:**
```java
News {
  id: Long
  url: String (unique)
  title: String
  subtitle: String
  date: LocalDateTime
  content: String
  tags: String
  sentimentScore: Float
  scrapedAt: LocalDateTime
  embedding: byte[]
}
```

**Docker Configuration:**
- ✅ Dockerfile exists (multi-stage Maven build)
- ✅ Already in docker-compose.yml
- ✅ Profiles: ["shared", "gibd-quant", "all"]
- ✅ Health check configured
- ✅ Eureka integration

**Status:** **PARTIALLY INTEGRATED** - Service exists in docker-compose but not fully tested in megabuild context.

---

### 1.2 gibd-intelligence Scripts (Python)

**Location:** `apps/gibd-intelligence/scripts/`

**Technology Stack:**
- Python 3.9+
- Key Libraries: Selenium, BeautifulSoup4, Requests, PyMySQL, psycopg2, OpenAI, pandas, fpdf

**Scripts:**

| Script | Purpose | Data Source | Target Database |
|--------|---------|-------------|-----------------|
| `scrape_amrastock_daily_news.py` | Scrape DSE news from AmraStock | https://www.amarstock.com/dse-news | MySQL (?) |
| `scrape_dsebd_news_archieve.py` | Scrape historical news from DSEBD | https://www.dsebd.org/old_news.php | ws-news API |
| `fetch_dse_daily_stock_data.py` | Fetch daily stock prices | DSE | Database |
| `scrape_dse_stock_price.py` | Scrape live stock prices | DSE | Database |
| `news_summarizer.py` | Summarize news using DeepSeek LLM | ws-news API | Email/PDF |
| `fetch_openai_news_explanation.py` | Generate news explanations | ws-news API | Database |

**Current Cron Schedule:**
```cron
# DSE Share Price Scraping (every minute during market hours)
* 4-7 * * 0-4     /bin/bash /mnt/data/scheduled_tasks/tasks/scrape_news/run_scrape_dse_latest_share_price.sh

# DSE Share Price Scraping (first 30 mins of 8AM hour)
0-30 8 * * 0-4    /bin/bash /mnt/data/scheduled_tasks/tasks/scrape_news/run_scrape_dse_latest_share_price.sh

# DSE Daily Stock Data (11AM weekdays)
0 11 * * 0-4      /bin/bash /mnt/data/scheduled_tasks/tasks/scrape_news/cron_fetch_dse_daily_stock_data.sh

# News Portal Scraping (every hour)
0 * * * *         /bin/bash /mnt/data/scheduled_tasks/tasks/scrape_news/cron_scrape_news_portals.sh

# News Summarization (5PM daily)
0 17 * * *        /bin/bash /mnt/data/scheduled_tasks/tasks/llm_tasks/cron_news_summarizer.sh
```

**Status:** **NOT INTEGRATED** - Scripts run on external server (10.0.0.84) via cron.

---

## 2. System Functionality Analysis

### 2.1 Core Capabilities

1. **News Data Collection**
   - Multi-source scraping (AmraStock, DSEBD)
   - Historical and real-time data
   - Duplicate detection via URL uniqueness

2. **Data Storage**
   - Centralized PostgreSQL database
   - RESTful API for data access
   - Support for embeddings and sentiment scores

3. **Data Processing**
   - LLM-based summarization (DeepSeek)
   - Entity extraction
   - Action item generation
   - PDF report generation

4. **Stock Price Tracking**
   - Real-time price scraping during market hours
   - Daily consolidated data fetch
   - Historical price tracking

5. **Distribution**
   - Email delivery of summarized reports
   - PDF generation for archival
   - API access for downstream systems

### 2.2 Integration Points

**Inbound:**
- External news websites (scraping)
- ws-news API (for news data retrieval)

**Outbound:**
- PostgreSQL database (ws_gibd_news_database)
- Email (SMTP - Gmail)
- PDF files (local filesystem)
- ws-news API (for data ingestion)

---

## 3. Requirements Analysis

### 3.1 Functional Requirements

| Requirement | Current Status | Priority |
|-------------|----------------|----------|
| News scraping from multiple sources | ✅ Implemented | High |
| RESTful API for news access | ✅ Implemented | High |
| Duplicate prevention | ✅ Implemented (URL unique) | High |
| Scheduled data collection | ⚠️ External cron | High |
| LLM-based summarization | ✅ Implemented | Medium |
| Email notifications | ✅ Implemented | Medium |
| Search and filtering | ✅ Implemented | High |
| Sentiment analysis | 🔴 Partial (field exists) | Low |
| Vector embeddings | 🔴 Partial (field exists) | Low |

### 3.2 Non-Functional Requirements

| Requirement | Current Status | Priority |
|-------------|----------------|----------|
| Containerization | ⚠️ Partial (only ws-news) | High |
| High availability | 🔴 Missing | Medium |
| Monitoring/Logging | 🔴 Missing | High |
| Error handling/Retry | 🔴 Minimal | High |
| Configuration management | ⚠️ Hard-coded values | High |
| Secret management | 🔴 Exposed in code | Critical |
| CI/CD integration | ⚠️ Jenkinsfile exists | Medium |
| Database migrations | 🔴 Manual (ddl-auto=none) | Medium |

### 3.3 Infrastructure Requirements

**Compute:**
- ws-news: 512MB-1GB RAM (Spring Boot)
- news-scraper: 1-2GB RAM (Selenium/Chrome)
- news-processor: 2-4GB RAM (LLM inference if local)

**Storage:**
- PostgreSQL database (current size unknown)
- PDF reports (ephemeral or archival)
- Logs

**Network:**
- Outbound HTTP/HTTPS for scraping
- SMTP for email (port 587)
- Internal service communication (Eureka)

**Dependencies:**
- PostgreSQL 13+
- Chrome/Chromium (for Selenium)
- Python 3.9+
- Java 17
- Spring Cloud Config Server
- Eureka Server

---

## 4. Gap Analysis

### 4.1 Critical Gaps

1. **🔴 Security Issues**
   - API keys and database passwords hard-coded in `news_summarizer.py` (lines 25, 29, 32)
   - SMTP credentials exposed
   - No secrets management

2. **🔴 Infrastructure Gaps**
   - Python scripts not containerized
   - Cron jobs running on external server
   - No orchestration for scheduled tasks
   - No health monitoring for scripts

3. **🔴 Reliability Issues**
   - No retry mechanisms for failed scraping
   - No dead letter queue for failed jobs
   - Single point of failure (one cron server)
   - No alerting on failures

### 4.2 Major Gaps

4. **⚠️ Configuration Management**
   - Mixed database references (MySQL vs PostgreSQL)
   - Environment-specific configs hard-coded
   - No centralized configuration

5. **⚠️ Observability**
   - No structured logging
   - No metrics collection
   - No distributed tracing
   - Limited error visibility

6. **⚠️ Data Quality**
   - Sentiment scores not populated
   - Embeddings not generated
   - No data validation
   - No schema versioning

### 4.3 Minor Gaps

7. **⚡ Performance**
   - Inefficient cron schedules (every minute unnecessary)
   - No caching layer
   - Sequential processing (could be parallel)
   - Selenium overhead (could use headless alternatives)

8. **⚡ Developer Experience**
   - No local development setup docs
   - Manual testing required
   - No integration tests
   - Missing API documentation

---

## 5. Optimized Cron Schedule Recommendations

### 5.1 Current Issues

1. **Over-fetching**: Running every minute (4-7 AM) creates 240+ executions
2. **No Rate Limiting**: Could trigger anti-scraping measures
3. **Resource Waste**: Most executions find no new data
4. **Overlap Risk**: Jobs could overlap if execution time > 1 minute

### 5.2 Optimized Schedule

```cron
# Pre-market stock price scraping (every 5 minutes)
*/5 4-7 * * 0-4   /usr/local/bin/run_scrape_dse_share_price.sh

# Market open scraping (every 2 minutes during first 30 mins)
*/2 8 * * 0-4     /usr/local/bin/run_scrape_dse_share_price.sh

# Mid-day stock price check (every 15 minutes during trading hours)
*/15 9-14 * * 0-4 /usr/local/bin/run_scrape_dse_share_price.sh

# End-of-day data consolidation (11:30 AM to avoid overlap)
30 11 * * 0-4     /usr/local/bin/run_fetch_dse_daily_stock_data.sh

# News portal scraping (every 2 hours during business hours)
0 6-20/2 * * *    /usr/local/bin/run_scrape_news_portals.sh

# News summarization (6 PM, after markets close)
0 18 * * *        /usr/local/bin/run_news_summarizer.sh

# Weekend/Holiday news catchup (once on Saturday morning)
0 9 * * 6         /usr/local/bin/run_scrape_news_portals.sh
```

### 5.3 Alternative: Event-Driven Architecture

Instead of cron, consider:
- **Kubernetes CronJobs** for scheduling
- **Apache Airflow** for complex DAG workflows
- **Message Queue** (RabbitMQ/Redis) for async processing
- **Change Data Capture** (CDC) for real-time updates

---

## 6. Megabuild Integration Plan

### 6.1 Phase 1: Containerization (Week 1-2)

**Objective**: Containerize Python scripts and ensure all services run in Docker.

**Tasks:**

1. **Create gibd-news-scraper Service**
   ```dockerfile
   # apps/gibd-news-scraper/Dockerfile
   FROM python:3.11-slim

   # Install Chrome for Selenium
   RUN apt-get update && apt-get install -y \
       chromium chromium-driver \
       && rm -rf /var/lib/apt/lists/*

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY scripts/ ./scripts/
   COPY config/ ./config/

   # Entry point for cron or specific script
   CMD ["python", "-u", "scripts/run_scrapers.py"]
   ```

2. **Create gibd-news-processor Service**
   ```dockerfile
   # apps/gibd-news-processor/Dockerfile
   FROM python:3.11-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY scripts/ ./scripts/
   COPY config/ ./config/

   CMD ["python", "-u", "scripts/news_summarizer.py"]
   ```

3. **Update docker-compose.yml**
   ```yaml
   gibd-news-scraper:
     build:
       context: ./apps/gibd-news-scraper
       dockerfile: Dockerfile
     profiles: ["gibd-news", "gibd-quant", "all"]
     container_name: gibd-news-scraper
     environment:
       - DB_HOST=postgres
       - DB_PORT=5432
       - DB_NAME=ws_gibd_news_database
       - DB_USER=${POSTGRES_USER}
       - DB_PASSWORD=${POSTGRES_PASSWORD}
       - WS_NEWS_API_URL=http://ws-news:8184
     depends_on:
       - ws-news
       - postgres
     networks:
       - gibd-network
     restart: unless-stopped

   gibd-news-processor:
     build:
       context: ./apps/gibd-news-processor
       dockerfile: Dockerfile
     profiles: ["gibd-news", "gibd-quant", "all"]
     container_name: gibd-news-processor
     environment:
       - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
       - OPENAI_API_KEY=${OPENAI_API_KEY}
       - SMTP_USER=${SMTP_USER}
       - SMTP_PASSWORD=${SMTP_PASSWORD}
       - WS_NEWS_API_URL=http://ws-news:8184
     depends_on:
       - ws-news
     networks:
       - gibd-network
     restart: unless-stopped
   ```

**Deliverables:**
- ✅ Dockerfiles for scraper and processor
- ✅ Updated docker-compose.yml
- ✅ Environment variable configuration
- ✅ README with build instructions

---

### 6.2 Phase 2: Scheduling Migration (Week 2-3)

**Objective**: Replace external cron with Kubernetes CronJobs or in-container scheduling.

**Option A: Kubernetes CronJobs** (Recommended)
```yaml
# k8s/cronjobs/news-scraper-market-hours.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: news-scraper-market-hours
  namespace: gibd
spec:
  schedule: "*/5 4-7 * * 0-4"  # Every 5 mins, 4-7 AM, Mon-Fri
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scraper
            image: wizardsofts/gibd-news-scraper:latest
            command: ["python", "scripts/scrape_dse_stock_price.py"]
            envFrom:
            - secretRef:
                name: gibd-news-secrets
            - configMapRef:
                name: gibd-news-config
          restartPolicy: OnFailure
```

**Option B: In-Container APScheduler** (Simpler for Docker Compose)
```python
# apps/gibd-news-scraper/scripts/scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

scheduler = BlockingScheduler()

# Pre-market scraping
scheduler.add_job(
    scrape_dse_stock_price,
    CronTrigger(minute='*/5', hour='4-7', day_of_week='mon-fri'),
    id='pre_market_scrape'
)

# News scraping
scheduler.add_job(
    scrape_news_portals,
    CronTrigger(minute='0', hour='6-20/2'),
    id='news_scrape'
)

# Summarization
scheduler.add_job(
    run_news_summarizer,
    CronTrigger(minute='0', hour='18'),
    id='news_summary'
)

scheduler.start()
```

**Tasks:**
1. Create Kubernetes CronJob manifests (if using K8s)
2. OR implement APScheduler in scraper container
3. Migrate cron jobs one by one with testing
4. Decommission external cron server

**Deliverables:**
- ✅ K8s CronJob YAMLs or APScheduler setup
- ✅ Migration runbook
- ✅ Rollback plan
- ✅ Validation tests

---

### 6.3 Phase 3: Configuration & Secrets (Week 3-4)

**Objective**: Remove hard-coded credentials and centralize configuration.

**Tasks:**

1. **Extract All Secrets**
   ```bash
   # .env.example
   # Database
   POSTGRES_USER=ws_gibd
   POSTGRES_PASSWORD=CHANGEME

   # LLM APIs
   DEEPSEEK_API_KEY=sk-xxxxx
   OPENAI_API_KEY=sk-xxxxx

   # Email
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=app-specific-password
   SMTP_RECIPIENTS=user1@example.com,user2@example.com

   # Service URLs
   WS_NEWS_API_URL=http://ws-news:8184
   EUREKA_SERVER_URL=http://ws-discovery:8761/eureka/
   ```

2. **Update news_summarizer.py**
   ```python
   # Remove hard-coded values (lines 25-36)
   MODEL_CONFIG = {
       "provider": os.getenv("LLM_PROVIDER", "deepseek"),
       "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY"),
       "openai_api_key": os.getenv("OPENAI_API_KEY"),
       "sender_email": os.getenv("SMTP_USER"),
       "sender_password": os.getenv("SMTP_PASSWORD"),
       "recipient_emails": os.getenv("SMTP_RECIPIENTS", "").split(","),
   }

   # Validate required env vars
   required_vars = ["DEEPSEEK_API_KEY", "SMTP_USER", "SMTP_PASSWORD"]
   missing = [var for var in required_vars if not os.getenv(var)]
   if missing:
       raise EnvironmentError(f"Missing required env vars: {missing}")
   ```

3. **Spring Cloud Config Integration**
   ```yaml
   # config-server/configs/ws-news-docker.yml
   spring:
     datasource:
       url: jdbc:postgresql://${DB_HOST:postgres}:${DB_PORT:5432}/${DB_NAME:ws_gibd_news_database}
       username: ${DB_USER}
       password: ${DB_PASSWORD}
     jpa:
       hibernate:
         ddl-auto: validate  # Use Flyway for migrations
   ```

**Deliverables:**
- ✅ `.env.example` file
- ✅ Updated scripts with env var usage
- ✅ Spring Cloud Config files
- ✅ Secrets management documentation

---

### 6.4 Phase 4: Observability (Week 4-5)

**Objective**: Add monitoring, logging, and alerting.

**Tasks:**

1. **Structured Logging**
   ```python
   import structlog

   logger = structlog.get_logger()

   def scrape_news_portals():
       logger.info("scrape_started", source="amarstock")
       try:
           # ... scraping logic
           logger.info("scrape_completed", source="amarstock", count=len(news_items))
       except Exception as e:
           logger.error("scrape_failed", source="amarstock", error=str(e))
           raise
   ```

2. **Metrics with Prometheus**
   ```python
   from prometheus_client import Counter, Histogram, start_http_server

   scrape_success = Counter('news_scrape_success_total', 'Successful scrapes', ['source'])
   scrape_failure = Counter('news_scrape_failure_total', 'Failed scrapes', ['source'])
   scrape_duration = Histogram('news_scrape_duration_seconds', 'Scrape duration', ['source'])

   # In scraper
   with scrape_duration.labels(source='amarstock').time():
       result = scrape_amarstock()
       if result:
           scrape_success.labels(source='amarstock').inc()
   ```

3. **Health Checks**
   ```python
   # Flask endpoint for health
   from flask import Flask, jsonify
   app = Flask(__name__)

   @app.route('/health')
   def health():
       # Check DB connection, last scrape time, etc.
       return jsonify({"status": "healthy"}), 200

   @app.route('/metrics')
   def metrics():
       # Prometheus metrics endpoint
       return generate_latest()
   ```

4. **Alerting Rules**
   ```yaml
   # prometheus/alerts/news-scraper.yml
   groups:
   - name: news_scraper
     rules:
     - alert: NewsScraperDown
       expr: up{job="gibd-news-scraper"} == 0
       for: 5m
       annotations:
         summary: "News scraper is down"

     - alert: NewsScrapeFailing
       expr: rate(news_scrape_failure_total[1h]) > 0.5
       for: 10m
       annotations:
         summary: "News scraper failing frequently"
   ```

**Deliverables:**
- ✅ Structured logging implementation
- ✅ Prometheus metrics
- ✅ Health check endpoints
- ✅ Alert rules
- ✅ Grafana dashboard

---

### 6.5 Phase 5: CI/CD Integration (Week 5-6)

**Objective**: Automate build, test, and deployment.

**Tasks:**

1. **Update .gitlab-ci.yml**
   ```yaml
   stages:
     - build
     - test
     - deploy

   build-ws-news:
     stage: build
     script:
       - cd apps/ws-news
       - docker build -t $CI_REGISTRY_IMAGE/ws-news:$CI_COMMIT_SHA .
       - docker push $CI_REGISTRY_IMAGE/ws-news:$CI_COMMIT_SHA
     only:
       changes:
         - apps/ws-news/**/*

   build-news-scraper:
     stage: build
     script:
       - cd apps/gibd-news-scraper
       - docker build -t $CI_REGISTRY_IMAGE/gibd-news-scraper:$CI_COMMIT_SHA .
       - docker push $CI_REGISTRY_IMAGE/gibd-news-scraper:$CI_COMMIT_SHA
     only:
       changes:
         - apps/gibd-news-scraper/**/*

   test-ws-news:
     stage: test
     script:
       - cd apps/ws-news
       - mvn test

   deploy-to-production:
     stage: deploy
     script:
       - kubectl set image deployment/ws-news ws-news=$CI_REGISTRY_IMAGE/ws-news:$CI_COMMIT_SHA
       - kubectl set image cronjob/news-scraper scraper=$CI_REGISTRY_IMAGE/gibd-news-scraper:$CI_COMMIT_SHA
     when: manual
     only:
       - main
   ```

2. **Add Integration Tests**
   ```python
   # tests/test_news_integration.py
   def test_scrape_and_store():
       # Scrape news
       news_items = scrape_amarstock()
       assert len(news_items) > 0

       # Store via API
       response = requests.post('http://ws-news:8184/api/news', json=news_items[0])
       assert response.status_code == 201

       # Retrieve and verify
       news_id = response.json()['data']['id']
       response = requests.get(f'http://ws-news:8184/api/news/{news_id}')
       assert response.status_code == 200
   ```

**Deliverables:**
- ✅ Updated CI/CD pipeline
- ✅ Integration tests
- ✅ Deployment automation
- ✅ Rollback procedures

---

### 6.6 Phase 6: Documentation & Handoff (Week 6)

**Objective**: Document the system and train the team.

**Deliverables:**
1. ✅ Architecture diagrams
2. ✅ API documentation (OpenAPI/Swagger)
3. ✅ Runbook for operations
4. ✅ Troubleshooting guide
5. ✅ Developer setup guide
6. ✅ Training sessions

---

## 7. Migration Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data loss during migration | High | Low | Blue-green deployment, DB backups |
| Scraper detection/blocking | High | Medium | Rate limiting, user-agent rotation, proxy |
| LLM API failures | Medium | Medium | Retry logic, fallback to simpler summary |
| Cron job downtime | Medium | Low | Parallel run during transition |
| Credential exposure | High | Medium | Secrets scanning, rotate all keys |
| Performance degradation | Medium | Medium | Load testing, gradual rollout |

---

## 8. Success Criteria

**Phase 1-2 (Containerization & Scheduling):**
- ✅ All services running in Docker/K8s
- ✅ Zero manual cron dependencies
- ✅ 99.9% uptime for scraping jobs

**Phase 3-4 (Config & Observability):**
- ✅ No hard-coded secrets
- ✅ Centralized logging with retention policy
- ✅ Alerts configured and tested
- ✅ <5 min MTTD (Mean Time To Detect)

**Phase 5-6 (CI/CD & Docs):**
- ✅ Automated deployments
- ✅ <30 min deployment time
- ✅ Complete documentation
- ✅ Team trained on new system

---

## 9. Cost Estimation

**Infrastructure (Monthly):**
- Compute (3 containers): $50-100
- Database storage: $20-40
- LLM API costs (DeepSeek): $10-50 (depends on usage)
- Monitoring/Logging: $20-40
- **Total:** $100-230/month

**Development Effort:**
- Phase 1-2: 40 hours
- Phase 3-4: 30 hours
- Phase 5-6: 30 hours
- **Total:** ~100 hours (~2.5 weeks for 1 engineer)

---

## 10. Next Steps

**Immediate Actions (This Week):**
1. ✅ Review and approve this plan
2. 🔲 Create Jira/Linear tickets for Phase 1
3. 🔲 Set up secrets in vault/GitLab CI
4. 🔲 Create feature branch: `feature/gibd-news-integration`

**Week 1-2:**
1. 🔲 Containerize Python scripts
2. 🔲 Update docker-compose.yml
3. 🔲 Test locally
4. 🔲 Deploy to staging

**Week 3-4:**
1. 🔲 Migrate scheduling
2. 🔲 Refactor configuration
3. 🔲 Add monitoring
4. 🔲 Deploy to production (parallel run)

**Week 5-6:**
1. 🔲 Full production cutover
2. 🔲 Documentation
3. 🔲 Team training
4. 🔲 Decommission old cron server

---

## 11. Appendix

### A. Database Schema

```sql
CREATE TABLE news (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR(2048) UNIQUE NOT NULL,
    title VARCHAR(1024),
    subtitle VARCHAR(1024),
    date TIMESTAMP,
    content TEXT,
    tags VARCHAR(255),
    sentiment_score REAL,
    scraped_at TIMESTAMP,
    embedding BYTEA
);

CREATE INDEX idx_news_date ON news(date DESC);
CREATE INDEX idx_news_tags ON news(tags);
CREATE INDEX idx_news_sentiment ON news(sentiment_score);
```

### B. Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `POSTGRES_HOST` | Database host | `postgres` | Yes |
| `POSTGRES_PORT` | Database port | `5432` | Yes |
| `POSTGRES_DB` | Database name | `ws_gibd_news_database` | Yes |
| `POSTGRES_USER` | Database user | `ws_gibd` | Yes |
| `POSTGRES_PASSWORD` | Database password | `****` | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek API key | `sk-****` | Yes (for processor) |
| `OPENAI_API_KEY` | OpenAI API key | `sk-****` | No (fallback) |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` | Yes (for emails) |
| `SMTP_PORT` | SMTP port | `587` | Yes |
| `SMTP_USER` | SMTP username | `user@gmail.com` | Yes |
| `SMTP_PASSWORD` | SMTP password | `****` | Yes |
| `SMTP_RECIPIENTS` | Email recipients | `user1@x.com,user2@x.com` | Yes |
| `WS_NEWS_API_URL` | ws-news API base URL | `http://ws-news:8184` | Yes |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### C. Useful Commands

```bash
# Build and start news services
docker-compose --profile gibd-news up -d

# View logs
docker-compose logs -f gibd-news-scraper
docker-compose logs -f gibd-news-processor
docker-compose logs -f ws-news

# Run manual scrape
docker-compose exec gibd-news-scraper python scripts/scrape_amrastock_daily_news.py

# Check database
docker-compose exec postgres psql -U ws_gibd -d ws_gibd_news_database -c "SELECT COUNT(*) FROM news;"

# Rebuild after code changes
docker-compose build gibd-news-scraper
docker-compose up -d gibd-news-scraper

# Run tests
docker-compose run --rm gibd-news-scraper pytest tests/
```

### D. Contact & Support

- **Owner**: Platform Team
- **Slack**: #gibd-news
- **Documentation**: [Confluence Link]
- **Runbook**: [Link]

---

**END OF DOCUMENT**

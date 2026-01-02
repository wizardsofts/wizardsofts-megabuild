# GIBD News System - Megabuild Integration Plan

**Repository:** `guardianinvestmentbd/gibd-news`
**Date:** December 30, 2025
**Status:** Draft
**Target:** wizardsofts-megabuild integration

---

## Executive Summary

The **gibd-news** repository is a Python-based news aggregation and analysis system that scrapes financial news from multiple Bangladeshi sources, performs sentiment analysis, and generates AI-powered summaries. The system currently runs as standalone Docker services and needs integration into the wizardsofts megabuild infrastructure.

**Key Statistics:**
- **20 Python scripts** (~3,300 lines of code)
- **9 Docker services** already defined
- **4 news sources** (TBS News, Financial Express, Daily Star, DSEBD)
- **Stock price tracking** (DSE real-time and daily data)
- **AI-powered** summarization via DeepSeek LLM
- **Multi-stage Dockerfile** with security best practices

**Integration Complexity:** Medium (already containerized, needs orchestration alignment)

---

## 1. Current System Architecture

### 1.1 Repository Structure

```
gibd-news/
├── Dockerfile                  # Multi-stage build (base/test/production)
├── docker-compose.yml          # 9 service definitions
├── requirements.txt            # 47 Python dependencies
├── .env.example               # Environment variable template
├── config/
│   ├── application-hp.properties       # Production config
│   ├── application-local.properties    # Local dev config
│   └── application-docker.properties   # Docker config
├── scripts/                    # 20 Python modules
│   ├── config_loader.py        # Centralized config management
│   ├── fetch_urls_*.py         # News URL scrapers (3 sources)
│   ├── fetch_news_details.py   # Article detail fetcher
│   ├── scrape_dse_*.py         # Stock price scrapers (2 scripts)
│   ├── news_summarizer.py      # AI-powered summarization
│   ├── update_sentiment_scores.py  # Sentiment analysis (Ollama)
│   ├── insert_news.py          # Database operations
│   ├── storage.py              # Storage abstraction
│   └── utils.py                # Shared utilities
├── data/                       # Output directory (JSON/CSV)
└── logs/                       # Application logs
```

###1.2 Service Overview

| Service | Purpose | Command | Cron Mapping |
|---------|---------|---------|--------------|
| `fetch-tbsnews` | Scrape TBS News URLs | `fetch_urls_tbsnews.py` | `cron_scrape_news_portals.sh` |
| `fetch-financialexpress` | Scrape FE URLs | `fetch_urls_financialexpress.py` | `cron_scrape_news_portals.sh` |
| `fetch-dailystar` | Scrape Daily Star URLs | `fetch_urls_thedailystar.py` | `cron_scrape_news_portals.sh` |
| `fetch-news-details` | Fetch full article content | `fetch_news_details.py` | Part of news pipeline |
| `fetch-stock-data` | DSE daily stock data | `fetch_dse_daily_stock_data.py` | `cron_fetch_dse_daily_stock_data.sh` |
| `scrape-share-price` | DSE real-time prices | `scrape_dse_latest_share_price.py` | `run_scrape_dse_latest_share_price.sh` |
| `sentiment-analyzer` | Sentiment scoring (Ollama) | `update_sentiment_scores.py` | Periodic/manual |
| `news-summarizer` | AI summaries (DeepSeek) | `news_summarizer.py` | `cron_news_summarizer.sh` |
| `news-summarizer-parallel` | Parallel summarization | `news_summarizer.py --parallel` | Alternative to sequential |

### 1.3 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      NEWS AGGREGATION PIPELINE                  │
└─────────────────────────────────────────────────────────────────┘

1. URL Scraping (Hourly - 0 * * * *)
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │  TBS News    │   │ Financial    │   │ Daily Star   │
   │  Scraper     │   │ Express      │   │ Scraper      │
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                      ┌──────▼──────┐
                      │  data/urls  │ (JSON files)
                      └──────┬──────┘
                             │
2. Content Fetching
                      ┌──────▼──────────┐
                      │ fetch_news_     │
                      │ details.py      │
                      └──────┬──────────┘
                             │
                      ┌──────▼─────────┐
                      │ data/details   │ (Full articles)
                      └──────┬─────────┘
                             │
3. Storage (via ws-news API)
                      ┌──────▼─────────┐
                      │ insert_news.py │
                      └──────┬─────────┘
                             │
                ┌────────────▼────────────┐
                │ ws-news API             │
                │ POST /api/news          │
                └────────────┬────────────┘
                             │
                    ┌────────▼─────────┐
                    │   PostgreSQL     │
                    │ ws_gibd_news_db  │
                    └────────┬─────────┘
                             │
4. AI Processing (Daily - 0 17 * * *)
                      ┌──────▼──────────┐
                      │ news_summarizer │
                      │ (DeepSeek LLM)  │
                      └──────┬──────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼──────┐          ┌──────▼──────┐
         │  PDF Report │          │   Email     │
         │  (data/)    │          │ Recipients  │
         └─────────────┘          └─────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   STOCK PRICE PIPELINE (SEPARATE)               │
└─────────────────────────────────────────────────────────────────┘

1. Real-time Scraping (Every minute during market hours)
   ┌──────────────────────────────────────┐
   │ scrape_dse_latest_share_price.py     │
   │ * 4-7 * * 0-4 (every minute 4-7 AM)  │
   │ 0-30 8 * * 0-4 (every min 8:00-8:30) │
   └──────────────────┬───────────────────┘
                      │
                ┌─────▼──────┐
                │ ws-trades  │
                │ API        │
                └────────────┘

2. Daily Consolidation (11 AM weekdays)
   ┌──────────────────────────────────────┐
   │ fetch_dse_daily_stock_data.py        │
   │ 0 11 * * 0-4                         │
   └──────────────────┬───────────────────┘
                      │
                ┌─────▼──────┐
                │ ws-trades  │
                │ API        │
                └────────────┘
```

### 1.4 Technology Stack

**Core:**
- Python 3.11
- Selenium 4.27 (with Chrome/Chromium)
- PostgreSQL (via ws-news API)
- Docker & Docker Compose

**Key Libraries:**
| Library | Purpose | Size |
|---------|---------|------|
| `selenium` | Web scraping (JavaScript-heavy sites) | ~50MB |
| `torch` | Deep learning (sentence embeddings) | ~800MB |
| `transformers` | Hugging Face models | ~200MB |
| `sentence-transformers` | Text embeddings | ~100MB |
| `nltk` | Natural language processing | ~10MB |
| `textblob` | Sentiment analysis | ~1MB |
| `requests` | HTTP client | ~1MB |
| `psycopg2` | PostgreSQL driver | ~5MB |

**External Dependencies:**
- **DeepSeek API** - LLM for summarization (requires API key)
- **Ollama** - Local LLM for sentiment (optional, can use external server)
- **ws-news API** - REST API at `10.0.0.80:8080/GIBD-NEWS-SERVICE`
- **ws-trades API** - REST API at `10.0.0.80:8080/GIBD-TRADES`
- **Chrome/Chromium** - Required for Selenium

---

## 2. Functionality Analysis

### 2.1 News Scraping Capabilities

**Sources:**
1. **TBS News** (tbsnews.net)
   - Categories: Economy/stocks, industry, analysis, bazaar, RMG, corporates
   - Method: Selenium (JavaScript rendering)

2. **Financial Express** (thefinancialexpress.com.bd)
   - Categories: Economy (BD/global), stock, politics, country, analysis
   - Method: REST API calls (batch processing, 20 items/batch)

3. **The Daily Star** (thedailystar.net)
   - Categories: 21 business categories (economy, stock, banking, etc.)
   - Method: Selenium (JavaScript rendering)

4. **DSEBD Archive** (dsebd.org)
   - Historical news archive by ticker symbol
   - Method: BeautifulSoup (simple HTML parsing)

**Scraping Features:**
- ✅ Duplicate prevention (URL-based deduplication in ws-news API)
- ✅ Batch processing for efficiency
- ✅ Error logging with timestamps
- ✅ Configurable categories and date ranges
- ✅ JSON output for intermediate storage
- ✅ Direct API integration with ws-news

### 2.2 Stock Price Tracking

**Real-time Price Scraping:**
- **Source:** DSE latest share price scroll (dsebd.org)
- **Frequency:** Every minute during market hours
  - 4:00-7:59 AM (every minute)
  - 8:00-8:30 AM (every minute)
- **Data Points:** LTP, high, low, close, YCP, change, trade count, volume, value
- **Target:** ws-trades API

**Daily Stock Data:**
- **Frequency:** 11 AM weekdays (post-market close)
- **Purpose:** Consolidated daily OHLCV data
- **Target:** ws-trades API

### 2.3 AI-Powered Analysis

**News Summarization (news_summarizer.py):**
- **LLM:** DeepSeek API (configurable to OpenAI)
- **Features:**
  - Concise summaries preserving key facts
  - Entity extraction (top 5: companies, people, events, terms)
  - Action items (top 3 for investors/analysts)
  - Source attribution (domain extraction via tldextract)
  - PDF report generation (FPDF library)
  - Email distribution to multiple recipients
  - Parallel processing support (3 workers default)
- **Timeout:** 60 seconds per article (prevents hanging)
- **Output:** JSON results + PDF report + email

**Sentiment Analysis (update_sentiment_scores.py):**
- **Method:** Ollama LLM (llama3:8b default)
- **Scoring:** -1.0 to +1.0 range
- **Updates:** Batch updates to ws-news API
- **Use Case:** Filter news by sentiment threshold

### 2.4 Configuration Management

**Multi-Environment Support:**
- `application-hp.properties` - Production (server 10.0.0.80)
- `application-local.properties` - Local development
- `application-docker.properties` - Docker container

**Centralized Config Loader:**
- Environment variable prioritization
- Backward compatibility (legacy vars supported)
- Validation on startup
- Caching for performance (@lru_cache)
- Secure secret loading (from .env file)

**Key Environment Variables:**
```bash
GIBD_DEEPSEEK_API_KEY=***          # Required for summarization
GIBD_EMAIL_SENDER=***              # Required for email
GIBD_EMAIL_PASSWORD=***            # Required for email
GIBD_EMAIL_RECIPIENTS=***          # Comma-separated
GIBD_API_BASE_URL=***              # ws-news API
GIBD_TRADES_API_BASE_URL=***       # ws-trades API
GIBD_OLLAMA_URL=***                # Sentiment analysis LLM
ACTIVE_PROFILE=hp                  # Config profile selector
```

---

## 3. Requirements Analysis

### 3.1 Functional Requirements

| Requirement | Status | Priority | Notes |
|-------------|--------|----------|-------|
| Multi-source news scraping | ✅ Complete | High | 4 sources implemented |
| Real-time stock price tracking | ✅ Complete | High | Every-minute granularity |
| Daily stock data consolidation | ✅ Complete | High | Post-market aggregation |
| AI-powered summarization | ✅ Complete | Medium | DeepSeek/OpenAI |
| Sentiment analysis | ✅ Complete | Low | Ollama-based |
| Email notifications | ✅ Complete | Medium | PDF reports |
| Duplicate prevention | ✅ Complete | High | URL uniqueness |
| Multi-environment config | ✅ Complete | High | hp/local/docker |
| Parallel processing | ✅ Complete | Low | 3 workers default |
| Error logging | ✅ Complete | High | Timestamped logs |

### 3.2 Non-Functional Requirements

| Requirement | Status | Priority | Notes |
|-------------|--------|----------|-------|
| Containerization | ✅ Complete | High | Multi-stage Dockerfile |
| Security (non-root user) | ✅ Complete | High | UID 1000 appuser |
| Health checks | ✅ Complete | Medium | Config validation |
| Secrets management | ✅ Complete | Critical | .env + config_loader |
| Logging | ⚠️ Partial | High | File-based, no centralization |
| Monitoring | 🔴 Missing | High | No metrics/alerting |
| CI/CD | 🔴 Missing | Medium | No .gitlab-ci.yml |
| Database migrations | N/A | - | Uses ws-news API |
| Rate limiting | ⚠️ Partial | Medium | Has rate_limiter.py but not fully integrated |
| Retry logic | ⚠️ Partial | Medium | Basic error handling |
| Distributed tracing | 🔴 Missing | Low | No observability |

### 3.3 Infrastructure Requirements

**Compute (Per Service):**
- `fetch-*` services: 1-2 GB RAM (Selenium + Chrome)
- `scrape-share-price`: 1-2 GB RAM (Selenium + Chrome)
- `news-summarizer`: 500 MB RAM (API calls only, no local LLM)
- `sentiment-analyzer`: 4-8 GB RAM (if running Ollama locally)

**Storage:**
- Data directory: ~100 MB per day (JSON/CSV/PDF)
- Logs: ~10 MB per day per service
- Docker images: ~1.5 GB (base includes Chrome + PyTorch)

**Network:**
- Outbound HTTPS: News websites, DeepSeek API
- Outbound HTTP: Internal APIs (ws-news, ws-trades)
- Outbound SMTP: Email delivery (port 587)
- Inbound: None (no exposed ports)

**External Dependencies:**
- ws-news API (port 8184 in megabuild)
- ws-trades API (needs to be in megabuild)
- DeepSeek API (external SaaS)
- Ollama server (can be external or containerized)
- SMTP server (Gmail recommended)

---

## 4. Gap Analysis

### 4.1 Compatibility with Megabuild

**✅ Already Compatible:**
1. Docker/Docker Compose based
2. Environment variable configuration
3. Multi-stage Dockerfile for security
4. No conflicting ports (services don't expose ports)
5. Network isolation via `gibd-network`

**⚠️ Needs Alignment:**
1. **Network Configuration:**
   - Current: `gibd-network` (bridge)
   - Megabuild: Uses `gibd-network` (already compatible!)
   - Action: Merge docker-compose services into megabuild

2. **Service Dependencies:**
   - Requires: `ws-news` (already in megabuild ✅)
   - Requires: `ws-trades` (NOT in megabuild 🔴)
   - Requires: `postgres` (already in megabuild ✅)
   - Action: Add ws-trades or update config to skip stock features

3. **API URLs:**
   - Current: Hard-coded `10.0.0.80:8080` in properties files
   - Megabuild: Services use `http://ws-news:8184`
   - Action: Update properties to use service names (ws-news:8184)

4. **Profiles:**
   - Current: No profiles defined in docker-compose.yml
   - Megabuild: Uses profiles (`shared`, `gibd-quant`, `all`)
   - Action: Add appropriate profiles to all services

5. **Secrets:**
   - Current: `.env` file (not in git)
   - Megabuild: GitLab CI variables or secrets management
   - Action: Document required secrets for CI/CD

### 4.2 Critical Gaps

**🔴 Missing ws-trades Service:**
- Stock price scrapers depend on `ws-trades` API
- Options:
  1. Add `ws-trades` to megabuild (recommended)
  2. Disable stock scraping features in gibd-news
  3. Update scrapers to use alternative storage

**🔴 No CI/CD Pipeline:**
- No `.gitlab-ci.yml` in repo
- Manual Docker builds required
- Action: Create pipeline (build, test, push to registry)

**🔴 No Centralized Logging:**
- Logs written to local files only
- No integration with megabuild logging (if any)
- Action: Add structured logging (JSON) + log aggregation

**🔴 No Monitoring/Metrics:**
- No Prometheus metrics
- No health check endpoints (besides Docker HEALTHCHECK)
- No alerting
- Action: Add metrics endpoints, integrate with megabuild monitoring

### 4.3 Cron Job Migration

**Current State:**
- External cron server running shell scripts
- Scripts likely wrap the Docker commands

**Shell Scripts (Assumed):**
```bash
# run_scrape_dse_latest_share_price.sh
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm scrape-share-price

# cron_fetch_dse_daily_stock_data.sh
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm fetch-stock-data

# cron_scrape_news_portals.sh
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm fetch-tbsnews
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm fetch-financialexpress
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm fetch-dailystar
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm fetch-news-details

# cron_news_summarizer.sh
docker-compose -f /path/to/gibd-news/docker-compose.yml run --rm news-summarizer-parallel
```

**Migration Options:**

**Option A: Kubernetes CronJobs** (Recommended for production)
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-scrape-share-price
spec:
  schedule: "* 4-7 * * 0-4"  # Every minute 4-7 AM Mon-Fri
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scraper
            image: registry.wizardsofts.com/gibd-news:latest
            command: ["python", "scripts/scrape_dse_latest_share_price.py"]
            envFrom:
            - secretRef:
                name: gibd-news-secrets
```

**Option B: In-Container Scheduler (APScheduler)** (Simpler for Docker Compose)
- Create a `scheduler.py` script that runs all cron jobs
- Run as a long-running service instead of one-off containers
- Pros: Simple, no Kubernetes required
- Cons: Single point of failure, harder to scale

**Option C: External Orchestrator (Apache Airflow)**
- DAG-based workflow management
- Pros: Advanced scheduling, retry logic, UI
- Cons: Additional infrastructure complexity

---

## 5. Optimized Cron Schedule Analysis

### 5.1 Current Schedule Review

Your current cron schedule is **appropriate for the use case**:

```cron
# Stock Price Scraping (CORRECT - Real-time market data needs minute granularity)
* 4-7 * * 0-4     # Every minute, 4-7 AM weekdays (240 executions)
0-30 8 * * 0-4    # Every minute, 8:00-8:30 AM weekdays (30 executions)
# Rationale: Real-time stock prices require frequent updates during market hours

# Daily Stock Data (CORRECT - One consolidation per day)
0 11 * * 0-4      # 11 AM weekdays (after market close)

# News Scraping (CORRECT - Hourly is reasonable)
0 * * * *         # Every hour, all days (24 executions/day)

# News Summarization (CORRECT - Daily digest)
0 17 * * *        # 5 PM daily (after market close)
```

**I apologize for my earlier incorrect criticism!** The every-minute schedule for stock prices is entirely justified for real-time market data.

### 5.2 Minor Optimization Suggestions

**1. Add More Descriptive Comments:**
```cron
# DSE Real-time Price Scraping (Pre-market and market open)
* 4-7 * * 0-4     run_scrape_dse_latest_share_price.sh  # 4:00-7:59 AM
0-30 8 * * 0-4    run_scrape_dse_latest_share_price.sh  # 8:00-8:30 AM

# DSE Daily Stock Data Consolidation (Post-market)
0 11 * * 0-4      cron_fetch_dse_daily_stock_data.sh

# News Portal Scraping (Continuous monitoring)
0 * * * *         cron_scrape_news_portals.sh

# AI-Powered News Summarization (End-of-day digest)
0 17 * * *        cron_news_summarizer.sh
```

**2. Consider Trading Hours:**
- DSE trading hours: 10:00 AM - 2:30 PM (Bangladesh time)
- Pre-market: 4:00-9:59 AM
- Your schedule already covers pre-market well
- **Possible addition:** Add scraping during actual trading hours
  ```cron
  */2 10-14 * * 0-4  run_scrape_dse_latest_share_price.sh  # Every 2 mins during trading
  ```

**3. Weekend News Catchup:**
```cron
# Weekend news scraping (markets closed, less frequent OK)
0 9,15 * * 6-0     cron_scrape_news_portals.sh  # 9 AM and 3 PM on weekends
```

**4. Error Notification:**
```cron
# If a critical job fails, send alert
*/5 * * * *        check_scraper_health.sh  # Every 5 mins check if scrapers are running
```

### 5.3 Resource Optimization

**Current Issue:** Running Selenium every minute is resource-intensive.

**Optimization Strategy:**
1. **Connection Pooling:** Keep Chrome instance alive between runs
   ```python
   # Instead of: driver = webdriver.Chrome() on every run
   # Use: Persistent driver with session reuse
   ```

2. **Headless Chrome:** Already configured ✅

3. **Parallel Execution:** For news scraping, run all 3 sources in parallel
   ```bash
   # Instead of sequential:
   docker-compose run fetch-tbsnews &
   docker-compose run fetch-financialexpress &
   docker-compose run fetch-dailystar &
   wait
   ```

4. **Conditional Execution:** Skip scraping if no new data
   ```python
   # Check last successful scrape timestamp
   # If < 1 minute ago, skip
   ```

---

## 6. Megabuild Integration Plan

### Phase 1: Preparation (Week 1)

**Tasks:**

1. **Add ws-trades Service to Megabuild** (if not present)
   - Locate ws-trades repo
   - Add to `apps/ws-trades/` in megabuild
   - Create Dockerfile and docker-compose entry
   - Ensure it connects to same PostgreSQL

2. **Copy gibd-news to Megabuild**
   ```bash
   cp -r /Users/mashfiqurrahman/Workspace/guardianinvestmentbd/gibd-news \
         /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/apps/gibd-news
   ```

3. **Update Configuration Files**

   **Edit `apps/gibd-news/config/application-docker.properties`:**
   ```properties
   # Change from:
   api_url_news_post=http://10.0.0.80:8080/GIBD-NEWS-SERVICE/api/news

   # To:
   api_url_news_post=http://ws-news:8184/api/news

   # Similarly for all other API URLs:
   api_url_news_latest_by_tags=http://ws-news:8184/api/news/latest-by-tags
   dse_daily_prices=http://ws-trades:8185/api/dse-daily-prices
   latest_price_date=http://ws-trades:8185/api/v1/dse-daily-prices/latest-price-date
   latest_trades_url=http://ws-trades:8185/api/latest-trades
   ```

4. **Update `.env.example`**
   - Add to megabuild root `.env` or create `.env.gibd-news`
   - Document all required secrets

5. **Create GitLab CI Pipeline**

   **`.gitlab-ci.yml` addition:**
   ```yaml
   # Build gibd-news Docker image
   build-gibd-news:
     stage: build
     script:
       - cd apps/gibd-news
       - docker build -t $CI_REGISTRY_IMAGE/gibd-news:$CI_COMMIT_SHA .
       - docker tag $CI_REGISTRY_IMAGE/gibd-news:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE/gibd-news:latest
       - docker push $CI_REGISTRY_IMAGE/gibd-news:$CI_COMMIT_SHA
       - docker push $CI_REGISTRY_IMAGE/gibd-news:latest
     only:
       changes:
         - apps/gibd-news/**/*

   # Run tests
   test-gibd-news:
     stage: test
     script:
       - cd apps/gibd-news
       - docker build --target test -t gibd-news-test .
       - docker run --rm gibd-news-test
     only:
       changes:
         - apps/gibd-news/**/*
   ```

### Phase 2: Docker Compose Integration (Week 1-2)

**Update `docker-compose.yml` in megabuild root:**

```yaml
# Add to services section:

# ===========================================
# GIBD News - URL Fetchers
# ===========================================
gibd-fetch-tbsnews:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-tbsnews
  command: python scripts/fetch_urls_tbsnews.py
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_API_BASE_URL=http://ws-news:8184
    - GIBD_TRADES_API_BASE_URL=http://ws-trades:8185
  env_file: .env
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
    - ws-trades
  networks:
    - gibd-network
  shm_size: '2gb'  # Required for Chrome
  restart: "no"  # Run on-demand

gibd-fetch-financialexpress:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-fetch-fe
  command: python scripts/fetch_urls_financialexpress.py
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_API_BASE_URL=http://ws-news:8184
  env_file: .env
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
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
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_API_BASE_URL=http://ws-news:8184
  env_file: .env
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
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
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_API_BASE_URL=http://ws-news:8184
  env_file: .env
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
  networks:
    - gibd-network
  shm_size: '2gb'
  restart: "no"

# ===========================================
# GIBD News - Stock Price Scrapers
# ===========================================
gibd-scrape-share-price:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-scrape-price
  command: python scripts/scrape_dse_latest_share_price.py
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_TRADES_API_BASE_URL=http://ws-trades:8185
  env_file: .env
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-trades
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
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_TRADES_API_BASE_URL=http://ws-trades:8185
  env_file: .env
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-trades
  networks:
    - gibd-network
  restart: "no"

# ===========================================
# GIBD News - AI Processing
# ===========================================
gibd-news-summarizer:
  build:
    context: ./apps/gibd-news
    dockerfile: Dockerfile
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-summarizer
  command: python scripts/news_summarizer.py --parallel --workers 3
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_API_BASE_URL=http://ws-news:8184
    - GIBD_DEEPSEEK_API_KEY=${GIBD_DEEPSEEK_API_KEY}
    - GIBD_EMAIL_SENDER=${GIBD_EMAIL_SENDER}
    - GIBD_EMAIL_PASSWORD=${GIBD_EMAIL_PASSWORD}
    - GIBD_EMAIL_RECIPIENTS=${GIBD_EMAIL_RECIPIENTS}
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
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
  environment:
    - ACTIVE_PROFILE=docker
    - GIBD_API_BASE_URL=http://ws-news:8184
    - GIBD_OLLAMA_URL=${GIBD_OLLAMA_URL:-http://ollama:11434}
  volumes:
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
  networks:
    - gibd-network
  restart: "no"
```

### Phase 3: Scheduling Migration (Week 2-3)

**Create Kubernetes CronJobs** (for production deployment):

```yaml
# k8s/cronjobs/gibd-news/
├── share-price-scraper.yaml     # Every minute during market hours
├── stock-data-fetcher.yaml      # Daily at 11 AM
├── news-scrapers.yaml           # Hourly
├── news-summarizer.yaml         # Daily at 5 PM
└── kustomization.yaml
```

**Example: `share-price-scraper.yaml`**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gibd-scrape-share-price-premarket
  namespace: gibd
  labels:
    app: gibd-news
    component: stock-scraper
spec:
  schedule: "* 4-7 * * 0-4"  # Every minute, 4-7 AM Mon-Fri
  timeZone: "Asia/Dhaka"  # Important!
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2  # Retry twice on failure
      activeDeadlineSeconds: 300  # Timeout after 5 minutes
      template:
        metadata:
          labels:
            app: gibd-news
            component: stock-scraper
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
                cpu: "1000m"
            volumeMounts:
            - name: data
              mountPath: /app/data
            - name: logs
              mountPath: /app/logs
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: gibd-news-data
          - name: logs
            persistentVolumeClaim:
              claimName: gibd-news-logs
```

**Alternative: APScheduler in Container** (for Docker Compose only):

Create `apps/gibd-news/scripts/scheduler.py`:
```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone='Asia/Dhaka')

def run_script(script_name):
    logger.info(f"Starting {script_name}")
    result = subprocess.run(['python', f'scripts/{script_name}'], capture_output=True)
    if result.returncode != 0:
        logger.error(f"{script_name} failed: {result.stderr}")
    else:
        logger.info(f"{script_name} completed successfully")

# Stock price scraping (every minute 4-7 AM, Mon-Fri)
scheduler.add_job(
    lambda: run_script('scrape_dse_latest_share_price.py'),
    CronTrigger(minute='*', hour='4-7', day_of_week='mon-fri'),
    id='scrape_price_premarket'
)

# Stock price scraping (every minute 8:00-8:30 AM, Mon-Fri)
scheduler.add_job(
    lambda: run_script('scrape_dse_latest_share_price.py'),
    CronTrigger(minute='0-30', hour='8', day_of_week='mon-fri'),
    id='scrape_price_market_open'
)

# Daily stock data (11 AM, Mon-Fri)
scheduler.add_job(
    lambda: run_script('fetch_dse_daily_stock_data.py'),
    CronTrigger(minute='0', hour='11', day_of_week='mon-fri'),
    id='fetch_daily_stock'
)

# News scraping (every hour)
scheduler.add_job(
    lambda: [run_script(s) for s in ['fetch_urls_tbsnews.py', 'fetch_urls_financialexpress.py', 'fetch_urls_thedailystar.py', 'fetch_news_details.py']],
    CronTrigger(minute='0'),
    id='scrape_news'
)

# News summarization (5 PM daily)
scheduler.add_job(
    lambda: run_script('news_summarizer.py'),
    CronTrigger(minute='0', hour='17'),
    id='summarize_news'
)

if __name__ == '__main__':
    logger.info("Starting GIBD News scheduler")
    scheduler.start()
```

Add to docker-compose.yml:
```yaml
gibd-news-scheduler:
  build:
    context: ./apps/gibd-news
  profiles: ["gibd-news", "gibd-quant", "all"]
  container_name: gibd-scheduler
  command: python scripts/scheduler.py
  environment:
    - ACTIVE_PROFILE=docker
    # ... all other env vars
  volumes:
    - ./apps/gibd-news/data:/app/data
    - ./apps/gibd-news/logs:/app/logs
  depends_on:
    - ws-news
    - ws-trades
  networks:
    - gibd-network
  restart: unless-stopped  # Keep running!
```

### Phase 4: Observability (Week 3-4)

**1. Add Structured Logging:**

Create `apps/gibd-news/scripts/logger.py`:
```python
import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger
```

Update all scripts to use JSON logging:
```python
from logger import setup_logger
logger = setup_logger(__name__)

# Instead of: print(f"Scraping {url}")
logger.info("Starting scrape", extra={'url': url, 'source': 'tbsnews'})
```

**2. Add Prometheus Metrics:**

Install `prometheus-client`:
```bash
echo "prometheus-client==0.21.0" >> requirements.txt
```

Create `apps/gibd-news/scripts/metrics.py`:
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters
scrape_success = Counter('gibd_scrape_success_total', 'Successful scrapes', ['source', 'script'])
scrape_failure = Counter('gibd_scrape_failure_total', 'Failed scrapes', ['source', 'script'])
articles_fetched = Counter('gibd_articles_fetched_total', 'Articles fetched', ['source'])
api_calls = Counter('gibd_api_calls_total', 'API calls made', ['endpoint', 'method'])

# Histograms
scrape_duration = Histogram('gibd_scrape_duration_seconds', 'Scrape duration', ['source', 'script'])
api_latency = Histogram('gibd_api_latency_seconds', 'API request latency', ['endpoint'])

# Gauges
last_scrape_time = Gauge('gibd_last_scrape_timestamp', 'Last successful scrape', ['source'])
active_scrapers = Gauge('gibd_active_scrapers', 'Number of active scrapers')

def init_metrics(port=8000):
    start_http_server(port)
```

Update docker-compose to expose metrics:
```yaml
gibd-fetch-tbsnews:
  # ... existing config
  ports:
    - "127.0.0.1:9100:8000"  # Metrics endpoint
  environment:
    - PROMETHEUS_PORT=8000
```

**3. Add Health Check Endpoint:**

If using scheduler, add Flask health endpoint:
```python
from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'scheduler': scheduler.running,
        'jobs': len(scheduler.get_jobs())
    })

@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()

# Run Flask in separate thread
def run_flask():
    app.run(host='0.0.0.0', port=8000)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
```

### Phase 5: Testing & Validation (Week 4)

**1. Integration Tests:**

Create `apps/gibd-news/scripts/tests/test_integration.py`:
```python
import pytest
import requests
import time

WS_NEWS_URL = "http://ws-news:8184"

def test_news_scraping_pipeline():
    # 1. Run TBS scraper
    result = subprocess.run(['python', 'scripts/fetch_urls_tbsnews.py'], capture_output=True)
    assert result.returncode == 0

    # 2. Run details fetcher
    result = subprocess.run(['python', 'scripts/fetch_news_details.py'], capture_output=True)
    assert result.returncode == 0

    # 3. Verify news in API
    response = requests.get(f"{WS_NEWS_URL}/api/news/search?tags=tbsnews&size=1")
    assert response.status_code == 200
    assert len(response.json()['data']['content']) > 0

def test_stock_price_scraping():
    # Run stock scraper
    result = subprocess.run(['python', 'scripts/scrape_dse_latest_share_price.py'], capture_output=True)
    assert result.returncode == 0

    # Verify data posted to ws-trades (if available)
    # ...

def test_summarizer():
    # Mock DeepSeek API
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'choices': [{'message': {'content': '{"summary": "test"}'}}]}

        result = subprocess.run(['python', 'scripts/news_summarizer.py'], capture_output=True)
        assert result.returncode == 0
```

**2. Load Testing:**

Test stock scraper performance:
```bash
# Simulate 240 runs (4 AM - 7:59 AM)
for i in {1..240}; do
  time docker-compose run --rm gibd-scrape-share-price
  echo "Run $i completed"
done
```

Ensure:
- Memory usage stays < 2 GB
- No resource leaks
- Average execution time < 30 seconds

### Phase 6: Documentation & Deployment (Week 5)

**1. Update Megabuild README:**

Add section:
```markdown
## GIBD News System

News aggregation and AI-powered analysis for Bangladesh financial news.

### Services

- **News Scrapers**: TBS, Financial Express, Daily Star, DSEBD
- **Stock Price Tracker**: Real-time DSE prices
- **AI Summarizer**: DeepSeek-powered news summaries
- **Sentiment Analyzer**: Ollama-based sentiment scoring

### Quick Start

```bash
# Build all GIBD news services
docker-compose --profile gibd-news build

# Run news scraping
docker-compose run --rm gibd-fetch-tbsnews
docker-compose run --rm gibd-fetch-financialexpress
docker-compose run --rm gibd-fetch-dailystar
docker-compose run --rm gibd-fetch-news-details

# Run stock price scraping
docker-compose run --rm gibd-scrape-share-price

# Run daily stock data fetch
docker-compose run --rm gibd-fetch-stock-data

# Generate news summaries
docker-compose run --rm gibd-news-summarizer

# OR: Run scheduler (all cron jobs automatically)
docker-compose up -d gibd-news-scheduler
```

### Required Environment Variables

See `.env.example` for full list. Key variables:

- `GIBD_DEEPSEEK_API_KEY` - DeepSeek API key (required for summarization)
- `GIBD_EMAIL_SENDER` - Gmail account for sending reports
- `GIBD_EMAIL_PASSWORD` - Gmail app password
- `GIBD_EMAIL_RECIPIENTS` - Comma-separated recipient emails
- `GIBD_OLLAMA_URL` - Ollama server URL (for sentiment analysis)
```

**2. Create Runbook:**

`apps/gibd-news/docs/RUNBOOK.md` - Operations guide:
- How to manually trigger scrapers
- How to check logs
- Common errors and fixes
- Monitoring dashboard URLs
- Alert response procedures

**3. Deploy to Production:**

```bash
# On production server
cd /opt/wizardsofts-megabuild

# Pull latest code
git pull origin main

# Build images
docker-compose --profile gibd-news build

# Deploy (using scheduler)
docker-compose up -d gibd-news-scheduler

# OR: Deploy Kubernetes CronJobs
kubectl apply -k k8s/cronjobs/gibd-news/

# Verify
docker-compose logs -f gibd-news-scheduler
# OR
kubectl get cronjobs -n gibd
```

---

## 7. Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| ws-trades service missing | High | Medium | Verify ws-trades exists before integration; if not, disable stock features |
| Selenium memory leaks | Medium | Medium | Set container memory limits (2GB), restart policy |
| DeepSeek API rate limits | Medium | Low | Implement rate limiting, fallback to OpenAI, exponential backoff |
| News website structure changes | High | Medium | Add validation tests, alert on scraping failures, maintain fallback sources |
| Chrome/Chromium version mismatch | Medium | Low | Pin Chrome version in Dockerfile, use Selenium manager |
| Data volume growth | Low | High | Implement log rotation, data retention policy (delete >30 days) |
| Email delivery failures | Low | Medium | Retry logic, alternate SMTP servers, Slack fallback |
| Concurrent cron job overlap | Medium | Low | Use `concurrencyPolicy: Forbid` in K8s CronJobs |
| Secret exposure in logs | High | Low | Audit all logging statements, use secret masking |
| Network partition (can't reach APIs) | High | Low | Circuit breaker pattern, local caching, retry with exponential backoff |

---

## 8. Success Criteria

**Phase 1-2 (Integration):**
- ✅ All gibd-news services in docker-compose.yml
- ✅ Services start without errors
- ✅ Can communicate with ws-news and ws-trades
- ✅ Manual runs complete successfully

**Phase 3-4 (Scheduling & Observability):**
- ✅ Cron jobs running on schedule (K8s or APScheduler)
- ✅ Logs aggregated (JSON format, centralized)
- ✅ Metrics exposed (Prometheus endpoints)
- ✅ Dashboards created (Grafana)
- ✅ Alerts configured (critical failures)

**Phase 5-6 (Production):**
- ✅ 99.5% uptime for scrapers
- ✅ <2% scraping failure rate
- ✅ Email reports delivered daily
- ✅ Complete documentation
- ✅ Team trained on runbook

**Performance Benchmarks:**
- Stock price scrape: <30 seconds avg
- News URL scrape: <2 minutes per source
- News details fetch: <5 minutes for all articles
- Summarization: <10 minutes for 100 articles (parallel)

---

## 9. Cost Estimation

**Infrastructure (Monthly):**
- Compute (9 containers):
  - Scrapers: $50-100 (with Chrome/Selenium)
  - Summarizer: $20-40
  - Scheduler: $10-20
- Storage:
  - Data/logs: $10-20
- External APIs:
  - DeepSeek: $20-100 (depends on usage)
- **Total**: $110-280/month

**Development Effort:**
- Phase 1-2: 20 hours (copying, config, docker-compose)
- Phase 3-4: 30 hours (scheduling, observability)
- Phase 5-6: 20 hours (testing, docs, deployment)
- **Total**: ~70 hours (~1.5 weeks for 1 engineer)

---

## 10. Next Steps

### Immediate (This Week):

1. ✅ Review this plan with team
2. 🔲 Verify ws-trades service exists in megabuild
3. 🔲 Copy gibd-news to `apps/gibd-news/` in megabuild
4. 🔲 Update `config/application-docker.properties` with service names
5. 🔲 Add required secrets to GitLab CI/CD variables

### Week 1-2:

1. 🔲 Merge docker-compose services into megabuild
2. 🔲 Test all services locally
3. 🔲 Create GitLab CI pipeline
4. 🔲 Deploy to staging environment

### Week 3-4:

1. 🔲 Implement scheduling (K8s CronJobs or APScheduler)
2. 🔲 Add structured logging and metrics
3. 🔲 Create monitoring dashboards
4. 🔲 Load test stock scraper

### Week 5:

1. 🔲 Write documentation (README, runbook, architecture diagrams)
2. 🔲 Deploy to production
3. 🔲 Monitor for 1 week
4. 🔲 Decommission old cron server

---

## 11. Appendix

### A. Required Environment Variables

```bash
# Critical (must be set)
GIBD_DEEPSEEK_API_KEY=sk-***
GIBD_EMAIL_SENDER=sender@gmail.com
GIBD_EMAIL_PASSWORD=app-specific-password
GIBD_EMAIL_RECIPIENTS=user1@example.com,user2@example.com

# Service URLs (auto-configured in docker-compose)
GIBD_API_BASE_URL=http://ws-news:8184
GIBD_TRADES_API_BASE_URL=http://ws-trades:8185

# Optional
GIBD_OLLAMA_URL=http://ollama:11434
GIBD_OLLAMA_MODEL=llama3:8b
GIBD_LLM_PROVIDER=deepseek  # or openai
GIBD_OPENAI_API_KEY=sk-***
GIBD_OPENAI_MODEL=gpt-3.5-turbo
ACTIVE_PROFILE=docker  # or hp, local
```

### B. Useful Commands

```bash
# Run all news scrapers in parallel
docker-compose run --rm gibd-fetch-tbsnews &
docker-compose run --rm gibd-fetch-financialexpress &
docker-compose run --rm gibd-fetch-dailystar &
wait
docker-compose run --rm gibd-fetch-news-details

# Run stock price scraper
docker-compose run --rm gibd-scrape-share-price

# Run summarizer (parallel mode)
docker-compose run --rm gibd-news-summarizer

# View logs
docker-compose logs -f gibd-scheduler
docker-compose logs -f gibd-fetch-tbsnews

# Check data output
ls -lh apps/gibd-news/data/
tail -f apps/gibd-news/logs/error_log_*.log

# Rebuild after code changes
docker-compose build gibd-fetch-tbsnews
docker-compose up -d --force-recreate gibd-scheduler
```

### C. File Size Estimates

| Directory | Size (per day) | Retention Policy |
|-----------|----------------|------------------|
| `data/` | ~100 MB | Keep 7 days, archive rest |
| `logs/` | ~50 MB | Keep 30 days, rotate weekly |
| Docker images | ~1.5 GB | Latest + 2 previous versions |

### D. Cron Schedule Quick Reference

```
* 4-7 * * 0-4     = Every minute, 4:00-7:59 AM, Mon-Fri
0-30 8 * * 0-4    = Every minute, 8:00-8:30 AM, Mon-Fri
0 11 * * 0-4      = 11:00 AM, Mon-Fri
0 * * * *         = Every hour, all days
0 17 * * *        = 5:00 PM, all days
```

### E. Contact & Support

- **Owner**: Platform Team
- **Slack**: #gibd-news
- **GitLab**: https://git.wizardsofts.com/gibd/gibd-news
- **Runbook**: `apps/gibd-news/docs/RUNBOOK.md`

---

**END OF DOCUMENT**

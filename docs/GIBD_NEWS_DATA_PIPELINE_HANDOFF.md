# GIBD News Data Pipeline - Deployment & Handoff Guide

## Overview

The GIBD News Data Pipeline consists of automated scrapers and processors that:
1. Fetch DSE (Dhaka Stock Exchange) daily stock prices
2. Scrape financial news from multiple sources (TBS News, Financial Express, Daily Star)
3. Process news with sentiment analysis and summarization
4. Store data in PostgreSQL for the quant trading system

## Infrastructure Status

### Cron Job Locations

| Server | User | Status | Purpose |
|--------|------|--------|---------|
| **Server 84** (10.0.0.84) | `wizardsofts` | **PRIMARY** | News scrapers, stock data fetching |
| **Server 80** (10.0.0.80) | `wizardsofts` | Active | DSE share price scraping, security scans |
| **Server 81** (10.0.0.81) | `wizardsofts` | Monitoring only | Security scans, cache cleanup |

### Server 84 Cron Schedule (Primary Data Collection)

```bash
# View current crontab
ssh wizardsofts@10.0.0.84 "crontab -l"

# GIBD-News Scrapers Schedule:
# News URL scrapers - every 2 hours
0 */2 * * *   fetch-financialexpress  # Financial Express
15 */2 * * *  fetch-tbsnews           # TBS News
30 */2 * * *  fetch-dailystar         # Daily Star

# News details fetcher - 45 minutes after URL scrapers
45 */2 * * *  fetch-news-details

# DSE stock data - once daily at 4 PM Bangladesh time (10:00 UTC)
0 10 * * 1-5  fetch-stock-data        # Mon-Fri only

# DSE share price - every 5 min during trading hours
*/5 3-9 * * 1-5  scrape-share-price   # 9:30 AM - 3:00 PM BDT
```

### Server 80 Cron Schedule (Supporting)

```bash
# DSE share price scraping (Sun-Thu, 4-7 AM)
* 4-7 * * 0-4 run_scrape_dse_latest_share_price.sh

# Indicator backfill (daily at 12:00 UTC)
0 12 * * * backfill_indicators.py

# DISABLED (uncomment to enable):
# 0 11 * * 0-4 cron_fetch_dse_daily_stock_data.sh
# 0 * * * *    cron_scrape_news_portals.sh
# 0 17 * * *   cron_news_summarizer.sh
```

## Critical Files & Paths

### Server 84

| Path | Purpose |
|------|---------|
| `/opt/wizardsofts-megabuild/apps/gibd-news/` | Application root |
| `/opt/wizardsofts-megabuild/apps/gibd-news/.env` | Environment config (**REQUIRED**) |
| `/opt/wizardsofts-megabuild/apps/gibd-news/logs/` | Cron job logs |
| `/opt/wizardsofts-megabuild/apps/gibd-news/docker-compose.yml` | Service definitions |

### Server 80

| Path | Purpose |
|------|---------|
| `/mnt/data/scheduled_tasks/tasks/scrape_news/` | Legacy scraper scripts |
| `/mnt/data/scheduled_tasks/logs/` | Script logs |
| `/home/agent/scripts/backfill_indicators.py` | Technical indicators backfill |

## Environment Configuration

### Required `.env` File (Server 84)

```bash
# Location: /opt/wizardsofts-megabuild/apps/gibd-news/.env
# Copy from .env.test or .env.example

# Database (PostgreSQL on Server 81)
POSTGRES_HOST=10.0.0.81
POSTGRES_PORT=5432
POSTGRES_DB=ws_gibd_news_database
POSTGRES_USER=ws_gibd
POSTGRES_PASSWORD=<password>

# API URLs (Backend services - if deployed)
GIBD_API_BASE_URL=http://10.0.0.84:8080/GIBD-NEWS-SERVICE
GIBD_TRADES_API_BASE_URL=http://10.0.0.84:8080/GIBD-TRADES

# Profile
ACTIVE_PROFILE=docker
```

### Creating .env from Template

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/gibd-news
cp .env.test .env  # OR cp .env.example .env and fill values
chmod 600 .env
```

## Running Services Manually

### Docker Compose Commands (Server 84)

```bash
cd /opt/wizardsofts-megabuild/apps/gibd-news

# Test configuration
docker-compose config

# Run individual scrapers
docker-compose run --rm fetch-financialexpress
docker-compose run --rm fetch-tbsnews
docker-compose run --rm fetch-dailystar
docker-compose run --rm fetch-news-details
docker-compose run --rm fetch-stock-data
docker-compose run --rm scrape-share-price

# Backfill (historical data)
docker-compose --profile backfill run --rm backfill-financialexpress
docker-compose --profile backfill run --rm backfill-tbsnews
docker-compose --profile backfill run --rm backfill-dailystar

# AI Processing (requires LLM API keys)
docker-compose run --rm sentiment-analyzer
docker-compose run --rm news-summarizer
```

## Database Access

### PostgreSQL Databases

| Database | Server | Port | Purpose |
|----------|--------|------|---------|
| `ws_gibd_news_database` | 10.0.0.81 | 5432 | News articles, sentiment |
| `ws_gibd_dse_daily_trades` | 10.0.0.81 | 5432 | Stock prices, indicators |

### Key Tables

```sql
-- Stock prices
SELECT COUNT(*), MAX(txn_date) FROM ws_dse_daily_prices;

-- Technical indicators
SELECT COUNT(*), MAX(trading_date) FROM indicators;

-- News articles (if populated)
SELECT COUNT(*), MAX(date) FROM news;
```

## Monitoring & Logs

### Check Cron Logs (Server 84)

```bash
# Recent activity
tail -50 /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_stock.log
tail -50 /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_fe.log
tail -50 /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_tbs.log
tail -50 /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_details.log

# Watch live
tail -f /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_price.log
```

### Check Data Freshness

```bash
# Latest stock price data
PGPASSWORD='29Dec2#24' psql -h 10.0.0.81 -U ws_gibd -d ws_gibd_dse_daily_trades \
  -c "SELECT MAX(txn_date), COUNT(*) FROM ws_dse_daily_prices;"

# Latest indicators
PGPASSWORD='29Dec2#24' psql -h 10.0.0.81 -U ws_gibd -d ws_gibd_dse_daily_trades \
  -c "SELECT MAX(trading_date), COUNT(*) FROM indicators;"
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `env file .env not found` | Missing .env file | `cp .env.test .env` |
| `connection refused` to API | Backend services not deployed | Use direct DB access |
| Stale data (>1 day old) | Cron not running | Check `crontab -l` and logs |
| Permission denied | Wrong user | Run as `wizardsofts` user |

### Fix Missing .env

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/gibd-news
cp .env.test .env
chmod 600 .env
```

### Restart Failed Service

```bash
# Check running containers
docker ps | grep gibd

# Force rebuild if needed
docker-compose build --no-cache fetch-stock-data
docker-compose run --rm fetch-stock-data
```

## User Access & Handoff

### Current Permissions

| User | Servers | Sudo | Purpose |
|------|---------|------|---------|
| `wizardsofts` | 80, 81, 84 | Yes | Primary operator, cron jobs |
| `agent` | 80, 81, 82, 84 | Limited | Automation, monitoring |
| `deploy` | TBD | TBD | Future deployment user |

### Making Scripts Accessible to All Users

```bash
# Option 1: Add users to docker group
sudo usermod -aG docker deploy
sudo usermod -aG docker agent

# Option 2: Create shared directory with group permissions
sudo chown -R wizardsofts:docker /opt/wizardsofts-megabuild/apps/gibd-news
sudo chmod -R g+rw /opt/wizardsofts-megabuild/apps/gibd-news

# Option 3: Move cron jobs to system cron (root)
sudo cp /home/wizardsofts/gibd-cron /etc/cron.d/gibd-news
```

### Handoff to Deploy User

1. **Create deploy user** (if not exists):
   ```bash
   sudo useradd -m -s /bin/bash deploy
   sudo usermod -aG docker deploy
   ```

2. **Copy crontab**:
   ```bash
   # Export current crontab
   crontab -l > /tmp/gibd-cron.txt

   # Import as deploy user
   sudo -u deploy crontab /tmp/gibd-cron.txt
   ```

3. **Verify permissions**:
   ```bash
   sudo -u deploy docker-compose config
   sudo -u deploy docker-compose run --rm fetch-financialexpress
   ```

## Backend Services (Future)

### Required Services (Not Yet Deployed)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| `ws-news` | 8080 | News API | **NOT DEPLOYED** |
| `ws-trades` | 8080 | Trades API | **NOT DEPLOYED** |

### Current Workaround

Scripts currently use direct PostgreSQL access instead of API:
- Connection: `10.0.0.81:5432`
- Credentials: In `.env` file

### Future: Deploy Backend Services

```bash
# When backend services are ready:
# 1. Deploy via Docker Compose or Swarm
# 2. Update .env to use service URLs:
GIBD_API_BASE_URL=http://ws-news:8080/GIBD-NEWS-SERVICE
GIBD_TRADES_API_BASE_URL=http://ws-trades:8080/GIBD-TRADES
```

## Incident Log

| Date | Issue | Resolution |
|------|-------|------------|
| 2026-01-06 | Data stale 100 days | `.env` file missing, copied from `.env.test` |
| 2026-01-05 | Cron logs show `env file not found` | Created `.env` file |

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Main project documentation
- [INDICATOR_BACKFILL.md](INDICATOR_BACKFILL.md) - Technical indicators system
- [apps/gibd-news/CLAUDE.md](../apps/gibd-news/CLAUDE.md) - App-specific docs

---

**Last Updated:** 2026-01-06
**Maintainer:** WizardSofts DevOps

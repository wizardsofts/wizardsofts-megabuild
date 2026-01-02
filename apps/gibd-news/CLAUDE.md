# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GIBD-News is a Financial News Business Intelligence Platform for Bangladesh. It scrapes financial news from multiple sources (The Daily Star, Financial Express, TBS News, DSE Archive), processes them with sentiment analysis and entity extraction, and stores data in PostgreSQL for investment decision-making.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest scripts/tests/

# Run individual scripts (from project root)
python scripts/fetch_urls_tbsnews.py
python scripts/fetch_news_details.py
python scripts/process_news_details.py {input_file_pattern}
python scripts/update_sentiment_scores.py
python scripts/news_summarizer.py
python scripts/fetch_dse_daily_stock_data.py
```

## Architecture

### Data Pipeline Flow
```
URL Scraping → Detail Fetching → Format Processing →
Sentiment Analysis → Summarization → Database/API Upload
```

### Key Components

**Scrapers** (scripts/):
- `fetch_urls_*.py` - Collect article URLs from news sources
- `fetch_news_details.py` - Extract full article content
- `scrape_dse_*.py` - DSE market data collection

**Processors** (scripts/):
- `process_news_details.py` - Clean and format raw articles
- `update_sentiment_scores.py` - Sentiment analysis via Ollama (localhost:11434)
- `news_summarizer.py` - LLM summarization (DeepSeek, OpenAI)
- `insert_news.py` - Database insertion with embeddings

**Shared Utilities** (scripts/utils.py):
- Configuration loading via `config/application-{profile}.properties`
- Selenium WebDriver setup (headless Chrome)
- Logging configuration
- Database connection management

### Configuration

Configuration is profile-based using `ACTIVE_PROFILE` environment variable (defaults to 'hp'):
- `config/application-hp.properties` - Production
- `config/application-local.properties` - Local development

Key config sections: `DEFAULT`, `THEDAILYSTAR`, `FINANCIALEXPRESS`, `TBSNEWS`, `DSEBD_NEWS_ARCHIEVE`

### External Services

- PostgreSQL database (connection config in properties)
- Backend API: `http://10.0.0.80:8080/GIBD-NEWS-SERVICE/api/news`
- DSE Trades API: `http://10.0.0.80:8080/GIBD-TRADES/api/dse-daily-prices`
- Ollama LLM: `localhost:11434`
- DeepSeek/OpenAI APIs for summarization

### Data Storage

- `data/` - Scraped news JSON files and stock price CSVs
- `logs/` - Timestamped application logs
- PostgreSQL news table with fields: url, title, subtitle, date, content, tags, embedding, sentiment_score

## Tech Stack

- **Scraping**: Selenium 4.27, BeautifulSoup
- **NLP/ML**: transformers, torch, sentence-transformers, NLTK, TextBlob
- **Database**: PostgreSQL (psycopg2)
- **LLM**: DeepSeek API, OpenAI, HuggingFace, Ollama

## Monitoring

The project includes a Prometheus metrics exporter for monitoring scraper health:

- **Metrics endpoint:** `http://localhost:9090/metrics`
- **Health endpoint:** `http://localhost:9090/health`
- **Metrics include:**
  - Article counts per source
  - URL collection counts
  - Last successful run timestamps
  - Error counts from logs
  - Scraper health status (1=healthy, 0=stale if not run in 3h)

Start the metrics exporter:
```bash
docker-compose up -d metrics
```

## Git Workflow

- Main branch: `main`
- Remote repositories: GitLab (origin) and GitHub (github)

## CI/CD Integration

This project is integrated into the megabuild monorepo CI/CD pipeline:
- **Pipeline triggers:** Changes to `apps/gibd-news/**/*` files
- **Deploy job:** `deploy-gibd-news` (manual trigger)
- **Target server:** 10.0.0.84 (HP Server)

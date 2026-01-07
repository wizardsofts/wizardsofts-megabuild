# Data Pipelines Documentation

Data processing, ETL pipelines, and ML data preparation.

## Contents

| Document | Description |
|----------|-------------|
| [gibd-news-pipeline.md](gibd-news-pipeline.md) | DSE stock data fetching |
| [indicator-backfill.md](indicator-backfill.md) | Technical indicator calculation |
| [data-cache.md](data-cache.md) | Parquet caching for ML training |

## Pipeline Overview

```
┌─────────────────────────────────────────┐
│ Daily Stock Data Fetch (10 AM UTC)      │
│ Cron: fetch-stock-data                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  PostgreSQL    │
        │  ws_gibd_dse   │
        └────────┬───────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Daily Indicator Backfill (12 PM UTC)    │
│ Cron: backfill_indicators.py            │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌─────────────────────────────┐
        │ TARP-DRL Training Pipeline  │
        │ (parquet cache)             │
        └─────────────────────────────┘
```

## Cron Jobs (Server 84)

| Schedule | Service | Purpose |
|----------|---------|---------|
| `0 10 * * 1-5` | fetch-stock-data | DSE daily prices |
| `*/5 3-9 * * 1-5` | scrape-share-price | Live prices |
| `0 12 * * *` | backfill_indicators.py | Technical indicators |

## Database

- **Host:** 10.0.0.81:5432
- **Database:** ws_gibd_dse_daily_trades
- **User:** ws_gibd

## Related Documentation

- [Deployment](../deployment/) - Service deployment
- [Operations](../operations/) - Cron job management
- [apps/gibd-news/](../../apps/gibd-news/) - News pipeline app

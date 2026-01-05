# Indicator Backfill System

## Overview

The indicator backfill system pre-computes and caches technical indicators for all DSE stock data. This enables fast feature loading during TARP-DRL training without computing indicators on-the-fly.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Daily Price    │     │   Backfill      │     │   Indicators    │
│  Data (828K+)   │────▶│   Script        │────▶│   Table         │
│  ws_dse_daily_  │     │   (Server 80)   │     │   (JSONB)       │
│  prices         │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │  Cron Job       │
                        │  (12 PM UTC)    │
                        └─────────────────┘
```

## Components

### Database

- **Server**: 10.0.0.81:5432
- **Database**: `ws_gibd_dse_daily_trades`
- **User**: `ws_gibd`

### Tables

**Source: `ws_dse_daily_prices`**
- Daily OHLCV data for all DSE stocks
- ~828,000+ rows (490 tickers × ~3,000 days)

**Target: `indicators`**
```sql
CREATE TABLE indicators (
    scrip text NOT NULL,
    trading_date date NOT NULL,
    indicators jsonb NOT NULL,
    status text NOT NULL DEFAULT 'CALCULATED',
    computed_at timestamp with time zone DEFAULT now(),
    version integer NOT NULL DEFAULT 1,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT indicators_pkey PRIMARY KEY (scrip, trading_date)
);
```

### Script Location

- **Source**: `apps/gibd-news/scripts/backfill_indicators.py`
- **Deployed**: Server 80 at `/home/agent/scripts/backfill_indicators.py`
- **Venv**: `/home/agent/indicator-backfill-venv/`
- **Logs**: `/home/agent/logs/indicator_backfill.log`

## Computed Indicators (29 Total)

### Moving Averages
- `SMA_3`, `SMA_5`, `SMA_20`, `SMA_50` - Simple Moving Average
- `EMA_3`, `EMA_20`, `EMA_50` - Exponential Moving Average

### Momentum
- `RSI_14` - Relative Strength Index (14 period)
- `MACD_line_12_26_9` - MACD line
- `MACD_signal_12_26_9` - MACD signal line
- `MACD_hist_12_26_9` - MACD histogram

### Volatility
- `ATR_14` - Average True Range (14 period)
- `BOLLINGER_upper_20_2` - Upper Bollinger Band
- `BOLLINGER_middle_20_2` - Middle Bollinger Band (20-day SMA)
- `BOLLINGER_lower_20_2` - Lower Bollinger Band
- `BOLLINGER_bandwidth_20_2` - Bollinger Bandwidth

### Volume Indicators
- `OBV` - On-Balance Volume (cumulative volume momentum)
- `volume_ratio_20` - Volume ratio (current / 20-day average)
- `volume_SMA_10` - 10-day Simple Moving Average of Volume
- `volume_SMA_20` - 20-day Simple Moving Average of Volume
- `MFI_14` - Money Flow Index (0-100, RSI weighted by volume)
  - Above 80: Overbought
  - Below 20: Oversold
- `AD_line` - Accumulation/Distribution Line (money flow tracking)
- `CMF_20` - Chaikin Money Flow (-1 to +1, 20-period)
  - Positive: Buying pressure
  - Negative: Selling pressure

### Price Features
- `log_return` - Logarithmic return
- `high_low_range` - (High - Low) / Close
- `close_open_diff` - (Close - Open) / Open

### Temporal Features
- `day_of_week` - 1 (Monday) to 5 (Friday)
- `week_of_month` - 1 to 4
- `month` - 1 to 12
- `is_month_end` - Boolean (last 3 days of month)
- `is_quarter_end` - Boolean (quarter-end month + month-end)

## Usage

### Manual Backfill

```bash
# SSH to Server 80
ssh agent@10.0.0.80

# Full historical backfill (processes all missing records)
/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py

# Dry run with limit
/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py --dry-run --limit 100

# Specific stock
/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py --scrip SQURPHARMA

# Today only (for daily incremental)
/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py --today-only
```

### Cron Schedule

The script runs daily at 12:00 PM UTC:

```cron
0 12 * * * /home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py >> /home/agent/logs/indicator_backfill.log 2>&1
```

### View Logs

```bash
ssh agent@10.0.0.80 "tail -100 /home/agent/logs/indicator_backfill.log"
```

## Configuration

Environment variables can override defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `INDICATOR_DB_HOST` | 10.0.0.81 | Database server |
| `INDICATOR_DB_PORT` | 5432 | Database port |
| `INDICATOR_DB_NAME` | ws_gibd_dse_daily_trades | Database name |
| `INDICATOR_DB_USER` | ws_gibd | Database user |
| `INDICATOR_DB_PASSWORD` | **** | Database password |

## Integration with TARP-DRL Training

After backfill, training can load pre-computed indicators:

```python
# In training code
import psycopg2
from psycopg2.extras import RealDictCursor

def load_indicators_from_db(scrip: str, trading_date: date) -> dict:
    """Load pre-computed indicators from database."""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT indicators FROM indicators
            WHERE scrip = %s AND trading_date = %s
        """, (scrip, trading_date))
        row = cur.fetchone()
        return row['indicators'] if row else None
```

## Monitoring

### Check Backfill Status

```bash
# Count total indicators
ssh agent@10.0.0.81 "PGPASSWORD='29Dec2#24' psql -h localhost -p 5432 -U ws_gibd -d ws_gibd_dse_daily_trades -t -c 'SELECT COUNT(*) FROM indicators'"

# Count missing indicators
ssh agent@10.0.0.81 "PGPASSWORD='29Dec2#24' psql -h localhost -p 5432 -U ws_gibd -d ws_gibd_dse_daily_trades -c '
SELECT COUNT(*) as missing
FROM ws_dse_daily_prices p
LEFT JOIN indicators i ON p.txn_scrip = i.scrip AND p.txn_date = i.trading_date
WHERE i.scrip IS NULL'"
```

### Check Cron Status

```bash
ssh agent@10.0.0.80 "crontab -l | grep backfill"
```

## Troubleshooting

### Script Not Running

1. Check cron is running:
   ```bash
   ssh agent@10.0.0.80 "sudo systemctl status cron"
   ```

2. Check virtual environment:
   ```bash
   ssh agent@10.0.0.80 "/home/agent/indicator-backfill-venv/bin/python --version"
   ```

3. Test manually:
   ```bash
   ssh agent@10.0.0.80 "/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py --dry-run --limit 1"
   ```

### Database Connection Issues

1. Verify database is accessible:
   ```bash
   ssh agent@10.0.0.81 "PGPASSWORD='29Dec2#24' psql -h localhost -p 5432 -U ws_gibd -d ws_gibd_dse_daily_trades -c 'SELECT 1'"
   ```

2. Check network connectivity:
   ```bash
   ssh agent@10.0.0.80 "nc -zv 10.0.0.81 5432"
   ```

### Indicator Calculation Errors

If specific indicators fail:
1. Check the logs for the specific scrip and date
2. Verify price data exists and has enough history
3. Most indicators require 50-200 days of historical data

## Performance

- **Batch Processing**: 100 records per batch (configurable)
- **Processing Rate**: ~100 records/second
- **Full Backfill**: ~2-3 hours for 828K records
- **Daily Incremental**: <1 minute for ~490 records

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-05 | Initial implementation with 23 indicators |

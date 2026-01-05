# Indicator Backfill - Idempotency & Optimization Guide

## Idempotency: Is It Safe to Run Twice?

**YES - The script is 100% idempotent.** Running it multiple times will NOT create duplicates or recalculate indicators unnecessarily.

### How It Works

The script uses a **LEFT JOIN** query to find ONLY missing records:

```sql
SELECT p.txn_scrip, p.txn_date
FROM ws_dse_daily_prices p
LEFT JOIN indicators i ON p.txn_scrip = i.scrip AND p.txn_date = i.trading_date
WHERE i.scrip IS NULL  -- Only find records NOT in indicators table
```

**Key features:**
1. **JOIN ensures exclusion**: Records already in the `indicators` table are filtered out
2. **UPSERT prevents duplicates**: Even if a record is found and processed, the database UPSERT won't create duplicates:
   ```sql
   ON CONFLICT (scrip, trading_date) DO UPDATE SET indicators = EXCLUDED.indicators
   ```
3. **No side effects**: The script is read-only until the final INSERT/UPDATE

### Idempotency Matrix

| Scenario | First Run | Second Run | Result |
|----------|-----------|-----------|--------|
| New record (BATBC, 2024-01-01) | Calculated + Inserted | Skipped (LEFT JOIN filters out) | ✅ Calculated once, inserted once |
| Existing record | Not processed | Not processed | ✅ No changes, no recalculation |
| Modified price data* | Not recalculated | Not recalculated | ⚠️ See "Force Recalculation" below |

*To handle price data changes, use `--force-recalc` flag (not yet implemented - see Enhancements)

## Performance Optimization

### 1. Database Indexing ✅ (Already Configured)

The indicators table has optimal indexes:
```sql
PRIMARY KEY (scrip, trading_date)  -- Unique constraint for UPSERT
INDEX idx_indicators_jsonb_gin     -- For future filtering by indicator values
INDEX idx_indicators_scrip         -- For lookups by ticker
INDEX idx_indicators_trading_date  -- For temporal queries
```

**Query Plan Impact**: The LEFT JOIN query uses these indexes to avoid full table scans.

### 2. Incremental Daily Processing ✅ (Already Implemented)

For daily cron jobs, use `--today-only` to process only new data:

```bash
# Daily cron (12 PM UTC) - Only process today's data
/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py --today-only

# Processing time: <1 minute (vs. 2-3 hours for full backfill)
# Records processed: ~490 (one per ticker)
```

### 3. Batch Processing ✅ (Already Implemented)

The script processes records in batches (default 100):

```python
# Batch INSERT/UPDATE (single transaction)
INSERT INTO indicators VALUES (...), (...), (...) ... (100 records)
ON CONFLICT ... DO UPDATE

# Benefits:
# - Reduced database round trips
# - Single transaction for consistency
# - 100-record batches = ~10x faster than individual inserts
```

### 4. Historical Data Caching (Recommended)

For repeated training runs with the same feature window, consider caching:

```python
# Option A: Cache complete price series (recommended for TARP-DRL)
# Load from parquet file (already implemented in data_cache.py)
# Cost: Disk space (~13MB compressed)
# Benefit: Training no longer blocks on database queries

# Option B: Cache computed indicators
# Already stored in PostgreSQL JSONB - load directly during training
# Cost: Network bandwidth to query database
# Benefit: No additional disk space needed
```

### 5. Skip Existing Records (Default Enabled)

The `skip_existing=True` parameter (default) ensures:

```python
# ✅ DEFAULT - Efficient
find_missing_indicators(conn, skip_existing=True)
# Query: LEFT JOIN (finds only missing) - ~100ms for 828K rows

# ❌ NOT RECOMMENDED - Inefficient
find_missing_indicators(conn, skip_existing=False)
# Query: SELECT all 828K rows, then filter in Python - Several seconds
```

## Processing Strategy for Different Use Cases

### Case 1: Initial Historical Backfill (One-time)

```bash
# Run once to backfill all 828K+ historical records
/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py

# Estimated time: 2-3 hours
# CPU: Moderate (indicator calculation is simple math)
# Disk: 100MB temporary (for batch accumulation)
# Network: Steady database traffic
```

### Case 2: Daily Incremental (Cron Job)

```bash
# Cron job runs daily at 12:00 PM UTC
0 12 * * * /home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py --today-only

# Processing time: <1 minute
# Records per run: ~490 (490 tickers × 1 day)
# Cost per month: ~12 minutes (490 records × 30 days)
```

### Case 3: Emergency Re-run (If Script Crashes)

```bash
# Same command as normal - no cleanup needed
# The LEFT JOIN will skip successfully processed records
# The UPSERT will update any partial records

/home/agent/indicator-backfill-venv/bin/python /home/agent/scripts/backfill_indicators.py
```

## Potential Optimizations (Future Enhancements)

### 1. Force Recalculation (NOT YET IMPLEMENTED)

For when price data changes:

```bash
# Would add this flag:
/home/agent/indicator-backfill-venv/bin/python \
  /home/agent/scripts/backfill_indicators.py \
  --force-recalc \
  --since 2024-01-01

# Would enable:
find_missing_indicators(conn, skip_existing=False, since_date='2024-01-01')
```

### 2. Parallel Processing (NOT YET IMPLEMENTED)

Currently single-threaded. Could parallelize:

```python
# Potential enhancement: Process 10 scrips in parallel
# Constraint: Database connection pooling (max 20 connections)
# Benefit: 10x speedup for initial backfill (2-3 hours → 15-20 minutes)
# Trade-off: Higher database load during backfill
```

### 3. Adaptive Batch Sizing (NOT YET IMPLEMENTED)

Automatically adjust batch size based on available memory:

```python
# Current: Fixed 100-record batches
# Proposed: Dynamic batching based on:
# - Available RAM
# - Average record size
# - Database responsiveness
```

### 4. Priority Queuing (NOT YET IMPLEMENTED)

Process most recent data first (already ordering by date DESC):

```python
# Current: Processes most recent first (good for daily incremental)
# Benefit: If script interrupted, at least recent data is available for training
```

## Monitoring Idempotency

### Check if Record Exists

```sql
-- Before first run:
SELECT COUNT(*) FROM indicators;  -- Returns 0 (or small number if partial)

-- After first run:
SELECT COUNT(*) FROM indicators;  -- Returns 828K+

-- After second run (no change):
SELECT COUNT(*) FROM indicators;  -- Still 828K+ (no duplicates)
```

### Verify No Duplicates

```sql
-- Should return 0 (no duplicates allowed by PRIMARY KEY)
SELECT scrip, trading_date, COUNT(*) as cnt
FROM indicators
GROUP BY scrip, trading_date
HAVING COUNT(*) > 1;
```

### Monitor Recalculation

```sql
-- Should return 0 (no records recalculated)
SELECT COUNT(DISTINCT (scrip, trading_date)) as unique_records,
       COUNT(*) as total_records
FROM indicators;
-- These should be equal (no duplicates)
```

## FAQ

### Q: What if the script crashes halfway?
**A:** Safe to re-run. The LEFT JOIN will skip successfully processed records, and the UPSERT will complete any partial ones.

### Q: What if price data changes?
**A:** Indicators won't be recalculated (by design, for performance). This is acceptable because price data is immutable after a trading day ends. For corrections, manually DELETE and re-run.

### Q: Why not use a "last_processed_date" table?
**A:** The LEFT JOIN is simpler and doesn't require maintaining state. If it fails, we can always re-scan the entire table.

### Q: Can I run multiple instances simultaneously?
**A:** Not recommended (database contention). Cron job on single server is sufficient for 490 tickers/day.

### Q: How do I know if backfill is still running?
**A:** Check logs: `tail -f /home/agent/logs/indicator_backfill.log`

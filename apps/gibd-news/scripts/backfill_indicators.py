#!/usr/bin/env python3
"""Daily indicator backfill script for DSE stock data.

This script:
1. Finds all (scrip, trading_date) pairs in ws_dse_daily_prices without indicators
2. Computes 23 technical indicators for each missing pair
3. Inserts results into the indicators table

Designed for both:
- Initial backfill: Process all historical data (~828K rows × 490 tickers)
- Daily incremental: Process only new dates added since last run

Usage:
    # Dry run (no database writes)
    python backfill_indicators.py --dry-run --limit 100

    # Process specific scrip
    python backfill_indicators.py --scrip SQURPHARMA

    # Full backfill (all missing)
    python backfill_indicators.py

    # Daily incremental (only today's missing)
    python backfill_indicators.py --today-only

Cron Job (12 PM UTC daily):
    0 12 * * * cd /path/to/gibd-news/scripts && python backfill_indicators.py >> /var/log/indicator_backfill.log 2>&1
"""

import os
import sys
import argparse
import logging
import json
import math
import statistics
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values, Json

# Database configuration (Server 81)
DB_CONFIG = {
    'host': os.getenv('INDICATOR_DB_HOST', '10.0.0.81'),
    'port': int(os.getenv('INDICATOR_DB_PORT', '5432')),
    'database': os.getenv('INDICATOR_DB_NAME', 'ws_gibd_dse_daily_trades'),
    'user': os.getenv('INDICATOR_DB_USER', 'ws_gibd'),
    'password': os.getenv('INDICATOR_DB_PASSWORD', '29Dec2#24'),
}

# Lookback period for indicator calculation (need historical data for moving averages)
LOOKBACK_DAYS = 200

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Technical Indicator Functions (from gibd-quant-agent/src/indicators/calc.py)
# ============================================================================

def sma(close: List[float], window: int) -> Optional[float]:
    """Simple Moving Average (returns most recent SMA)."""
    if close is None or len(close) < window:
        return None
    return sum(close[-window:]) / float(window)


def ema(close: List[float], window: int) -> Optional[float]:
    """Exponential Moving Average (returns most recent EMA).
    Uses standard smoothing with alpha = 2 / (window + 1).
    """
    if close is None or len(close) < window:
        return None
    alpha = 2.0 / (window + 1)
    ema_prev = sum(close[:window]) / float(window)
    for price in close[window:]:
        ema_prev = alpha * price + (1 - alpha) * ema_prev
    return ema_prev


def ema_series(close: List[float], window: int) -> List[float]:
    """Return EMA series (aligned from index window-1 to end)."""
    if close is None or len(close) < window:
        return []
    alpha = 2.0 / (window + 1)
    ema_vals: List[float] = []
    ema_prev = sum(close[:window]) / float(window)
    ema_vals.append(ema_prev)
    for price in close[window:]:
        ema_prev = alpha * price + (1 - alpha) * ema_prev
        ema_vals.append(ema_prev)
    return ema_vals


def rsi(close: List[float], period: int) -> Optional[float]:
    """Relative Strength Index (0-100)."""
    if close is None or len(close) <= period:
        return None
    deltas = [close[i] - close[i - 1] for i in range(1, len(close))]
    recent = deltas[-period:]
    gains = sum(d for d in recent if d > 0)
    losses = -sum(d for d in recent if d < 0)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(close: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Compute MACD line, signal, and histogram."""
    if close is None or len(close) < slow:
        return (None, None, None)
    fast_ema = ema_series(close, fast)
    slow_ema = ema_series(close, slow)
    offset = (slow - fast)
    if offset < 0:
        return (None, None, None)
    macd_vals: List[float] = []
    for i in range(len(slow_ema)):
        f_idx = i + offset
        if f_idx < 0 or f_idx >= len(fast_ema):
            continue
        macd_vals.append(fast_ema[f_idx] - slow_ema[i])
    if len(macd_vals) < signal:
        return (None, None, None)
    macd_line = macd_vals[-1]
    signal_vals = ema_series(macd_vals, signal)
    if not signal_vals:
        return (None, None, None)
    signal_line = signal_vals[-1]
    hist = macd_line - signal_line
    return (macd_line, signal_line, hist)


def obv(close: List[float], volume: List[float]) -> Optional[float]:
    """On-Balance Volume."""
    if close is None or volume is None or len(close) != len(volume) or len(close) == 0:
        return None
    obv_val = 0
    for i in range(1, len(close)):
        if close[i] > close[i - 1]:
            obv_val += int(volume[i])
        elif close[i] < close[i - 1]:
            obv_val -= int(volume[i])
    return float(obv_val)


def bollinger(close: List[float], window: int = 20, num_std: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """Bollinger Bands: (upper, middle, lower, bandwidth)."""
    if close is None or len(close) < window:
        return (None, None, None, None)
    window_vals = close[-window:]
    middle = sum(window_vals) / float(window)
    std = statistics.pstdev(window_vals)
    upper = middle + num_std * std
    lower = middle - num_std * std
    bandwidth = (upper - lower) / middle if middle != 0 else None
    return (upper, middle, lower, bandwidth)


def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> Optional[float]:
    """Average True Range."""
    if high is None or low is None or close is None:
        return None
    if not (len(high) == len(low) == len(close)):
        return None
    if len(close) <= period:
        return None
    trs: List[float] = []
    for i in range(1, len(close)):
        tr = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / float(period)


def volume_ratio(volume: List[float], window: int = 20) -> Optional[float]:
    """Volume ratio: current volume / average volume over window."""
    if volume is None or len(volume) < window:
        return None
    avg_vol = sum(volume[-window:]) / float(window)
    if avg_vol == 0:
        return None
    return volume[-1] / avg_vol


def volume_sma(volume: List[float], window: int) -> Optional[float]:
    """Simple Moving Average of Volume."""
    if volume is None or len(volume) < window:
        return None
    return sum(volume[-window:]) / float(window)


def money_flow_index(high: List[float], low: List[float], close: List[float], volume: List[float], period: int = 14) -> Optional[float]:
    """Money Flow Index (MFI) - RSI weighted by volume.

    Ranges from 0 to 100:
    - Above 80: Overbought
    - Below 20: Oversold
    """
    if high is None or low is None or close is None or volume is None:
        return None
    if not (len(high) == len(low) == len(close) == len(volume)):
        return None
    if len(close) <= period:
        return None

    # Calculate typical price: (High + Low + Close) / 3
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]

    # Calculate raw money flow: typical price * volume
    raw_money_flow = [tp * v for tp, v in zip(typical_prices, volume)]

    # Calculate positive and negative money flow
    positive_flow = 0.0
    negative_flow = 0.0

    for i in range(-period, 0):
        if typical_prices[i] > typical_prices[i - 1]:
            positive_flow += raw_money_flow[i]
        elif typical_prices[i] < typical_prices[i - 1]:
            negative_flow += raw_money_flow[i]

    if negative_flow == 0:
        return 100.0

    money_ratio = positive_flow / negative_flow
    mfi = 100 - (100 / (1 + money_ratio))
    return mfi


def accumulation_distribution(high: List[float], low: List[float], close: List[float], volume: List[float]) -> Optional[float]:
    """Accumulation/Distribution Line.

    Measures cumulative flow of money in/out of a stock based on:
    - Money Flow Multiplier: ((Close - Low) - (High - Close)) / (High - Low)
    - Money Flow Volume: MFM * Volume
    - A/D Line: Running sum of Money Flow Volume
    """
    if high is None or low is None or close is None or volume is None:
        return None
    if not (len(high) == len(low) == len(close) == len(volume)):
        return None
    if len(close) == 0:
        return None

    ad_line = 0.0
    for h, l, c, v in zip(high, low, close, volume):
        if h == l:  # Avoid division by zero
            mfm = 0.0
        else:
            mfm = ((c - l) - (h - c)) / (h - l)
        mfv = mfm * v
        ad_line += mfv

    return ad_line


def chaikin_money_flow(high: List[float], low: List[float], close: List[float], volume: List[float], period: int = 20) -> Optional[float]:
    """Chaikin Money Flow (CMF).

    Ranges from -1 to +1:
    - Positive: Buying pressure
    - Negative: Selling pressure
    """
    if high is None or low is None or close is None or volume is None:
        return None
    if not (len(high) == len(low) == len(close) == len(volume)):
        return None
    if len(close) < period:
        return None

    mfv_sum = 0.0
    vol_sum = 0.0

    for i in range(-period, 0):
        h, l, c, v = high[i], low[i], close[i], volume[i]
        if h == l:
            mfm = 0.0
        else:
            mfm = ((c - l) - (h - c)) / (h - l)
        mfv_sum += mfm * v
        vol_sum += v

    if vol_sum == 0:
        return None

    return mfv_sum / vol_sum


def log_return(close: List[float]) -> Optional[float]:
    """Log return: log(close_t / close_t-1)."""
    if close is None or len(close) < 2:
        return None
    if close[-2] <= 0 or close[-1] <= 0:
        return None
    return math.log(close[-1] / close[-2])


def high_low_range(high: List[float], low: List[float], close: List[float]) -> Optional[float]:
    """High-low range normalized by close."""
    if high is None or low is None or close is None:
        return None
    if len(high) == 0 or len(low) == 0 or len(close) == 0:
        return None
    if close[-1] == 0:
        return None
    return (high[-1] - low[-1]) / close[-1]


def close_open_diff(close: List[float], open_: List[float]) -> Optional[float]:
    """Close-open difference normalized by open."""
    if close is None or open_ is None:
        return None
    if len(close) == 0 or len(open_) == 0:
        return None
    if open_[-1] == 0:
        return None
    return (close[-1] - open_[-1]) / open_[-1]


def temporal_features(trading_date: date) -> Dict[str, Any]:
    """Extract temporal features from trading date."""
    if trading_date is None:
        return {
            'day_of_week': None,
            'week_of_month': None,
            'month': None,
            'is_month_end': None,
            'is_quarter_end': None
        }
    dow = trading_date.weekday() + 1
    week_of_month = (trading_date.day - 1) // 7 + 1
    month = trading_date.month
    if trading_date.month == 12:
        next_month_first = date(trading_date.year + 1, 1, 1)
    else:
        next_month_first = date(trading_date.year, trading_date.month + 1, 1)
    days_to_month_end = (next_month_first - trading_date).days
    is_month_end = days_to_month_end <= 3
    is_quarter_end = month in (3, 6, 9, 12) and is_month_end
    return {
        'day_of_week': dow,
        'week_of_month': week_of_month,
        'month': month,
        'is_month_end': is_month_end,
        'is_quarter_end': is_quarter_end
    }


def compute_all_indicators(
    price_series: Dict[str, List[float]],
    trading_date: Optional[date] = None
) -> Dict[str, Any]:
    """Compute all 23 technical indicators from price series.

    Args:
        price_series: Dict with keys 'open', 'high', 'low', 'close', 'volume'
                     Each value is a list in chronological order (oldest first)
        trading_date: Trading date for temporal features

    Returns:
        Dict mapping indicator name to value (or None if insufficient data)
    """
    close = price_series.get('close', []) or []
    high = price_series.get('high', []) or []
    low = price_series.get('low', []) or []
    open_ = price_series.get('open', []) or []
    volume = price_series.get('volume', []) or []

    indicators: Dict[str, Any] = {}

    # SMA (3, 5, 20, 50)
    for w in (3, 5, 20, 50):
        try:
            indicators[f'SMA_{w}'] = sma(close, w)
        except Exception:
            indicators[f'SMA_{w}'] = None

    # EMA (3, 20, 50)
    for w in (3, 20, 50):
        try:
            indicators[f'EMA_{w}'] = ema(close, w)
        except Exception:
            indicators[f'EMA_{w}'] = None

    # RSI (14)
    try:
        indicators['RSI_14'] = rsi(close, 14)
    except Exception:
        indicators['RSI_14'] = None

    # MACD (12, 26, 9)
    try:
        macd_line, macd_signal, macd_hist = macd(close, 12, 26, 9)
        indicators['MACD_line_12_26_9'] = macd_line
        indicators['MACD_signal_12_26_9'] = macd_signal
        indicators['MACD_hist_12_26_9'] = macd_hist
    except Exception:
        indicators['MACD_line_12_26_9'] = None
        indicators['MACD_signal_12_26_9'] = None
        indicators['MACD_hist_12_26_9'] = None

    # OBV
    try:
        indicators['OBV'] = obv(close, volume)
    except Exception:
        indicators['OBV'] = None

    # Bollinger Bands (20, 2)
    try:
        upper, middle, lower, bw = bollinger(close, 20, 2.0)
        indicators['BOLLINGER_upper_20_2'] = upper
        indicators['BOLLINGER_middle_20_2'] = middle
        indicators['BOLLINGER_lower_20_2'] = lower
        indicators['BOLLINGER_bandwidth_20_2'] = bw
    except Exception:
        indicators['BOLLINGER_upper_20_2'] = None
        indicators['BOLLINGER_middle_20_2'] = None
        indicators['BOLLINGER_lower_20_2'] = None
        indicators['BOLLINGER_bandwidth_20_2'] = None

    # ATR (14)
    try:
        indicators['ATR_14'] = atr(high, low, close, 14)
    except Exception:
        indicators['ATR_14'] = None

    # Volume ratio (20)
    try:
        indicators['volume_ratio_20'] = volume_ratio(volume, 20)
    except Exception:
        indicators['volume_ratio_20'] = None

    # Volume SMA (10, 20)
    for w in (10, 20):
        try:
            indicators[f'volume_SMA_{w}'] = volume_sma(volume, w)
        except Exception:
            indicators[f'volume_SMA_{w}'] = None

    # Money Flow Index (14)
    try:
        indicators['MFI_14'] = money_flow_index(high, low, close, volume, 14)
    except Exception:
        indicators['MFI_14'] = None

    # Accumulation/Distribution Line
    try:
        indicators['AD_line'] = accumulation_distribution(high, low, close, volume)
    except Exception:
        indicators['AD_line'] = None

    # Chaikin Money Flow (20)
    try:
        indicators['CMF_20'] = chaikin_money_flow(high, low, close, volume, 20)
    except Exception:
        indicators['CMF_20'] = None

    # Log return
    try:
        indicators['log_return'] = log_return(close)
    except Exception:
        indicators['log_return'] = None

    # High-low range
    try:
        indicators['high_low_range'] = high_low_range(high, low, close)
    except Exception:
        indicators['high_low_range'] = None

    # Close-open diff
    try:
        indicators['close_open_diff'] = close_open_diff(close, open_)
    except Exception:
        indicators['close_open_diff'] = None

    # Temporal features
    if trading_date:
        temp = temporal_features(trading_date)
        indicators.update(temp)
    else:
        indicators['day_of_week'] = None
        indicators['week_of_month'] = None
        indicators['month'] = None
        indicators['is_month_end'] = None
        indicators['is_quarter_end'] = None

    return indicators


# ============================================================================
# Database Functions
# ============================================================================

def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(**DB_CONFIG)


def find_missing_indicators(
    conn,
    scrip_filter: Optional[str] = None,
    today_only: bool = False,
    limit: Optional[int] = None,
    skip_existing: bool = True
) -> List[Tuple[str, date]]:
    """Find (scrip, trading_date) pairs to process.

    **Idempotency**: Uses LEFT JOIN to find ONLY records not in indicators table.
    Running twice won't recalculate - it's safe and efficient.

    Args:
        conn: Database connection
        scrip_filter: Optional scrip to filter
        today_only: If True, only find today's missing indicators
        limit: Optional limit on results
        skip_existing: If True, skip records already in indicators table (RECOMMENDED)

    Returns:
        List of (scrip, trading_date) tuples
    """
    if skip_existing:
        # PRIMARY QUERY: Only find records NOT in indicators (idempotent)
        # LEFT JOIN ensures we don't recalculate existing indicators
        query = """
            SELECT p.txn_scrip, p.txn_date
            FROM ws_dse_daily_prices p
            LEFT JOIN indicators i ON p.txn_scrip = i.scrip AND p.txn_date = i.trading_date
            WHERE i.scrip IS NULL
        """
    else:
        # FORCE RECALC: Find ALL records (only use if you want to force recalculation)
        query = "SELECT txn_scrip, txn_date FROM ws_dse_daily_prices WHERE 1=1"

    params = []

    if scrip_filter:
        col = "p.txn_scrip" if skip_existing else "txn_scrip"
        query += f" AND {col} = %s"
        params.append(scrip_filter)

    if today_only:
        col = "p.txn_date" if skip_existing else "txn_date"
        query += f" AND {col} = CURRENT_DATE"

    # Order most recent first (new data before old)
    col_scrip = "p.txn_scrip" if skip_existing else "txn_scrip"
    col_date = "p.txn_date" if skip_existing else "txn_date"
    query += f" ORDER BY {col_date} DESC, {col_scrip}"

    if limit:
        query += f" LIMIT {limit}"

    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_price_series(
    conn,
    scrip: str,
    trading_date: date,
    lookback: int = LOOKBACK_DAYS
) -> Optional[Dict[str, List[float]]]:
    """Fetch historical price series for indicator calculation.

    Args:
        conn: Database connection
        scrip: Stock ticker
        trading_date: Target date
        lookback: Number of days to look back

    Returns:
        Dict with 'open', 'high', 'low', 'close', 'volume' lists (chronological)
    """
    query = """
        SELECT txn_open, txn_high, txn_low, txn_close, txn_volume
        FROM ws_dse_daily_prices
        WHERE txn_scrip = %s AND txn_date <= %s
        ORDER BY txn_date DESC
        LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(query, (scrip, trading_date, lookback))
        rows = cur.fetchall()

    if not rows:
        return None

    # Reverse to chronological order (oldest first)
    rows = rows[::-1]

    return {
        'open': [float(r[0]) if r[0] is not None else 0.0 for r in rows],
        'high': [float(r[1]) if r[1] is not None else 0.0 for r in rows],
        'low': [float(r[2]) if r[2] is not None else 0.0 for r in rows],
        'close': [float(r[3]) if r[3] is not None else 0.0 for r in rows],
        'volume': [float(r[4]) if r[4] is not None else 0.0 for r in rows],
    }


def insert_indicators_batch(
    conn,
    records: List[Tuple[str, date, Dict[str, Any]]],
    dry_run: bool = False
) -> int:
    """Batch insert indicator records.

    Args:
        conn: Database connection
        records: List of (scrip, trading_date, indicators_dict) tuples
        dry_run: If True, don't actually insert

    Returns:
        Number of records inserted
    """
    if not records:
        return 0

    if dry_run:
        logger.info(f"[DRY RUN] Would insert {len(records)} records")
        return len(records)

    query = """
        INSERT INTO indicators (scrip, trading_date, indicators, status, notes)
        VALUES %s
        ON CONFLICT (scrip, trading_date) DO UPDATE SET
            indicators = EXCLUDED.indicators,
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            updated_at = NOW()
    """

    values = [
        (scrip, trading_date, Json(indicators), 'CALCULATED', 'Backfilled by daily job')
        for scrip, trading_date, indicators in records
    ]

    with conn.cursor() as cur:
        execute_values(cur, query, values, template="(%s, %s, %s, %s, %s)")

    conn.commit()
    return len(records)


# ============================================================================
# Main Backfill Logic
# ============================================================================

def backfill_indicators(
    dry_run: bool = False,
    limit: Optional[int] = None,
    scrip_filter: Optional[str] = None,
    today_only: bool = False,
    batch_size: int = 100
) -> Dict[str, int]:
    """Run indicator backfill process.

    Args:
        dry_run: If True, don't write to database
        limit: Optional limit on records to process
        scrip_filter: Optional scrip to filter
        today_only: If True, only process today's data
        batch_size: Number of records to insert per batch

    Returns:
        Summary dict with counts
    """
    logger.info("=" * 60)
    logger.info("INDICATOR BACKFILL STARTED")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"  - Dry run: {dry_run}")
    logger.info(f"  - Limit: {limit}")
    logger.info(f"  - Scrip filter: {scrip_filter}")
    logger.info(f"  - Today only: {today_only}")
    logger.info(f"  - Batch size: {batch_size}")
    logger.info(f"  - Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    summary = {
        'total_missing': 0,
        'processed': 0,
        'inserted': 0,
        'skipped': 0,
        'errors': 0,
    }

    conn = get_db_connection()

    try:
        # Find missing indicators
        logger.info("Finding missing indicators...")
        missing = find_missing_indicators(conn, scrip_filter, today_only, limit)
        summary['total_missing'] = len(missing)
        logger.info(f"Found {len(missing)} missing indicator records")

        if not missing:
            logger.info("No missing indicators. Backfill complete.")
            return summary

        # Process in batches
        batch: List[Tuple[str, date, Dict[str, Any]]] = []
        total = len(missing)

        for idx, (scrip, trading_date) in enumerate(missing):
            try:
                # Convert date if needed
                if isinstance(trading_date, str):
                    trading_date = datetime.strptime(trading_date, '%Y-%m-%d').date()

                # Fetch price series
                price_series = get_price_series(conn, scrip, trading_date)

                if price_series is None:
                    logger.warning(f"No price data for {scrip} on {trading_date}")
                    summary['skipped'] += 1
                    continue

                # Compute indicators
                indicators = compute_all_indicators(price_series, trading_date)

                # Add to batch
                batch.append((scrip, trading_date, indicators))
                summary['processed'] += 1

                # Insert batch when full
                if len(batch) >= batch_size:
                    inserted = insert_indicators_batch(conn, batch, dry_run)
                    summary['inserted'] += inserted
                    batch = []

                # Progress logging
                if (idx + 1) % 500 == 0 or (idx + 1) == total:
                    pct = 100 * (idx + 1) / total
                    logger.info(f"Progress: {idx + 1}/{total} ({pct:.1f}%)")

            except Exception as e:
                logger.error(f"Error processing {scrip} on {trading_date}: {e}")
                summary['errors'] += 1

        # Insert remaining batch
        if batch:
            inserted = insert_indicators_batch(conn, batch, dry_run)
            summary['inserted'] += inserted

    finally:
        conn.close()

    # Final summary
    logger.info("=" * 60)
    logger.info("BACKFILL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total missing:  {summary['total_missing']}")
    logger.info(f"Processed:      {summary['processed']}")
    logger.info(f"Inserted:       {summary['inserted']}")
    logger.info(f"Skipped:        {summary['skipped']}")
    logger.info(f"Errors:         {summary['errors']}")

    if dry_run:
        logger.info("\n[DRY RUN] No changes were written to database")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Backfill technical indicators for DSE stock data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run with 100 records
    python backfill_indicators.py --dry-run --limit 100

    # Process specific stock
    python backfill_indicators.py --scrip SQURPHARMA

    # Daily incremental (cron job)
    python backfill_indicators.py --today-only

    # Full historical backfill
    python backfill_indicators.py
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate without writing to database')
    parser.add_argument('--limit', type=int,
                        help='Limit number of records to process')
    parser.add_argument('--scrip', type=str,
                        help='Filter to specific stock ticker')
    parser.add_argument('--today-only', action='store_true',
                        help='Only process today\'s missing indicators')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Batch size for database inserts (default: 100)')

    args = parser.parse_args()

    try:
        summary = backfill_indicators(
            dry_run=args.dry_run,
            limit=args.limit,
            scrip_filter=args.scrip,
            today_only=args.today_only,
            batch_size=args.batch_size
        )

        # Exit with error if there were errors
        if summary['errors'] > 0:
            logger.warning(f"Completed with {summary['errors']} errors")
            sys.exit(1)

        logger.info("Backfill completed successfully")

    except KeyboardInterrupt:
        logger.info("\nBackfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

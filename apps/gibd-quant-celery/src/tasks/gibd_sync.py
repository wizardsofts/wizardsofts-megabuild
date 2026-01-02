"""Celery tasks for synchronizing with GIBD database and monitoring data quality.

These tasks verify data freshness, identify missing indicators, and perform
daily health checks on the GIBD data that Quant-Flow depends on.

Tasks:
- verify_data_freshness: Check latest data availability
- check_missing_indicators: Identify gaps in indicator computation
- daily_health_check: Comprehensive daily monitoring
"""

import logging
from datetime import date, timedelta

from sqlalchemy import distinct, func

from src.celery_app import app
from src.database.connection import get_db_context
from src.database.models import Indicator, WsDseDailyPrice

logger = logging.getLogger(__name__)


@app.task(name="gibd_sync.verify_data_freshness")
def verify_data_freshness() -> dict:
    """Verify that GIBD data is up-to-date.

    Checks:
    1. Latest date in ws_dse_daily_prices
    2. Number of tickers with recent data
    3. Indicator computation status

    Returns:
        Dict with data freshness metrics:
        {
            "status": "ok" | "stale" | "error",
            "latest_trading_date": "2025-12-22",
            "days_old": 0,
            "tickers_with_data": 350,
            "indicators_computed": 350,
            "indicators_pending": 0,
        }
    """
    try:
        with get_db_context() as session:
            # Get latest trading date
            latest_date = session.query(func.max(WsDseDailyPrice.txn_date)).scalar()

            if not latest_date:
                return {
                    "status": "error",
                    "message": "No data found in ws_dse_daily_prices",
                    "latest_trading_date": None,
                    "days_old": None,
                }

            # Count tickers with data on latest date
            ticker_count = (
                session.query(func.count(distinct(WsDseDailyPrice.txn_scrip)))
                .filter(WsDseDailyPrice.txn_date == latest_date)
                .scalar()
            )

            # Check indicator computation status
            indicators_computed = (
                session.query(func.count(Indicator.scrip))
                .filter(Indicator.trading_date == latest_date, Indicator.status == "CALCULATED")
                .scalar()
            )

            indicators_pending = ticker_count - indicators_computed
            days_old = (date.today() - latest_date).days

            # Determine status
            status = "ok" if days_old <= 1 else "stale"

            result = {
                "status": status,
                "latest_trading_date": latest_date.isoformat(),
                "days_old": days_old,
                "tickers_with_data": ticker_count,
                "indicators_computed": indicators_computed,
                "indicators_pending": indicators_pending,
            }

            logger.info(
                f"Data freshness check: {status} - "
                f"{latest_date} ({days_old} days old), "
                f"{indicators_computed}/{ticker_count} indicators"
            )

            return result

    except Exception as e:
        logger.error(f"Error verifying data freshness: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }


@app.task(name="gibd_sync.check_missing_indicators")
def check_missing_indicators(lookback_days: int = 7) -> dict:
    """Identify tickers with missing indicators.

    Compares price data availability with indicator computation to find gaps.

    Args:
        lookback_days: Number of days to check (default: 7)

    Returns:
        Dict with missing indicator statistics:
        {
            "total_price_records": 2450,
            "total_indicator_records": 2400,
            "missing_indicators": 50,
            "coverage_pct": 97.96,
            "missing_sample": [("GP", "2025-12-22"), ...],
        }
    """
    try:
        with get_db_context() as session:
            cutoff_date = date.today() - timedelta(days=lookback_days)

            # Get all ticker-date combinations from ws_dse_daily_prices
            price_data = (
                session.query(WsDseDailyPrice.txn_scrip, WsDseDailyPrice.txn_date)
                .filter(WsDseDailyPrice.txn_date >= cutoff_date)
                .all()
            )

            # Get all ticker-date combinations with computed indicators
            indicator_data = (
                session.query(Indicator.scrip, Indicator.trading_date)
                .filter(Indicator.trading_date >= cutoff_date, Indicator.status == "CALCULATED")
                .all()
            )

            # Convert to sets for comparison
            price_set = {(row[0], row[1]) for row in price_data}
            indicator_set = {(row[0], row[1]) for row in indicator_data}

            # Find missing indicators
            missing = price_set - indicator_set

            # Calculate coverage
            coverage_pct = (len(indicator_set) / len(price_set) * 100) if price_set else 0

            result = {
                "lookback_days": lookback_days,
                "total_price_records": len(price_set),
                "total_indicator_records": len(indicator_set),
                "missing_indicators": len(missing),
                "coverage_pct": round(coverage_pct, 2),
                "missing_sample": list(missing)[:10],  # First 10 missing
            }

            if missing:
                logger.warning(
                    f"Missing indicators: {len(missing)} out of {len(price_set)} "
                    f"({100 - coverage_pct:.1f}% missing)"
                )
            else:
                logger.info(f"All indicators present for last {lookback_days} days")

            return result

    except Exception as e:
        logger.error(f"Error checking missing indicators: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }


@app.task(name="gibd_sync.daily_health_check", bind=True)
def daily_health_check(self) -> dict:
    """Comprehensive daily health check of GIBD data.

    Runs all verification tasks and sends alerts if issues found.

    Returns:
        Dict with overall health status:
        {
            "status": "healthy" | "critical",
            "freshness": {...},
            "missing_indicators": {...},
            "issues": ["Data is 3 days old", ...],
        }
    """
    try:
        logger.info("Starting daily GIBD health check")

        # Run sub-checks
        freshness_result = verify_data_freshness()
        missing_result = check_missing_indicators(lookback_days=7)

        # Analyze results
        issues = []

        # Check freshness
        if freshness_result.get("status") == "error":
            issues.append("No data in ws_dse_daily_prices")
        elif freshness_result.get("days_old", 0) > 3:
            issues.append(f"Data is {freshness_result['days_old']} days old")

        # Check indicator coverage
        coverage_pct = missing_result.get("coverage_pct", 100)
        if coverage_pct < 90:
            issues.append(f"Only {coverage_pct:.1f}% indicator coverage")

        # Determine overall status
        status = "critical" if issues else "healthy"

        result = {
            "status": status,
            "timestamp": date.today().isoformat(),
            "freshness": freshness_result,
            "missing_indicators": missing_result,
            "issues": issues,
        }

        if issues:
            logger.error(f"GIBD health check FAILED: {', '.join(issues)}")
        else:
            logger.info("GIBD health check PASSED")

        return result

    except Exception as e:
        logger.error(f"Error during health check: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }


@app.task(name="gibd_sync.get_ticker_coverage")
def get_ticker_coverage(ticker: str, lookback_days: int = 30) -> dict:
    """Get data coverage statistics for a specific ticker.

    Args:
        ticker: Stock ticker symbol
        lookback_days: Number of days to check (default: 30)

    Returns:
        Dict with ticker-specific coverage:
        {
            "ticker": "GP",
            "lookback_days": 30,
            "price_data_days": 22,
            "indicator_days": 22,
            "coverage_pct": 100.0,
            "latest_price_date": "2025-12-22",
            "latest_indicator_date": "2025-12-22",
        }
    """
    try:
        with get_db_context() as session:
            cutoff_date = date.today() - timedelta(days=lookback_days)

            # Count price data days
            price_days = (
                session.query(func.count(distinct(WsDseDailyPrice.txn_date)))
                .filter(
                    WsDseDailyPrice.txn_scrip == ticker,
                    WsDseDailyPrice.txn_date >= cutoff_date,
                )
                .scalar()
            )

            # Count indicator days
            indicator_days = (
                session.query(func.count(distinct(Indicator.trading_date)))
                .filter(
                    Indicator.scrip == ticker,
                    Indicator.trading_date >= cutoff_date,
                    Indicator.status == "CALCULATED",
                )
                .scalar()
            )

            # Get latest dates
            latest_price_date = (
                session.query(func.max(WsDseDailyPrice.txn_date))
                .filter(WsDseDailyPrice.txn_scrip == ticker)
                .scalar()
            )

            latest_indicator_date = (
                session.query(func.max(Indicator.trading_date))
                .filter(Indicator.scrip == ticker, Indicator.status == "CALCULATED")
                .scalar()
            )

            # Calculate coverage
            coverage_pct = (indicator_days / price_days * 100) if price_days > 0 else 0

            return {
                "ticker": ticker,
                "lookback_days": lookback_days,
                "price_data_days": price_days,
                "indicator_days": indicator_days,
                "coverage_pct": round(coverage_pct, 2),
                "latest_price_date": latest_price_date.isoformat() if latest_price_date else None,
                "latest_indicator_date": (
                    latest_indicator_date.isoformat() if latest_indicator_date else None
                ),
            }

    except Exception as e:
        logger.error(f"Error getting ticker coverage for {ticker}: {e}", exc_info=True)
        return {
            "ticker": ticker,
            "status": "error",
            "message": str(e),
        }

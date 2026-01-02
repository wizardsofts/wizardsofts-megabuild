"""Celery tasks for daily analysis, outcome tracking, and reporting.

Tasks:
- daily_market_analysis: Analyze all 300+ stocks daily
- analyze_single_stock: Single stock analysis
- update_signal_outcomes: Batch update pending signal outcomes
- generate_backtest_report: Weekly performance report
- precompute_indicators: Hourly indicator pre-computation
- check_exit_signals: Daily exit condition check
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import distinct

from src.backtesting.analyzer import BacktestAnalyzer
from src.backtesting.outcome_tracker import SignalOutcomeTracker
from src.celery_app import app
from src.database.connection import get_db_context
from src.database.models import MarketRegime, WsDseDailyPrice
from src.fast_track.signal_engine import AdaptiveSignalEngine
from src.regime import MarketRegimeDetector
from src.tasks.exit_checker import ExitSignalChecker

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=300)
def analyze_single_stock(self, ticker: str) -> dict[str, Any]:
    """Celery task for single stock analysis.

    Runs indicator pipeline, generates signal, and tracks signal.

    Args:
        ticker: Stock symbol

    Returns:
        Dict with analysis results
    """
    try:
        logger.info(f"Starting analysis for {ticker}")

        with get_db_context() as session:
            engine = AdaptiveSignalEngine(session=session)
            signal = engine.generate_signal(ticker)

            if signal:
                logger.info(f"Signal generated for {ticker}: {signal.signal_type}")
                return {
                    "ticker": ticker,
                    "signal_type": signal.signal_type,
                    "confidence": signal.confidence,
                    "entry_price": signal.entry_price,
                    "target_price": signal.target_price,
                    "stop_loss": signal.stop_loss,
                    "status": "success",
                }
            else:
                logger.warning(f"No signal generated for {ticker}")
                return {
                    "ticker": ticker,
                    "status": "no_signal",
                    "reason": "Insufficient data or no signal criteria met",
                }

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}", exc_info=True)

        # Retry up to 3 times with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300 * (self.request.retries + 1)) from e
        else:
            return {
                "ticker": ticker,
                "status": "error",
                "error": str(e),
            }


@app.task(bind=True, default_retry_delay=600)
def daily_market_analysis(self) -> dict[str, Any]:
    """Daily task to analyze all 300+ stocks.

    Flow:
    1. Get all active tickers
    2. Run batch analysis (parallel)
    3. Generate report
    4. Send email notification

    Runs at 5:00 PM UTC daily.

    Returns:
        Dict with analysis statistics
    """
    try:
        logger.info("Starting daily market analysis")

        with get_db_context() as session:
            # Get all active tickers from GIBD
            result = session.query(distinct(WsDseDailyPrice.txn_scrip)).all()
            active_tickers = sorted([row[0] for row in result])

            if not active_tickers:
                logger.warning("No active tickers found in GIBD")
                return {
                    "status": "no_tickers",
                    "total_analyzed": 0,
                    "signals_generated": 0,
                }

            logger.info(f"Found {len(active_tickers)} active tickers in GIBD")

            # Queue individual stock analysis tasks
            results = []
            signal_count = 0

            for ticker in active_tickers:
                try:
                    result = analyze_single_stock.apply_async(
                        args=(ticker,),
                        queue="analysis",
                        expires=3600,
                    )
                    results.append(result)

                    # Check if signal was generated
                    try:
                        task_result = result.get(timeout=30)
                        if task_result.get("status") == "success":
                            signal_count += 1
                    except Exception:
                        pass

                except Exception as e:
                    logger.error(f"Error queuing analysis for {ticker}: {str(e)}")

            logger.info(f"Daily market analysis complete: {signal_count} signals generated")

            return {
                "status": "success",
                "total_analyzed": len(active_tickers),
                "signals_generated": signal_count,
                "timestamp": str(datetime.utcnow()),
            }

    except Exception as e:
        logger.error(f"Error in daily_market_analysis: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


@app.task(bind=True, max_retries=3, default_retry_delay=300)
def update_signal_outcomes(self) -> dict[str, Any]:
    """Daily task to update signal outcomes.

    Calls SignalOutcomeTracker.update_outcomes(lookback_days=7) to
    evaluate pending signals against actual price movements.

    Runs at 5:30 PM UTC daily.

    Returns:
        Dict with update statistics
    """
    try:
        logger.info("Starting signal outcome updates")

        tracker = SignalOutcomeTracker()
        stats = tracker.update_outcomes(lookback_days=7)

        logger.info(f"Outcome update complete: {stats}")

        return {
            "status": "success",
            **stats,
            "timestamp": str(datetime.utcnow()),
        }

    except Exception as e:
        logger.error(f"Error in update_signal_outcomes: {str(e)}", exc_info=True)

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300) from e
        else:
            return {
                "status": "error",
                "error": str(e),
            }


@app.task(bind=True, default_retry_delay=300)
def precompute_indicators(self) -> dict[str, Any]:
    """Hourly task to pre-compute indicators.

    Pre-computes indicators for all stocks and caches them
    for fast signal generation.

    Runs hourly during market hours (9 AM - 4 PM UTC).

    Returns:
        Dict with pre-computation statistics
    """
    try:
        logger.info("Starting indicator pre-computation")

        # Import here to avoid circular dependencies
        from src.fast_track.batch_calculator import BatchIndicatorCalculator

        with get_db_context() as session:
            # Get all active tickers from GIBD
            result = session.query(distinct(WsDseDailyPrice.txn_scrip)).all()
            active_tickers = sorted([row[0] for row in result])

            if not active_tickers:
                logger.warning("No active tickers found in GIBD for pre-computation")
                return {
                    "status": "no_tickers",
                    "indicators_computed": 0,
                }

            calculator = BatchIndicatorCalculator(session=session)
            results = calculator.batch_calculate_all(tickers=active_tickers)

            logger.info(f"Indicator pre-computation complete: {len(results)} stocks")

            return {
                "status": "success",
                "indicators_computed": len(results),
                "timestamp": str(datetime.utcnow()),
            }

    except Exception as e:
        logger.error(f"Error in precompute_indicators: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


@app.task(bind=True, default_retry_delay=600)
def generate_backtest_report(self) -> dict[str, Any]:
    """Weekly task to generate backtest report.

    Generates comprehensive performance report for all signals
    from the past week.

    Runs every Sunday at 9:00 AM UTC.

    Returns:
        Dict with report generation status
    """
    try:
        logger.info("Starting backtest report generation")

        # Calculate date range (last 7 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        analyzer = BacktestAnalyzer()
        analyzer.generate_report(start_date, end_date, format_type="markdown")

        logger.info("Backtest report generated successfully")

        # In a production system, you would:
        # 1. Save report to file system
        # 2. Send email notification
        # 3. Update dashboard

        return {
            "status": "success",
            "report_period": f"{start_date} to {end_date}",
            "timestamp": str(datetime.utcnow()),
        }

    except Exception as e:
        logger.error(f"Error in generate_backtest_report: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


@app.task(bind=True, default_retry_delay=300)
def check_exit_signals(self) -> dict[str, Any]:
    """Daily task to check all exit conditions.

    Monitors open positions and checks all 7 exit conditions:
    1. RSI reversal
    2. Partial profit
    3. Time stop
    4. Stop-loss hit
    5. Sector rotation
    6. Index breakdown
    7. Flat price

    Runs at 4:00 PM UTC daily (before market close).

    Returns:
        Dict with exit check statistics
    """
    try:
        logger.info("Starting exit signal check")

        with get_db_context() as session:
            checker = ExitSignalChecker(session=session)
            stats = checker.check_all_exits()

            logger.info(f"Exit signal check complete: {stats}")

            return {
                "status": "success",
                **stats,
                "timestamp": str(datetime.utcnow()),
            }

    except Exception as e:
        logger.error(f"Error in check_exit_signals: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


@app.task(bind=True, max_retries=3, default_retry_delay=300)
def track_market_regime(self) -> dict[str, Any]:
    """Daily task to detect and track market regime.

    Runs market regime detection using DSEX index data and stores
    the result for signal threshold adjustments.

    Phase 5 Optimization - EPIC 5.2: Market Regime Detection

    Runs at 5:00 PM UTC daily (after market close).

    Returns:
        Dict with regime detection results
    """
    try:
        logger.info("Starting market regime detection")

        with get_db_context() as session:
            # Fetch DSEX index data (200+ days for SMA calculation)
            dsex_data = (
                session.query(WsDseDailyPrice)
                .filter(WsDseDailyPrice.txn_scrip == "DSEX")
                .order_by(WsDseDailyPrice.txn_date.desc())
                .limit(250)
                .all()
            )

            if not dsex_data or len(dsex_data) < 200:
                logger.warning("Insufficient DSEX data for regime detection")
                return {
                    "status": "insufficient_data",
                    "regime": "sideways",
                    "confidence": 0.5,
                }

            # Convert to DataFrame (reverse for chronological order)
            dsex_data.reverse()
            import pandas as pd

            index_df = pd.DataFrame(
                {
                    "date": [row.txn_date for row in dsex_data],
                    "open": [float(row.txn_open) for row in dsex_data],
                    "high": [float(row.txn_high) for row in dsex_data],
                    "low": [float(row.txn_low) for row in dsex_data],
                    "close": [float(row.txn_close) for row in dsex_data],
                    "volume": [int(row.txn_volume) for row in dsex_data],
                }
            )

            # Detect regime
            detector = MarketRegimeDetector()
            regime = detector.detect_regime(index_df)

            # Store in database
            regime_record = MarketRegime(
                regime_date=regime.regime_date,
                regime_type=regime.regime_type.value,
                confidence=regime.confidence,
                trend_direction=regime.trend_direction.value,
                volatility_level=regime.volatility_level.value,
                index_price=regime.index_price,
                index_sma_200=regime.index_sma_200,
                atr_ratio=regime.atr_ratio,
                adx_value=regime.adx_value,
                breadth_ratio=regime.breadth_ratio,
            )

            # Check if record already exists for this date
            existing = (
                session.query(MarketRegime)
                .filter(MarketRegime.regime_date == regime.regime_date)
                .first()
            )

            if existing:
                # Update existing record
                existing.regime_type = regime.regime_type.value
                existing.confidence = regime.confidence
                existing.trend_direction = regime.trend_direction.value
                existing.volatility_level = regime.volatility_level.value
                existing.index_price = regime.index_price
                existing.index_sma_200 = regime.index_sma_200
                existing.atr_ratio = regime.atr_ratio
                existing.adx_value = regime.adx_value
                existing.breadth_ratio = regime.breadth_ratio
                logger.info(f"Updated existing regime record for {regime.regime_date}")
            else:
                session.add(regime_record)
                logger.info(f"Created new regime record for {regime.regime_date}")

            session.commit()

            logger.info(
                f"Market regime detected: {regime.regime_type.value} "
                f"(confidence: {regime.confidence:.2f})"
            )

            return {
                "status": "success",
                "regime": regime.regime_type.value,
                "confidence": regime.confidence,
                "trend": regime.trend_direction.value,
                "volatility": regime.volatility_level.value,
                "timestamp": str(datetime.utcnow()),
            }

    except Exception as e:
        logger.error(f"Error in track_market_regime: {str(e)}", exc_info=True)

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300) from e
        else:
            return {
                "status": "error",
                "error": str(e),
            }

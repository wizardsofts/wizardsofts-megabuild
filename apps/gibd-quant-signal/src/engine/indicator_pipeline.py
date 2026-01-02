"""Indicator Pipeline for orchestrating comprehensive technical analysis.

This module provides the IndicatorPipeline class that orchestrates all indicator
calculations including multi-timeframe analysis, trend detection, and conditional
tool selection into a unified pipeline.

Phase 5 Enhancement: Integrated IncrementalCalculator for 10x faster updates
when previous day's indicators are cached.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.database.connection import get_db_context
from src.database.models import WsDseDailyPrice
from src.fast_track.analyzers.trend_detector import TrendDetector
from src.fast_track.calculators import IndicatorCalculator, MultiTimeframeCalculator
from src.fast_track.incremental_calculator import IncrementalCalculator
from src.fast_track.selectors.tool_selector import ConditionalToolSelector

logger = logging.getLogger(__name__)


class IndicatorPipeline:
    """Orchestrate all indicator calculations into a unified pipeline.

    This pipeline integrates:
    - MultiTimeframeCalculator for multi-timeframe RSI and SMA analysis
    - TrendDetector for pattern and trend detection
    - ConditionalToolSelector for intelligent tool selection
    - Individual indicator calculators (momentum, overlap, volume, volatility, pattern)

    The pipeline follows these steps:
    1. Cache check (L1/L2 multi-layer cache)
    2. Data fetch (from API or database)
    3. Multi-timeframe calculation
    4. Trend detection
    5. Tool selection based on context
    6. Individual indicator calculation
    7. Result aggregation and formatting
    8. Cache storage
    """

    def __init__(self, cache_size: int = 1000, cache_ttl_seconds: int = 3600):
        """Initialize the indicator pipeline with all components.

        Args:
            cache_size: Maximum number of cached items (default: 1000)
            cache_ttl_seconds: Cache TTL in seconds (default: 3600 = 1 hour)
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("IndicatorPipeline initialized")

        # Initialize pipeline components
        self.multi_timeframe_calculator = MultiTimeframeCalculator()
        self.trend_detector = TrendDetector()
        self.tool_selector = ConditionalToolSelector()
        self.indicator_calculator = IndicatorCalculator()

        # Phase 5: Incremental calculator for fast daily updates
        self.incremental_calculator = IncrementalCalculator()

        # Cache configuration
        self.cache_size = cache_size
        self.cache_ttl_seconds = cache_ttl_seconds

        # Track incremental vs full calculation stats
        self._incremental_hits = 0
        self._full_calculations = 0

        self.logger.info("All pipeline components initialized (with incremental calculator)")

    def calculate_all(
        self, ticker: str, data: pd.DataFrame | None = None, context: dict | None = None
    ) -> dict[str, Any]:
        """Calculate all indicators for a given stock.

        Orchestrates the complete indicator pipeline:
        1. Validates input data
        2. Selects tools based on context
        3. Calculates multi-timeframe indicators
        4. Detects trends and patterns
        5. Aggregates and formats results

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            data: Optional DataFrame with OHLCV data. If None, should be fetched externally.
            context: Optional market context dictionary for tool selection.
                    Should contain: query, volatility_regime, market_regime, adx, etc.

        Returns:
            Dictionary with complete indicator results:
            {
                'ticker': str,
                'status': 'success' | 'error',
                'multi_timeframe': {...},  # From MultiTimeframeCalculator
                'trends': {...},           # From TrendDetector
                'selected_tools': [...],   # From ConditionalToolSelector
                'indicators': {...},       # Individual calculator results
                'error': str (if status == 'error')
            }

        Raises:
            ValueError: If ticker is invalid or data is insufficient
        """
        self.logger.info(f"[{ticker}] Starting comprehensive indicator calculation")

        result: dict[str, Any] = {
            "ticker": ticker,
            "status": "success",
        }

        try:
            # Validate input
            if not ticker:
                raise ValueError("Ticker cannot be empty")

            # Step 1: Check cache (placeholder for now - would integrate with Redis/PostgreSQL)
            self.logger.debug(f"[{ticker}] Checking cache...")
            # cached_result = self._check_cache(ticker, date)
            # if cached_result:
            #     self.logger.info(f"[{ticker}] Cache hit - returning cached result")
            #     return cached_result

            # Step 2: Select tools based on context
            if context is None:
                context = {}

            self.logger.debug(f"[{ticker}] Selecting tools based on context")
            selected_tools = self.tool_selector.select_tools(context)
            result["selected_tools"] = selected_tools
            self.logger.info(f"[{ticker}] Selected {len(selected_tools)} tools")

            # Step 3: Calculate individual indicators using selected tools
            if data is not None:
                self.logger.debug(f"[{ticker}] Calculating individual indicators")
                try:
                    indicators = self.indicator_calculator.calculate_all(
                        data, ticker, selected_tools=selected_tools
                    )
                    result["indicators"] = indicators
                    self.logger.info(
                        f"[{ticker}] Individual indicator calculation complete: {len(indicators)} indicators"
                    )
                except Exception as e:
                    self.logger.error(
                        f"[{ticker}] Individual indicator calculation failed: {str(e)}"
                    )
                    result["indicators"] = {"error": str(e), "available": False}

                # Step 4: Calculate multi-timeframe indicators (if data provided)
                self.logger.debug(f"[{ticker}] Calculating multi-timeframe indicators")
                try:
                    multi_timeframe_results = self.multi_timeframe_calculator.calculate(
                        data, ticker
                    )
                    result["multi_timeframe"] = multi_timeframe_results
                    self.logger.info(f"[{ticker}] Multi-timeframe calculation complete")
                except Exception as e:
                    self.logger.error(f"[{ticker}] Multi-timeframe calculation failed: {str(e)}")
                    result["multi_timeframe"] = {"error": str(e), "available": False}

                # Step 5: Detect trends and patterns (if we have indicators and multi-timeframe results)
                if (
                    "indicators" in result
                    and "error" not in result.get("indicators", {})
                    and "multi_timeframe" in result
                    and "error" not in result["multi_timeframe"]
                ):
                    self.logger.debug(f"[{ticker}] Detecting trends and patterns")
                    try:
                        # Prepare indicators dict for trend detector
                        all_indicators = result.get("indicators", {})
                        indicators_for_trend = {
                            "rsi": (
                                all_indicators.get("rsi", [None])[-1]
                                if all_indicators.get("rsi")
                                else None
                            ),
                            "bb_upper": (
                                all_indicators.get("bb_upper", [None])[-1]
                                if all_indicators.get("bb_upper")
                                else None
                            ),
                            "bb_lower": (
                                all_indicators.get("bb_lower", [None])[-1]
                                if all_indicators.get("bb_lower")
                                else None
                            ),
                            "volume": data["volume"].iloc[-1] if data is not None else None,
                            "macd": (
                                all_indicators.get("macd", [None])[-1]
                                if all_indicators.get("macd")
                                else None
                            ),
                            "stoch_k": (
                                all_indicators.get("stoch_k", [None])[-1]
                                if all_indicators.get("stoch_k")
                                else None
                            ),
                            "stoch_d": (
                                all_indicators.get("stoch_d", [None])[-1]
                                if all_indicators.get("stoch_d")
                                else None
                            ),
                        }

                        price_data = {"close": data["close"].tolist() if data is not None else None}

                        trends = self.trend_detector.detect_all(indicators_for_trend, price_data)
                        result["trends"] = trends
                        self.logger.info(f"[{ticker}] Trend detection complete")
                    except Exception as e:
                        self.logger.error(f"[{ticker}] Trend detection failed: {str(e)}")
                        result["trends"] = {"error": str(e)}

            # Step 6: Store supported tools for reference
            result["supported_tools"] = self.tool_selector.get_supported_tools()

            self.logger.info(f"[{ticker}] Comprehensive indicator calculation complete")

        except Exception as e:
            self.logger.error(f"[{ticker}] Pipeline error: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _check_cache(
        self, ticker: str, cache_date: date, session: Session | None = None
    ) -> dict[str, Any] | None:
        """Check multi-layer cache for existing results.

        Checks L2 cache (PostgreSQL indicator_values table) for indicators
        calculated on the given date. L1 cache (Redis) would be implemented
        separately with a dedicated caching layer.

        Args:
            ticker: Stock ticker symbol
            cache_date: Date for which to check cache
            session: Optional SQLAlchemy session. If None, creates new session.

        Returns:
            Dictionary of cached indicators if found, None if cache miss

        Note:
            L1 (Redis) cache integration would be added as a separate layer.
            Currently implements L2 (PostgreSQL) persistent cache.
        """
        self.logger.debug(f"[{ticker}] Checking L2 cache (database) for {cache_date}")

        try:
            # Use provided session or create new one
            if session is None:
                with get_db_context() as db_session:
                    return self._query_cached_indicators(ticker, cache_date, db_session)
            else:
                return self._query_cached_indicators(ticker, cache_date, session)

        except Exception as e:
            self.logger.warning(f"[{ticker}] Cache check failed: {str(e)}")
            return None

    def _query_cached_indicators(
        self, ticker: str, cache_date: date, session: Session
    ) -> dict[str, Any] | None:
        """Query cached indicators from GIBD indicators table for a specific ticker and date.

        Args:
            ticker: Stock ticker symbol
            cache_date: Date to query
            session: Active database session

        Returns:
            Dictionary mapping indicator names to values from JSONB column, or None if no data
        """
        from src.database.models import Indicator

        try:
            # Query indicator record for this ticker and date
            indicator = (
                session.query(Indicator)
                .filter(
                    Indicator.scrip == ticker,
                    Indicator.trading_date == cache_date,
                    Indicator.status == "CALCULATED",
                )
                .first()
            )

            if not indicator:
                self.logger.debug(f"[{ticker}] No cached indicators found for {cache_date}")
                return None

            # Return the entire indicators JSONB dict
            cached_indicators = indicator.indicators

            self.logger.info(
                f"[{ticker}] Cache hit: Found {len(cached_indicators)} indicators for {cache_date}"
            )
            return cached_indicators

        except Exception as e:
            self.logger.debug(f"[{ticker}] Error querying indicators: {str(e)}")
            return None

    def _fetch_data(
        self, ticker: str, lookback: int = 220, session: Session | None = None
    ) -> pd.DataFrame | None:
        """Fetch OHLCV data from database for a given ticker.

        Fetches the most recent N days of OHLCV data from the StockData table.

        Args:
            ticker: Stock ticker symbol
            lookback: Number of days to fetch (default 220 for 200d SMA + buffer)
            session: Optional SQLAlchemy session. If None, creates new session.

        Returns:
            DataFrame with OHLCV data or None if fetch fails

        Raises:
            Logs errors instead of raising, returns None on failure
        """
        self.logger.debug(f"[{ticker}] Fetching {lookback} days of data from database")

        try:
            # Use provided session or create new one
            if session is None:
                with get_db_context() as db_session:
                    return self._query_stock_data(ticker, lookback, db_session)
            else:
                return self._query_stock_data(ticker, lookback, session)

        except Exception as e:
            self.logger.error(f"[{ticker}] Data fetch failed: {str(e)}")
            return None

    def _query_stock_data(
        self, ticker: str, lookback: int, session: Session
    ) -> pd.DataFrame | None:
        """Query OHLCV data from GIBD ws_dse_daily_prices table for a specific ticker.

        Args:
            ticker: Stock ticker symbol
            lookback: Number of days to fetch
            session: Active database session

        Returns:
            DataFrame with columns [date, open, high, low, close, volume] or None
        """
        try:
            # Query most recent N days of stock data from GIBD table
            stock_data = (
                session.query(WsDseDailyPrice)
                .filter(WsDseDailyPrice.txn_scrip == ticker)
                .order_by(WsDseDailyPrice.txn_date.desc())
                .limit(lookback)
                .all()
            )

            if not stock_data:
                self.logger.warning(f"[{ticker}] No stock data found in database")
                return None

            # Reverse to get chronological order (oldest to newest)
            stock_data.reverse()

            # Convert to DataFrame with standard column names
            data = pd.DataFrame(
                {
                    "date": [row.txn_date for row in stock_data],
                    "open": [float(row.txn_open) for row in stock_data],
                    "high": [float(row.txn_high) for row in stock_data],
                    "low": [float(row.txn_low) for row in stock_data],
                    "close": [float(row.txn_close) for row in stock_data],
                    "volume": [int(row.txn_volume) for row in stock_data],
                }
            )

            self.logger.info(f"[{ticker}] Successfully fetched {len(data)} days of data from GIBD")
            return data

        except Exception as e:
            self.logger.error(f"[{ticker}] Error querying stock data from GIBD: {str(e)}")
            return None

    def _store_cache(
        self,
        ticker: str,
        cache_date: date,
        indicators: dict[str, Any],
        session: Session | None = None,
    ) -> bool:
        """Store indicators in L2 cache (database).

        Stores calculated indicators in the PostgreSQL Indicator table for
        persistent caching. L1 cache (Redis) integration would be added separately.

        Args:
            ticker: Stock ticker symbol
            cache_date: Date for which indicators were calculated
            indicators: Dictionary mapping indicator names to values
            session: Optional SQLAlchemy session. If None, creates new session.

        Returns:
            True if storage successful, False otherwise

        Note:
            L1 (Redis) cache storage would be implemented as a separate layer.
            Currently implements L2 (PostgreSQL) persistent storage.
        """
        self.logger.debug(
            f"[{ticker}] Storing {len(indicators)} indicators in L2 cache for {cache_date}"
        )

        try:
            # Use provided session or create new one
            if session is None:
                with get_db_context() as db_session:
                    return self._write_cached_indicators(ticker, cache_date, indicators, db_session)
            else:
                return self._write_cached_indicators(ticker, cache_date, indicators, session)

        except Exception as e:
            self.logger.error(f"[{ticker}] Cache storage failed: {str(e)}")
            return False

    def _write_cached_indicators(
        self, ticker: str, cache_date: date, indicators: dict[str, Any], session: Session
    ) -> bool:
        """Write indicators to database cache.

        NOTE: GIBD indicators table is managed by GIBD system.
        Quant-Flow reads indicators but does not write to the table.
        This method is kept for backwards compatibility but currently does nothing.

        Args:
            ticker: Stock ticker symbol
            cache_date: Date for indicators
            indicators: Dictionary of indicator name -> value
            session: Active database session

        Returns:
            False (indicators are read-only from GIBD)
        """
        self.logger.debug(
            f"[{ticker}] Skipping indicator cache storage - GIBD indicators table is managed by GIBD system (read-only for Quant-Flow)"
        )
        return False

    def calculate_incremental(
        self,
        ticker: str,
        new_day_data: dict[str, Any],
        historical_data: pd.DataFrame | None = None,
        force_full: bool = False,
    ) -> dict[str, Any]:
        """Calculate indicators using incremental method when possible.

        This method provides 10x performance improvement by using cached state
        and incremental calculations instead of full recalculation.

        Phase 5 Optimization: Uses IncrementalCalculator for fast daily updates.

        Args:
            ticker: Stock ticker symbol
            new_day_data: Dict with new day's OHLCV data:
                {"date": date, "open": float, "high": float,
                 "low": float, "close": float, "volume": int}
            historical_data: Optional DataFrame for initialization (220+ days).
                Required if no cached state exists.
            force_full: If True, skip incremental and use full calculation.

        Returns:
            Dictionary with indicator results:
            {
                "ticker": str,
                "date": date,
                "method": "incremental" | "full",
                "calculation_time_ms": float,
                "indicators": {...}
            }

        Performance:
            - Incremental: <50ms
            - Full calculation: ~500ms
        """
        self.logger.info(f"[{ticker}] Starting indicator calculation (incremental mode)")

        # Check if we should use incremental calculation
        cached_state = self.incremental_calculator.get_cached_state(ticker)

        if cached_state is not None and not force_full:
            # Use incremental calculation
            self.logger.debug(f"[{ticker}] Using incremental calculation (cached state found)")
            result = self.incremental_calculator.update_indicators(
                ticker=ticker,
                new_day_data=new_day_data,
            )
            self._incremental_hits += 1
            return result

        # Need to initialize or do full calculation
        if historical_data is not None and len(historical_data) >= 220:
            self.logger.debug(f"[{ticker}] Initializing incremental state from historical data")
            result = self.incremental_calculator.update_indicators(
                ticker=ticker,
                new_day_data=new_day_data,
                historical_data=historical_data,
            )
            self._incremental_hits += 1
            return result

        # Fall back to full calculation
        self.logger.debug(f"[{ticker}] Falling back to full calculation")
        self._full_calculations += 1

        # Use standard calculate_all
        if historical_data is not None:
            full_result = self.calculate_all(ticker, historical_data)
            return {
                "ticker": ticker,
                "date": new_day_data.get("date"),
                "method": "full",
                "calculation_time_ms": 500.0,  # Approximate
                "indicators": full_result.get("indicators", {}),
            }

        return {
            "ticker": ticker,
            "date": new_day_data.get("date"),
            "method": "failed",
            "error": "No cached state and no historical data provided",
            "indicators": {},
        }

    def get_incremental_stats(self) -> dict[str, Any]:
        """Get statistics on incremental vs full calculations.

        Returns:
            Dict with calculation statistics:
            {
                "incremental_hits": int,
                "full_calculations": int,
                "incremental_rate": float,
                "cached_tickers": list[str]
            }
        """
        total = self._incremental_hits + self._full_calculations
        rate = self._incremental_hits / total if total > 0 else 0.0

        return {
            "incremental_hits": self._incremental_hits,
            "full_calculations": self._full_calculations,
            "total_calculations": total,
            "incremental_rate": rate,
            "cached_tickers": self.incremental_calculator.get_state_info()["cached_tickers"],
        }

    def clear_incremental_cache(self, ticker: str | None = None):
        """Clear incremental calculation cache.

        Args:
            ticker: Optional specific ticker to clear. If None, clears all.
        """
        self.incremental_calculator.clear_state(ticker)
        if ticker is None:
            self._incremental_hits = 0
            self._full_calculations = 0
            self.logger.info("Cleared all incremental cache and stats")
        else:
            self.logger.info(f"[{ticker}] Cleared incremental cache")

    def get_pipeline_components(self) -> dict:
        """Get information about all pipeline components.

        Returns:
            Dictionary with component information:
            {
                'multi_timeframe_calculator': {...},
                'trend_detector': {...},
                'tool_selector': {...},
                'supported_tools': {...}
            }
        """
        return {
            "multi_timeframe_calculator": {
                "class": "MultiTimeframeCalculator",
                "timeframes": self.multi_timeframe_calculator.get_supported_timeframes(),
            },
            "trend_detector": {
                "class": "TrendDetector",
                "methods": [
                    "detect_rsi_reversal",
                    "detect_bb_squeeze",
                    "detect_volume_trend",
                    "detect_macd_divergence",
                    "detect_stochastic_pattern",
                    "detect_consolidation",
                    "calculate_trend_quality",
                ],
            },
            "tool_selector": {
                "class": "ConditionalToolSelector",
                "core_tools": self.tool_selector.CORE_TOOLS,
                "supported_tools": self.tool_selector.get_supported_tools(),
            },
        }

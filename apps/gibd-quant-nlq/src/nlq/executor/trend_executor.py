"""Trend query executor for natural language queries.

Handles queries like:
- "stocks with increasing RSI for last 5 days"
- "stocks with decreasing SMA_20 for 3 days"
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from src.nlq.executor.base import BaseExecutor
from src.nlq.types import ParsedQuery, QueryType, TrendDirection

logger = logging.getLogger(__name__)


class TrendExecutor(BaseExecutor):
    """Execute trend-based queries."""

    # Minimum percentage of days that must follow the trend
    TREND_THRESHOLD = 0.6  # 60% of days must be increasing/decreasing

    def can_execute(self, query: ParsedQuery) -> bool:
        """Check if this executor can handle the query."""
        return query.query_type == QueryType.TREND

    def execute(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Execute a trend query.

        Args:
            query: Parsed trend query.
            session: Database session.
            tickers: Optional list of tickers to search.
            limit: Maximum results to return.

        Returns:
            List of matching stocks with trend data.
        """
        from src.database.batch_queries import fetch_indicators_batch

        indicator_name = query.indicator
        days = query.lookback_days
        direction = query.trend_direction

        if not indicator_name or not direction:
            return []

        # Calculate date range (add buffer for potential missing days)
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 10)

        # Get all tickers if not specified
        if not tickers:
            tickers = self.get_all_tickers(session)

        # Handle price-based indicators (stored in prices table, not indicators)
        if indicator_name in ("volume", "close"):
            return self._execute_price_trend(
                query, session, tickers, start_date, end_date, days, direction, limit
            )

        # Fetch indicators in batch
        indicators_data = fetch_indicators_batch(tickers, start_date, end_date, session)

        results = []
        for ticker, records in indicators_data.items():
            if len(records) < days:
                continue

            # Get the most recent N days of data
            recent_records = sorted(records, key=lambda x: x["date"], reverse=True)[:days]
            recent_records = list(reversed(recent_records))  # Oldest first for trend calc

            # Extract indicator values
            values = []
            for record in recent_records:
                indicators = record.get("indicators", {})
                value = indicators.get(indicator_name)
                if value is not None:
                    values.append(float(value))

            if len(values) < days:
                continue

            # Check trend
            if self._check_trend(values, direction):
                trend_strength = self._calculate_trend_strength(values)
                results.append(
                    {
                        "ticker": ticker,
                        "indicator": indicator_name,
                        "values": values,
                        "trend": direction.value,
                        "days": days,
                        "trend_strength": trend_strength,
                        "start_value": values[0],
                        "end_value": values[-1],
                        "change_pct": (
                            ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                        ),
                    }
                )

        # Sort by trend strength (absolute value for consistent ranking)
        results.sort(key=lambda x: abs(x["trend_strength"]), reverse=True)
        return results[:limit]

    def _execute_price_trend(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str],
        start_date: date,
        end_date: date,
        days: int,
        direction: TrendDirection,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute price-based trend query (volume or close price).

        Args:
            query: Parsed query.
            session: Database session.
            tickers: List of tickers.
            start_date: Start date for data.
            end_date: End date for data.
            days: Number of lookback days.
            direction: Trend direction.
            limit: Maximum results.

        Returns:
            List of matching stocks with trend data.
        """
        from src.database.batch_queries import fetch_prices_batch

        indicator_name = query.indicator
        prices_data = fetch_prices_batch(tickers, start_date, end_date, session)

        results = []
        for ticker, records in prices_data.items():
            if len(records) < days:
                continue

            # Get the most recent N days
            recent_records = sorted(records, key=lambda x: x["date"], reverse=True)[:days]
            recent_records = list(reversed(recent_records))  # Oldest first

            # Extract values based on indicator type
            if indicator_name == "volume":
                values = [float(r["volume"]) for r in recent_records]
            else:  # close price
                values = [float(r["close"]) for r in recent_records]

            if self._check_trend(values, direction):
                trend_strength = self._calculate_trend_strength(values)
                results.append(
                    {
                        "ticker": ticker,
                        "indicator": indicator_name,
                        "values": values,
                        "trend": direction.value,
                        "days": days,
                        "trend_strength": trend_strength,
                        "start_value": values[0],
                        "end_value": values[-1],
                        "change_pct": (
                            ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                        ),
                    }
                )

        results.sort(key=lambda x: abs(x["trend_strength"]), reverse=True)
        return results[:limit]

    def _check_trend(self, values: list[float], direction: TrendDirection) -> bool:
        """Check if values follow the expected trend.

        Args:
            values: List of indicator values (oldest to newest).
            direction: Expected trend direction.

        Returns:
            True if values follow the trend.
        """
        if len(values) < 2:
            return False

        if direction == TrendDirection.INCREASING:
            # Count how many consecutive increases
            increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
            return increases >= len(values) * self.TREND_THRESHOLD

        elif direction == TrendDirection.DECREASING:
            # Count how many consecutive decreases
            decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])
            return decreases >= len(values) * self.TREND_THRESHOLD

        elif direction == TrendDirection.STABLE:
            # Check if values are within 5% range
            min_val, max_val = min(values), max(values)
            if min_val == 0:
                return False
            return (max_val - min_val) / min_val < 0.05

        return False

    def _calculate_trend_strength(self, values: list[float]) -> float:
        """Calculate trend strength as percentage change.

        Args:
            values: List of indicator values.

        Returns:
            Percentage change from first to last value.
        """
        if not values or values[0] == 0:
            return 0.0
        return (values[-1] - values[0]) / values[0]

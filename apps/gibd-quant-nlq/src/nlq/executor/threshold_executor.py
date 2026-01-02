"""Threshold query executor for natural language queries.

Handles queries like:
- "stocks with RSI above 70"
- "stocks with volume above average"
- "overbought stocks"
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from src.nlq.executor.base import BaseExecutor
from src.nlq.types import ComparisonOperator, ParsedQuery, QueryType

logger = logging.getLogger(__name__)


class ThresholdExecutor(BaseExecutor):
    """Execute threshold-based queries."""

    # Percentage threshold for "near" comparisons
    NEAR_THRESHOLD = 0.05  # Within 5%

    def can_execute(self, query: ParsedQuery) -> bool:
        """Check if this executor can handle the query."""
        return query.query_type == QueryType.THRESHOLD

    def execute(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Execute a threshold query.

        Args:
            query: Parsed threshold query.
            session: Database session.
            tickers: Optional list of tickers to search.
            limit: Maximum results to return.

        Returns:
            List of matching stocks with indicator values.
        """
        indicator_name = query.indicator
        operator = query.operator

        if not indicator_name or not operator:
            return []

        # Get all tickers if not specified
        if not tickers:
            tickers = self.get_all_tickers(session)

        # Handle "volume above average" queries
        if indicator_name == "volume" and query.threshold_is_average:
            return self._execute_volume_average_query(query, session, tickers, operator, limit)

        # Handle regular threshold queries
        if query.threshold_value is not None:
            return self._execute_indicator_threshold(
                query, session, tickers, indicator_name, operator, query.threshold_value, limit
            )

        return []

    def _execute_indicator_threshold(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str],
        indicator_name: str,
        operator: ComparisonOperator,
        threshold: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute threshold query for a specific indicator.

        Args:
            query: Parsed query.
            session: Database session.
            tickers: List of tickers.
            indicator_name: Normalized indicator name.
            operator: Comparison operator.
            threshold: Threshold value.
            limit: Maximum results.

        Returns:
            List of matching stocks.
        """
        from src.database.batch_queries import fetch_latest_indicators

        # Fetch latest indicators for all tickers
        indicators = fetch_latest_indicators(tickers, session)

        results = []
        for ticker, data in indicators.items():
            indicator_values = data.get("indicators", {})
            value = indicator_values.get(indicator_name)

            if value is None:
                continue

            value = float(value)

            if self._matches_threshold(value, operator, threshold):
                results.append(
                    {
                        "ticker": ticker,
                        "indicator": indicator_name,
                        "value": value,
                        "threshold": threshold,
                        "operator": operator.value,
                        "date": data.get("date"),
                        "distance": abs(value - threshold),
                        "distance_pct": (
                            abs(value - threshold) / threshold * 100 if threshold != 0 else 0
                        ),
                    }
                )

        # Sort by distance from threshold (closest first for NEAR, furthest for ABOVE/BELOW)
        if operator == ComparisonOperator.NEAR:
            results.sort(key=lambda x: x["distance"])
        elif operator == ComparisonOperator.ABOVE:
            results.sort(key=lambda x: x["value"], reverse=True)
        else:  # BELOW
            results.sort(key=lambda x: x["value"])

        return results[:limit]

    def _execute_volume_average_query(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str],
        operator: ComparisonOperator,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute volume above/below average query.

        Uses StockProfile.typical_volume for comparison, or calculates
        from historical data if not available.

        Args:
            query: Parsed query.
            session: Database session.
            tickers: List of tickers.
            operator: Comparison operator.
            limit: Maximum results.

        Returns:
            List of matching stocks.
        """
        from src.database.batch_queries import (
            fetch_latest_prices,
            fetch_prices_batch,
            fetch_profiles_batch,
        )

        # Get stock profiles for typical volume
        profiles = fetch_profiles_batch(tickers, session)

        # Get latest prices for current volume
        latest_prices = fetch_latest_prices(tickers, session)

        # For tickers without profiles, calculate average from historical data
        tickers_without_profile = [t for t in tickers if t not in profiles]
        historical_averages = {}

        if tickers_without_profile:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            historical_data = fetch_prices_batch(
                tickers_without_profile, start_date, end_date, session
            )

            for ticker, records in historical_data.items():
                if records:
                    volumes = [r["volume"] for r in records]
                    historical_averages[ticker] = sum(volumes) / len(volumes)

        results = []
        for ticker in tickers:
            if ticker not in latest_prices:
                continue

            current_volume = latest_prices[ticker]["volume"]

            # Get average volume (from profile or historical calculation)
            if ticker in profiles and profiles[ticker].get("typical_volume"):
                avg_volume = profiles[ticker]["typical_volume"]
            elif ticker in historical_averages:
                avg_volume = historical_averages[ticker]
            else:
                continue

            if avg_volume == 0:
                continue

            volume_ratio = current_volume / avg_volume

            # Check threshold
            matches = False
            if operator == ComparisonOperator.ABOVE:
                matches = volume_ratio > 1.0
            elif operator == ComparisonOperator.BELOW:
                matches = volume_ratio < 1.0
            elif operator == ComparisonOperator.NEAR:
                matches = abs(volume_ratio - 1.0) < self.NEAR_THRESHOLD

            if matches:
                results.append(
                    {
                        "ticker": ticker,
                        "indicator": "volume",
                        "value": current_volume,
                        "average": avg_volume,
                        "ratio": volume_ratio,
                        "operator": operator.value,
                        "date": latest_prices[ticker].get("date"),
                        "above_average_pct": (volume_ratio - 1.0) * 100,
                    }
                )

        # Sort by ratio (highest for ABOVE, lowest for BELOW)
        if operator == ComparisonOperator.ABOVE:
            results.sort(key=lambda x: x["ratio"], reverse=True)
        elif operator == ComparisonOperator.BELOW:
            results.sort(key=lambda x: x["ratio"])
        else:
            results.sort(key=lambda x: abs(x["ratio"] - 1.0))

        return results[:limit]

    def _matches_threshold(
        self, value: float, operator: ComparisonOperator, threshold: float
    ) -> bool:
        """Check if value matches the threshold condition.

        Args:
            value: Indicator value.
            operator: Comparison operator.
            threshold: Threshold value.

        Returns:
            True if value matches the condition.
        """
        if operator == ComparisonOperator.ABOVE:
            return value > threshold
        elif operator == ComparisonOperator.BELOW:
            return value < threshold
        elif operator == ComparisonOperator.EQUALS:
            return abs(value - threshold) < 0.001
        elif operator == ComparisonOperator.NEAR:
            if threshold == 0:
                return abs(value) < 0.001
            return abs(value - threshold) / abs(threshold) < self.NEAR_THRESHOLD
        return False

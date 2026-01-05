"""Comparison query executor for natural language queries.

Handles queries like:
- "stocks outperforming their sector"
- "stocks underperforming sector"
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from nlq.executor.base import BaseExecutor
from nlq.types import ParsedQuery, QueryType

logger = logging.getLogger(__name__)


class ComparisonExecutor(BaseExecutor):
    """Execute comparison-based queries (sector performance, etc.)."""

    # Threshold for outperforming/underperforming (percentage points)
    OUTPERFORM_THRESHOLD = 5.0  # 5% better than sector
    UNDERPERFORM_THRESHOLD = -5.0  # 5% worse than sector

    def can_execute(self, query: ParsedQuery) -> bool:
        """Check if this executor can handle the query."""
        return query.query_type == QueryType.COMPARISON

    def execute(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Execute a comparison query.

        Args:
            query: Parsed comparison query.
            session: Database session.
            tickers: Optional list of tickers to search.
            limit: Maximum results to return.

        Returns:
            List of matching stocks with comparison data.
        """
        target = query.comparison_target
        direction = query.comparison_direction

        if target == "sector":
            return self._execute_sector_comparison(query, session, tickers, direction, limit)

        return []

    def _execute_sector_comparison(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str] | None,
        direction: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute sector comparison query.

        Args:
            query: Parsed query.
            session: Database session.
            tickers: Optional list of tickers.
            direction: "outperforming" or "underperforming".
            limit: Maximum results.

        Returns:
            List of matching stocks with sector performance.
        """
        from database.batch_queries import fetch_prices_batch
        from sectors.manager import SectorManager

        # Get all tickers if not specified
        if not tickers:
            tickers = self.get_all_tickers(session)

        # Initialize sector manager
        sector_manager = SectorManager()

        # Get price data for performance calculation
        end_date = date.today()
        start_date = end_date - timedelta(days=10)  # Get last ~5 trading days

        prices_data = fetch_prices_batch(tickers, start_date, end_date, session)

        # Calculate performance for each stock
        stock_performance = {}
        for ticker, records in prices_data.items():
            if len(records) < 2:
                continue
            # Sort by date, get oldest and newest
            sorted_records = sorted(records, key=lambda x: x["date"])
            start_price = sorted_records[0]["close"]
            end_price = sorted_records[-1]["close"]
            if start_price > 0:
                performance = (end_price - start_price) / start_price * 100
                stock_performance[ticker] = performance

        # Calculate sector performance
        sector_performance = self._calculate_sector_performance(stock_performance, sector_manager)

        # Compare each stock to its sector
        results = []
        for ticker, performance in stock_performance.items():
            sector = sector_manager.get_sector(ticker)
            if not sector or sector not in sector_performance:
                continue

            sector_perf = sector_performance[sector]
            relative_strength = performance - sector_perf

            # Check if matches direction
            matches = False
            if direction == "outperforming":
                matches = relative_strength >= self.OUTPERFORM_THRESHOLD
            elif direction == "underperforming":
                matches = relative_strength <= self.UNDERPERFORM_THRESHOLD

            if matches:
                results.append(
                    {
                        "ticker": ticker,
                        "sector": sector,
                        "stock_performance": round(performance, 2),
                        "sector_performance": round(sector_perf, 2),
                        "relative_strength": round(relative_strength, 2),
                        "interpretation": direction,
                    }
                )

        # Sort by relative strength
        if direction == "outperforming":
            results.sort(key=lambda x: x["relative_strength"], reverse=True)
        else:
            results.sort(key=lambda x: x["relative_strength"])

        return results[:limit]

    def _calculate_sector_performance(
        self,
        stock_performance: dict[str, float],
        sector_manager,
    ) -> dict[str, float]:
        """Calculate average performance for each sector.

        Args:
            stock_performance: Dictionary of ticker -> performance %.
            sector_manager: SectorManager instance.

        Returns:
            Dictionary of sector -> average performance %.
        """
        sector_totals: dict[str, list[float]] = {}

        for ticker, performance in stock_performance.items():
            sector = sector_manager.get_sector(ticker)
            if sector:
                if sector not in sector_totals:
                    sector_totals[sector] = []
                sector_totals[sector].append(performance)

        return {sector: sum(perfs) / len(perfs) for sector, perfs in sector_totals.items() if perfs}

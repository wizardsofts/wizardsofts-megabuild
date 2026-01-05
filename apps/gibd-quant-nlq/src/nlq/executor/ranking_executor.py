"""Ranking query executor for natural language queries.

Handles queries like:
- "top 20 stocks by volume"
- "show 10 stocks with highest RSI"
- "stocks with lowest price"
- "show 10 Bank sector stocks with highest volume"
"""

import logging
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from nlq.executor.base import BaseExecutor
from nlq.types import ParsedQuery, QueryType, RankingOrder

logger = logging.getLogger(__name__)


class RankingExecutor(BaseExecutor):
    """Execute ranking-based queries."""

    def can_execute(self, query: ParsedQuery) -> bool:
        """Check if this executor can handle the query."""
        return query.query_type == QueryType.RANKING

    def execute(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Execute a ranking query.

        Args:
            query: Parsed ranking query.
            session: Database session.
            tickers: Optional list of tickers to search.
            limit: Maximum results to return (overridden by ranking_limit).

        Returns:
            List of stocks sorted by the indicator value.
        """
        indicator_name = query.indicator
        order = query.ranking_order or RankingOrder.HIGHEST
        result_limit = query.ranking_limit or limit

        if not indicator_name:
            return []

        # Get all tickers if not specified
        if not tickers:
            tickers = self.get_all_tickers(session)

        # Apply sector filter if specified
        if query.sector_filter:
            tickers = self._filter_by_sector(tickers, query.sector_filter)
            if not tickers:
                logger.warning(f"No tickers found for sector: {query.sector_filter}")
                return []

        # Handle price-based indicators (volume, close)
        if indicator_name in ("volume", "close"):
            return self._execute_price_ranking(
                query, session, tickers, indicator_name, order, result_limit
            )

        # Handle computed indicators (RSI, SMA, etc.)
        return self._execute_indicator_ranking(
            query, session, tickers, indicator_name, order, result_limit
        )

    def _filter_by_sector(self, tickers: list[str], sector_filter: str) -> list[str]:
        """Filter tickers by sector.

        Args:
            tickers: List of all tickers.
            sector_filter: Sector name to filter by (case-insensitive).

        Returns:
            List of tickers in the specified sector.
        """
        from sectors.manager import SectorManager

        manager = SectorManager()

        # Get all available sectors for partial matching
        all_sectors = manager.get_all_sectors()

        # Try exact match first (case-insensitive)
        matching_sector = None
        for sector in all_sectors:
            if sector.lower() == sector_filter.lower():
                matching_sector = sector
                break

        # If no exact match, try partial match
        if not matching_sector:
            for sector in all_sectors:
                if sector_filter.lower() in sector.lower():
                    matching_sector = sector
                    break

        if not matching_sector:
            logger.warning(
                f"Sector '{sector_filter}' not found. "
                f"Available sectors: {', '.join(sorted(all_sectors)[:10])}..."
            )
            return []

        # Get tickers for the matching sector
        sector_tickers = set(manager.get_sector_tickers(matching_sector))

        # Filter to only include tickers that are in both lists
        filtered = [t for t in tickers if t in sector_tickers]
        logger.info(
            f"Sector filter '{sector_filter}' matched '{matching_sector}' "
            f"with {len(filtered)} stocks"
        )

        return filtered

    def _get_latest_trading_date(self, session: Session) -> date | None:
        """Get the most recent trading date across all stocks.

        Args:
            session: Database session.

        Returns:
            The latest trading date, or None if no data.
        """
        from database.models import WsDseDailyPrice

        result = session.query(func.max(WsDseDailyPrice.txn_date)).scalar()
        return result

    def _execute_price_ranking(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str],
        indicator_name: str,
        order: RankingOrder,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute ranking query for price-based indicators.

        Args:
            query: Parsed query.
            session: Database session.
            tickers: List of tickers.
            indicator_name: Name of the indicator (volume or close).
            order: Ranking order (highest or lowest).
            limit: Maximum results.

        Returns:
            List of stocks sorted by the indicator value.
        """
        from database.models import WsDseDailyPrice

        # Get the latest trading date to ensure consistent, recent data
        latest_date = self._get_latest_trading_date(session)
        if not latest_date:
            return []

        # Query prices for the latest trading date only
        query_result = (
            session.query(WsDseDailyPrice)
            .filter(
                WsDseDailyPrice.txn_scrip.in_(tickers),
                WsDseDailyPrice.txn_date == latest_date,
            )
            .all()
        )

        results = []
        for record in query_result:
            if indicator_name == "volume":
                value = float(record.txn_volume) if record.txn_volume else 0
            else:  # close
                value = float(record.txn_close) if record.txn_close else 0

            if value > 0:
                results.append(
                    {
                        "ticker": record.txn_scrip,
                        "indicator": indicator_name,
                        "value": value,
                        "date": record.txn_date,
                    }
                )

        # Sort by value
        reverse = order == RankingOrder.HIGHEST
        results.sort(key=lambda x: x["value"], reverse=reverse)

        return results[:limit]

    def _execute_indicator_ranking(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str],
        indicator_name: str,
        order: RankingOrder,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute ranking query for computed indicators.

        Args:
            query: Parsed query.
            session: Database session.
            tickers: List of tickers.
            indicator_name: Name of the indicator (RSI_14, SMA_20, etc.).
            order: Ranking order (highest or lowest).
            limit: Maximum results.

        Returns:
            List of stocks sorted by the indicator value.
        """
        from database.batch_queries import fetch_latest_indicators

        latest_indicators = fetch_latest_indicators(tickers, session)

        results = []
        for ticker, data in latest_indicators.items():
            indicators = data.get("indicators", {})
            value = indicators.get(indicator_name)

            if value is not None:
                results.append(
                    {
                        "ticker": ticker,
                        "indicator": indicator_name,
                        "value": float(value),
                        "date": data.get("date"),
                    }
                )

        # Sort by value
        reverse = order == RankingOrder.HIGHEST
        results.sort(key=lambda x: x["value"], reverse=reverse)

        return results[:limit]

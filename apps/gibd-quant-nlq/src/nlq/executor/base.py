"""Base executor interface for NLQ queries."""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from nlq.types import ParsedQuery


class BaseExecutor(ABC):
    """Abstract base class for query executors."""

    @abstractmethod
    def can_execute(self, query: ParsedQuery) -> bool:
        """Check if this executor can handle the given query.

        Args:
            query: Parsed query to check.

        Returns:
            True if this executor can handle the query.
        """
        pass

    @abstractmethod
    def execute(
        self,
        query: ParsedQuery,
        session: Session,
        tickers: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Execute the query and return matching results.

        Args:
            query: Parsed query to execute.
            session: Database session.
            tickers: Optional list of tickers to search (default: all).
            limit: Maximum results to return.

        Returns:
            List of result dictionaries with ticker and query-specific data.
        """
        pass

    def get_all_tickers(self, session: Session) -> list[str]:
        """Get all available tickers from the database.

        Args:
            session: Database session.

        Returns:
            List of all ticker symbols.
        """
        from sqlalchemy import distinct

        from database.models import WsDseDailyPrice

        result = session.query(distinct(WsDseDailyPrice.txn_scrip)).all()
        return sorted([row[0] for row in result])

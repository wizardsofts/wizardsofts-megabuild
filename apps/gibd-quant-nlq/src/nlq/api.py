"""Public API for natural language queries.

This module provides the main entry point for external integrations
like chat interfaces.

Example usage:
    from nlq.api import NLQueryEngine

    engine = NLQueryEngine()

    # Simple query
    result = engine.query("stocks with RSI above 70")
    for stock in result.results:
        print(f"{stock['ticker']}: RSI = {stock['value']}")

    # Query with filters
    result = engine.query(
        "increasing SMA_20 for 5 days",
        tickers=["GP", "SQURPHARMA", "BATBC"],
        limit=10
    )
"""

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from nlq.executor.base import BaseExecutor
from nlq.executor.comparison_executor import ComparisonExecutor
from nlq.executor.ranking_executor import RankingExecutor
from nlq.executor.threshold_executor import ThresholdExecutor
from nlq.executor.trend_executor import TrendExecutor
from nlq.parser.pattern_parser import PatternParser
from nlq.types import ParsedQuery, QueryResult, QueryType

logger = logging.getLogger(__name__)


class NLQueryEngine:
    """Main entry point for natural language queries.

    This class provides a unified interface for parsing and executing
    natural language queries against the quant-flow database.

    Attributes:
        pattern_parser: Pattern-based query parser.
        llm_parser: Optional LLM-based parser for complex queries.
        executors: List of query executors.
        llm_confidence_threshold: Minimum confidence to skip LLM fallback.
    """

    # Default confidence threshold - if pattern match confidence is below this,
    # try LLM fallback (if enabled) for potentially better interpretation
    DEFAULT_LLM_CONFIDENCE_THRESHOLD = 0.8

    def __init__(
        self,
        enable_llm: bool = False,
        llm_api_key: str | None = None,
        llm_confidence_threshold: float = DEFAULT_LLM_CONFIDENCE_THRESHOLD,
    ):
        """Initialize the query engine.

        Args:
            enable_llm: Enable LLM fallback for complex queries.
            llm_api_key: OpenAI API key (or from env OPENAI_API_KEY).
            llm_confidence_threshold: Minimum pattern confidence to skip LLM.
                If pattern confidence < threshold and LLM is enabled,
                LLM will be used to try to get a better interpretation.
        """
        self.pattern_parser = PatternParser()
        self.llm_parser = None
        self.llm_confidence_threshold = llm_confidence_threshold

        if enable_llm:
            try:
                from nlq.parser.llm_parser import LLMParser

                self.llm_parser = LLMParser(api_key=llm_api_key)
            except ImportError:
                logger.warning("LLM parser not available, using pattern matching only")

        # Initialize executors
        self.executors: list[BaseExecutor] = [
            TrendExecutor(),
            ThresholdExecutor(),
            ComparisonExecutor(),
            RankingExecutor(),
        ]

    def query(
        self,
        query_text: str,
        tickers: list[str] | None = None,
        limit: int = 50,
        session: Session | None = None,
    ) -> QueryResult:
        """Execute a natural language query.

        Args:
            query_text: Natural language query string.
            tickers: Optional list of tickers to search (default: all).
            limit: Maximum results to return.
            session: Optional database session.

        Returns:
            QueryResult with matching stocks and details.
        """
        start_time = time.time()

        # Step 1: Parse the query
        parsed = self.pattern_parser.parse(query_text)

        # Fallback to LLM if:
        # - Pattern matching failed completely (UNKNOWN), or
        # - Pattern confidence is below threshold (e.g., unknown indicator)
        should_try_llm = (
            self.llm_parser
            and self.llm_parser.enabled
            and (
                parsed.query_type == QueryType.UNKNOWN
                or parsed.confidence < self.llm_confidence_threshold
            )
        )

        if should_try_llm:
            try:
                llm_parsed = self.llm_parser.parse(query_text)
                # Only use LLM result if it's valid and better than pattern result
                if (
                    llm_parsed
                    and llm_parsed.query_type != QueryType.UNKNOWN
                    and (
                        parsed.query_type == QueryType.UNKNOWN
                        or llm_parsed.confidence > parsed.confidence
                    )
                ):
                    logger.info(
                        f"Using LLM parse (confidence={llm_parsed.confidence:.2f}) "
                        f"over pattern (confidence={parsed.confidence:.2f})"
                    )
                    parsed = llm_parsed
            except Exception as e:
                logger.warning(f"LLM parsing failed: {e}")

        if parsed.query_type == QueryType.UNKNOWN:
            return QueryResult(
                query=parsed,
                matching_tickers=[],
                results=[],
                total_scanned=0,
                execution_time_ms=0,
                error=self._get_unknown_query_error(query_text),
            )

        # Step 2: Execute the query
        from database.connection import get_db_context

        own_session = session is None
        try:
            if own_session:
                with get_db_context() as sess:
                    results = self._execute(parsed, sess, tickers, limit)
                    total_scanned = self._count_tickers(sess, tickers)
            else:
                results = self._execute(parsed, session, tickers, limit)
                total_scanned = self._count_tickers(session, tickers)

            execution_time = (time.time() - start_time) * 1000

            return QueryResult(
                query=parsed,
                matching_tickers=[r["ticker"] for r in results],
                results=results,
                total_scanned=total_scanned,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                query=parsed,
                matching_tickers=[],
                results=[],
                total_scanned=0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )

    def parse(self, query_text: str) -> ParsedQuery:
        """Parse a query without executing it.

        Useful for debugging and testing the parser.

        Args:
            query_text: Natural language query string.

        Returns:
            ParsedQuery object.
        """
        parsed = self.pattern_parser.parse(query_text)

        # Fallback to LLM if pattern confidence is low
        should_try_llm = (
            self.llm_parser
            and self.llm_parser.enabled
            and (
                parsed.query_type == QueryType.UNKNOWN
                or parsed.confidence < self.llm_confidence_threshold
            )
        )

        if should_try_llm:
            try:
                llm_parsed = self.llm_parser.parse(query_text)
                if (
                    llm_parsed
                    and llm_parsed.query_type != QueryType.UNKNOWN
                    and (
                        parsed.query_type == QueryType.UNKNOWN
                        or llm_parsed.confidence > parsed.confidence
                    )
                ):
                    return llm_parsed
            except Exception as e:
                logger.warning(f"LLM parsing failed: {e}")

        return parsed

    def get_supported_queries(self) -> list[str]:
        """Return list of example supported queries.

        Returns:
            List of example query strings.
        """
        return self.pattern_parser.get_supported_patterns()

    def get_help_text(self) -> str:
        """Get formatted help text for users.

        Returns:
            Multi-line help string.
        """
        lines = [
            "Supported query types:",
            "",
            "TREND QUERIES (indicator changes over time):",
            '  "stocks with increasing RSI for 5 days"',
            '  "decreasing SMA_20 for last 3 days"',
            '  "increasing volume"',
            "",
            "THRESHOLD QUERIES (indicator above/below value):",
            '  "stocks with RSI above 70"',
            '  "RSI below 30"',
            '  "volume above average"',
            '  "overbought stocks"',
            '  "oversold stocks"',
            "",
            "COMPARISON QUERIES (relative performance):",
            '  "stocks outperforming their sector"',
            '  "stocks underperforming sector"',
            "",
            "TIPS:",
            "  - Indicator names: RSI, SMA_20, SMA_50, MACD, ADX, volume",
            "  - Days default to 5 if not specified",
            "  - Use 'stocks with' prefix or just the condition",
        ]
        return "\n".join(lines)

    def _execute(
        self,
        parsed: ParsedQuery,
        session: Session,
        tickers: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find and run appropriate executor.

        Args:
            parsed: Parsed query.
            session: Database session.
            tickers: Optional ticker filter.
            limit: Maximum results.

        Returns:
            List of result dictionaries.
        """
        for executor in self.executors:
            if executor.can_execute(parsed):
                return executor.execute(parsed, session, tickers, limit)
        return []

    def _count_tickers(
        self,
        session: Session,
        tickers: list[str] | None,
    ) -> int:
        """Count total tickers that were scanned.

        Args:
            session: Database session.
            tickers: Optional ticker filter.

        Returns:
            Number of tickers scanned.
        """
        if tickers:
            return len(tickers)

        from sqlalchemy import func

        from database.models import WsDseDailyPrice

        result = session.query(func.count(func.distinct(WsDseDailyPrice.txn_scrip))).scalar()
        return result or 0

    def _get_unknown_query_error(self, query_text: str) -> str:
        """Generate helpful error message for unknown queries.

        Args:
            query_text: Original query string.

        Returns:
            Error message with suggestions.
        """
        return (
            f"Could not understand query: '{query_text}'\n\n"
            "Try one of these formats:\n"
            "  - 'stocks with RSI above 70'\n"
            "  - 'increasing SMA_20 for 5 days'\n"
            "  - 'stocks outperforming sector'\n"
            "  - 'volume above average'\n\n"
            "Use 'help' for more examples."
        )

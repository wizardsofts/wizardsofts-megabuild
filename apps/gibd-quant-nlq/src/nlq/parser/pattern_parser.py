"""Pattern-based parser for natural language queries.

Uses regex patterns to parse common query structures into ParsedQuery objects.
"""

import re
from typing import Any

from src.nlq.types import (
    ComparisonOperator,
    ParsedQuery,
    QueryType,
    RankingOrder,
    TrendDirection,
    is_known_indicator,
    normalize_indicator,
)


class PatternParser:
    """Parse natural language queries using regex patterns."""

    # Words to skip before indicator names (common modifiers that aren't indicators)
    SKIP_WORDS = {"average", "avg", "mean", "typical", "normal", "daily", "weekly", "monthly"}

    # Pattern definitions with named groups
    PATTERNS: list[tuple[str, QueryType, dict[str, Any]]] = [
        # Trend patterns: "stocks with increasing RSI for last 5 days"
        # Also handles: "increasing average SMA" by capturing last indicator-like word
        (
            r"(?:stocks?\s+with\s+)?(increasing|rising|growing|going\s+up)\s+"
            r"(?:(?:average|avg|mean|typical|normal|daily|weekly|monthly)\s+)?"
            r"(\w+(?:_\d+)?)\s+(?:for\s+)?(?:last\s+)?(\d+)\s+days?",
            QueryType.TREND,
            {"direction": TrendDirection.INCREASING, "groups": ["_", "indicator", "days"]},
        ),
        (
            r"(?:stocks?\s+with\s+)?(decreasing|falling|declining|going\s+down)\s+"
            r"(?:(?:average|avg|mean|typical|normal|daily|weekly|monthly)\s+)?"
            r"(\w+(?:_\d+)?)\s+(?:for\s+)?(?:last\s+)?(\d+)\s+days?",
            QueryType.TREND,
            {"direction": TrendDirection.DECREASING, "groups": ["_", "indicator", "days"]},
        ),
        # Trend without explicit days: "stocks with increasing RSI"
        (
            r"(?:stocks?\s+with\s+)?(increasing|rising|growing)\s+"
            r"(?:(?:average|avg|mean|typical|normal|daily|weekly|monthly)\s+)?"
            r"(\w+(?:_\d+)?)",
            QueryType.TREND,
            {
                "direction": TrendDirection.INCREASING,
                "groups": ["_", "indicator"],
                "default_days": 5,
            },
        ),
        (
            r"(?:stocks?\s+with\s+)?(decreasing|falling|declining)\s+"
            r"(?:(?:average|avg|mean|typical|normal|daily|weekly|monthly)\s+)?"
            r"(\w+(?:_\d+)?)",
            QueryType.TREND,
            {
                "direction": TrendDirection.DECREASING,
                "groups": ["_", "indicator"],
                "default_days": 5,
            },
        ),
        # Threshold patterns: "stocks with RSI above 70"
        (
            r"(?:stocks?\s+with\s+)?(\w+(?:_\d+)?)\s+(above|over|greater\s+than|>)\s+([\d.]+)",
            QueryType.THRESHOLD,
            {"operator": ComparisonOperator.ABOVE, "groups": ["indicator", "_", "value"]},
        ),
        (
            r"(?:stocks?\s+with\s+)?(\w+(?:_\d+)?)\s+(below|under|less\s+than|<)\s+([\d.]+)",
            QueryType.THRESHOLD,
            {"operator": ComparisonOperator.BELOW, "groups": ["indicator", "_", "value"]},
        ),
        (
            r"(?:stocks?\s+with\s+)?(\w+(?:_\d+)?)\s+(near|around|close\s+to|~)\s+([\d.]+)",
            QueryType.THRESHOLD,
            {"operator": ComparisonOperator.NEAR, "groups": ["indicator", "_", "value"]},
        ),
        # Volume above average: "stocks with volume above average"
        (
            r"(?:stocks?\s+with\s+)?volume\s+(above|higher\s+than|over)\s+average"
            r"(?:\s+(?:in\s+)?(?:last\s+)?(\d+)\s+days?)?",
            QueryType.THRESHOLD,
            {
                "operator": ComparisonOperator.ABOVE,
                "indicator": "volume",
                "is_average": True,
                "groups": ["_", "days"],
            },
        ),
        (
            r"(?:stocks?\s+with\s+)?volume\s+(below|lower\s+than|under)\s+average",
            QueryType.THRESHOLD,
            {
                "operator": ComparisonOperator.BELOW,
                "indicator": "volume",
                "is_average": True,
                "groups": ["_"],
            },
        ),
        # High/low volume: "high volume stocks"
        (
            r"high\s+volume\s+stocks?",
            QueryType.THRESHOLD,
            {
                "operator": ComparisonOperator.ABOVE,
                "indicator": "volume",
                "is_average": True,
                "groups": [],
            },
        ),
        (
            r"low\s+volume\s+stocks?",
            QueryType.THRESHOLD,
            {
                "operator": ComparisonOperator.BELOW,
                "indicator": "volume",
                "is_average": True,
                "groups": [],
            },
        ),
        # Comparison patterns: "stocks outperforming their sector"
        (
            r"(?:stocks?\s+)?(outperforming|beating|ahead\s+of)\s+(?:their\s+)?sector",
            QueryType.COMPARISON,
            {"target": "sector", "direction": "outperforming", "groups": ["_"]},
        ),
        (
            r"(?:stocks?\s+)?(underperforming|lagging|behind)\s+(?:their\s+)?sector",
            QueryType.COMPARISON,
            {"target": "sector", "direction": "underperforming", "groups": ["_"]},
        ),
        # Support/resistance patterns: "stocks near support"
        (
            r"(?:stocks?\s+)?(?:where\s+)?price\s+(?:is\s+)?(?:near|at|close\s+to)\s+support",
            QueryType.SUPPORT_RESISTANCE,
            {"level": "support", "groups": []},
        ),
        (
            r"(?:stocks?\s+)?(?:where\s+)?price\s+(?:is\s+)?(?:near|at|close\s+to)\s+resistance",
            QueryType.SUPPORT_RESISTANCE,
            {"level": "resistance", "groups": []},
        ),
        # MACD crossover patterns
        (
            r"(?:stocks?\s+with\s+)?macd\s+(bullish|positive)\s+crossover",
            QueryType.CROSSOVER,
            {"indicator": "MACD", "direction": "bullish", "groups": ["_"]},
        ),
        (
            r"(?:stocks?\s+with\s+)?macd\s+(bearish|negative)\s+crossover",
            QueryType.CROSSOVER,
            {"indicator": "MACD", "direction": "bearish", "groups": ["_"]},
        ),
        # Overbought/oversold shortcuts
        (
            r"overbought\s+stocks?",
            QueryType.THRESHOLD,
            {
                "operator": ComparisonOperator.ABOVE,
                "indicator": "RSI_14",
                "value": 70.0,
                "groups": [],
            },
        ),
        (
            r"oversold\s+stocks?",
            QueryType.THRESHOLD,
            {
                "operator": ComparisonOperator.BELOW,
                "indicator": "RSI_14",
                "value": 30.0,
                "groups": [],
            },
        ),
        # Ranking patterns: "top 20 stocks by volume", "show 10 stocks with highest RSI"
        # With optional sector filter: "show 10 Bank sector stocks with highest volume"
        (
            r"(?:show\s+)?(?:top\s+)?(\d+)\s+(\w+)\s+(?:sector\s+)?stocks?\s+"
            r"(?:with\s+)?(?:the\s+)?(highest|largest|biggest|most|lowest|smallest|least)\s+"
            r"(?:average\s+)?(\w+(?:_\d+)?)",
            QueryType.RANKING,
            {"groups": ["limit", "sector", "order", "indicator"]},
        ),
        (
            r"(?:show\s+)?(?:top\s+)?(\d+)\s+stocks?\s+(?:with\s+)?(?:the\s+)?"
            r"(highest|largest|biggest|most|lowest|smallest|least)\s+"
            r"(?:average\s+)?(\w+(?:_\d+)?)",
            QueryType.RANKING,
            {"groups": ["limit", "order", "indicator"]},
        ),
        (
            r"(?:show\s+)?stocks?\s+(?:with\s+)?(?:the\s+)?"
            r"(highest|largest|biggest|most|lowest|smallest|least)\s+"
            r"(?:average\s+)?(\w+(?:_\d+)?)",
            QueryType.RANKING,
            {"groups": ["order", "indicator"], "default_limit": 20},
        ),
        (
            r"(?:show\s+)?(?:top\s+)?(\d+)\s+(?:by\s+)?(\w+(?:_\d+)?)",
            QueryType.RANKING,
            {"groups": ["limit", "indicator"], "order": RankingOrder.HIGHEST},
        ),
    ]

    def __init__(self):
        """Initialize parser with compiled patterns."""
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), query_type, config)
            for pattern, query_type, config in self.PATTERNS
        ]

    def parse(self, query: str) -> ParsedQuery:
        """Parse a natural language query into a structured ParsedQuery.

        Args:
            query: Natural language query string.

        Returns:
            ParsedQuery object with extracted information.
        """
        query = query.strip()

        for pattern, query_type, config in self._compiled_patterns:
            match = pattern.search(query)
            if match:
                return self._build_parsed_query(query, match, query_type, config)

        # No pattern matched
        return ParsedQuery(
            original_query=query,
            query_type=QueryType.UNKNOWN,
            parsed_by="pattern",
            confidence=0.0,
        )

    def _build_parsed_query(
        self,
        original_query: str,
        match: re.Match,
        query_type: QueryType,
        config: dict[str, Any],
    ) -> ParsedQuery:
        """Build ParsedQuery from regex match and config.

        Args:
            original_query: Original query string.
            match: Regex match object.
            query_type: Type of query.
            config: Pattern configuration.

        Returns:
            ParsedQuery with extracted values.
        """
        groups = match.groups()
        group_names = config.get("groups", [])

        # Extract values from groups
        extracted = {}
        for i, name in enumerate(group_names):
            if i < len(groups) and name != "_":
                extracted[name] = groups[i]

        # Build the ParsedQuery
        parsed = ParsedQuery(
            original_query=original_query,
            query_type=query_type,
            parsed_by="pattern",
            confidence=1.0,
        )

        # Handle by query type
        if query_type == QueryType.TREND:
            parsed.trend_direction = config.get("direction")
            indicator_raw = extracted.get("indicator", "")
            parsed.indicator_raw = indicator_raw
            parsed.indicator = normalize_indicator(indicator_raw)
            days = extracted.get("days")
            parsed.lookback_days = int(days) if days else config.get("default_days", 5)

        elif query_type == QueryType.THRESHOLD:
            parsed.operator = config.get("operator")

            # Handle indicator
            indicator_raw = config.get("indicator") or extracted.get("indicator", "")
            parsed.indicator_raw = indicator_raw
            parsed.indicator = normalize_indicator(indicator_raw)

            # Handle threshold value
            if config.get("is_average"):
                parsed.threshold_is_average = True
                days = extracted.get("days")
                if days:
                    parsed.lookback_days = int(days)
            elif "value" in config:
                parsed.threshold_value = float(config["value"])
            elif "value" in extracted and extracted["value"]:
                parsed.threshold_value = float(extracted["value"])

        elif query_type == QueryType.COMPARISON:
            parsed.comparison_target = config.get("target")
            parsed.comparison_direction = config.get("direction")

        elif query_type == QueryType.SUPPORT_RESISTANCE:
            parsed.extra["level"] = config.get("level")

        elif query_type == QueryType.CROSSOVER:
            parsed.indicator = config.get("indicator", "MACD")
            parsed.extra["crossover_direction"] = config.get("direction")

        elif query_type == QueryType.RANKING:
            # Handle indicator
            indicator_raw = extracted.get("indicator", "")
            parsed.indicator_raw = indicator_raw
            parsed.indicator = normalize_indicator(indicator_raw)

            # Handle limit
            limit = extracted.get("limit")
            if limit:
                parsed.ranking_limit = int(limit)
            else:
                parsed.ranking_limit = config.get("default_limit", 20)

            # Handle order (highest/lowest)
            order = config.get("order") or extracted.get("order", "")
            if isinstance(order, RankingOrder):
                parsed.ranking_order = order
            elif order.lower() in ("highest", "largest", "biggest", "most"):
                parsed.ranking_order = RankingOrder.HIGHEST
            elif order.lower() in ("lowest", "smallest", "least"):
                parsed.ranking_order = RankingOrder.LOWEST
            else:
                parsed.ranking_order = RankingOrder.HIGHEST  # Default

            # Handle sector filter
            sector = extracted.get("sector")
            if sector:
                parsed.sector_filter = sector

        # Adjust confidence based on whether indicator is known
        # Queries with unknown indicators get partial confidence (0.5)
        # to potentially trigger LLM fallback for better interpretation
        if parsed.indicator and not is_known_indicator(parsed.indicator):
            parsed.confidence = 0.5

        return parsed

    def get_supported_patterns(self) -> list[str]:
        """Return list of example queries that this parser supports.

        Returns:
            List of example query strings.
        """
        return [
            # Trend queries
            "stocks with increasing RSI for 5 days",
            "stocks with decreasing SMA_20 for 3 days",
            "increasing volume for last 5 days",
            "falling MACD",
            # Threshold queries
            "stocks with RSI above 70",
            "RSI below 30",
            "stocks with volume above average",
            "high volume stocks",
            "overbought stocks",
            "oversold stocks",
            # Comparison queries
            "stocks outperforming their sector",
            "stocks underperforming sector",
            # Support/resistance queries
            "stocks where price is near support",
            "price near resistance",
            # Crossover queries
            "stocks with MACD bullish crossover",
            "MACD bearish crossover",
        ]

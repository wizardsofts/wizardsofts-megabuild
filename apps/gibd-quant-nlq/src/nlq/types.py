"""Type definitions for natural language queries."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QueryType(Enum):
    """Types of queries supported by the NLQ system."""

    TREND = "trend"  # e.g., "increasing RSI for 5 days"
    THRESHOLD = "threshold"  # e.g., "RSI above 70"
    COMPARISON = "comparison"  # e.g., "outperforming sector"
    CROSSOVER = "crossover"  # e.g., "MACD bullish crossover"
    SUPPORT_RESISTANCE = "sr"  # e.g., "price near support"
    RANKING = "ranking"  # e.g., "top 20 stocks by volume"
    UNKNOWN = "unknown"


class RankingOrder(Enum):
    """Order for ranking queries."""

    HIGHEST = "highest"
    LOWEST = "lowest"


class TrendDirection(Enum):
    """Direction of trend for trend queries."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class ComparisonOperator(Enum):
    """Comparison operators for threshold queries."""

    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    NEAR = "near"


# Mapping from user-friendly indicator names to database indicator names
INDICATOR_MAP: dict[str, str] = {
    # RSI variants
    "rsi": "RSI_14",
    "rsi14": "RSI_14",
    "rsi_14": "RSI_14",
    # SMA variants
    "sma": "SMA_20",
    "sma20": "SMA_20",
    "sma_20": "SMA_20",
    "sma50": "SMA_50",
    "sma_50": "SMA_50",
    "sma200": "SMA_200",
    "sma_200": "SMA_200",
    # MACD variants
    "macd": "MACD_histogram_12_26_9",
    "macd_histogram": "MACD_histogram_12_26_9",
    "macd_line": "MACD_line_12_26_9",
    "macd_signal": "MACD_signal_12_26_9",
    # ADX
    "adx": "ADX_14",
    "adx14": "ADX_14",
    "adx_14": "ADX_14",
    # ATR
    "atr": "ATR_14",
    "atr14": "ATR_14",
    "atr_14": "ATR_14",
    # Volume (special handling)
    "volume": "volume",
    "vol": "volume",
    # Price
    "price": "close",
    "close": "close",
}

# Set of all known/valid indicator names (normalized database format)
KNOWN_INDICATORS: set[str] = {
    "RSI_14",
    "SMA_20",
    "SMA_50",
    "SMA_200",
    "MACD_histogram_12_26_9",
    "MACD_line_12_26_9",
    "MACD_signal_12_26_9",
    "ADX_14",
    "ATR_14",
    "volume",
    "close",
}


def normalize_indicator(name: str) -> str:
    """Normalize indicator name to database format.

    Args:
        name: User-provided indicator name (e.g., "RSI", "sma20").

    Returns:
        Normalized indicator name (e.g., "RSI_14", "SMA_20").
    """
    normalized = name.lower().strip().replace(" ", "_").replace("-", "_")
    return INDICATOR_MAP.get(normalized, name.upper())


def is_known_indicator(indicator: str | None) -> bool:
    """Check if an indicator is a known/valid indicator.

    Args:
        indicator: Normalized indicator name to check.

    Returns:
        True if the indicator is known, False otherwise.
    """
    if indicator is None:
        return False
    return indicator in KNOWN_INDICATORS


@dataclass
class ParsedQuery:
    """Structured representation of a natural language query."""

    original_query: str
    query_type: QueryType = QueryType.UNKNOWN

    # Indicator info
    indicator: str | None = None  # Normalized indicator name (e.g., "RSI_14")
    indicator_raw: str | None = None  # Original indicator text from query

    # Threshold query fields
    operator: ComparisonOperator | None = None
    threshold_value: float | None = None
    threshold_is_average: bool = False  # True for "volume above average"

    # Trend query fields
    trend_direction: TrendDirection | None = None
    lookback_days: int = 5

    # Comparison query fields
    comparison_target: str | None = None  # "sector", "average", or ticker
    comparison_direction: str | None = None  # "outperforming", "underperforming"

    # Ranking query fields
    ranking_order: "RankingOrder | None" = None  # highest or lowest
    ranking_limit: int | None = None  # Number of results to return (e.g., "top 20")

    # Metadata
    ticker_filter: str | None = None  # Specific ticker if mentioned
    sector_filter: str | None = None  # Sector filter (e.g., "Bank", "Pharmaceuticals")
    confidence: float = 1.0  # Parser confidence (0-1)
    parsed_by: str = "unknown"  # "pattern" or "llm"
    extra: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable representation."""
        if self.query_type == QueryType.TREND:
            return (
                f"Trend query: {self.trend_direction.value if self.trend_direction else '?'} "
                f"{self.indicator} for {self.lookback_days} days"
            )
        elif self.query_type == QueryType.THRESHOLD:
            threshold = "average" if self.threshold_is_average else self.threshold_value
            return (
                f"Threshold query: {self.indicator} "
                f"{self.operator.value if self.operator else '?'} {threshold}"
            )
        elif self.query_type == QueryType.COMPARISON:
            return f"Comparison query: {self.comparison_direction} {self.comparison_target}"
        else:
            return f"Unknown query: {self.original_query}"


@dataclass
class QueryResult:
    """Result from executing a parsed query."""

    query: ParsedQuery
    matching_tickers: list[str] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    total_scanned: int = 0
    execution_time_ms: float = 0.0
    error: str | None = None

    @property
    def success(self) -> bool:
        """Check if query executed successfully."""
        return self.error is None

    @property
    def count(self) -> int:
        """Number of matching results."""
        return len(self.matching_tickers)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": {
                "original": self.query.original_query,
                "type": self.query.query_type.value,
                "indicator": self.query.indicator,
                "parsed_by": self.query.parsed_by,
            },
            "matching_tickers": self.matching_tickers,
            "results": self.results,
            "total_scanned": self.total_scanned,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
        }

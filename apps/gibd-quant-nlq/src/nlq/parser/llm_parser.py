"""LLM-based parser for complex natural language queries.

Uses OpenAI API to parse queries that don't match predefined patterns.
This is an optional component - if OPENAI_API_KEY is not set, the parser
will gracefully fail and the system will rely on pattern matching only.
"""

import json
import logging
import os
from typing import Any

from src.nlq.types import (
    ComparisonOperator,
    ParsedQuery,
    QueryType,
    TrendDirection,
    normalize_indicator,
)

logger = logging.getLogger(__name__)


# System prompt for the LLM
LLM_SYSTEM_PROMPT = """You are a query parser for a stock analysis system. Parse the user's query into structured JSON.

Available indicators:
- RSI_14 (Relative Strength Index)
- SMA_20, SMA_50, SMA_200 (Simple Moving Averages)
- MACD_line_12_26_9, MACD_histogram_12_26_9, MACD_signal_12_26_9
- ATR_14 (Average True Range)
- ADX_14 (Average Directional Index)
- volume (trading volume)
- close (closing price)

Query types:
- trend: Looking for increasing/decreasing indicators over time
- threshold: Looking for indicators above/below a specific value
- comparison: Comparing stock performance to sector or other stocks
- crossover: Looking for indicator crossovers (like MACD)
- sr: Support/resistance proximity
- unknown: Cannot understand the query

Respond with ONLY valid JSON (no markdown, no explanation):
{
  "query_type": "trend|threshold|comparison|crossover|sr|unknown",
  "indicator": "indicator_name or null",
  "operator": "above|below|equals|near or null",
  "threshold_value": number or null,
  "threshold_is_average": boolean (true if comparing to average),
  "trend_direction": "increasing|decreasing|stable or null",
  "lookback_days": number (default 5),
  "comparison_target": "sector|average or null",
  "comparison_direction": "outperforming|underperforming or null",
  "confidence": 0.0-1.0
}"""


class LLMParser:
    """Parse natural language queries using an LLM.

    This parser uses OpenAI's API to understand complex queries that
    don't match predefined regex patterns.

    Attributes:
        api_key: OpenAI API key.
        model: Model to use (default: gpt-3.5-turbo).
        enabled: Whether the parser is available.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-3.5-turbo",
    ):
        """Initialize the LLM parser.

        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: Model to use for parsing.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.enabled = self.api_key is not None

        if not self.enabled:
            logger.info("LLM parser disabled - OPENAI_API_KEY not set")

    def parse(self, query: str) -> ParsedQuery | None:
        """Parse a query using the LLM.

        Args:
            query: Natural language query string.

        Returns:
            ParsedQuery if successful, None if parsing fails or LLM is disabled.
        """
        if not self.enabled:
            return None

        try:
            response = self._call_llm(query)
            if response:
                return self._parse_response(query, response)
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}")

        return None

    def _call_llm(self, query: str) -> dict[str, Any] | None:
        """Call the LLM API to parse the query.

        Args:
            query: Natural language query string.

        Returns:
            Parsed JSON response or None if failed.
        """
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Parse this query: {query}"},
                ],
                temperature=0,  # Deterministic output
                max_tokens=200,
            )

            content = response.choices[0].message.content
            if content:
                # Clean up response (remove markdown if present)
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()

                return json.loads(content)

        except ImportError:
            logger.warning("openai package not installed")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            logger.warning(f"LLM API call failed: {e}")

        return None

    def _parse_response(self, original_query: str, response: dict[str, Any]) -> ParsedQuery:
        """Convert LLM response to ParsedQuery.

        Args:
            original_query: Original query string.
            response: Parsed JSON from LLM.

        Returns:
            ParsedQuery object.
        """
        # Map query type
        query_type_str = response.get("query_type", "unknown")
        query_type_map = {
            "trend": QueryType.TREND,
            "threshold": QueryType.THRESHOLD,
            "comparison": QueryType.COMPARISON,
            "crossover": QueryType.CROSSOVER,
            "sr": QueryType.SUPPORT_RESISTANCE,
        }
        query_type = query_type_map.get(query_type_str, QueryType.UNKNOWN)

        # Map trend direction
        trend_direction = None
        trend_str = response.get("trend_direction")
        if trend_str:
            trend_map = {
                "increasing": TrendDirection.INCREASING,
                "decreasing": TrendDirection.DECREASING,
                "stable": TrendDirection.STABLE,
            }
            trend_direction = trend_map.get(trend_str)

        # Map operator
        operator = None
        operator_str = response.get("operator")
        if operator_str:
            operator_map = {
                "above": ComparisonOperator.ABOVE,
                "below": ComparisonOperator.BELOW,
                "equals": ComparisonOperator.EQUALS,
                "near": ComparisonOperator.NEAR,
            }
            operator = operator_map.get(operator_str)

        # Normalize indicator
        indicator_raw = response.get("indicator")
        indicator = normalize_indicator(indicator_raw) if indicator_raw else None

        return ParsedQuery(
            original_query=original_query,
            query_type=query_type,
            indicator=indicator,
            indicator_raw=indicator_raw,
            operator=operator,
            threshold_value=response.get("threshold_value"),
            threshold_is_average=response.get("threshold_is_average", False),
            trend_direction=trend_direction,
            lookback_days=response.get("lookback_days", 5),
            comparison_target=response.get("comparison_target"),
            comparison_direction=response.get("comparison_direction"),
            confidence=response.get("confidence", 0.8),
            parsed_by="llm",
        )

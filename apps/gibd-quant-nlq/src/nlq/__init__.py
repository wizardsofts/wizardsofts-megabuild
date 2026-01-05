"""Natural Language Query (NLQ) module for quant-flow.

This module provides natural language query capabilities for stock analysis,
enabling users to query data using plain English through both CLI and API.

Example usage:
    from nlq.api import NLQueryEngine

    engine = NLQueryEngine()
    result = engine.query("stocks with RSI above 70")
    for stock in result.results:
        print(f"{stock['ticker']}: RSI = {stock['value']}")
"""

from nlq.api import NLQueryEngine
from nlq.types import ComparisonOperator, ParsedQuery, QueryResult, QueryType, TrendDirection

__all__ = [
    "NLQueryEngine",
    "ParsedQuery",
    "QueryResult",
    "QueryType",
    "TrendDirection",
    "ComparisonOperator",
]

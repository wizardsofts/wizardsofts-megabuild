"""Conditional tool selector for fast track indicator analysis.

This module provides intelligent selection of technical analysis tools based on
market context, query keywords, and detected patterns.
"""

import logging

logger = logging.getLogger(__name__)


class ConditionalToolSelector:
    """Intelligently select which technical indicators to calculate.

    This selector uses market context, volatility conditions, and user queries
    to determine which tools should be calculated. Core tools are always included.

    Attributes:
        CORE_TOOLS: List of 8 essential indicators always calculated
    """

    # 8 core tools always calculated
    CORE_TOOLS = [
        "rsi",  # Relative Strength Index - momentum
        "macd",  # Moving Average Convergence Divergence - trend
        "sma_20",  # 20-period Simple Moving Average - trend
        "sma_50",  # 50-period Simple Moving Average - medium trend
        "sma_200",  # 200-period Simple Moving Average - long-term trend
        "bbands",  # Bollinger Bands - volatility and mean reversion
        "atr",  # Average True Range - volatility
        "obv",  # On-Balance Volume - volume and momentum
    ]

    def __init__(self):
        """Initialize the tool selector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("ConditionalToolSelector initialized")

    def select_tools(self, context: dict) -> list[str]:
        """Select tools based on market context and conditions.

        Starts with core tools and adds additional tools based on:
        - Market volatility
        - Price position relative to moving averages
        - Trend strength
        - Market regime (trending vs sideways)
        - User query keywords

        Args:
            context: Dictionary containing:
                {
                    'query': str,  # Optional user query
                    'atr': float,  # Current ATR for volatility
                    'price': float,  # Current price
                    'sma_200': float,  # 200-day SMA
                    'adx': float,  # ADX for trend strength
                    'volatility_regime': str,  # 'high', 'normal', 'low'
                    'market_regime': str,  # 'trending', 'sideways'
                }

        Returns:
            List of selected tool names (strings)
        """
        # Start with core tools
        selected_tools = self.CORE_TOOLS.copy()

        self.logger.info("Starting tool selection from core tools")

        # Apply context-based triggers
        if context:
            # Trigger 1: High volatility
            if self._check_high_volatility(context):
                volatility_tools = self._get_volatility_tools()
                selected_tools.extend(volatility_tools)
                self.logger.debug(f"High volatility detected: added {len(volatility_tools)} tools")

            # Trigger 2: Price near SMA_200
            if self._check_price_near_sma200(context):
                support_tools = self._get_support_resistance_tools()
                selected_tools.extend(support_tools)
                self.logger.debug(f"Price near SMA200 detected: added {len(support_tools)} tools")

            # Trigger 3: Strong trend
            if self._check_strong_trend(context):
                trend_tools = self._get_trend_tools()
                selected_tools.extend(trend_tools)
                self.logger.debug(f"Strong trend detected: added {len(trend_tools)} tools")

            # Trigger 4: Sideways market
            if self._check_sideways_market(context):
                cycle_tools = self._get_cycle_tools()
                selected_tools.extend(cycle_tools)
                self.logger.debug(f"Sideways market detected: added {len(cycle_tools)} tools")

            # Trigger 5: Query-based selection
            if "query" in context and context["query"]:
                query_tools = self._get_query_based_tools(context["query"])
                selected_tools.extend(query_tools)
                self.logger.debug(f"Query-based tools: added {len(query_tools)} tools")

        # Remove duplicates while preserving order
        unique_tools = []
        seen = set()
        for tool in selected_tools:
            if tool not in seen:
                unique_tools.append(tool)
                seen.add(tool)

        self.logger.info(f"Tool selection complete: {len(unique_tools)} tools selected")
        return unique_tools

    def _check_high_volatility(self, context: dict) -> bool:
        """Check if market is in high volatility regime.

        High volatility is detected when:
        - ATR is > 1.5x the average, OR
        - Volatility regime is 'high'

        Args:
            context: Market context dictionary

        Returns:
            True if high volatility detected, False otherwise
        """
        if not context:
            return False

        # Check volatility regime flag
        if context.get("volatility_regime") == "high":
            return True

        # Check if ATR indicates high volatility (would need historical ATR average)
        # For now, rely on volatility_regime flag
        return False

    def _check_price_near_sma200(self, context: dict) -> bool:
        """Check if price is near 200-day SMA (within 2%).

        Support/resistance tools are useful when price is consolidating
        around major moving averages.

        Args:
            context: Market context dictionary

        Returns:
            True if price within 2% of SMA200, False otherwise
        """
        if not context or "price" not in context or "sma_200" not in context:
            return False

        price = context.get("price", 0)
        sma_200 = context.get("sma_200", 0)

        if sma_200 == 0:
            return False

        distance_pct = abs(price - sma_200) / sma_200 * 100
        is_near: bool = distance_pct < 2.0

        if is_near:
            self.logger.debug(f"Price {distance_pct:.2f}% near SMA200")

        return is_near

    def _check_strong_trend(self, context: dict) -> bool:
        """Check if market is in a strong trend (ADX > 25).

        Trend-following tools are most useful in strong directional markets.

        Args:
            context: Market context dictionary

        Returns:
            True if ADX > 25 (strong trend), False otherwise
        """
        if not context or "adx" not in context:
            return False

        adx = context.get("adx", 0)
        is_strong_trend: bool = adx > 25

        if is_strong_trend:
            self.logger.debug(f"Strong trend detected: ADX={adx:.2f}")

        return is_strong_trend

    def _check_sideways_market(self, context: dict) -> bool:
        """Check if market is in sideways/range-bound regime.

        Cycle and pattern tools are useful in choppy sideways markets.

        Args:
            context: Market context dictionary

        Returns:
            True if market_regime is 'sideways', False otherwise
        """
        if not context:
            return False

        is_sideways: bool = context.get("market_regime") == "sideways"

        if is_sideways:
            self.logger.debug("Sideways market detected")

        return is_sideways

    def _get_volatility_tools(self) -> list[str]:
        """Get volatility analysis tools.

        Returns:
            List of volatility-related tool names
        """
        return [
            "natr",  # Normalized Average True Range
            "trange",  # True Range
            "keltner_channels",  # Keltner Channels for volatility bands
        ]

    def _get_support_resistance_tools(self) -> list[str]:
        """Get support and resistance tools.

        Returns:
            List of support/resistance tool names
        """
        return [
            "pivot_points",  # Pivot point levels
            "fibonacci_retracement",  # Fibonacci support/resistance
        ]

    def _get_trend_tools(self) -> list[str]:
        """Get trend analysis tools.

        Returns:
            List of trend analysis tool names
        """
        return [
            "adx",  # Average Directional Index
            "aroon",  # Aroon indicator
            "ppo",  # Percentage Price Oscillator
        ]

    def _get_cycle_tools(self) -> list[str]:
        """Get cycle and pattern identification tools.

        Returns:
            List of cycle identification tool names
        """
        return [
            "ht_dcperiod",  # HT Dominant Cycle Period
            "ht_trendmode",  # HT Trend Mode
        ]

    def _get_query_based_tools(self, query: str) -> list[str]:
        """Select tools based on query keywords.

        Maps user query keywords to relevant technical tools.

        Args:
            query: User query string

        Returns:
            List of query-matched tool names
        """
        if not query:
            return []

        query_lower = query.lower()
        selected_tools = []

        # Keyword to tools mapping
        keyword_map = {
            "fibonacci": ["fibonacci_retracement"],
            "divergence": ["rsi", "macd", "obv"],  # Ensure divergence tools
            "volume": ["obv", "ad", "adosc", "mfi"],  # Volume analysis
            "volatility": ["atr", "natr", "bbands", "keltner_channels"],
            "pattern": self._get_pattern_tools(),
            "trend": ["adx", "aroon", "ppo"],
            "support": ["pivot_points", "fibonacci_retracement"],
            "resistance": ["pivot_points", "fibonacci_retracement"],
            "momentum": ["rsi", "stoch", "cci", "mom"],
            "cycle": ["ht_dcperiod", "ht_trendmode"],
        }

        # Check for keywords and add corresponding tools
        for keyword, tools in keyword_map.items():
            if keyword in query_lower:
                selected_tools.extend(tools)
                self.logger.debug(f"Query keyword '{keyword}' matched: added {tools}")

        return selected_tools

    def _get_pattern_tools(self) -> list[str]:
        """Get all candlestick pattern tools.

        These are TA-Lib pattern recognition functions for identifying
        common candlestick formations that may signal trend reversals
        or continuations.

        Returns:
            List of all candlestick pattern tool names
        """
        patterns = [
            # Single-bar patterns
            "cdl2crows",  # Two Crows
            "cdl3blackcrows",  # Three Black Crows
            "cdl3inside",  # Three Inside Up/Down
            "cdl3linestrike",  # Three-Line Strike
            "cdl3outside",  # Three Outside Up/Down
            "cdl3starsinsouth",  # Three Stars In The South
            "cdl3whitesoldiers",  # Three White Soldiers
            "cdlabandonedbaby",  # Abandoned Baby
            "cdladvanceblock",  # Advance Block
            "cdlbelthold",  # Belt-hold
            "cdlclosingmarubozu",  # Closing Marubozu
            "cdlconcealbabyswall",  # Concealing Baby Swallow
            "cdlcounterattack",  # Counterattack
            "cdldarkcloudcover",  # Dark Cloud Cover
            "cdldoji",  # Doji
            "cdldojistar",  # Doji Star
            "cdldragonflydoji",  # Dragonfly Doji
            "cdlengulfing",  # Engulfing Pattern
            "cdleveningdojistar",  # Evening Doji Star
            "cdleveningstar",  # Evening Star
            "cdlgapsidesidewhite",  # Up/Down-gap side-by-side white lines
            "cdlhammer",  # Hammer
            "cdlhangingman",  # Hanging Man
            "cdlharami",  # Harami
            "cdlharamicross",  # Harami Cross
            "cdlhighwave",  # High Wave Candle
            "cdlinvertedhammer",  # Inverted Hammer
            "cdlkicking",  # Kicking
            "cdlkickingbylength",  # Kicking by Length
            "cdlkickingbyvolume",  # Kicking by Volume
            "cdlladderbottom",  # Ladder Bottom
            "cdlmorningdojistar",  # Morning Doji Star
            "cdlmorningstar",  # Morning Star
            "cdlonneck",  # On-Neck Pattern
            "cdlpiercing",  # Piercing Pattern
            "cdlrickshaw",  # Rickshaw Man
            "cdlrisefall3methods",  # Rising/Falling Three Methods
            "cdlseparatinglines",  # Separating Lines
            "cdlshootingstar",  # Shooting Star
            "cdltakuri",  # Takuri (Dragonfly Doji with very long lower shadow)
            "cdltasukigap",  # Tasuki Gap
            "cdlthrusting",  # Thrusting Pattern
            "cdlupsidegap2crows",  # Upside Gap Two Crows
        ]
        return patterns

    def get_supported_tools(self) -> dict:
        """Get all supported tools by category.

        Returns:
            Dictionary with tool categories and their tools
        """
        return {
            "core": self.CORE_TOOLS,
            "volatility": self._get_volatility_tools(),
            "support_resistance": self._get_support_resistance_tools(),
            "trend": self._get_trend_tools(),
            "cycle": self._get_cycle_tools(),
            "patterns": self._get_pattern_tools(),
        }

"""Comprehensive indicator calculator for all technical analysis tools.

This module provides the IndicatorCalculator class that calculates a wide range
of technical indicators including momentum, overlap, volume, volatility, and
pattern recognition indicators using TA-Lib.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
import talib

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """Calculate all supported technical indicators from OHLCV data.

    This calculator provides methods to compute:
    - Momentum indicators (RSI, MACD, Stochastic, CCI, Momentum)
    - Overlap indicators (SMA, EMA, Bollinger Bands, Keltner Channels)
    - Volume indicators (OBV, AD, ADOSC, MFI)
    - Volatility indicators (ATR, NATR, True Range)
    - Pattern indicators (43 candlestick patterns)
    - Cycle indicators (HT_DCPERIOD, HT_TRENDMODE)
    """

    def __init__(self):
        """Initialize the indicator calculator."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("IndicatorCalculator initialized")

    def calculate_all(
        self, data: pd.DataFrame, ticker: str, selected_tools: list[str] | None = None
    ) -> dict[str, Any]:
        """Calculate all requested indicators.

        Args:
            data: DataFrame with OHLCV data. Must have columns:
                  ['open', 'high', 'low', 'close', 'volume']
            ticker: Stock ticker symbol for logging.
            selected_tools: List of specific tools to calculate. If None, calculates all.

        Returns:
            Dictionary mapping indicator names to calculated values/arrays.

        Raises:
            ValueError: If data is None, empty, or missing required columns.
        """
        self.logger.info(f"[{ticker}] Calculating indicators for {len(data)} periods")

        # Validate input
        if data is None or len(data) == 0:
            raise ValueError(f"[{ticker}] Data cannot be None or empty")

        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"[{ticker}] Data missing required columns: {missing_columns}")

        results: dict[str, Any] = {}

        # Extract OHLCV data
        open_data = data["open"].values
        high_data = data["high"].values
        low_data = data["low"].values
        close_data = data["close"].values
        volume_data = data["volume"].values

        try:
            # Calculate momentum indicators
            if selected_tools is None or "rsi" in selected_tools:
                try:
                    results["rsi"] = talib.RSI(close_data, timeperiod=14).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] RSI calculation failed: {e}")

            if selected_tools is None or "macd" in selected_tools:
                try:
                    macd, signal, hist = talib.MACD(
                        close_data, fastperiod=12, slowperiod=26, signalperiod=9
                    )
                    results["macd"] = macd.tolist()
                    results["macd_signal"] = signal.tolist()
                    results["macd_hist"] = hist.tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] MACD calculation failed: {e}")

            if selected_tools is None or "stoch" in selected_tools:
                try:
                    slowk, slowd = talib.STOCH(
                        high_data,
                        low_data,
                        close_data,
                        fastk_period=5,
                        slowk_period=3,
                        slowd_period=3,
                    )
                    results["stoch_k"] = slowk.tolist()
                    results["stoch_d"] = slowd.tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Stochastic calculation failed: {e}")

            if selected_tools is None or "cci" in selected_tools:
                try:
                    results["cci"] = talib.CCI(
                        high_data, low_data, close_data, timeperiod=20
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] CCI calculation failed: {e}")

            if selected_tools is None or "mom" in selected_tools:
                try:
                    results["momentum"] = talib.MOM(close_data, timeperiod=10).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Momentum calculation failed: {e}")

            # Calculate overlap indicators
            if selected_tools is None or "sma_20" in selected_tools:
                try:
                    results["sma_20"] = talib.SMA(close_data, timeperiod=20).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] SMA20 calculation failed: {e}")

            if selected_tools is None or "sma_50" in selected_tools:
                try:
                    results["sma_50"] = talib.SMA(close_data, timeperiod=50).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] SMA50 calculation failed: {e}")

            if selected_tools is None or "sma_200" in selected_tools:
                try:
                    results["sma_200"] = talib.SMA(close_data, timeperiod=200).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] SMA200 calculation failed: {e}")

            if selected_tools is None or "ema" in selected_tools:
                try:
                    results["ema_12"] = talib.EMA(close_data, timeperiod=12).tolist()
                    results["ema_26"] = talib.EMA(close_data, timeperiod=26).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] EMA calculation failed: {e}")

            if selected_tools is None or "bbands" in selected_tools:
                try:
                    upper, middle, lower = talib.BBANDS(
                        close_data, timeperiod=20, nbdevup=2, nbdevdn=2
                    )
                    results["bb_upper"] = upper.tolist()
                    results["bb_middle"] = middle.tolist()
                    results["bb_lower"] = lower.tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Bollinger Bands calculation failed: {e}")

            if selected_tools is None or "keltner_channels" in selected_tools:
                try:
                    # Keltner Channels: EMA ± ATR
                    ema = talib.EMA(close_data, timeperiod=20)
                    atr = talib.ATR(high_data, low_data, close_data, timeperiod=10)
                    results["keltner_upper"] = (ema + atr).tolist()
                    results["keltner_middle"] = ema.tolist()
                    results["keltner_lower"] = (ema - atr).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Keltner Channels calculation failed: {e}")

            # Calculate volume indicators
            if selected_tools is None or "obv" in selected_tools:
                try:
                    results["obv"] = talib.OBV(
                        close_data.astype(np.float64), volume_data.astype(np.float64)
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] OBV calculation failed: {e}")

            if selected_tools is None or "ad" in selected_tools:
                try:
                    results["ad"] = talib.AD(
                        high_data.astype(np.float64),
                        low_data.astype(np.float64),
                        close_data.astype(np.float64),
                        volume_data.astype(np.float64),
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] A/D calculation failed: {e}")

            if selected_tools is None or "adosc" in selected_tools:
                try:
                    results["adosc"] = talib.ADOSC(
                        high_data.astype(np.float64),
                        low_data.astype(np.float64),
                        close_data.astype(np.float64),
                        volume_data.astype(np.float64),
                        fastperiod=3,
                        slowperiod=10,
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] ADOSC calculation failed: {e}")

            if selected_tools is None or "mfi" in selected_tools:
                try:
                    results["mfi"] = talib.MFI(
                        high_data.astype(np.float64),
                        low_data.astype(np.float64),
                        close_data.astype(np.float64),
                        volume_data.astype(np.float64),
                        timeperiod=14,
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] MFI calculation failed: {e}")

            # Calculate volatility indicators
            if selected_tools is None or "atr" in selected_tools:
                try:
                    results["atr"] = talib.ATR(
                        high_data, low_data, close_data, timeperiod=14
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] ATR calculation failed: {e}")

            if selected_tools is None or "natr" in selected_tools:
                try:
                    results["natr"] = talib.NATR(
                        high_data, low_data, close_data, timeperiod=14
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] NATR calculation failed: {e}")

            if selected_tools is None or "trange" in selected_tools:
                try:
                    results["trange"] = talib.TRANGE(high_data, low_data, close_data).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] TRANGE calculation failed: {e}")

            # Calculate support/resistance indicators
            if selected_tools is None or "pivot_points" in selected_tools:
                try:
                    pivot = (data["high"] + data["low"] + data["close"]) / 3
                    results["pivot"] = pivot.tolist()
                    results["r1"] = (2 * pivot - data["low"]).tolist()
                    results["s1"] = (2 * pivot - data["high"]).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Pivot Points calculation failed: {e}")

            if selected_tools is None or "fibonacci_retracement" in selected_tools:
                try:
                    # Fibonacci levels from high and low
                    period_high = data["high"].rolling(window=20).max()
                    period_low = data["low"].rolling(window=20).min()
                    diff = period_high - period_low

                    results["fib_0"] = period_low.tolist()
                    results["fib_236"] = (period_low + diff * 0.236).tolist()
                    results["fib_382"] = (period_low + diff * 0.382).tolist()
                    results["fib_500"] = (period_low + diff * 0.5).tolist()
                    results["fib_618"] = (period_low + diff * 0.618).tolist()
                    results["fib_786"] = (period_low + diff * 0.786).tolist()
                    results["fib_100"] = period_high.tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Fibonacci Retracement calculation failed: {e}")

            # Calculate trend indicators
            if selected_tools is None or "adx" in selected_tools:
                try:
                    results["adx"] = talib.ADX(
                        high_data, low_data, close_data, timeperiod=14
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] ADX calculation failed: {e}")

            if selected_tools is None or "aroon" in selected_tools:
                try:
                    aroondown, aroonup = talib.AROON(high_data, low_data, timeperiod=25)
                    results["aroon_up"] = aroonup.tolist()
                    results["aroon_down"] = aroondown.tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] Aroon calculation failed: {e}")

            if selected_tools is None or "ppo" in selected_tools:
                try:
                    results["ppo"] = talib.PPO(
                        close_data, fastperiod=12, slowperiod=26, matype=0
                    ).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] PPO calculation failed: {e}")

            # Calculate cycle indicators
            if selected_tools is None or "ht_dcperiod" in selected_tools:
                try:
                    results["ht_dcperiod"] = talib.HT_DCPERIOD(close_data).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] HT_DCPERIOD calculation failed: {e}")

            if selected_tools is None or "ht_trendmode" in selected_tools:
                try:
                    results["ht_trendmode"] = talib.HT_TRENDMODE(close_data).tolist()
                except Exception as e:
                    self.logger.warning(f"[{ticker}] HT_TRENDMODE calculation failed: {e}")

            # Calculate candlestick patterns
            patterns = self._get_pattern_tools()
            if selected_tools is None:
                selected_patterns = patterns
            else:
                selected_patterns = [p for p in patterns if p in selected_tools]

            for pattern in selected_patterns:
                try:
                    pattern_func = getattr(talib, pattern.upper())
                    results[pattern] = pattern_func(
                        open_data, high_data, low_data, close_data
                    ).tolist()
                except AttributeError:
                    self.logger.debug(f"[{ticker}] Pattern {pattern} not found in talib")
                except Exception as e:
                    self.logger.debug(f"[{ticker}] Pattern {pattern} calculation failed: {e}")

            self.logger.info(f"[{ticker}] Calculated {len(results)} indicators")
            return results

        except Exception as e:
            self.logger.error(f"[{ticker}] Indicator calculation failed: {e}")
            raise

    def _get_pattern_tools(self) -> list[str]:
        """Get list of all supported candlestick pattern names.

        Returns:
            List of pattern tool names from TA-Lib
        """
        return [
            "cdl2crows",
            "cdl3blackcrows",
            "cdl3inside",
            "cdl3linestrike",
            "cdl3outside",
            "cdl3starsinsouth",
            "cdl3whitesoldiers",
            "cdlabandonedbaby",
            "cdladvanceblock",
            "cdlbelthold",
            "cdlclosingmarubozu",
            "cdlconcealbabyswall",
            "cdlcounterattack",
            "cdldarkcloudcover",
            "cdldoji",
            "cdldojistar",
            "cdldragonflydoji",
            "cdlengulfing",
            "cdleveningdojistar",
            "cdleveningstar",
            "cdlgapsidesidewhite",
            "cdlhammer",
            "cdlhangingman",
            "cdlharami",
            "cdlharamicross",
            "cdlhighwave",
            "cdlinvertedhammer",
            "cdlkicking",
            "cdlkickingbylength",
            "cdlkickingbyvolume",
            "cdlladderbottom",
            "cdlmorningdojistar",
            "cdlmorningstar",
            "cdlonneck",
            "cdlpiercing",
            "cdlrickshaw",
            "cdlrisefall3methods",
            "cdlseparatinglines",
            "cdlshootingstar",
            "cdltakuri",
            "cdltasukigap",
            "cdlthrusting",
            "cdlupsidegap2crows",
        ]

"""Multi-timeframe indicator calculator for Fast Track analysis.

This module provides the MultiTimeframeCalculator class for calculating indicators
across multiple timeframes (5d, 20d, 50d, 200d) to identify aligned signals
and cross-timeframe patterns.
"""

import logging

import numpy as np
import pandas as pd
import talib

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when there is not enough data for the requested timeframe."""

    pass


class MultiTimeframeCalculator:
    """Calculate indicators across multiple timeframes.

    This calculator computes indicators for 5-day, 20-day, 50-day, and 200-day
    timeframes to enable multi-timeframe analysis for trend confirmation and
    signal alignment detection.

    Attributes:
        TIMEFRAMES: List of timeframe periods in days (5, 20, 50, 200).
    """

    TIMEFRAMES = [5, 20, 50, 200]

    def __init__(self):
        """Initialize the multi-timeframe calculator."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def calculate(self, data: pd.DataFrame, ticker: str) -> dict:
        """Calculate indicators across all timeframes.

        Args:
            data: DataFrame with OHLCV data. Must have columns:
                  ['date', 'open', 'high', 'low', 'close', 'volume']
            ticker: Stock ticker symbol for logging purposes.

        Returns:
            Dictionary with timeframe-keyed results:
            {
                '5d': {...},
                '20d': {...},
                '50d': {...},
                '200d': {...}
            }

        Raises:
            InsufficientDataError: If data doesn't contain enough periods
                                  for the largest timeframe.
            ValueError: If data is None or empty, or missing required columns.
        """
        # Validate input
        if data is None or len(data) == 0:
            raise ValueError(f"[{ticker}] Data cannot be None or empty")

        required_columns = ["date", "open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"[{ticker}] Data missing required columns: {missing_columns}")

        # Check minimum data availability
        max_timeframe = max(self.TIMEFRAMES)
        if len(data) < max_timeframe:
            raise InsufficientDataError(
                f"[{ticker}] Insufficient data: {len(data)} periods available, "
                f"but {max_timeframe} required for largest timeframe"
            )

        self.logger.info(
            f"[{ticker}] Starting multi-timeframe calculation with {len(data)} periods"
        )

        results = {}
        for timeframe in self.TIMEFRAMES:
            try:
                tf_key = f"{timeframe}d"
                self.logger.debug(f"[{ticker}] Calculating {tf_key} timeframe")

                tf_result = self._calc_timeframe(data, timeframe, ticker)
                results[tf_key] = tf_result

                self.logger.debug(f"[{ticker}] {tf_key} calculation complete: {tf_result}")
            except Exception as e:
                self.logger.error(f"[{ticker}] Error calculating {timeframe}d timeframe: {str(e)}")
                results[f"{timeframe}d"] = {
                    "error": str(e),
                    "timeframe": timeframe,
                    "available": False,
                }

        self.logger.info(
            f"[{ticker}] Multi-timeframe calculation complete for {len(results)} timeframes"
        )

        return results

    def _calc_timeframe(self, data: pd.DataFrame, timeframe: int, ticker: str) -> dict:
        """Calculate indicators for a specific timeframe.

        Calculates RSI for the given timeframe along with basic availability info.

        Args:
            data: Full DataFrame with OHLCV data.
            timeframe: Number of days for this timeframe window.
            ticker: Stock ticker symbol for logging.

        Returns:
            Dictionary with timeframe calculation results:
            {
                'timeframe': int,
                'data_points': int,
                'available': bool,
                'start_date': str,
                'end_date': str,
                'rsi': float or None  # Only if RSI calculation succeeds
            }

        Raises:
            InsufficientDataError: If not enough data for this timeframe.
        """
        if len(data) < timeframe:
            raise InsufficientDataError(
                f"[{ticker}] Insufficient data for {timeframe}d: " f"{len(data)} periods available"
            )

        # Get the window of data for this timeframe
        window_data = data.tail(timeframe)

        result = {
            "timeframe": timeframe,
            "data_points": len(window_data),
            "available": True,
            "start_date": str(window_data.iloc[0]["date"]),
            "end_date": str(window_data.iloc[-1]["date"]),
        }

        # Calculate RSI for this timeframe if method exists
        rsi_method_name = f"_calc_rsi_{timeframe}d"
        if hasattr(self, rsi_method_name):
            try:
                rsi_method = getattr(self, rsi_method_name)
                rsi_value = rsi_method(data, ticker)
                result["rsi"] = rsi_value
                self.logger.debug(f"[{ticker}] {timeframe}d timeframe RSI: {rsi_value}")
            except Exception as e:
                self.logger.warning(
                    f"[{ticker}] Could not calculate RSI for {timeframe}d: {str(e)}"
                )
                result["rsi"] = None

        return result

    def get_supported_timeframes(self) -> list[int]:
        """Get list of supported timeframes in days.

        Returns:
            List of timeframe periods (e.g., [5, 20, 50, 200]).
        """
        return self.TIMEFRAMES.copy()

    def calculate_sma_all(self, data: pd.DataFrame, ticker: str) -> dict[str, np.ndarray | None]:
        """Calculate all SMA indicators (20, 50, 200).

        Args:
            data: DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Dictionary with SMA arrays:
            {
                'sma_20': array or None,
                'sma_50': array or None,
                'sma_200': array or None
            }
        """
        self.logger.debug(f"[{ticker}] Calculating all SMAs")

        return {
            "sma_20": self._calc_sma_20(data, ticker),
            "sma_50": self._calc_sma_50(data, ticker),
            "sma_200": self._calc_sma_200(data, ticker),
        }

    def check_alignment(self, indicators: dict) -> str:
        """Check if signals align across timeframes.

        Analyzes RSI values across all timeframes to determine if they show
        aligned signals (all overbought, all oversold, etc.)

        Args:
            indicators: Dictionary of indicators with RSI values for each timeframe:
                       {'5d': {'rsi': 75}, '20d': {'rsi': 72}, ...}

        Returns:
            Alignment status string:
            - "strong_overbought": All RSIs > 70
            - "strong_oversold": All RSIs < 30
            - "short_term_overbought": Only 5d RSI > 70, long-term < 70
            - "short_term_oversold": Only 5d RSI < 30, long-term > 30
            - "conflicted": Mixed signals
            - "neutral": All between 30-70
        """
        # Extract RSI values from each timeframe
        rsi_values = {}
        for tf in self.TIMEFRAMES:
            tf_key = f"{tf}d"
            if tf_key in indicators and indicators[tf_key].get("rsi") is not None:
                rsi_values[tf_key] = indicators[tf_key]["rsi"]

        if not rsi_values:
            self.logger.warning("No RSI values available for alignment check")
            return "neutral"

        # Count overbought (>70) and oversold (<30) signals
        overbought_count = sum(1 for rsi in rsi_values.values() if rsi > 70)
        oversold_count = sum(1 for rsi in rsi_values.values() if rsi < 30)
        total_count = len(rsi_values)

        # Check alignment patterns
        rsi_5d = rsi_values.get("5d", 50)
        rsi_200d = rsi_values.get("200d", 50)

        # All overbought
        if overbought_count == total_count:
            return "strong_overbought"

        # All oversold
        if oversold_count == total_count:
            return "strong_oversold"

        # Short-term overbought, long-term not
        if rsi_5d > 70 and rsi_200d < 70:
            return "short_term_overbought"

        # Short-term oversold, long-term not
        if rsi_5d < 30 and rsi_200d > 30:
            return "short_term_oversold"

        # Mixed signals
        if overbought_count > 0 and oversold_count > 0:
            return "conflicted"

        # Neutral
        return "neutral"

    def calculate_volume_metrics(self, data: pd.DataFrame, ticker: str) -> dict:
        """Calculate volume metrics across timeframes.

        Analyzes volume patterns to detect trends, spikes, and relative volume.

        Args:
            data: DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Dictionary with volume metrics:
            {
                'avg_volume_5d': float,
                'avg_volume_20d': float,
                'avg_volume_50d': float,
                'avg_volume_200d': float,
                'volume_trend': str,  # "increasing", "decreasing", "stable"
                'current_rvol': float,  # relative volume vs 200-day average
                'volume_spike_detected': bool,
                'volume_metrics_available': bool
            }
        """
        if data is None or len(data) < 20:
            self.logger.warning(
                f"[{ticker}] Insufficient data for volume analysis: "
                f"{len(data) if data is not None else 0} periods"
            )
            return {
                "volume_metrics_available": False,
                "error": "Insufficient data for volume analysis",
            }

        try:
            volumes = data["volume"].values.astype(np.float64)

            # Calculate average volumes for each timeframe
            avg_volume_5d = float(np.mean(volumes[-5:])) if len(volumes) >= 5 else 0
            avg_volume_20d = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 0
            avg_volume_50d = float(np.mean(volumes[-50:])) if len(volumes) >= 50 else 0
            avg_volume_200d = float(np.mean(volumes[-200:])) if len(volumes) >= 200 else 0

            # Current and recent average volumes
            current_volume = float(volumes[-1])
            recent_avg = float(np.mean(volumes[-20:]))

            # Detect volume trend using linear regression on last 20 periods
            if len(volumes) >= 20:
                volume_20 = volumes[-20:]
                x = np.arange(len(volume_20))
                slope = np.polyfit(x, volume_20, 1)[0]
                volume_change_rate = slope / recent_avg if recent_avg > 0 else 0

                if volume_change_rate > 0.05:
                    trend = "increasing"
                elif volume_change_rate < -0.05:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"

            # Detect volume spikes (current > 3x average)
            spike_threshold = recent_avg * 3.0 if recent_avg > 0 else 0
            spike_detected = current_volume > spike_threshold

            # Calculate relative volume (RVOL)
            rvol = current_volume / avg_volume_200d if avg_volume_200d > 0 else 1.0

            result = {
                "avg_volume_5d": avg_volume_5d,
                "avg_volume_20d": avg_volume_20d,
                "avg_volume_50d": avg_volume_50d,
                "avg_volume_200d": avg_volume_200d,
                "current_volume": current_volume,
                "volume_trend": trend,
                "current_rvol": rvol,
                "volume_spike_detected": spike_detected,
                "volume_metrics_available": True,
            }

            self.logger.debug(
                f"[{ticker}] Volume metrics calculated: "
                f"avg_200d={avg_volume_200d:.0f}, "
                f"current_rvol={rvol:.2f}, trend={trend}"
            )

            return result

        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating volume metrics: {str(e)}")
            return {
                "volume_metrics_available": False,
                "error": str(e),
            }

    def validate_data_sufficiency(self, data: pd.DataFrame, ticker: str) -> dict[str, bool]:
        """Check which timeframes have sufficient data.

        Args:
            data: DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Dictionary mapping timeframe keys to availability:
            {
                '5d': True,
                '20d': True,
                '50d': False,
                '200d': False
            }
        """
        if data is None or len(data) == 0:
            return {f"{tf}d": False for tf in self.TIMEFRAMES}

        data_len = len(data)
        availability = {}

        for timeframe in self.TIMEFRAMES:
            tf_key = f"{timeframe}d"
            availability[tf_key] = data_len >= timeframe
            if not availability[tf_key]:
                self.logger.warning(
                    f"[{ticker}] Insufficient data for {tf_key}: "
                    f"{data_len} periods available, {timeframe} required"
                )

        return availability

    def _calc_rsi_5d(self, data: pd.DataFrame, ticker: str) -> float | None:
        """Calculate RSI for 5-day timeframe.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Latest RSI value (0-100) or None if insufficient data.

        Raises:
            InsufficientDataError: If less than 5 periods available.
        """
        if len(data) < 5:
            raise InsufficientDataError(
                f"[{ticker}] Insufficient data for 5d RSI: {len(data)} periods available"
            )

        # Get the last 5 days of close prices
        window_close = data["close"].tail(5).values.astype(np.float64)

        try:
            # TA-Lib requires at least period+1 data points for RSI
            # For RSI with period 14, we need at least 15 points
            # For 5-day window, calculate RSI with period 2
            # (minimum meaningful for 5 days)
            if len(window_close) >= 3:
                rsi_values = talib.RSI(window_close, timeperiod=2)
                latest_rsi = float(rsi_values[-1])

                self.logger.debug(f"[{ticker}] 5d RSI calculated: {latest_rsi:.2f}")
                return latest_rsi
            else:
                self.logger.warning(f"[{ticker}] Insufficient data for 5d RSI calculation")
                return None
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating 5d RSI: {str(e)}")
            raise

    def _calc_rsi_20d(self, data: pd.DataFrame, ticker: str) -> float | None:
        """Calculate RSI for 20-day timeframe.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Latest RSI value (0-100) or None if insufficient data.
        """
        if len(data) < 20:
            raise InsufficientDataError(
                f"[{ticker}] Insufficient data for 20d RSI: {len(data)} periods available"
            )

        # Get the last 20 days of close prices
        window_close = data["close"].tail(20).values.astype(np.float64)

        try:
            rsi_values = talib.RSI(window_close, timeperiod=14)
            latest_rsi = float(rsi_values[-1])

            self.logger.debug(f"[{ticker}] 20d RSI calculated: {latest_rsi:.2f}")
            return latest_rsi
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating 20d RSI: {str(e)}")
            raise

    def _calc_rsi_50d(self, data: pd.DataFrame, ticker: str) -> float | None:
        """Calculate RSI for 50-day timeframe.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Latest RSI value (0-100) or None if insufficient data.
        """
        if len(data) < 50:
            raise InsufficientDataError(
                f"[{ticker}] Insufficient data for 50d RSI: {len(data)} periods available"
            )

        # Get the last 50 days of close prices
        window_close = data["close"].tail(50).values.astype(np.float64)

        try:
            rsi_values = talib.RSI(window_close, timeperiod=14)
            latest_rsi = float(rsi_values[-1])

            self.logger.debug(f"[{ticker}] 50d RSI calculated: {latest_rsi:.2f}")
            return latest_rsi
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating 50d RSI: {str(e)}")
            raise

    def _calc_rsi_200d(self, data: pd.DataFrame, ticker: str) -> float | None:
        """Calculate RSI for 200-day timeframe.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Latest RSI value (0-100) or None if insufficient data.
        """
        if len(data) < 200:
            raise InsufficientDataError(
                f"[{ticker}] Insufficient data for 200d RSI: " f"{len(data)} periods available"
            )

        # Get the last 200 days of close prices
        window_close = data["close"].tail(200).values.astype(np.float64)

        try:
            rsi_values = talib.RSI(window_close, timeperiod=14)
            latest_rsi = float(rsi_values[-1])

            self.logger.debug(f"[{ticker}] 200d RSI calculated: {latest_rsi:.2f}")
            return latest_rsi
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating 200d RSI: {str(e)}")
            raise

    def _calc_sma_20(self, data: pd.DataFrame, ticker: str) -> np.ndarray | None:
        """Calculate SMA 20 for the full dataset.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Array of SMA 20 values or None if error.
        """
        if len(data) < 20:
            self.logger.warning(
                f"[{ticker}] Insufficient data for SMA 20: {len(data)} periods available"
            )
            return None

        try:
            close_prices = data["close"].values.astype(np.float64)
            sma_20 = talib.SMA(close_prices, timeperiod=20)
            self.logger.debug(f"[{ticker}] SMA 20 calculated")
            return sma_20
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating SMA 20: {str(e)}")
            return None

    def _calc_sma_50(self, data: pd.DataFrame, ticker: str) -> np.ndarray | None:
        """Calculate SMA 50 for the full dataset.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Array of SMA 50 values or None if error.
        """
        if len(data) < 50:
            self.logger.warning(
                f"[{ticker}] Insufficient data for SMA 50: {len(data)} periods available"
            )
            return None

        try:
            close_prices = data["close"].values.astype(np.float64)
            sma_50 = talib.SMA(close_prices, timeperiod=50)
            self.logger.debug(f"[{ticker}] SMA 50 calculated")
            return sma_50
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating SMA 50: {str(e)}")
            return None

    def _calc_sma_200(self, data: pd.DataFrame, ticker: str) -> np.ndarray | None:
        """Calculate SMA 200 for the full dataset.

        Args:
            data: Full DataFrame with OHLCV data.
            ticker: Stock ticker symbol for logging.

        Returns:
            Array of SMA 200 values or None if error.
        """
        if len(data) < 200:
            self.logger.warning(
                f"[{ticker}] Insufficient data for SMA 200: {len(data)} periods available"
            )
            return None

        try:
            close_prices = data["close"].values.astype(np.float64)
            sma_200 = talib.SMA(close_prices, timeperiod=200)
            self.logger.debug(f"[{ticker}] SMA 200 calculated")
            return sma_200
        except Exception as e:
            self.logger.error(f"[{ticker}] Error calculating SMA 200: {str(e)}")
            return None

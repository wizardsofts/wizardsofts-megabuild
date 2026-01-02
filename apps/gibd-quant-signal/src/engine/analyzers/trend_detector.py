"""Trend detector for identifying patterns in indicator time-series.

This module provides the TrendDetector class for detecting trends and patterns
such as RSI reversals, Bollinger Band squeezes, volume trends, MACD divergences,
and stochastic crossovers.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class TrendDetector:
    """Detect trends and patterns in indicator time-series.

    This detector analyzes various technical indicators to identify trading
    patterns and trend reversals with confidence scoring.

    Supported Detection Methods:
    - RSI reversal detection
    - Bollinger Band squeeze/expansion detection
    - Volume trend analysis
    - MACD convergence/divergence detection
    - Stochastic crossover detection
    """

    def __init__(self):
        """Initialize the trend detector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def detect_all(self, indicators: dict, price_data: dict) -> dict:
        """Detect all available trends and patterns.

        Orchestrates all detection methods and returns comprehensive trend analysis.

        Args:
            indicators: Dictionary containing calculated indicators:
                       {
                           'rsi': [list of RSI values],
                           'rsi_5d': float,
                           'rsi_20d': float,
                           'bb_upper': [upper band array],
                           'bb_lower': [lower band array],
                           'volume': [volume array],
                           'macd': [MACD values],
                           'macd_signal': [signal line],
                           'macd_histogram': [histogram],
                           'stoch_k': [%K values],
                           'stoch_d': [%D values]
                       }
            price_data: Dictionary containing price information:
                       {
                           'close': [close prices],
                           'current_price': float
                       }

        Returns:
            Dictionary with detected trends:
            {
                'rsi_reversal': {...},
                'bb_squeeze': {...},
                'volume_trend': {...},
                'macd_divergence': {...},
                'stochastic_pattern': {...},
                'consolidation': {...},
                'trend_quality': {...},
                'overall_signal': str  # 'bullish', 'bearish', 'neutral'
            }
        """
        self.logger.info("Starting comprehensive trend detection")

        trends = {}

        # Detect RSI reversal
        if "rsi" in indicators and indicators["rsi"] is not None:
            try:
                trends["rsi_reversal"] = self.detect_rsi_reversal(indicators["rsi"])
            except Exception as e:
                self.logger.error(f"RSI reversal detection failed: {str(e)}")
                trends["rsi_reversal"] = {"error": str(e), "detected": False}

        # Detect Bollinger Band squeeze
        if (
            "bb_upper" in indicators
            and "bb_lower" in indicators
            and indicators["bb_upper"] is not None
            and indicators["bb_lower"] is not None
        ):
            try:
                trends["bb_squeeze"] = self.detect_bb_squeeze(
                    indicators["bb_upper"], indicators["bb_lower"]
                )
            except Exception as e:
                self.logger.error(f"BB squeeze detection failed: {str(e)}")
                trends["bb_squeeze"] = {"error": str(e), "detected": False}

        # Detect volume trend
        if "volume" in indicators and indicators["volume"] is not None:
            try:
                trends["volume_trend"] = self.detect_volume_trend(indicators["volume"])
            except Exception as e:
                self.logger.error(f"Volume trend detection failed: {str(e)}")
                trends["volume_trend"] = {"error": str(e), "detected": False}

        # Detect MACD divergence
        if (
            "macd" in indicators
            and "close" in price_data
            and indicators["macd"] is not None
            and price_data["close"] is not None
        ):
            try:
                trends["macd_divergence"] = self.detect_macd_divergence(
                    indicators["macd"], price_data["close"]
                )
            except Exception as e:
                self.logger.error(f"MACD divergence detection failed: {str(e)}")
                trends["macd_divergence"] = {"error": str(e), "detected": False}

        # Detect stochastic patterns
        if (
            "stoch_k" in indicators
            and "stoch_d" in indicators
            and indicators["stoch_k"] is not None
            and indicators["stoch_d"] is not None
        ):
            try:
                trends["stochastic_pattern"] = self.detect_stochastic_pattern(
                    indicators["stoch_k"], indicators["stoch_d"]
                )
            except Exception as e:
                self.logger.error(f"Stochastic pattern detection failed: {str(e)}")
                trends["stochastic_pattern"] = {"error": str(e), "detected": False}

        # Detect consolidation patterns
        if "close" in price_data and price_data["close"] is not None:
            try:
                trends["consolidation"] = self.detect_consolidation(price_data["close"])
            except Exception as e:
                self.logger.error(f"Consolidation detection failed: {str(e)}")
                trends["consolidation"] = {"error": str(e), "detected": False}

        # Calculate trend quality
        if "close" in price_data and price_data["close"] is not None:
            try:
                trends["trend_quality"] = self.calculate_trend_quality(price_data["close"])
            except Exception as e:
                self.logger.error(f"Trend quality calculation failed: {str(e)}")
                trends["trend_quality"] = {"error": str(e), "detected": False}

        self.logger.info(f"Trend detection complete: {len(trends)} patterns analyzed")

        return trends

    def detect_rsi_reversal(self, rsi_series: list) -> dict:
        """Detect if RSI has peaked and is reversing.

        Identifies RSI reversal signals where the indicator has topped
        and is now declining.

        Args:
            rsi_series: List of RSI values in chronological order

        Returns:
            Dictionary with reversal info:
            {
                'detected': bool,
                'peak_value': float,
                'peak_index': int,
                'current_slope': float,
                'confidence': float (0-1),
                'signal': str  # 'strong_reversal', 'weak_reversal', 'no_reversal'
            }
        """
        if not rsi_series or len(rsi_series) < 10:
            return {
                "detected": False,
                "reason": "Insufficient data (< 10 periods)",
            }

        rsi_array = np.array(rsi_series, dtype=np.float64)
        recent_window = rsi_array[-10:]

        # Find peak in recent window
        peak_idx = np.argmax(recent_window)
        peak_value = float(recent_window[peak_idx])

        # Check if peak is in the past (not at the end)
        if peak_idx == len(recent_window) - 1:
            return {
                "detected": False,
                "reason": "Peak is at current position (not reversal)",
            }

        # Calculate slope after peak
        after_peak = recent_window[peak_idx + 1 :]
        if len(after_peak) < 2:
            return {
                "detected": False,
                "reason": "Not enough data after peak for trend analysis",
            }

        # Linear regression slope
        x = np.arange(len(after_peak))
        slope = np.polyfit(x, after_peak, 1)[0]

        # Confidence: absolute slope normalized to [0, 1]
        confidence = min(abs(slope) / 5.0, 1.0)

        # Determine signal strength
        if slope < -0.5:
            signal = "strong_reversal" if confidence > 0.6 else "weak_reversal"
            detected = True
        else:
            signal = "no_reversal"
            detected = False

        result = {
            "detected": detected,
            "peak_value": peak_value,
            "peak_index": peak_idx,
            "current_slope": slope,
            "confidence": float(confidence),
            "signal": signal,
        }

        self.logger.debug(f"RSI reversal detection: {result}")
        return result

    def detect_bb_squeeze(self, bb_upper: list | np.ndarray, bb_lower: list | np.ndarray) -> dict:
        """Detect Bollinger Band squeeze and expansion.

        Identifies periods where bands are compressed (squeeze) or expanding,
        which can indicate upcoming volatility breakouts.

        Args:
            bb_upper: List/array of upper Bollinger Band values
            bb_lower: List/array of lower Bollinger Band values

        Returns:
            Dictionary with squeeze info:
            {
                'detected': bool,
                'pattern': str,  # 'squeeze_ongoing', 'expansion_after_squeeze', 'normal'
                'squeeze_duration': int,
                'expansion_strength': float,
                'breakout_likely': bool,
                'confidence': float
            }
        """
        if not bb_upper or not bb_lower or len(bb_upper) < 20 or len(bb_lower) < 20:
            return {"detected": False, "reason": "Insufficient data (< 20 periods)"}

        bb_upper_arr = np.array(bb_upper, dtype=np.float64)
        bb_lower_arr = np.array(bb_lower, dtype=np.float64)

        # Calculate bandwidth
        bandwidth = bb_upper_arr - bb_lower_arr

        # Get last 20 periods
        recent_bw = bandwidth[-20:]

        # Find squeeze point (minimum bandwidth)
        min_bw = float(np.min(recent_bw))
        min_idx = int(np.argmin(recent_bw))

        # Current bandwidth and average
        current_bw = float(recent_bw[-1])
        avg_bw = float(np.mean(recent_bw))

        # Detect squeeze vs expansion
        if current_bw < avg_bw * 0.7:
            pattern = "squeeze_ongoing"
            squeeze_duration = len(recent_bw) - min_idx
            expansion_strength = 1.0
            breakout_likely = False
            confidence = 0.7
            detected = True
        elif current_bw > min_bw * 1.5:
            pattern = "expansion_after_squeeze"
            squeeze_duration = min_idx
            expansion_strength = current_bw / min_bw if min_bw > 0 else 1.0
            breakout_likely = expansion_strength > 2.0
            confidence = min(expansion_strength / 3.0, 1.0)
            detected = True
        else:
            pattern = "normal"
            squeeze_duration = 0
            expansion_strength = 1.0
            breakout_likely = False
            confidence = 0.3
            detected = False

        result = {
            "detected": detected,
            "pattern": pattern,
            "squeeze_duration": squeeze_duration,
            "expansion_strength": float(expansion_strength),
            "breakout_likely": breakout_likely,
            "confidence": float(confidence),
        }

        self.logger.debug(f"BB squeeze detection: {result}")
        return result

    def detect_volume_trend(self, volume_series: list | np.ndarray) -> dict:
        """Detect volume trend (spike, increasing, decreasing, or stable).

        Analyzes volume patterns to identify significant changes that may
        confirm price movements or indicate potential reversals.

        Args:
            volume_series: List/array of volume values

        Returns:
            Dictionary with volume trend info:
            {
                'detected': bool,
                'trend': str,  # 'spike', 'increasing', 'decreasing', 'stable'
                'spike_detected': bool,
                'spike_magnitude': float,
                'rate': float,
                'significance': str,  # 'critical', 'high', 'medium', 'low'
                'confidence': float
            }
        """
        if not volume_series or len(volume_series) < 5:
            return {"detected": False, "reason": "Insufficient data (< 5 periods)"}

        volume_arr = np.array(volume_series, dtype=np.float64)
        recent_vol = volume_arr[-5:]

        current_vol = float(recent_vol[-1])
        avg_vol = float(np.mean(volume_arr[-20:]))
        recent_avg = float(np.mean(recent_vol[:-1]))

        # Check for spike
        spike_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
        spike_detected = spike_ratio > 3.0

        if spike_detected:
            trend = "spike"
            rate = (current_vol - avg_vol) / avg_vol if avg_vol > 0 else 0
            significance = "critical"
            confidence = min(spike_ratio / 5.0, 1.0)
            detected = True
        else:
            # Calculate trend: linear regression on last 10 periods
            if len(volume_arr) >= 10:
                vol_10 = volume_arr[-10:]
                x = np.arange(len(vol_10))
                slope = np.polyfit(x, vol_10, 1)[0]
                rate = slope / avg_vol if avg_vol > 0 else 0
            else:
                rate = (current_vol - recent_avg) / recent_avg if recent_avg > 0 else 0

            # Classify trend
            if rate > 0.1:  # >10% increase
                trend = "increasing"
                significance = "high" if rate > 0.15 else "medium"
                confidence = min(rate, 1.0)
                detected = True
            elif rate < -0.05:  # <-5% decrease
                trend = "decreasing"
                significance = "medium"
                confidence = min(abs(rate), 1.0)
                detected = False
            else:
                trend = "stable"
                significance = "low"
                confidence = 0.3
                detected = False

        result = {
            "detected": detected,
            "trend": trend,
            "spike_detected": spike_detected,
            "spike_magnitude": float(spike_ratio),
            "rate": float(rate),
            "significance": significance,
            "confidence": float(confidence),
        }

        self.logger.debug(f"Volume trend detection: {result}")
        return result

    def detect_macd_divergence(
        self, macd_series: list | np.ndarray, price_series: list | np.ndarray
    ) -> dict:
        """Detect MACD convergence/divergence with price.

        Identifies divergences between price movement and MACD indicator,
        which can signal potential reversals.

        Args:
            macd_series: List/array of MACD values
            price_series: List/array of closing prices

        Returns:
            Dictionary with divergence info:
            {
                'detected': bool,
                'divergence_type': str,  # 'bullish', 'bearish', 'none'
                'confidence': float,
                'strength': float
            }
        """
        if not macd_series or not price_series or len(macd_series) < 10 or len(price_series) < 10:
            return {
                "detected": False,
                "reason": "Insufficient data (< 10 periods)",
            }

        macd_arr = np.array(macd_series, dtype=np.float64)
        price_arr = np.array(price_series, dtype=np.float64)

        # Use last 10 periods
        macd_10 = macd_arr[-10:]
        price_10 = price_arr[-10:]

        # Calculate slopes
        x = np.arange(len(macd_10))
        macd_slope = np.polyfit(x, macd_10, 1)[0]
        price_slope = np.polyfit(x, price_10, 1)[0]

        # Detect divergence
        # Bullish divergence: price declining, MACD increasing
        if price_slope < 0 and macd_slope > 0:
            divergence_type = "bullish"
            detected = True
            strength = abs(macd_slope) / max(abs(price_slope), 0.1)
            confidence = min(strength / 2.0, 1.0)
        # Bearish divergence: price increasing, MACD declining
        elif price_slope > 0 and macd_slope < 0:
            divergence_type = "bearish"
            detected = True
            strength = abs(macd_slope) / max(abs(price_slope), 0.1)
            confidence = min(strength / 2.0, 1.0)
        else:
            divergence_type = "none"
            detected = False
            strength = 0.0
            confidence = 0.0

        result = {
            "detected": detected,
            "divergence_type": divergence_type,
            "confidence": float(confidence),
            "strength": float(strength),
        }

        self.logger.debug(f"MACD divergence detection: {result}")
        return result

    def detect_stochastic_pattern(
        self, stoch_k: list | np.ndarray, stoch_d: list | np.ndarray
    ) -> dict:
        """Detect stochastic crossover patterns.

        Identifies %K crossing %D in oversold/overbought zones which can
        signal potential trend changes.

        Args:
            stoch_k: List/array of %K values
            stoch_d: List/array of %D values

        Returns:
            Dictionary with crossover info:
            {
                'detected': bool,
                'crossover_type': str,  # 'oversold_bullish', 'overbought_bearish', 'none'
                'crossover_level': float,
                'confidence': float
            }
        """
        if not stoch_k or not stoch_d or len(stoch_k) < 3 or len(stoch_d) < 3:
            return {
                "detected": False,
                "reason": "Insufficient data (< 3 periods)",
            }

        k_arr = np.array(stoch_k, dtype=np.float64)
        d_arr = np.array(stoch_d, dtype=np.float64)

        # Get last 3 values to detect crossover
        k_recent = k_arr[-3:]
        d_recent = d_arr[-3:]

        # Current values
        k_curr = float(k_recent[-1])
        d_curr = float(d_recent[-1])
        k_prev = float(k_recent[-2])
        d_prev = float(d_recent[-2])

        # Detect crossover
        k_crossed_d = (k_prev <= d_prev) and (k_curr > d_curr)  # Bullish crossover
        d_crossed_k = (d_prev <= k_prev) and (d_curr > k_curr)  # Bearish crossover

        if k_crossed_d and k_curr < 20:
            # Oversold bullish crossover
            crossover_type = "oversold_bullish"
            crossover_level = float(k_curr)
            detected = True
            confidence = min((20.0 - k_curr) / 20.0, 1.0)
        elif d_crossed_k and k_curr > 80:
            # Overbought bearish crossover
            crossover_type = "overbought_bearish"
            crossover_level = float(k_curr)
            detected = True
            confidence = min((k_curr - 80.0) / 20.0, 1.0)
        else:
            crossover_type = "none"
            crossover_level = float(k_curr)
            detected = False
            confidence = 0.0

        result = {
            "detected": detected,
            "crossover_type": crossover_type,
            "crossover_level": crossover_level,
            "confidence": float(confidence),
        }

        self.logger.debug(f"Stochastic pattern detection: {result}")
        return result

    def detect_consolidation(self, price_series: list | np.ndarray, min_duration: int = 7) -> dict:
        """Detect consolidation (range-bound) periods before breakouts.

        Identifies periods where price trades in a tight range, which often
        precedes significant breakouts. Also detects breakouts from consolidation.

        Args:
            price_series: List/array of closing prices
            min_duration: Minimum periods for consolidation detection (default 7)

        Returns:
            Dictionary with consolidation info:
            {
                'detected': bool,
                'is_consolidating': bool,
                'duration': int,
                'range_min': float,
                'range_max': float,
                'range_width': float,
                'range_width_pct': float,
                'breakout_detected': bool,
                'breakout_direction': str,  # 'up', 'down', 'none'
                'confidence': float
            }
        """
        if not price_series or len(price_series) < min_duration + 2:
            return {
                "detected": False,
                "reason": f"Insufficient data (< {min_duration + 2} periods)",
            }

        price_arr = np.array(price_series, dtype=np.float64)

        # Check last min_duration periods for consolidation
        recent_prices = price_arr[-min_duration:]
        range_min = float(np.min(recent_prices))
        range_max = float(np.max(recent_prices))
        range_width = range_max - range_min
        range_width_pct = (range_width / range_min * 100) if range_min > 0 else 0

        # Consolidation: tight range (< 5% width)
        is_consolidating = range_width_pct < 5.0

        # Check for breakout: current price outside recent range
        current_price = float(price_arr[-1])
        breakout_detected = False
        breakout_direction = "none"

        if current_price > range_max:
            # Upside breakout
            breakout_detected = True
            breakout_direction = "up"
            detected = True
        elif current_price < range_min:
            # Downside breakout
            breakout_detected = True
            breakout_direction = "down"
            detected = True
        else:
            detected = is_consolidating

        # Calculate duration of consolidation
        # Find how many periods back maintained tight range
        consolidation_duration = 0
        if is_consolidating:
            for i in range(len(price_arr) - 1, -1, -1):
                check_window = price_arr[max(0, i - min_duration) : i + 1]
                if len(check_window) < 2:
                    break
                w = float(np.max(check_window)) - float(np.min(check_window))
                w_pct = (w / float(np.min(check_window)) * 100) if np.min(check_window) > 0 else 100
                if w_pct < 5.0:
                    consolidation_duration = len(price_arr) - i
                else:
                    break

        # Confidence scoring
        if breakout_detected:
            # Breakout strength
            if breakout_direction == "up":
                breakout_strength = (
                    (current_price - range_max) / range_width if range_width > 0 else 0
                )
            else:
                breakout_strength = (
                    (range_min - current_price) / range_width if range_width > 0 else 0
                )
            confidence = min(breakout_strength, 1.0)
        else:
            # Consolidation confidence based on how tight the range is
            confidence = 1.0 - (range_width_pct / 5.0) if range_width_pct < 5.0 else 0.0
            confidence = min(confidence, 1.0)

        result = {
            "detected": detected,
            "is_consolidating": is_consolidating,
            "duration": consolidation_duration,
            "range_min": range_min,
            "range_max": range_max,
            "range_width": float(range_width),
            "range_width_pct": float(range_width_pct),
            "breakout_detected": breakout_detected,
            "breakout_direction": breakout_direction,
            "confidence": float(confidence),
        }

        self.logger.debug(f"Consolidation detection: {result}")
        return result

    def calculate_trend_quality(
        self, price_series: list | np.ndarray, lookback_days: int = 90
    ) -> dict:
        """Calculate trend quality using R² (coefficient of determination).

        Measures the reliability of a trend using linear regression to
        determine how well prices follow the trend line.

        Args:
            price_series: List/array of closing prices
            lookback_days: Number of days for trend calculation (default 90)

        Returns:
            Dictionary with trend quality info:
            {
                'detected': bool,
                'r_squared': float,
                'trend_quality_score': float,  # 0-1
                'trend_direction': str,  # 'up', 'down', 'flat'
                'slope': float,
                'regression_line': [float],  # Fitted line values
                'confidence': float
            }
        """
        if not price_series or len(price_series) < lookback_days:
            return {
                "detected": False,
                "reason": f"Insufficient data (< {lookback_days} periods)",
            }

        price_arr = np.array(price_series[-lookback_days:], dtype=np.float64)

        # Linear regression
        x = np.arange(len(price_arr))
        coeffs = np.polyfit(x, price_arr, 1)
        slope = float(coeffs[0])

        # Calculate R² (coefficient of determination)
        y_fit = coeffs[0] * x + coeffs[1]
        ss_res = np.sum((price_arr - y_fit) ** 2)
        ss_tot = np.sum((price_arr - np.mean(price_arr)) ** 2)
        r_squared = float(1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0)

        # Clamp R² between 0 and 1
        r_squared = max(0.0, min(1.0, r_squared))

        # Quality score based on R²
        if r_squared > 0.7:
            trend_quality_score = 0.9
        elif r_squared > 0.4:
            trend_quality_score = 0.6
        else:
            trend_quality_score = 0.3

        # Trend direction
        if abs(slope) < 0.0001:  # Essentially flat
            trend_direction = "flat"
            detected = False
        elif slope > 0:
            trend_direction = "up"
            detected = True
        else:
            trend_direction = "down"
            detected = True

        # Confidence based on R²
        confidence = r_squared

        result = {
            "detected": detected,
            "r_squared": r_squared,
            "trend_quality_score": trend_quality_score,
            "trend_direction": trend_direction,
            "slope": slope,
            "regression_line": y_fit.tolist(),
            "confidence": confidence,
        }

        self.logger.debug(f"Trend quality calculation: {result}")
        return result

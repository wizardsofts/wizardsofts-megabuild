#!/usr/bin/env python3
"""Unit tests for indicator calculations in backfill_indicators.py."""

import unittest
from datetime import date
from backfill_indicators import (
    sma, ema, rsi, macd, obv, bollinger, atr, volume_ratio,
    volume_sma, money_flow_index, accumulation_distribution, chaikin_money_flow,
    log_return, high_low_range, close_open_diff, temporal_features,
    compute_all_indicators
)


class TestMovingAverages(unittest.TestCase):
    """Test SMA and EMA calculations."""

    def test_sma_basic(self):
        """Test SMA with basic data."""
        close = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = sma(close, 3)
        expected = (12.0 + 13.0 + 14.0) / 3
        self.assertAlmostEqual(result, expected, places=6)

    def test_sma_insufficient_data(self):
        """Test SMA returns None with insufficient data."""
        close = [10.0, 11.0]
        result = sma(close, 5)
        self.assertIsNone(result)

    def test_ema_basic(self):
        """Test EMA calculation."""
        close = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        result = ema(close, 3)
        self.assertIsNotNone(result)
        # EMA should be close to recent prices, above SMA for uptrend
        self.assertGreater(result, 13.0)

    def test_ema_insufficient_data(self):
        """Test EMA returns None with insufficient data."""
        close = [10.0, 11.0]
        result = ema(close, 5)
        self.assertIsNone(result)


class TestMomentum(unittest.TestCase):
    """Test RSI and MACD calculations."""

    def test_rsi_basic(self):
        """Test RSI calculation."""
        # Uptrend data should give RSI > 50
        close = [i * 1.0 for i in range(1, 20)]  # 1, 2, 3, ..., 19
        result = rsi(close, 14)
        self.assertIsNotNone(result)
        self.assertEqual(result, 100.0)  # All gains, no losses

    def test_rsi_downtrend(self):
        """Test RSI in downtrend."""
        close = [i * 1.0 for i in range(20, 0, -1)]  # 20, 19, 18, ..., 1
        result = rsi(close, 14)
        self.assertIsNotNone(result)
        self.assertLess(result, 10.0)  # All losses

    def test_rsi_insufficient_data(self):
        """Test RSI returns None with insufficient data."""
        close = [10.0, 11.0, 12.0]
        result = rsi(close, 14)
        self.assertIsNone(result)

    def test_macd_basic(self):
        """Test MACD calculation returns tuple."""
        close = [float(i) for i in range(1, 50)]
        macd_line, signal_line, hist = macd(close, 12, 26, 9)
        self.assertIsNotNone(macd_line)
        self.assertIsNotNone(signal_line)
        self.assertIsNotNone(hist)
        self.assertAlmostEqual(hist, macd_line - signal_line, places=6)


class TestVolume(unittest.TestCase):
    """Test volume-related indicators."""

    def test_obv_uptrend(self):
        """Test OBV in uptrend."""
        close = [10.0, 11.0, 12.0, 13.0, 14.0]
        volume = [100.0, 200.0, 300.0, 400.0, 500.0]
        result = obv(close, volume)
        # OBV should be positive in uptrend
        expected = 200 + 300 + 400 + 500  # All up days
        self.assertEqual(result, expected)

    def test_obv_downtrend(self):
        """Test OBV in downtrend."""
        close = [14.0, 13.0, 12.0, 11.0, 10.0]
        volume = [100.0, 200.0, 300.0, 400.0, 500.0]
        result = obv(close, volume)
        # OBV should be negative in downtrend
        expected = -(200 + 300 + 400 + 500)  # All down days
        self.assertEqual(result, expected)

    def test_volume_ratio(self):
        """Test volume ratio calculation."""
        # Volume ratio uses last 20 values for average
        # With 20 at 100 + 1 at 200: avg of last 20 = (19*100+200)/20 = 105
        # ratio = 200/105 = 1.9047...
        volume = [100.0] * 20 + [200.0]
        result = volume_ratio(volume, 20)
        expected = 200.0 / ((19 * 100.0 + 200.0) / 20)
        self.assertAlmostEqual(result, expected, places=6)

    def test_volume_sma(self):
        """Test volume SMA."""
        volume = [100.0, 200.0, 300.0, 400.0, 500.0]
        result = volume_sma(volume, 5)
        expected = 300.0
        self.assertAlmostEqual(result, expected, places=6)

    def test_mfi_basic(self):
        """Test Money Flow Index."""
        high = [12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
        low = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0]
        close = [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0]
        volume = [1000.0] * 15
        result = money_flow_index(high, low, close, volume, 14)
        self.assertIsNotNone(result)
        # In uptrend, MFI should be high
        self.assertGreater(result, 50.0)

    def test_ad_line(self):
        """Test Accumulation/Distribution line."""
        high = [12.0, 13.0]
        low = [10.0, 11.0]
        close = [12.0, 13.0]  # Close at high
        volume = [1000.0, 1000.0]
        result = accumulation_distribution(high, low, close, volume)
        self.assertIsNotNone(result)
        # Close at high means positive A/D
        self.assertGreater(result, 0)

    def test_cmf_basic(self):
        """Test Chaikin Money Flow."""
        high = [12.0] * 25
        low = [10.0] * 25
        close = [12.0] * 25  # Close at high
        volume = [1000.0] * 25
        result = chaikin_money_flow(high, low, close, volume, 20)
        self.assertIsNotNone(result)
        # Close at high means positive CMF
        self.assertAlmostEqual(result, 1.0, places=6)


class TestVolatility(unittest.TestCase):
    """Test volatility indicators."""

    def test_bollinger_basic(self):
        """Test Bollinger Bands calculation."""
        close = [10.0 + i * 0.1 for i in range(30)]
        upper, middle, lower, bandwidth = bollinger(close, 20, 2.0)
        self.assertIsNotNone(upper)
        self.assertIsNotNone(middle)
        self.assertIsNotNone(lower)
        self.assertIsNotNone(bandwidth)
        self.assertGreater(upper, middle)
        self.assertGreater(middle, lower)
        self.assertGreater(bandwidth, 0)

    def test_atr_basic(self):
        """Test ATR calculation."""
        high = [12.0] * 20
        low = [10.0] * 20
        close = [11.0] * 20
        result = atr(high, low, close, 14)
        self.assertIsNotNone(result)
        # ATR should be 2.0 (high - low)
        self.assertAlmostEqual(result, 2.0, places=6)


class TestPriceFeatures(unittest.TestCase):
    """Test price-based features."""

    def test_log_return_positive(self):
        """Test positive log return."""
        import math
        close = [100.0, 110.0]
        result = log_return(close)
        expected = math.log(110.0 / 100.0)
        self.assertAlmostEqual(result, expected, places=6)

    def test_log_return_negative(self):
        """Test negative log return."""
        import math
        close = [110.0, 100.0]
        result = log_return(close)
        expected = math.log(100.0 / 110.0)
        self.assertAlmostEqual(result, expected, places=6)

    def test_high_low_range(self):
        """Test high-low range calculation."""
        high = [110.0]
        low = [90.0]
        close = [100.0]
        result = high_low_range(high, low, close)
        expected = (110.0 - 90.0) / 100.0
        self.assertAlmostEqual(result, expected, places=6)

    def test_close_open_diff(self):
        """Test close-open diff calculation."""
        close = [110.0]
        open_ = [100.0]
        result = close_open_diff(close, open_)
        expected = (110.0 - 100.0) / 100.0
        self.assertAlmostEqual(result, expected, places=6)


class TestTemporalFeatures(unittest.TestCase):
    """Test temporal feature extraction."""

    def test_day_of_week_monday(self):
        """Test day_of_week for Monday."""
        d = date(2026, 1, 5)  # Monday
        result = temporal_features(d)
        self.assertEqual(result['day_of_week'], 1)

    def test_day_of_week_friday(self):
        """Test day_of_week for Friday."""
        d = date(2026, 1, 9)  # Friday
        result = temporal_features(d)
        self.assertEqual(result['day_of_week'], 5)

    def test_month_end(self):
        """Test is_month_end detection."""
        d = date(2026, 1, 30)  # 2 days from month end
        result = temporal_features(d)
        self.assertTrue(result['is_month_end'])

    def test_quarter_end(self):
        """Test is_quarter_end detection."""
        d = date(2026, 3, 30)  # March 30, near quarter end
        result = temporal_features(d)
        self.assertTrue(result['is_quarter_end'])


class TestComputeAllIndicators(unittest.TestCase):
    """Test the full compute_all_indicators function."""

    def test_compute_all_basic(self):
        """Test compute_all_indicators with valid data."""
        price_series = {
            'open': [float(i) for i in range(100, 200)],
            'high': [float(i + 2) for i in range(100, 200)],
            'low': [float(i - 2) for i in range(100, 200)],
            'close': [float(i + 1) for i in range(100, 200)],
            'volume': [1000.0 * i for i in range(1, 101)],
        }
        trading_date = date(2026, 1, 5)

        result = compute_all_indicators(price_series, trading_date)

        # Check that all expected indicators are present
        expected_keys = [
            'SMA_3', 'SMA_5', 'SMA_20', 'SMA_50',
            'EMA_3', 'EMA_20', 'EMA_50',
            'RSI_14', 'MACD_line_12_26_9', 'MACD_signal_12_26_9', 'MACD_hist_12_26_9',
            'OBV', 'volume_ratio_20', 'volume_SMA_10', 'volume_SMA_20',
            'MFI_14', 'AD_line', 'CMF_20',
            'ATR_14',
            'BOLLINGER_upper_20_2', 'BOLLINGER_middle_20_2', 'BOLLINGER_lower_20_2', 'BOLLINGER_bandwidth_20_2',
            'log_return', 'high_low_range', 'close_open_diff',
            'day_of_week', 'week_of_month', 'month', 'is_month_end', 'is_quarter_end'
        ]

        for key in expected_keys:
            self.assertIn(key, result, f"Missing indicator: {key}")

        # Check that most indicators have values (not None)
        non_none_count = sum(1 for v in result.values() if v is not None)
        self.assertGreater(non_none_count, 25, "Too many None values")

    def test_compute_all_insufficient_data(self):
        """Test compute_all_indicators with insufficient data."""
        price_series = {
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [98.0, 99.0],
            'close': [101.0, 102.0],
            'volume': [1000.0, 1100.0],
        }

        result = compute_all_indicators(price_series)

        # Indicators requiring more data should be None
        self.assertIsNone(result['SMA_20'])
        self.assertIsNone(result['RSI_14'])
        self.assertIsNone(result['MACD_line_12_26_9'])

        # Basic features should still work
        self.assertIsNotNone(result['log_return'])


if __name__ == '__main__':
    unittest.main()

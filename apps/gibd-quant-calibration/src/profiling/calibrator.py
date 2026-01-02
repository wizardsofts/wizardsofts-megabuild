"""Stock-specific threshold calibration from historical data.

This module provides the StockCalibrator class for analyzing historical
stock data to determine optimal RSI thresholds, volume characteristics,
volatility categories, and support/resistance levels.

The calibration process:
1. Analyzes 365 days of historical data
2. Identifies price reversal points (peaks and troughs)
3. Calculates adaptive RSI thresholds from reversals
4. Determines typical volume and spike thresholds
5. Categorizes volatility based on ATR
6. Clusters support and resistance levels
7. Stores results in stock_profiles table
"""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session

from src.database.connection import get_db_context
from src.database.models import StockProfile, WsDseDailyPrice

logger = logging.getLogger(__name__)


class StockCalibrator:
    """Base class for stock-specific threshold calibration.

    Analyzes historical reversals to find optimal RSI/MACD thresholds,
    volume characteristics, volatility categories, and key price levels.

    Example:
        calibrator = StockCalibrator()
        profile = calibrator.calibrate_stock('GP')
        print(f"RSI oversold: {profile.rsi_oversold}")
        print(f"RSI overbought: {profile.rsi_overbought}")
    """

    def __init__(self, lookback_days: int = 365):
        """Initialize stock calibrator.

        Args:
            lookback_days: Number of historical days to analyze (default: 365)
        """
        self.lookback_days = lookback_days
        logger.info(f"StockCalibrator initialized with {lookback_days} day lookback")

    def calibrate_stock(self, ticker: str, session: Session | None = None) -> StockProfile | None:
        """Calibrate stock-specific thresholds from historical data.

        Complete workflow:
        1. Fetch 365 days of data
        2. Find reversals
        3. Calculate RSI thresholds
        4. Calculate volume metrics
        5. Determine volatility category
        6. Find support/resistance levels
        7. Get sector from mapping
        8. Create StockProfile object
        9. Upsert to database

        Args:
            ticker: Stock ticker symbol (e.g., 'GP', 'SQURPHARMA')
            session: Optional database session (creates new if None)

        Returns:
            StockProfile object if successful, None if insufficient data

        Raises:
            ValueError: If ticker not found in database
        """
        own_session = session is None

        try:
            if own_session:
                with get_db_context() as sess:
                    return self._calibrate_with_session(ticker, sess)
            else:
                return self._calibrate_with_session(ticker, session)
        except Exception as e:
            logger.error(f"Calibration failed for {ticker}: {e}")
            return None

    def _calibrate_with_session(self, ticker: str, session: Session) -> StockProfile | None:
        """Internal calibration implementation with provided session.

        Args:
            ticker: Stock ticker symbol
            session: Database session

        Returns:
            StockProfile object if successful, None if insufficient data
        """
        logger.info(f"Starting calibration for {ticker}")

        # 1. Fetch historical data from GIBD
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.lookback_days)

        data = (
            session.query(WsDseDailyPrice)
            .filter(
                WsDseDailyPrice.txn_scrip == ticker,
                WsDseDailyPrice.txn_date >= start_date,
                WsDseDailyPrice.txn_date <= end_date,
            )
            .order_by(WsDseDailyPrice.txn_date)
            .all()
        )

        if len(data) < 100:
            logger.warning(
                f"Insufficient data for {ticker}: {len(data)} days " f"(minimum 100 required)"
            )
            return None

        logger.info(f"Loaded {len(data)} days of data for {ticker}")

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(
            [
                {
                    "date": row.txn_date,
                    "open": float(row.txn_open),
                    "high": float(row.txn_high),
                    "low": float(row.txn_low),
                    "close": float(row.txn_close),
                    "volume": int(row.txn_volume),
                }
                for row in data
            ]
        )

        # 3. Find reversals
        reversals = self._find_reversals(df["close"])

        if len(reversals["peaks"]) < 3 or len(reversals["troughs"]) < 3:
            logger.warning(
                f"Insufficient reversals for {ticker}: "
                f"{len(reversals['peaks'])} peaks, {len(reversals['troughs'])} troughs"
            )
            return None

        # 4. Calculate RSI for threshold determination
        # We'll need RSI values at reversal points
        rsi_values = self._calculate_rsi(df["close"])
        df["rsi"] = rsi_values

        # 5. Calculate adaptive RSI thresholds
        rsi_overbought, rsi_oversold = self._calculate_rsi_thresholds(df, reversals)

        # 6. Calculate volume metrics
        volume_metrics = self._calculate_volume_metrics(df["volume"])

        # 7. Determine volatility category
        volatility_category = self._determine_volatility_category(df)

        # 8. Find support/resistance levels
        sr_levels = self._find_support_resistance(
            df["close"], reversals, df["close"].iloc[-1]  # Current price
        )

        # 9. Get or create stock profile
        profile = session.query(StockProfile).filter_by(ticker=ticker).first()

        if profile is None:
            profile = StockProfile(ticker=ticker)
            session.add(profile)

        # 10. Update profile fields
        profile.volatility_category = volatility_category
        profile.rsi_overbought = rsi_overbought
        profile.rsi_oversold = rsi_oversold
        profile.typical_volume = volume_metrics["median"]
        profile.high_volume_threshold = volume_metrics["spike_threshold"]
        profile.support_levels = sr_levels["support"]
        profile.resistance_levels = sr_levels["resistance"]
        profile.last_calibrated_at = datetime.utcnow()
        profile.calibration_period_days = len(data)

        session.commit()

        logger.info(
            f"Calibration complete for {ticker}: "
            f"RSI ({rsi_oversold:.1f}/{rsi_overbought:.1f}), "
            f"Volatility: {volatility_category}, "
            f"Support levels: {len(sr_levels['support'])}, "
            f"Resistance levels: {len(sr_levels['resistance'])}"
        )

        return profile

    def _find_reversals(self, price_series: pd.Series, order: int = 5) -> dict[str, list[int]]:
        """Find local peaks and troughs in price series.

        Uses scipy.signal.argrelextrema to identify local extrema.
        A peak is a local maximum where the price is higher than
        the surrounding `order` prices on both sides.

        Args:
            price_series: Price time series (typically close prices)
            order: Number of points on each side to compare (default: 5)

        Returns:
            Dict with 'peaks' and 'troughs' lists containing indices

        Example:
            >>> prices = pd.Series([100, 105, 110, 105, 100, 105, 110])
            >>> reversals = calibrator._find_reversals(prices, order=2)
            >>> reversals
            {'peaks': [2, 6], 'troughs': [4]}
        """
        # Convert to numpy array
        prices = price_series.values

        # Find local maxima (peaks)
        peak_indices = argrelextrema(prices, np.greater, order=order)[0]

        # Find local minima (troughs)
        trough_indices = argrelextrema(prices, np.less, order=order)[0]

        logger.debug(f"Found {len(peak_indices)} peaks and {len(trough_indices)} troughs")

        return {"peaks": peak_indices.tolist(), "troughs": trough_indices.tolist()}

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index).

        Standard RSI calculation:
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss over period

        Args:
            prices: Price series
            period: RSI period (default: 14)

        Returns:
            RSI series (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_thresholds(
        self, data: pd.DataFrame, reversals: dict[str, list[int]]
    ) -> tuple[float, float]:
        """Calculate stock-specific RSI overbought/oversold levels.

        Determines adaptive thresholds by analyzing RSI at reversal points:
        - Overbought = median RSI at peaks (price tops)
        - Oversold = median RSI at troughs (price bottoms)

        Args:
            data: DataFrame with 'rsi' column
            reversals: Dict with 'peaks' and 'troughs' indices

        Returns:
            Tuple of (rsi_overbought, rsi_oversold)

        Raises:
            ValueError: If fewer than 5 reversals in either direction
        """
        peaks = reversals["peaks"]
        troughs = reversals["troughs"]

        if len(peaks) < 5:
            raise ValueError(
                f"Insufficient peaks for RSI calibration: {len(peaks)} " f"(minimum 5 required)"
            )

        if len(troughs) < 5:
            raise ValueError(
                f"Insufficient troughs for RSI calibration: {len(troughs)} " f"(minimum 5 required)"
            )

        # Get RSI values at peaks and troughs
        peak_rsi = data.iloc[peaks]["rsi"].dropna()
        trough_rsi = data.iloc[troughs]["rsi"].dropna()

        # Use median for robustness against outliers
        rsi_overbought = float(peak_rsi.median())
        rsi_oversold = float(trough_rsi.median())

        # Validate thresholds are reasonable
        if not (30 <= rsi_oversold <= 50):
            logger.warning(
                f"Unusual RSI oversold threshold: {rsi_oversold:.1f}, "
                f"clamping to range [30, 50]"
            )
            rsi_oversold = max(30, min(50, rsi_oversold))

        if not (50 <= rsi_overbought <= 80):
            logger.warning(
                f"Unusual RSI overbought threshold: {rsi_overbought:.1f}, "
                f"clamping to range [50, 80]"
            )
            rsi_overbought = max(50, min(80, rsi_overbought))

        logger.debug(
            f"RSI thresholds: oversold={rsi_oversold:.1f}, " f"overbought={rsi_overbought:.1f}"
        )

        return rsi_overbought, rsi_oversold

    def _calculate_volume_metrics(self, volume_series: pd.Series) -> dict[str, int]:
        """Calculate typical volume metrics.

        Determines stock-specific volume characteristics:
        - Typical volume (median of recent 90 days)
        - Volume 90th percentile (spike threshold)
        - Volume volatility (std dev)

        Args:
            volume_series: Volume time series

        Returns:
            Dict with 'median', 'percentile_90', 'spike_threshold'
        """
        # Use last 90 days for typical volume
        recent_volume = volume_series.tail(90)

        median_vol = int(recent_volume.median())
        percentile_90 = int(recent_volume.quantile(0.9))

        # Spike threshold is ratio of 90th percentile to median
        spike_threshold = percentile_90 / median_vol if median_vol > 0 else 2.0

        logger.debug(
            f"Volume metrics: median={median_vol:,}, "
            f"p90={percentile_90:,}, spike_threshold={spike_threshold:.2f}x"
        )

        return {
            "median": median_vol,
            "percentile_90": percentile_90,
            "spike_threshold": spike_threshold,
        }

    def _determine_volatility_category(self, data: pd.DataFrame, period: int = 14) -> str:
        """Classify stocks by volatility level.

        Uses ATR (Average True Range) / price ratio:
        - < 0.02 → "low"
        - 0.02-0.04 → "medium"
        - > 0.04 → "high"

        Args:
            data: DataFrame with OHLC data
            period: ATR calculation period (default: 14)

        Returns:
            Volatility category: "low", "medium", or "high"
        """
        # Calculate True Range
        high = data["high"]
        low = data["low"]
        close = data["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR (simple moving average of TR)
        atr = tr.rolling(window=period).mean()

        # Get recent ATR/price ratio (last 90 days average)
        recent_atr = atr.tail(90).mean()
        recent_price = close.tail(90).mean()

        atr_ratio = recent_atr / recent_price if recent_price > 0 else 0.03

        # Categorize
        if atr_ratio < 0.02:
            category = "low"
        elif atr_ratio < 0.04:
            category = "medium"
        else:
            category = "high"

        logger.debug(f"Volatility: ATR/price={atr_ratio:.4f}, category={category}")

        return category

    def _find_support_resistance(
        self,
        price_series: pd.Series,
        reversals: dict[str, list[int]],
        current_price: float,
        eps_pct: float = 0.02,
    ) -> dict[str, list[float]]:
        """Find key support and resistance levels using DBSCAN clustering.

        Clusters similar reversal price levels to identify key S/R zones:
        1. Collect all reversal price levels
        2. Cluster similar levels using DBSCAN (eps = 2% of price)
        3. Find cluster centers
        4. Split into support (below current) and resistance (above current)
        5. Return top 3 of each

        Args:
            price_series: Price time series
            reversals: Dict with 'peaks' and 'troughs' indices
            current_price: Current stock price
            eps_pct: DBSCAN epsilon as percentage of price (default: 0.02 = 2%)

        Returns:
            Dict with 'support' and 'resistance' lists (each max 3 levels)
        """
        # Collect all reversal prices
        peaks = reversals["peaks"]
        troughs = reversals["troughs"]

        reversal_prices = []
        reversal_prices.extend(price_series.iloc[peaks].values)
        reversal_prices.extend(price_series.iloc[troughs].values)

        if len(reversal_prices) < 3:
            logger.warning("Insufficient reversals for S/R clustering")
            return {"support": [], "resistance": []}

        # Prepare data for clustering
        x = np.array(reversal_prices).reshape(-1, 1)

        # DBSCAN clustering
        # eps is 2% of average price
        avg_price = np.mean(reversal_prices)
        eps = eps_pct * avg_price

        clustering = DBSCAN(eps=eps, min_samples=2).fit(x)
        labels = clustering.labels_

        # Find cluster centers
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # Remove noise points

        cluster_centers = []
        for label in unique_labels:
            cluster_points = x[labels == label]
            center = float(np.mean(cluster_points))
            cluster_centers.append(center)

        # Sort cluster centers
        cluster_centers.sort()

        # Split into support (below current) and resistance (above current)
        support = [level for level in cluster_centers if level < current_price]
        resistance = [level for level in cluster_centers if level > current_price]

        # Take top 3 closest to current price
        support = sorted(support, reverse=True)[:3]  # Closest below
        resistance = sorted(resistance)[:3]  # Closest above

        logger.debug(
            f"S/R levels: {len(support)} support, {len(resistance)} resistance "
            f"(from {len(cluster_centers)} clusters)"
        )

        return {"support": support, "resistance": resistance}

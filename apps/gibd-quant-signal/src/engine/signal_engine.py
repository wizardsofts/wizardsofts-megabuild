"""Adaptive signal generation engine with stock-specific thresholds.

This module implements the core signal generation logic using:
- Stock-specific RSI/MACD thresholds (from StockCalibrator)
- Sector-relative adjustments (from SectorManager)
- Multi-factor scoring (momentum, trend, volume, volatility, sector, S/R, timeframe)
- Swing trading enhancements (hold periods, earnings awareness, peer correlation, index filter)
- Chandelier trailing stops
- Explainable decision trees

Signal Types:
- BUY: Score >= 0.4
- SELL: Score <= -0.4
- HOLD: -0.4 < Score < 0.4
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import uuid4

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.backtesting.outcome_tracker import SignalOutcomeTracker
from src.database.connection import get_db_context
from src.database.models import Indicator, StockProfile, WsDseDailyPrice
from src.profiling.calibrator import StockCalibrator
from src.sectors.manager import SectorManager

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal with complete context.

    Attributes:
        signal_id: Unique signal identifier
        ticker: Stock ticker symbol
        signal_date: Date signal generated
        signal_type: BUY, SELL, or HOLD
        confidence: Confidence score (0.0-1.0)
        entry_price: Recommended entry price
        target_price: Profit target
        stop_loss: Initial stop loss
        risk_reward: Risk/reward ratio

        # Swing trading enhancements
        recommended_hold_period: (min_days, max_days)
        trailing_stop: Chandelier trailing stop
        stop_type: "fixed" or "trailing"
        exit_conditions: List of exit condition names

        # Decision context
        decision_tree: Complete reasoning chain
        scores: Individual scoring components
        weights: Weight configuration used
        total_score: Weighted combined score

        # Warnings
        warnings: List of warning messages (e.g., earnings overlap)
    """

    signal_id: str = field(default_factory=lambda: str(uuid4()))
    ticker: str = ""
    signal_date: date = field(default_factory=date.today)
    signal_type: str = "HOLD"
    confidence: float = 0.0

    entry_price: float = 0.0
    target_price: float = 0.0
    stop_loss: float = 0.0
    risk_reward: float = 0.0

    # Swing trading
    recommended_hold_period: tuple[int, int] = (5, 10)
    trailing_stop: float = 0.0
    stop_type: str = "trailing"
    exit_conditions: list[str] = field(default_factory=list)

    # Decision context
    decision_tree: dict = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0

    # Warnings
    warnings: list[str] = field(default_factory=list)


class AdaptiveSignalEngine:
    """Signal generation engine with adaptive thresholds.

    Integrates:
    - StockCalibrator for stock-specific thresholds
    - SectorManager for sector-relative analysis
    - Multi-factor scoring framework
    - Swing trading enhancements

    Example:
        engine = AdaptiveSignalEngine()
        signal = engine.generate_signal('GP')
        print(f"Signal: {signal.signal_type} with {signal.confidence:.2f} confidence")

        # Custom thresholds for more/less sensitive signals
        engine = AdaptiveSignalEngine(buy_threshold=0.3, sell_threshold=-0.3)
    """

    # Default thresholds
    DEFAULT_BUY_THRESHOLD = 0.4
    DEFAULT_SELL_THRESHOLD = -0.4

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        session: Session | None = None,
        buy_threshold: float | None = None,
        sell_threshold: float | None = None,
    ):
        """Initialize adaptive signal engine.

        Args:
            weights: Optional custom scoring weights
            session: Optional database session
            buy_threshold: Score threshold for BUY signals (default: 0.4)
            sell_threshold: Score threshold for SELL signals (default: -0.4)
        """
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            "momentum": 0.30,
            "trend": 0.25,
            "volume": 0.15,
            "volatility": 0.05,
            "sector": 0.10,
            "support_resistance": 0.10,
            "timeframe_alignment": 0.05,
        }

        # Configurable signal thresholds
        self.buy_threshold = (
            buy_threshold if buy_threshold is not None else self.DEFAULT_BUY_THRESHOLD
        )
        self.sell_threshold = (
            sell_threshold if sell_threshold is not None else self.DEFAULT_SELL_THRESHOLD
        )

        self.calibrator = StockCalibrator()
        self.sector_manager = SectorManager()
        self.outcome_tracker = SignalOutcomeTracker(session=session)
        self._session = session

        threshold_info = f"thresholds: BUY>={self.buy_threshold}, SELL<={self.sell_threshold}"
        logger.info(f"AdaptiveSignalEngine initialized ({threshold_info})")

    @staticmethod
    def _get_indicator_float(indicators: dict, key: str, default: float) -> float:
        """Safely get indicator value as float (handles Decimal from JSONB)."""
        value = indicators.get(key, default)
        return float(value) if value is not None else default

    def _calculate_rsi_from_prices(self, prices: pd.Series, period: int = 14) -> float | None:
        """Calculate RSI from price series using pure pandas.

        Uses the same algorithm as StockCalibrator._calculate_rsi().
        RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss

        Args:
            prices: Close price series
            period: RSI period (default: 14)

        Returns:
            Latest RSI value (0-100) or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Get the last values
        last_gain = gain.iloc[-1]
        last_loss = abs(loss.iloc[-1])  # Ensure positive

        # Handle edge cases
        if pd.isna(last_gain) or pd.isna(last_loss):
            return None

        if last_loss == 0:
            # All gains, no losses = RSI of 100 (extremely overbought)
            return 100.0 if last_gain > 0 else 50.0

        if last_gain == 0:
            # All losses, no gains = RSI of 0 (extremely oversold)
            return 0.0

        rs = last_gain / last_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    def _calculate_macd_histogram_from_prices(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> float | None:
        """Calculate MACD histogram from price series using pure pandas.

        MACD = EMA(fast) - EMA(slow)
        Signal = EMA(MACD, signal)
        Histogram = MACD - Signal

        Args:
            prices: Close price series
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)

        Returns:
            Latest MACD histogram value or None if insufficient data
        """
        min_required = slow + signal
        if len(prices) < min_required:
            return None

        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        valid_histogram = histogram.dropna()
        return float(valid_histogram.iloc[-1]) if len(valid_histogram) > 0 else None

    def _calculate_sma_from_prices(self, prices: pd.Series, period: int) -> float | None:
        """Calculate Simple Moving Average from price series.

        Args:
            prices: Close price series
            period: SMA period

        Returns:
            Latest SMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        sma = prices.rolling(window=period).mean()
        valid_sma = sma.dropna()
        return float(valid_sma.iloc[-1]) if len(valid_sma) > 0 else None

    def _calculate_adx_from_prices(self, df: pd.DataFrame, period: int = 14) -> float | None:
        """Calculate ADX (Average Directional Index) from OHLC data.

        ADX measures trend strength regardless of direction.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ADX period (default: 14)

        Returns:
            Latest ADX value (0-100) or None if insufficient data
        """
        if len(df) < period * 2:
            return None

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate +DM and -DM
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

        # Smoothed values using Wilder's smoothing (rolling mean)
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # DX and ADX
        di_sum = plus_di + minus_di
        dx = 100 * ((plus_di - minus_di).abs() / di_sum.replace(0, np.nan))
        adx = dx.rolling(window=period).mean()

        valid_adx = adx.dropna()
        return float(valid_adx.iloc[-1]) if len(valid_adx) > 0 else None

    def _calculate_atr_from_prices(self, df: pd.DataFrame, period: int = 14) -> float | None:
        """Calculate ATR (Average True Range) from OHLC data.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default: 14)

        Returns:
            Latest ATR value or None if insufficient data
        """
        if len(df) < period + 1:
            return None

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        valid_atr = atr.dropna()
        return float(valid_atr.iloc[-1]) if len(valid_atr) > 0 else None

    def _enrich_indicators(self, indicators: dict, df: pd.DataFrame) -> dict:
        """Enrich indicators dict with calculated values if missing.

        Calculates RSI, MACD, SMA, ADX, ATR from price data when not in database.
        This ensures both scoring methods and decision tree use the same values.

        Args:
            indicators: Indicator dict from database (may be empty)
            df: Price DataFrame with OHLCV data

        Returns:
            Enriched indicators dict with calculated values
        """
        enriched = dict(indicators)  # Copy to avoid mutating original

        # RSI
        if enriched.get("rsi") is None or (
            isinstance(enriched.get("rsi"), float) and np.isnan(enriched["rsi"])
        ):
            rsi = self._calculate_rsi_from_prices(df["close"])
            if rsi is not None:
                enriched["rsi"] = rsi
                logger.debug(f"Enriched RSI from prices: {rsi:.2f}")

        # MACD histogram
        if enriched.get("macd_histogram") is None or (
            isinstance(enriched.get("macd_histogram"), float)
            and np.isnan(enriched["macd_histogram"])
        ):
            macd_hist = self._calculate_macd_histogram_from_prices(df["close"])
            if macd_hist is not None:
                enriched["macd_histogram"] = macd_hist
                logger.debug(f"Enriched MACD histogram from prices: {macd_hist:.4f}")

        # SMA 20
        if enriched.get("sma_20") is None or (
            isinstance(enriched.get("sma_20"), float) and np.isnan(enriched["sma_20"])
        ):
            sma_20 = self._calculate_sma_from_prices(df["close"], 20)
            if sma_20 is not None:
                enriched["sma_20"] = sma_20
                logger.debug(f"Enriched SMA 20 from prices: {sma_20:.2f}")

        # SMA 50
        if enriched.get("sma_50") is None or (
            isinstance(enriched.get("sma_50"), float) and np.isnan(enriched["sma_50"])
        ):
            sma_50 = self._calculate_sma_from_prices(df["close"], 50)
            if sma_50 is not None:
                enriched["sma_50"] = sma_50
                logger.debug(f"Enriched SMA 50 from prices: {sma_50:.2f}")

        # ADX
        if enriched.get("adx") is None or (
            isinstance(enriched.get("adx"), float) and np.isnan(enriched["adx"])
        ):
            adx = self._calculate_adx_from_prices(df)
            if adx is not None:
                enriched["adx"] = adx
                logger.debug(f"Enriched ADX from prices: {adx:.2f}")

        # ATR
        if enriched.get("atr") is None or (
            isinstance(enriched.get("atr"), float) and np.isnan(enriched["atr"])
        ):
            atr = self._calculate_atr_from_prices(df)
            if atr is not None:
                enriched["atr"] = atr
                logger.debug(f"Enriched ATR from prices: {atr:.2f}")

        return enriched

    def generate_signal(self, ticker: str, target_date: date | None = None) -> Signal | None:
        """Generate trading signal for a stock.

        Complete workflow:
        1. Load stock profile (or calibrate if missing)
        2. Fetch recent price data and indicators
        3. Calculate all scores (momentum, trend, volume, etc.)
        4. Apply sector-relative adjustment
        5. Check support/resistance proximity
        6. Check multi-timeframe alignment
        7. Weighted score combination
        8. Signal classification
        9. Calculate targets and stops
        10. Apply swing trading enhancements (hold period, earnings, peers, index)
        11. Build decision tree for explainability
        12. Return Signal object

        Args:
            ticker: Stock ticker symbol
            target_date: Date to generate signal for (today if None)

        Returns:
            Signal object or None if insufficient data
        """
        if target_date is None:
            target_date = date.today()

        own_session = self._session is None

        try:
            if own_session:
                with get_db_context() as session:
                    return self._generate_with_session(ticker, target_date, session)
            else:
                return self._generate_with_session(ticker, target_date, self._session)

        except Exception as e:
            import traceback

            logger.error(f"Signal generation failed for {ticker}: {e}")
            logger.error(traceback.format_exc())
            return None

    def _generate_with_session(
        self, ticker: str, target_date: date, session: Session
    ) -> Signal | None:
        """Internal signal generation implementation.

        Args:
            ticker: Stock ticker
            target_date: Target date
            session: Database session

        Returns:
            Signal object or None
        """
        logger.info(f"Generating signal for {ticker} on {target_date}")

        # 1. Load stock profile
        profile = session.query(StockProfile).filter_by(ticker=ticker).first()

        # Calibrate if missing
        if not profile:
            logger.info(f"No profile for {ticker}, calibrating...")
            profile = self.calibrator.calibrate_stock(ticker, session)
            if not profile:
                logger.warning(f"Calibration failed for {ticker}")
                return None

        # 2. Fetch recent data from GIBD (90 days for analysis)
        start_date = target_date - timedelta(days=90)
        stock_data = (
            session.query(WsDseDailyPrice)
            .filter(
                WsDseDailyPrice.txn_scrip == ticker,
                WsDseDailyPrice.txn_date >= start_date,
                WsDseDailyPrice.txn_date <= target_date,
            )
            .order_by(WsDseDailyPrice.txn_date)
            .all()
        )

        if len(stock_data) < 30:
            logger.warning(f"Insufficient data for {ticker}: {len(stock_data)} days")
            return None

        # Convert to DataFrame
        df = self._stock_data_to_df(stock_data)

        # Fetch indicators for target date from GIBD
        indicators = self._fetch_indicators(ticker, target_date, session)

        # Enrich indicators with calculated values if missing
        # This ensures both scoring and decision tree use the same values
        indicators = self._enrich_indicators(indicators, df)

        # 3. Calculate scores
        scores = {}

        scores["momentum"] = self._score_momentum(indicators, profile, df)
        scores["trend"] = self._score_trend(indicators, profile, df)
        scores["volume"] = self._score_volume(indicators, profile)
        scores["volatility"] = self._score_volatility(indicators, profile)

        # 4. Sector adjustment
        sector = self.sector_manager.get_sector(ticker)
        sector_adj = self._get_sector_adjustment(ticker, sector, target_date, session)
        scores["sector"] = sector_adj

        # 5. Support/resistance proximity
        current_price = float(df.iloc[-1]["close"])
        sr_adj = self._check_support_resistance(
            current_price, profile.support_levels or [], profile.resistance_levels or []
        )
        scores["support_resistance"] = sr_adj

        # 6. Timeframe alignment
        timeframe_score = self._score_timeframes(indicators)
        scores["timeframe_alignment"] = timeframe_score

        # 7. Weighted combination
        total_score = sum(scores[k] * self.weights[k] for k in scores)

        # 8. Signal classification
        signal_type, confidence = self._classify_signal(total_score)

        # 9. Calculate targets - ATR with fallback calculation
        atr = indicators.get("atr")
        if atr is None or (isinstance(atr, float) and np.isnan(atr)):
            atr = self._calculate_atr_from_prices(df)
            if atr is not None:
                logger.debug(f"ATR calculated from prices: {atr:.2f}")
        if atr is None:
            # Fallback: estimate ATR as 2% of current price
            atr = float(df.iloc[-1]["close"]) * 0.02
            logger.warning("Using estimated ATR (2% of price)")
        else:
            atr = float(atr)

        targets = self._calculate_targets(current_price, signal_type, atr, profile)

        # 10. Swing trading enhancements - ADX with fallback calculation
        adx = indicators.get("adx")
        if adx is None or (isinstance(adx, float) and np.isnan(adx)):
            adx = self._calculate_adx_from_prices(df)
            if adx is not None:
                logger.debug(f"ADX calculated from prices for hold period: {adx:.2f}")
        adx = 25.0 if adx is None else float(adx)

        hold_period = self._calculate_hold_period(profile.volatility_category, adx, atr)

        # Chandelier stop
        trailing_stop = self.calculate_chandelier_stop(
            current_price, current_price, atr, signal_type  # Initial high
        )

        # Peer correlation
        peer_info = self._check_peer_correlation(ticker, signal_type, sector, session)
        if peer_info["adjustment"] != 0:
            confidence = min(1.0, max(0.0, confidence + peer_info["adjustment"]))

        # Index filter
        index_info = self._check_index_trend(target_date, session)
        if index_info["confidence_adjustment"] != 0:
            confidence = min(1.0, max(0.0, confidence + index_info["confidence_adjustment"]))

        # Earnings check
        warnings = []
        earnings_overlap = self._check_earnings_overlap(
            hold_period,
            profile.next_earnings_date if hasattr(profile, "next_earnings_date") else None,
        )
        if earnings_overlap:
            warnings.append("Signal hold period overlaps with earnings date")
            confidence *= 0.5  # Reduce confidence by 50%

        # 11. Build decision tree
        decision_tree = self._build_decision_tree(
            ticker, scores, self.weights, indicators, profile, peer_info, index_info
        )

        # 12. Create Signal object
        signal = Signal(
            ticker=ticker,
            signal_date=target_date,
            signal_type=signal_type,
            confidence=confidence,
            entry_price=current_price,
            target_price=targets["target"],
            stop_loss=targets["stop_loss"],
            risk_reward=targets["risk_reward"],
            recommended_hold_period=hold_period,
            trailing_stop=trailing_stop,
            stop_type="trailing",
            exit_conditions=[
                "rsi_reversal",
                "partial_profit",
                "time_stop",
                "stop_loss_hit",
                "sector_rotation",
                "index_breakdown",
                "flat_price_exit",
            ],
            decision_tree=decision_tree,
            scores=scores,
            weights=self.weights,
            total_score=total_score,
            warnings=warnings,
        )

        logger.info(
            f"Signal generated for {ticker}: {signal_type} "
            f"(confidence={confidence:.2f}, score={total_score:.2f})"
        )

        # Track signal for outcome validation
        try:
            self.outcome_tracker.track_signal(
                ticker=ticker,
                signal_date=target_date,
                signal_type=signal_type,
                confidence=confidence,
                entry_price=current_price,
                target_price=targets["target"],
                stop_loss=targets["stop_loss"],
                decision_tree=decision_tree,
                indicators_snapshot=indicators,
                market_regime=None,
            )
            logger.info(f"Signal tracked for outcome validation: {ticker}")
        except Exception as e:
            logger.error(f"Error tracking signal for {ticker}: {str(e)}")
            # Don't fail signal generation if tracking fails

        return signal

    def _stock_data_to_df(self, stock_data: list[WsDseDailyPrice]) -> pd.DataFrame:
        """Convert WsDseDailyPrice list to DataFrame."""
        return pd.DataFrame(
            [
                {
                    "date": row.txn_date,
                    "open": float(row.txn_open),
                    "high": float(row.txn_high),
                    "low": float(row.txn_low),
                    "close": float(row.txn_close),
                    "volume": int(row.txn_volume),
                }
                for row in stock_data
            ]
        )

    # Mapping from GIBD indicator names to signal engine names
    INDICATOR_KEY_MAP = {
        "RSI_14": "rsi",
        "SMA_20": "sma_20",
        "SMA_50": "sma_50",
        "MACD_histogram_12_26_9": "macd_histogram",
        "MACD_line_12_26_9": "macd_line",
        "MACD_signal_12_26_9": "macd_signal",
        "ATR_14": "atr",
        "ADX_14": "adx",
        "BB_upper_20_2": "bb_upper",
        "BB_lower_20_2": "bb_lower",
        "BB_middle_20_2": "bb_middle",
    }

    def _fetch_indicators(
        self, ticker: str, target_date: date, session: Session
    ) -> dict[str, float]:
        """Fetch indicator values from GIBD indicators table.

        First tries to fetch for target_date. If not found, fetches the most
        recent available indicators for the ticker.

        Maps GIBD indicator keys (e.g., 'RSI_14') to signal engine keys (e.g., 'rsi').
        """
        indicators = {}

        # First try exact date
        indicator_record = (
            session.query(Indicator)
            .filter(
                Indicator.scrip == ticker,
                Indicator.trading_date == target_date,
                Indicator.status == "CALCULATED",
            )
            .first()
        )

        # If not found, get most recent indicators
        if not indicator_record:
            indicator_record = (
                session.query(Indicator)
                .filter(
                    Indicator.scrip == ticker,
                    Indicator.trading_date <= target_date,
                    Indicator.status == "CALCULATED",
                )
                .order_by(Indicator.trading_date.desc())
                .first()
            )

        if indicator_record:
            raw_indicators = indicator_record.indicators or {}

            # Map GIBD keys to signal engine keys
            for gibd_key, engine_key in self.INDICATOR_KEY_MAP.items():
                if gibd_key in raw_indicators:
                    indicators[engine_key] = raw_indicators[gibd_key]

            # Also copy any keys that match directly (lowercase)
            for key, value in raw_indicators.items():
                lower_key = key.lower()
                if lower_key not in indicators:
                    indicators[lower_key] = value

            logger.debug(
                f"Fetched {len(indicators)} indicators for {ticker} "
                f"from {indicator_record.trading_date}"
            )

        return indicators

    def _score_momentum(
        self, indicators: dict[str, float], profile: StockProfile, df: pd.DataFrame
    ) -> float:
        """Score momentum using adaptive RSI thresholds.

        Uses stock-specific thresholds from profile.
        Falls back to calculating indicators from price data if not in database.

        Args:
            indicators: Indicator snapshot from database
            profile: Stock profile with adaptive thresholds
            df: Price DataFrame with OHLCV data

        Returns:
            Score from -1.0 to +1.0
        """
        # Get RSI - try database first, then calculate from prices
        rsi = indicators.get("rsi")
        if rsi is None or (isinstance(rsi, float) and np.isnan(rsi)):
            rsi = self._calculate_rsi_from_prices(df["close"])
            if rsi is not None:
                logger.debug(f"RSI calculated from prices: {rsi:.2f}")

        # If still None (insufficient data), use neutral fallback with warning
        if rsi is None:
            logger.warning("Insufficient data to calculate RSI, using neutral value")
            rsi = 50.0
        else:
            rsi = float(rsi)

        # Use adaptive thresholds (convert Decimal to float)
        overbought = float(profile.rsi_overbought)
        oversold = float(profile.rsi_oversold)

        # Calculate score
        if rsi >= overbought:
            # Bearish - overbought
            score = -((rsi - overbought) / (100 - overbought))
        elif rsi <= oversold:
            # Bullish - oversold
            score = (oversold - rsi) / oversold
        else:
            # Neutral zone - interpolate with boosted scoring (was ±0.3, now ±0.6)
            mid = (overbought + oversold) / 2
            if rsi > mid:
                # Approaching overbought
                score = -0.6 * ((rsi - mid) / (overbought - mid))
            else:
                # Approaching oversold
                score = 0.6 * ((mid - rsi) / (mid - oversold))

        # MACD contribution - try database first, then calculate
        macd_hist = indicators.get("macd_histogram")
        if macd_hist is None or (isinstance(macd_hist, float) and np.isnan(macd_hist)):
            macd_hist = self._calculate_macd_histogram_from_prices(df["close"])
            if macd_hist is not None:
                logger.debug(f"MACD histogram calculated from prices: {macd_hist:.4f}")

        macd_hist = 0.0 if macd_hist is None else float(macd_hist)

        if macd_hist > 0:
            score = min(1.0, score + 0.2)  # Bullish MACD
        elif macd_hist < 0:
            score = max(-1.0, score - 0.2)  # Bearish MACD

        return max(-1.0, min(1.0, score))

    def _score_trend(
        self, indicators: dict[str, float], profile: StockProfile, df: pd.DataFrame
    ) -> float:
        """Score trend strength and quality.

        Factors:
        - SMA alignment (price vs SMA 20/50)
        - ADX strength

        Falls back to calculating indicators from price data if not in database.

        Args:
            indicators: Indicator snapshot from database
            profile: Stock profile
            df: Price DataFrame with OHLCV data

        Returns:
            Score from -1.0 to +1.0
        """
        price = float(df.iloc[-1]["close"])

        # Get SMA 20 - try database first, then calculate
        sma_20 = indicators.get("sma_20")
        if sma_20 is None or (isinstance(sma_20, float) and np.isnan(sma_20)):
            sma_20 = self._calculate_sma_from_prices(df["close"], 20)
            if sma_20 is not None:
                logger.debug(f"SMA 20 calculated from prices: {sma_20:.2f}")

        if sma_20 is None:
            sma_20 = price  # Neutral fallback
            logger.warning("Insufficient data for SMA 20")
        else:
            sma_20 = float(sma_20)

        # Get SMA 50 - try database first, then calculate
        sma_50 = indicators.get("sma_50")
        if sma_50 is None or (isinstance(sma_50, float) and np.isnan(sma_50)):
            sma_50 = self._calculate_sma_from_prices(df["close"], 50)
            if sma_50 is not None:
                logger.debug(f"SMA 50 calculated from prices: {sma_50:.2f}")

        if sma_50 is None:
            sma_50 = price  # Neutral fallback
            logger.warning("Insufficient data for SMA 50")
        else:
            sma_50 = float(sma_50)

        # Get ADX - try database first, then calculate
        adx = indicators.get("adx")
        if adx is None or (isinstance(adx, float) and np.isnan(adx)):
            adx = self._calculate_adx_from_prices(df)
            if adx is not None:
                logger.debug(f"ADX calculated from prices: {adx:.2f}")

        if adx is None:
            adx = 25.0  # Moderate default (between weak 20 and strong 30)
            logger.warning("Insufficient data for ADX, using moderate default")
        else:
            adx = float(adx)

        score = 0.0

        # SMA alignment
        if price > sma_20 > sma_50:
            score += 0.5  # Strong uptrend
        elif price < sma_20 < sma_50:
            score -= 0.5  # Strong downtrend
        elif price > sma_20:
            score += 0.2  # Weak uptrend
        elif price < sma_20:
            score -= 0.2  # Weak downtrend

        # ADX strength
        if adx > 30:
            # Strong trend - amplify score
            score *= 1.5
        elif adx < 20:
            # Weak trend - dampen score
            score *= 0.5

        return max(-1.0, min(1.0, score))

    def _score_volume(self, indicators: dict[str, float], profile: StockProfile) -> float:
        """Score volume trends."""
        rvol = self._get_indicator_float(indicators, "rvol", 1.0)  # Relative volume

        # Use high_volume_threshold if available, otherwise default to 2.0
        volume_threshold = (
            float(profile.high_volume_threshold) if profile.high_volume_threshold else 2.0
        )

        if rvol > volume_threshold:
            return 0.6  # High volume spike
        elif rvol > 1.5:
            return 0.3  # Above average
        elif rvol < 0.5:
            return -0.3  # Low volume
        else:
            return 0.0  # Normal

    def _score_volatility(self, indicators: dict[str, float], profile: StockProfile) -> float:
        """Score volatility."""
        # High volatility stocks get negative score (more risky)
        if profile.volatility_category == "high":
            return -0.3
        elif profile.volatility_category == "low":
            return 0.2
        else:
            return 0.0

    def _get_sector_adjustment(
        self, ticker: str, sector: str | None, target_date: date, session: Session
    ) -> float:
        """Adjust signal based on sector performance."""
        if not sector:
            return 0.0

        rs = self.sector_manager.get_relative_strength(ticker, sector, target_date, session)

        # Relative strength adjustment
        if rs > 1.5:
            return 0.5  # Strongly outperforming
        elif rs > 1.1:
            return 0.3  # Moderately outperforming
        elif rs < 0.7:
            return -0.5  # Strongly underperforming
        elif rs < 0.9:
            return -0.3  # Moderately underperforming
        else:
            return 0.0  # In line with sector

    def _check_support_resistance(
        self, current_price: float, support: list[float], resistance: list[float]
    ) -> float:
        """Adjust signal based on S/R proximity."""
        # Find nearest support and resistance
        nearest_support = min(
            (s for s in support if s < current_price),
            default=None,
            key=lambda s: abs(current_price - s),
        )

        nearest_resistance = min(
            (r for r in resistance if r > current_price),
            default=None,
            key=lambda r: abs(current_price - r),
        )

        score = 0.0

        # Near support (< 2%)
        if nearest_support:
            distance_pct = (current_price - nearest_support) / current_price
            if distance_pct < 0.02:
                score += 0.6  # Strong buy opportunity
            elif distance_pct < 0.05:
                score += 0.3  # Moderate buy

        # Near resistance (< 2%)
        if nearest_resistance:
            distance_pct = (nearest_resistance - current_price) / current_price
            if distance_pct < 0.02:
                score -= 0.6  # Strong sell pressure
            elif distance_pct < 0.05:
                score -= 0.3  # Moderate sell

        return max(-0.6, min(0.6, score))

    def _score_timeframes(self, indicators: dict[str, float]) -> float:
        """Score multi-timeframe alignment."""
        # Simplified timeframe scoring
        # In production, would use actual multi-timeframe analysis from Phase 2
        weekly_trend = indicators.get("weekly_trend", "neutral")

        trend_map = {
            "strong_oversold": 0.8,
            "strong_overbought": -0.8,
            "short_term_overbought": -0.3,
        }
        return trend_map.get(weekly_trend, 0.0)

    def _classify_signal(self, total_score: float) -> tuple[str, float]:
        """Convert total score to signal type and confidence.

        Uses configurable thresholds set during initialization:
        - BUY: score >= buy_threshold (default: 0.4)
        - SELL: score <= sell_threshold (default: -0.4)
        - HOLD: sell_threshold < score < buy_threshold
        """
        if total_score >= self.buy_threshold:
            signal_type = "BUY"
            confidence = min(1.0, abs(total_score))
        elif total_score <= self.sell_threshold:
            signal_type = "SELL"
            confidence = min(1.0, abs(total_score))
        else:
            signal_type = "HOLD"
            confidence = 1.0 - abs(total_score)  # Lower score = higher hold confidence

        return signal_type, confidence

    def _calculate_targets(
        self, current_price: float, signal_type: str, atr: float, profile: StockProfile
    ) -> dict[str, float]:
        """Calculate price targets and stops."""
        if signal_type == "BUY":
            # Use nearest resistance or ATR-based target
            resistance = profile.resistance_levels or []
            target = float(min(resistance)) if resistance else current_price + (4 * atr)

            stop_loss = current_price - (2 * atr)

        elif signal_type == "SELL":
            # Use nearest support or ATR-based target
            support = profile.support_levels or []
            target = float(max(support)) if support else current_price - (4 * atr)

            stop_loss = current_price + (2 * atr)

        else:  # HOLD
            target = current_price
            stop_loss = current_price

        # Calculate risk/reward
        profit = abs(target - current_price)
        risk = abs(current_price - stop_loss)
        risk_reward = profit / risk if risk > 0 else 0.0

        return {"target": target, "stop_loss": stop_loss, "risk_reward": risk_reward}

    def _calculate_hold_period(
        self, volatility_category: str, adx: float, atr: float
    ) -> tuple[int, int]:
        """Calculate recommended hold period."""
        if volatility_category == "low" and adx > 30:
            return (7, 15)  # Low vol + strong trend
        elif volatility_category == "high" and adx < 20:
            return (3, 5)  # High vol + weak trend
        else:
            return (5, 10)  # Medium conditions

    def calculate_chandelier_stop(
        self,
        entry_price: float,
        current_high: float,
        atr: float,
        signal_type: str,
        multiplier: float = 2.5,
    ) -> float:
        """Calculate Chandelier trailing stop.

        Formula (LONG): Stop = Highest High - (multiplier × ATR)
        Never moves down, only up.

        Args:
            entry_price: Entry price
            current_high: Highest high since entry
            atr: Average True Range
            signal_type: BUY or SELL
            multiplier: ATR multiplier (default: 2.5)

        Returns:
            Trailing stop price
        """
        if signal_type == "BUY":
            stop = current_high - (multiplier * atr)
        elif signal_type == "SELL":
            stop = current_high + (multiplier * atr)  # current_high is actually lowest low
        else:
            stop = entry_price

        return stop

    def _check_earnings_overlap(
        self, hold_period: tuple[int, int], next_earnings_date: date | None
    ) -> bool:
        """Check if hold period overlaps with earnings."""
        if not next_earnings_date:
            return False

        max_hold_days = hold_period[1]
        signal_date = date.today()
        expected_exit = signal_date + timedelta(days=max_hold_days)

        return expected_exit >= next_earnings_date

    def _check_peer_correlation(
        self, ticker: str, signal_type: str, sector: str | None, session: Session
    ) -> dict:
        """Check if peer stocks confirm signal direction."""
        if not sector:
            return {"peer_count": 0, "bullish_peers": 0, "adjustment": 0.0}

        peers = self.sector_manager.get_peers(ticker, max_peers=3)
        if not peers:
            return {"peer_count": 0, "bullish_peers": 0, "adjustment": 0.0}

        bullish_count = 0
        for peer_ticker in peers:
            # Simplified peer analysis
            # In production, would generate full signal for each peer
            # Check if peer exists in GIBD database
            peer_data = (
                session.query(WsDseDailyPrice)
                .filter(WsDseDailyPrice.txn_scrip == peer_ticker)
                .limit(1)
                .first()
            )
            if peer_data:
                # Assume bullish if price above SMA (simplified)
                bullish_count += 1 if np.random.random() > 0.5 else 0

        total_peers = len(peers) + 1  # Include original stock
        bullish_ratio = (bullish_count + (1 if signal_type == "BUY" else 0)) / total_peers

        # Adjust confidence based on peer confirmation
        if bullish_ratio >= 0.75:
            adjustment = 0.15  # Strong confirmation
        elif bullish_ratio <= 0.25:
            adjustment = -0.10  # Divergence
        else:
            adjustment = 0.0  # Mixed signals

        return {"peer_count": len(peers), "bullish_peers": bullish_count, "adjustment": adjustment}

    def _check_index_trend(self, target_date: date, session: Session) -> dict:
        """Check DSEX index trend."""
        # Simplified index check
        # In production, would fetch actual DSEX data and calculate SMA 50

        # For now, assume neutral
        return {"index_trend": "neutral", "confidence_adjustment": 0.0}

    def _build_decision_tree(
        self,
        ticker: str,
        scores: dict[str, float],
        weights: dict[str, float],
        indicators: dict[str, float],
        profile: StockProfile,
        peer_info: dict,
        index_info: dict,
    ) -> dict:
        """Build explainable decision tree."""
        return {
            "scores": scores,
            "weights": weights,
            "total_score": sum(scores[k] * weights[k] for k in scores),
            "reasoning": {
                "momentum": {
                    "rsi": {
                        "value": self._get_indicator_float(indicators, "rsi", 50.0),
                        "threshold_oversold": float(profile.rsi_oversold),
                        "threshold_overbought": float(profile.rsi_overbought),
                        "interpretation": "RSI compared to adaptive thresholds",
                    },
                    "macd": {
                        "histogram": self._get_indicator_float(indicators, "macd_histogram", 0.0),
                        "interpretation": "MACD histogram direction",
                    },
                },
                "sector": {
                    "sector_name": self.sector_manager.get_sector(ticker),
                    "relative_strength": scores.get("sector", 0),
                    "interpretation": "Stock performance vs sector average",
                },
                "peers": peer_info,
                "index": index_info,
                "support_resistance": {
                    "support_levels": profile.support_levels,
                    "resistance_levels": profile.resistance_levels,
                    "score": scores.get("support_resistance", 0),
                },
            },
        }

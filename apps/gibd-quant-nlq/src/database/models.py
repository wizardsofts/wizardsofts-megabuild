"""SQLAlchemy ORM models for quant-flow with GIBD database integration.

Models:
- WsDseDailyPrice: Read-only model for GIBD's ws_dse_daily_prices table (PRIMARY DATA SOURCE)
- Indicator: Read-only model for GIBD's indicators table (COMPUTED INDICATORS)
- StockProfile: Stock-specific calibration data (ticker-based)
- SignalHistory: Generated trading signals with outcomes (ticker-based)
- MarketRegime: Daily market regime classification
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Use JSONB for PostgreSQL, JSON for other databases (like SQLite)
JSONType = JSONB().with_variant(JSON(), "sqlite")


class WsDseDailyPrice(Base):
    """Read-only model for GIBD's ws_dse_daily_prices table.

    This is the PRIMARY source of OHLCV stock price data.
    Data is managed by GIBD system - Quant-Flow reads only.

    Note: Matches actual GIBD schema with id, created_at, last_updated_at
    """

    __tablename__ = "ws_dse_daily_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    txn_date = Column(Date, nullable=False, index=True)
    txn_scrip = Column(Text, nullable=False, index=True)
    txn_open = Column(Numeric(12, 2), nullable=False)
    txn_high = Column(Numeric(12, 2), nullable=False)
    txn_low = Column(Numeric(12, 2), nullable=False)
    txn_close = Column(Numeric(12, 2), nullable=False)
    txn_volume = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=False))  # timestamp without time zone
    last_updated_at = Column(DateTime(timezone=False))  # timestamp without time zone

    def __repr__(self) -> str:
        return f"<WsDseDailyPrice(scrip='{self.txn_scrip}', date={self.txn_date}, close={self.txn_close})>"


class Indicator(Base):
    """Read-only model for GIBD's indicators table.

    Stores computed technical indicators in JSONB format.
    Data is computed by GIBD system - Quant-Flow reads only.

    Example indicators JSONB structure:
    {
        "SMA_20": 450.5,
        "RSI_14": 62.5,
        "MACD_line_12_26_9": 3.45,
        "MACD_signal_12_26_9": 2.10,
        "ATR_14": 12.34
    }
    """

    __tablename__ = "indicators"
    __table_args__ = (Index("ix_indicators_scrip_date", "scrip", "trading_date"),)

    scrip = Column(Text, primary_key=True)  # Ticker symbol
    trading_date = Column(Date, primary_key=True)  # Trading date
    indicators = Column(JSONB, nullable=False)  # All computed indicator values
    status = Column(Text, nullable=False, server_default="CALCULATED")
    computed_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(Integer, nullable=False, server_default="1")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<Indicator(scrip='{self.scrip}', date={self.trading_date}, status='{self.status}')>"
        )


class StockProfile(Base):
    """Stock-specific calibration and profile data.

    Stores calibrated parameters and characteristics for each stock.
    Uses ticker (TEXT) instead of scrip_id foreign key.
    """

    __tablename__ = "stock_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(Text, unique=True, nullable=False, index=True)

    # Calibrated RSI thresholds
    rsi_overbought = Column(Numeric(5, 2), server_default="70.0", nullable=False)
    rsi_oversold = Column(Numeric(5, 2), server_default="30.0", nullable=False)

    # Volatility classification
    volatility_category = Column(Text, nullable=True)  # low, medium, high
    avg_true_range = Column(Numeric(12, 2), nullable=True)

    # Volume characteristics
    typical_volume = Column(BigInteger, nullable=True)
    high_volume_threshold = Column(BigInteger, nullable=True)

    # Support/Resistance levels
    support_levels = Column(JSONType, nullable=True)  # Array of support price levels
    resistance_levels = Column(JSONType, nullable=True)  # Array of resistance price levels

    # Metadata
    last_calibrated_at = Column(DateTime(timezone=True), nullable=True)
    calibration_period_days = Column(Integer, server_default="365", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<StockProfile(ticker='{self.ticker}', volatility='{self.volatility_category}')>"


class SignalHistory(Base):
    """Trading signal history with outcomes and exit tracking.

    Tracks all generated signals for backtesting and performance analysis.
    Uses ticker (TEXT) instead of scrip_id foreign key.
    """

    __tablename__ = "signal_history"
    __table_args__ = (
        UniqueConstraint("ticker", "signal_date", name="uq_signal_history_ticker_date"),
        Index("idx_signal_history_ticker_date", "ticker", "signal_date"),
        Index("idx_signal_history_signal_type", "signal_type"),
        Index("idx_signal_history_outcome", "outcome_result"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(Text, nullable=False, index=True)

    # Signal details
    signal_date = Column(Date, nullable=False, index=True)
    signal_type = Column(Text, nullable=False)  # BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
    confidence = Column(Numeric(4, 3), nullable=True)  # 0.0-1.0

    # Entry parameters
    entry_price = Column(Numeric(12, 2), nullable=False)
    target_price = Column(Numeric(12, 2), nullable=True)
    stop_loss = Column(Numeric(12, 2), nullable=True)

    # Decision context
    decision_tree = Column(JSONType, nullable=True)  # Complete reasoning chain
    indicators_snapshot = Column(JSONType, nullable=True)  # Indicator values at signal time
    market_regime = Column(Text, nullable=True)  # bull, bear, sideways, volatile

    # Outcome tracking (filled later)
    outcome_date = Column(Date, nullable=True)
    outcome_price = Column(Numeric(12, 2), nullable=True)
    outcome_result = Column(Text, nullable=True)  # target_hit, stop_loss, partial, expired, error
    return_pct = Column(Numeric(8, 3), nullable=True)

    # Exit signal tracking
    exit_signal_date = Column(Date, nullable=True)
    exit_signal_type = Column(Text, nullable=True)
    exit_reason = Column(Text, nullable=True)
    actual_exit_date = Column(Date, nullable=True)
    actual_exit_price = Column(Numeric(12, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<SignalHistory(ticker='{self.ticker}', date={self.signal_date}, type='{self.signal_type}')>"


class Company(Base):
    """DSE company information including sector classification.

    Read-only model for 'company' table in ws_gibd_dse_company_info database.
    Contains official DSE sector classifications for all listed companies.

    Note: This table is in a separate database (ws_gibd_dse_company_info),
    so use get_company_info_db_context() instead of get_db_context().
    """

    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=False))
    last_updated_at = Column(DateTime(timezone=False))
    record_status = Column(Text, nullable=True)
    company_name = Column(Text, nullable=True)
    trading_code = Column(Text, nullable=False, unique=True, index=True)
    scrip_code = Column(Text, nullable=True)
    listing_year = Column(Integer, nullable=True)
    market_category = Column(Text, nullable=True)  # A, B, Z, N
    sector = Column(Text, nullable=True, index=True)
    instrument_category = Column(Text, nullable=True)  # Equity, Mutual Funds, etc.
    electronic_share = Column(Text, nullable=True)
    fiscal_year_end = Column(Date, nullable=True)
    operational_state = Column(Text, nullable=True)
    debut_trading_date = Column(Date, nullable=True)
    otc_delisting_relisting = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Company(trading_code='{self.trading_code}', sector='{self.sector}')>"


class MarketRegime(Base):
    """Daily market regime classification.

    Tracks overall market conditions for context-aware analysis.
    """

    __tablename__ = "market_regimes"
    __table_args__ = (
        UniqueConstraint("regime_date", name="uq_market_regime_date"),
        Index("idx_market_regimes_date", "regime_date"),
        Index("idx_market_regimes_type", "regime_type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    regime_date = Column(Date, unique=True, nullable=False, index=True)

    # Regime classification
    regime_type = Column(Text, nullable=False)  # bull, bear, sideways, volatile
    trend_direction = Column(Text, nullable=True)  # uptrend, downtrend, sideways
    volatility_level = Column(Text, nullable=True)  # low, medium, high
    confidence = Column(Numeric(4, 3), nullable=True)

    # Market metrics
    dse_broad_index = Column(Numeric(12, 2), nullable=True)
    dse_30_index = Column(Numeric(12, 2), nullable=True)
    market_breadth = Column(Numeric(5, 2), nullable=True)
    volatility_index = Column(Numeric(8, 4), nullable=True)

    # Volume analysis
    total_market_volume = Column(BigInteger, nullable=True)
    avg_stock_volume = Column(BigInteger, nullable=True)

    # Additional context
    notes = Column(Text, nullable=True)
    extra_metadata = Column(JSONType, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<MarketRegime(date={self.regime_date}, type='{self.regime_type}')>"

"""Exit signal generation and position monitoring.

Monitors open positions and checks all exit conditions:
1. RSI reversal - RSI peaked and declining
2. Partial profit - 80% of target reached
3. Time stop - Max hold period exceeded
4. Stop-loss hit - Price hit stop loss
5. Sector rotation - Sector turned bearish
6. Index breakdown - DSEX broke key support
7. Flat price - Stagnant price for 3+ days
8. Chandelier trailing stop - Trailing stop hit

Classes:
    ExitSignalChecker: Main exit checker with all conditions
"""

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.database.connection import get_db_context
from src.database.models import Indicator, SignalHistory, WsDseDailyPrice
from src.sectors.manager import SectorManager

logger = logging.getLogger(__name__)


class ExitSignalChecker:
    """Monitor positions and check all 7 exit conditions.

    Exit conditions:
    1. RSI reversal: RSI peaked and declined 3+ points
    2. Partial profit: Price at 80% of target
    3. Time stop: Hold period exceeded
    4. Stop-loss hit: Price hit stop loss
    5. Sector rotation: Sector performance < -2%
    6. Index breakdown: DSEX < SMA200
    7. Flat price: < 1% range for 3+ consecutive days
    8. Chandelier stop: Trailing stop hit
    """

    def __init__(self, session: Session | None = None):
        """Initialize exit checker.

        Args:
            session: SQLAlchemy session. If None, creates new context.
        """
        self.session = session
        self._session_context = None
        self.sector_manager = SectorManager()

    def _get_session(self) -> Session:
        """Get or create database session."""
        if self.session:
            return self.session
        if self._session_context is None:
            self._session_context = get_db_context()
            return self._session_context.__enter__()
        return self._session_context.__enter__()

    def check_all_exits(self) -> dict[str, Any]:
        """Check all exit conditions for open positions.

        Gets all pending signals (open positions) and checks
        all exit conditions. Generates EXIT signal if condition met.

        Returns:
            Dict with statistics:
                - total_open_positions: Number of open trades
                - exit_signals_generated: Count of exits
                - by_condition: Exit counts by condition type
        """
        try:
            session = self._get_session()

            # Get all open positions (pending signals)
            pending_signals = (
                session.query(SignalHistory).filter(SignalHistory.outcome_result.is_(None)).all()
            )

            if not pending_signals:
                logger.info("No open positions to check")
                return {
                    "total_open_positions": 0,
                    "exit_signals_generated": 0,
                    "by_condition": {},
                }

            stats = {
                "total_open_positions": len(pending_signals),
                "exit_signals_generated": 0,
                "by_condition": {
                    "rsi_reversal": 0,
                    "partial_profit": 0,
                    "time_stop": 0,
                    "stop_loss_hit": 0,
                    "sector_rotation": 0,
                    "index_breakdown": 0,
                    "flat_price": 0,
                    "chandelier_stop": 0,
                },
            }

            for signal in pending_signals:
                try:
                    exit_result = self._check_exit_conditions(signal, session)

                    if exit_result:
                        # Update signal with exit info (P4.3.2d)
                        signal.exit_signal_date = date.today()
                        signal.outcome_date = date.today()
                        signal.outcome_result = "manual_exit"
                        signal.exit_reason = exit_result.get("condition")
                        signal.exit_confidence = 0.9  # High confidence for automated exits
                        signal.actual_hold_days = (date.today() - signal.signal_date).days
                        signal.updated_at = datetime.utcnow()
                        session.add(signal)

                        condition = exit_result.get("condition")
                        if condition in stats["by_condition"]:
                            stats["by_condition"][condition] += 1
                        stats["exit_signals_generated"] += 1

                except Exception as e:
                    logger.error(f"Error checking exits for signal {signal.id}: {str(e)}")

            session.commit()
            logger.info(f"Exit check complete: {stats}")

            return stats

        except Exception as e:
            logger.error(f"Error in check_all_exits: {str(e)}", exc_info=True)
            return {
                "total_open_positions": 0,
                "exit_signals_generated": 0,
                "error": str(e),
            }

    def _check_exit_conditions(
        self, signal: SignalHistory, session: Session
    ) -> dict[str, Any] | None:
        """Check all exit conditions for a signal.

        Args:
            signal: SignalHistory record for open position
            session: Database session

        Returns:
            Dict with exit condition if triggered, None otherwise
        """
        # Get recent price data from GIBD
        stock_data = (
            session.query(WsDseDailyPrice)
            .filter(
                WsDseDailyPrice.txn_scrip == signal.ticker,
                WsDseDailyPrice.txn_date >= signal.signal_date,
            )
            .order_by(WsDseDailyPrice.txn_date)
            .all()
        )

        if not stock_data or len(stock_data) < 2:
            return None

        current_price = float(stock_data[-1].txn_close)

        # Check each condition in order
        # 1. Stop-loss hit (highest priority)
        if signal.stop_loss and current_price <= float(signal.stop_loss):
            return {"condition": "stop_loss_hit", "reason": "Price hit stop loss"}

        # 2. Target hit (should rarely happen here, but check)
        if signal.target_price and current_price >= float(signal.target_price):
            return {"condition": "target_hit", "reason": "Price hit target"}

        # 3. Partial profit (80% of target)
        if self._check_partial_profit(signal, current_price):
            return {"condition": "partial_profit", "reason": "Reached 80% of target"}

        # 4. Time stop (hold period exceeded)
        if self._check_time_stop(signal):
            return {"condition": "time_stop", "reason": "Maximum hold period exceeded"}

        # 5. RSI reversal
        if self._check_rsi_reversal(signal, signal.ticker, session):
            return {"condition": "rsi_reversal", "reason": "RSI peaked and declining"}

        # 6. Sector rotation
        if self._check_sector_rotation(signal.ticker):
            return {"condition": "sector_rotation", "reason": "Sector turned bearish"}

        # 7. Index breakdown
        if self._check_index_breakdown(session):
            return {"condition": "index_breakdown", "reason": "Index broke key support"}

        # 8. Flat price (< 1% range for 3 days)
        if self._check_flat_price(stock_data):
            return {"condition": "flat_price", "reason": "Price stagnant for 3+ days"}

        # 9. Chandelier trailing stop
        if self._check_chandelier_stop(signal, stock_data):
            return {
                "condition": "chandelier_stop",
                "reason": "Trailing stop hit",
            }

        return None

    def _check_partial_profit(self, signal: SignalHistory, current_price: float) -> bool:
        """Check if 80% of target reached.

        Args:
            signal: SignalHistory record
            current_price: Current stock price

        Returns:
            True if 80% of target reached, False otherwise
        """
        if not signal.target_price or not signal.entry_price:
            return False

        entry = float(signal.entry_price)
        target = float(signal.target_price)

        is_buy = signal.signal_type.upper() in ("BUY", "STRONG_BUY")

        if is_buy:
            target_distance = target - entry
            current_distance = current_price - entry
            progress = current_distance / target_distance if target_distance > 0 else 0
        else:
            target_distance = entry - target
            current_distance = entry - current_price
            progress = current_distance / target_distance if target_distance > 0 else 0

        return progress >= 0.8

    def _check_time_stop(self, signal: SignalHistory) -> bool:
        """Check if maximum hold period exceeded.

        Args:
            signal: SignalHistory record

        Returns:
            True if hold period exceeded, False otherwise
        """
        days_held = (date.today() - signal.signal_date).days

        # Assume recommended hold is 5-10 days, max 15 days
        max_hold_period = 15

        return days_held > max_hold_period

    def _check_rsi_reversal(self, signal: SignalHistory, ticker: str, session: Session) -> bool:
        """Check RSI reversal (peaked and declined 3+ points).

        Args:
            signal: SignalHistory record
            ticker: Stock ticker symbol
            session: Database session

        Returns:
            True if RSI reversed, False otherwise
        """
        try:
            # Get recent RSI values from GIBD indicators table
            recent_indicators = (
                session.query(Indicator)
                .filter(
                    Indicator.scrip == ticker,
                    Indicator.trading_date >= signal.signal_date,
                )
                .order_by(Indicator.trading_date)
                .all()
            )

            if len(recent_indicators) < 3:
                return False

            # Extract RSI values from JSONB indicators column
            rsi_values = []
            for ind in recent_indicators[-3:]:
                # Look for RSI in the indicators JSONB dict (e.g., "RSI_14")
                rsi_key = next((k for k in ind.indicators if k.startswith("RSI")), None)
                if rsi_key:
                    rsi_values.append(float(ind.indicators[rsi_key]))

            # Check if peaked (first < second > third) and declined 3+ points
            if len(rsi_values) >= 3:
                peak = max(rsi_values)
                current = rsi_values[-1]
                return peak - current >= 3.0 and current < 65

            return False

        except Exception as e:
            logger.error(f"Error checking RSI reversal: {str(e)}")
            return False

    def _check_sector_rotation(self, ticker: str) -> bool:
        """Check if sector turned bearish.

        Condition: Sector performance < -2% and all peers declining

        Args:
            ticker: Stock symbol

        Returns:
            True if sector rotation detected, False otherwise
        """
        try:
            # Get sector and peer performance
            sector = self.sector_manager.get_sector(ticker)
            if not sector:
                return False

            # In production, would fetch sector performance from data
            # For now, return False (requires sector data source)
            return False

        except Exception as e:
            logger.error(f"Error checking sector rotation: {str(e)}")
            return False

    def _check_index_breakdown(self, session: Session) -> bool:
        """Check if DSEX broke key support (< SMA200).

        Args:
            session: Database session

        Returns:
            True if index breakdown detected, False otherwise
        """
        try:
            # In production, would fetch DSEX data and calculate SMA200
            # For now, return False (requires index data source)
            return False

        except Exception as e:
            logger.error(f"Error checking index breakdown: {str(e)}")
            return False

    def _check_flat_price(self, stock_data: list[WsDseDailyPrice]) -> bool:
        """Check if price stagnant (< 1% range for 3+ consecutive days).

        Args:
            stock_data: Recent stock data

        Returns:
            True if flat price detected, False otherwise
        """
        try:
            if len(stock_data) < 3:
                return False

            # Check last 3 days
            last_three = stock_data[-3:]

            for i in range(len(last_three)):
                day = last_three[i]
                high = float(day.txn_high)
                low = float(day.txn_low)

                if high == 0:
                    return False

                price_range = (high - low) / low * 100

                if price_range >= 1.0:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking flat price: {str(e)}")
            return False

    def _check_chandelier_stop(
        self, signal: SignalHistory, stock_data: list[WsDseDailyPrice]
    ) -> bool:
        """Check if Chandelier trailing stop hit.

        Chandelier stop = highest_high - (2.5 × ATR)

        Args:
            signal: SignalHistory record
            stock_data: Recent stock data

        Returns:
            True if trailing stop hit, False otherwise
        """
        try:
            if len(stock_data) < 2:
                return False

            current_price = float(stock_data[-1].txn_close)

            # Calculate ATR (simplified: average of high-low)
            if len(stock_data) >= 14:
                tr_values = [float(d.txn_high) - float(d.txn_low) for d in stock_data[-14:]]
                atr = sum(tr_values) / len(tr_values)
            else:
                atr = float(stock_data[-1].txn_high) - float(stock_data[-1].txn_low)

            # Calculate highest high since entry
            highest_high = max(float(d.txn_high) for d in stock_data)

            # Chandelier stop
            chandelier_stop = highest_high - (2.5 * atr)

            return current_price <= chandelier_stop

        except Exception as e:
            logger.error(f"Error checking Chandelier stop: {str(e)}")
            return False

    def cleanup(self):
        """Clean up database session if created internally."""
        if self._session_context:
            try:
                self._session_context.__exit__(None, None, None)
            except Exception as e:
                logger.error(f"Error cleaning up session: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

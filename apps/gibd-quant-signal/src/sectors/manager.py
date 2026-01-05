"""Sector management and analysis for DSE (Dhaka Stock Exchange).

This module manages sector definitions, calculates sector performance,
and provides relative strength analysis for stocks within their sectors.

Sector data is fetched from the dse_company_info database table which
contains official DSE sector classifications for all listed companies.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from database.connection import get_company_info_db_context, get_db_context
from database.models import Company, WsDseDailyPrice

logger = logging.getLogger(__name__)


class SectorManager:
    """Manage DSE sectors and calculate sector-relative metrics.

    Provides functionality to:
    - Map stocks to sectors (fetched from dse_company_info table)
    - Calculate sector performance
    - Compute relative strength
    - Detect sector rotation

    Example:
        manager = SectorManager()
        sector = manager.get_sector('GP')  # Returns 'Telecommunication'
        performance = manager.get_sector_performance(date.today())
        # {'Bank': 0.023, 'Pharmaceuticals & Chemicals': -0.015, ...}
    """

    def __init__(self):
        """Initialize sector manager by loading sector data from database."""
        self._ticker_to_sector: dict[str, str] = {}
        self._sector_to_tickers: dict[str, list[str]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazy load sector data from database on first use."""
        if self._loaded:
            return

        try:
            # Use separate database connection for company info
            with get_company_info_db_context() as session:
                # Fetch all company info with sector data
                companies = (
                    session.query(Company)
                    .filter(
                        Company.sector.isnot(None),
                        Company.trading_code.isnot(None),
                    )
                    .all()
                )

                for company in companies:
                    ticker = company.trading_code.upper()
                    sector = company.sector

                    # Build ticker -> sector mapping
                    self._ticker_to_sector[ticker] = sector

                    # Build sector -> tickers mapping
                    if sector not in self._sector_to_tickers:
                        self._sector_to_tickers[sector] = []
                    self._sector_to_tickers[sector].append(ticker)

                self._loaded = True
                logger.info(
                    f"SectorManager loaded {len(self._sector_to_tickers)} sectors, "
                    f"{len(self._ticker_to_sector)} stocks from database"
                )

        except Exception as e:
            logger.error(f"Failed to load sector data from database: {e}")
            self._loaded = True  # Mark as loaded to avoid repeated failures

    def get_sector(self, ticker: str) -> str | None:
        """Get sector name for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'GP', 'SQURPHARMA')

        Returns:
            Sector name or None if ticker not found
        """
        self._ensure_loaded()
        return self._ticker_to_sector.get(ticker.upper())

    def get_sector_tickers(self, sector: str) -> list[str]:
        """Get list of tickers in a sector.

        Args:
            sector: Sector name (e.g., 'Bank', 'Pharmaceuticals & Chemicals')

        Returns:
            List of ticker symbols in the sector
        """
        self._ensure_loaded()
        return self._sector_to_tickers.get(sector, [])

    def get_all_sectors(self) -> list[str]:
        """Get list of all sector names.

        Returns:
            List of sector names
        """
        self._ensure_loaded()
        return list(self._sector_to_tickers.keys())

    def get_sector_performance(
        self, target_date: date, session: Session | None = None
    ) -> dict[str, float]:
        """Calculate daily performance for each sector.

        For each sector:
        1. Get all constituent stocks
        2. Calculate 1-day return for each stock
        3. Sector performance = average return across stocks
        4. Store in market_regimes table

        Args:
            target_date: Date to calculate performance for
            session: Optional database session

        Returns:
            Dict mapping sector name to return percentage

        Example:
            >>> performance = manager.get_sector_performance(date(2023, 12, 21))
            >>> performance
            {'Banking': 0.023, 'Pharmaceutical': -0.015, 'Telecommunication': 0.041}
        """
        own_session = session is None

        try:
            if own_session:
                with get_db_context() as sess:
                    return self._calculate_sector_performance(target_date, sess)
            else:
                return self._calculate_sector_performance(target_date, session)

        except Exception as e:
            logger.error(f"Failed to calculate sector performance: {e}")
            return {}

    def _calculate_sector_performance(
        self, target_date: date, session: Session
    ) -> dict[str, float]:
        """Internal implementation of sector performance calculation.

        Args:
            target_date: Target date
            session: Database session

        Returns:
            Dict of sector performances
        """
        self._ensure_loaded()

        sector_returns = {}

        for sector, tickers in self._sector_to_tickers.items():
            if not tickers:
                continue

            returns = []

            for ticker in tickers:
                # Get today's and previous close from GIBD
                today_data = (
                    session.query(WsDseDailyPrice)
                    .filter(
                        WsDseDailyPrice.txn_scrip == ticker,
                        WsDseDailyPrice.txn_date == target_date,
                    )
                    .first()
                )

                prev_data = (
                    session.query(WsDseDailyPrice)
                    .filter(
                        WsDseDailyPrice.txn_scrip == ticker,
                        WsDseDailyPrice.txn_date < target_date,
                    )
                    .order_by(WsDseDailyPrice.txn_date.desc())
                    .first()
                )

                if today_data and prev_data:
                    close_today = float(today_data.txn_close)
                    close_prev = float(prev_data.txn_close)

                    if close_prev > 0:
                        ret = (close_today - close_prev) / close_prev
                        returns.append(ret)

            # Calculate sector average return
            if returns:
                sector_avg = sum(returns) / len(returns)
                sector_returns[sector] = sector_avg
            else:
                sector_returns[sector] = 0.0

        logger.debug(
            f"Sector performance for {target_date}: " f"{len(sector_returns)} sectors calculated"
        )

        return sector_returns

    def get_relative_strength(
        self,
        ticker: str,
        sector: str | None = None,
        target_date: date | None = None,
        session: Session | None = None,
    ) -> float:
        """Calculate stock performance relative to its sector.

        Formula:
        - Stock return: (close_today - close_yesterday) / close_yesterday
        - Sector return: Average return of sector stocks
        - Relative strength: (1 + stock_return) / (1 + sector_return)

        Interpretation:
        - > 1.0 = Outperforming sector
        - < 1.0 = Underperforming sector
        - ~1.0 = In line with sector

        Args:
            ticker: Stock ticker symbol
            sector: Sector name (auto-detected if None)
            target_date: Date to calculate for (today if None)
            session: Optional database session

        Returns:
            Relative strength ratio

        Example:
            >>> rs = manager.get_relative_strength('GP')
            >>> # GP return: +5.2%, Telecom sector: +2.5%
            >>> # RS = (1.052 / 1.025) = 1.026 (outperforming)
        """
        if target_date is None:
            target_date = date.today()

        if sector is None:
            sector = self.get_sector(ticker)
            if sector is None:
                logger.warning(f"Ticker {ticker} not found in any sector")
                return 1.0  # Neutral

        own_session = session is None

        try:
            if own_session:
                with get_db_context() as sess:
                    return self._calculate_relative_strength(ticker, sector, target_date, sess)
            else:
                return self._calculate_relative_strength(ticker, sector, target_date, session)

        except Exception as e:
            logger.error(f"Failed to calculate relative strength: {e}")
            return 1.0  # Neutral on error

    def _calculate_relative_strength(
        self, ticker: str, sector: str, target_date: date, session: Session
    ) -> float:
        """Internal implementation of relative strength calculation.

        Args:
            ticker: Stock ticker
            sector: Sector name
            target_date: Target date
            session: Database session

        Returns:
            Relative strength ratio
        """
        # Get stock return from GIBD
        today_data = (
            session.query(WsDseDailyPrice)
            .filter(
                WsDseDailyPrice.txn_scrip == ticker,
                WsDseDailyPrice.txn_date == target_date,
            )
            .first()
        )

        prev_data = (
            session.query(WsDseDailyPrice)
            .filter(
                WsDseDailyPrice.txn_scrip == ticker,
                WsDseDailyPrice.txn_date < target_date,
            )
            .order_by(WsDseDailyPrice.txn_date.desc())
            .first()
        )

        if not (today_data and prev_data):
            return 1.0

        close_today = float(today_data.txn_close)
        close_prev = float(prev_data.txn_close)

        if close_prev == 0:
            return 1.0

        stock_return = (close_today - close_prev) / close_prev

        # Get sector return
        sector_performance = self.get_sector_performance(target_date, session)
        sector_return = sector_performance.get(sector, 0.0)

        # Calculate relative strength
        # Avoid division by zero
        if sector_return == -1.0:  # Sector down 100% (unlikely but possible)
            return 1.0

        rs = (1 + stock_return) / (1 + sector_return)

        logger.debug(
            f"{ticker} relative strength: {rs:.4f} "
            f"(stock: {stock_return:.4f}, sector: {sector_return:.4f})"
        )

        return rs

    def detect_sector_rotation(
        self, target_date: date, session: Session | None = None
    ) -> dict[str, list[str]]:
        """Identify which sectors are strong/weak.

        Classify sectors by performance:
        - Strong: Top 30% performers
        - Weak: Bottom 30% performers
        - Neutral: Middle 40%

        Args:
            target_date: Date to analyze
            session: Optional database session

        Returns:
            Dict with 'strong_sectors', 'weak_sectors', 'neutral_sectors' lists
        """
        sector_performance = self.get_sector_performance(target_date, session)

        if not sector_performance:
            return {"strong_sectors": [], "weak_sectors": [], "neutral_sectors": []}

        # Sort sectors by performance
        sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)

        total_sectors = len(sorted_sectors)
        strong_count = int(total_sectors * 0.3)
        weak_count = int(total_sectors * 0.3)

        strong_sectors = [s[0] for s in sorted_sectors[:strong_count]]
        weak_sectors = [s[0] for s in sorted_sectors[-weak_count:]]
        neutral_sectors = [s[0] for s in sorted_sectors[strong_count:-weak_count] if weak_count > 0]

        logger.info(
            f"Sector rotation on {target_date}: "
            f"{len(strong_sectors)} strong, {len(weak_sectors)} weak, "
            f"{len(neutral_sectors)} neutral"
        )

        return {
            "strong_sectors": strong_sectors,
            "weak_sectors": weak_sectors,
            "neutral_sectors": neutral_sectors,
        }

    def get_peers(self, ticker: str, max_peers: int = 3) -> list[str]:
        """Get top peer stocks in the same sector.

        Returns top N other stocks in the sector by market cap or
        alphabetically if market cap not available.

        Args:
            ticker: Stock ticker symbol
            max_peers: Maximum number of peers to return (default: 3)

        Returns:
            List of ticker symbols (peers), excluding input ticker
        """
        sector = self.get_sector(ticker)
        if not sector:
            return []

        sector_tickers = self.get_sector_tickers(sector)

        # Remove the input ticker itself
        peers = [t for t in sector_tickers if t != ticker.upper()]

        # Return top N peers (alphabetically for now)
        # TODO: Could be enhanced to sort by market cap
        return peers[:max_peers]

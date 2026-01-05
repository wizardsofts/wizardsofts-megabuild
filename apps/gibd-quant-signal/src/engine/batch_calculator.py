"""Batch calculator for processing multiple stocks efficiently.

This module provides the BatchCalculator class for calculating indicators
across multiple stocks with support for parallel execution and performance
optimization.
"""

import logging
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd

from fast_track.indicator_pipeline import IndicatorPipeline

logger = logging.getLogger(__name__)


class BatchCalculatorResults:
    """Container for batch calculation results.

    Attributes:
        successful: Number of successful calculations
        failed: Number of failed calculations
        total: Total number of calculations attempted
        results: Dictionary mapping ticker to result dict
        errors: Dictionary mapping ticker to error message
    """

    def __init__(self):
        """Initialize results container."""
        self.successful = 0
        self.failed = 0
        self.total = 0
        self.results: dict[str, dict[str, Any]] = {}
        self.errors: dict[str, str] = {}

    def add_success(self, ticker: str, result: dict[str, Any]):
        """Add a successful result.

        Args:
            ticker: Stock ticker symbol
            result: Calculation result dictionary
        """
        self.successful += 1
        self.total += 1
        self.results[ticker] = result

    def add_failure(self, ticker: str, error: str):
        """Add a failed result.

        Args:
            ticker: Stock ticker symbol
            error: Error message
        """
        self.failed += 1
        self.total += 1
        self.errors[ticker] = error

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Dictionary with summary information
        """
        success_rate = (self.successful / self.total * 100) if self.total > 0 else 0
        return {
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": success_rate,
        }


class BatchCalculator:
    """Calculate indicators for multiple stocks in batch.

    Supports:
    - Sequential processing for simplicity
    - ThreadPool processing for I/O-bound operations
    - ProcessPool processing for CPU-intensive calculations
    - Progress tracking and result aggregation
    - Error handling and recovery

    Attributes:
        execution_mode: 'sequential', 'thread', or 'process'
        max_workers: Maximum number of parallel workers
    """

    EXECUTION_MODES = ["sequential", "thread", "process"]
    DEFAULT_MAX_WORKERS = 4

    def __init__(self, execution_mode: str = "sequential", max_workers: int | None = None):
        """Initialize batch calculator.

        Args:
            execution_mode: How to execute calculations ('sequential', 'thread', 'process')
            max_workers: Maximum number of parallel workers (default: 4)

        Raises:
            ValueError: If execution_mode is not valid
        """
        if execution_mode not in self.EXECUTION_MODES:
            raise ValueError(
                f"Invalid execution_mode: {execution_mode}. Must be one of {self.EXECUTION_MODES}"
            )

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.execution_mode = execution_mode
        self.max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        self.pipeline = IndicatorPipeline()

        self.logger.info(
            f"BatchCalculator initialized (mode={execution_mode}, workers={self.max_workers})"
        )

    def calculate_batch(
        self,
        tickers: list[str],
        data_fetcher: Callable[[str], pd.DataFrame | None] | None = None,
        context: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BatchCalculatorResults:
        """Calculate indicators for multiple stocks.

        Args:
            tickers: List of stock ticker symbols
            data_fetcher: Optional function to fetch data for each ticker.
                         If None, uses pipeline's _fetch_data method.
            context: Optional market context dict for tool selection
            progress_callback: Optional callback function(current, total) for progress tracking

        Returns:
            BatchCalculatorResults with all results and statistics
        """
        self.logger.info(
            f"Starting batch calculation for {len(tickers)} tickers "
            f"(mode={self.execution_mode})"
        )

        results = BatchCalculatorResults()

        if self.execution_mode == "sequential":
            results = self._calculate_sequential(tickers, data_fetcher, context, progress_callback)
        elif self.execution_mode == "thread":
            results = self._calculate_threaded(tickers, data_fetcher, context, progress_callback)
        elif self.execution_mode == "process":
            results = self._calculate_process(tickers, data_fetcher, context, progress_callback)

        summary = results.get_summary()
        self.logger.info(f"Batch calculation complete: {summary}")

        return results

    def _calculate_sequential(
        self,
        tickers: list[str],
        data_fetcher: Callable[[str], pd.DataFrame | None] | None,
        context: dict[str, Any] | None,
        progress_callback: Callable[[int, int], None] | None,
    ) -> BatchCalculatorResults:
        """Calculate indicators sequentially for each ticker.

        Args:
            tickers: List of tickers
            data_fetcher: Data fetcher function or None
            context: Market context dictionary
            progress_callback: Progress callback function

        Returns:
            BatchCalculatorResults with all results
        """
        results = BatchCalculatorResults()

        for i, ticker in enumerate(tickers):
            try:
                self.logger.debug(f"Processing {ticker} ({i + 1}/{len(tickers)})")

                # Fetch data if provided
                data = None
                if data_fetcher:
                    data = data_fetcher(ticker)

                # Calculate indicators
                indicator_result = self.pipeline.calculate_all(ticker, data, context)

                if indicator_result.get("status") == "success":
                    results.add_success(ticker, indicator_result)
                else:
                    error_msg = indicator_result.get("error", "Unknown error")
                    results.add_failure(ticker, error_msg)

            except Exception as e:
                self.logger.error(f"Error processing {ticker}: {e}")
                results.add_failure(ticker, str(e))

            # Call progress callback
            if progress_callback:
                progress_callback(i + 1, len(tickers))

        return results

    def _calculate_threaded(
        self,
        tickers: list[str],
        data_fetcher: Callable[[str], pd.DataFrame | None] | None,
        context: dict[str, Any] | None,
        progress_callback: Callable[[int, int], None] | None,
    ) -> BatchCalculatorResults:
        """Calculate indicators using thread pool.

        Args:
            tickers: List of tickers
            data_fetcher: Data fetcher function or None
            context: Market context dictionary
            progress_callback: Progress callback function

        Returns:
            BatchCalculatorResults with all results
        """
        results = BatchCalculatorResults()
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self._process_ticker, ticker, data_fetcher, context): ticker
                for ticker in tickers
            }

            # Process completed tasks
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    indicator_result = future.result()
                    if indicator_result.get("status") == "success":
                        results.add_success(ticker, indicator_result)
                    else:
                        error_msg = indicator_result.get("error", "Unknown error")
                        results.add_failure(ticker, error_msg)
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
                    results.add_failure(ticker, str(e))

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(tickers))

        return results

    def _calculate_process(
        self,
        tickers: list[str],
        data_fetcher: Callable[[str], pd.DataFrame | None] | None,
        context: dict[str, Any] | None,
        progress_callback: Callable[[int, int], None] | None,
    ) -> BatchCalculatorResults:
        """Calculate indicators using process pool.

        Note: This mode is less practical for I/O-bound operations like
        database access. Use thread mode for better performance with database queries.

        Args:
            tickers: List of tickers
            data_fetcher: Data fetcher function or None
            context: Market context dictionary
            progress_callback: Progress callback function

        Returns:
            BatchCalculatorResults with all results
        """
        results = BatchCalculatorResults()
        completed = 0

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self._process_ticker, ticker, data_fetcher, context): ticker
                for ticker in tickers
            }

            # Process completed tasks
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    indicator_result = future.result()
                    if indicator_result.get("status") == "success":
                        results.add_success(ticker, indicator_result)
                    else:
                        error_msg = indicator_result.get("error", "Unknown error")
                        results.add_failure(ticker, error_msg)
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
                    results.add_failure(ticker, str(e))

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(tickers))

        return results

    def _process_ticker(
        self,
        ticker: str,
        data_fetcher: Callable[[str], pd.DataFrame | None] | None,
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Process a single ticker.

        Args:
            ticker: Stock ticker symbol
            data_fetcher: Data fetcher function or None
            context: Market context dictionary

        Returns:
            Indicator calculation result
        """
        try:
            # Fetch data if provided
            data = None
            if data_fetcher:
                data = data_fetcher(ticker)

            # Calculate indicators
            return self.pipeline.calculate_all(ticker, data, context)

        except Exception as e:
            self.logger.error(f"Error processing {ticker}: {e}")
            return {"ticker": ticker, "status": "error", "error": str(e)}

    def get_execution_mode(self) -> str:
        """Get current execution mode.

        Returns:
            Current execution mode string
        """
        return self.execution_mode

    def set_execution_mode(self, mode: str):
        """Change execution mode.

        Args:
            mode: New execution mode ('sequential', 'thread', or 'process')

        Raises:
            ValueError: If mode is not valid
        """
        if mode not in self.EXECUTION_MODES:
            raise ValueError(
                f"Invalid execution_mode: {mode}. Must be one of {self.EXECUTION_MODES}"
            )
        self.execution_mode = mode
        self.logger.info(f"Execution mode changed to: {mode}")

"""
Adaptive rate limiter with exponential backoff.

Provides intelligent rate limiting that adjusts based on success/failure patterns.
"""
import time
import random
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional
from contextlib import contextmanager


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting behavior."""
    min_delay: float = 1.0        # Minimum delay between requests (seconds)
    max_delay: float = 60.0       # Maximum delay between requests (seconds)
    initial_delay: float = 2.0    # Starting delay (seconds)
    backoff_factor: float = 2.0   # Multiplier on failure
    jitter_factor: float = 0.2    # Random jitter as fraction of delay (0-1)
    cooldown_factor: float = 0.8  # Multiplier on success (< 1 to decrease delay)


class AdaptiveRateLimiter:
    """
    Rate limiter with exponential backoff and jitter.

    Automatically adjusts delay based on request success/failure patterns:
    - On success: Gradually reduces delay (faster requests)
    - On failure: Exponentially increases delay (slower requests)
    - On rate limit: Aggressively increases delay

    Example:
        limiter = AdaptiveRateLimiter()

        for url in urls:
            limiter.wait()  # Wait before request
            try:
                response = requests.get(url)
                response.raise_for_status()
                limiter.report_success()
            except requests.HTTPError as e:
                is_rate_limit = e.response.status_code == 429
                limiter.report_failure(is_rate_limit=is_rate_limit)
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize the rate limiter.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or RateLimitConfig()
        self._delay = self.config.initial_delay
        self._lock = Lock()
        self._last_request_time: Optional[float] = None
        self._consecutive_failures = 0
        self._consecutive_successes = 0

    @property
    def current_delay(self) -> float:
        """Get current delay value (for monitoring)."""
        return self._delay

    def wait(self) -> float:
        """
        Wait for the appropriate delay before making a request.

        Applies jitter to avoid thundering herd problem.

        Returns:
            Actual wait time in seconds
        """
        with self._lock:
            # Calculate delay with jitter
            jitter_range = self._delay * self.config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            actual_delay = max(self.config.min_delay, self._delay + jitter)

            # Account for time already elapsed since last request
            if self._last_request_time is not None:
                elapsed = time.time() - self._last_request_time
                wait_time = max(0, actual_delay - elapsed)
            else:
                wait_time = actual_delay

            if wait_time > 0:
                time.sleep(wait_time)

            self._last_request_time = time.time()
            return wait_time

    def report_success(self) -> None:
        """
        Report a successful request.

        Gradually reduces delay to allow faster requests.
        """
        with self._lock:
            self._consecutive_failures = 0
            self._consecutive_successes += 1

            # Reduce delay after consecutive successes
            if self._consecutive_successes >= 3:
                self._delay = max(
                    self.config.min_delay,
                    self._delay * self.config.cooldown_factor
                )

    def report_failure(self, is_rate_limit: bool = False) -> None:
        """
        Report a failed request.

        Increases delay exponentially, more aggressively for rate limits.

        Args:
            is_rate_limit: True if failure was due to rate limiting (429/503)
        """
        with self._lock:
            self._consecutive_successes = 0
            self._consecutive_failures += 1

            # More aggressive backoff for rate limits
            factor = self.config.backoff_factor
            if is_rate_limit:
                factor *= 2  # Double the backoff factor for rate limits

            self._delay = min(
                self.config.max_delay,
                self._delay * factor
            )

    def reset(self) -> None:
        """Reset limiter to initial state."""
        with self._lock:
            self._delay = self.config.initial_delay
            self._consecutive_failures = 0
            self._consecutive_successes = 0
            self._last_request_time = None

    @contextmanager
    def request(self):
        """
        Context manager for making a rate-limited request.

        Automatically waits before the request and reports success/failure.

        Example:
            with limiter.request() as ctx:
                response = requests.get(url)
                response.raise_for_status()
                ctx.success()  # Mark as successful

        Note: If ctx.success() is not called before exit, failure is assumed.
        """
        self.wait()
        result = _RequestContext(self)
        try:
            yield result
        except Exception:
            if not result._reported:
                self.report_failure()
            raise
        else:
            if not result._reported:
                # If no explicit success/failure reported, assume success
                self.report_success()


class _RequestContext:
    """Helper class for request context manager."""

    def __init__(self, limiter: AdaptiveRateLimiter):
        self._limiter = limiter
        self._reported = False

    def success(self) -> None:
        """Mark this request as successful."""
        if not self._reported:
            self._limiter.report_success()
            self._reported = True

    def failure(self, is_rate_limit: bool = False) -> None:
        """Mark this request as failed."""
        if not self._reported:
            self._limiter.report_failure(is_rate_limit=is_rate_limit)
            self._reported = True


# Pre-configured rate limiters for common use cases
def create_web_scraper_limiter() -> AdaptiveRateLimiter:
    """Create a rate limiter configured for web scraping."""
    return AdaptiveRateLimiter(RateLimitConfig(
        min_delay=1.0,
        max_delay=30.0,
        initial_delay=2.0,
        backoff_factor=1.5,
        jitter_factor=0.3,
    ))


def create_api_limiter() -> AdaptiveRateLimiter:
    """Create a rate limiter configured for API calls."""
    return AdaptiveRateLimiter(RateLimitConfig(
        min_delay=0.5,
        max_delay=60.0,
        initial_delay=1.0,
        backoff_factor=2.0,
        jitter_factor=0.1,
    ))


def create_gentle_limiter() -> AdaptiveRateLimiter:
    """Create a very conservative rate limiter for sensitive endpoints."""
    return AdaptiveRateLimiter(RateLimitConfig(
        min_delay=5.0,
        max_delay=120.0,
        initial_delay=10.0,
        backoff_factor=2.5,
        jitter_factor=0.2,
    ))

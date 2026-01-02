"""
Unit tests for rate_limiter.py
"""
import time
import unittest
from unittest.mock import patch


class TestRateLimitConfig(unittest.TestCase):
    """Tests for RateLimitConfig dataclass."""

    def test_default_values(self):
        from rate_limiter import RateLimitConfig
        config = RateLimitConfig()

        self.assertEqual(config.min_delay, 1.0)
        self.assertEqual(config.max_delay, 60.0)
        self.assertEqual(config.initial_delay, 2.0)
        self.assertEqual(config.backoff_factor, 2.0)
        self.assertEqual(config.jitter_factor, 0.2)
        self.assertEqual(config.cooldown_factor, 0.8)

    def test_custom_values(self):
        from rate_limiter import RateLimitConfig
        config = RateLimitConfig(
            min_delay=0.5,
            max_delay=30.0,
            initial_delay=1.0
        )

        self.assertEqual(config.min_delay, 0.5)
        self.assertEqual(config.max_delay, 30.0)
        self.assertEqual(config.initial_delay, 1.0)


class TestAdaptiveRateLimiter(unittest.TestCase):
    """Tests for AdaptiveRateLimiter class."""

    def test_initial_delay(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(initial_delay=5.0)
        limiter = AdaptiveRateLimiter(config)

        self.assertEqual(limiter.current_delay, 5.0)

    def test_success_reduces_delay(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=10.0,
            min_delay=1.0,
            cooldown_factor=0.5
        )
        limiter = AdaptiveRateLimiter(config)

        # Need 3 consecutive successes to reduce delay
        limiter.report_success()
        limiter.report_success()
        limiter.report_success()

        self.assertLess(limiter.current_delay, 10.0)

    def test_failure_increases_delay(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=5.0,
            backoff_factor=2.0
        )
        limiter = AdaptiveRateLimiter(config)

        limiter.report_failure()

        self.assertEqual(limiter.current_delay, 10.0)

    def test_rate_limit_failure_increases_delay_more(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=5.0,
            backoff_factor=2.0
        )
        limiter = AdaptiveRateLimiter(config)

        limiter.report_failure(is_rate_limit=True)

        # Rate limit uses factor * 2
        self.assertEqual(limiter.current_delay, 20.0)

    def test_delay_capped_at_max(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=30.0,
            max_delay=60.0,
            backoff_factor=3.0
        )
        limiter = AdaptiveRateLimiter(config)

        limiter.report_failure()

        # Would be 90, but capped at 60
        self.assertEqual(limiter.current_delay, 60.0)

    def test_delay_floored_at_min(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=2.0,
            min_delay=1.0,
            cooldown_factor=0.1
        )
        limiter = AdaptiveRateLimiter(config)

        # Many successes should not go below min
        for _ in range(20):
            limiter.report_success()

        self.assertGreaterEqual(limiter.current_delay, 1.0)

    def test_reset_restores_initial_state(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(initial_delay=5.0)
        limiter = AdaptiveRateLimiter(config)

        limiter.report_failure()
        limiter.report_failure()

        self.assertGreater(limiter.current_delay, 5.0)

        limiter.reset()

        self.assertEqual(limiter.current_delay, 5.0)

    def test_failure_resets_consecutive_successes(self):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(initial_delay=10.0)
        limiter = AdaptiveRateLimiter(config)

        limiter.report_success()
        limiter.report_success()
        limiter.report_failure()

        initial_delay = limiter.current_delay

        # These 2 successes shouldn't trigger cooldown (need 3 consecutive)
        limiter.report_success()
        limiter.report_success()

        # Delay should still be same (no reduction yet)
        self.assertEqual(limiter.current_delay, initial_delay)

    @patch('time.sleep')
    def test_wait_calls_sleep(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=1.0,
            jitter_factor=0  # No jitter for predictable test
        )
        limiter = AdaptiveRateLimiter(config)

        limiter.wait()

        mock_sleep.assert_called()

    @patch('time.sleep')
    def test_wait_respects_min_delay(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig
        config = RateLimitConfig(
            initial_delay=0.5,
            min_delay=1.0,
            jitter_factor=0
        )
        limiter = AdaptiveRateLimiter(config)

        limiter.wait()

        # Should wait at least min_delay
        args = mock_sleep.call_args[0]
        self.assertGreaterEqual(args[0], 1.0)


class TestRequestContextManager(unittest.TestCase):
    """Tests for request context manager."""

    @patch('time.sleep')
    def test_request_waits_before_yield(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter

        limiter = AdaptiveRateLimiter()

        with limiter.request():
            pass

        mock_sleep.assert_called()

    @patch('time.sleep')
    def test_request_auto_success_on_normal_exit(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig

        config = RateLimitConfig(initial_delay=10.0, cooldown_factor=0.5)
        limiter = AdaptiveRateLimiter(config)

        # 3 successful requests
        for _ in range(3):
            with limiter.request():
                pass

        # Delay should have reduced
        self.assertLess(limiter.current_delay, 10.0)

    @patch('time.sleep')
    def test_request_auto_failure_on_exception(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig

        config = RateLimitConfig(initial_delay=5.0, backoff_factor=2.0)
        limiter = AdaptiveRateLimiter(config)

        with self.assertRaises(ValueError):
            with limiter.request():
                raise ValueError("test error")

        # Delay should have increased
        self.assertEqual(limiter.current_delay, 10.0)

    @patch('time.sleep')
    def test_request_explicit_success(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig

        config = RateLimitConfig(initial_delay=10.0, cooldown_factor=0.5)
        limiter = AdaptiveRateLimiter(config)

        for _ in range(3):
            with limiter.request() as ctx:
                ctx.success()

        self.assertLess(limiter.current_delay, 10.0)

    @patch('time.sleep')
    def test_request_explicit_failure(self, mock_sleep):
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig

        config = RateLimitConfig(initial_delay=5.0, backoff_factor=2.0)
        limiter = AdaptiveRateLimiter(config)

        with limiter.request() as ctx:
            ctx.failure(is_rate_limit=True)

        self.assertEqual(limiter.current_delay, 20.0)


class TestPreConfiguredLimiters(unittest.TestCase):
    """Tests for pre-configured rate limiter factories."""

    def test_create_web_scraper_limiter(self):
        from rate_limiter import create_web_scraper_limiter

        limiter = create_web_scraper_limiter()

        self.assertEqual(limiter.config.min_delay, 1.0)
        self.assertEqual(limiter.config.max_delay, 30.0)

    def test_create_api_limiter(self):
        from rate_limiter import create_api_limiter

        limiter = create_api_limiter()

        self.assertEqual(limiter.config.min_delay, 0.5)
        self.assertEqual(limiter.config.max_delay, 60.0)

    def test_create_gentle_limiter(self):
        from rate_limiter import create_gentle_limiter

        limiter = create_gentle_limiter()

        self.assertEqual(limiter.config.min_delay, 5.0)
        self.assertEqual(limiter.config.initial_delay, 10.0)


if __name__ == '__main__':
    unittest.main()

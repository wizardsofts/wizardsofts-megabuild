"""Celery application configuration and initialization.

Configures Celery with Redis broker/backend and Beat schedule for
scheduled tasks like daily market analysis, outcome updates, and
indicator pre-computation.

Configuration:
- Broker: Redis (default localhost:6379)
- Backend: Redis (result caching)
- Beat: Periodic task scheduling
"""

import os

from celery import Celery
from celery.schedules import crontab

# Initialize Celery app
app = Celery("quant-flow")

# Load configuration from environment or defaults
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 0)

# Broker and backend URLs
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB + 1}"

# Configure Celery
app.conf.update(
    # Broker settings
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    # Beat schedule for periodic tasks
    beat_schedule={
        # Daily market analysis at 5:00 PM UTC (12:00 PM EST)
        "daily-market-analysis": {
            "task": "src.tasks.celery_tasks.daily_market_analysis",
            "schedule": crontab(hour=17, minute=0),
            "options": {"queue": "analysis", "expires": 3600},
        },
        # Update signal outcomes at 5:30 PM UTC
        "update-signal-outcomes": {
            "task": "src.tasks.celery_tasks.update_signal_outcomes",
            "schedule": crontab(hour=17, minute=30),
            "options": {"queue": "analysis", "expires": 3600},
        },
        # Pre-compute indicators hourly during market hours (9 AM - 4 PM UTC)
        "precompute-indicators-9am": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=9, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-10am": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=10, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-11am": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=11, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-12pm": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=12, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-1pm": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=13, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-2pm": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=14, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-3pm": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=15, minute=0),
            "options": {"queue": "indicators"},
        },
        "precompute-indicators-4pm": {
            "task": "src.tasks.celery_tasks.precompute_indicators",
            "schedule": crontab(hour=16, minute=0),
            "options": {"queue": "indicators"},
        },
        # Exit signal check at 4:00 PM UTC (before market close)
        "check-exit-signals": {
            "task": "src.tasks.celery_tasks.check_exit_signals",
            "schedule": crontab(hour=16, minute=0),
            "options": {"queue": "analysis", "expires": 3600},
        },
        # Generate weekly backtest report on Sunday at 9:00 AM UTC
        "generate-backtest-report": {
            "task": "src.tasks.celery_tasks.generate_backtest_report",
            "schedule": crontab(day_of_week=6, hour=9, minute=0),
            "options": {"queue": "analysis", "expires": 3600},
        },
        # GIBD data health checks
        "gibd-daily-health-check": {
            "task": "gibd_sync.daily_health_check",
            "schedule": crontab(hour=18, minute=0),  # 6 PM daily
            "options": {"queue": "monitoring", "expires": 3600},
        },
        "gibd-verify-freshness": {
            "task": "gibd_sync.verify_data_freshness",
            "schedule": crontab(hour="*/4"),  # Every 4 hours
            "options": {"queue": "monitoring", "expires": 1800},
        },
    },
    # Task routes (specify which queue each task goes to)
    task_routes={
        "src.tasks.celery_tasks.daily_market_analysis": {"queue": "analysis"},
        "src.tasks.celery_tasks.analyze_single_stock": {"queue": "analysis"},
        "src.tasks.celery_tasks.update_signal_outcomes": {"queue": "analysis"},
        "src.tasks.celery_tasks.generate_backtest_report": {"queue": "analysis"},
        "src.tasks.celery_tasks.check_exit_signals": {"queue": "analysis"},
        "src.tasks.celery_tasks.precompute_indicators": {"queue": "indicators"},
        "gibd_sync.verify_data_freshness": {"queue": "monitoring"},
        "gibd_sync.check_missing_indicators": {"queue": "monitoring"},
        "gibd_sync.daily_health_check": {"queue": "monitoring"},
        "gibd_sync.get_ticker_coverage": {"queue": "monitoring"},
    },
)


# Auto-discover tasks from src.tasks module
app.autodiscover_tasks(["src.tasks"])


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f"Request: {self.request!r}")
    return "Debug task executed"

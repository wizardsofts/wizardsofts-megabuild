"""
Celery configuration
"""
import os

# ===== Broker Configuration =====
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://:password@10.0.0.84:6380/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://:password@10.0.0.84:6380/1')

# Broker connection retry settings
broker_connection_retry_on_startup = True
broker_connection_retry = True
broker_connection_max_retries = 10

# ===== Serialization =====
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# ===== Task Routing =====
task_routes = {
    'tasks.ml_tasks.*': {'queue': 'ml'},
    'tasks.data_tasks.*': {'queue': 'data'},
    'tasks.simple_tasks.*': {'queue': 'default'}
}

# ===== Task Execution =====
# Time limits
task_soft_time_limit = 3600  # 1 hour soft limit
task_time_limit = 7200  # 2 hours hard limit

# Result settings
result_expires = 86400  # Results expire after 24 hours
result_extended = True

# Worker settings
worker_prefetch_multiplier = 1  # Fetch one task at a time for long-running tasks
worker_max_tasks_per_child = 100  # Restart worker after 100 tasks to prevent memory leaks

# Task acknowledgment
task_acks_late = True  # Acknowledge task after completion, not before
task_reject_on_worker_lost = True

# ===== Beat Schedule (Recurring Tasks) =====
beat_schedule = {
    # Example: Daily model retraining at 2 AM
    'daily-model-retraining': {
        'task': 'tasks.ml_tasks.retrain_models',
        'schedule': 3600 * 24,  # Every 24 hours
        'args': (),
        'options': {'queue': 'ml'}
    },

    # Example: Hourly data processing
    'hourly-data-processing': {
        'task': 'tasks.data_tasks.process_new_data',
        'schedule': 3600,  # Every hour
        'args': (),
        'options': {'queue': 'data'}
    },

    # Example: Check cluster health every 5 minutes
    'cluster-health-check': {
        'task': 'tasks.simple_tasks.check_cluster_health',
        'schedule': 300,  # Every 5 minutes
        'args': (),
        'options': {'queue': 'default'}
    }
}

# ===== Monitoring =====
# Enable events for monitoring with Flower
worker_send_task_events = True
task_send_sent_event = True

# Prometheus metrics
worker_enable_remote_control = True

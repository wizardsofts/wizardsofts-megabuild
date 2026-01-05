"""
Celery application initialization
"""
from celery import Celery
import os

# Initialize Celery app
app = Celery('wizardsofts_ml_tasks')

# Load configuration from celeryconfig module
app.config_from_object('tasks.celeryconfig')

# Import task modules to register tasks
from tasks import simple_tasks  # noqa: F401
from tasks import ml_tasks      # noqa: F401
from tasks import data_tasks    # noqa: F401

# Export app
__all__ = ['app']

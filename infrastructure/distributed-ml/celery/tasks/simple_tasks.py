"""
Simple tasks that don't require Ray cluster
Used for monitoring, health checks, and lightweight operations
"""
from tasks import app
import logging
import requests

logger = logging.getLogger(__name__)

@app.task
def check_cluster_health():
    """
    Scheduled task: Check Ray cluster health every 5 minutes
    """
    try:
        # Check Ray dashboard
        response = requests.get("http://10.0.0.84:8265/api/cluster_status", timeout=10)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Ray cluster healthy. Nodes: {data.get('num_nodes', 'unknown')}")
            return {
                'status': 'healthy',
                'timestamp': response.headers.get('Date'),
                'cluster_data': data
            }
        else:
            logger.warning(f"Ray cluster returned status {response.status_code}")
            return {
                'status': 'degraded',
                'status_code': response.status_code
            }

    except Exception as e:
        logger.error(f"Ray cluster health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


@app.task
def send_notification(message: str, channel: str = 'default'):
    """
    Send notification (email, Slack, etc.)

    Args:
        message: Notification message
        channel: Notification channel (email, slack, etc.)
    """
    logger.info(f"Sending notification to {channel}: {message}")

    # TODO: Implement actual notification logic
    # For now, just log it
    return {
        'status': 'sent',
        'channel': channel,
        'message': message
    }


@app.task
def cleanup_old_results():
    """
    Scheduled task: Clean up old task results and logs
    """
    logger.info("Starting cleanup of old results")

    # TODO: Implement cleanup logic
    # - Remove old Celery results from Redis
    # - Archive or delete old log files
    # - Clean up temporary files

    return {
        'status': 'completed',
        'files_deleted': 0,
        'space_freed': 0
    }


@app.task
def ping():
    """
    Simple ping task for testing
    """
    return {'status': 'pong', 'worker': 'celery'}

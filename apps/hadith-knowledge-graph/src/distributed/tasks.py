"""
Celery tasks for distributed Hadith processing

Uses existing Celery infrastructure on Server 84
"""

from celery import Celery, group
from typing import List, Dict, Any
from loguru import logger

from src.config import get_settings
from src.extraction.pipeline import ExtractionPipeline

settings = get_settings()

# Connect to existing Celery on Server 84
celery_app = Celery(
    "hadith-extraction",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)


@celery_app.task(name="hadith.process_single", bind=True, max_retries=3)
def process_single_hadith(self, hadith_id: int, hadith_text: str) -> Dict[str, Any]:
    """
    Process a single hadith (Celery task).

    Args:
        hadith_id: Hadith ID
        hadith_text: Hadith text in English

    Returns:
        Processing result
    """
    try:
        logger.info(f"[Celery] Processing hadith {hadith_id}")

        pipeline = ExtractionPipeline()
        result = pipeline.process_hadith(hadith_id, hadith_text)

        logger.info(f"[Celery] Completed hadith {hadith_id}")
        return result

    except Exception as e:
        logger.error(f"[Celery] Failed hadith {hadith_id}: {e}")

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(name="hadith.process_batch", bind=True)
def process_hadith_batch(self, hadiths: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a batch of hadiths in parallel.

    Args:
        hadiths: List of {hadith_id, hadith_text} dicts

    Returns:
        Batch processing summary
    """
    logger.info(f"[Celery] Processing batch of {len(hadiths)} hadiths")

    # Create parallel tasks
    job = group(
        process_single_hadith.s(h["hadith_id"], h["hadith_text"])
        for h in hadiths
    )

    # Execute in parallel
    result = job.apply_async()

    # Wait for all tasks to complete
    results = result.get(timeout=600)  # 10 minutes timeout

    # Summarize results
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed")

    summary = {
        "total": len(hadiths),
        "successful": successful,
        "failed": failed,
        "results": results
    }

    logger.info(f"[Celery] Batch complete: {successful}/{len(hadiths)} successful")
    return summary


# Task for monitoring
@celery_app.task(name="hadith.health_check")
def health_check() -> Dict[str, str]:
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "service": "hadith-extraction",
        "celery_broker": settings.celery_broker_url.split("@")[-1]  # Hide password
    }

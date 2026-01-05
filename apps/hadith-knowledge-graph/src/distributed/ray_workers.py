"""
Ray workers for parallel entity extraction

Connects to existing Ray cluster on Server 84
"""

import ray
from typing import List, Dict, Any
from loguru import logger

from src.config import get_settings
from src.extraction.entity_extractor import EntityExtractor

settings = get_settings()


def init_ray():
    """Initialize Ray connection to existing cluster on Server 84."""
    if not ray.is_initialized():
        try:
            # Connect to existing Ray cluster
            ray.init(
                address=settings.ray_address,
                namespace=settings.ray_namespace,
                runtime_env={
                    "pip": [
                        "httpx",
                        "loguru",
                        "pydantic",
                        "pydantic-settings"
                    ]
                }
            )
            logger.info(f"Connected to Ray cluster: {settings.ray_address}")
        except Exception as e:
            logger.warning(f"Failed to connect to Ray cluster: {e}. Running locally.")
            ray.init(ignore_reinit_error=True)


@ray.remote
def extract_entities_single(hadith_id: int, hadith_text: str) -> Dict[str, Any]:
    """
    Ray remote function to extract entities from a single hadith.

    Args:
        hadith_id: Hadith ID
        hadith_text: Hadith text

    Returns:
        Extracted entities
    """
    try:
        extractor = EntityExtractor()
        entities = extractor.extract_all(hadith_text)

        return {
            "hadith_id": hadith_id,
            "status": "success",
            "entities": entities
        }

    except Exception as e:
        logger.error(f"Ray extraction failed for hadith {hadith_id}: {e}")
        return {
            "hadith_id": hadith_id,
            "status": "failed",
            "error": str(e)
        }


def extract_entities_parallel(hadiths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract entities from multiple hadiths in parallel using Ray.

    Args:
        hadiths: List of {hadith_id, hadith_text} dicts

    Returns:
        List of extraction results
    """
    init_ray()

    logger.info(f"[Ray] Extracting entities from {len(hadiths)} hadiths in parallel")

    # Submit tasks to Ray cluster
    futures = [
        extract_entities_single.remote(h["hadith_id"], h["hadith_text"])
        for h in hadiths
    ]

    # Wait for all tasks to complete
    results = ray.get(futures)

    successful = sum(1 for r in results if r.get("status") == "success")
    logger.info(f"[Ray] Extraction complete: {successful}/{len(hadiths)} successful")

    return results


def shutdown_ray():
    """Shutdown Ray connection."""
    if ray.is_initialized():
        ray.shutdown()
        logger.info("Ray shutdown complete")

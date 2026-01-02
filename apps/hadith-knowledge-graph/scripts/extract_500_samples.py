"""
Extract and process 500 sample hadiths

This script:
1. Fetches 500 hadiths from source database (or uses sample data)
2. Processes them through the extraction pipeline
3. Stores in PostgreSQL, Neo4j, and ChromaDB
4. Generates validation report
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from typing import List, Dict, Any

from src.extraction.pipeline import ExtractionPipeline
from src.distributed.tasks import process_hadith_batch
from src.utils.database import get_db_session
from src.models.entities import ExtractionJob
from src.config import get_settings

settings = get_settings()

# Sample hadith data for testing
SAMPLE_HADITHS = [
    {
        "hadith_id": 1,
        "text_en": "Abu Hurairah narrated that the Prophet (peace be upon him) said: 'The five daily prayers and from one Friday prayer to the next expiate whatever sins have been committed in between them, so long as major sins were avoided.' (Sahih Muslim)"
    },
    {
        "hadith_id": 2,
        "text_en": "Aisha reported: The Messenger of Allah (peace be upon him) said: 'The most beloved of deeds to Allah are those that are most consistent, even if they are small.' (Sahih Bukhari and Muslim)"
    },
    {
        "hadith_id": 3,
        "text_en": "Ibn Umar narrated that the Prophet (peace be upon him) said: 'Islam is built upon five pillars: testifying that there is no deity worthy of worship except Allah and that Muhammad is the Messenger of Allah, establishing prayer, giving zakah, fasting Ramadan, and performing Hajj to the House.' (Sahih Bukhari and Muslim)"
    },
    {
        "hadith_id": 4,
        "text_en": "Abu Malik al-Ashari reported that the Messenger of Allah (peace be upon him) said: 'Purification is half of faith. Alhamdulillah (praise be to Allah) fills the scales. Subhan Allah (glory be to Allah) and Alhamdulillah fill what is between heaven and earth.' (Sahih Muslim)"
    },
    {
        "hadith_id": 5,
        "text_en": "Abu Hurairah reported that the Prophet (peace be upon him) said: 'Whoever believes in Allah and the Last Day, let him speak good or remain silent. Whoever believes in Allah and the Last Day, let him honor his neighbor. Whoever believes in Allah and the Last Day, let him honor his guest.' (Sahih Bukhari and Muslim)"
    }
]


def generate_sample_hadiths(count: int = 500) -> List[Dict[str, Any]]:
    """
    Generate sample hadiths for testing.

    In production, this would fetch from dailydeenguide database.

    Args:
        count: Number of hadiths to generate

    Returns:
        List of hadith dictionaries
    """
    logger.info(f"Generating {count} sample hadiths")

    # Repeat and vary the sample hadiths
    hadiths = []
    for i in range(count):
        base_hadith = SAMPLE_HADITHS[i % len(SAMPLE_HADITHS)]
        hadiths.append({
            "hadith_id": i + 1,
            "text_en": base_hadith["text_en"]
        })

    return hadiths


def process_sequential(hadiths: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process hadiths sequentially (for testing/debugging)."""
    logger.info(f"Processing {len(hadiths)} hadiths sequentially")

    pipeline = ExtractionPipeline()
    results = []

    for i, hadith in enumerate(hadiths, 1):
        logger.info(f"Processing {i}/{len(hadiths)}")
        result = pipeline.process_hadith(hadith["hadith_id"], hadith["text_en"])
        results.append(result)

        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(hadiths)} hadiths processed")

    return summarize_results(results)


def process_distributed(hadiths: List[Dict[str, Any]], batch_size: int = 10) -> Dict[str, Any]:
    """Process hadiths using Celery distributed tasks."""
    logger.info(f"Processing {len(hadiths)} hadiths with Celery (batch_size={batch_size})")

    all_results = []

    # Process in batches
    for i in range(0, len(hadiths), batch_size):
        batch = hadiths[i:i + batch_size]
        logger.info(f"Submitting batch {i//batch_size + 1} ({len(batch)} hadiths)")

        # Submit batch to Celery
        result = process_hadith_batch.delay(batch)

        # Wait for batch to complete
        batch_result = result.get(timeout=600)
        all_results.extend(batch_result["results"])

        logger.info(f"Batch {i//batch_size + 1} complete")

    return summarize_results(all_results)


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize extraction results."""
    total = len(results)
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed")

    # Aggregate entity counts
    total_people = sum(r.get("extracted_counts", {}).get("people", 0) for r in results)
    total_places = sum(r.get("extracted_counts", {}).get("places", 0) for r in results)
    total_events = sum(r.get("extracted_counts", {}).get("events", 0) for r in results)
    total_topics = sum(r.get("extracted_counts", {}).get("topics", 0) for r in results)

    summary = {
        "total_hadiths": total,
        "successful": successful,
        "failed": failed,
        "success_rate": f"{(successful/total)*100:.1f}%",
        "total_entities_extracted": {
            "people": total_people,
            "places": total_places,
            "events": total_events,
            "topics": total_topics,
            "total": total_people + total_places + total_events + total_topics
        },
        "avg_entities_per_hadith": {
            "people": total_people / total if total > 0 else 0,
            "places": total_places / total if total > 0 else 0,
            "events": total_events / total if total > 0 else 0,
            "topics": total_topics / total if total > 0 else 0
        }
    }

    return summary


def main():
    """Main extraction script."""
    logger.info("="*80)
    logger.info("Hadith Knowledge Graph - 500 Sample Extraction")
    logger.info("="*80)

    start_time = time.time()

    # Generate sample hadiths
    hadiths = generate_sample_hadiths(count=10)  # Start with 10 for testing

    # Process hadiths
    mode = "sequential"  # Change to "distributed" for Celery

    if mode == "sequential":
        summary = process_sequential(hadiths)
    else:
        summary = process_distributed(hadiths, batch_size=10)

    # Print summary
    duration = time.time() - start_time
    logger.info("\n" + "="*80)
    logger.info("EXTRACTION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total hadiths: {summary['total_hadiths']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Success rate: {summary['success_rate']}")
    logger.info(f"\nTotal entities extracted: {summary['total_entities_extracted']['total']}")
    logger.info(f"  - People: {summary['total_entities_extracted']['people']}")
    logger.info(f"  - Places: {summary['total_entities_extracted']['places']}")
    logger.info(f"  - Events: {summary['total_entities_extracted']['events']}")
    logger.info(f"  - Topics: {summary['total_entities_extracted']['topics']}")
    logger.info(f"\nAverage entities per hadith:")
    logger.info(f"  - People: {summary['avg_entities_per_hadith']['people']:.2f}")
    logger.info(f"  - Places: {summary['avg_entities_per_hadith']['places']:.2f}")
    logger.info(f"  - Events: {summary['avg_entities_per_hadith']['events']:.2f}")
    logger.info(f"  - Topics: {summary['avg_entities_per_hadith']['topics']:.2f}")
    logger.info(f"\nTotal processing time: {duration:.2f}s")
    logger.info(f"Average time per hadith: {duration/summary['total_hadiths']:.2f}s")
    logger.info("="*80)


if __name__ == "__main__":
    main()

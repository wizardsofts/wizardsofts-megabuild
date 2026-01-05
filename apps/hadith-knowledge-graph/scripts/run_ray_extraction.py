#!/usr/bin/env python3
"""
Run entity extraction on hadiths using Ray distributed processing.

This script:
1. Fetches hadiths from the database
2. Uses Ray to parallelize entity extraction
3. Resolves and stores entities in PostgreSQL
"""

import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import ray
from loguru import logger

from src.config import get_settings
from src.extraction.entity_extractor import EntityExtractor
from src.extraction.entity_resolver import EntityResolver
from src.utils.database import get_db_session

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level:<8} | {message}")

settings = get_settings()


def get_hadiths(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch hadiths from database."""
    conn = psycopg2.connect(
        host='10.0.0.80',
        port=5435,
        user='postgres',
        password='29Dec2#24',
        database='ws_daily_deen_guide'
    )
    cur = conn.cursor()

    cur.execute('''
        SELECT id, translation, narrator, source, reference
        FROM hadith
        WHERE translation IS NOT NULL
        AND LENGTH(translation) > 50
        ORDER BY created_at
        LIMIT %s
    ''', (limit,))

    hadiths = cur.fetchall()
    conn.close()

    return [
        {
            "id": str(h[0]),
            "text": h[1],
            "narrator": h[2],
            "source": h[3],
            "reference": h[4]
        }
        for h in hadiths
    ]


@ray.remote
def extract_hadith_entities(hadith: Dict[str, Any], model: str) -> Dict[str, Any]:
    """
    Ray remote function to extract entities from a single hadith.

    Args:
        hadith: Hadith data dict
        model: Ollama model to use

    Returns:
        Extraction result
    """
    start_time = time.time()
    hadith_id = hadith["id"]

    try:
        extractor = EntityExtractor(model=model)
        entities = extractor.extract_all(hadith["text"])

        elapsed = time.time() - start_time

        return {
            "hadith_id": hadith_id,
            "status": "success",
            "time_seconds": elapsed,
            "entities": entities,
            "counts": {
                "people": len(entities.get("people", [])),
                "places": len(entities.get("places", [])),
                "events": len(entities.get("events", [])),
                "topics": len(entities.get("topics", []))
            }
        }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "hadith_id": hadith_id,
            "status": "failed",
            "time_seconds": elapsed,
            "error": str(e)
        }


def resolve_and_store_entities(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Resolve extracted entities and store in PostgreSQL.

    Args:
        results: List of extraction results from Ray

    Returns:
        Counts of stored entities by type
    """
    total_counts = {"people": 0, "places": 0, "events": 0, "topics": 0}

    with get_db_session() as db:
        resolver = EntityResolver(db)

        for result in results:
            if result.get("status") != "success":
                continue

            entities = result.get("entities", {})
            hadith_id = result["hadith_id"]

            # Resolve and store people
            for person in entities.get("people", []):
                try:
                    resolver.resolve_person(person)
                    total_counts["people"] += 1
                except Exception as e:
                    logger.warning(f"Failed to resolve person in hadith {hadith_id}: {e}")

            # Resolve and store places
            for place in entities.get("places", []):
                try:
                    resolver.resolve_place(place)
                    total_counts["places"] += 1
                except Exception as e:
                    logger.warning(f"Failed to resolve place in hadith {hadith_id}: {e}")

            # Resolve and store events
            for event in entities.get("events", []):
                try:
                    resolver.resolve_event(event)
                    total_counts["events"] += 1
                except Exception as e:
                    logger.warning(f"Failed to resolve event in hadith {hadith_id}: {e}")

            # Resolve and store topics
            for topic in entities.get("topics", []):
                try:
                    resolver.resolve_topic(topic)
                    total_counts["topics"] += 1
                except Exception as e:
                    logger.warning(f"Failed to resolve topic in hadith {hadith_id}: {e}")

    return total_counts


def main():
    parser = argparse.ArgumentParser(description="Run entity extraction using Ray")
    parser.add_argument("--limit", type=int, default=50, help="Number of hadiths to process")
    parser.add_argument("--model", type=str, default=None, help="Ollama model to use")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for Ray tasks")
    parser.add_argument("--local", action="store_true", help="Run Ray locally instead of cluster")
    args = parser.parse_args()

    model = args.model or settings.ollama_model

    logger.info("=" * 80)
    logger.info(f"Hadith Entity Extraction with Ray")
    logger.info(f"Model: {model}")
    logger.info(f"Limit: {args.limit} hadiths")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info("=" * 80)

    # Initialize Ray
    if args.local:
        logger.info("Initializing Ray locally...")
        ray.init(ignore_reinit_error=True)
    else:
        logger.info(f"Connecting to Ray cluster at {settings.ray_address}...")
        try:
            ray.init(
                address=settings.ray_address,
                namespace=settings.ray_namespace,
                ignore_reinit_error=True
            )
            logger.info(f"Connected to Ray cluster with {len(ray.nodes())} nodes")
        except Exception as e:
            logger.warning(f"Failed to connect to Ray cluster: {e}. Running locally.")
            ray.init(ignore_reinit_error=True)

    # Fetch hadiths
    logger.info(f"Fetching {args.limit} hadiths from database...")
    hadiths = get_hadiths(args.limit)
    logger.info(f"Found {len(hadiths)} hadiths")

    if not hadiths:
        logger.error("No hadiths found!")
        return

    # Submit extraction tasks to Ray
    logger.info(f"Submitting {len(hadiths)} extraction tasks to Ray...")
    start_time = time.time()

    futures = [
        extract_hadith_entities.remote(hadith, model)
        for hadith in hadiths
    ]

    # Wait for results with progress tracking
    results = []
    pending = futures.copy()

    while pending:
        done, pending = ray.wait(pending, num_returns=min(args.batch_size, len(pending)))
        batch_results = ray.get(done)
        results.extend(batch_results)

        successful = sum(1 for r in results if r.get("status") == "success")
        logger.info(f"Progress: {len(results)}/{len(hadiths)} ({successful} successful)")

    extraction_time = time.time() - start_time

    # Summarize extraction results
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "failed"]

    logger.info("")
    logger.info("=" * 80)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total hadiths: {len(hadiths)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Extraction time: {extraction_time:.2f}s")
    logger.info(f"Average time per hadith: {extraction_time / len(hadiths):.2f}s")

    # Count extracted entities
    total_entities = {"people": 0, "places": 0, "events": 0, "topics": 0}
    for result in successful:
        counts = result.get("counts", {})
        for entity_type in total_entities:
            total_entities[entity_type] += counts.get(entity_type, 0)

    logger.info(f"\nExtracted entities:")
    for entity_type, count in total_entities.items():
        logger.info(f"  {entity_type.capitalize()}: {count}")

    # Resolve and store entities
    logger.info("\nResolving and storing entities in PostgreSQL...")
    store_start = time.time()
    stored_counts = resolve_and_store_entities(results)
    store_time = time.time() - store_start

    logger.info(f"\nStored entities (after deduplication):")
    for entity_type, count in stored_counts.items():
        logger.info(f"  {entity_type.capitalize()}: {count}")
    logger.info(f"Storage time: {store_time:.2f}s")

    # Final summary
    total_time = time.time() - start_time
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Hadiths processed: {len(successful)}/{len(hadiths)}")
    logger.info(f"Entities stored: {sum(stored_counts.values())}")

    # Save results to file
    output_file = f"/tmp/ray_extraction_results_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": model,
            "total_hadiths": len(hadiths),
            "successful": len(successful),
            "failed": len(failed),
            "extraction_time_seconds": extraction_time,
            "storage_time_seconds": store_time,
            "total_time_seconds": total_time,
            "extracted_entities": total_entities,
            "stored_entities": stored_counts,
            "results": results
        }, f, indent=2)

    logger.info(f"\nResults saved to: {output_file}")
    logger.info("=" * 80)

    # Shutdown Ray
    ray.shutdown()


if __name__ == "__main__":
    main()

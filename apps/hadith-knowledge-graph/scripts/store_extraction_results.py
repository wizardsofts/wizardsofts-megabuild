#!/usr/bin/env python3
"""
Store previously extracted entities from JSON file to PostgreSQL.
"""

import os
import sys
import json
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from src.config import get_settings
from src.extraction.entity_resolver import EntityResolver
from src.utils.database import get_db_session

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level:<8} | {message}")

settings = get_settings()


def main():
    parser = argparse.ArgumentParser(description="Store extraction results to PostgreSQL")
    parser.add_argument("--input", type=str, required=True, help="Path to extraction results JSON file")
    args = parser.parse_args()

    # Load results
    logger.info(f"Loading extraction results from {args.input}...")
    with open(args.input, "r") as f:
        data = json.load(f)

    results = data.get("results", [])
    logger.info(f"Found {len(results)} hadith extraction results")

    # Count entities
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

    logger.info("")
    logger.info("=" * 60)
    logger.info("STORAGE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Stored entities (after deduplication):")
    for entity_type, count in total_counts.items():
        logger.info(f"  {entity_type.capitalize()}: {count}")


if __name__ == "__main__":
    main()

"""
Test extraction with a single hadith
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.extraction.pipeline import ExtractionPipeline

def main():
    logger.info("Testing single hadith extraction...")

    pipeline = ExtractionPipeline()

    hadith_text = """Abu Hurairah narrated that the Prophet (peace be upon him) said: 'The five daily prayers and from one Friday prayer to the next expiate whatever sins have been committed in between them, so long as major sins were avoided.' (Sahih Muslim)"""

    result = pipeline.process_hadith(hadith_id=1, hadith_text=hadith_text)

    logger.info(f"Result: {result}")

    if result.get("status") == "success":
        logger.info("✅ Single hadith extraction successful!")
        logger.info(f"Extracted entities: {result.get('extracted_counts')}")
        logger.info(f"Duration: {result.get('duration_ms')}ms")
    else:
        logger.error(f"❌ Extraction failed: {result.get('error')}")

if __name__ == "__main__":
    main()

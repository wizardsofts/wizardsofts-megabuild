#!/usr/bin/env python3
"""
Test extraction on multiple hadiths to check consistency
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.extraction.pipeline import ExtractionPipeline

# Test hadiths with known entity counts
TEST_HADITHS = [
    {
        "id": 1,
        "text": """Abu Hurairah narrated that the Prophet (peace and blessings be upon him) said: 
                  "Faith has over seventy branches, the highest of which is to say 'There is no god but Allah,' 
                  and the least of which is to remove something harmful from the road. Modesty is a branch of faith." """,
        "expected_people": 2,  # Abu Hurairah + Prophet Muhammad
        "expected_names": ["Abu Hurairah", "Muhammad"]
    },
    {
        "id": 2,
        "text": """Umar ibn al-Khattab reported that the Messenger of Allah said: 
                  "Actions are according to intentions, and every person will have what they intended." """,
        "expected_people": 2,  # Umar + Messenger
        "expected_names": ["Umar ibn al-Khattab", "Muhammad"]
    },
    {
        "id": 3,
        "text": """Aisha narrated: I asked the Prophet about virtue, and he said: 
                  "Good character." """,
        "expected_people": 2,  # Aisha + Prophet
        "expected_names": ["Aisha", "Muhammad"]
    },
    {
        "id": 4,
        "text": """Abdullah ibn Umar said that Allah's Messenger told us about the battle of Badr.""",
        "expected_people": 2,  # Abdullah ibn Umar + Allah's Messenger
        "expected_names": ["Abdullah ibn Umar", "Muhammad"]
    },
    {
        "id": 5,
        "text": """The Prophet Muhammad went to Medina and met Abu Bakr at the mosque.""",
        "expected_people": 2,  # Muhammad + Abu Bakr
        "expected_names": ["Muhammad", "Abu Bakr"]
    }
]

def main():
    logger.info("Testing extraction on multiple hadiths...")
    
    pipeline = ExtractionPipeline()
    results = []
    
    for hadith in TEST_HADITHS:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Hadith {hadith['id']}")
        logger.info(f"Expected {hadith['expected_people']} people: {hadith['expected_names']}")
        logger.info(f"Text: {hadith['text'][:100]}...")
        
        # Extract entities (skip the full pipeline to avoid ChromaDB errors)
        extracted = pipeline.extractor.extract_all(hadith['text'])
        
        people_count = len(extracted['people'])
        people_names = [p.get('canonical_name_en', 'UNKNOWN') for p in extracted['people']]
        
        logger.info(f"Extracted {people_count} people: {people_names}")
        
        # Check if extraction is complete
        if people_count < hadith['expected_people']:
            logger.warning(f"❌ INCOMPLETE: Expected {hadith['expected_people']}, got {people_count}")
        elif people_count == hadith['expected_people']:
            logger.success(f"✅ CORRECT: Extracted {people_count} people as expected")
        else:
            logger.info(f"⚠️  OVER-EXTRACTION: Expected {hadith['expected_people']}, got {people_count}")
        
        results.append({
            'hadith_id': hadith['id'],
            'expected': hadith['expected_people'],
            'extracted': people_count,
            'names': people_names,
            'complete': people_count >= hadith['expected_people']
        })
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    
    total = len(results)
    complete = sum(1 for r in results if r['complete'])
    incomplete = total - complete
    
    logger.info(f"Total hadiths tested: {total}")
    logger.info(f"Complete extractions: {complete} ({complete/total*100:.1f}%)")
    logger.info(f"Incomplete extractions: {incomplete} ({incomplete/total*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['complete'] else "❌"
        logger.info(f"  {status} Hadith {result['hadith_id']}: {result['extracted']}/{result['expected']} people - {result['names']}")

if __name__ == "__main__":
    main()

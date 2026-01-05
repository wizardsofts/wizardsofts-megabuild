"""
Initialize Neo4j constraints and indexes
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.utils.database import get_neo4j_session

def init_neo4j():
    """Initialize Neo4j constraints and indexes"""

    logger.info("Initializing Neo4j schema...")

    constraints = [
        "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT place_id_unique IF NOT EXISTS FOR (p:Place) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT hadith_id_unique IF NOT EXISTS FOR (h:Hadith) REQUIRE h.hadith_id IS UNIQUE",
    ]

    indexes = [
        # Person indexes
        "CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.canonical_name)",
        "CREATE INDEX person_type_idx IF NOT EXISTS FOR (p:Person) ON (p.person_type)",
        "CREATE INDEX person_reliability_idx IF NOT EXISTS FOR (p:Person) ON (p.reliability_grade)",

        # Place indexes
        "CREATE INDEX place_name_idx IF NOT EXISTS FOR (p:Place) ON (p.canonical_name)",
        "CREATE INDEX place_type_idx IF NOT EXISTS FOR (p:Place) ON (p.place_type)",

        # Event indexes
        "CREATE INDEX event_name_idx IF NOT EXISTS FOR (e:Event) ON (e.canonical_name)",
        "CREATE INDEX event_date_idx IF NOT EXISTS FOR (e:Event) ON (e.date_hijri_year)",

        # Topic indexes
        "CREATE INDEX topic_name_idx IF NOT EXISTS FOR (t:Topic) ON (t.canonical_name)",
        "CREATE INDEX topic_category_idx IF NOT EXISTS FOR (t:Topic) ON (t.category)",

        # Hadith indexes
        "CREATE INDEX hadith_grading_idx IF NOT EXISTS FOR (h:Hadith) ON (h.grading)",
        "CREATE INDEX hadith_collection_idx IF NOT EXISTS FOR (h:Hadith) ON (h.collection)",
    ]

    fulltext_indexes = [
        "CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS FOR (p:Person) ON EACH [p.canonical_name]",
        "CREATE FULLTEXT INDEX place_fulltext IF NOT EXISTS FOR (p:Place) ON EACH [p.canonical_name]",
        "CREATE FULLTEXT INDEX event_fulltext IF NOT EXISTS FOR (e:Event) ON EACH [e.canonical_name]",
        "CREATE FULLTEXT INDEX topic_fulltext IF NOT EXISTS FOR (t:Topic) ON EACH [t.canonical_name]",
        "CREATE FULLTEXT INDEX hadith_fulltext IF NOT EXISTS FOR (h:Hadith) ON EACH [h.text_en]",
    ]

    try:
        with get_neo4j_session() as session:
            # Create constraints
            logger.info("Creating constraints...")
            for constraint in constraints:
                logger.debug(f"Executing: {constraint}")
                session.run(constraint)
            logger.info(f"✅ Created {len(constraints)} constraints")

            # Create regular indexes
            logger.info("Creating regular indexes...")
            for index in indexes:
                logger.debug(f"Executing: {index}")
                session.run(index)
            logger.info(f"✅ Created {len(indexes)} indexes")

            # Create full-text indexes
            logger.info("Creating full-text indexes...")
            for index in fulltext_indexes:
                logger.debug(f"Executing: {index}")
                session.run(index)
            logger.info(f"✅ Created {len(fulltext_indexes)} full-text indexes")

            logger.info("✅ Neo4j schema initialization complete!")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Neo4j schema: {e}")
        raise

if __name__ == "__main__":
    init_neo4j()

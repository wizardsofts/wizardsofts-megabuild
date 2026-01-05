"""
Extraction pipeline orchestrating entity extraction, resolution, and storage
"""

import time
from typing import Dict, Any, List
from uuid import UUID
from loguru import logger

from src.extraction.entity_extractor import EntityExtractor
from src.extraction.entity_resolver import EntityResolver
from src.utils.database import get_db_session, get_neo4j_session, get_or_create_collection
from src.utils.embeddings import get_embedding
from src.config import get_settings

settings = get_settings()


class ExtractionPipeline:
    """Orchestrate entity extraction, resolution, and storage"""

    def __init__(self):
        self.extractor = EntityExtractor()

    def process_hadith(self, hadith_id: int, hadith_text: str) -> Dict[str, Any]:
        """
        Process a single hadith through the full extraction pipeline.

        Args:
            hadith_id: Hadith ID from source database
            hadith_text: Hadith text in English

        Returns:
            Extraction results summary
        """
        start_time = time.time()
        logger.info(f"Processing hadith {hadith_id}")

        try:
            # Step 1: Extract entities using LLM
            logger.info("Step 1: Extracting entities...")
            extracted = self.extractor.extract_all(hadith_text)

            # Step 2: Resolve entities and store in PostgreSQL
            logger.info("Step 2: Resolving entities...")
            with get_db_session() as db:
                resolver = EntityResolver(db)

                resolved_ids = {
                    "people": [resolver.resolve_person(p) for p in extracted["people"]],
                    "places": [resolver.resolve_place(p) for p in extracted["places"]],
                    "events": [resolver.resolve_event(e) for e in extracted["events"]],
                    "topics": [resolver.resolve_topic(t) for t in extracted["topics"]]
                }

                logger.info(f"Resolved entities: {sum(len(v) for v in resolved_ids.values())} total")

            # Step 3: Generate embedding
            logger.info("Step 3: Generating embedding...")
            embedding = get_embedding(hadith_text)

            # Step 4: Sync to Neo4j
            logger.info("Step 4: Syncing to Neo4j...")
            self._sync_to_neo4j(hadith_id, hadith_text, resolved_ids)

            # Step 5: Store in ChromaDB
            logger.info("Step 5: Storing in ChromaDB...")
            self._store_in_chroma(hadith_id, hadith_text, embedding, resolved_ids)

            duration = time.time() - start_time
            logger.info(f"✅ Completed hadith {hadith_id} in {duration:.2f}s")

            return {
                "hadith_id": hadith_id,
                "status": "success",
                "duration_ms": int(duration * 1000),
                "extracted_counts": {k: len(v) for k, v in extracted.items()},
                "resolved_ids": {k: [str(id) for id in v] for k, v in resolved_ids.items()}
            }

        except Exception as e:
            logger.error(f"❌ Failed to process hadith {hadith_id}: {e}")
            return {
                "hadith_id": hadith_id,
                "status": "failed",
                "error": str(e)
            }

    def _sync_to_neo4j(self, hadith_id: int, text: str, resolved_ids: Dict[str, List[UUID]]):
        """
        Sync entities and relationships to Neo4j.

        Args:
            hadith_id: Hadith ID
            text: Hadith text
            resolved_ids: Resolved entity UUIDs
        """
        with get_neo4j_session() as session:
            # Create Hadith node
            session.run("""
                MERGE (h:Hadith {hadith_id: $hadith_id})
                SET h.text_en = $text,
                    h.updated_at = datetime()
            """, hadith_id=hadith_id, text=text[:500])

            # Link to people
            for person_id in resolved_ids["people"]:
                session.run("""
                    MATCH (h:Hadith {hadith_id: $hadith_id})
                    MERGE (p:Person {id: $person_id})
                    MERGE (h)-[r:MENTIONS_PERSON]->(p)
                    SET r.confidence = 0.8
                """, hadith_id=hadith_id, person_id=str(person_id))

            # Link to places
            for place_id in resolved_ids["places"]:
                session.run("""
                    MATCH (h:Hadith {hadith_id: $hadith_id})
                    MERGE (p:Place {id: $place_id})
                    MERGE (h)-[r:MENTIONS_PLACE]->(p)
                    SET r.confidence = 0.8
                """, hadith_id=hadith_id, place_id=str(place_id))

            # Link to topics
            for topic_id in resolved_ids["topics"]:
                session.run("""
                    MATCH (h:Hadith {hadith_id: $hadith_id})
                    MERGE (t:Topic {id: $topic_id})
                    MERGE (h)-[r:ABOUT_TOPIC]->(t)
                    SET r.relevance = 0.9
                """, hadith_id=hadith_id, topic_id=str(topic_id))

            logger.debug(f"Synced hadith {hadith_id} to Neo4j")

    def _store_in_chroma(
        self,
        hadith_id: int,
        text: str,
        embedding: List[float],
        resolved_ids: Dict[str, List[UUID]]
    ):
        """
        Store hadith in ChromaDB for vector search.

        Args:
            hadith_id: Hadith ID
            text: Hadith text
            embedding: Pre-computed embedding
            resolved_ids: Resolved entity UUIDs
        """
        collection = get_or_create_collection()

        collection.add(
            ids=[str(hadith_id)],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "hadith_id": hadith_id,
                "text": text[:500],
                "people_count": len(resolved_ids["people"]),
                "places_count": len(resolved_ids["places"]),
                "topics_count": len(resolved_ids["topics"])
            }]
        )

        logger.debug(f"Stored hadith {hadith_id} in ChromaDB")

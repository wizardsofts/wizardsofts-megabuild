"""
Hybrid retriever combining vector search (ChromaDB) and graph context (Neo4j)
"""

from typing import List, Dict, Any
from loguru import logger

from src.utils.database import get_or_create_collection, execute_neo4j_query
from src.utils.embeddings import get_embedding
from src.config import get_settings

settings = get_settings()


class HybridRetriever:
    """Retrieve hadiths using vector similarity + graph context"""

    def __init__(self):
        self.collection = get_or_create_collection()

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        similarity_threshold: float = None,
        topic_filter: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant hadiths using hybrid approach.

        Args:
            query: User query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            topic_filter: Filter by topics

        Returns:
            List of hadith results with graph context
        """
        top_k = top_k or settings.rag_top_k
        threshold = similarity_threshold or settings.rag_similarity_threshold

        logger.info(f"Retrieving hadiths for query: '{query}' (top_k={top_k})")

        # Step 1: Vector search in ChromaDB
        logger.debug("Step 1: Vector search...")
        query_embedding = get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # Get more candidates for filtering
            include=["documents", "metadatas", "distances"]
        )

        if not results["ids"] or not results["ids"][0]:
            logger.warning("No results from vector search")
            return []

        # Extract hadith IDs and scores
        hadith_ids = [int(id) for id in results["ids"][0]]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Convert distances to similarity scores (cosine similarity = 1 - distance)
        similarities = [1 - dist for dist in distances]

        # Step 2: Filter by similarity threshold
        filtered_results = []
        for hadith_id, doc, meta, similarity in zip(hadith_ids, documents, metadatas, similarities):
            if similarity >= threshold:
                filtered_results.append({
                    "hadith_id": hadith_id,
                    "text": doc,
                    "metadata": meta,
                    "similarity_score": similarity
                })

        logger.info(f"Vector search: {len(filtered_results)} results above threshold {threshold}")

        # Step 3: Enrich with graph context from Neo4j
        logger.debug("Step 2: Enriching with graph context...")
        enriched_results = []

        for result in filtered_results[:top_k]:  # Limit to top_k
            hadith_id = result["hadith_id"]

            # Get graph context
            graph_context = self._get_graph_context(hadith_id)

            enriched_results.append({
                **result,
                "graph_context": graph_context
            })

        return enriched_results

    def _get_graph_context(self, hadith_id: int) -> Dict[str, Any]:
        """
        Get graph context for a hadith from Neo4j.

        Args:
            hadith_id: Hadith ID

        Returns:
            Dictionary with related entities and relationships
        """
        query = """
        MATCH (h:Hadith {hadith_id: $hadith_id})
        OPTIONAL MATCH (h)-[:MENTIONS_PERSON]->(p:Person)
        OPTIONAL MATCH (h)-[:MENTIONS_PLACE]->(place:Place)
        OPTIONAL MATCH (h)-[:ABOUT_TOPIC]->(t:Topic)
        OPTIONAL MATCH (h)-[:DESCRIBES_EVENT]->(e:Event)
        RETURN
            collect(DISTINCT {id: p.id, name: p.canonical_name}) as people,
            collect(DISTINCT {id: place.id, name: place.canonical_name}) as places,
            collect(DISTINCT {id: t.id, name: t.canonical_name, category: t.category}) as topics,
            collect(DISTINCT {id: e.id, name: e.canonical_name}) as events
        """

        try:
            results = execute_neo4j_query(query, {"hadith_id": hadith_id})

            if results:
                context = results[0]
                return {
                    "people": [p for p in context.get("people", []) if p.get("id")],
                    "places": [p for p in context.get("places", []) if p.get("id")],
                    "topics": [t for t in context.get("topics", []) if t.get("id")],
                    "events": [e for e in context.get("events", []) if e.get("id")]
                }

        except Exception as e:
            logger.error(f"Failed to get graph context for hadith {hadith_id}: {e}")

        return {"people": [], "places": [], "topics": [], "events": []}

    def find_related_hadiths(self, hadith_id: int, limit: int = 5) -> List[int]:
        """
        Find hadiths related through shared entities.

        Args:
            hadith_id: Source hadith ID
            limit: Maximum number of related hadiths

        Returns:
            List of related hadith IDs
        """
        query = """
        MATCH (h1:Hadith {hadith_id: $hadith_id})
        MATCH (h1)-[:ABOUT_TOPIC]->(t:Topic)<-[:ABOUT_TOPIC]-(h2:Hadith)
        WHERE h1 <> h2
        RETURN h2.hadith_id as hadith_id, count(t) as shared_topics
        ORDER BY shared_topics DESC
        LIMIT $limit
        """

        try:
            results = execute_neo4j_query(query, {"hadith_id": hadith_id, "limit": limit})
            return [r["hadith_id"] for r in results]

        except Exception as e:
            logger.error(f"Failed to find related hadiths: {e}")
            return []

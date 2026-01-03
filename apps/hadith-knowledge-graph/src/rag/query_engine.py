"""
RAG query engine for answering questions about Hadith
"""

import time
from typing import List, Dict, Any
from loguru import logger

from src.rag.retriever import HybridRetriever
from src.config import get_settings

settings = get_settings()


class RAGQueryEngine:
    """Query engine for Hadith Q&A using RAG"""

    def __init__(self):
        self.retriever = HybridRetriever()

    def query(
        self,
        question: str,
        top_k: int = None,
        similarity_threshold: float = None,
        topic_filter: List[str] = None
    ) -> Dict[str, Any]:
        """
        Answer question using RAG retrieval.

        Args:
            question: User question
            top_k: Number of hadiths to retrieve
            similarity_threshold: Minimum similarity score
            topic_filter: Filter by topics

        Returns:
            Dictionary with results and metadata
        """
        start_time = time.time()
        logger.info(f"RAG query: '{question}'")

        # Retrieve relevant hadiths
        results = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            topic_filter=topic_filter
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Retrieved {len(results)} hadiths in {duration_ms}ms")

        return {
            "query": question,
            "results": results,
            "total_results": len(results),
            "processing_time_ms": duration_ms
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format a single result for display.

        Args:
            result: Result dictionary

        Returns:
            Formatted string
        """
        output = []
        output.append(f"Hadith #{result['hadith_id']} (similarity: {result['similarity_score']:.2f})")
        output.append(f"Text: {result['text'][:200]}...")

        context = result.get("graph_context", {})

        if context.get("people"):
            people = [p.get("name") for p in context["people"] if p.get("name")]
            output.append(f"People: {', '.join(people)}")

        if context.get("topics"):
            topics = [t.get("name") for t in context["topics"] if t.get("name")]
            output.append(f"Topics: {', '.join(topics)}")

        if context.get("places"):
            places = [p.get("name") for p in context["places"] if p.get("name")]
            output.append(f"Places: {', '.join(places)}")

        return "\n".join(output)

    def display_results(self, query_result: Dict[str, Any]):
        """
        Display query results.

        Args:
            query_result: Result from query() method
        """
        print(f"\n{'='*80}")
        print(f"Query: {query_result['query']}")
        print(f"Results: {query_result['total_results']} hadiths")
        print(f"Time: {query_result['processing_time_ms']}ms")
        print(f"{'='*80}\n")

        for i, result in enumerate(query_result["results"], 1):
            print(f"\n[{i}] {self.format_result(result)}")
            print(f"{'-'*80}")

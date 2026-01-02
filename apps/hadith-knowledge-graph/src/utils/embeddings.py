"""
Embedding generation utilities using local models (Ollama)
"""

import httpx
from typing import List
from loguru import logger

from src.config import get_settings

settings = get_settings()


def get_embedding(text: str, model: str = None) -> List[float]:
    """
    Generate embedding vector for text using Ollama.

    Args:
        text: Text to embed
        model: Model name (defaults to settings)

    Returns:
        Embedding vector (768-dimensional for nomic-embed-text)

    Raises:
        Exception if embedding generation fails
    """
    model = model or settings.ollama_embedding_model

    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={
                "model": model,
                "prompt": text
            },
            timeout=30.0
        )
        response.raise_for_status()

        data = response.json()
        embedding = data.get("embedding")

        if not embedding:
            raise ValueError("No embedding returned from Ollama")

        logger.debug(f"Generated embedding for text (length: {len(text)}, dims: {len(embedding)})")
        return embedding

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def get_embeddings_batch(texts: List[str], model: str = None) -> List[List[float]]:
    """
    Generate embeddings for multiple texts (sequential for now).

    Args:
        texts: List of texts to embed
        model: Model name (defaults to settings)

    Returns:
        List of embedding vectors

    Note:
        For large batches, consider using Ray for parallel processing.
    """
    model = model or settings.ollama_embedding_model
    embeddings = []

    for i, text in enumerate(texts):
        try:
            embedding = get_embedding(text, model=model)
            embeddings.append(embedding)

            if (i + 1) % 10 == 0:
                logger.info(f"Generated {i + 1}/{len(texts)} embeddings")

        except Exception as e:
            logger.error(f"Failed to generate embedding for text {i}: {e}")
            # Return zero vector as fallback
            embeddings.append([0.0] * 768)

    return embeddings


def get_embedding_function():
    """
    Get embedding function compatible with ChromaDB.

    Returns:
        Callable that generates embeddings for ChromaDB
    """
    def embed_fn(texts: List[str]) -> List[List[float]]:
        """ChromaDB-compatible embedding function"""
        return get_embeddings_batch(texts)

    return embed_fn

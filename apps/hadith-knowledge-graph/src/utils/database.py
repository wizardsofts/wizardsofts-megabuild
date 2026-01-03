"""
Database connection utilities for PostgreSQL, Neo4j, and ChromaDB
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from neo4j import GraphDatabase, Driver
import chromadb
from chromadb.config import Settings
from loguru import logger

from src.config import get_settings

settings = get_settings()


# ============================================
# PostgreSQL
# ============================================

# Create engine with connection pooling
engine = create_engine(
    settings.postgres_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.log_level == "DEBUG"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get PostgreSQL database session with automatic cleanup.

    Usage:
        with get_db_session() as db:
            result = db.query(PersonEntity).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


# ============================================
# Neo4j
# ============================================

_neo4j_driver: Driver | None = None


def get_neo4j_driver() -> Driver:
    """
    Get Neo4j driver singleton with connection pooling.

    Returns:
        Neo4j Driver instance
    """
    global _neo4j_driver

    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=50,
            connection_acquisition_timeout=60.0
        )
        # Verify connectivity
        _neo4j_driver.verify_connectivity()
        logger.info("Neo4j driver initialized successfully")

    return _neo4j_driver


@contextmanager
def get_neo4j_session():
    """
    Get Neo4j session with automatic cleanup.

    Usage:
        with get_neo4j_session() as session:
            result = session.run("MATCH (n) RETURN count(n)")
    """
    driver = get_neo4j_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def execute_neo4j_query(query: str, parameters: dict = None):
    """
    Execute Neo4j query and return results.

    Args:
        query: Cypher query string
        parameters: Query parameters

    Returns:
        Query results
    """
    with get_neo4j_session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


# ============================================
# ChromaDB
# ============================================

_chroma_client: chromadb.HttpClient | None = None


def get_chroma_client() -> chromadb.HttpClient:
    """
    Get ChromaDB client singleton.

    Returns:
        ChromaDB HttpClient instance
    """
    global _chroma_client

    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        logger.info(f"ChromaDB client initialized: {settings.chroma_url}")

    return _chroma_client


def get_or_create_collection(collection_name: str = None):
    """
    Get or create ChromaDB collection for hadith embeddings.

    Args:
        collection_name: Collection name (defaults to settings)

    Returns:
        ChromaDB Collection instance
    """
    client = get_chroma_client()
    name = collection_name or settings.chroma_collection_name

    try:
        collection = client.get_collection(name=name)
        logger.info(f"Retrieved existing collection: {name}")
    except Exception:
        collection = client.create_collection(
            name=name,
            metadata={"description": "Hadith text embeddings for RAG retrieval"}
        )
        logger.info(f"Created new collection: {name}")

    return collection


# ============================================
# Cleanup
# ============================================

def close_all_connections():
    """Close all database connections."""
    global _neo4j_driver, _chroma_client

    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Neo4j driver closed")

    # ChromaDB HTTP client doesn't need explicit closing
    _chroma_client = None

    # Dispose SQLAlchemy engine
    engine.dispose()
    logger.info("PostgreSQL engine disposed")

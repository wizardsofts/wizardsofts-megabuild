"""
Hadith Knowledge Graph Data Models

This package contains:
- SQLAlchemy ORM models for PostgreSQL
- Pydantic models for validation
- Neo4j node/relationship definitions
"""

from .entities import (
    PersonEntity,
    PlaceEntity,
    EventEntity,
    TopicEntity,
    HadithVector,
    EntityMerge,
    ExtractionJob
)

from .schemas import (
    PersonCreate,
    PersonResponse,
    PlaceCreate,
    PlaceResponse,
    EventCreate,
    EventResponse,
    TopicCreate,
    TopicResponse,
    ExtractionOutput,
    EntityResolutionDecision
)

__all__ = [
    # ORM Models
    "PersonEntity",
    "PlaceEntity",
    "EventEntity",
    "TopicEntity",
    "HadithVector",
    "EntityMerge",
    "ExtractionJob",

    # Pydantic Schemas
    "PersonCreate",
    "PersonResponse",
    "PlaceCreate",
    "PlaceResponse",
    "EventCreate",
    "EventResponse",
    "TopicCreate",
    "TopicResponse",
    "ExtractionOutput",
    "EntityResolutionDecision",
]

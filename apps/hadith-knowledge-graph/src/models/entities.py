"""
SQLAlchemy ORM Models for Hadith Knowledge Graph

Maps to PostgreSQL entity tables.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, ARRAY, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class PersonEntity(Base):
    """Person entity (narrators, prophets, companions, scholars)"""
    __tablename__ = "entities_people"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Canonical identification
    canonical_name_en = Column(String(255), nullable=False)
    canonical_name_ar = Column(String(255))
    normalization_key = Column(String(255), nullable=False, unique=True, index=True)
    phonetic_key = Column(String(50), index=True)

    # Name variations
    name_variants = Column(JSONB, default=list)

    # Biographical data
    person_type = Column(String(50), index=True)  # prophet, companion, narrator, scholar
    birth_year = Column(Integer)
    death_year = Column(Integer)
    birth_year_hijri = Column(Integer)
    death_year_hijri = Column(Integer)

    # Narrator-specific
    reliability_grade = Column(String(50))  # trustworthy, weak, fabricator
    narrator_tier = Column(Integer)  # Generation (Sahaba=1, Tabi'un=2, etc.)

    # Rich metadata
    attributes = Column(JSONB, default=dict)

    # Data quality
    confidence_score = Column(Float, default=0.0)
    data_sources = Column(JSONB, default=list)
    last_verified_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_people_search', 'canonical_name_en', postgresql_using='gin',
              postgresql_ops={'canonical_name_en': 'gin_trgm_ops'}),
    )


class PlaceEntity(Base):
    """Place entity (cities, regions, mosques, battlefields)"""
    __tablename__ = "entities_places"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Canonical identification
    canonical_name_en = Column(String(255), nullable=False)
    canonical_name_ar = Column(String(255))
    normalization_key = Column(String(255), nullable=False, unique=True, index=True)
    name_variants = Column(JSONB, default=list)

    # Geographic hierarchy
    place_type = Column(String(50), index=True)  # city, region, mosque, mountain
    parent_place_id = Column(PGUUID(as_uuid=True), ForeignKey('entities_places.id'))
    modern_name = Column(String(255))
    modern_country = Column(String(100))

    # Coordinates
    latitude = Column(Float)
    longitude = Column(Float)

    # Metadata
    attributes = Column(JSONB, default=dict)
    confidence_score = Column(Float, default=0.0)
    data_sources = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_place = relationship("PlaceEntity", remote_side=[id], backref="sub_places")


class EventEntity(Base):
    """Event entity (battles, migrations, treaties, revelations)"""
    __tablename__ = "entities_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Canonical identification
    canonical_name_en = Column(String(255), nullable=False)
    canonical_name_ar = Column(String(255))
    normalization_key = Column(String(255), nullable=False, unique=True, index=True)
    name_variants = Column(JSONB, default=list)

    # Event classification
    event_type = Column(String(50), index=True)  # battle, migration, treaty
    event_category = Column(String(50))  # military, political, religious

    # Temporal data
    date_gregorian = Column(DateTime)
    date_hijri_year = Column(Integer, index=True)
    date_hijri_month = Column(Integer)
    date_hijri_day = Column(Integer)
    date_precision = Column(String(20))  # exact, month, year, approximate

    # Descriptions
    description_en = Column(Text)
    description_ar = Column(Text)

    # Metadata
    attributes = Column(JSONB, default=dict)
    confidence_score = Column(Float, default=0.0)
    data_sources = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicEntity(Base):
    """Topic/Concept entity with semantic embeddings"""
    __tablename__ = "entities_topics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Canonical identification
    canonical_name_en = Column(String(255), nullable=False)
    canonical_name_ar = Column(String(255))
    normalization_key = Column(String(255), nullable=False, unique=True, index=True)
    name_variants = Column(JSONB, default=list)

    # Topic taxonomy
    topic_type = Column(String(50))  # theological, legal, ethical, historical
    category = Column(String(100), index=True)  # prayer, fasting, business
    subcategory = Column(String(100))

    # Hierarchy
    parent_topic_id = Column(PGUUID(as_uuid=True), ForeignKey('entities_topics.id'))
    topic_level = Column(Integer, default=0)  # 0=root, 1=category, 2=subcategory

    # Descriptions
    definition_en = Column(Text)
    definition_ar = Column(Text)

    # Semantic embeddings
    embedding_vector = Column(Vector(1536))  # OpenAI text-embedding-3-large

    # Metadata
    attributes = Column(JSONB, default=dict)
    confidence_score = Column(Float, default=0.0)
    data_sources = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_topic = relationship("TopicEntity", remote_side=[id], backref="sub_topics")


class HadithVector(Base):
    """Vector embeddings for hadith text (RAG retrieval)"""
    __tablename__ = "hadith_vectors"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    hadith_id = Column(Integer, nullable=False, index=True)  # FK to hadiths table

    # Vector embedding
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-large

    # Chunk info
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)

    # Minimal metadata (most data in hadiths table)
    metadata = Column(JSONB, nullable=False)

    # Embedding metadata
    embedding_model = Column(String(100), default='text-embedding-3-large')
    embedding_created_at = Column(DateTime, default=datetime.utcnow)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_hadith_chunk', 'hadith_id', 'chunk_index'),
    )


class EntityMerge(Base):
    """Audit trail for entity deduplication"""
    __tablename__ = "entity_merges"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    source_entity_type = Column(String(50), nullable=False, index=True)
    source_entity_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    target_entity_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    merge_decision = Column(JSONB, nullable=False)
    merge_method = Column(String(50))  # automated, human_reviewed, manual
    merged_by = Column(String(255))
    merged_at = Column(DateTime, default=datetime.utcnow)

    # Rollback capability
    can_rollback = Column(Boolean, default=True)
    rollback_data = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)


class ExtractionJob(Base):
    """Track batch extraction job status"""
    __tablename__ = "extraction_jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    job_type = Column(String(50), nullable=False)  # full_extraction, incremental
    status = Column(String(50), nullable=False, index=True)  # pending, running, completed, failed

    # Job parameters
    hadith_ids = Column(JSONB)  # Array of hadith IDs
    total_hadiths = Column(Integer)
    processed_hadiths = Column(Integer, default=0)
    failed_hadiths = Column(Integer, default=0)

    # Metrics
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Results
    extraction_summary = Column(JSONB)
    errors = Column(JSONB, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

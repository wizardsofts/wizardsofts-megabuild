"""
Pydantic Schemas for Validation and API Responses
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# BASE SCHEMAS
# ============================================

class EntityBase(BaseModel):
    """Base schema for all entities"""
    canonical_name_en: str
    canonical_name_ar: Optional[str] = None
    normalization_key: str
    name_variants: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    data_sources: List[str] = Field(default_factory=list)


# ============================================
# PERSON SCHEMAS
# ============================================

class PersonCreate(EntityBase):
    """Schema for creating a person entity"""
    phonetic_key: Optional[str] = None
    person_type: Optional[str] = None  # prophet, companion, narrator, scholar
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    birth_year_hijri: Optional[int] = None
    death_year_hijri: Optional[int] = None
    reliability_grade: Optional[str] = None
    narrator_tier: Optional[int] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class PersonResponse(PersonCreate):
    """Schema for person entity response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PLACE SCHEMAS
# ============================================

class PlaceCreate(EntityBase):
    """Schema for creating a place entity"""
    place_type: Optional[str] = None  # city, region, mosque, mountain
    parent_place_id: Optional[UUID] = None
    modern_name: Optional[str] = None
    modern_country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class PlaceResponse(PlaceCreate):
    """Schema for place entity response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EVENT SCHEMAS
# ============================================

class EventCreate(EntityBase):
    """Schema for creating an event entity"""
    event_type: Optional[str] = None  # battle, migration, treaty
    event_category: Optional[str] = None  # military, political, religious
    date_hijri_year: Optional[int] = None
    date_hijri_month: Optional[int] = None
    date_hijri_day: Optional[int] = None
    date_precision: Optional[str] = None  # exact, month, year, approximate
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class EventResponse(EventCreate):
    """Schema for event entity response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# TOPIC SCHEMAS
# ============================================

class TopicCreate(EntityBase):
    """Schema for creating a topic entity"""
    topic_type: Optional[str] = None  # theological, legal, ethical
    category: Optional[str] = None  # prayer, fasting, business
    subcategory: Optional[str] = None
    parent_topic_id: Optional[UUID] = None
    topic_level: int = 0
    definition_en: Optional[str] = None
    definition_ar: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TopicResponse(TopicCreate):
    """Schema for topic entity response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EXTRACTION OUTPUT SCHEMAS
# ============================================

class ExtractedEntity(BaseModel):
    """Schema for an extracted entity (before resolution)"""
    canonical_name_en: str
    canonical_name_ar: Optional[str] = None
    variants: List[str] = Field(default_factory=list)
    normalization_key: str
    phonetic_key: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    text_span: str
    span_indices: tuple[int, int]
    context: str

    # Resolution result
    matched_entity_id: Optional[UUID] = None
    is_new_entity: bool = False
    match_method: Optional[str] = None
    match_confidence: Optional[float] = None
    suggested_attributes: Dict[str, Any] = Field(default_factory=dict)


class ExtractedPerson(ExtractedEntity):
    """Schema for extracted person entity"""
    person_type: Optional[str] = None
    reliability_grade: Optional[str] = None
    narrator_tier: Optional[int] = None


class ExtractedPlace(ExtractedEntity):
    """Schema for extracted place entity"""
    place_type: Optional[str] = None


class ExtractedEvent(ExtractedEntity):
    """Schema for extracted event entity"""
    event_type: Optional[str] = None
    extracted_date: Optional[Dict[str, Any]] = None


class ExtractedTopic(ExtractedEntity):
    """Schema for extracted topic entity"""
    topic_type: Optional[str] = None
    category: Optional[str] = None
    embedding_vector: Optional[List[float]] = None


class ExtractedRelationship(BaseModel):
    """Schema for an extracted relationship"""
    source: Dict[str, Any]  # {type: str, id: UUID/int}
    target: Dict[str, Any]  # {type: str, id: UUID/int}
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class QuranReference(BaseModel):
    """Schema for Quran verse reference"""
    surah: int = Field(ge=1, le=114)
    ayah: int = Field(ge=1)
    reference_type: Literal["explicit", "implicit", "thematic"] = "explicit"
    relationship: str
    confidence: float = Field(ge=0.0, le=1.0)
    text_span: Optional[str] = None
    span_indices: Optional[tuple[int, int]] = None


class SemanticSummary(BaseModel):
    """Schema for semantic summary of hadith"""
    main_theme: str
    key_teachings: List[str]
    fiqh_ruling: Optional[str] = None
    madhab_consensus: bool = False
    tags: List[str] = Field(default_factory=list)
    summary_en: str
    summary_ar: Optional[str] = None


class QualityMetrics(BaseModel):
    """Schema for extraction quality metrics"""
    overall_confidence: float = Field(ge=0.0, le=1.0)
    entity_extraction_confidence: float = Field(ge=0.0, le=1.0)
    relationship_confidence: float = Field(ge=0.0, le=1.0)
    topic_classification_confidence: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)


class ProcessingLog(BaseModel):
    """Schema for processing stage log"""
    stage: str
    status: Literal["success", "failed", "skipped"]
    duration_ms: int
    details: Dict[str, Any] = Field(default_factory=dict)


class ExtractionOutput(BaseModel):
    """Schema for complete extraction output"""
    extraction_metadata: Dict[str, Any]
    source_text: Dict[str, str]  # arabic, english, matn_ar, matn_en, isnad_ar, isnad_en

    # Extracted entities
    extracted_entities: Dict[str, List[Any]]  # people, places, events, topics

    # Extracted relationships
    extracted_relationships: List[ExtractedRelationship]

    # Quran references
    quran_references: List[QuranReference] = Field(default_factory=list)

    # Semantic summary
    semantic_summary: SemanticSummary

    # Quality metrics
    quality_metrics: QualityMetrics

    # Processing log
    processing_log: List[ProcessingLog]


# ============================================
# ENTITY RESOLUTION SCHEMAS
# ============================================

class PotentialMatch(BaseModel):
    """Schema for a potential entity match"""
    existing_entity_id: UUID
    canonical_name: str
    match_scores: Dict[str, float]
    match_evidence: List[str]
    recommended_action: Literal["MERGE", "CREATE_NEW", "LINK_AS_VARIANT", "SKIP"]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = False


class EntityResolutionDecision(BaseModel):
    """Schema for entity resolution decision"""
    candidate_entity: Dict[str, Any]
    potential_matches: List[PotentialMatch]
    resolution_decision: Dict[str, Any]


# ============================================
# HADITH VECTOR SCHEMAS
# ============================================

class HadithVectorMetadata(BaseModel):
    """Schema for hadith vector metadata"""
    hadith_id: int
    chunk_index: int = 0
    reference: str  # "Bukhari 520"
    grading: str  # "Sahih"
    primary_topics: List[str] = Field(default_factory=list)


class HadithVectorCreate(BaseModel):
    """Schema for creating hadith vector"""
    hadith_id: int
    embedding: List[float]
    chunk_index: int = 0
    chunk_text: str
    metadata: HadithVectorMetadata


class HadithVectorResponse(BaseModel):
    """Schema for hadith vector response"""
    id: UUID
    hadith_id: int
    chunk_index: int
    metadata: HadithVectorMetadata
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# RAG QUERY SCHEMAS
# ============================================

class RAGQuery(BaseModel):
    """Schema for RAG query request"""
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    topic_filter: Optional[List[str]] = None
    grading_filter: Optional[List[str]] = None
    use_graph_context: bool = True


class RAGResult(BaseModel):
    """Schema for RAG query result"""
    hadith_id: int
    text_en: str
    text_ar: Optional[str] = None
    reference: str
    grading: str
    similarity_score: float
    graph_context: Optional[Dict[str, Any]] = None
    entities: Dict[str, List[str]] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    """Schema for RAG query response"""
    query: str
    results: List[RAGResult]
    total_results: int
    processing_time_ms: int


# ============================================
# JOB STATUS SCHEMAS
# ============================================

class JobStatus(BaseModel):
    """Schema for extraction job status"""
    job_id: UUID
    job_type: str
    status: Literal["pending", "running", "completed", "failed"]
    total_hadiths: int
    processed_hadiths: int
    failed_hadiths: int
    progress_percentage: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    extraction_summary: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

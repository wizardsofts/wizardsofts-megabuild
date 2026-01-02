-- ============================================
-- Hadith Knowledge Graph Database Schema
-- (Without pgvector - using ChromaDB for vectors)
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- PEOPLE ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS entities_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Canonical identification
    canonical_name_en VARCHAR(255) NOT NULL,
    canonical_name_ar VARCHAR(255),
    normalization_key VARCHAR(255) NOT NULL UNIQUE,
    phonetic_key VARCHAR(50),

    -- Name variations for fuzzy matching
    name_variants JSONB DEFAULT '[]'::jsonb,

    -- Biographical data
    person_type VARCHAR(50),  -- prophet, companion, narrator, scholar, etc.
    birth_year INTEGER,
    death_year INTEGER,
    birth_year_hijri INTEGER,
    death_year_hijri INTEGER,

    -- Narrator-specific fields
    reliability_grade VARCHAR(50),  -- trustworthy, weak, fabricator, etc.
    narrator_tier INTEGER,          -- Generation (Sahaba=1, Tabi'un=2, etc.)

    -- Rich metadata (evolves over time)
    attributes JSONB DEFAULT '{}'::jsonb,

    -- Data quality
    confidence_score FLOAT DEFAULT 0.0,
    data_sources JSONB DEFAULT '[]'::jsonb,
    last_verified_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(canonical_name_en, '') || ' ' ||
            coalesce(name_variants::text, '')
        )
    ) STORED
);

CREATE INDEX idx_people_normalization ON entities_people(normalization_key);
CREATE INDEX idx_people_phonetic ON entities_people(phonetic_key);
CREATE INDEX idx_people_search ON entities_people USING GIN(search_vector);
CREATE INDEX idx_people_attributes ON entities_people USING GIN(attributes);
CREATE INDEX idx_people_type ON entities_people(person_type);

-- ============================================
-- PLACES ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS entities_places (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Canonical identification
    canonical_name_en VARCHAR(255) NOT NULL,
    canonical_name_ar VARCHAR(255),
    normalization_key VARCHAR(255) NOT NULL UNIQUE,
    name_variants JSONB DEFAULT '[]'::jsonb,

    -- Geographic hierarchy
    place_type VARCHAR(50),  -- city, region, country, mosque, mountain, etc.
    parent_place_id UUID REFERENCES entities_places(id),
    modern_name VARCHAR(255),
    modern_country VARCHAR(100),

    -- Coordinates
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    -- Metadata
    attributes JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    data_sources JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(canonical_name_en, '') || ' ' ||
            coalesce(modern_name, '')
        )
    ) STORED
);

CREATE INDEX idx_places_normalization ON entities_places(normalization_key);
CREATE INDEX idx_places_search ON entities_places USING GIN(search_vector);
CREATE INDEX idx_places_attributes ON entities_places USING GIN(attributes);
CREATE INDEX idx_places_type ON entities_places(place_type);
CREATE INDEX idx_places_parent ON entities_places(parent_place_id);

-- ============================================
-- EVENTS ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS entities_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Canonical identification
    canonical_name_en VARCHAR(255) NOT NULL,
    canonical_name_ar VARCHAR(255),
    normalization_key VARCHAR(255) NOT NULL UNIQUE,
    name_variants JSONB DEFAULT '[]'::jsonb,

    -- Event details
    event_type VARCHAR(50),  -- battle, treaty, migration, revelation, etc.
    event_date VARCHAR(100),
    event_year_hijri INTEGER,

    -- Related entities (stored as references, mirrored in Neo4j for graph)
    related_people_ids UUID[],
    related_places_ids UUID[],

    -- Metadata
    description TEXT,
    attributes JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    data_sources JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(canonical_name_en, '') || ' ' ||
            coalesce(description, '')
        )
    ) STORED
);

CREATE INDEX idx_events_normalization ON entities_events(normalization_key);
CREATE INDEX idx_events_search ON entities_events USING GIN(search_vector);
CREATE INDEX idx_events_type ON entities_events(event_type);
CREATE INDEX idx_events_attributes ON entities_events USING GIN(attributes);

-- ============================================
-- TOPICS ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS entities_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Canonical identification
    canonical_name_en VARCHAR(255) NOT NULL,
    canonical_name_ar VARCHAR(255),
    normalization_key VARCHAR(255) NOT NULL UNIQUE,
    name_variants JSONB DEFAULT '[]'::jsonb,

    -- Topic hierarchy
    topic_category VARCHAR(100),    -- aqeedah, fiqh, akhlaq, seerah, etc.
    parent_topic_id UUID REFERENCES entities_topics(id),
    subcategory VARCHAR(100),

    -- Metadata
    description TEXT,
    attributes JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    data_sources JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(canonical_name_en, '') || ' ' ||
            coalesce(description, '') || ' ' ||
            coalesce(topic_category, '')
        )
    ) STORED
);

CREATE INDEX idx_topics_normalization ON entities_topics(normalization_key);
CREATE INDEX idx_topics_search ON entities_topics USING GIN(search_vector);
CREATE INDEX idx_topics_category ON entities_topics(topic_category);
CREATE INDEX idx_topics_attributes ON entities_topics USING GIN(attributes);
CREATE INDEX idx_topics_parent ON entities_topics(parent_topic_id);

-- ============================================
-- EXTRACTION JOBS (For tracking progress)
-- ============================================
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255),
    status VARCHAR(50),  -- pending, running, completed, failed
    total_hadiths INTEGER DEFAULT 0,
    processed_hadiths INTEGER DEFAULT 0,
    failed_hadiths INTEGER DEFAULT 0,

    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,

    job_metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_extraction_jobs_status ON extraction_jobs(status);
CREATE INDEX idx_extraction_jobs_started ON extraction_jobs(started_at);

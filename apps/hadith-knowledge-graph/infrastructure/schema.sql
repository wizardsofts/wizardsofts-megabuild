-- ============================================
-- Hadith Knowledge Graph Database Schema
-- ============================================

-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;
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
CREATE INDEX idx_places_parent ON entities_places(parent_place_id);
CREATE INDEX idx_places_search ON entities_places USING GIN(search_vector);
CREATE INDEX idx_places_type ON entities_places(place_type);

-- ============================================
-- EVENTS ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS entities_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    canonical_name_en VARCHAR(255) NOT NULL,
    canonical_name_ar VARCHAR(255),
    normalization_key VARCHAR(255) NOT NULL UNIQUE,
    name_variants JSONB DEFAULT '[]'::jsonb,

    -- Event classification
    event_type VARCHAR(50),
    event_category VARCHAR(50),

    -- Temporal data
    date_gregorian DATE,
    date_hijri_year INTEGER,
    date_hijri_month INTEGER,
    date_hijri_day INTEGER,
    date_precision VARCHAR(20),

    -- Descriptions
    description_en TEXT,
    description_ar TEXT,

    -- Metadata
    attributes JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    data_sources JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(canonical_name_en, '') || ' ' ||
            coalesce(description_en, '')
        )
    ) STORED
);

CREATE INDEX idx_events_normalization ON entities_events(normalization_key);
CREATE INDEX idx_events_date ON entities_events(date_gregorian, date_hijri_year);
CREATE INDEX idx_events_search ON entities_events USING GIN(search_vector);
CREATE INDEX idx_events_type ON entities_events(event_type);

-- ============================================
-- TOPICS/CONCEPTS ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS entities_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    canonical_name_en VARCHAR(255) NOT NULL,
    canonical_name_ar VARCHAR(255),
    normalization_key VARCHAR(255) NOT NULL UNIQUE,
    name_variants JSONB DEFAULT '[]'::jsonb,

    -- Topic taxonomy
    topic_type VARCHAR(50),
    category VARCHAR(100),
    subcategory VARCHAR(100),

    -- Hierarchy
    parent_topic_id UUID REFERENCES entities_topics(id),
    topic_level INTEGER DEFAULT 0,

    -- Descriptions
    definition_en TEXT,
    definition_ar TEXT,

    -- Semantic embeddings
    embedding_vector vector(1536),

    -- Metadata
    attributes JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    data_sources JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(canonical_name_en, '') || ' ' ||
            coalesce(definition_en, '')
        )
    ) STORED
);

CREATE INDEX idx_topics_normalization ON entities_topics(normalization_key);
CREATE INDEX idx_topics_parent ON entities_topics(parent_topic_id);
CREATE INDEX idx_topics_category ON entities_topics(category, subcategory);
CREATE INDEX idx_topics_search ON entities_topics USING GIN(search_vector);
CREATE INDEX idx_topics_embedding ON entities_topics USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- HADITH VECTORS (for RAG)
-- ============================================
CREATE TABLE IF NOT EXISTS hadith_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hadith_id INTEGER NOT NULL,  -- FK to hadiths table

    -- Vector embedding (English text only)
    embedding vector(1536),

    -- Chunk strategy
    chunk_index INTEGER DEFAULT 0,
    chunk_text TEXT NOT NULL,  -- The actual text that was embedded

    -- Minimal metadata (most data in hadiths table)
    metadata JSONB NOT NULL,

    -- Embedding metadata
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-large',
    embedding_created_at TIMESTAMP DEFAULT NOW(),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_hadith_vectors_hadith ON hadith_vectors(hadith_id);
CREATE INDEX idx_hadith_vectors_chunk ON hadith_vectors(hadith_id, chunk_index);
CREATE INDEX idx_hadith_embedding ON hadith_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_hadith_metadata ON hadith_vectors USING GIN(metadata);

-- ============================================
-- ENTITY MERGES (Audit Trail)
-- ============================================
CREATE TABLE IF NOT EXISTS entity_merges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_entity_type VARCHAR(50) NOT NULL,
    source_entity_id UUID NOT NULL,
    target_entity_id UUID NOT NULL,

    merge_decision JSONB NOT NULL,
    merge_method VARCHAR(50),  -- automated, human_reviewed, manual
    merged_by VARCHAR(255),
    merged_at TIMESTAMP DEFAULT NOW(),

    -- Rollback capability
    can_rollback BOOLEAN DEFAULT TRUE,
    rollback_data JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_merge_source ON entity_merges(source_entity_id);
CREATE INDEX idx_merge_target ON entity_merges(target_entity_id);
CREATE INDEX idx_merge_type ON entity_merges(source_entity_type);

-- ============================================
-- EXTRACTION JOBS (Track processing)
-- ============================================
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    job_type VARCHAR(50) NOT NULL,  -- full_extraction, incremental, reprocessing
    status VARCHAR(50) NOT NULL,    -- pending, running, completed, failed

    -- Job parameters
    hadith_ids JSONB,  -- Array of hadith IDs to process
    total_hadiths INTEGER,
    processed_hadiths INTEGER DEFAULT 0,
    failed_hadiths INTEGER DEFAULT 0,

    -- Metrics
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Results
    extraction_summary JSONB,
    errors JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_extraction_jobs_status ON extraction_jobs(status);
CREATE INDEX idx_extraction_jobs_created ON extraction_jobs(created_at DESC);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to normalize names for deduplication
CREATE OR REPLACE FUNCTION normalize_name(name TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            regexp_replace(
                unaccent(name),  -- Remove diacritics
                '[^a-z0-9]', '', 'g'  -- Remove non-alphanumeric
            ),
            '^(al|ibn|bin|bint)', '', 'i'  -- Remove common prefixes
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_entities_people_updated_at BEFORE UPDATE ON entities_people
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_places_updated_at BEFORE UPDATE ON entities_places
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_events_updated_at BEFORE UPDATE ON entities_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_topics_updated_at BEFORE UPDATE ON entities_topics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View: All entities with type
CREATE OR REPLACE VIEW all_entities AS
SELECT
    'people' as entity_type,
    id,
    canonical_name_en,
    canonical_name_ar,
    normalization_key,
    confidence_score,
    created_at
FROM entities_people
UNION ALL
SELECT
    'places' as entity_type,
    id,
    canonical_name_en,
    canonical_name_ar,
    normalization_key,
    confidence_score,
    created_at
FROM entities_places
UNION ALL
SELECT
    'events' as entity_type,
    id,
    canonical_name_en,
    canonical_name_ar,
    normalization_key,
    confidence_score,
    created_at
FROM entities_events
UNION ALL
SELECT
    'topics' as entity_type,
    id,
    canonical_name_en,
    canonical_name_ar,
    normalization_key,
    confidence_score,
    created_at
FROM entities_topics;

-- View: Extraction statistics
CREATE OR REPLACE VIEW extraction_statistics AS
SELECT
    (SELECT COUNT(*) FROM entities_people) as total_people,
    (SELECT COUNT(*) FROM entities_places) as total_places,
    (SELECT COUNT(*) FROM entities_events) as total_events,
    (SELECT COUNT(*) FROM entities_topics) as total_topics,
    (SELECT COUNT(*) FROM hadith_vectors) as total_vectors,
    (SELECT COUNT(DISTINCT hadith_id) FROM hadith_vectors) as hadiths_vectorized,
    (SELECT COUNT(*) FROM entity_merges) as total_merges;

COMMENT ON TABLE entities_people IS 'Stores person entities (narrators, prophets, companions, scholars)';
COMMENT ON TABLE entities_places IS 'Stores geographic entities (cities, regions, mosques, etc.)';
COMMENT ON TABLE entities_events IS 'Stores historical events (battles, migrations, treaties, etc.)';
COMMENT ON TABLE entities_topics IS 'Stores topics and concepts with semantic embeddings';
COMMENT ON TABLE hadith_vectors IS 'Stores vector embeddings of hadith text for RAG retrieval';
COMMENT ON TABLE entity_merges IS 'Audit trail for entity deduplication and merges';
COMMENT ON TABLE extraction_jobs IS 'Tracks batch extraction job status and metrics';

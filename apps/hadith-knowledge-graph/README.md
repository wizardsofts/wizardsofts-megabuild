# Hadith Knowledge Graph System

A comprehensive knowledge graph and RAG (Retrieval-Augmented Generation) system for Hadith text analysis, built with Neo4j, PostgreSQL, ChromaDB, and distributed processing via Ray+Celery.

## Architecture Overview

### Data Storage Strategy

```
PostgreSQL (Source of Truth)          Neo4j (Graph View)           ChromaDB (Vector Search)
─────────────────────────          ───────────────────          ──────────────────────
✅ entities_people                 ✅ (:Person) nodes           ✅ Hadith embeddings
✅ entities_places                 ✅ (:Place) nodes            ✅ Semantic search
✅ entities_topics                 ✅ (:Topic) nodes
✅ entities_events                 ✅ (:Event) nodes
✅ hadith_vectors                  ✅ ALL relationships
✅ Audit trails                    ✅ Isnad chains
```

### Key Design Decisions

1. **Hybrid Database Architecture**
   - PostgreSQL: Full entity data, vector embeddings, audit trails
   - Neo4j: Lightweight nodes + rich relationship graph
   - ChromaDB: Fast vector similarity search

2. **Entity Resolution**
   - `normalization_key`: Lowercase, no diacritics (e.g., "abuhurairah")
   - `phonetic_key`: Soundex for fuzzy matching across transliterations
   - `name_variants`: JSONB array of all known spellings

3. **Minimal Vector Metadata**
   - Store only: `hadith_id`, `chunk_index`, `reference`, `grading`, `primary_topics`
   - Query PostgreSQL + Neo4j at runtime for full context

4. **Relationship Management (Neo4j only)**
   - Use relationship properties instead of creating new types
   - Intermediate nodes for complex relationships
   - Confidence thresholds (>0.8) to prevent explosion

## Quick Start

### 1. Start Infrastructure

```bash
cd infrastructure
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# Check services are healthy
docker-compose ps
```

### 2. Initialize Databases

```bash
# PostgreSQL schema
psql -h localhost -U your_user -d dailydeenguide -f infrastructure/schema.sql

# Neo4j schema (from Neo4j browser at http://localhost:7474)
# Copy and paste contents of infrastructure/neo4j_schema.cypher
```

### 3. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy and edit .env file
cp infrastructure/.env.example .env

# Required settings:
# - POSTGRES_* (database connection)
# - OPENAI_API_KEY (for embeddings)
# - NEO4J_PASSWORD
```

## Project Structure

```
apps/hadith-knowledge-graph/
├── infrastructure/
│   ├── docker-compose.yml          # Neo4j, ChromaDB, Ollama, Redis
│   ├── schema.sql                  # PostgreSQL entity tables
│   ├── neo4j_schema.cypher         # Neo4j constraints & indexes
│   └── .env.example                # Environment configuration
├── src/
│   ├── models/
│   │   ├── entities.py             # SQLAlchemy ORM models
│   │   └── schemas.py              # Pydantic validation schemas
│   ├── extraction/
│   │   ├── entity_extractor.py     # LangChain entity extraction
│   │   ├── entity_resolver.py      # Name deduplication logic
│   │   ├── relationship_extractor.py
│   │   └── pipeline.py             # LangGraph orchestration
│   ├── rag/
│   │   ├── retriever.py            # Hybrid retrieval (vector + graph)
│   │   └── query_engine.py         # RAG query interface
│   ├── distributed/
│   │   ├── tasks.py                # Celery tasks
│   │   └── ray_workers.py          # Ray distributed workers
│   ├── utils/
│   │   ├── database.py             # DB connections
│   │   ├── text_processing.py     # Name normalization
│   │   └── embeddings.py           # OpenAI embedding wrapper
│   └── config.py                   # Settings management
├── scripts/
│   ├── init_db.py                  # Initialize databases
│   ├── extract_500_samples.py      # Test extraction on 500 hadiths
│   └── test_queries.py             # Example RAG & graph queries
├── tests/
│   ├── test_entity_resolution.py
│   ├── test_extraction.py
│   └── test_rag.py
├── docs/
│   └── ARCHITECTURE.md             # Detailed architecture docs
├── requirements.txt
└── README.md (this file)
```

## Core Concepts

### Entity Types

1. **Person** (`entities_people`)
   - Narrators, prophets, companions, scholars
   - Reliability grades for Hadith authentication
   - Narrator tiers (Sahaba=1, Tabi'un=2, etc.)

2. **Place** (`entities_places`)
   - Cities, regions, mosques, battlefields
   - Hierarchical (parent_place_id)
   - Modern names + historical context

3. **Event** (`entities_events`)
   - Battles, migrations, treaties, revelations
   - Hijri/Gregorian dates with precision levels
   - Participants linked via Neo4j

4. **Topic** (`entities_topics`)
   - Theological, legal, ethical, historical
   - Hierarchical taxonomy
   - Semantic embeddings for similarity

### Relationship Types (Neo4j)

```cypher
// Narration Chain (Isnad)
(h:Hadith)-[:NARRATED_BY]->(p:Person)
(p1:Person)-[:HEARD_FROM]->(p2:Person)

// Content Relationships
(h:Hadith)-[:MENTIONS_PLACE {context: "event_location"}]->(place:Place)
(h:Hadith)-[:ABOUT_TOPIC {relevance: 0.95}]->(t:Topic)
(h:Hadith)-[:DESCRIBES_EVENT]->(e:Event)
(h:Hadith)-[:REFERENCES_QURAN]->(v:QuranVerse)

// Event Relationships
(e:Event)-[:OCCURRED_AT]->(place:Place)
(e:Event)-[:HAD_PARTICIPANT {role: "commander"}]->(p:Person)

// Educational Relationships
(p1:Person)-[:STUDIED_UNDER]->(p2:Person)
```

### Extraction Pipeline (LangGraph)

```
Hadith Text
     ↓
1. Entity Extraction (LangChain + GPT-4)
   → People, Places, Events, Topics
     ↓
2. Entity Resolution (Fuzzy Matching)
   → Match to existing or create new
     ↓
3. Relationship Extraction
   → Narration chain, mentions, explains
     ↓
4. Topic Classification
   → Semantic embeddings + taxonomy
     ↓
5. Vector Embedding
   → OpenAI text-embedding-3-large
     ↓
6. Sync to Neo4j
   → Create nodes + relationships
     ↓
7. Store in ChromaDB
   → Vector for RAG retrieval
```

### RAG Query Flow

```
User Query
     ↓
1. Embedding (OpenAI)
     ↓
2. Vector Search (ChromaDB)
   → Top-K similar hadiths
     ↓
3. Graph Context (Neo4j)
   → Related entities, narrators, topics
     ↓
4. Merge & Rank
     ↓
5. Generate Response (LLM)
```

## Example Usage

### Query 500 Sample Hadiths

```bash
python scripts/extract_500_samples.py
```

This will:
1. Fetch 500 diverse hadiths from dailydeenguide database
2. Extract entities and relationships
3. Store in PostgreSQL, Neo4j, ChromaDB
4. Generate extraction report

### RAG Query Example

```python
from src.rag import RAGQueryEngine

engine = RAGQueryEngine()

# Query hadiths about prayer times
results = engine.query(
    "What did the Prophet say about prayer times?",
    top_k=5,
    topic_filter=["prayer"]
)

for result in results:
    print(f"{result.reference}: {result.text_en}")
    print(f"Similarity: {result.similarity_score}")
    print(f"Narrators: {result.graph_context['narrators']}")
```

### Neo4j Graph Query

```cypher
// Find all hadiths narrated by Abu Hurairah about prayer
MATCH (h:Hadith)-[:NARRATED_BY]->(p:Person {canonical_name: "Abu Hurairah"})
MATCH (h)-[:ABOUT_TOPIC]->(t:Topic {category: "Salah"})
RETURN h.hadith_id, h.text_en, t.canonical_name
LIMIT 10;
```

## Distributed Processing (Ray + Celery)

### Ray for CPU-Intensive Tasks

```python
import ray
from src.distributed.ray_workers import extract_entities_batch

ray.init()

# Process 1000 hadiths in parallel
hadith_ids = list(range(1, 1001))
results = ray.get([
    extract_entities_batch.remote(batch)
    for batch in chunks(hadith_ids, 100)
])
```

### Celery for Background Jobs

```bash
# Start Celery worker
celery -A src.distributed.tasks worker --loglevel=info

# Submit extraction job
from src.distributed.tasks import extract_hadith_batch
job = extract_hadith_batch.delay(hadith_ids)
```

## Configuration

### Key Settings (.env)

```bash
# Database Credentials
POSTGRES_HOST=localhost
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=dailydeenguide

NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=hadithknowledge2025

# API Keys
OPENAI_API_KEY=sk-...

# Extraction Parameters
CONFIDENCE_THRESHOLD=0.8      # Minimum confidence for entity/relationship
BATCH_SIZE=10                  # Hadiths per batch
MAX_WORKERS=4                  # Parallel workers

# RAG Parameters
RAG_TOP_K=5                    # Number of results to return
RAG_SIMILARITY_THRESHOLD=0.7   # Minimum similarity score
```

## Next Steps

### Phase 1: Test with 500 Hadiths ✅ (This document)
- [x] Infrastructure setup
- [x] Database schemas
- [x] Data models
- [ ] Extraction pipeline implementation
- [ ] Entity resolution logic
- [ ] RAG query system
- [ ] Test with 500 samples
- [ ] Document gaps and improvements

### Phase 2: Full Implementation
- [ ] Complete extraction pipeline (LangChain + LangGraph)
- [ ] Implement distributed processing (Ray + Celery)
- [ ] Build web API (FastAPI)
- [ ] Create admin dashboard
- [ ] Full test coverage

### Phase 3: Production Deployment
- [ ] Process all hadiths in dailydeenguide database
- [ ] Optimize Neo4j indexes
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Deploy to Server 84

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check Neo4j is running
docker logs hadith-neo4j

# Test connection
curl http://localhost:7474
```

### PostgreSQL pgvector Extension
```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Test vector operations
SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector;
```

### ChromaDB Issues
```bash
# Check ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Reset collection (CAUTION: deletes all data)
curl -X DELETE http://localhost:8000/api/v1/collections/hadith_embeddings
```

## Contributing

This is an internal WizardSofts project. See [CLAUDE.md](/CLAUDE.md) for development guidelines.

## License

Proprietary - WizardSofts © 2025

# Hadith Knowledge Graph - Implementation Status

**Created:** 2026-01-03
**Git Branch:** `feature/hadith-knowledge-graph`
**Worktree Location:** `/Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/hadith-knowledge-graph`

## Executive Summary

A foundational architecture has been established for extracting, storing, and querying knowledge from Hadith texts using a hybrid database system (PostgreSQL + Neo4j + ChromaDB) with distributed processing capabilities (Ray + Celery).

### What's Been Built

✅ **Infrastructure Setup**
- Docker Compose configuration for all services
- Neo4j 5.15.0 with APOC plugins
- ChromaDB 0.4.22 for vector search
- Ollama for optional local LLM
- Redis for Celery task queue

✅ **Database Schemas**
- PostgreSQL entity tables (`entities_people`, `entities_places`, `entities_events`, `entities_topics`)
- Vector storage (`hadith_vectors` with pgvector)
- Audit trails (`entity_merges`, `extraction_jobs`)
- Neo4j constraints and indexes
- Full-text search indexes

✅ **Data Models**
- SQLAlchemy ORM models for all entities
- Pydantic validation schemas
- Extraction output templates
- Entity resolution decision structures

✅ **Architecture Design**
- Hybrid database strategy (PostgreSQL as source of truth, Neo4j for graph, ChromaDB for vectors)
- Entity deduplication workflow using normalization keys + phonetic keys
- Minimal vector metadata approach (query at runtime)
- Relationship modeling patterns

### What Needs Implementation

🔲 **Extraction Pipeline** (Priority: HIGH)
- LangChain entity extraction prompts
- LangGraph orchestration workflow
- Entity resolution fuzzy matching logic
- Isnad (narration chain) parser
- Topic classification using embeddings

🔲 **Database Utilities** (Priority: HIGH)
- PostgreSQL connection pooling
- Neo4j driver wrapper
- ChromaDB client setup
- Text processing functions (normalize_name, phonetic_key)
- Embedding generation wrapper

🔲 **RAG System** (Priority: MEDIUM)
- Hybrid retrieval (vector + graph)
- Context aggregation from Neo4j
- Query interface
- Reranking logic

🔲 **Distributed Processing** (Priority: MEDIUM)
- Ray workers for entity extraction
- Celery tasks for background jobs
- Job status tracking
- Error handling and retries

🔲 **Testing & Validation** (Priority: HIGH)
- Extract 500 sample hadiths
- Validate entity extraction accuracy
- Test graph query patterns
- Benchmark RAG retrieval quality
- Identify gaps and improvements

## Detailed Architecture

### 1. Data Flow

```
dailydeenguide.hadiths (PostgreSQL)
         ↓
    [Extraction Pipeline]
         ↓
    ┌────────────────┐
    │ LangChain      │  → Extract entities (people, places, events, topics)
    │ + GPT-4        │  → Extract relationships
    └────────────────┘
         ↓
    ┌────────────────┐
    │ Entity         │  → Fuzzy match existing entities
    │ Resolution     │  → Create new if no match
    └────────────────┘
         ↓
    ┌────────────────────────────────────────────┐
    │          Store in Three Systems            │
    │  ┌───────────┐  ┌──────────┐  ┌──────────┐│
    │  │PostgreSQL │  │  Neo4j   │  │ ChromaDB ││
    │  │           │  │          │  │          ││
    │  │Full entity│  │ Nodes+   │  │ Vector   ││
    │  │data       │  │ Relations│  │ search   ││
    │  └───────────┘  └──────────┘  └──────────┘│
    └────────────────────────────────────────────┘
         ↓
    [RAG Query System]
         ↓
    User gets contextualized results
```

### 2. Entity Resolution Strategy

**Problem:** "Abu Hurairah", "Abu Hurayrah", "Abi Huraira" are the same person.

**Solution:**
```python
# Step 1: Normalize
normalize("Abu Hurairah")    → "abuhurairah"
normalize("Abu Hurayrah")    → "abuhurairah"  # Match!
normalize("Abi Huraira")     → "abihuraira"   # Close match

# Step 2: Phonetic key
phonetic("Abu Hurairah")     → "ABHRR"
phonetic("Abu Hurayrah")     → "ABHRR"        # Match!
phonetic("Abi Huraira")      → "ABHR"         # Close match

# Step 3: Fuzzy string similarity
levenshtein_ratio("abuhurairah", "abihuraira") → 0.85  # 85% similar

# Decision: MERGE if:
# - normalization_key matches (1.0 confidence)
# - OR phonetic_key matches + similarity > 0.80
# - OR manual review if 0.70 < similarity < 0.80
```

### 3. Neo4j Relationship Patterns

**Isnad Chain (Critical for Authentication):**
```cypher
// Example: Hadith #12345
(h:Hadith {hadith_id: 12345})
  -[:NARRATED_BY {position: 0}]->
(bukhari:Person {name: "Bukhari", generation: 4})
  -[:HEARD_FROM {transmission_type: "hearing"}]->
(abdullah:Person {name: "Abdullah ibn Yusuf", generation: 3})
  -[:HEARD_FROM]->
(malik:Person {name: "Malik", generation: 2})
  -[:HEARD_FROM]->
(abu_hurairah:Person {name: "Abu Hurairah", generation: 1})

// Query: Verify chain authenticity
MATCH path = (h:Hadith {hadith_id: 12345})-[:NARRATED_BY*]-(prophet:Person {person_type: "prophet"})
WITH nodes(path) as narrators
WHERE all(n in narrators WHERE n.reliability_grade IN ['trustworthy', 'very_reliable'])
RETURN "Authentic chain" as result
```

**Complex Event Modeling:**
```cypher
// Hadith about Battle of Badr
(h:Hadith {hadith_id: 456})
  -[:DESCRIBES_EVENT]->
(battle:Event {name: "Battle of Badr", date_hijri_year: 2})
  -[:OCCURRED_AT]->
(badr:Place {name: "Badr Valley"})

(battle)-[:HAD_PARTICIPANT {role: "divine_intervention"}]->
(angels:Person {type: "celestial"})

(h)-[:MENTIONS_PLACE {context: "event_location", confidence: 0.95}]->
(badr)

(h)-[:ABOUT_TOPIC {relevance: 0.92}]->
(topic:Topic {category: "Jihad"})
```

### 4. Vector Metadata Design

**Minimalist Approach (Recommended):**
```python
# Store only in hadith_vectors.metadata
{
    "hadith_id": 12345,
    "chunk_index": 0,
    "reference": "Bukhari 520",
    "grading": "Sahih",
    "primary_topics": ["prayer"]  # For pre-filtering
}

# Fetch full context at query time
def get_rag_context(hadith_id):
    # From PostgreSQL
    hadith = db.query("SELECT * FROM hadiths WHERE id = %s", hadith_id)

    # From Neo4j
    graph_context = neo4j.run("""
        MATCH (h:Hadith {hadith_id: $hadith_id})
        OPTIONAL MATCH (h)-[:NARRATED_BY]->(narrator:Person)
        OPTIONAL MATCH (h)-[:ABOUT_TOPIC]->(topic:Topic)
        OPTIONAL MATCH (h)-[:MENTIONS_PLACE]->(place:Place)
        RETURN
            collect(DISTINCT narrator.canonical_name) as narrators,
            collect(DISTINCT topic.canonical_name) as topics,
            collect(DISTINCT place.canonical_name) as places
    """, hadith_id=hadith_id)

    return {
        "text": hadith.text_en,
        "narrators": graph_context.narrators,
        "topics": graph_context.topics,
        "places": graph_context.places
    }
```

### 5. Preventing Relationship Explosion

**Problem:** With 10,000 hadiths × 50 entities/hadith × 5 relationship types = 2.5M relationships

**Solutions:**

1. **Confidence Thresholds**
   ```python
   # Only create relationship if confidence > 0.8
   if extraction_confidence > 0.8:
       create_relationship(hadith, entity, confidence)
   ```

2. **Relationship Properties (Not Types)**
   ```cypher
   // ❌ Bad: Too many types
   -[:MENTIONS_BIRTHPLACE]->
   -[:MENTIONS_DEATH_PLACE]->
   -[:MENTIONS_EVENT_LOCATION]->

   // ✅ Good: Properties
   -[:MENTIONS_PLACE {context: "birthplace"}]->
   -[:MENTIONS_PLACE {context: "death_place"}]->
   -[:MENTIONS_PLACE {context: "event_location"}]->
   ```

3. **On-Demand Computation**
   ```cypher
   // Don't pre-compute indirect relationships
   // Query when needed:
   MATCH path = (h1:Hadith)-[:RELATED_TO*1..2]-(h2:Hadith)
   WHERE h1.hadith_id = 12345
   RETURN h2
   ```

## Implementation Roadmap

### Phase 0: Foundation ✅ (Completed)
- [x] Git worktree setup
- [x] Infrastructure docker-compose
- [x] PostgreSQL schema
- [x] Neo4j schema
- [x] Data models (SQLAlchemy + Pydantic)
- [x] Architecture documentation

### Phase 1: Core Extraction (Next)
**Estimated Time:** 3-4 days

**Tasks:**
1. Implement database connection utilities
   ```python
   # src/utils/database.py
   def get_db_session() -> Session
   def get_neo4j_driver() -> Driver
   def get_chroma_client() -> Client
   ```

2. Implement text processing utilities
   ```python
   # src/utils/text_processing.py
   def normalize_name(name: str) -> str
   def get_phonetic_key(name: str) -> str
   def calculate_similarity(s1: str, s2: str) -> float
   ```

3. Implement entity extractor (LangChain)
   ```python
   # src/extraction/entity_extractor.py
   class EntityExtractor:
       def extract_people(hadith_text: str) -> List[ExtractedPerson]
       def extract_places(hadith_text: str) -> List[ExtractedPlace]
       def extract_events(hadith_text: str) -> List[ExtractedEvent]
       def extract_topics(hadith_text: str) -> List[ExtractedTopic]
   ```

4. Implement entity resolver
   ```python
   # src/extraction/entity_resolver.py
   class EntityResolver:
       def resolve_person(extracted: ExtractedPerson) -> UUID
       def find_matches(name: str) -> List[PotentialMatch]
       def merge_entities(source_id: UUID, target_id: UUID)
   ```

5. Simple extraction pipeline (without LangGraph first)
   ```python
   # src/extraction/pipeline.py
   class ExtractionPipeline:
       def process_hadith(hadith_id: int) -> ExtractionOutput
   ```

### Phase 2: Test with 500 Hadiths
**Estimated Time:** 2-3 days

**Tasks:**
1. Create extraction script
   ```python
   # scripts/extract_500_samples.py
   - Fetch 500 diverse hadiths
   - Process with extraction pipeline
   - Store results in all 3 databases
   - Generate quality report
   ```

2. Validation queries
   ```python
   # scripts/test_queries.py
   - Entity deduplication accuracy
   - Relationship completeness
   - Graph query patterns
   - Vector search quality
   ```

3. Gap analysis
   - What extraction patterns failed?
   - Which entity types have low confidence?
   - Are relationships accurate?
   - Performance bottlenecks?

### Phase 3: RAG System
**Estimated Time:** 2-3 days

**Tasks:**
1. Implement hybrid retrieval
   ```python
   # src/rag/retriever.py
   class HybridRetriever:
       def vector_search(query: str) -> List[int]  # hadith_ids
       def graph_context(hadith_ids: List[int]) -> Dict
       def merge_results() -> List[RAGResult]
   ```

2. Query engine
   ```python
   # src/rag/query_engine.py
   class RAGQueryEngine:
       def query(text: str, filters: Dict) -> RAGResponse
   ```

### Phase 4: Distributed Processing
**Estimated Time:** 3-4 days

**Tasks:**
1. Ray workers
   ```python
   # src/distributed/ray_workers.py
   @ray.remote
   def extract_entities_batch(hadith_ids: List[int])
   ```

2. Celery tasks
   ```python
   # src/distributed/tasks.py
   @celery_app.task
   def extract_hadith_batch(hadith_ids: List[int])
   ```

3. Job monitoring
   ```python
   # Track progress in extraction_jobs table
   # Expose via API endpoint
   ```

### Phase 5: Full Production
**Estimated Time:** 1-2 weeks

- Process all hadiths in database
- Web API (FastAPI)
- Admin dashboard
- Monitoring (Prometheus + Grafana)
- Deploy to Server 84

## Quick Start Commands

### 1. Start Infrastructure
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/hadith-knowledge-graph
cd apps/hadith-knowledge-graph/infrastructure

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# Verify services
docker-compose ps
docker logs hadith-neo4j
docker logs hadith-chromadb
```

### 2. Initialize Databases
```bash
# PostgreSQL (adjust credentials)
psql -h localhost -U your_user -d dailydeenguide < infrastructure/schema.sql

# Neo4j (via browser at http://localhost:7474)
# Username: neo4j
# Password: hadithknowledge2025
# Run contents of infrastructure/neo4j_schema.cypher
```

### 3. Test Connections
```python
# Python test
from sqlalchemy import create_engine
from neo4j import GraphDatabase
import chromadb

# PostgreSQL
engine = create_engine("postgresql://user:pass@localhost/dailydeenguide")
print("PostgreSQL:", engine.connect())

# Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "hadithknowledge2025"))
print("Neo4j:", driver.verify_connectivity())

# ChromaDB
client = chromadb.HttpClient(host="localhost", port=8000)
print("ChromaDB:", client.heartbeat())
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `infrastructure/docker-compose.yml` | All services (Neo4j, ChromaDB, Ollama, Redis) |
| `infrastructure/schema.sql` | PostgreSQL entity tables |
| `infrastructure/neo4j_schema.cypher` | Neo4j constraints & indexes |
| `src/models/entities.py` | SQLAlchemy ORM models |
| `src/models/schemas.py` | Pydantic validation schemas |
| `src/config.py` | Settings management |
| `README.md` | Project overview & usage guide |

## Next Immediate Steps

1. **Start Infrastructure** (5 min)
   ```bash
   cd infrastructure && docker-compose up -d
   ```

2. **Initialize Databases** (10 min)
   - Run `schema.sql` on PostgreSQL
   - Run `neo4j_schema.cypher` on Neo4j

3. **Implement Core Utilities** (2-3 hours)
   - `src/utils/database.py`
   - `src/utils/text_processing.py`
   - `src/utils/embeddings.py`

4. **Build Entity Extractor** (1 day)
   - LangChain prompts for entity extraction
   - Test on 10 hadiths manually

5. **Build Entity Resolver** (1 day)
   - Fuzzy matching logic
   - Test deduplication on known duplicates

6. **Test Pipeline on 500 Hadiths** (1 day)
   - Run extraction
   - Analyze results
   - Document improvements

## Research Findings Summary

Based on extensive research (see README for sources), key findings:

1. **Proven Approaches**
   - SemanticHadith project successfully built Hadith knowledge graphs
   - Multi-IsnadSet (MIS) project used Neo4j for 77,797 narrator relationships
   - RAG improves LLM accuracy by 40%+ for Islamic Q&A (2025 research)

2. **Best Practices**
   - Use confidence thresholds (>0.8) to manage relationship explosion
   - Hybrid retrieval (vector + graph) outperforms vector-only
   - Entity resolution critical for name variations across transliterations

3. **Technology Validation**
   - Neo4j proven for isnad chain analysis
   - ChromaDB + OpenAI embeddings standard for RAG
   - LangChain + LangGraph suitable for extraction orchestration

## Success Metrics

### Technical Metrics
- **Entity Extraction Accuracy:** >90% for people, >85% for places/events
- **Deduplication Rate:** <5% duplicate entities remaining
- **RAG Retrieval Quality:** >80% relevant results in top-5
- **Processing Speed:** >100 hadiths/minute with distributed processing

### Business Metrics
- Knowledge graph enables advanced semantic search
- RAG provides contextual answers with source attribution
- Isnad chain analysis supports authentication research
- Extensible to other Islamic texts (Quran, Tafsir, Fiqh)

## Conclusion

A solid foundation has been established for the Hadith Knowledge Graph system. The architecture is research-backed, scalable, and follows best practices.

**Next step:** Implement core extraction utilities and test with 500 hadiths to validate the approach before full-scale deployment.

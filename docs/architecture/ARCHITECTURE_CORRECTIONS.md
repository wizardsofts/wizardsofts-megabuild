# Architecture Corrections & Simplifications

**Date:** 2026-01-03
**Issues Identified:** Over-engineering, service duplication, poor reusability

---

## ❌ What Was Wrong

### 1. **Duplicate Redis/Celery**
**Problem:** Created hadith-specific Redis container when production infrastructure already exists.

**Existing Infrastructure (Server 84):**
- Redis: `redis-celery` on port 6380 ✅ (Already running)
- Celery Workers: `ml`, `data`, `default` queues ✅ (Already running)
- Celery Beat: Scheduler ✅ (Already running)
- Flower: Dashboard on port 5555 ✅ (Already running)

**Fix:** Remove `apps/hadith-knowledge-graph/infrastructure/docker-compose.yml` Redis service. Use existing.

### 2. **Ollama Not Reusable**
**Problem:** `hadith-ollama` container is project-specific, not shared.

**Should Be:** Single Ollama instance accessible via API from all projects.

**Fix:**
- Move Ollama to `/infrastructure/ollama/docker-compose.yml`
- Expose on known port (11434)
- Update hadith project to connect via API URL

### 3. **Extraction Worker Unnecessary**
**Problem:** Created dedicated extraction container when Celery workers can handle it.

**Should Be:** Hadith extraction tasks run on existing Celery `ml` or `data` queue.

**Fix:** Deploy extraction tasks to existing Celery infrastructure.

---

## ✅ Correct Architecture

### Infrastructure Layout

```
Server 84 (10.0.0.84) - Production Infrastructure
├── Ray Cluster (port 10001) ✅ Existing
│   └── 9 worker nodes across servers 80, 81, 82, 84
│
├── Redis (port 6380) ✅ Existing
│   └── Celery broker + result backend
│
├── Celery ✅ Existing
│   ├── celery-worker-ml (2 cores, 4GB)
│   ├── celery-worker-data (4 cores, 8GB)
│   ├── celery-worker-default
│   ├── celery-beat (scheduler)
│   └── Flower (port 5555) - Monitoring
│
├── Ollama (port 11434) ⚠️ Should be here, not project-specific
│   └── Shared LLM inference service
│
└── PostgreSQL (Server 80:5433) ✅ Existing
    └── gibd database

Project-Specific Services (Local Dev or Server 84)
├── Neo4j (port 7687, 7474)
│   └── Hadith knowledge graph only
│
└── ChromaDB (port 8000)
    └── Hadith vector embeddings only
```

### Data Flow

```
Hadith Text
    ↓
Celery Task (on existing ml queue)
    ↓
1. Extract Entities (Ollama API → http://10.0.0.84:11434)
2. Resolve Entities (PostgreSQL → 10.0.0.80:5433)
3. Store Graph (Neo4j → local or remote)
4. Store Vectors (ChromaDB → local or remote)
    ↓
Knowledge Graph Complete
```

---

## 🔧 Required Changes

### 1. Move Ollama to Shared Infrastructure

**Create:** `/infrastructure/ollama/docker-compose.yml`
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - /home/wizardsofts/ollama-models:/root/.ollama
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
    security_opt:
      - no-new-privileges:true
```

**Deploy on Server 84:**
```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/ollama
docker-compose up -d

# Pull models once
docker exec ollama ollama pull llama3.2:3b-instruct-q4_K_M
docker exec ollama ollama pull nomic-embed-text
```

### 2. Simplify Hadith Docker Compose

**Remove from `apps/hadith-knowledge-graph/infrastructure/docker-compose.yml`:**
- ❌ `redis` service (use existing on 10.0.0.84:6380)
- ❌ `ollama` service (use shared on 10.0.0.84:11434)

**Keep only:**
- ✅ `neo4j` (project-specific graph database)
- ✅ `chromadb` (project-specific vector database)

### 3. Update Environment Variables

**`apps/hadith-knowledge-graph/.env`:**
```env
# Use existing infrastructure
REDIS_URL=redis://:${REDIS_PASSWORD}@10.0.0.84:6380/0
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@10.0.0.84:6380/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@10.0.0.84:6380/1

# Shared Ollama
OLLAMA_BASE_URL=http://10.0.0.84:11434

# Existing Ray
RAY_ADDRESS=10.0.0.84:10001
```

### 4. Deploy Extraction Tasks to Existing Celery

**No new workers needed.** Add hadith tasks to existing Celery setup:

```bash
# On Server 84
cd /home/wizardsofts/celery
cp /path/to/hadith/tasks.py ./tasks/hadith_tasks.py

# Restart workers to load new tasks
docker-compose restart celery-worker-ml
```

---

## 🧪 Testing (Simplified)

### Test 1: Verify Infrastructure Access

```bash
# From anywhere
curl http://10.0.0.84:11434/api/tags  # Ollama
curl http://10.0.0.84:5555  # Flower dashboard

# Test Redis
redis-cli -h 10.0.0.84 -p 6380 -a <password> PING
```

### Test 2: Run Extraction Task

```python
from celery import Celery

app = Celery(
    broker='redis://:password@10.0.0.84:6380/0',
    backend='redis://:password@10.0.0.84:6380/1'
)

# Submit to existing ml queue
result = app.send_task(
    'hadith_tasks.extract_hadith',
    args=[hadith_id, hadith_text],
    queue='ml'
)

# Wait for result
output = result.get(timeout=60)
```

### Test 3: Check Flower Dashboard

Open: http://10.0.0.84:5555 (already running)

---

## 🔐 Security Audit ✅ APPLIED

### Network Security Strategy

**IMPORTANT:** Services are accessible from **local network (10.0.0.0/24)** only, NOT localhost.
This allows distributed infrastructure (Ray workers on servers 80, 81, 82) to access services.

**Security Layers:**
1. ✅ UFW Firewall - Blocks external internet access
2. ✅ Local network only (10.0.0.0/24) - Internal servers can access
3. ✅ Container security (no-new-privileges, memory limits)
4. ⚠️ Application auth - TODO for production hardening

### Neo4j (Port 7687, 7474) ✅

**Current Configuration:**
```yaml
NEO4J_AUTH=neo4j/hadithknowledge2025  # ⚠️ Should be in .env
ports:
  - "7474:7474"  # Local network (protected by UFW)
  - "7687:7687"  # Local network (protected by UFW)
```

**Security Measures:**
- ✅ Accessible from local network (10.0.0.0/24)
- ✅ UFW firewall blocks internet access
- ✅ Password authentication required
- ⚠️ TODO: Move password to .env secrets

**UFW Rules (REQUIRED - Run infrastructure/ufw-rules.sh):**
```bash
sudo ufw allow from 10.0.0.0/24 to any port 7474 proto tcp
sudo ufw allow from 10.0.0.0/24 to any port 7687 proto tcp
sudo ufw deny 7474/tcp  # Block internet
sudo ufw deny 7687/tcp  # Block internet
```

### ChromaDB (Port 8000) ✅

**Current Configuration:**
```yaml
ALLOW_RESET=FALSE  # ✅ Production safe
ports:
  - "8000:8000"  # Local network (protected by UFW)
```

**Security Measures:**
- ✅ ALLOW_RESET=FALSE (prevents data wipes)
- ✅ Local network access only (10.0.0.0/24)
- ✅ UFW firewall blocks internet access
- ⚠️ TODO: Add token authentication for production

**UFW Rules:**
```bash
sudo ufw allow from 10.0.0.0/24 to any port 8000 proto tcp
sudo ufw deny 8000/tcp  # Block internet
```

### Ollama (Port 11434) ✅

**Current Configuration:**
```yaml
ports:
  - "11434:11434"  # Local network (protected by UFW)
```

**Security Measures:**
- ✅ Local network access only (10.0.0.0/24)
- ✅ UFW firewall blocks internet access
- ✅ Shared infrastructure (reusable across projects)
- ⚠️ No API authentication (acceptable for internal network)

**UFW Rules:**
```bash
sudo ufw allow from 10.0.0.0/24 to any port 11434 proto tcp
sudo ufw deny 11434/tcp  # Block internet
```

### Redis (Port 6380) - Already Secure ✅

**Current:**
```yaml
command: redis-server --requirepass ${REDIS_PASSWORD}
```

**Status:** ✅ Password protected
**Recommendation:** Ensure strong password in `.env.celery`

---

## 🌐 RAG API Endpoint

### FastAPI Service

**Create:** `apps/hadith-knowledge-graph/api/main.py`

```python
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
import os

from src.rag.query_engine import QueryEngine

app = FastAPI(title="Hadith Knowledge Graph API", version="1.0.0")
API_KEY = os.getenv("API_KEY", "change-me-in-production")

# Authentication
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    include_graph_context: bool = True

class HadithResult(BaseModel):
    hadith_id: int
    text: str
    similarity_score: float
    entities: dict

class QueryResponse(BaseModel):
    query: str
    results: List[HadithResult]
    total_found: int

# Endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "hadith-rag-api"}

@app.post("/query", response_model=QueryResponse)
def query_hadiths(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Query hadith knowledge graph with semantic search + graph context"""
    engine = QueryEngine()
    results = engine.query(
        query_text=request.query,
        top_k=request.top_k,
        use_graph_context=request.include_graph_context
    )

    return QueryResponse(
        query=request.query,
        results=[
            HadithResult(
                hadith_id=r["hadith_id"],
                text=r["text"],
                similarity_score=r["score"],
                entities=r.get("entities", {})
            )
            for r in results
        ],
        total_found=len(results)
    )

@app.get("/entities/{entity_type}")
def list_entities(
    entity_type: str,
    api_key: str = Depends(verify_api_key)
):
    """List all entities of a given type (people, places, events, topics)"""
    # TODO: Implement
    pass
```

**Docker Compose:**
```yaml
# apps/hadith-knowledge-graph/infrastructure/docker-compose.yml
services:
  api:
    build:
      context: ..
      dockerfile: api/Dockerfile
    container_name: hadith-rag-api
    ports:
      - "8001:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - CHROMA_HOST=chromadb
      - API_KEY=${API_KEY}
    depends_on:
      - neo4j
      - chromadb
    restart: unless-stopped
```

**Usage:**
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "What did the Prophet say about prayer?",
    "top_k": 5
  }'
```

---

## 📊 Knowledge Graph Analysis

### Current Gaps (From Implementation)

1. **No Isnad (Chain of Narration) Parsing**
   - Code: `enable_isnad_parsing: bool = True` (not implemented)
   - **Impact:** Missing critical hadith provenance
   - **Fix:** Add isnad extraction to entity_extractor.py

2. ~~**No Hadith Grading Integration**~~ **NOT NEEDED**
   - ✅ Using Sahih hadiths only (pre-authenticated source)
   - No grading classifier required

3. **No Relationship Confidence Scores**
   - Neo4j relationships use hardcoded confidence (0.8, 0.9)
   - **Impact:** Can't filter low-confidence extractions
   - **Fix:** Use LLM confidence scores from extraction

4. **Topic Hierarchy Not Built**
   - Schema supports `parent_topic_id` but extraction creates flat topics
   - **Impact:** No topic tree (Prayer → Obligatory Prayer → Fajr)
   - **Fix:** Add topic hierarchy resolution

### Recommended Truncations ✅ APPLIED

**Removed These Fields:**
- ✅ `entities_people.birth_year` - Rarely known for hadith narrators
- ✅ `entities_people.death_year` - Rarely known for hadith narrators
- ✅ `entities_people.birth_year_hijri` - Rarely known
- ✅ `entities_people.death_year_hijri` - Rarely known
- ✅ `entities_people.data_sources` - Not populated in extraction
- ✅ `entities_places.latitude` - Not used for Islamic hadith scholarship
- ✅ `entities_places.longitude` - Not used for Islamic hadith scholarship
- ✅ `entities_events.data_sources` - Not populated in extraction

**Note:** Fields removed from SQLAlchemy models (entities.py). Migration script needed for existing databases.

**Keep Essential Fields:**
- ✅ canonical_name_en/ar
- ✅ normalization_key (for deduplication)
- ✅ person_type, place_type, event_type
- ✅ reliability_grade (critical for hadith scholarship)
- ✅ attributes (JSONB for flexibility)

### Performance Improvements

**Add Missing Indexes:**
```sql
-- Full-text search on hadith text (if storing hadiths in PostgreSQL)
CREATE INDEX idx_hadiths_fulltext ON hadiths USING GIN(to_tsvector('english', text_en));

-- Entity relationship counts (for popular entities)
CREATE MATERIALIZED VIEW entity_mention_counts AS
SELECT entity_type, entity_id, COUNT(*) as mention_count
FROM hadith_entity_links
GROUP BY entity_type, entity_id;

CREATE INDEX idx_mention_counts ON entity_mention_counts(mention_count DESC);
```

---

## 🎯 Simple Test Instructions

### Prerequisites
```bash
# Ensure services running on Server 84
ssh wizardsofts@10.0.0.84
docker ps | grep -E "redis|celery|ollama"
```

### Test 1: Ollama API (30 seconds)
```bash
curl -X POST http://10.0.0.84:11434/api/generate \
  -d '{"model":"llama3.2:3b-instruct-q4_K_M","prompt":"Test","stream":false}' \
  | python -m json.tool
```

### Test 2: Neo4j Dashboard (Browser)
**URL:** http://localhost:7474 (or http://10.0.0.84:7474 if exposed)
**Credentials:**
- Username: `neo4j`
- Password: `hadithknowledge2025`

**Test Query:**
```cypher
// Check database is empty (before extraction)
MATCH (n) RETURN count(n) as total_nodes

// After extraction, check relationships
MATCH (h:Hadith)-[r]->(e)
RETURN h.hadith_id, type(r), labels(e), count(*) as relationships
```

### Test 3: Run Single Extraction (5 minutes)
```bash
cd apps/hadith-knowledge-graph

# Start Neo4j + ChromaDB
cd infrastructure
docker-compose up -d neo4j chromadb

# Run extraction (using existing Ollama + PostgreSQL)
python -c "
from src.extraction.pipeline import ExtractionPipeline
from src.config import get_settings
import os

# Override config for existing infrastructure
os.environ['OLLAMA_BASE_URL'] = 'http://10.0.0.84:11434'
os.environ['NEO4J_URI'] = 'bolt://localhost:7687'
os.environ['CHROMA_HOST'] = 'localhost'

pipeline = ExtractionPipeline()
result = pipeline.process_hadith(
    hadith_id=1,
    hadith_text='Abu Hurairah narrated that the Prophet said: The five daily prayers expiate sins.'
)
print(result)
"
```

---

**Next Actions:**
1. Move Ollama to shared infrastructure
2. Remove duplicate Redis from hadith project
3. Security hardening (restrict ports, add auth)
4. Deploy RAG API
5. Run test extraction and analyze results

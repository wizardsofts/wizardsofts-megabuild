# Hadith Knowledge Graph - Next Steps

**Status:** Phase 1-3 Complete | Ollama Connectivity Verified ✅
**Date:** 2026-01-03
**Branch:** `feature/hadith-knowledge-graph`

---

## ✅ Completed This Session

### Infrastructure Verification
- All Docker services running healthy (Neo4j, ChromaDB, Ollama, Redis)
- Ollama accessible from Docker network: `http://hadith-ollama:11434`
- Models confirmed available: `llama3.2:3b-instruct-q4_K_M`, `nomic-embed-text`

### Code Implementation
- Removed all `pgvector` dependencies (using ChromaDB for vectors)
- Fixed Python 3.11 type hints (`from __future__ import annotations`)
- Updated config with `ollama_embedding_model` parameter
- Created extraction worker Docker Compose setup

### Files Created
- `infrastructure/docker-compose.extraction.yml` - Extraction worker container config
- `infrastructure/Dockerfile.extraction` - Python worker Dockerfile
- `scripts/test_ollama_direct.py` - Ollama connectivity test
- `IMPLEMENTATION_STATUS.md` - Comprehensive status document

---

## 🎯 Immediate Next Steps (1-2 Hours)

### 1. Run Extraction Test in Container

**Why:** Python code needs to run inside Docker network to access Ollama models.

**Command:**
```bash
cd apps/hadith-knowledge-graph

# Option A: Use docker run (fastest)
docker run --rm -it \
  --network infrastructure_hadith-network \
  -v $(pwd):/app \
  -w /app \
  -e POSTGRES_HOST=10.0.0.80 \
  -e POSTGRES_PORT=5433 \
  -e POSTGRES_USER=gibd \
  -e POSTGRES_PASSWORD='29Dec2#24' \
  -e POSTGRES_DB=gibd \
  -e NEO4J_URI=bolt://hadith-neo4j:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=hadithknowledge2025 \
  -e CHROMA_HOST=hadith-chromadb \
  -e CHROMA_PORT=8000 \
  -e OLLAMA_BASE_URL=http://hadith-ollama:11434 \
  -e OLLAMA_MODEL=llama3.2:3b-instruct-q4_K_M \
  -e OLLAMA_EMBEDDING_MODEL=nomic-embed-text \
  python:3.11-slim bash

# Inside container:
apt-get update && apt-get install -y gcc g++ postgresql-client
pip install -r requirements.txt
python scripts/test_single_hadith.py
```

**Option B: Use docker-compose (persistent container)**
```bash
cd infrastructure
docker compose -f docker-compose.extraction.yml up -d
docker exec -it hadith-extraction-worker bash

# Inside container:
python scripts/test_single_hadith.py
```

### 2. Validate First Extraction

**Expected Output:**
```
Processing hadith 1...
Extracting entities...
  - People: 1 (Abu Hurairah)
  - Places: 0
  - Events: 0
  - Topics: 2 (Prayer, Sin Expiation)

Resolved entities: 3 total
Stored in Neo4j ✅
Stored in ChromaDB ✅
Duration: 8-12 seconds
```

**Validation Checks:**
```bash
# Check Neo4j
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 \
  "MATCH (h:Hadith {hadith_id: 1}) RETURN h"

# Check PostgreSQL
PGPASSWORD='29Dec2#24' psql -h 10.0.0.80 -p 5433 -U gibd -d gibd \
  -c "SELECT canonical_name_en FROM entities_people LIMIT 5"

# Check ChromaDB
curl http://localhost:8000/api/v1/collections/hadith_embeddings
```

### 3. Run 10-Hadith Batch

```bash
# Edit scripts/extract_500_samples.py line 165
# Change: count=10 (already set)

docker exec -it hadith-extraction-worker python scripts/extract_500_samples.py
```

**Expected Results:**
- Success rate: >90%
- Total entities: 30-50
- Avg entities per hadith: 3-5
- Processing time: 10-15 minutes (sequential)

---

## 🐛 Known Issues & Solutions

### Issue: Container Build Taking Long

The `docker-compose.extraction.yml` build may take 5-10 minutes due to installing all requirements.

**Solution:** Use the quick `docker run` approach (Option A above) for immediate testing.

### Issue: Ollama Response Timeout

If Ollama takes >60s to respond, increase timeout in `src/extraction/entity_extractor.py:51`:

```python
timeout=120.0  # Increase from 60.0
```

### Issue: PostgreSQL Connection Refused

Ensure PostgreSQL is accessible from Docker network:

```bash
# Test from container
docker run --rm --network infrastructure_hadith-network \
  postgres:15-alpine \
  psql -h 10.0.0.80 -p 5433 -U gibd -d gibd -c "SELECT 1"
```

---

## 📊 Validation Criteria

### Entity Extraction Quality (Target: >85% Precision)

**Sample Validation:**
1. Extract 10 hadiths
2. Manually review extracted entities
3. Calculate:
   - **Precision:** Correct entities / Total extracted
   - **Recall:** Correct entities / Total should be extracted
   - **Deduplication:** Merged duplicates / Total duplicates

**Example:**
```
Hadith: "Abu Hurairah narrated that the Prophet said..."

Expected Entities:
✅ Abu Hurairah (narrator)
✅ Prophet Muhammad (central figure)
✅ Prayer (topic)

Extraction Result:
✅ Abu Hurairah (confidence: 0.95)
✅ Prophet Muhammad (confidence: 0.90)
✅ Prayer (confidence: 0.92)
❌ Hurairah (duplicate - should be merged)

Precision: 3/4 = 75% (needs improvement)
Deduplication needed: 1/4 duplicates found
```

### Performance Benchmarks

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Extraction time per hadith | <15s | TBD | ⏳ Pending |
| Entity accuracy (precision) | >85% | TBD | ⏳ Pending |
| Entity recall | >80% | TBD | ⏳ Pending |
| Deduplication rate | >90% | TBD | ⏳ Pending |
| Neo4j query latency | <100ms | TBD | ⏳ Pending |
| ChromaDB vector search | <200ms | TBD | ⏳ Pending |

---

## 🚀 Phase 4: Distributed Processing (After Validation)

### Ray Cluster Integration

```python
# Test Ray connection
import ray
ray.init(address="10.0.0.84:10001", namespace="hadith-extraction")

# Run distributed extraction
from src.distributed.ray_workers import process_hadiths_parallel
results = process_hadiths_parallel(hadiths[:100], batch_size=10)
```

### Celery Task Queue

```python
# Start Celery worker (in container)
celery -A src.distributed.tasks worker --loglevel=info

# Submit task
from src.distributed.tasks import process_hadith_batch
result = process_hadith_batch.delay(hadiths[:10])
result.get(timeout=600)  # Wait for completion
```

---

## 📝 Testing Checklist

- [ ] Single hadith extraction succeeds
- [ ] Entity extractor returns valid JSON
- [ ] Entity resolver deduplicates correctly
- [ ] Neo4j stores relationships
- [ ] ChromaDB stores embeddings
- [ ] 10-hadith batch completes successfully
- [ ] Manual validation shows >85% precision
- [ ] No memory leaks (check with `docker stats`)
- [ ] Error handling works (malformed hadith text)
- [ ] Retry logic works (Neo4j timeout)

---

## 🔄 Continuous Integration (Future)

### GitLab CI/CD Pipeline

```yaml
# .gitlab-ci.yml
test-extraction:
  stage: test
  script:
    - docker compose up -d
    - docker exec hadith-extraction-worker pytest tests/
    - docker compose down
```

### Monitoring

- Prometheus metrics for extraction rate
- Grafana dashboard for entity counts
- Alerts for low accuracy (<85%)
- Flower dashboard for Celery tasks

---

## 📖 References

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Full implementation details
- [src/extraction/pipeline.py](src/extraction/pipeline.py:26) - Main extraction logic
- [infrastructure/docker-compose.yml](infrastructure/docker-compose.yml:1) - Service definitions
- [Claude.md](../../CLAUDE.md) - Project guidelines

---

**Next Session Priorities:**
1. Run extraction test in container
2. Validate first 10 hadiths
3. Document accuracy metrics
4. Optimize slow queries if needed
5. Scale to 500-hadith batch

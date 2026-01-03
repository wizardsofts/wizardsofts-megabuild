# Hadith Knowledge Graph - Deployment Guide

**Last Updated:** 2026-01-03
**Status:** Ready for CI/CD Deployment
**Target:** Server 84 (10.0.0.84)

---

## Quick Deployment (Using GitLab CI/CD)

### Prerequisites

1. **GitLab CI/CD Variables Set:**
   ```
   SSH_PRIVATE_KEY (File, Protected)
   DEPLOY_SUDO_PASSWORD (Variable, Protected, Masked)
   ```

2. **Existing Infrastructure Running on Server 84:**
   - ✅ Ray Cluster (port 10001)
   - ✅ Redis (port 6380) - Celery broker
   - ✅ Celery Workers (ml, data, default queues)
   - ✅ PostgreSQL (Server 80:5433)

### Deployment Steps

1. **Merge Feature Branch:**
   ```bash
   # Create merge request
   cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/hadith-knowledge-graph
   git push origin feature/hadith-knowledge-graph

   # In GitLab: Create MR → Merge to master
   ```

2. **Deploy Shared Ollama (One-time):**
   ```
   GitLab → CI/CD → Pipelines → Run Pipeline
   Job: deploy:shared-ollama → Manual trigger
   ```

3. **Deploy Infrastructure (Neo4j + ChromaDB):**
   ```
   GitLab → CI/CD → Pipelines → Run Pipeline
   Job: deploy:infrastructure → Manual trigger
   ```

4. **Verify Deployment:**
   ```bash
   ssh wizardsofts@10.0.0.84
   docker ps | grep -E "hadith-neo4j|hadith-chromadb|ollama"
   ```

---

## Manual Deployment (Fallback)

If CI/CD is unavailable:

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild

# Pull latest code
git pull origin master

# Deploy Ollama (one-time)
cd infrastructure/ollama
docker-compose up -d
docker exec ollama ollama pull llama3.2:3b-instruct-q4_K_M
docker exec ollama ollama pull nomic-embed-text

# Deploy Neo4j + ChromaDB
cd ../../apps/hadith-knowledge-graph/infrastructure
docker-compose up -d neo4j chromadb

# Wait for health checks
sleep 30

# Verify
docker ps | grep hadith
```

---

## Configuration

### Environment Variables

Create `/opt/wizardsofts-megabuild/apps/hadith-knowledge-graph/.env`:

```env
# Existing Infrastructure
REDIS_URL=redis://:YOUR_PASSWORD@10.0.0.84:6380/0
CELERY_BROKER_URL=redis://:YOUR_PASSWORD@10.0.0.84:6380/0
CELERY_RESULT_BACKEND=redis://:YOUR_PASSWORD@10.0.0.84:6380/1
OLLAMA_BASE_URL=http://10.0.0.84:11434
RAY_ADDRESS=10.0.0.84:10001

# Database
POSTGRES_HOST=10.0.0.80
POSTGRES_PORT=5433
POSTGRES_USER=gibd
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_DB=gibd

# Neo4j (Local)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=hadithknowledge2025

# ChromaDB (Local)
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

---

## Testing

### 1. Verify Services

```bash
# Neo4j Browser
open http://10.0.0.84:7474
# Login: neo4j / hadithknowledge2025

# ChromaDB Health
curl http://localhost:8000/api/v1/heartbeat

# Ollama
curl http://10.0.0.84:11434/api/tags
```

### 2. Run Test Extraction

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/apps/hadith-knowledge-graph

# Create venv and install deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run single hadith test
python scripts/test_single_hadith.py
```

**Expected Output:**
```
Processing hadith 1...
Extracting entities...
  - People: 1 (Abu Hurairah)
  - Topics: 2 (Prayer, Sin Expiation)
Resolved entities: 3 total
Stored in Neo4j ✅
Stored in ChromaDB ✅
Duration: 8-12 seconds
```

### 3. Verify Neo4j Graph

```cypher
// In Neo4j Browser (http://10.0.0.84:7474)

// Count nodes
MATCH (n) RETURN count(n) as total_nodes

// View hadith relationships
MATCH (h:Hadith)-[r]->(e)
RETURN h.hadith_id, type(r), labels(e), e.name
LIMIT 10
```

---

## CI/CD Pipeline

### Pipeline Stages

1. **security** - Mandatory security scanning
   - pip-audit (dependency CVEs)
   - safety (vulnerability database)
   - bandit (code security)
   - trivy (Docker image scan)

2. **test** - Unit tests with pytest
   - Coverage reports
   - PostgreSQL test database

3. **build** - Docker image build
   - Push to GitLab Container Registry
   - Tagged with commit SHA

4. **deploy** - Manual deployment
   - deploy:shared-ollama
   - deploy:infrastructure
   - deploy:extraction-worker
   - run:extraction-test

### Running Pipeline Jobs

```
GitLab → hadith-knowledge-graph → CI/CD → Pipelines

1. Security scans run automatically
2. Tests run automatically
3. Build runs on master branch
4. Deploy jobs require manual trigger (safety)
```

---

## Architecture

### Infrastructure Reuse

| Component | Location | Port | Purpose |
|-----------|----------|------|---------|
| Ray | Server 84 | 10001 | Distributed processing |
| Redis | Server 84 | 6380 | Celery broker |
| Celery | Server 84 | - | Task queue |
| Ollama | Server 84 | 11434 | LLM inference (shared) |
| PostgreSQL | Server 80 | 5433 | Entity storage |

### Project-Specific Services

| Service | Port | Localhost Only | Purpose |
|---------|------|----------------|---------|
| Neo4j | 7687, 7474 | ✅ | Knowledge graph |
| ChromaDB | 8000 | ✅ | Vector embeddings |

### Security Hardening

- ✅ All ports bound to 127.0.0.1 (localhost only)
- ✅ ChromaDB ALLOW_RESET=FALSE
- ✅ No-new-privileges on all containers
- ✅ Memory limits enforced
- ✅ Mandatory security scanning in CI/CD

---

## Schema Optimizations

**Removed Unused Fields:**
- ✅ `latitude`, `longitude` (not needed for Islamic scholarship)
- ✅ `birth_year`, `death_year` (rarely known for hadith narrators)
- ✅ `data_sources` (not populated in extraction)

**Database Migration Required:**
If deploying to existing database with old schema, run:
```sql
ALTER TABLE entities_people DROP COLUMN IF EXISTS birth_year;
ALTER TABLE entities_people DROP COLUMN IF EXISTS death_year;
ALTER TABLE entities_people DROP COLUMN IF EXISTS birth_year_hijri;
ALTER TABLE entities_people DROP COLUMN IF EXISTS death_year_hijri;
ALTER TABLE entities_people DROP COLUMN IF EXISTS data_sources;
ALTER TABLE entities_places DROP COLUMN IF EXISTS latitude;
ALTER TABLE entities_places DROP COLUMN IF EXISTS longitude;
ALTER TABLE entities_events DROP COLUMN IF EXISTS data_sources;
```

---

## Remaining Gaps (Future Work)

1. **Isnad (Chain of Narration) Parsing** - Add to entity_extractor.py
2. **Relationship Confidence Scores** - Use LLM confidence instead of hardcoded
3. **Topic Hierarchy** - Build tree structure (Prayer → Fajr → Times)

**Note:** Hadith grading integration NOT needed (Sahih hadiths only).

---

## Troubleshooting

### Neo4j Won't Start
```bash
# Check logs
docker logs hadith-neo4j

# Verify APOC plugin
docker exec hadith-neo4j ls /var/lib/neo4j/plugins/
```

### ChromaDB Connection Refused
```bash
# Check service
docker ps | grep chromadb

# Test heartbeat
curl http://localhost:8000/api/v1/heartbeat
```

### Ollama Models Not Found
```bash
# List models
docker exec ollama ollama list

# Pull missing models
docker exec ollama ollama pull llama3.2:3b-instruct-q4_K_M
```

### Extraction Fails with Ollama Timeout
```python
# In src/extraction/entity_extractor.py:51
timeout=120.0  # Increase from 60.0
```

---

## Monitoring

### Health Checks

```bash
# Neo4j
curl http://localhost:7474

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Ollama
curl http://10.0.0.84:11434/api/tags
```

### Metrics (Future)

- Prometheus exporter for extraction rate
- Grafana dashboard for entity counts
- Celery Flower (http://10.0.0.84:5555)

---

## Next Steps

1. ✅ Deploy using GitLab CI/CD
2. Run 10-hadith test extraction
3. Validate entity quality (>85% precision target)
4. Scale to 500-hadith batch
5. Deploy RAG API endpoint
6. Add isnad parsing
7. Implement topic hierarchy

---

## References

- [ARCHITECTURE_CORRECTIONS.md](ARCHITECTURE_CORRECTIONS.md) - Architecture analysis
- [SECURITY_VULNERABILITIES.md](apps/hadith-knowledge-graph/SECURITY_VULNERABILITIES.md) - CVE report
- [NEXT_STEPS.md](apps/hadith-knowledge-graph/NEXT_STEPS.md) - Testing instructions
- [.gitlab-ci.yml](apps/hadith-knowledge-graph/.gitlab-ci.yml) - CI/CD pipeline
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines

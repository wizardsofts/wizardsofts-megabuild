# CORRECTED: Ray 2.53.0 Distributed Hadith Extraction Plan

**Date**: 2026-01-05
**Status**: Planning Phase - CORRECTIONS APPLIED
**Critical Fixes**: Model, Metrics, Schema, Ollama Scaling

---

## ⚠️ **CRITICAL CORRECTIONS FROM PREVIOUS PLAN**

### 1. **Model Configuration** ❌ → ✅

**WRONG** (Previous): `llama3.1:8b`
**CORRECT** (Updated): **`mistral:7b`**

**Rationale**:
- Benchmarking showed `mistral:7b` achieves 100% accuracy with JSON schema
- Smaller model (4.4 GB vs 4.9 GB)
- Already pulled and tested locally

**Files to Update**:
```
apps/hadith-knowledge-graph/src/config.py:24
apps/hadith-knowledge-graph/.env
apps/hadith-knowledge-graph/infrastructure/.env
```

### 2. **JSON Schema Implementation** ❌ NOT DONE

**Current Code** (Line 44 in entity_extractor.py):
```python
"format": "json",  # ❌ Simple flag - NOT a schema!
```

**Required Fix**:
```python
PERSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "canonical_name_en": {"type": "string"},
            "variants": {"type": "array", "items": {"type": "string"}},
            "person_type": {"type": "string"},
            "reliability_grade": {"type": "string"},
            "context": {"type": "string"},
            "text_span": {"type": "string"}
        },
        "required": ["canonical_name_en", "person_type"]
    }
}

# In _call_ollama method:
"format": PERSON_SCHEMA,  # ✅ Proper schema constraint
```

**Status**: ❌ **NOT IMPLEMENTED** - Success report was premature!

### 3. **Arabic Name Fields** ❌ REMOVE ENTIRELY

**Remove from ALL locations**:
- PostgreSQL schema (`canonical_name_ar` column)
- Entity extractor prompts
- Documentation
- Evaluation metrics (H1d hypothesis)

**Rationale**: User requirement - no Arabic support needed

### 4. **Evaluation Metrics** ❌ WRONG FOR ENTITY EXTRACTION

**WRONG** (Previous): Classification metrics (TP/FP/FN for entire hadith)

**CORRECT**: Entity-level string matching metrics

**Proper Evaluation Method**:

```python
def evaluate_entity_extraction(extracted, ground_truth):
    """
    Entity extraction is NOT classification!

    We need to match entity STRINGS, not classify hadiths.
    """

    # Normalize entities to lowercase names for matching
    extracted_names = {e["canonical_name_en"].lower() for e in extracted}
    ground_truth_names = {e["canonical_name_en"].lower() for e in ground_truth}

    # Exact match metrics
    true_positives = len(extracted_names & ground_truth_names)
    false_positives = len(extracted_names - ground_truth_names)
    false_negatives = len(ground_truth_names - extracted_names)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": precision,  # Correctness of extracted entities
        "recall": recall,        # Completeness of extraction
        "f1": f1
    }
```

**Example**:
```
Ground Truth: ["Abu Hurairah", "Prophet Muhammad", "Umar ibn al-Khattab"]
Extracted:    ["Abu Hurairah", "Prophet Muhammad", "Ali ibn Abi Talib"]

TP = 2 (Abu Hurairah, Prophet Muhammad)
FP = 1 (Ali - wrong person)
FN = 1 (Umar - missed)

Precision = 2/3 = 66.7% (2 correct out of 3 extracted)
Recall = 2/3 = 66.7% (2 found out of 3 expected)
F1 = 66.7%
```

### 5. **Ollama Autoscaling** ❌ NOT IMPLEMENTED

**Current State**:
- Server 80: 1 Ollama instance (`hadith-ollama`)
- Server 84: No Ollama
- **NO** NFS setup
- **NO** load balancing

**Required Implementation** (from [OLLAMA_AUTOSCALING.md](OLLAMA_AUTOSCALING.md)):

**Step 1**: NFS Server Setup (Server 80)
```bash
ssh wizardsofts@10.0.0.80
sudo apt install nfs-kernel-server -y
sudo mkdir -p /opt/ollama-models
sudo chown -R 1000:1000 /opt/ollama-models
echo "/opt/ollama-models 10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
sudo ufw allow from 10.0.0.0/24 to any port 2049 proto tcp
```

**Step 2**: NFS Client Setup (Server 84)
```bash
ssh wizardsofts@10.0.0.84
sudo apt install nfs-common -y
sudo mkdir -p /opt/ollama-models
echo "10.0.0.80:/opt/ollama-models /opt/ollama-models nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
sudo mount -a
df -h /opt/ollama-models  # Verify
```

**Step 3**: Deploy Ollama Instances

**Server 80** (1 instance, read-write):
```yaml
# /opt/ollama/docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    volumes:
      - /opt/ollama-models:/root/.ollama  # Read-Write
    ports:
      - "11434:11434"
    deploy:
      resources:
        limits:
          memory: 16G
    restart: unless-stopped
```

**Server 84** (3 instances, read-only):
```yaml
# /opt/ollama/docker-compose.yml
services:
  ollama-1:
    image: ollama/ollama:latest
    container_name: ollama-1
    volumes:
      - /opt/ollama-models:/root/.ollama:ro  # Read-Only
    ports:
      - "11434:11434"
    deploy:
      resources:
        limits:
          memory: 16G

  ollama-2:
    image: ollama/ollama:latest
    container_name: ollama-2
    volumes:
      - /opt/ollama-models:/root/.ollama:ro
    ports:
      - "11435:11434"
    deploy:
      resources:
        limits:
          memory: 16G

  ollama-3:
    image: ollama/ollama:latest
    container_name: ollama-3
    volumes:
      - /opt/ollama-models:/root/.ollama:ro
    ports:
      - "11436:11434"
    deploy:
      resources:
        limits:
          memory: 16G
```

**Step 4**: Pull mistral:7b (ONLY on Server 80)
```bash
ssh wizardsofts@10.0.0.80
docker exec ollama ollama pull mistral:7b
docker exec ollama ollama list  # Verify

# Model automatically available to Server 84 instances via NFS
```

**Step 5**: Load Balancing (Traefik or Round-Robin)

**Option A**: Traefik Dynamic Config
```yaml
# traefik/dynamic/ollama.yml
http:
  services:
    ollama:
      loadBalancer:
        servers:
          - url: "http://10.0.0.80:11434"
          - url: "http://10.0.0.84:11434"
          - url: "http://10.0.0.84:11435"
          - url: "http://10.0.0.84:11436"
        healthCheck:
          path: /api/version
          interval: "10s"
```

**Option B**: Round-Robin in Code (Simpler)
```python
import itertools

OLLAMA_ENDPOINTS = [
    "http://10.0.0.80:11434",
    "http://10.0.0.84:11434",
    "http://10.0.0.84:11435",
    "http://10.0.0.84:11436",
]
ollama_cycle = itertools.cycle(OLLAMA_ENDPOINTS)

def get_ollama_endpoint():
    return next(ollama_cycle)

# In entity_extractor.py:
response = httpx.post(
    f"{get_ollama_endpoint()}/api/generate",
    json={...}
)
```

---

## CORRECTED Hypothesis & Metrics

### Revised Hypotheses

**H1**: JSON schema extraction with **mistral:7b** will achieve **≥85% F1 score** on entity extraction

**Sub-hypotheses**:
- H1a: Narrator detection **≥90% F1** (clear patterns: "narrated", "reported")
- H1b: Prophet Muhammad **≥95% F1** (high frequency, explicit mentions)
- H1c: Companions/scholars **≥75% F1** (name variants, fuzzy matching needed)
- ~~H1d: Arabic names~~ ❌ **REMOVED**

**H2**: Ollama autoscaling (4 instances) will handle **4x concurrent requests** vs single instance

**H3**: Ray distributed extraction achieves **3-5x speedup** (200 hadiths in 40-60 min)

**H4**: Entity deduplication merges **20-30%** (name variants: "Abu Hurairah" = "Abu Hurayrah")

**H5**: Topics extraction has **lower F1** (65-75%) due to ambiguity

### Corrected Evaluation Metrics

#### **Entity-Level Metrics** (CORRECT)

| Metric | Formula | Explanation | Target |
|--------|---------|-------------|--------|
| **Precision** | TP / (TP + FP) | % of extracted entities that are correct | ≥85% |
| **Recall** | TP / (TP + FN) | % of ground truth entities found | ≥80% |
| **F1 Score** | 2×(P×R)/(P+R) | Harmonic mean of precision & recall | **≥80%** |

**Matching Rules**:
1. **Exact Match**: Normalize to lowercase, strip whitespace
2. **Fuzzy Match**: Levenshtein distance ≤2 or 90% similarity
3. **Partial Match**: One name contains the other (e.g., "Muhammad" in "Prophet Muhammad")

**Example Calculation**:
```python
Ground Truth: ["Abu Hurairah", "Prophet Muhammad"]
Extracted:    ["Abu Hurairah", "Prophet", "Ali"]

Exact matches:
- "Abu Hurairah" ✅ TP
- "Prophet" vs "Prophet Muhammad" → Fuzzy match ✅ TP (90% similar)
- "Ali" ❌ FP (not in ground truth)

Missing:
- None (both ground truth entities matched)

TP = 2, FP = 1, FN = 0
Precision = 2/3 = 66.7%
Recall = 2/2 = 100%
F1 = 80%
```

#### **System Performance Metrics**

| Metric | Formula | Target |
|--------|---------|--------|
| Throughput | Hadiths/minute | ≥3.0 |
| Ollama Requests/sec | Total requests / Duration | ≥8.0 (4 instances × 2 req/s) |
| Ray Speedup | Sequential time / Distributed time | ≥3x |
| Worker Failures | Failed tasks / Total tasks | ≤2% |

---

## Corrected Implementation Plan

### Phase 0: Critical Fixes (2 hours)

**Task 1**: Update Model to mistral:7b (30 min)
```bash
cd apps/hadith-knowledge-graph

# Update config
sed -i 's/llama3.2:3b-instruct-q4_K_M/mistral:7b/g' src/config.py
sed -i 's/llama3.2:3b-instruct-q4_K_M/mistral:7b/g' .env
sed -i 's/llama3.2:3b-instruct-q4_K_M/mistral:7b/g' infrastructure/.env

# Pull model on Server 80
ssh wizardsofts@10.0.0.80 "docker exec hadith-ollama ollama pull mistral:7b"
```

**Task 2**: Implement JSON Schema (1 hour)

**File**: `apps/hadith-knowledge-graph/src/extraction/entity_extractor.py`

```python
class EntityExtractor:
    """Extract entities with JSON schema constraints"""

    # JSON Schemas for each entity type
    PERSON_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "canonical_name_en": {"type": "string"},
                "variants": {"type": "array", "items": {"type": "string"}},
                "person_type": {"type": "string"},
                "reliability_grade": {"type": "string"},
                "context": {"type": "string"},
                "text_span": {"type": "string"}
            },
            "required": ["canonical_name_en", "person_type"]
        }
    }

    PLACE_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "canonical_name_en": {"type": "string"},
                "variants": {"type": "array", "items": {"type": "string"}},
                "place_type": {"type": "string"},
                "context": {"type": "string"},
                "text_span": {"type": "string"}
            },
            "required": ["canonical_name_en", "place_type"]
        }
    }

    TOPIC_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "canonical_name_en": {"type": "string"},
                "category": {"type": "string"},
                "context": {"type": "string"}
            },
            "required": ["canonical_name_en", "category"]
        }
    }

    EVENT_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "canonical_name_en": {"type": "string"},
                "event_type": {"type": "string"},
                "date_hijri_year": {"type": "integer"},
                "context": {"type": "string"}
            },
            "required": ["canonical_name_en", "event_type"]
        }
    }

    def _call_ollama(self, prompt: str, system: str = None, schema: Dict = None):
        """Call Ollama with JSON schema constraint"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }

        # ✅ Use schema if provided, else simple JSON flag
        if schema:
            payload["format"] = schema
        else:
            payload["format"] = "json"

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=60.0
        )
        # ... rest

    def extract_people(self, hadith_text: str) -> List[Dict[str, Any]]:
        """Extract people with JSON schema"""

        result = self._call_ollama(
            prompt=self._build_people_prompt(hadith_text),
            system=self._build_people_system_prompt(),
            schema=self.PERSON_SCHEMA  # ← Pass schema
        )

        if isinstance(result, list):
            return result
        # ... fallback handling
```

**Task 3**: Remove Arabic Name Fields (30 min)

**PostgreSQL Schema**:
```sql
-- Remove canonical_name_ar column
ALTER TABLE entities_people DROP COLUMN IF EXISTS canonical_name_ar;
ALTER TABLE entities_places DROP COLUMN IF EXISTS canonical_name_ar;
ALTER TABLE entities_topics DROP COLUMN IF EXISTS canonical_name_ar;
ALTER TABLE entities_events DROP COLUMN IF EXISTS canonical_name_ar;
```

**Entity Extractor**: Remove all `canonical_name_ar` from prompts

**Documentation**: Remove H1d hypothesis and Arabic references

### Phase 1: Ollama Autoscaling (3 hours)

**Task 1**: NFS Setup (1 hour)
- Server 80: NFS server configuration
- Server 84: NFS client mount
- Verify shared volume accessible

**Task 2**: Deploy 3 Ollama Instances on Server 84 (1 hour)
- Create docker-compose.yml with 3 instances
- Mount NFS volume as read-only
- Start services, verify health

**Task 3**: Implement Load Balancing (1 hour)
- Option B (round-robin in code) - simpler
- Test all 4 endpoints respond
- Verify model loaded on all instances

**Validation**:
```bash
# Test all 4 Ollama instances
for port in 11434 11435 11436; do
  curl http://10.0.0.84:$port/api/version
done

curl http://10.0.0.80:11434/api/version

# Test load balancing (should distribute across endpoints)
python scripts/test_ollama_load_balancing.py
```

### Phase 2: Database Reset & Testing (2 hours)

**Task 1**: Fresh Database (30 min)
```bash
# Drop/recreate PostgreSQL
PGPASSWORD='29Dec2#24' psql -h 10.0.0.80 -p 5433 -U gibd -d gibd <<EOF
DROP TABLE entities_people, entities_places, entities_topics, entities_events CASCADE;
\i infrastructure/schema_no_vector.sql
EOF

# Clear Neo4j
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 \
  "MATCH (n) WHERE n:Hadith OR n:Person DETACH DELETE n"

# Clear ChromaDB
python scripts/reset_chromadb.py
```

**Task 2**: Single Hadith Test (30 min)
```bash
# In Docker container
python scripts/test_single_hadith.py

# Expected: 2 people extracted, full properties, Neo4j stored
```

**Task 3**: 10-Hadith Batch Test (1 hour)
```bash
python scripts/test_10_hadiths.py

# Verify load balancing across 4 Ollama instances
# Check /tmp disk usage doesn't spike
```

### Phase 3: Ray Distributed Extraction (3 hours)

**Same as before** but with corrected:
- Model: mistral:7b
- JSON schema enforcement
- Load-balanced Ollama endpoints
- No Arabic fields

### Phase 4: Evaluation (2 hours)

**Corrected Evaluation Script**:

```python
def evaluate_extraction(extracted_entities, ground_truth_entities):
    """
    Entity-level evaluation with fuzzy matching

    Args:
        extracted_entities: List of extracted entity names
        ground_truth_entities: List of ground truth entity names

    Returns:
        dict: Precision, recall, F1 scores
    """
    from fuzzywuzzy import fuzz

    # Normalize names
    extracted = {e.lower().strip() for e in extracted_entities}
    ground_truth = {e.lower().strip() for e in ground_truth_entities}

    # Exact matches
    exact_matches = extracted & ground_truth

    # Fuzzy matches for non-exact
    fuzzy_matches = set()
    extracted_remaining = extracted - exact_matches
    ground_truth_remaining = ground_truth - exact_matches

    for ext_name in extracted_remaining:
        for gt_name in ground_truth_remaining:
            similarity = fuzz.ratio(ext_name, gt_name)
            if similarity >= 90:  # 90% similarity threshold
                fuzzy_matches.add((ext_name, gt_name))
                break

    # Calculate metrics
    tp = len(exact_matches) + len(fuzzy_matches)
    fp = len(extracted) - tp
    fn = len(ground_truth) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_matches": len(exact_matches),
        "fuzzy_matches": len(fuzzy_matches),
        "false_positives": fp,
        "false_negatives": fn
    }
```

---

## Revised Timeline

| Phase | Duration | Cumulative | Dependencies |
|-------|----------|------------|--------------|
| Phase 0: Critical Fixes | 2 hours | 2h | None |
| Phase 1: Ollama Autoscaling | 3 hours | 5h | Phase 0 |
| Phase 2: Database & Testing | 2 hours | 7h | Phase 0, 1 |
| Phase 3: Ray Distributed | 3 hours | 10h | Phase 2 |
| Phase 4: Evaluation | 2 hours | 12h | Phase 3 |
| **Total** | **12 hours** | | **1.5 days** |

---

## Success Criteria (Updated)

### Must-Have

- [x] Model changed to mistral:7b
- [ ] JSON schema implemented (not just "json" flag)
- [ ] Arabic fields removed from all schemas
- [ ] Ollama autoscaling deployed (4 instances)
- [ ] Entity-level evaluation metrics (not classification)
- [ ] People F1 ≥ 85%
- [ ] Processing time ≤ 60 min (200 hadiths)
- [ ] Ollama load distributed across 4 instances

### Nice-to-Have

- [ ] Topics F1 ≥ 75%
- [ ] Events F1 ≥ 70%
- [ ] Ray speedup ≥ 4x
- [ ] Worker failures ≤ 1%

---

## CRITICAL Action Items

1. ✅ **Stop using llama3.1:8b** - Switch to mistral:7b everywhere
2. ❌ **Implement JSON schema** - Not just "format": "json"
3. ❌ **Remove Arabic support** - Drop canonical_name_ar columns
4. ❌ **Fix evaluation metrics** - Entity matching, not classification
5. ❌ **Deploy Ollama autoscaling** - 4 instances with NFS + load balancing

---

**Document Owner**: Claude Sonnet 4.5
**Last Updated**: 2026-01-05
**Status**: CORRECTIONS APPLIED - Ready for Implementation

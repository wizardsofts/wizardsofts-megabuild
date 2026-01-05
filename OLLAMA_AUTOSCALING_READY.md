# Ollama Autoscaling - Ready for Deployment

**Date**: 2026-01-05
**Status**: ✅ Scripts Ready - Awaiting Manual Deployment
**Branch**: `feature/hadith-knowledge-graph` (worktree)

---

## ✅ What's Complete

### 1. Infrastructure Analysis (Reality Check)

**Document**: [apps/hadith-knowledge-graph/docs/REALITY_CHECK_AUTOSCALING.md](apps/hadith-knowledge-graph/docs/REALITY_CHECK_AUTOSCALING.md)

**Findings**:
- ✅ Docker Swarm: **ACTIVE** on infrastructure
- ✅ Traefik: **RUNNING** (but swarmMode: false)
- ✅ HAProxy: **RUNNING** (internal load balancing)
- ❌ Custom Autoscaler: **FAILING** (restarting loop)
- ❌ Ollama: **NOT AUTOSCALED** (single instance, max_replicas: 1)
- ❌ NFS: **NOT CONFIGURED** (no shared model storage)

**Recommendation**: Use Docker Swarm native scaling (Option C) - simplest, fastest, most integrated.

---

### 2. Deployment Scripts Created

All scripts are executable and ready to run:

| Script | Purpose | Server | Requires Sudo |
|--------|---------|--------|---------------|
| [scripts/setup_nfs_server80.sh](scripts/setup_nfs_server80.sh) | Setup NFS server | Server 80 | ✅ Yes |
| [scripts/setup_nfs_client84.sh](scripts/setup_nfs_client84.sh) | Mount NFS client | Server 84 | ✅ Yes |
| [scripts/deploy_ollama_swarm.sh](scripts/deploy_ollama_swarm.sh) | Deploy Ollama Swarm service | Server 84 | ❌ No |
| [scripts/DEPLOYMENT_STEPS.md](scripts/DEPLOYMENT_STEPS.md) | Quick reference guide | - | - |

**What Scripts Do**:

1. **setup_nfs_server80.sh**:
   - Install nfs-kernel-server
   - Create /opt/ollama-models directory
   - Configure NFS exports (10.0.0.0/24 network)
   - Start NFS server
   - Configure UFW firewall

2. **setup_nfs_client84.sh**:
   - Install nfs-common
   - Create mount point /opt/ollama-models
   - Add to /etc/fstab for persistent mount
   - Mount NFS volume

3. **deploy_ollama_swarm.sh**:
   - Verify NFS mount exists
   - Pull mistral:7b model to NFS (Server 80 RW container)
   - Update Traefik config (swarmMode: true)
   - Restart Traefik
   - Create overlay network (ollama-network)
   - Deploy Ollama as Swarm service (1 replica)
   - Configure Traefik labels for load balancing

---

### 3. Comprehensive Documentation

| Document | Purpose |
|----------|---------|
| [docs/OLLAMA_SWARM_DEPLOYMENT_GUIDE.md](docs/OLLAMA_SWARM_DEPLOYMENT_GUIDE.md) | Complete deployment guide (75 min) |
| [apps/hadith-knowledge-graph/docs/REALITY_CHECK_AUTOSCALING.md](apps/hadith-knowledge-graph/docs/REALITY_CHECK_AUTOSCALING.md) | Infrastructure analysis |
| [apps/hadith-knowledge-graph/docs/CORRECTED_EXTRACTION_PLAN.md](apps/hadith-knowledge-graph/docs/CORRECTED_EXTRACTION_PLAN.md) | Fixed extraction plan (mistral:7b, JSON schema, entity metrics) |
| [scripts/DEPLOYMENT_STEPS.md](scripts/DEPLOYMENT_STEPS.md) | Quick deployment reference |

---

### 4. Corrected Extraction Plan

**Document**: [apps/hadith-knowledge-graph/docs/CORRECTED_EXTRACTION_PLAN.md](apps/hadith-knowledge-graph/docs/CORRECTED_EXTRACTION_PLAN.md)

**Key Corrections**:
- ✅ Fixed model: **mistral:7b** (was incorrectly llama3.1:8b)
- ✅ JSON Schema constraint implementation (not just "json" flag)
- ✅ Entity-level evaluation metrics (string matching, not classification)
- ✅ Removed Arabic name fields (H1d hypothesis removed)
- ✅ Updated success criteria

---

## 🚀 Ready to Deploy

### Prerequisites

1. **SSH Access**: You need sudo access to:
   - Server 80 (10.0.0.80) - NFS server setup
   - Server 84 (10.0.0.84) - NFS client + Swarm deployment

2. **Disk Space**: Verified available ✅
   - Server 80: 171GB free (18% used)
   - Server 84: Sufficient space available

3. **Network Connectivity**: 10.0.0.0/24 network ✅

---

### Deployment Commands (Copy-Paste Ready)

#### Step 1: NFS Server Setup (Server 80) - 15 minutes

```bash
# Copy script
scp scripts/setup_nfs_server80.sh wizardsofts@10.0.0.80:~/

# SSH and run
ssh wizardsofts@10.0.0.80
sudo bash setup_nfs_server80.sh

# Verify
exportfs -v
showmount -e localhost

exit
```

**Expected Output**:
```
/opt/ollama-models  10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)
```

---

#### Step 2: NFS Client Setup (Server 84) - 15 minutes

```bash
# Copy script
scp scripts/setup_nfs_client84.sh wizardsofts@10.0.0.84:~/

# SSH and run
ssh wizardsofts@10.0.0.84
sudo bash setup_nfs_client84.sh

# Verify
df -h /opt/ollama-models

exit
```

**Expected Output**:
```
10.0.0.80:/opt/ollama-models  217G   37G  171G  18% /opt/ollama-models
```

---

#### Step 3: Deploy Ollama Swarm Service - 30 minutes

```bash
# Copy deployment script
scp scripts/deploy_ollama_swarm.sh wizardsofts@10.0.0.84:~/

# SSH and run
ssh wizardsofts@10.0.0.84
bash deploy_ollama_swarm.sh

# Wait for deployment to complete (~10-15 min for model pull)

# Verify
docker service ps ollama
curl http://10.0.0.84:11434/api/version
curl http://10.0.0.84:11434/api/tags

exit
```

**Expected Output**:
```json
{"version":"0.1.17"}
{"models":[{"name":"mistral:7b","size":4109865159}]}
```

---

#### Step 4: Test Autoscaling - 15 minutes

```bash
ssh wizardsofts@10.0.0.84

# Scale up to 4 replicas
docker service scale ollama=4

# Monitor (Ctrl+C to exit)
watch -n 2 'docker service ps ollama'

# Test load balancing
for i in {1..10}; do
  curl -s http://10.0.0.84:11434/api/version | jq .version
  sleep 1
done

# Scale back to 2
docker service scale ollama=2

exit
```

---

## ⏳ What Still Needs to Be Done

### Manual Deployment Tasks (Awaiting Your Execution)

1. **NFS Setup** (30 minutes)
   - Run setup_nfs_server80.sh on Server 80
   - Run setup_nfs_client84.sh on Server 84

2. **Ollama Deployment** (30 minutes)
   - Run deploy_ollama_swarm.sh on Server 84
   - Verify service health

3. **Autoscaling Test** (15 minutes)
   - Scale to 4 replicas
   - Test load balancing
   - Scale back to 2

**Total Deployment Time**: ~75 minutes

---

### Code Changes Required (After Deployment)

#### 1. Update Model to mistral:7b

**File**: `apps/hadith-knowledge-graph/src/config.py`

```python
# Line 24: Change model
ollama_model: str = "mistral:7b"  # Changed from "llama3.2:3b-instruct-q4_K_M"
```

**File**: `apps/hadith-knowledge-graph/.env`

```bash
OLLAMA_MODEL=mistral:7b
OLLAMA_BASE_URL=http://10.0.0.84:11434  # Traefik load-balanced
```

---

#### 2. Implement JSON Schema Constraint

**File**: `apps/hadith-knowledge-graph/src/extraction/entity_extractor.py`

**Add schemas** (before class definition):

```python
# JSON schemas for structured output
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
            "modern_location": {"type": "string"},
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
            "name_en": {"type": "string"},
            "category": {"type": "string"},
            "context": {"type": "string"}
        },
        "required": ["name_en", "category"]
    }
}

EVENT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name_en": {"type": "string"},
            "event_type": {"type": "string"},
            "participants": {"type": "array", "items": {"type": "string"}},
            "context": {"type": "string"}
        },
        "required": ["name_en", "event_type"]
    }
}
```

**Update _call_ollama** (around line 30):

```python
def _call_ollama(self, prompt: str, system: str, schema: dict = None):
    """Call Ollama API with optional JSON schema"""
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

    # Use schema if provided, otherwise simple JSON flag
    if schema:
        payload["format"] = schema  # Schema constraint for array output
    else:
        payload["format"] = "json"  # Simple JSON mode

    response = httpx.post(
        f"{self.base_url}/api/generate",
        json=payload,
        timeout=120.0  # Increased timeout for larger models
    )
    # ... rest of code
```

**Update extract_people** (around line 60):

```python
def extract_people(self, hadith_text: str) -> List[Dict[str, Any]]:
    """Extract person entities using JSON schema"""

    result = self._call_ollama(
        prompt=self._build_people_prompt(hadith_text),
        system=self._build_people_system_prompt(),
        schema=PERSON_SCHEMA  # ← Add schema constraint
    )

    # Schema should enforce array, but handle edge cases
    if isinstance(result, list):
        return result
    elif isinstance(result, dict) and "people" in result:
        return result["people"]
    else:
        logger.warning(f"Unexpected format despite schema: {result}")
        return [result] if isinstance(result, dict) else []
```

**Apply same changes to**:
- `extract_places()` → use `PLACE_SCHEMA`
- `extract_topics()` → use `TOPIC_SCHEMA`
- `extract_events()` → use `EVENT_SCHEMA`

---

#### 3. Remove Arabic Name Fields

**PostgreSQL**:

```sql
-- Drop Arabic name columns
ALTER TABLE entities_people DROP COLUMN IF EXISTS canonical_name_ar;
ALTER TABLE entities_places DROP COLUMN IF EXISTS canonical_name_ar;

-- Verify
\d entities_people
\d entities_places
```

**entity_extractor.py**:

Remove all `canonical_name_ar` references from:
- Line 82-110: `_build_people_prompt()`
- Line 138-165: `_build_places_prompt()`
- Prompt examples (lines 85, 142)

**Documentation**:

Remove H1d hypothesis from:
- CORRECTED_EXTRACTION_PLAN.md (already done ✅)
- IMPLEMENTATION_STATUS.md

---

#### 4. Update Evaluation Metrics

**File**: Create `apps/hadith-knowledge-graph/src/evaluation/entity_evaluator.py`

```python
from typing import List, Dict, Any
from difflib import SequenceMatcher

def evaluate_entity_extraction(
    extracted: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    entity_type: str
) -> Dict[str, float]:
    """
    Evaluate entity extraction using string matching

    Args:
        extracted: Extracted entities from model
        ground_truth: Ground truth entities
        entity_type: "people", "places", "topics", "events"

    Returns:
        Dict with precision, recall, f1 metrics
    """
    # Extract entity names (canonical_name_en or name_en)
    name_field = "canonical_name_en" if entity_type in ["people", "places"] else "name_en"

    extracted_names = {e[name_field].lower().strip() for e in extracted if name_field in e}
    ground_truth_names = {e[name_field].lower().strip() for e in ground_truth if name_field in e}

    # Exact match
    exact_matches = extracted_names & ground_truth_names

    # Fuzzy match for remaining (90% similarity threshold)
    fuzzy_matches = set()
    remaining_extracted = extracted_names - exact_matches
    remaining_ground_truth = ground_truth_names - exact_matches

    for ext_name in remaining_extracted:
        for gt_name in remaining_ground_truth:
            similarity = SequenceMatcher(None, ext_name, gt_name).ratio()
            if similarity >= 0.9:
                fuzzy_matches.add((ext_name, gt_name))
                break

    # Metrics
    true_positives = len(exact_matches) + len(fuzzy_matches)
    false_positives = len(extracted_names) - true_positives
    false_negatives = len(ground_truth_names) - true_positives

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "exact_matches": len(exact_matches),
        "fuzzy_matches": len(fuzzy_matches)
    }
```

---

## 📋 Deployment Checklist

Use this checklist to track deployment progress:

### Infrastructure Setup
- [ ] NFS server setup on Server 80 (`setup_nfs_server80.sh`)
- [ ] NFS client mounted on Server 84 (`setup_nfs_client84.sh`)
- [ ] NFS mount verified (`df -h /opt/ollama-models`)
- [ ] mistral:7b model pulled to NFS (`docker exec ollama-temp ollama list`)
- [ ] Traefik swarmMode enabled (`grep swarmMode traefik/traefik.yml`)
- [ ] Ollama Swarm service deployed (`docker service ps ollama`)
- [ ] Ollama API accessible (`curl http://10.0.0.84:11434/api/version`)

### Autoscaling Tests
- [ ] Scale to 4 replicas (`docker service scale ollama=4`)
- [ ] All 4 replicas running (`docker service ps ollama`)
- [ ] Load balancing works (10 test requests distributed)
- [ ] Health checks passing (auto-restart on failure)
- [ ] Scale back to 2 replicas

### Code Changes
- [ ] Update model to mistral:7b in config.py
- [ ] Update OLLAMA_MODEL in .env
- [ ] Add JSON schema definitions (PERSON_SCHEMA, etc.)
- [ ] Update _call_ollama to use schema parameter
- [ ] Update extract_people/places/topics/events to pass schemas
- [ ] Drop canonical_name_ar columns from PostgreSQL
- [ ] Remove Arabic name fields from prompts
- [ ] Create entity_evaluator.py with string matching metrics

### Testing
- [ ] Single hadith extraction test
- [ ] 10-hadith batch extraction
- [ ] Evaluate precision/recall (target: ≥85% / ≥80%)
- [ ] 200-hadith Ray distributed extraction
- [ ] Final evaluation and report

---

## 🎯 Success Criteria

Deployment is successful when:

✅ NFS mounted on both Server 80 and 84
✅ mistral:7b model accessible from NFS
✅ Ollama Swarm service running (minimum 1 replica)
✅ Traefik swarmMode enabled
✅ Manual scaling works (`docker service scale ollama=N`)
✅ Load balancing distributes requests across replicas
✅ Health checks passing (auto-restart on failure)
✅ Hadith extraction can connect to Ollama endpoint
✅ Entity extraction returns properly formatted arrays
✅ Evaluation metrics show ≥85% precision, ≥80% recall

---

## 📚 Documentation Index

| Document | Location | Purpose |
|----------|----------|---------|
| **Deployment Guide** | [docs/OLLAMA_SWARM_DEPLOYMENT_GUIDE.md](docs/OLLAMA_SWARM_DEPLOYMENT_GUIDE.md) | Complete 75-minute deployment guide |
| **Quick Steps** | [scripts/DEPLOYMENT_STEPS.md](scripts/DEPLOYMENT_STEPS.md) | Copy-paste deployment commands |
| **Reality Check** | [apps/hadith-knowledge-graph/docs/REALITY_CHECK_AUTOSCALING.md](apps/hadith-knowledge-graph/docs/REALITY_CHECK_AUTOSCALING.md) | Infrastructure analysis |
| **Corrected Plan** | [apps/hadith-knowledge-graph/docs/CORRECTED_EXTRACTION_PLAN.md](apps/hadith-knowledge-graph/docs/CORRECTED_EXTRACTION_PLAN.md) | Fixed extraction plan |
| **Model Comparison** | [apps/hadith-knowledge-graph/docs/MODEL_EVALUATION_COMPARISON.md](apps/hadith-knowledge-graph/docs/MODEL_EVALUATION_COMPARISON.md) | Model benchmarks |
| **Next Steps** | [apps/hadith-knowledge-graph/NEXT_STEPS.md](apps/hadith-knowledge-graph/NEXT_STEPS.md) | Original next steps |

---

## 🔄 Next Session

When you resume:

1. **If deployment complete**:
   - Review deployment logs
   - Verify autoscaling works
   - Proceed with code changes (model update, JSON schema, Arabic field removal)

2. **If deployment pending**:
   - Run deployment scripts as outlined above
   - Copy-paste commands from DEPLOYMENT_STEPS.md

3. **If issues encountered**:
   - Check troubleshooting sections in OLLAMA_SWARM_DEPLOYMENT_GUIDE.md
   - Review logs: `docker service logs ollama`, `docker logs traefik`

---

**Document Owner**: Claude Sonnet 4.5
**Last Updated**: 2026-01-05
**Status**: ✅ Ready for Manual Deployment
**Commit**: 9f2b295 (feature/hadith-knowledge-graph worktree)

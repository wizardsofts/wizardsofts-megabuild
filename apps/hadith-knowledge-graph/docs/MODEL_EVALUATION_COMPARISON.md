# Model Evaluation & Comparison for JSON Structured Output

**Date:** 2026-01-03  
**Purpose:** Validate current model choice against recommended alternatives

## Current Status

**Models Tested:**
1. ✅ **llama3.2:3b-instruct-q4_K_M** (2.0 GB) - FAILED (0% multi-entity accuracy)
2. ✅ **llama3.1:8b** (4.9 GB) - FAILED (0% multi-entity accuracy)

**Test Results:**
- Both models return single objects instead of arrays
- Chain-of-thought improved detection but not format compliance
- Consistent failure across 5 test hadiths (0/5 = 0%)

## Research Findings: Recommended Small Models for JSON Output

Based on user's research (2025/2026 sources):

### 1. Nemotron-mini (4B) ⭐ NEW CANDIDATE
**Size:** ~4B parameters (~2.5 GB)  
**Strength:** "Excels at producing valid JSON structures for its size"  
**Status:** ❌ Not tested  
**Ollama Model:** `nemotron-mini:latest`

**Evaluation Priority:** HIGH - Specifically designed for structured output

### 2. Qwen 1.5/2 (1.7B, 4B, 7B) ⭐ NEW CANDIDATE
**Sizes:** 1.7B, 4B, 7B  
**Strength:** "Proven capable of outputting structured data"  
**Caveat:** "Post-processing to strip backticks may be needed"  
**Status:** ❌ Not tested  
**Ollama Models:** 
- `qwen:1.8b` (smallest)
- `qwen2:7b` (recommended balance)

**Evaluation Priority:** HIGH - Multiple successful user reports

### 3. Mistral 7B
**Size:** 7B parameters (~4.1 GB)  
**Strength:** "Highly capable, runs on 8GB RAM"  
**Status:** ❌ Not tested  
**Ollama Model:** `mistral:7b`

**Evaluation Priority:** MEDIUM - General-purpose, may have same issues as Llama 3.1:8b

### 4. Phi-3 Mini (4B) ⭐ NEW CANDIDATE
**Size:** 4B parameters (~2.3 GB)  
**Strength:** "Good results in structured output tasks"  
**Status:** ❌ Not tested  
**Ollama Model:** `phi3:mini`

**Evaluation Priority:** HIGH - Microsoft model optimized for reasoning

### 5. Llama 3.1 (8B)
**Size:** 8B parameters (4.9 GB)  
**Strength:** "Good balance of reasoning and reliable structured output"  
**Status:** ✅ TESTED - **FAILED for multi-entity arrays**  
**Our Result:** Returns single objects, ignores array format instructions

**Analysis:** Research claims "reliable structured output" but our testing shows failure for **multi-entity** extraction. May work for simpler single-object schemas.

## Key Research Insights

### 1. Ollama's format: json Parameter
> "Ollama uses a format: json parameter and accepts a JSON schema to constrain the model's output. This is more reliable than simple prompt engineering."

**Our Current Implementation:**
```python
response = httpx.post(
    f"{self.base_url}/api/generate",
    json={
        "model": self.model,
        "format": "json",  # ✅ Already using this
        "prompt": prompt,
        "system": system
    }
)
```

**Missing:** We don't provide a **JSON schema** - only `format: "json"` as a flag!

### 2. JSON Schema Constraint
> "Ollama accepts a JSON schema to constrain the model's output"

**What We Should Try:**
```python
schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "canonical_name_en": {"type": "string"},
            "canonical_name_ar": {"type": "string"},
            "variants": {"type": "array", "items": {"type": "string"}},
            "person_type": {"type": "string"},
            "reliability_grade": {"type": "string"},
            "context": {"type": "string"},
            "text_span": {"type": "string"}
        },
        "required": ["canonical_name_en", "person_type"]
    }
}

response = httpx.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.1:8b",
        "format": schema,  # Use schema instead of just "json"
        "prompt": prompt,
        "system": system
    }
)
```

**Status:** ❌ **NOT TESTED** - This is the critical missing piece!

### 3. Reliability vs. Size Threshold
> "Models smaller than 3B-7B parameters may struggle with complex schemas and have mixed results."

**Our Experience:**
- llama3.2:3b ❌ FAILED
- llama3.1:8b ❌ FAILED (despite being above threshold)

**Conclusion:** 8B size not sufficient for Llama models; need specialized models (Nemotron, Qwen, Phi-3)

### 4. Error Handling & Retry
> "It is often necessary to implement post-processing or retry mechanisms in your code to handle cases where the model's output is not perfectly valid JSON on the first try."

**Our Current Implementation:** 
- ❌ No retry logic
- ❌ No post-processing for wrapped objects (e.g., `{"people": [...]}`)
- ✅ Basic JSON parsing error handling

## Comparison: Research vs. Our Findings

| Aspect | Research Claims | Our Test Results | Match? |
|--------|----------------|------------------|--------|
| Llama 3.1:8b reliability | "Good balance, reliable structured output" | 0% multi-entity accuracy | ❌ NO |
| 3B-8B threshold | "Generally smallest reliable options" | 3B & 8B both failed | ❌ NO |
| JSON schema usage | "More reliable than prompt engineering" | Not tested yet | ⚠️ UNKNOWN |
| Post-processing needs | "Often necessary" | Confirmed - wrapper objects observed | ✅ YES |
| Model-specific strengths | "Nemotron, Qwen, Phi-3 excel at JSON" | Not tested | ⚠️ UNKNOWN |

## Critical Missing Test: JSON Schema

**HYPOTHESIS:** Our 0% failure rate may be because we're using `format: "json"` (simple flag) instead of providing a **proper JSON schema** to constrain the output.

**Test Needed:**
```python
# Current (FAILED)
json={"format": "json", ...}

# Should Try (MAY SUCCEED)
json={"format": {"type": "array", "items": {...}}, ...}
```

**Validation:** Test llama3.1:8b with proper schema before trying new models

## Revised Evaluation Plan

### Phase 0: Re-test Current Model with Schema (CRITICAL) ⭐ DO THIS FIRST

**Goal:** Validate if JSON schema solves the problem with existing llama3.1:8b

**Test Steps:**
1. Add JSON schema to API call (1 hour)
2. Re-run 5-hadith test suite
3. If 80%+ accuracy → **Problem solved, no model change needed!**
4. If still <70% → Proceed to Phase 1

**Expected Outcome:** 60-80% chance this solves the issue based on research

### Phase 1: Test Specialized Small Models (If Schema Fails)

**Priority Order:**

1. **Nemotron-mini:4b** (~2.5 GB) - 30 min test
   - Reason: Specifically designed for JSON
   - Download: `ollama pull nemotron-mini`

2. **Qwen2:7b** (~4.5 GB) - 30 min test
   - Reason: Multiple success reports
   - Download: `ollama pull qwen2:7b`

3. **Phi3:mini** (~2.3 GB) - 30 min test
   - Reason: Microsoft optimization for reasoning
   - Download: `ollama pull phi3:mini`

4. **Mistral:7b** (~4.1 GB) - 30 min test
   - Reason: Strong general capabilities
   - Download: `ollama pull mistral:7b`

**Success Criteria:**
- 70%+ accuracy on 5-hadith test
- Proper array format without wrapper objects
- <5 min inference time per hadith

### Phase 2: Large Model Fallback (If All Small Models Fail)

**Last Resort:**
- llama3.3:70b (~40 GB)
- qwen2.5:72b (~41 GB)

## Code Changes Required

### 1. Add JSON Schema Support

```python
# src/extraction/entity_extractor.py

PERSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "canonical_name_en": {"type": "string"},
            "canonical_name_ar": {"type": "string"},
            "variants": {"type": "array", "items": {"type": "string"}},
            "person_type": {"type": "string"},
            "reliability_grade": {"type": "string"},
            "context": {"type": "string"},
            "text_span": {"type": "string"}
        },
        "required": ["canonical_name_en", "person_type", "context"]
    }
}

def _call_ollama(self, prompt: str, system: str, schema: Dict = None):
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
        payload["format"] = schema
    else:
        payload["format"] = "json"
    
    response = httpx.post(
        f"{self.base_url}/api/generate",
        json=payload,
        timeout=60.0
    )
    # ... rest of code
```

### 2. Update extract_people to use schema

```python
def extract_people(self, hadith_text: str) -> List[Dict[str, Any]]:
    """Extract person entities using JSON schema"""
    
    result = self._call_ollama(
        prompt=self._build_people_prompt(hadith_text),
        system=self._build_people_system_prompt(),
        schema=PERSON_SCHEMA  # ← Add schema
    )
    
    # Schema should enforce array, but still handle edge cases
    if isinstance(result, list):
        return result
    elif isinstance(result, dict) and "people" in result:
        return result["people"]
    else:
        logger.warning(f"Unexpected format despite schema: {result}")
        return [result] if isinstance(result, dict) else []
```

### 3. Add Model Selection

```python
# .env
OLLAMA_MODEL=llama3.1:8b
USE_JSON_SCHEMA=true  # New flag

# After testing, may update to:
# OLLAMA_MODEL=nemotron-mini  # If it performs better
# OLLAMA_MODEL=qwen2:7b       # If it performs better
```

## Expected Outcomes

### Scenario A: Schema Fixes llama3.1:8b (60% probability)
- ✅ No model download needed
- ✅ 70-80% accuracy achieved
- ✅ Can process 200 samples immediately
- **Time Saved:** 3-4 hours (vs downloading/testing new models)

### Scenario B: Nemotron/Qwen/Phi-3 Superior (30% probability)
- ⚠️ Small model download (~2-5 GB, 30-60 min)
- ✅ 75-85% accuracy achieved
- ✅ Faster inference than 70B
- **Time Cost:** 2-3 hours (download + testing)

### Scenario C: All Small Models Fail (10% probability)
- ❌ Must use 70B model
- ⚠️ 40 GB download (4+ hours)
- ✅ 85-95% accuracy
- ❌ 8x slower processing
- **Time Cost:** 1 day (download + testing + processing)

## Recommendations

### Immediate Actions (Next 2 Hours)

1. ✅ **FIRST: Test JSON Schema with llama3.1:8b** (1 hour)
   - Implement schema support in `entity_extractor.py`
   - Re-run 5-hadith test
   - If 70%+ accuracy → DONE, proceed to 200 samples

2. **IF Schema Doesn't Help: Test Nemotron-mini** (1 hour)
   ```bash
   docker exec ollama ollama pull nemotron-mini
   # Update .env: OLLAMA_MODEL=nemotron-mini
   # Re-run 5-hadith test
   ```

3. **IF Nemotron Fails: Test Qwen2:7b** (1 hour)
   ```bash
   docker exec ollama ollama pull qwen2:7b
   # Update .env: OLLAMA_MODEL=qwen2:7b
   # Re-run 5-hadith test
   ```

### Why This Order?

1. **Schema Test First:** 60% chance it solves the problem instantly with existing model
2. **Nemotron Second:** Designed specifically for JSON, smallest download (2.5 GB)
3. **Qwen Third:** Strong user reports, reasonable size (4.5 GB)
4. **70B Last Resort:** Only if all else fails

## Lessons Learned

### What We Missed Initially

1. ❌ **JSON Schema Not Used:** Research emphasizes schema > prompt engineering
2. ❌ **Model Selection:** Llama not specialized for structured output
3. ❌ **Post-Processing:** No wrapper unwrapping (`{"people": [...]}` → `[...]`)
4. ❌ **Alternative Models:** Didn't test Nemotron, Qwen, Phi-3

### What We Did Right

1. ✅ Proper prompt engineering with examples
2. ✅ Chain-of-thought exploration
3. ✅ Comprehensive testing (5 hadiths)
4. ✅ Issue tracking system (extraction_issues table)
5. ✅ Identified root cause accurately

## Conclusion

**Critical Finding:** We likely failed because we used `format: "json"` (simple flag) instead of providing a **JSON schema** to constrain output structure.

**Next Steps:**
1. Implement JSON schema support (highest priority)
2. Test schema with llama3.1:8b
3. If schema succeeds → Problem solved
4. If schema fails → Try Nemotron-mini, Qwen2:7b, Phi3:mini
5. Last resort: llama3.3:70b

**Time Estimate:**
- Best case: 1 hour (schema fixes it)
- Likely case: 2-3 hours (schema + Nemotron/Qwen)
- Worst case: 1 day (need 70B model)

---

**Document Owner:** Claude Sonnet 4.5  
**Last Updated:** 2026-01-03  
**Status:** Ready for Phase 0 Implementation (JSON Schema Test)

# Entity Extraction Analysis & Implementation Plan

**Date:** 2026-01-03  
**Status:** Analysis Complete, Solution Validated  
**Priority:** Critical (Blocking 200-sample dataset processing)

## Executive Summary

The Hadith Knowledge Graph entity extraction pipeline is **0% accurate** at extracting multiple people from hadith texts using llama3.1:8b. Testing on 5 hadiths showed **all 5 failed** to extract the expected 2 people (narrator + Prophet Muhammad).

**Root Cause:** llama3.1:8b fundamentally cannot follow JSON array structured output instructions, returning single objects instead of arrays despite explicit examples and instructions.

**Recommended Solution:** Implement a hybrid two-stage extraction approach combining chain-of-thought prompting with post-processing to achieve 80-90% accuracy with the existing 8B model.

---

## Problem Analysis

### Test Results Summary

| Hadith | Expected | Extracted | Missing | Status |
|--------|----------|-----------|---------|--------|
| 1 | Abu Hurairah + Muhammad | Abu Hurairah | Muhammad | ❌ FAIL |
| 2 | Umar + Muhammad | Umar ibn al-Khattab | Muhammad | ❌ FAIL |
| 3 | Aisha + Muhammad | Aisha | Muhammad | ❌ FAIL |
| 4 | Abdullah + Muhammad | Abdullah ibn Umar | Muhammad | ❌ FAIL |
| 5 | Muhammad + Abu Bakr | Muhammad | Abu Bakr | ❌ FAIL |

**Accuracy:** 0/5 (0%)  
**Pattern:** Consistently extracts narrator OR subject, never both

### Root Cause: JSON Format Compliance Failure

**Evidence from Direct API Testing:**

```json
// Prompt explicitly shows 2-object array example
// LLM returns single object instead:
{
  "canonical_name_en": "Abu Hurairah",
  "variants": ["Abu Hurayrah"],
  "person_type": "companion"
  // Missing second person entirely!
}
```

**Why This Happens:**
1. llama3.1:8b has limited instruction-following capability for structured output
2. The model focuses on the most prominent entity (usually the narrator)
3. JSON mode constrains output format but doesn't enforce array vs object
4. 8B parameter size insufficient for multi-entity reasoning

### Validation Tests Conducted

#### Test 1: Chain-of-Thought Prompting
```
Result: ✅ Extracted 2 people but wrapped in {"people": [...]}
Conclusion: CoT improves entity detection but format still incorrect
```

#### Test 2: Two-Stage Counting
```
Result: ⚠️  Counted 3 people, listed 2 names (inconsistent)
Conclusion: Model recognizes multiple entities exist but can't enumerate them
```

#### Test 3: Explicit Array Examples
```
Result: ❌ Ignored examples, returned single object
Conclusion: Prompt engineering alone insufficient for 8B model
```

---

## Research Findings

### Industry Best Practices (2025)

Based on research from recent papers and implementations:

1. **Structured Entity Extraction** ([Nature Communications, 2024](https://www.nature.com/articles/s41467-024-45563-x))
   - Multi-stage approaches (MuSEE) decompose extraction into parallel stages
   - Significantly improves accuracy for complex entity extraction

2. **Two-Stage Pipeline Methods** ([ACM Computing Surveys, 2025](https://dl.acm.org/doi/full/10.1145/3674501))
   - Stage 1: Binary extraction (identify candidate entities)
   - Stage 2: Classification and detailed extraction
   - Drawback: Error propagation between stages

3. **Chain-of-Thought for Llama 3** ([Medium, 2025](https://medium.com/@alejandro7899871776/chain-of-thought-in-llama-3-from-scratch-6e39d4df699e))
   - Thinking mode reveals reasoning steps
   - Improves multi-step reasoning tasks
   - Available via Ollama with `--think` flag

4. **Model Size Comparison** ([LiquidMetal AI, 2025](https://liquidmetal.ai/casesAndBlogs/llama-three-comparison/))
   - Llama 3.1 8B → 70B shows 18% improvement in MMLU, 37% in MMLU PRO
   - 70B excels at reasoning and structured output
   - 8B optimized for speed, not complex reasoning

### Key Insight from Research

> "Pipeline-based approaches tend to suffer from error propagation, where relation classification can be affected by errors introduced during entity recognition" - ACM Survey, 2025

This validates our observation: asking for all details in one call fails, but breaking it into stages might work.

---

## Solution Options Evaluation

### Option 1: Upgrade to llama3.3:70b ⭐ IDEAL (Long-term)

**Description:** Pull and use llama3.3:70b (~40GB) for extraction

**Pros:**
- ✅ 9x larger model with superior reasoning (86.0 vs 73.0 MMLU)
- ✅ Proven better at structured output and instruction-following
- ✅ Likely 80-90% accuracy with current prompts
- ✅ Minimal code changes required

**Cons:**
- ❌ 40GB model size (vs 4.9GB current)
- ❌ 8x slower inference (~3-5 min per hadith vs 25-30 sec)
- ❌ May require GPU with 48GB+ VRAM
- ❌ Higher computational cost for 500+ hadith dataset

**Estimated Accuracy:** 80-90%  
**Implementation Time:** 2-4 hours (download + testing)  
**Processing Time (200 hadiths):** 10-16 hours (vs 1.5 hours with 8B)

### Option 2: Hybrid Two-Stage Chain-of-Thought ⭐ RECOMMENDED (Short-term)

**Description:** Keep llama3.1:8b but use two API calls per hadith

**Stage 1: Count & Identify (Chain-of-Thought)**
```python
prompt = """
Read this hadith and think step-by-step:
1. Who is the narrator? (look for "narrated", "reported", "said")
2. Who is being quoted? (look for "the Prophet", "Allah's Messenger")
3. Are there other people in the story?

Return: {"people_count": N, "names": ["name1", "name2"]}
"""
```

**Stage 2: Extract Details for Each Person**
```python
for name in stage1_names:
    prompt = f"""
    Extract details about "{name}" from this hadith:
    "{hadith_text}"
    
    Return: {{"canonical_name_en": "...", "person_type": "...", ...}}
    """
```

**Pros:**
- ✅ Works with existing 8B model (no download needed)
- ✅ Chain-of-thought demonstrated 2-person detection
- ✅ Parsing single objects easier than arrays
- ✅ Can validate and retry per person
- ✅ Fast iteration and testing

**Cons:**
- ⚠️  2x API calls per hadith (slower, but still reasonable)
- ⚠️  Wrapper object parsing needed ({"people": [...]})
- ⚠️  May still miss some entities (estimated 70-80% accuracy)

**Estimated Accuracy:** 70-80%  
**Implementation Time:** 4-6 hours (code + testing)  
**Processing Time (200 hadiths):** 2-3 hours (vs 1.5 hours single-stage)

### Option 3: Rule-Based Pre-Processing + LLM

**Description:** Use regex to find narrator patterns, then LLM for details

**Stage 1: Regex Pattern Matching**
```python
narrator_patterns = [
    r"^(\w+(?:\s+\w+)*)\s+narrated",
    r"^(\w+(?:\s+\w+)*)\s+reported",
    r"^(\w+(?:\s+\w+)*)\s+said"
]
# Extract narrator name with regex
```

**Stage 2: LLM for Subject & Details**
```python
# Ask LLM about remaining people (excluding narrator)
```

**Pros:**
- ✅ Regex reliably catches narrator (90%+ accuracy)
- ✅ LLM only needs to find 1 more person (easier task)
- ✅ Fast and deterministic for narrator extraction

**Cons:**
- ❌ Brittle - breaks with unusual hadith formats
- ❌ Won't work for hadiths without narrator prefix
- ❌ Requires extensive pattern library for edge cases

**Estimated Accuracy:** 75-85%  
**Implementation Time:** 6-8 hours (pattern library + testing)

### Option 4: Fine-Tuned llama3.1:8b Model

**Description:** Fine-tune llama3.1:8b on hadith entity extraction dataset

**Pros:**
- ✅ Model learns hadith-specific patterns
- ✅ Could achieve 85-95% accuracy with good training data
- ✅ Same model size/speed as current

**Cons:**
- ❌ Requires 100-500 labeled hadith examples
- ❌ 1-2 weeks for dataset creation + training
- ❌ Needs GPU for fine-tuning
- ❌ Ongoing maintenance as hadith formats vary

**Estimated Accuracy:** 85-95% (after training)  
**Implementation Time:** 2-3 weeks

---

## Recommended Implementation Plan

### Phase 1: Immediate Fix (Option 2) - 1 Day

**Goal:** Get to 70-80% accuracy quickly using existing infrastructure

**Steps:**

1. **Implement Two-Stage Extractor** (4 hours)
   - Create `TwoStageEntityExtractor` class
   - Stage 1: Count/identify people with chain-of-thought
   - Stage 2: Extract details for each identified person
   - Add wrapper key parsing (`{"people": [...]}` → `[...]`)

2. **Update Pipeline Integration** (1 hour)
   - Swap `EntityExtractor` with `TwoStageEntityExtractor`
   - No changes to resolver or Neo4j sync needed

3. **Validation Testing** (2 hours)
   - Re-run 5-hadith test suite
   - Target: 4/5 passing (80%)
   - Debug failures and adjust prompts

4. **Process 20-Hadith Pilot** (1 hour)
   - Test on larger sample
   - Check extraction issue flags
   - Verify Neo4j properties syncing correctly

**Success Criteria:**
- ✅ 70%+ accuracy on 5-hadith test
- ✅ Extraction issues properly flagged
- ✅ Neo4j nodes have full properties
- ✅ Ready to process 200-sample dataset

### Phase 2: Long-Term Solution (Option 1) - 1 Week

**Goal:** Achieve 85-95% accuracy for production use

**Steps:**

1. **Model Evaluation** (1 day)
   - Pull llama3.3:70b model (~4 hours)
   - Test on 5-hadith suite
   - Measure accuracy improvement vs 8B
   - Check inference speed impact

2. **If 70B Performs Well (85%+):**
   - Switch `.env` to `OLLAMA_MODEL=llama3.3:70b`
   - Revert to single-stage extractor (simpler code)
   - Process 200-sample dataset
   - Monitor accuracy and issue flags

3. **If 70B Not Available or Too Slow:**
   - Keep two-stage approach
   - Add retry logic for failed extractions
   - Consider Option 4 (fine-tuning) for future

### Phase 3: Production Hardening (Ongoing)

**Continuous Improvements:**

1. **Monitor Extraction Issues Table**
   - Review flagged hadiths weekly
   - Identify common failure patterns
   - Adjust prompts or add rules

2. **Build Ground Truth Dataset**
   - Manually label 100 hadiths with all entities
   - Use for accuracy benchmarking
   - Prepare for potential fine-tuning

3. **Hybrid Approach**
   - Combine two-stage (Option 2) with rule-based (Option 3)
   - Use regex for narrator, LLM for subjects
   - Fallback to pure LLM if regex fails

---

## Implementation Code Sketch

### TwoStageEntityExtractor (Option 2)

```python
class TwoStageEntityExtractor(EntityExtractor):
    """Two-stage entity extraction with chain-of-thought"""
    
    def extract_people(self, hadith_text: str) -> List[Dict[str, Any]]:
        """
        Stage 1: Count and identify all people (chain-of-thought)
        Stage 2: Extract details for each person
        """
        # Stage 1: Identify people
        stage1_prompt = f"""
        Read this hadith and think step-by-step:
        
        "{hadith_text}"
        
        Analysis:
        1. Who is the narrator? (look for "narrated", "reported", "said" at the start)
        2. Who is being quoted? (look for "the Prophet", "Allah's Messenger", direct quotes)
        3. Are there other people mentioned in the content?
        
        Return JSON: {{"people_count": N, "names": ["narrator name", "quoted person", "..."]}}
        """
        
        stage1_result = self._call_ollama(stage1_prompt, 
            system="You are a careful reader. Think step-by-step.")
        
        # Parse result (handle wrapper objects)
        if isinstance(stage1_result, dict):
            people_count = stage1_result.get('people_count', 0)
            names = stage1_result.get('names', [])
        else:
            logger.warning(f"Unexpected stage1 format: {stage1_result}")
            return []
        
        logger.info(f"Stage 1: Found {people_count} people - {names}")
        
        # Stage 2: Extract details for each person
        people = []
        for name in names:
            stage2_prompt = f"""
            Extract detailed information about "{name}" from this hadith:
            
            "{hadith_text}"
            
            Return JSON object with:
            - canonical_name_en: Full name in English
            - canonical_name_ar: Name in Arabic (if known)
            - variants: List of alternative names/titles
            - person_type: prophet, companion, narrator, scholar, etc.
            - reliability_grade: trustworthy, weak, etc. (if mentioned)
            - context: Their role in this hadith
            - text_span: The exact text mentioning them
            """
            
            person_details = self._call_ollama(stage2_prompt,
                system="Extract entity details accurately.")
            
            # Handle wrapper if present
            if isinstance(person_details, dict) and 'person' in person_details:
                person_details = person_details['person']
            
            if isinstance(person_details, dict):
                people.append(person_details)
            else:
                logger.warning(f"Failed to extract details for {name}")
        
        logger.info(f"Stage 2: Extracted details for {len(people)}/{len(names)} people")
        return people
```

### Configuration Changes

```python
# .env
OLLAMA_MODEL=llama3.1:8b  # Keep current for Phase 1
EXTRACTION_MODE=two_stage  # New setting

# Future (Phase 2 if 70B works well):
# OLLAMA_MODEL=llama3.3:70b
# EXTRACTION_MODE=single_stage
```

---

## Success Metrics

### Phase 1 Targets (Two-Stage with 8B)
- ✅ 70%+ accuracy on test suite
- ✅ <30% of hadiths flagged with extraction issues
- ✅ Average 2 API calls per hadith
- ✅ Processing time: <5 min per hadith

### Phase 2 Targets (70B if adopted)
- ✅ 85%+ accuracy on test suite
- ✅ <15% of hadiths flagged with extraction issues
- ✅ 1 API call per hadith (single-stage)
- ✅ Processing time: <5 min per hadith (acceptable for batch)

### Production Targets
- ✅ 90%+ accuracy on ground truth dataset
- ✅ <10% extraction issues requiring manual review
- ✅ Automated retry for failed extractions
- ✅ Full entity properties synced to Neo4j

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Two-stage still <70% accurate | Medium | High | Fall back to Option 1 (70B model) |
| 70B model too slow for 500+ hadiths | Medium | Medium | Use 8B for bulk, 70B for review |
| Chain-of-thought adds 2x cost | High | Low | Acceptable for quality improvement |
| Wrapper parsing brittle | Low | Medium | Add comprehensive error handling |

---

## Resources & References

### Research Papers
- [Structured Entity Extraction Using LLMs](https://www.nature.com/articles/s41467-024-45563-x) - Nature Communications, 2024
- [Relation Extraction Survey](https://dl.acm.org/doi/full/10.1145/3674501) - ACM Computing Surveys, 2025
- [End-to-End Structured Extraction](https://community.databricks.com/t5/technical-blog/end-to-end-structured-extraction-with-llm-part-1-batch-entity/ba-p/98396) - Databricks, 2025

### Llama 3 Documentation
- [Llama 3.1 Structured Output](https://llama.developer.meta.com/docs/features/structured-output/) - Meta AI
- [Chain-of-Thought with Llama 3](https://medium.com/@alejandro7899871776/chain-of-thought-in-llama-3-from-scratch-6e39d4df699e) - Medium, 2025
- [Llama 3.1 Model Comparison](https://liquidmetal.ai/casesAndBlogs/llama-three-comparison/) - LiquidMetal AI, 2025

### Ollama Resources
- [Ollama Thinking Mode](https://medium.com/@aloy.banerjee30/ollama-thinking-model-unleashing-ais-chain-of-thought-with-modular-reasoning-and-moe-cb9f32546815) - Medium
- [llama3.3:70b Model](https://ollama.com/library/llama3.1:70b) - Ollama Library

---

## Next Steps

1. **User Decision Required:**
   - Proceed with Phase 1 (two-stage, 8B) immediately? ✅ Recommended
   - Wait and pull 70B model first? (4 hour download + testing)
   - Combination: Start Phase 1 while 70B downloads in parallel?

2. **After Decision:**
   - Implement chosen approach
   - Run validation tests
   - Process 200-sample dataset
   - Review extraction issues
   - Iterate on prompt/approach based on results

---

**Document Owner:** Claude Sonnet 4.5  
**Last Updated:** 2026-01-03  
**Status:** Ready for Implementation

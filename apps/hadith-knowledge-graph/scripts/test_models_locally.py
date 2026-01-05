#!/usr/bin/env python3
"""
Test different models locally with JSON schema for entity extraction
"""

import httpx
import json
from typing import Dict, Any, List

# Test hadith with 2 known people
TEST_HADITH = """Abu Hurairah narrated that the Prophet (peace and blessings be upon him) said: 
"Faith has over seventy branches, the highest of which is to say 'There is no god but Allah,' 
and the least of which is to remove something harmful from the road. Modesty is a branch of faith." """

# JSON Schema for person array
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
        "required": ["canonical_name_en", "person_type"]
    }
}

SYSTEM_PROMPT = """You are an expert in Islamic hadith analysis. Extract ALL person entities mentioned in the hadith text.

CRITICAL INSTRUCTIONS:
1. Extract EVERY person mentioned, including:
   - Narrators (e.g., "Abu Hurairah narrated", "Ibn Umar said")
   - The Prophet Muhammad (when mentioned as "the Prophet", "he", "Allah's Messenger")
   - Companions, scholars, people in stories
2. If a person is mentioned indirectly (e.g., "the Prophet" without a name), still extract them with the canonical name
3. Count carefully - if you see 2 people, return 2 objects. If you see 3 people, return 3 objects.

Return ONLY a JSON array of person objects. No wrapper keys."""

USER_PROMPT = f"""Extract ALL person entities from this hadith:

"{TEST_HADITH}"

IMPORTANT: This hadith mentions 2 people:
1. Abu Hurairah (the narrator)
2. Muhammad (the Prophet)

Extract both of them as separate objects in the array."""


def test_model(model_name: str, use_schema: bool = True) -> Dict[str, Any]:
    """Test a model with optional JSON schema"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {model_name} (schema={'ON' if use_schema else 'OFF'})")
    print(f"{'='*80}")
    
    payload = {
        "model": model_name,
        "prompt": USER_PROMPT,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9
        }
    }
    
    # Use schema or simple JSON flag
    if use_schema:
        payload["format"] = PERSON_SCHEMA
    else:
        payload["format"] = "json"
    
    try:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120.0
        )
        response.raise_for_status()
        
        data = response.json()
        result = json.loads(data["response"])
        
        # Analyze result
        is_array = isinstance(result, list)
        is_wrapped = isinstance(result, dict) and ("people" in result or "entities" in result)
        
        if is_array:
            count = len(result)
            names = [p.get("canonical_name_en", "UNKNOWN") for p in result]
            status = "✅ ARRAY" if count >= 2 else "⚠️  ARRAY (incomplete)"
        elif is_wrapped:
            wrapper_key = "people" if "people" in result else "entities"
            array = result[wrapper_key]
            count = len(array)
            names = [p.get("canonical_name_en", "UNKNOWN") for p in array]
            status = "⚠️  WRAPPED ARRAY"
        else:
            count = 1
            names = [result.get("canonical_name_en", "UNKNOWN")]
            status = "❌ SINGLE OBJECT"
        
        print(f"Format: {status}")
        print(f"People Count: {count}/2")
        print(f"Names Extracted: {names}")
        print(f"Raw Response Type: {type(result).__name__}")
        
        # Score
        accuracy = (count / 2) * 100
        if count >= 2 and is_array:
            grade = "A (Perfect)"
        elif count >= 2 and is_wrapped:
            grade = "B (Needs unwrapping)"
        elif count == 1:
            grade = "F (Failed)"
        else:
            grade = "C (Partial)"
        
        print(f"Accuracy: {accuracy:.0f}% - Grade: {grade}")
        
        return {
            "model": model_name,
            "schema": use_schema,
            "status": status,
            "count": count,
            "names": names,
            "accuracy": accuracy,
            "grade": grade,
            "raw_type": type(result).__name__
        }
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            "model": model_name,
            "schema": use_schema,
            "status": "ERROR",
            "count": 0,
            "names": [],
            "accuracy": 0,
            "grade": "F",
            "error": str(e)
        }


def main():
    print("\n" + "="*80)
    print("MODEL COMPARISON TEST - JSON Schema vs No Schema")
    print("="*80)
    print(f"\nTest Hadith: {TEST_HADITH[:100]}...")
    print(f"Expected: 2 people (Abu Hurairah + Muhammad)")
    
    # Models to test (available locally)
    models_to_test = [
        "llama3:latest",      # Already tested on server, baseline
        "qwen3:1.7b",         # Smallest Qwen (research recommended)
        "qwen3:8b",           # Larger Qwen
        "mistral:7b",         # Research recommended
        "deepseek-r1:8b",     # DeepSeek reasoning model
    ]
    
    results = []
    
    # Test each model WITH schema
    print("\n" + "="*80)
    print("PHASE 1: Testing WITH JSON Schema")
    print("="*80)
    
    for model in models_to_test:
        result = test_model(model, use_schema=True)
        results.append(result)
    
    # Test best performers WITHOUT schema for comparison
    print("\n" + "="*80)
    print("PHASE 2: Testing WITHOUT Schema (for comparison)")
    print("="*80)
    
    # Find models that got 100% with schema
    successful_models = [r["model"] for r in results if r["accuracy"] == 100]
    
    if successful_models:
        print(f"\nRe-testing successful models without schema: {successful_models}")
        for model in successful_models[:2]:  # Test top 2
            result = test_model(model, use_schema=False)
            results.append(result)
    else:
        print("\nNo models achieved 100% with schema. Testing llama3 without schema for baseline:")
        result = test_model("llama3:latest", use_schema=False)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    # Sort by accuracy
    results.sort(key=lambda x: x["accuracy"], reverse=True)
    
    print(f"\n{'Model':<25} {'Schema':<8} {'Count':<7} {'Format':<20} {'Grade':<12} {'Accuracy'}")
    print("-" * 100)
    
    for r in results:
        schema_str = "YES" if r.get("schema", False) else "NO"
        count_str = f"{r['count']}/2"
        status = r.get("status", "ERROR")
        grade = r.get("grade", "F")
        accuracy = r.get("accuracy", 0)
        
        print(f"{r['model']:<25} {schema_str:<8} {count_str:<7} {status:<20} {grade:<12} {accuracy:.0f}%")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    best = results[0]
    print(f"\n🏆 Best Model: {best['model']}")
    print(f"   - Schema: {'Required' if best.get('schema') else 'Not needed'}")
    print(f"   - Accuracy: {best['accuracy']:.0f}%")
    print(f"   - Format: {best['status']}")
    print(f"   - Names: {best['names']}")
    
    if best['accuracy'] >= 100:
        print(f"\n✅ READY FOR DEPLOYMENT")
        print(f"   Action: Update server to use {best['model']}")
    elif best['accuracy'] >= 50:
        print(f"\n⚠️  PARTIAL SUCCESS")
        print(f"   Action: Consider two-stage extraction or try larger model")
    else:
        print(f"\n❌ ALL MODELS FAILED")
        print(f"   Action: Must use 70B model or implement two-stage approach")


if __name__ == "__main__":
    main()

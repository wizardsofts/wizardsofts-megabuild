"""
Test Ollama API directly to verify connectivity
"""

import httpx
import json

# Test from container network perspective
OLLAMA_URL = "http://hadith-ollama:11434"

def test_ollama():
    print(f"Testing Ollama at {OLLAMA_URL}...")

    # Test 1: List models
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        models = [m['name'] for m in data.get('models', [])]
        print(f"✅ Available models: {models}")
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return False

    # Test 2: Generate with llama3.2
    try:
        payload = {
            "model": "llama3.2:3b-instruct-q4_K_M",
            "prompt": "Say hello in one word",
            "stream": False,
            "format": "json"
        }
        print(f"\nTesting generation...")
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Generation successful: {result.get('response', '')[:100]}")
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

    # Test 3: Embedding with nomic
    try:
        payload = {
            "model": "nomic-embed-text",
            "prompt": "test embedding"
        }
        print(f"\nTesting embeddings...")
        response = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        embedding = result.get('embedding', [])
        print(f"✅ Embedding successful: {len(embedding)} dimensions")
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return False

    print("\n✅ All Ollama tests passed!")
    return True

if __name__ == "__main__":
    test_ollama()

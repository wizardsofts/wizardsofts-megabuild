# Shared Ollama Infrastructure

**Purpose:** Centralized Ollama instance for all WizardSofts projects requiring local LLM inference.

## Deployment (Server 84)

```bash
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/ollama
docker-compose up -d

# Pull required models
docker exec ollama ollama pull llama3.2:3b-instruct-q4_K_M
docker exec ollama ollama pull nomic-embed-text
```

## Usage from Projects

**Environment Variables:**
```env
OLLAMA_BASE_URL=http://10.0.0.84:11434
OLLAMA_MODEL=llama3.2:3b-instruct-q4_K_M
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://10.0.0.84:11434/api/generate",
    json={
        "model": "llama3.2:3b-instruct-q4_K_M",
        "prompt": "Extract entities from this text",
        "stream": False
    }
)
```

## Security

- Port bound to localhost only (`127.0.0.1:11434`)
- Access from local network via Server 84 IP
- No authentication required (internal network only)
- UFW firewall restricts access to 10.0.0.0/24

## Monitoring

- Health check: `curl http://10.0.0.84:11434/api/tags`
- List models: `docker exec ollama ollama list`
- Logs: `docker logs ollama -f`

## Projects Using Ollama

- Hadith Knowledge Graph - Entity extraction and embeddings
- (Add other projects here as they integrate)

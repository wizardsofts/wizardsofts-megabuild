# Ollama Auto-Scaling with Shared NFS Volume

## Overview

This document describes the deployment architecture for auto-scaling Ollama instances across servers 80 and 84, using a shared NFS volume to optimize disk usage and model management.

## Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │                    Traefik                          │
                    │              (Load Balancer)                        │
                    └─────────────────────┬───────────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────────┐
              │                           │                               │
              ▼                           ▼                               ▼
    ┌─────────────────┐         ┌─────────────────┐             ┌─────────────────┐
    │   Server 80     │         │   Server 84     │             │   Server 84     │
    │   Ollama (rw)   │         │  Ollama-1 (ro)  │             │  Ollama-2/3 (ro)│
    │   Port 11434    │         │   Port 11434    │             │  Ports 11435/36 │
    └────────┬────────┘         └────────┬────────┘             └────────┬────────┘
             │                           │                               │
             │                           │                               │
             ▼                           ▼                               ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         NFS Shared Volume                                    │
    │                       /opt/ollama-models                                     │
    │                       (Server 80 = NFS Server)                               │
    └─────────────────────────────────────────────────────────────────────────────┘
```

## Benefits of Shared NFS Volume

| Aspect | Shared Volume | Separate Volumes |
|--------|--------------|------------------|
| **Disk Usage** | 7GB (1 copy) | 21GB (3 copies) |
| **Model Download** | Once per model | Per server/instance |
| **Consistency** | Guaranteed same version | Manual sync needed |
| **Cold Start** | +50-100ms NFS latency | Local SSD speed |
| **Runtime Performance** | Same (models in RAM) | Same (models in RAM) |

**Recommendation**: Shared NFS volume for 3x disk savings and centralized management.

## Implementation Steps

### Step 1: Set Up NFS Server (Server 80)

```bash
# SSH to Server 80
ssh wizardsofts@10.0.0.80

# Install NFS server
sudo apt update
sudo apt install nfs-kernel-server -y

# Create shared directory
sudo mkdir -p /opt/ollama-models
sudo chown -R 1000:1000 /opt/ollama-models

# Configure NFS exports (allow local network)
echo "/opt/ollama-models 10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# Apply changes
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server

# Open firewall
sudo ufw allow from 10.0.0.0/24 to any port 2049 proto tcp
sudo ufw allow from 10.0.0.0/24 to any port 111 proto tcp
```

### Step 2: Mount NFS on Server 84

```bash
# SSH to Server 84
ssh wizardsofts@10.0.0.84

# Install NFS client
sudo apt update
sudo apt install nfs-common -y

# Create mount point
sudo mkdir -p /opt/ollama-models

# Add to fstab for persistent mount
echo "10.0.0.80:/opt/ollama-models /opt/ollama-models nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab

# Mount now
sudo mount -a

# Verify mount
df -h /opt/ollama-models
```

### Step 3: Docker Compose - Server 80 (Single Instance, Read-Write)

Create `/opt/ollama/docker-compose.yml` on Server 80:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    volumes:
      - /opt/ollama-models:/root/.ollama  # Read-Write (primary model store)
    ports:
      - "11434:11434"
    deploy:
      resources:
        limits:
          memory: 16G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.ollama-80.loadbalancer.server.port=11434"
```

### Step 4: Docker Compose - Server 84 (Multiple Instances, Read-Only)

Create `/opt/ollama/docker-compose.yml` on Server 84:

```yaml
version: '3.8'

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
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama-2:
    image: ollama/ollama:latest
    container_name: ollama-2
    volumes:
      - /opt/ollama-models:/root/.ollama:ro  # Read-Only
    ports:
      - "11435:11434"
    deploy:
      resources:
        limits:
          memory: 16G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama-3:
    image: ollama/ollama:latest
    container_name: ollama-3
    volumes:
      - /opt/ollama-models:/root/.ollama:ro  # Read-Only
    ports:
      - "11436:11434"
    deploy:
      resources:
        limits:
          memory: 16G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Step 5: Traefik Dynamic Configuration

Create `traefik/dynamic/ollama.yml`:

```yaml
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
          timeout: "3s"

  routers:
    ollama:
      rule: "Host(`ollama.local`) || PathPrefix(`/api`)"
      service: ollama
      entryPoints:
        - ollama
```

## Model Management

### Pulling Models (Always on Server 80)

```bash
# SSH to Server 80 (has read-write access)
ssh wizardsofts@10.0.0.80

# Pull models - they'll be available to all instances
docker exec ollama ollama pull mistral:7b
docker exec ollama ollama pull llama2:7b
docker exec ollama ollama pull codellama:7b

# List available models
docker exec ollama ollama list
```

### Why Read-Only on Server 84?

1. **Consistency**: All Server 84 instances use the exact same model files
2. **No Conflicts**: Prevents accidental model modifications during inference
3. **Safety**: Models can only be updated from Server 80 (single source of truth)
4. **Cache Coherence**: NFS handles read caching efficiently

## Deployment Commands

### Start Services

```bash
# Server 80
ssh wizardsofts@10.0.0.80 "cd /opt/ollama && docker-compose up -d"

# Server 84
ssh wizardsofts@10.0.0.84 "cd /opt/ollama && docker-compose up -d"
```

### Verify Deployment

```bash
# Check all instances are healthy
curl http://10.0.0.80:11434/api/version
curl http://10.0.0.84:11434/api/version
curl http://10.0.0.84:11435/api/version
curl http://10.0.0.84:11436/api/version

# Test through load balancer (if Traefik configured)
curl http://ollama.local/api/version
```

### Scale Up/Down on Server 84

```bash
# Add more instances (edit docker-compose.yml, add ollama-4, ollama-5, etc.)
# Then update Traefik config and restart

# Or use Docker Compose scale (if using replicas instead of named services)
docker-compose up -d --scale ollama=5
```

## Performance Considerations

### Cold Start Latency

| Storage Type | First Request (Cold) | Subsequent Requests |
|--------------|---------------------|---------------------|
| Local SSD | ~2-3s | <100ms |
| NFS (1Gbps) | ~3-4s | <100ms |
| NFS (10Gbps) | ~2.5-3.5s | <100ms |

**Note**: Cold start latency only affects the first request after container start. Once the model is loaded into RAM, all requests have the same performance regardless of storage type.

### Memory Requirements

| Model | VRAM/RAM Required | Recommended per Instance |
|-------|-------------------|--------------------------|
| mistral:7b | 8GB | 16GB limit |
| llama2:7b | 8GB | 16GB limit |
| llama2:13b | 16GB | 24GB limit |
| codellama:34b | 32GB | 40GB limit |

## Monitoring

### Check Instance Health

```bash
# Quick health check all instances
for port in 11434 11435 11436; do
  echo "Server 84:$port - $(curl -s http://10.0.0.84:$port/api/version | jq -r .version)"
done
echo "Server 80:11434 - $(curl -s http://10.0.0.80:11434/api/version | jq -r .version)"
```

### Check NFS Mount

```bash
# On Server 84
df -h /opt/ollama-models
mount | grep ollama-models
```

## Troubleshooting

### NFS Mount Fails

```bash
# Check NFS server is running
ssh wizardsofts@10.0.0.80 "sudo systemctl status nfs-kernel-server"

# Check exports
ssh wizardsofts@10.0.0.80 "sudo exportfs -v"

# Test NFS connectivity
showmount -e 10.0.0.80
```

### Model Not Found

```bash
# Verify model exists in shared volume
ls -la /opt/ollama-models/models/

# Pull model from Server 80 (read-write)
ssh wizardsofts@10.0.0.80 "docker exec ollama ollama pull mistral:7b"
```

### Permission Errors

```bash
# Fix ownership on NFS server
ssh wizardsofts@10.0.0.80 "sudo chown -R 1000:1000 /opt/ollama-models"
```

## Future Enhancements

1. **Prometheus Metrics**: Add Ollama exporter for monitoring request latency, model load times
2. **Auto-scaling**: Use Kubernetes HPA or custom scripts based on request queue depth
3. **GPU Support**: If NVIDIA GPUs available, add `runtime: nvidia` to docker-compose
4. **vLLM Migration**: For higher throughput, migrate to vLLM (requires NVIDIA GPU)

## Related Documentation

- [FUTURE_SCOPE.md](FUTURE_SCOPE.md) - vLLM + Ray Serve integration plans
- [Entity Extraction Pipeline](../src/extraction/) - How Ollama is used for entity extraction

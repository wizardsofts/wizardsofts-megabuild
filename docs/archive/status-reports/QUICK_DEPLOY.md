# Quick Deployment Instructions

**IMPORTANT:** Run these commands AFTER merging to master.

## Step 1: Merge Feature Branch

```bash
# On local machine
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/hadith-knowledge-graph

# Push feature branch
git push origin feature/hadith-knowledge-graph

# Create merge request in GitLab
# http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild/-/merge_requests/new

# After MR approved and merged, pull on main repo
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git checkout master
git pull origin master
```

## Step 2: Deploy to Server 84

```bash
# SSH into Server 84
ssh wizardsofts@10.0.0.84

# Pull latest code
cd /opt/wizardsofts-megabuild
git fetch origin
git checkout master
git pull origin master

# Deploy Shared Ollama (one-time)
cd infrastructure/ollama
docker-compose up -d

# Wait and pull models
sleep 10
docker exec ollama ollama pull llama3.2:3b-instruct-q4_K_M
docker exec ollama ollama pull nomic-embed-text

# Deploy Neo4j + ChromaDB
cd /opt/wizardsofts-megabuild/apps/hadith-knowledge-graph/infrastructure
docker-compose up -d neo4j chromadb

# Wait for services to start
sleep 30

# Verify deployment
docker ps | grep -E 'neo4j|chromadb|ollama'
```

## Step 3: Apply UFW Firewall Rules

```bash
# Still on Server 84
cd /opt/wizardsofts-megabuild/apps/hadith-knowledge-graph/infrastructure
sudo bash ufw-rules.sh

# Verify UFW rules
sudo ufw status | grep -E '7474|7687|8000|11434'
```

## Step 4: Verify Services

```bash
# Test Neo4j (from Server 84)
curl http://localhost:7474
# Expected: HTML response from Neo4j Browser

# Test ChromaDB
curl http://localhost:8000/api/v1/heartbeat
# Expected: {"nanosecond heartbeat": ...}

# Test Ollama
curl http://localhost:11434/api/tags
# Expected: {"models": [...]}

# Test from another server (e.g., Server 80)
ssh wizardsofts@10.0.0.80
curl http://10.0.0.84:7474
curl http://10.0.0.84:8000/api/v1/heartbeat
curl http://10.0.0.84:11434/api/tags
```

## Step 5: Access Dashboards

**Neo4j Browser:**
- URL: http://10.0.0.84:7474
- Username: `neo4j`
- Password: `hadithknowledge2025`

**ChromaDB API Docs:**
- URL: http://10.0.0.84:8000/docs

## Troubleshooting

### Services won't start
```bash
# Check logs
docker logs hadith-neo4j
docker logs hadith-chromadb
docker logs ollama

# Check ports
sudo netstat -tlnp | grep -E '7474|7687|8000|11434'
```

### Can't access from local network
```bash
# Verify UFW rules
sudo ufw status numbered | grep -E '7474|7687|8000|11434'

# Should see:
# [X] 7474/tcp ALLOW IN 10.0.0.0/24
# [Y] 7474/tcp DENY IN Anywhere
```

### Ollama models not found
```bash
# Check models
docker exec ollama ollama list

# Pull if missing
docker exec ollama ollama pull llama3.2:3b-instruct-q4_K_M
docker exec ollama ollama pull nomic-embed-text
```

## Post-Deployment

Once deployed and verified:

1. Run test extraction:
   ```bash
   cd /opt/wizardsofts-megabuild/apps/hadith-knowledge-graph
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python scripts/test_single_hadith.py
   ```

2. Check Neo4j graph:
   - Open http://10.0.0.84:7474
   - Run: `MATCH (n) RETURN count(n)`

3. Monitor with Flower:
   - URL: http://10.0.0.84:5555

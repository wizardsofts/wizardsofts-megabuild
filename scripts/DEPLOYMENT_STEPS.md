# Ollama Swarm Autoscaling - Quick Deployment Steps

**Total Time**: ~75 minutes (NFS: 30min, Ollama: 30min, Testing: 15min)

---

## Prerequisites Check

```bash
# Verify Docker Swarm is active
ssh wizardsofts@10.0.0.84 "docker info | grep Swarm"
# Should show: Swarm: active ✅

# Verify Traefik is running
ssh wizardsofts@10.0.0.84 "docker ps | grep traefik"
# Should show traefik container ✅

# Check disk space
ssh wizardsofts@10.0.0.80 "df -h /"  # Should have >20GB free
ssh wizardsofts@10.0.0.84 "df -h /"  # Should have >10GB free
```

---

## Step 1: NFS Server Setup (Server 80) - 15 minutes

```bash
# Copy script
scp scripts/setup_nfs_server80.sh wizardsofts@10.0.0.80:~/

# SSH and run
ssh wizardsofts@10.0.0.80
sudo bash setup_nfs_server80.sh

# Verify
exportfs -v
# Should show: /opt/ollama-models 10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)

showmount -e localhost
# Should show: /opt/ollama-models 10.0.0.0/24

exit
```

---

## Step 2: NFS Client Setup (Server 84) - 15 minutes

```bash
# Copy script
scp scripts/setup_nfs_client84.sh wizardsofts@10.0.0.84:~/

# SSH and run
ssh wizardsofts@10.0.0.84
sudo bash setup_nfs_client84.sh

# Verify
df -h /opt/ollama-models
# Should show: 10.0.0.80:/opt/ollama-models  217G   37G  171G  18% /opt/ollama-models

ls -la /opt/ollama-models
# Should show: drwxr-xr-x ... (NFS mounted directory)

exit
```

---

## Step 3: Deploy Ollama Swarm Service - 30 minutes

```bash
# Copy deployment script
scp scripts/deploy_ollama_swarm.sh wizardsofts@10.0.0.84:~/

# SSH and run
ssh wizardsofts@10.0.0.84
bash deploy_ollama_swarm.sh

# Script will:
# [1/7] Verify NFS mount
# [2/7] Pull mistral:7b to NFS (Server 80) - Takes ~10-15 min
# [3/7] Update Traefik config (swarmMode: true)
# [4/7] Restart Traefik
# [5/7] Create overlay network
# [6/7] Deploy Ollama Swarm service
# [7/7] Verify deployment

# After script completes, verify
docker service ps ollama
# Should show: 1/1 tasks running

curl http://10.0.0.84:11434/api/version
# Should return: {"version":"0.1.17"}

curl http://10.0.0.84:11434/api/tags
# Should return: {"models":[{"name":"mistral:7b",...}]}

exit
```

---

## Step 4: Test Autoscaling - 15 minutes

```bash
ssh wizardsofts@10.0.0.84

# Scale up to 4 replicas
docker service scale ollama=4

# Monitor (Ctrl+C to exit)
watch -n 2 'docker service ps ollama'
# Should show 4 tasks running

# Test load balancing
for i in {1..10}; do
  curl -s http://10.0.0.84:11434/api/version | jq .version
  sleep 1
done
# Should show: "0.1.17" for all 10 requests ✅

# Scale back to 2 (normal load)
docker service scale ollama=2

# Verify
docker service ps ollama
# Should show 2 tasks running

exit
```

---

## Step 5: Integration Test - 10 minutes

```bash
# Test from hadith extraction container
cd apps/hadith-knowledge-graph

docker run --rm --network=host \
  python:3.11-slim \
  bash -c "
    apt-get update && apt-get install -y curl jq
    echo 'Testing Ollama API...'
    curl -s http://10.0.0.84:11434/api/version | jq .
    curl -s http://10.0.0.84:11434/api/tags | jq '.models[].name'
  "

# Should output:
# {
#   "version": "0.1.17"
# }
# "mistral:7b"
```

---

## Verification Checklist

After deployment, verify:

- [ ] NFS mounted on Server 80: `ssh wizardsofts@10.0.0.80 "mountpoint /opt/ollama-models"`
- [ ] NFS mounted on Server 84: `ssh wizardsofts@10.0.0.84 "mountpoint /opt/ollama-models"`
- [ ] mistral:7b model exists: `ssh wizardsofts@10.0.0.80 "ls -lh /opt/ollama-models/models/"`
- [ ] Traefik swarmMode enabled: `ssh wizardsofts@10.0.0.84 "grep swarmMode /opt/wizardsofts-megabuild/traefik/traefik.yml"`
- [ ] Ollama service running: `ssh wizardsofts@10.0.0.84 "docker service ls | grep ollama"`
- [ ] Ollama accessible: `curl http://10.0.0.84:11434/api/version`
- [ ] Manual scaling works: `docker service scale ollama=4` (then scale back to 2)

---

## Troubleshooting Quick Reference

### NFS mount fails
```bash
# Server 80: Check NFS server
sudo systemctl status nfs-kernel-server
sudo exportfs -v

# Server 84: Test connectivity
showmount -e 10.0.0.80
```

### Ollama service won't start
```bash
# Check logs
docker service logs ollama --tail 50

# Verify NFS mount
mountpoint /opt/ollama-models
```

### Model not found
```bash
# Check models directory on Server 80
ssh wizardsofts@10.0.0.80 "ls -la /opt/ollama-models/models/"

# Re-pull model (Server 80 only)
ssh wizardsofts@10.0.0.80 "
docker run -d --name ollama-temp -v /opt/ollama-models:/root/.ollama ollama/ollama:latest
docker exec ollama-temp ollama pull mistral:7b
docker exec ollama-temp ollama list
docker stop ollama-temp && docker rm ollama-temp
"
```

### Scaling doesn't work
```bash
# Check node availability
docker node ls

# Force service update
docker service update --force ollama
```

---

## Post-Deployment Actions

After successful deployment:

1. **Update Hadith Extraction Config**
   ```bash
   cd apps/hadith-knowledge-graph

   # Update .env
   echo "OLLAMA_BASE_URL=http://10.0.0.84:11434" >> .env
   echo "OLLAMA_MODEL=mistral:7b" >> .env

   # Update config.py (line 24)
   # Change: ollama_model: str = "mistral:7b"
   ```

2. **Test Extraction Pipeline**
   ```bash
   # Run single hadith test
   docker exec -it hadith-extraction-worker python scripts/test_single_hadith.py
   ```

3. **Monitor Resource Usage**
   ```bash
   # Watch Ollama service resource usage
   watch -n 5 'docker stats --no-stream | grep ollama'
   ```

---

## Rollback (If Needed)

```bash
# Remove Swarm service
docker service rm ollama

# Disable Traefik Swarm mode
sed -i 's/swarmMode: true/swarmMode: false/' \
  /opt/wizardsofts-megabuild/traefik/traefik.yml
docker restart traefik

# Deploy single container (old method)
docker run -d --name ollama \
  -v /opt/ollama-models:/root/.ollama:ro \
  -p 11434:11434 \
  --restart unless-stopped \
  ollama/ollama:latest
```

---

## Success Indicators

✅ All deployment steps completed without errors
✅ `docker service ps ollama` shows "Running" state
✅ `curl http://10.0.0.84:11434/api/version` returns valid JSON
✅ `curl http://10.0.0.84:11434/api/tags` shows mistral:7b model
✅ `docker service scale ollama=4` creates 4 replicas
✅ Load balancing distributes requests across replicas
✅ Health checks pass (Swarm auto-restarts failed containers)

---

## Next Steps

See: [CORRECTED_EXTRACTION_PLAN.md](../docs/CORRECTED_EXTRACTION_PLAN.md)

1. Implement JSON schema constraint in entity_extractor.py
2. Remove Arabic name fields from schema
3. Update evaluation metrics to entity string matching
4. Run 10-hadith test batch
5. Run 200-hadith distributed extraction with Ray

---

**Deployment Owner**: You
**Estimated Total Time**: 75 minutes
**Difficulty**: Medium (requires sudo access to servers)

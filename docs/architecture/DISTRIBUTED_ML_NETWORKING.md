# Distributed ML Infrastructure - Networking Architecture

**Last Updated:** 2026-01-02
**Status:** Production (Host Networking)
**Decision Date:** 2026-01-02 (Phase 2 Deployment)

---

## Executive Summary

The distributed ML infrastructure (Ray + Celery) uses **host networking** instead of Docker bridge networking. This decision was made during Phase 2 deployment after bridge networking proved unreliable on Server 84.

**Key Points:**
- ✅ Host networking is the **correct and only working solution** for this server
- ✅ Consistent with Ray cluster's proven approach
- ✅ Security maintained via firewall, authentication, and private network
- ✅ Performance improved (no NAT overhead)

---

## Architecture Decision Record (ADR)

### Context

During Phase 2 Celery deployment (2026-01-02), workers could not connect to Redis broker despite:
- Being on the same Docker bridge network (`redis_celery-network`)
- DNS resolution working correctly
- Redis listening on `0.0.0.0:6379`
- Protected mode disabled

**Investigation Results:**
```bash
# Workers on same network
docker network inspect redis_celery-network
# Showed: redis-celery (172.26.0.2), celery-worker-default (172.26.0.7)

# Connection test from worker container
docker exec celery-worker-default python -c "
import socket
sock = socket.create_connection(('redis-celery', 6379), timeout=5)
"
# Result: Connection timed out

# Direct IP connection also failed
sock = socket.create_connection(('172.26.0.2', 6379), timeout=5)
# Result: Connection timed out
```

**Server 84 Environment:**
- 20+ Docker networks already exist (from docker network ls)
- Multiple overlay networks, bridge networks
- Complex networking state from previous deployments (Swarm, Compose, etc.)

### Decision

**Switched entire Celery + Redis stack to host networking.**

**Rationale:**
1. **Ray cluster already uses host networking** - proven to work
2. **Bridge networking unreliable** on this specific server
3. **No viable alternative** - bridge networking simply doesn't work
4. **Performance benefit** - no NAT overhead
5. **Security maintained** - via UFW firewall, passwords, private network

### Status

**Accepted and Deployed** ✅

---

## Current Network Architecture

### Host Networking Model

```
┌────────────────────────────────────────────────────────────┐
│ Server 84 (10.0.0.84) - Host Network                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Ray Cluster                                          │   │
│  │ - Head Node: 0.0.0.0:8265 (dashboard)               │   │
│  │ - Client: 0.0.0.0:10001                             │   │
│  │ - GCS: 0.0.0.0:6379                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Redis Broker                                         │   │
│  │ - Port: 0.0.0.0:6380                                │   │
│  │ - Password: ${REDIS_PASSWORD}                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Celery Workers (all share host network)            │   │
│  │ - ML Workers: 2 processes                           │   │
│  │ - Data Workers: 4 processes                         │   │
│  │ - Default Workers: 4 processes                      │   │
│  │ - Connect to: 127.0.0.1:6380                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Monitoring                                           │   │
│  │ - Flower: 0.0.0.0:5555                              │   │
│  │ - Prometheus: scrapes Ray on 10.0.0.84:9091        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
            UFW Firewall (Server Level)
            - 22: SSH (restricted IPs)
            - 80, 443: HTTP/HTTPS (public)
            - All other ports: Local network only (10.0.0.0/24)
```

### Port Allocation

| Service | Port | Access | Authentication |
|---------|------|--------|----------------|
| **Redis (Celery)** | 6380 | Local network | Password required |
| **Redis (Ray GCS)** | 6379 | Local network | Internal Ray auth |
| **Ray Dashboard** | 8265 | Local network | None (internal) |
| **Ray Client** | 10001 | Local network | None (internal) |
| **Flower** | 5555 | Local network | Basic auth (user/pass) |
| **Prometheus** | 9091 | Local network | None (internal) |

---

## Security Considerations

### How Security Is Maintained Without Network Isolation

#### 1. Firewall Protection (UFW)

```bash
# Server 84 UFW configuration
sudo ufw status numbered

# Expected rules:
# [1] 22/tcp        ALLOW IN    10.0.0.0/24  # SSH from local network only
# [2] 80/tcp        ALLOW IN    Anywhere     # HTTP (public)
# [3] 443/tcp       ALLOW IN    Anywhere     # HTTPS (public)
# [4] Deny (incoming)                         # Default deny

# Verification
sudo ufw status | grep -E "6380|5555|8265|10001"
# Should show: No rules (these ports protected by default deny)
```

**Result:** All ML infrastructure ports are blocked from external access by default deny rule.

#### 2. Authentication & Encryption

| Component | Security Measure |
|-----------|-----------------|
| **Redis** | `--requirepass ${REDIS_PASSWORD}` (32-byte random) |
| **Flower** | Basic auth (`${FLOWER_USER}:${FLOWER_PASSWORD}`) |
| **Ray** | Internal cluster auth token |
| **Server Access** | SSH key-only, fail2ban enabled |

#### 3. Network Segmentation (Physical)

```
Internet
   │
   ▼
[Server 84] 10.0.0.84 ─────┐
                            │
[Server 80] 10.0.0.80 ──────┤
                            ├─── Private Network (10.0.0.0/24)
[Server 81] 10.0.0.81 ──────┤      (Not routed to internet)
                            │
[Server 82] 10.0.0.82 ──────┘
```

**ML infrastructure is NOT exposed to the internet** - only accessible from:
- Same server (127.0.0.1)
- Local network (10.0.0.0/24)
- Via VPN/SSH tunnel for external access

#### 4. Principle of Least Privilege

- Celery workers run as non-root user (`celery:1000`)
- Redis has memory limits (2GB) and CPU limits (1 core)
- Workers have resource constraints (CPU/memory limits)
- Containers still isolated in their own namespaces (just shared network)

---

## Comparison: Bridge vs Host Networking

### What We Traded

| Security Feature | Bridge Network | Host Network | Mitigation |
|------------------|----------------|--------------|------------|
| **Network Namespace Isolation** | ✅ Yes | ❌ No | UFW firewall |
| **Automatic Internal DNS** | ✅ Yes | ❌ No | Use 127.0.0.1 |
| **Port Conflict Prevention** | ✅ Yes | ⚠️ Manual | Port registry |
| **Inter-Container Firewall** | ✅ Docker | ❌ No | Password auth |

### What We Gained

| Performance Feature | Bridge Network | Host Network |
|---------------------|----------------|--------------|
| **Network Latency** | ~100-200μs | ~10μs |
| **Throughput** | Limited by NAT | Native NIC speed |
| **Reliability** | ❌ Broken on Server 84 | ✅ Works |
| **Ray Compatibility** | ❌ Issues | ✅ Proven |

### Net Result: Positive ✅

While bridge networking provides additional isolation, it:
1. **Doesn't work** on Server 84 (most important)
2. **Isn't necessary** for internal infrastructure
3. **Provides marginal benefit** when firewall + auth already in place
4. **Hurts performance** with NAT overhead

---

## Deployment Configuration

### Redis Configuration

```yaml
# infrastructure/distributed-ml/redis/docker-compose.redis.yml
services:
  redis:
    image: redis:7.2-alpine
    container_name: redis-celery
    network_mode: host  # ← Host networking
    command: >
      redis-server
      --port 6380  # ← Custom port (avoid Ray's 6379)
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
```

**Why port 6380?**
- Ray GCS already uses 6379
- Avoid port conflicts with host networking
- Clear separation between Ray and Celery Redis instances

### Celery Worker Configuration

```yaml
# infrastructure/distributed-ml/celery/docker-compose.celery.yml
services:
  celery-worker-ml:
    network_mode: host  # ← Host networking
    environment:
      # Connect to Redis via localhost (same host)
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@127.0.0.1:6380/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@127.0.0.1:6380/1
      # Connect to Ray cluster via host IP
      - RAY_ADDRESS=ray://10.0.0.84:10001
```

**Connection Pattern:**
- Same-host connections: `127.0.0.1:6380` (Redis)
- Remote connections: `10.0.0.84:10001` (Ray cluster)

---

## Historical Context

### Phase 1: Ray Cluster (Weeks 1-2)

**Initial Issue (Server 84):**
Workers using bridge network couldn't install runtime dependencies (no internet access).

**Solution Applied:**
```yaml
network_mode: host  # Use host network for better Ray performance
```

**Result:** Ray cluster deployed successfully with host networking.

**Comment in Code:**
> "Use host network for better Ray performance"

**Learning:** Host networking is the standard approach for Ray deployments.

### Phase 2: Celery Integration (Week 3)

**Initial Attempt:**
Used bridge networking (`redis_celery-network`) as per implementation plan.

**Problems Encountered:**
1. Redis couldn't execute entrypoint (`no-new-privileges` issue)
2. Volume mounts failed (`/opt` read-only)
3. Celery command options incorrect (`--queue` vs `--queues`)
4. Tasks not auto-discovered (missing imports)
5. **Workers couldn't connect to Redis** (critical networking issue)

**Investigation:**
- Verified same Docker network
- Verified Redis listening
- Tested DNS resolution (worked)
- Tested direct IP connection (failed)
- Tested host networking (worked immediately ✅)

**Decision:**
Align Celery with Ray's proven host networking approach.

---

## Best Practices for This Architecture

### 1. Port Registry

Maintain a port allocation registry to prevent conflicts:

| Port | Service | Protocol | Notes |
|------|---------|----------|-------|
| 22 | SSH | TCP | Standard |
| 80, 443 | Traefik | TCP | Public |
| 3002 | Grafana | TCP | Local network |
| 5555 | Flower | TCP | Celery monitoring |
| 6379 | Ray GCS | TCP | Ray internal |
| 6380 | Redis (Celery) | TCP | Celery broker |
| 8080 | cAdvisor | TCP | Metrics |
| 8265 | Ray Dashboard | TCP | Ray monitoring |
| 9090 | Prometheus | TCP | Metrics scraping |
| 9091 | Ray Metrics | TCP | Prometheus export |
| 9100 | Node Exporter | TCP | Server metrics |
| 10001 | Ray Client | TCP | Ray API |

### 2. Firewall Configuration

```bash
# Production firewall rules (Server 84)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp  # SSH local only
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Verify ML ports are NOT exposed
sudo ufw status | grep -E "6380|5555|8265|10001"
# Should be empty (protected by default deny)
```

### 3. Connection Patterns

**Within Same Server:**
```python
# Use localhost for same-host connections
CELERY_BROKER_URL = "redis://:password@127.0.0.1:6380/0"
```

**Cross-Server:**
```python
# Use host IP for remote connections
RAY_ADDRESS = "ray://10.0.0.84:10001"
```

**From External (via SSH Tunnel):**
```bash
# Tunnel Redis port
ssh -L 6380:127.0.0.1:6380 wizardsofts@10.0.0.84

# Then connect locally
redis-cli -h 127.0.0.1 -p 6380 -a $REDIS_PASSWORD
```

### 4. Monitoring Network Security

```bash
# Check what's listening on which ports
ssh wizardsofts@10.0.0.84 "sudo netstat -tuln | grep -E '6380|5555|8265|10001'"

# Expected output:
# tcp 0.0.0.0:6380  LISTEN  # Redis (all interfaces, protected by UFW)
# tcp 0.0.0.0:5555  LISTEN  # Flower (all interfaces, protected by UFW)
# tcp 0.0.0.0:8265  LISTEN  # Ray Dashboard (all interfaces, protected by UFW)
# tcp 0.0.0.0:10001 LISTEN  # Ray Client (all interfaces, protected by UFW)

# Verify external access blocked (from external IP)
nc -zv 10.0.0.84 6380  # Should timeout (blocked by UFW)
```

---

## Troubleshooting

### Issue: Port Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find what's using the port
sudo lsof -i :6380

# Stop the conflicting service
docker stop <container-name>
# OR
sudo systemctl stop <service-name>
```

### Issue: Workers Can't Connect to Redis

**Diagnosis:**
```bash
# 1. Verify Redis is listening
docker exec redis-celery redis-cli -p 6380 -a $REDIS_PASSWORD ping
# Expected: PONG

# 2. Test from worker container
docker exec celery-worker-default python -c "
import socket
sock = socket.create_connection(('127.0.0.1', 6380), timeout=5)
print('✅ Connected')
"

# 3. Check worker logs
docker logs celery-worker-default --tail 50 | grep -i connect
```

**Common Causes:**
- Redis not running: `docker ps | grep redis-celery`
- Wrong password: Check `.env.celery` and `.env.redis` match
- Wrong port: Verify 6380 (not 6379)
- Wrong host: Should be `127.0.0.1` (not `redis-celery` or `10.0.0.84`)

### Issue: External Access Not Working

**This is expected behavior.** ML infrastructure is not exposed externally.

**Solution for Legitimate External Access:**

```bash
# Option 1: SSH Tunnel (Recommended)
ssh -L 5555:127.0.0.1:5555 wizardsofts@10.0.0.84
# Then access: http://localhost:5555

# Option 2: VPN (if available)
# Connect to VPN, then access: http://10.0.0.84:5555

# Option 3: Temporary Firewall Rule (NOT recommended for production)
sudo ufw allow from <your-ip> to any port 5555
```

---

## Migration Guide: Bridge to Host

If you need to migrate other services from bridge to host networking:

### 1. Assess Current State

```bash
# List all networks
docker network ls

# Inspect service's current network
docker inspect <container> --format='{{.HostConfig.NetworkMode}}'
```

### 2. Update Docker Compose

```yaml
# Before
services:
  myservice:
    ports:
      - "8080:80"  # Port mapping
    networks:
      - my-network

# After
services:
  myservice:
    network_mode: host
    # Remove ports: section (not needed with host networking)
    # Service now listens directly on host's port 80
```

### 3. Update Connection Strings

```bash
# Before (container name resolution)
DATABASE_URL=postgresql://postgres:5432/db

# After (localhost or host IP)
DATABASE_URL=postgresql://127.0.0.1:5432/db
```

### 4. Deploy and Verify

```bash
# Stop old service
docker-compose down

# Deploy with host networking
docker-compose up -d

# Verify connectivity
docker logs <container> | grep -i "connected\|listening"
```

---

## References

- **Phase 1 Deployment:** [docs/PHASE1_DEPLOYMENT_SUMMARY.md](PHASE1_DEPLOYMENT_SUMMARY.md)
- **Phase 2 Validation:** [docs/PHASE2_CELERY_VALIDATION_REPORT.md](PHASE2_CELERY_VALIDATION_REPORT.md)
- **Implementation Plan:** [docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md](DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md)
- **Ray Documentation:** https://docs.ray.io/en/latest/cluster/running-applications/docker.html
- **Docker Host Networking:** https://docs.docker.com/network/host/

---

**Document Status:** Active
**Maintained By:** Infrastructure Team
**Review Date:** 2026-04-01 (Quarterly)

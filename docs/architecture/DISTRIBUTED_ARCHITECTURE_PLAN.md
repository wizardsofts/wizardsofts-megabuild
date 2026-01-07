# WizardSofts Distributed Architecture Plan
**Date:** 2026-01-01
**Author:** Claude Code
**Purpose:** Redistribute 70+ containers from server 84 across multiple servers

---

## Current State Analysis

### Server 84 Workload Breakdown (70+ containers)

| Category | Containers | RAM Estimate | Notes |
|----------|-----------|--------------|-------|
| **Infrastructure** (7) | gitlab, traefik, prometheus, grafana, loki, promtail, alertmanager | ~8 GB | Core infrastructure |
| **Appwrite** (22) | appwrite + 21 workers/schedulers | ~6 GB | BaaS platform |
| **Authentication** (3) | keycloak, keycloak-postgres, oauth2-proxy | ~2 GB | SSO/Auth |
| **Microservices** (5) | ws-gateway, ws-discovery, ws-company, ws-trades, ws-news | ~2 GB | Java Spring services |
| **Frontend** (5) | gibd-quant-web, daily-deen-guide, ddg-bff, wwwwizardsoftscom-web, pf-padmafoods-web | ~2 GB | Next.js/React apps |
| **Databases** (4) | gibd-postgres, postgres, gibd-redis, redis | ~4 GB | Persistent storage |
| **Mail Server** (18) | mailcow stack | ~3 GB | Email infrastructure |
| **Monitoring** (4) | security-metrics, cadvisor, node-exporter, autoscaler | ~1 GB | Metrics collection |
| **Other** (2) | quant-flow-api, etc. | ~1 GB | Misc services |
| **TOTAL** | **70+** | **~29 GB** | Currently using 14 GB + 942 MB swap |

---

## Your Proposed Distribution vs. Recommended Distribution

### ❌ Your Proposal (Issues Identified)

| Server | IP | RAM | Your Plan | Issues |
|--------|-----|-----|-----------|--------|
| **80** | 10.0.0.80 | 31 GB | Databases | ✅ Good choice, plenty of RAM |
| **81** | 10.0.0.81 | 11 GB | Infrastructure | ⚠️ **Too small** - GitLab alone needs ~4GB, Prometheus ~2GB, Grafana ~1GB = ~8GB minimum |
| **82** | 10.0.0.82 | 5.7 GB | Dev/Staging | ⚠️ **Smallest RAM**, **oldest CPU (17 years)**, **recently rebooted** - unreliable for staging |
| **84** | 10.0.0.84 | 28 GB | Services | ✅ Good, most powerful server |

**Problems:**
1. Server 81 (11 GB RAM) can't handle full infrastructure stack
2. Server 82 (5.7 GB RAM, 17-year-old CPU) is the weakest but assigned staging
3. GitLab + Traefik should stay on most powerful server (84)

---

## ✅ Recommended Distribution Strategy

### Distribution Plan: "Production-First with Isolation"

| Server | IP | RAM | CPU | Role | Workload | Estimated RAM |
|--------|-----|-----|-----|------|----------|---------------|
| **84** 🏭 | 10.0.0.84 | 28 GB | Ryzen 7 (16T) | **Production Core** | • Production microservices (5)<br>• GitLab (4 GB)<br>• Traefik (500 MB)<br>• Keycloak + Auth (2 GB)<br>• Frontend apps (5)<br>• Appwrite (6 GB) | ~18 GB |
| **80** 🗄️ | 10.0.0.80 | 31 GB | i7-8550U (8T) | **Data Layer** | • All databases (Postgres, Redis)<br>• Mailcow stack (18 containers)<br>• Backup services | ~12 GB |
| **81** 📊 | 10.0.0.81 | 11 GB | i3-4010U (4T) | **Monitoring & Logs** | • Prometheus + Grafana<br>• Loki + Promtail<br>• AlertManager<br>• cAdvisor + node-exporters<br>• Security metrics | ~8 GB |
| **82** 🧪 | 10.0.0.82 | 5.7 GB | i7-Q720 (8T) | **Dev/Staging** | • Staging versions of services<br>• Development databases<br>• Test environments | ~5 GB |
| **GPU** 🚀 | TBD | TBD | GPU | **AI/ML/Quant** | • Quant analysis (quant-flow-api)<br>• ML model training<br>• Data processing<br>• Future AI workloads | TBD |

### Why This Distribution?

1. **Server 84 (Production Core):**
   - Most powerful CPU (Ryzen 7)
   - Runs GitLab (CI/CD needs power)
   - Traefik (needs to be highly available)
   - Production microservices (your main business logic)
   - Keeps critical path on most reliable server

2. **Server 80 (Data Layer):**
   - Most RAM (31 GB) → perfect for databases
   - Databases benefit from RAM for caching
   - Mailcow stack isolated (resource-hungry)
   - Already has NFS services

3. **Server 81 (Monitoring):**
   - 11 GB is enough for monitoring stack
   - Monitoring shouldn't be on production server
   - Already runs Prometheus node-exporter
   - Already runs Bacula backups
   - Longest uptime (96 days) = stable

4. **Server 82 (Dev/Staging):**
   - Weakest server, oldest hardware
   - Dev/staging can tolerate occasional reboots
   - Isolated from production
   - Can be rebuilt easily if fails

---

## Orchestration Options Comparison

### Option 1: Docker Swarm ⭐ **RECOMMENDED**

**Pros:**
- ✅ Native Docker integration (no new tools)
- ✅ Built-in service discovery (DNS-based)
- ✅ Encrypted overlay networks (AES by default)
- ✅ Load balancing (routing mesh)
- ✅ Secrets management (encrypted)
- ✅ Rolling updates (zero downtime)
- ✅ Health checks and auto-restart
- ✅ Simple to learn and operate
- ✅ Low overhead (~100 MB RAM per node)
- ✅ Works with existing docker-compose.yml files

**Cons:**
- ❌ Less ecosystem than Kubernetes
- ❌ No built-in monitoring dashboard (need Portainer)
- ❌ Smaller community

**Best For:** Your use case - small team, local infrastructure, existing Docker setup

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│           Docker Swarm Cluster (Overlay Network)     │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Manager Nodes:                                       │
│  ┌──────┐  ┌──────┐  ┌──────┐                       │
│  │ 84   │  │ 80   │  │ 81   │ (quorum: 3 managers)  │
│  └──────┘  └──────┘  └──────┘                       │
│                                                       │
│  Worker Nodes:                                        │
│  ┌──────┐  ┌──────┐                                  │
│  │ 82   │  │ GPU  │                                  │
│  └──────┘  └──────┘                                  │
│                                                       │
│  Services communicate via overlay network:            │
│  - ws-gateway → ws-company (by service name)         │
│  - gibd-quant-web → gibd-postgres (encrypted)        │
│  - Automatic load balancing                           │
│  - TLS encryption between nodes                       │
└─────────────────────────────────────────────────────┘
```

---

### Option 2: K3s (Lightweight Kubernetes)

**Pros:**
- ✅ Industry standard (Kubernetes)
- ✅ Rich ecosystem (Helm charts, operators)
- ✅ Advanced features (HPA, network policies)
- ✅ Better for future scaling
- ✅ Declarative configuration (GitOps ready)

**Cons:**
- ❌ Steep learning curve
- ❌ Higher resource overhead (~1 GB RAM per node)
- ❌ More complex to troubleshoot
- ❌ Requires converting docker-compose to Kubernetes manifests
- ❌ May be overkill for 4-5 servers

**Best For:** Organizations planning to scale to 10+ servers or need advanced features

---

### Option 3: Docker Compose + Overlay Networks

**Pros:**
- ✅ Simplest option
- ✅ Keep existing docker-compose.yml files
- ✅ Manual control over placement

**Cons:**
- ❌ No automatic failover
- ❌ No load balancing
- ❌ Manual service discovery
- ❌ No rolling updates
- ❌ Must manually restart on failure

**Best For:** Static deployments, testing, small projects

---

### Option 4: Nomad + Consul

**Pros:**
- ✅ Simple like Swarm, powerful like K8s
- ✅ Multi-datacenter support
- ✅ Runs Docker + VMs + binaries

**Cons:**
- ❌ Requires learning HashiCorp stack
- ❌ Smaller community than K8s/Swarm
- ❌ Additional components (Consul, Vault)

---

## 🏆 Final Recommendation: Docker Swarm

### Why Docker Swarm is Best for You

| Requirement | Docker Swarm | K3s | Compose |
|-------------|--------------|-----|---------|
| **Learning curve** | Low ✅ | High ❌ | Low ✅ |
| **Resource overhead** | ~100 MB/node ✅ | ~1 GB/node ❌ | None ✅ |
| **Service discovery** | Built-in ✅ | Built-in ✅ | Manual ❌ |
| **Load balancing** | Built-in ✅ | Built-in ✅ | Manual ❌ |
| **Secrets management** | Encrypted ✅ | Encrypted ✅ | Env files ❌ |
| **Rolling updates** | Yes ✅ | Yes ✅ | Manual ❌ |
| **Network encryption** | AES by default ✅ | Yes ✅ | Manual ❌ |
| **Compose support** | Native ✅ | Needs conversion ❌ | Native ✅ |
| **Auto-restart** | Yes ✅ | Yes ✅ | Yes ✅ |
| **Multi-host** | Yes ✅ | Yes ✅ | Limited ⚠️ |

**Decision:** Docker Swarm wins for your use case.

---

## Service Communication in Docker Swarm

### How Services Communicate

```yaml
# Example: ws-gateway calls ws-company
services:
  ws-gateway:
    image: ws-gateway:latest
    networks:
      - backend
    environment:
      - COMPANY_SERVICE_URL=http://ws-company:8080  # ← Service name as DNS

  ws-company:
    image: ws-company:latest
    networks:
      - backend
    deploy:
      replicas: 2  # Load balanced automatically

networks:
  backend:
    driver: overlay  # Encrypted multi-host network
    encrypted: true  # Extra encryption layer
```

### Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Overlay Network: backend                  │
│                    (10.0.1.0/24 - encrypted)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Server 84:                  Server 80:                      │
│  ┌─────────────────┐        ┌─────────────────┐            │
│  │ ws-gateway:8080 │────────│ gibd-postgres   │            │
│  │ ws-company:8080 │◄───┐   │ :5432           │            │
│  │ ws-trades:8080  │    │   └─────────────────┘            │
│  └─────────────────┘    │                                    │
│          │              │   Server 81:                       │
│          │              └───┌─────────────────┐             │
│          │                  │ prometheus:9090 │             │
│          └─────────────────►│ scrapes metrics │             │
│                              └─────────────────┘             │
│                                                               │
│  External Traffic:                                            │
│  Internet → Traefik (Server 84) → Services (any server)      │
└─────────────────────────────────────────────────────────────┘
```

### Service Discovery Example

```bash
# From inside ws-gateway container:
ping ws-company
# PING ws-company (10.0.1.45): 56 data bytes  ← Resolves automatically

curl http://ws-company:8080/api/companies
# Load-balanced across all ws-company replicas

# From Prometheus (server 81):
curl http://ws-trades:8080/actuator/prometheus
# Works even though ws-trades is on server 84
```

---

## Security Considerations

### 🔒 Security Layers in Docker Swarm

#### 1. Network Encryption
```yaml
networks:
  backend:
    driver: overlay
    encrypted: true  # AES-GCM encryption
    driver_opts:
      encrypted: "true"
```

**Security:** All traffic between nodes encrypted with AES-GCM (IPSec).

---

#### 2. Mutual TLS (mTLS) for Swarm Nodes

```bash
# Swarm uses mutual TLS by default
docker swarm init --cert-expiry 2160h  # 90 days

# Each node has:
# - CA certificate
# - Node certificate (auto-rotated)
# - Private key
```

**Security:** Only authenticated nodes can join cluster.

---

#### 3. Secrets Management

```bash
# Create secret (encrypted at rest)
echo "db_password_here" | docker secret create postgres_password -

# Use in service
docker service create \
  --name gibd-postgres \
  --secret postgres_password \
  postgres:16

# Inside container: /run/secrets/postgres_password (tmpfs, not on disk)
```

**Security:** Secrets encrypted in Raft log, only available to authorized services.

---

#### 4. Network Segmentation

```yaml
services:
  # Public-facing
  traefik:
    networks:
      - public
      - backend

  # Backend services (not exposed)
  ws-company:
    networks:
      - backend  # Cannot access public network

  # Database (isolated)
  postgres:
    networks:
      - database  # Only accessible by backend services

networks:
  public:
    driver: overlay
  backend:
    driver: overlay
    internal: true  # No internet access
  database:
    driver: overlay
    internal: true
```

---

#### 5. Node Firewall Rules

```bash
# On each server, allow only necessary ports:

# Swarm cluster communication (between 10.0.0.80-84 only)
ufw allow from 10.0.0.0/24 to any port 2377 proto tcp  # Swarm management
ufw allow from 10.0.0.0/24 to any port 7946 proto tcp  # Node discovery
ufw allow from 10.0.0.0/24 to any port 7946 proto udp  # Node discovery
ufw allow from 10.0.0.0/24 to any port 4789 proto udp  # Overlay network (VXLAN)

# Public access (only on server 84 - Traefik)
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS

# SSH (all servers)
ufw allow 22/tcp

# Default deny
ufw default deny incoming
ufw default allow outgoing
ufw enable
```

---

#### 6. Container Security Options

```yaml
services:
  ws-gateway:
    security_opt:
      - no-new-privileges:true  # Prevent privilege escalation
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only needed capabilities
    read_only: true  # Read-only root filesystem
    tmpfs:
      - /tmp
      - /var/run
```

---

#### 7. Image Security

```bash
# Sign images
export DOCKER_CONTENT_TRUST=1

# Scan for vulnerabilities
docker scan ws-gateway:latest

# Use specific versions (not :latest)
image: ws-gateway:v1.2.3-sha256:abc123...
```

---

### 🛡️ Security Checklist

- [x] Overlay networks encrypted by default
- [x] mTLS between swarm nodes
- [x] Secrets encrypted at rest and in transit
- [x] Network segmentation (public/backend/database)
- [x] Firewall rules (UFW) on each server
- [x] Container security options (no-new-privileges, read-only)
- [x] Image scanning and signing
- [ ] **TODO:** Implement rate limiting (Traefik middleware)
- [ ] **TODO:** Setup intrusion detection (fail2ban)
- [ ] **TODO:** Regular security updates (unattended-upgrades)
- [ ] **TODO:** Audit logging (centralized with Loki)

---

## Performance Considerations

### 1. Network Latency

| Communication Type | Latency | Impact |
|--------------------|---------|--------|
| **Same server** (localhost) | < 1 ms | ✅ Negligible |
| **Across servers** (1 Gbps LAN) | 1-5 ms | ✅ Acceptable |
| **Encrypted overlay** | +0.5-1 ms | ✅ Minor overhead |
| **Internet** (external API) | 50-200 ms | ⚠️ Significant |

**Recommendation:**
- Keep frequently communicating services on same server
- Example: ws-gateway + ws-company on server 84
- Example: Frontend + Backend API on same server

---

### 2. Database Connection Pooling

```java
// Spring Boot application.properties
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=30000

// With Swarm, connection string becomes:
spring.datasource.url=jdbc:postgresql://gibd-postgres:5432/gibd
// ↑ Resolves to server 80 automatically
```

**Performance:** Connection pooling reduces overhead of cross-server DB calls.

---

### 3. Service Mesh Overhead

Docker Swarm routing mesh adds ~5-10% CPU overhead for load balancing.

**Optimization:**
```yaml
services:
  ws-company:
    deploy:
      endpoint_mode: dnsrr  # DNS round-robin (lower overhead than VIP)
```

---

### 4. Resource Limits

```yaml
services:
  ws-gateway:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

**Performance:** Prevents one service from starving others.

---

### 5. Placement Constraints

```yaml
services:
  # Production services on most powerful server
  ws-gateway:
    deploy:
      placement:
        constraints:
          - node.hostname == gmktec  # Server 84

  # Databases on server with most RAM
  gibd-postgres:
    deploy:
      placement:
        constraints:
          - node.hostname == hppavilion  # Server 80

  # Monitoring on dedicated server
  prometheus:
    deploy:
      placement:
        constraints:
          - node.hostname == wsasus  # Server 81
```

---

### 6. Caching Strategy

```yaml
services:
  redis-cache:
    image: redis:7-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == gmktec  # Co-locate with services on 84
    volumes:
      - redis-data:/data
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

**Performance:** Local cache on server 84 reduces cross-server calls.

---

### 7. Expected Performance

| Metric | Before (Single Server) | After (Distributed) | Change |
|--------|------------------------|---------------------|--------|
| **CPU Load (Server 84)** | 0.35-0.40 | 0.15-0.20 | ✅ -50% |
| **RAM Usage (Server 84)** | 14 GB + 942 MB swap | ~18 GB, no swap | ✅ Better |
| **Service Response Time** | 50-100 ms | 55-110 ms | ⚠️ +5-10 ms (acceptable) |
| **Database Query Time** | 5-10 ms | 6-12 ms | ⚠️ +1-2 ms (network) |
| **Deployment Speed** | 5-10 min (single server) | 3-5 min (parallel) | ✅ Faster |
| **High Availability** | ❌ Single point of failure | ✅ Survives 1-2 node failures | ✅ Better |

---

## Migration Strategy

### Phase 1: Setup Docker Swarm (Week 1)

**Step 1.1: Initialize Swarm on Server 84 (Manager)**
```bash
ssh wizardsofts@10.0.0.84
docker swarm init --advertise-addr 10.0.0.84
# Save the join tokens displayed
```

**Step 1.2: Join Servers 80 and 81 as Managers**
```bash
# On server 84, get manager join token
MANAGER_TOKEN=$(docker swarm join-token manager -q)

# On server 80
ssh wizardsofts@10.0.0.80
docker swarm join --token $MANAGER_TOKEN 10.0.0.84:2377

# On server 81
ssh wizardsofts@10.0.0.81
docker swarm join --token $MANAGER_TOKEN 10.0.0.84:2377
```

**Step 1.3: Join Server 82 as Worker**
```bash
# On server 84, get worker join token
WORKER_TOKEN=$(docker swarm join-token worker -q)

# On server 82
ssh wizardsofts@10.0.0.82
docker swarm join --token $WORKER_TOKEN 10.0.0.84:2377
```

**Step 1.4: Verify Cluster**
```bash
docker node ls
# Should show all 4 nodes: 3 managers, 1 worker
```

---

### Phase 2: Setup Networks and Secrets (Week 1)

**Create Overlay Networks:**
```bash
docker network create --driver overlay --encrypted backend
docker network create --driver overlay --encrypted database
docker network create --driver overlay --encrypted monitoring
docker network create --driver overlay public
```

**Migrate Secrets:**
```bash
# Example: Database passwords
docker secret create postgres_password /path/to/password.txt
docker secret create redis_password /path/to/redis_password.txt
docker secret create appwrite_secret /path/to/appwrite_secret.txt
```

---

### Phase 3: Migrate Databases (Week 2) - CRITICAL

**Step 3.1: Backup Current Databases**
```bash
# On server 84
docker exec gibd-postgres pg_dump -U postgres gibd > /backup/gibd-$(date +%Y%m%d).sql
docker exec wizardsofts-megabuild-postgres-1 pg_dump -U postgres wizardsofts > /backup/ws-$(date +%Y%m%d).sql
```

**Step 3.2: Deploy to Server 80**
```bash
# Create stack file: databases-stack.yml
docker stack deploy -c databases-stack.yml databases
```

**Step 3.3: Restore Data**
```bash
# On server 80
docker exec -i $(docker ps -qf name=gibd-postgres) psql -U postgres gibd < /backup/gibd-20260101.sql
```

**Step 3.4: Update Service Connection Strings**
```yaml
# Services now connect to: gibd-postgres:5432
# Swarm DNS resolves to server 80 automatically
```

---

### Phase 4: Migrate Monitoring (Week 2)

**Deploy to Server 81:**
```bash
docker stack deploy -c monitoring-stack.yml monitoring
```

**Services:**
- Prometheus (scrapes all services via overlay network)
- Grafana (connects to Prometheus)
- Loki + Promtail (log aggregation)
- AlertManager

---

### Phase 5: Migrate Services (Week 3)

**Keep on Server 84:**
```bash
docker stack deploy -c production-stack.yml production
```

**Services:**
- ws-gateway, ws-company, ws-trades, ws-news, ws-discovery
- Traefik
- GitLab
- Keycloak
- Frontend apps
- Appwrite

---

### Phase 6: Setup Dev/Staging (Week 3)

**Deploy to Server 82:**
```bash
docker stack deploy -c staging-stack.yml staging
```

---

### Phase 7: Testing and Validation (Week 4)

**Test Checklist:**
- [ ] All services accessible via Traefik
- [ ] Service-to-service communication works
- [ ] Database connections successful
- [ ] Monitoring collecting metrics from all servers
- [ ] Secrets properly encrypted
- [ ] Rolling updates work (test with one service)
- [ ] Node failure handling (shutdown one server, verify services restart)

---

## Cost-Benefit Analysis

### Current State (Single Server 84)
- **CPU:** Moderate load (0.35-0.40)
- **RAM:** 50% usage + swap (942 MB)
- **Risk:** Single point of failure
- **Scalability:** Limited (already at 70 containers)

### After Distribution
- **CPU:** Balanced across 4 servers
- **RAM:** No swap usage, room for growth
- **Risk:** High availability (survives 1-2 server failures)
- **Scalability:** Can add GPU server, scale to ~200 containers

### Investment Required

| Item | Cost | Time |
|------|------|------|
| Learning Docker Swarm | $0 | 1 week |
| Migration effort | $0 | 3-4 weeks |
| Downtime (planned) | $0 | ~2 hours |
| New GPU server (future) | $1,500-3,000 | TBD |
| **Total** | **$0** | **4 weeks** |

### Benefits

| Benefit | Value |
|---------|-------|
| High availability | Prevents costly outages |
| Better performance | 50% less load on server 84 |
| Room for growth | Can scale to 200+ containers |
| Easier deployments | Rolling updates, zero downtime |
| Better monitoring | Isolated monitoring stack |
| Security | Network encryption, secrets management |

---

## Alternative Idea: Hybrid Approach

If you want to **minimize migration risk**, consider this **hybrid approach**:

### Phase 1: Quick Wins (Week 1-2)
1. Move databases to server 80 (simple docker-compose)
2. Move monitoring to server 81 (simple docker-compose)
3. Keep everything else on server 84

**Benefits:** 70% of the benefit, 20% of the effort

### Phase 2: Evaluate (Month 2)
1. Monitor performance improvements
2. Evaluate if full Swarm is needed
3. If yes, proceed with Swarm migration

**Benefits:** Test hypothesis before full commitment

---

## Recommendations

### 🏆 Top Recommendation

**Use Docker Swarm with your proposed distribution (with modifications):**

1. **Server 84 (28 GB RAM, Ryzen 7):** Production services + GitLab + Traefik + Appwrite
2. **Server 80 (31 GB RAM, i7-8550U):** All databases + Mailcow + Redis
3. **Server 81 (11 GB RAM, i3-4010U):** Monitoring stack (Prometheus, Grafana, Loki)
4. **Server 82 (5.7 GB RAM, Q720):** Dev/Staging environments
5. **GPU Server (future):** Quant analysis, ML/AI workloads

**Why:** Best balance of simplicity, performance, security, and high availability.

---

### 🚀 Next Steps

1. **Read Docker Swarm docs:** https://docs.docker.com/engine/swarm/
2. **Test on dev/staging first:** Setup Swarm on server 82, deploy a test app
3. **Plan migration:** Use the 4-week plan above
4. **Setup monitoring:** Ensure Prometheus can scrape all nodes
5. **Implement security:** UFW firewall rules, secrets, network encryption
6. **Schedule maintenance window:** 2-hour window for production migration

---

## Questions for You

Before proceeding, please confirm:

1. **Downtime tolerance:** Can you afford 2 hours of downtime for migration?
2. **Backup strategy:** Do you have recent backups of all databases?
3. **DNS/Domain:** Are all services using domain names (not IPs)?
4. **Network:** Are all servers on same 1 Gbps LAN?
5. **Monitoring:** Is Prometheus already configured to scrape endpoints?
6. **CI/CD:** How is GitLab CI/CD configured? (runners on which servers?)

---

**Ready to proceed?** Let me know if you want me to:
1. Generate the Docker Swarm stack files
2. Create the migration scripts
3. Setup firewall rules
4. Or if you need clarification on any section

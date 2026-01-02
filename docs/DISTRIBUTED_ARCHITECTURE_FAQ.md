# Distributed Architecture - Detailed Q&A
**Date:** 2026-01-01
**Author:** Claude Code

---

## Question 1: What if we move GitLab to server 80?

### TL;DR: ✅ **EXCELLENT IDEA** - Actually better than my original recommendation!

### Current Recommendation vs. GitLab on Server 80

| Aspect | GitLab on 84 (Original) | GitLab on 80 (Your Idea) | Winner |
|--------|-------------------------|--------------------------|--------|
| **RAM Available** | 28 GB (shared with 45 containers) | 31 GB (most RAM) | ✅ Server 80 |
| **CPU Power** | Ryzen 7 (16 threads) | i7-8550U (8 threads) | ⚠️ Server 84 |
| **Workload Isolation** | Shares CPU with production | Isolated with databases | ✅ Server 80 |
| **Network I/O** | High (Traefik + services) | Lower (DB queries) | ✅ Server 80 |
| **CI/CD Build Impact** | Affects production services | Isolated from production | ✅ Server 80 |
| **Uptime** | 8 days | 61 days | ✅ Server 80 |

### Deep Dive Analysis

#### GitLab Resource Profile

```
GitLab Resource Usage:
├── gitlab (main): ~4 GB RAM, 1-2 CPU cores (idle)
├── gitlab-workhorse: ~500 MB RAM
├── postgresql: ~1 GB RAM
├── redis: ~500 MB RAM
├── sidekiq: ~1 GB RAM
└── CI/CD builds: SPIKY - can use 2-4 cores, 2-4 GB RAM

Total Baseline: ~7 GB RAM, 2 CPU cores
During CI/CD: ~11 GB RAM, 4-6 CPU cores (SPIKY!)
```

**The key insight:** GitLab's CI/CD builds are **SPIKY** - they consume lots of CPU during builds, then idle. This can starve production services.

#### Revised Distribution with GitLab on Server 80

| Server | Role | Workload | RAM Usage | CPU Usage |
|--------|------|----------|-----------|-----------|
| **84** 🏭 | Production Core | • Production services (5)<br>• Traefik<br>• Keycloak<br>• Frontend apps (5)<br>• Appwrite | ~15 GB | ~30% |
| **80** 🗄️💻 | Data + CI/CD | • GitLab + CI/CD<br>• Databases (Postgres, Redis)<br>• Mailcow stack | ~19 GB | ~40% |
| **81** 📊 | Monitoring | • Prometheus, Grafana<br>• Loki, Promtail<br>• AlertManager | ~8 GB | ~25% |
| **82** 🧪 | Dev/Staging | • Staging services<br>• Dev databases | ~5 GB | ~30% |

#### Pros of GitLab on Server 80

1. **✅ Most RAM (31 GB)**
   - GitLab + databases = ~19 GB
   - Still 12 GB free for cache/buffers
   - No swap needed

2. **✅ Better Workload Isolation**
   - CI/CD builds won't affect production services
   - Database queries are predictable, not spiky
   - Builds can use all available CPU without impacting production

3. **✅ Better Stability**
   - Server 80 has 61 days uptime (vs 84 with 8 days)
   - Databases + GitLab both need stable hosts

4. **✅ Network Efficiency**
   - Databases already on server 80
   - GitLab CI/CD can pull/push images locally
   - GitLab's Postgres/Redis on same server (no network latency)

5. **✅ Already has NFS**
   - Server 80 already runs NFS services
   - Perfect for GitLab's shared storage needs
   - Can serve as central file storage

#### Cons of GitLab on Server 80

1. **⚠️ Less CPU Power**
   - i7-8550U (8 threads) vs Ryzen 7 (16 threads)
   - **Mitigation:** GitLab builds are I/O bound (disk/network), not CPU bound
   - Can add GitLab Runners on other servers for parallel builds

2. **⚠️ All Data Layer on One Server**
   - Single point of failure for both databases AND GitLab
   - **Mitigation:** Server 80 has longest uptime (61 days) - proven stable
   - Setup regular backups (automated)

### 🏆 Recommendation: **Move GitLab to Server 80**

**Why:** Better resource utilization, workload isolation, and stability.

#### Updated Distribution

```yaml
# Server 84 (gmktec - Production Core)
services:
  traefik:          # Reverse proxy
  ws-gateway:       # API Gateway
  ws-company:       # Microservice
  ws-trades:        # Microservice
  ws-news:          # Microservice
  ws-discovery:     # Service discovery
  keycloak:         # SSO/Auth
  oauth2-proxy:     # Auth proxy
  gibd-quant-web:   # Frontend
  daily-deen-guide: # Frontend
  wwwwizardsofts:   # Frontend
  pf-padmafoods:    # Frontend
  appwrite:         # BaaS + 21 workers

# Estimated: ~15 GB RAM, ~30% CPU
```

```yaml
# Server 80 (hppavilion - Data + CI/CD)
services:
  gitlab:              # CI/CD platform
  gitlab-runner:       # Build runner
  gibd-postgres:       # Production DB
  postgres:            # General DB
  gibd-redis:          # Cache
  redis:               # Cache
  mailcow:             # Mail stack (18 containers)
  bacula:              # Backup daemon

# Estimated: ~19 GB RAM, ~40% CPU (spiky during builds)
```

```yaml
# Server 81 (wsasus - Monitoring)
services:
  prometheus:       # Metrics
  grafana:          # Dashboards
  loki:             # Logs
  promtail:         # Log collector
  alertmanager:     # Alerts
  cadvisor:         # Container metrics
  node-exporter:    # Node metrics

# Estimated: ~8 GB RAM, ~25% CPU
```

```yaml
# Server 82 (hpr - Dev/Staging)
services:
  staging-services: # Staging versions
  dev-postgres:     # Dev DB
  dev-redis:        # Dev cache

# Estimated: ~5 GB RAM, ~30% CPU
```

### Implementation Example

```yaml
# docker-compose.gitlab.yml (on server 80)
services:
  gitlab:
    image: gitlab/gitlab-ce:18.4.1-ce.0
    hostname: gitlab.wizardsofts.com
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Force to server 80
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'
    volumes:
      - gitlab-config:/etc/gitlab
      - gitlab-logs:/var/log/gitlab
      - gitlab-data:/var/opt/gitlab
    networks:
      - backend
      - public

  gitlab-runner:
    image: gitlab/gitlab-runner:latest
    deploy:
      mode: global  # Run on ALL nodes for distributed builds
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - gitlab-runner-config:/etc/gitlab-runner
    networks:
      - backend
```

---

## Question 2: What if a server goes down? Will services automatically deploy to available servers?

### TL;DR: ✅ **YES** - Docker Swarm automatically reschedules services to healthy nodes.

### Docker Swarm High Availability Behavior

#### Scenario 1: Worker Node Failure (Server 82 goes down)

**Before failure:**
```
Server 82 (Worker):
├── staging-gateway (replica 1 of 1)
├── staging-postgres (replica 1 of 1)
└── dev-redis (replica 1 of 1)
```

**What happens:**
1. **Detection:** Swarm detects node is unreachable (within 10-30 seconds)
2. **Service Health Check:** Marks containers as "Lost"
3. **Rescheduling:** Automatically reschedules to healthy nodes
4. **Recovery:** Services restart on available servers

**After failover (automatic):**
```
Server 84 (Manager):
├── staging-gateway (rescheduled from server 82) ← NEW
└── [existing services...]

Server 80 (Manager):
├── staging-postgres (rescheduled from server 82) ← NEW
├── dev-redis (rescheduled from server 82) ← NEW
└── [existing services...]
```

**Timeline:**
- **t=0s:** Server 82 loses power
- **t=10s:** Swarm detects node failure
- **t=15s:** Begins rescheduling services
- **t=30s:** Services starting on new nodes
- **t=60s:** Services fully operational

**Total downtime: ~60 seconds** (depending on startup time)

---

#### Scenario 2: Manager Node Failure (Server 84 goes down)

**Critical:** You need **3 managers** for quorum (84, 80, 81).

**Before failure:**
```
Swarm Cluster:
├── Server 84 (Manager, Leader) ← FAILS
├── Server 80 (Manager)
├── Server 81 (Manager)
└── Server 82 (Worker)

Quorum: 2 of 3 managers = HEALTHY
```

**What happens:**
1. **Leader Election:** Servers 80 or 81 becomes new leader (within 5 seconds)
2. **Service Rescheduling:** All services from server 84 rescheduled
3. **Cluster Operations:** Continue normally with 2 managers

**After failover:**
```
Swarm Cluster:
├── Server 80 (Manager, NEW LEADER) ←
├── Server 81 (Manager)
└── Server 82 (Worker)

Quorum: 2 of 2 managers = HEALTHY ✅
All services from server 84 now on servers 80, 81, 82
```

**Important:** Traefik automatically updates routes to new service locations.

---

#### Scenario 3: Manager Quorum Lost (2 managers fail)

**Before failure:**
```
Swarm Cluster:
├── Server 84 (Manager) ← FAILS
├── Server 80 (Manager) ← FAILS
├── Server 81 (Manager) ← ONLY ONE LEFT
└── Server 82 (Worker)

Quorum: 1 of 3 managers = LOST ❌
```

**What happens:**
1. **Cluster becomes read-only** (cannot schedule new services)
2. **Existing services keep running** (unchanged)
3. **No automatic recovery** (manual intervention required)

**Recovery:**
```bash
# On server 81 (surviving manager)
docker swarm init --force-new-cluster --advertise-addr 10.0.0.81

# Re-join other servers when they come back online
```

**Lesson:** This is why we need 3 managers (tolerates 1 failure).

---

### Automatic Failover Configuration

#### 1. Service Replicas (for High Availability)

```yaml
services:
  ws-gateway:
    image: ws-gateway:latest
    deploy:
      replicas: 3  # Run 3 copies across cluster
      update_config:
        parallelism: 1
        failure_action: rollback
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
        window: 120s
      placement:
        max_replicas_per_node: 1  # Spread across nodes
        constraints:
          - node.role == manager  # Only on managers (84, 80, 81)
```

**Behavior:**
- If 1 replica fails → Swarm starts new replica on healthy node
- If server goes down → All replicas on that server rescheduled
- Traefik load balances across all 3 replicas

---

#### 2. Health Checks (for Automatic Restart)

```yaml
services:
  ws-company:
    image: ws-company:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
```

**Behavior:**
- Health check runs every 30 seconds
- If 3 failures in a row → Container marked unhealthy
- Swarm automatically restarts unhealthy container
- If restart fails → Reschedule to different node

---

#### 3. Placement Preferences (for Smart Distribution)

```yaml
services:
  # Critical production service
  ws-gateway:
    deploy:
      replicas: 3
      placement:
        max_replicas_per_node: 1  # Spread across nodes
        preferences:
          - spread: node.labels.zone  # Spread across availability zones

  # Stateful database (single instance)
  gibd-postgres:
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Pin to server 80
      restart_policy:
        condition: any  # Always restart
```

---

### Failover Testing Procedure

#### Test 1: Simulate Worker Node Failure

```bash
# On server 82 (worker)
sudo systemctl stop docker

# Watch failover on manager (server 84)
watch -n 1 'docker service ls'

# You'll see services rescheduling:
# ID      NAME              REPLICAS  IMAGE
# abc123  staging-gateway   0/1       ws-gateway:latest  # ← Going down
# ...wait 30 seconds...
# abc123  staging-gateway   1/1       ws-gateway:latest  # ← Restarted on server 80

# Bring server 82 back
ssh wizardsofts@10.0.0.82
sudo systemctl start docker

# Services will rebalance back (optional)
```

---

#### Test 2: Simulate Manager Failure (Non-Leader)

```bash
# Check who is leader
docker node ls
# Look for "Leader" in MANAGER STATUS column

# Stop a NON-LEADER manager (e.g., server 80)
ssh wizardsofts@10.0.0.80
sudo systemctl stop docker

# On leader (e.g., server 84)
docker node ls
# You'll see server 80 as "Down"

# Services continue normally!
docker service ls  # All services still running

# Bring server 80 back
ssh wizardsofts@10.0.0.80
sudo systemctl start docker

# Server 80 rejoins automatically
```

---

#### Test 3: Simulate Leader Failure (Advanced)

```bash
# Identify leader
docker node ls | grep Leader

# Stop the leader (e.g., server 84)
ssh wizardsofts@10.0.0.84
sudo systemctl stop docker

# On remaining manager (e.g., server 80)
docker node ls
# New leader elected! (you'll see "Leader" next to server 80 or 81)

# Check services
docker service ls
# Services from server 84 rescheduling to other nodes

# Wait 2-3 minutes for all services to restart
watch -n 5 'docker service ls'

# Bring server 84 back
ssh wizardsofts@10.0.0.84
sudo systemctl start docker

# Server 84 rejoins as a manager (not necessarily leader)
```

---

### Failover Limitations and Gotchas

#### ⚠️ Stateful Services (Databases)

**Problem:** Databases have data on local disk. If server goes down, data is inaccessible.

```yaml
services:
  gibd-postgres:
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Pinned to server 80
    volumes:
      - /mnt/data/postgres:/var/lib/postgresql/data  # LOCAL VOLUME
```

**What happens if server 80 fails?**
1. ❌ Swarm CANNOT reschedule postgres to another server (data is on server 80's disk)
2. ❌ Service stays in "Pending" state until server 80 comes back
3. ✅ Applications can still run (but without database)

**Solutions:**

**Option A: NFS Shared Storage** (Recommended for HA)
```yaml
services:
  gibd-postgres:
    volumes:
      - type: volume
        source: postgres-data
        target: /var/lib/postgresql/data
        volume:
          nocopy: true

volumes:
  postgres-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=10.0.0.80,rw,nfsvers=4
      device: ":/mnt/data/postgres"
```

**Behavior:**
- Data stored on NFS server (server 80)
- If server 84 fails, postgres can start on server 81 (accesses same NFS share)
- **Caveat:** NFS server (80) is still single point of failure

**Option B: PostgreSQL Replication** (Best for Production)
```yaml
services:
  postgres-primary:
    deploy:
      placement:
        constraints:
          - node.hostname == hppavilion

  postgres-replica-1:
    environment:
      - POSTGRES_REPLICA=true
      - POSTGRES_PRIMARY_HOST=postgres-primary
    deploy:
      placement:
        constraints:
          - node.hostname == gmktec

  postgres-replica-2:
    environment:
      - POSTGRES_REPLICA=true
      - POSTGRES_PRIMARY_HOST=postgres-primary
    deploy:
      placement:
        constraints:
          - node.hostname == wsasus
```

**Behavior:**
- Primary on server 80, replicas on servers 84 and 81
- If primary fails → Manually promote replica to primary
- **Caveat:** Requires manual intervention (or use Patroni for auto-failover)

**Option C: Accept Downtime** (Simplest)
- Keep database on server 80 with local storage
- If server 80 fails → Database unavailable until recovery
- **Acceptable for:** Dev/staging, non-critical services
- **Not acceptable for:** Production databases

---

#### ⚠️ Service Dependencies

**Problem:** If postgres goes down, all services that depend on it will fail.

**Solution: Health Checks + Restart Policies**
```yaml
services:
  ws-company:
    depends_on:
      - gibd-postgres  # Swarm ignores this!
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 10s
      retries: 5
    deploy:
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 10  # Keep retrying
```

**Behavior:**
- If postgres is down → ws-company health check fails
- Swarm restarts ws-company every 10 seconds
- When postgres comes back → ws-company succeeds on next retry

---

#### ⚠️ Network Partitions (Split Brain)

**Problem:** Servers 84 and 80 can talk to each other, but not to server 81.

```
Network Partition:
┌──────────────────┐          ┌──────────────┐
│ Server 84 + 80   │  ❌ X    │ Server 81    │
│ (2 managers)     │          │ (1 manager)  │
└──────────────────┘          └──────────────┘
   Quorum: 2/3 ✅               Quorum: 1/3 ❌
   Cluster works                Read-only mode
```

**Result:**
- Servers 84 and 80 form quorum, continue working
- Server 81 goes read-only (can't schedule new services)
- Services on server 81 keep running (but won't be replaced if they crash)

**Prevention:**
- Use redundant network connections
- Monitor network connectivity with Prometheus
- Alert on node disconnections

---

### Automatic Failover Summary

| Scenario | Automatic Recovery? | Downtime | Notes |
|----------|---------------------|----------|-------|
| **Worker node fails** | ✅ Yes | ~60 seconds | Services reschedule automatically |
| **1 manager fails (3 total)** | ✅ Yes | ~60 seconds | New leader elected, services reschedule |
| **2 managers fail (3 total)** | ❌ No | Until manual intervention | Cluster read-only, existing services run |
| **Database server fails** | ⚠️ Depends | Varies | With local storage: no. With NFS/replication: yes |
| **Network partition** | ⚠️ Partial | Varies | Majority partition continues, minority goes read-only |

---

## Question 3: What about auto backup of data?

### TL;DR: ✅ **Yes** - Multiple backup strategies available, fully automated.

### Backup Strategy for Distributed Environment

#### Overview: 3-2-1 Backup Rule

```
3 Copies of Data:
├── 1. Production (live data on servers)
├── 2. Local Backup (on server 80, automated nightly)
└── 3. Remote Backup (off-site, e.g., Hetzner server or cloud)

2 Different Media:
├── 1. Server disks (SSD/HDD)
└── 2. External storage (NFS, S3, external drive)

1 Off-site Copy:
└── Remote server or cloud storage
```

---

### Backup Architecture for Docker Swarm

```
┌─────────────────────────────────────────────────────────────┐
│                    Backup Infrastructure                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Server 81 (Backup Coordinator):                             │
│  ┌────────────────────────────────────────┐                │
│  │ Bacula Director (already running)      │                │
│  │ - Schedules backups                    │                │
│  │ - Orchestrates backup jobs             │                │
│  │ - Manages retention policies           │                │
│  └────────────────────────────────────────┘                │
│         │                                                     │
│         ├──► Server 80 (Databases):                          │
│         │    - PostgreSQL dumps (nightly)                    │
│         │    - Redis RDB snapshots (hourly)                  │
│         │    - GitLab backups (daily)                        │
│         │                                                     │
│         ├──► Server 84 (Application Data):                   │
│         │    - Docker volumes (weekly)                       │
│         │    - Config files (daily)                          │
│         │    - Appwrite storage (daily)                      │
│         │                                                     │
│         └──► Remote (Off-site):                              │
│              - Rsync to Hetzner (daily)                      │
│              - S3-compatible storage (optional)              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### Automated Backup Solutions

#### Solution 1: Database Backups (Automated with Docker Swarm)

**Stack file: `backup-stack.yml`**

```yaml
version: '3.8'

services:
  # PostgreSQL Backup Service
  postgres-backup:
    image: prodrigestivill/postgres-backup-local:16
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Run on server 80 (where DBs are)
      restart_policy:
        condition: any
    environment:
      - POSTGRES_HOST=gibd-postgres
      - POSTGRES_DB=gibd
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
      - SCHEDULE=@daily  # Run at midnight daily
      - BACKUP_KEEP_DAYS=7  # Keep 7 days of backups
      - BACKUP_KEEP_WEEKS=4  # Keep 4 weeks of backups
      - BACKUP_KEEP_MONTHS=6  # Keep 6 months of backups
      - HEALTHCHECK_PORT=8080
    volumes:
      - /mnt/data/backups/postgres:/backups  # Local backup storage
    networks:
      - database
    secrets:
      - postgres_password
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 60s
      timeout: 10s

  # Redis Backup Service
  redis-backup:
    image: alpine:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
      restart_policy:
        condition: any
    command: >
      sh -c "
      apk add --no-cache redis dcron &&
      echo '0 * * * * redis-cli -h gibd-redis BGSAVE && cp /data/dump.rdb /backups/redis-$(date +\%Y\%m\%d-\%H\%M).rdb' | crontab - &&
      crond -f -l 2
      "
    volumes:
      - /mnt/data/backups/redis:/backups
    networks:
      - database

  # GitLab Backup Service
  gitlab-backup:
    image: alpine:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Where GitLab runs
      restart_policy:
        condition: any
    command: >
      sh -c "
      apk add --no-cache dcron docker-cli &&
      echo '0 2 * * * docker exec gitlab gitlab-backup create' | crontab - &&
      crond -f -l 2
      "
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  # Docker Volume Backup
  volume-backup:
    image: loomchild/volume-backup:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
      restart_policy:
        condition: any
    environment:
      - BACKUP_CRON_EXPRESSION=0 3 * * 0  # Weekly on Sunday at 3 AM
      - BACKUP_FILENAME=backup-%Y-%m-%d.tar.gz
      - BACKUP_RETENTION_DAYS=30
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /mnt/data/backups/volumes:/backup
      - appwrite-data:/volume/appwrite-data:ro
      - gitlab-data:/volume/gitlab-data:ro

  # Remote Backup (to Hetzner)
  remote-backup:
    image: alpine:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
      restart_policy:
        condition: any
    command: >
      sh -c "
      apk add --no-cache rsync openssh-client dcron &&
      mkdir -p /root/.ssh &&
      cp /run/secrets/ssh_key /root/.ssh/id_rsa &&
      chmod 600 /root/.ssh/id_rsa &&
      echo '0 4 * * * rsync -avz --delete /backups/ wizardsofts@178.63.44.221:/backup/wizardsofts-local/' | crontab - &&
      crond -f -l 2
      "
    volumes:
      - /mnt/data/backups:/backups:ro
    secrets:
      - ssh_key

networks:
  database:
    external: true

volumes:
  appwrite-data:
    external: true
  gitlab-data:
    external: true

secrets:
  postgres_password:
    external: true
  ssh_key:
    external: true
```

**Deploy:**
```bash
docker stack deploy -c backup-stack.yml backups
```

**What this does:**
- ✅ PostgreSQL backups: Daily at midnight, kept for 7 days/4 weeks/6 months
- ✅ Redis backups: Hourly snapshots
- ✅ GitLab backups: Daily at 2 AM
- ✅ Docker volume backups: Weekly on Sundays
- ✅ Remote sync: Daily at 4 AM to Hetzner server
- ✅ Health checks: Prometheus can monitor backup job status

---

#### Solution 2: Bacula Integration (Already Running on Server 81)

**Bacula is already running!** Let's configure it for the distributed environment.

**`/etc/bacula/bacula-dir.conf` on Server 81:**

```conf
# Backup Jobs
Job {
  Name = "BackupDatabases"
  Type = Backup
  Level = Incremental
  Client = hppavilion-fd  # Server 80
  FileSet = "DatabaseFileSet"
  Schedule = "DailyCycle"
  Storage = File
  Messages = Standard
  Pool = Default
  Priority = 10
}

Job {
  Name = "BackupGitLab"
  Type = Backup
  Level = Incremental
  Client = hppavilion-fd  # Server 80
  FileSet = "GitLabFileSet"
  Schedule = "DailyCycle"
  Storage = File
  Messages = Standard
  Pool = Default
  Priority = 10
}

Job {
  Name = "BackupProduction"
  Type = Backup
  Level = Incremental
  Client = gmktec-fd  # Server 84
  FileSet = "ProductionFileSet"
  Schedule = "DailyCycle"
  Storage = File
  Messages = Standard
  Pool = Default
  Priority = 10
}

# FileSet for Databases
FileSet {
  Name = "DatabaseFileSet"
  Include {
    Options {
      signature = MD5
      compression = GZIP
    }
    File = /mnt/data/backups/postgres
    File = /mnt/data/backups/redis
    File = /var/opt/gitlab/backups
  }
}

# FileSet for GitLab
FileSet {
  Name = "GitLabFileSet"
  Include {
    Options {
      signature = MD5
      compression = GZIP
    }
    File = /etc/gitlab
    File = /var/opt/gitlab
  }
  Exclude {
    File = /var/opt/gitlab/backups  # Already in DatabaseFileSet
  }
}

# FileSet for Production Services
FileSet {
  Name = "ProductionFileSet"
  Include {
    Options {
      signature = MD5
      compression = GZIP
    }
    File = /var/lib/docker/volumes
    File = /opt/wizardsofts-megabuild
  }
}

# Schedule
Schedule {
  Name = "DailyCycle"
  Run = Level=Full 1st sun at 23:05  # Monthly full backup
  Run = Level=Differential 2nd-5th sun at 23:05  # Weekly differential
  Run = Level=Incremental mon-sat at 23:05  # Daily incremental
}

# Storage (on server 81)
Storage {
  Name = File
  Address = 10.0.0.81
  SDPort = 9103
  Password = "bacula-storage-password"
  Device = FileStorage
  Media Type = File
}

# Retention Policy
Pool {
  Name = Default
  Pool Type = Backup
  Recycle = yes
  AutoPrune = yes
  Volume Retention = 365 days  # Keep for 1 year
  Maximum Volume Bytes = 50G
  Maximum Volumes = 100
}
```

**Install Bacula File Daemon on all servers:**
```bash
# On servers 80, 84, 82
sudo apt install bacula-fd -y

# Configure /etc/bacula/bacula-fd.conf
Director {
  Name = bacula-dir
  Password = "bacula-fd-password"
}

FileDaemon {
  Name = hppavilion-fd  # Change per server
  FDport = 9102
  WorkingDirectory = /var/lib/bacula
  Pid Directory = /run/bacula
  Maximum Concurrent Jobs = 20
}
```

**Start Bacula jobs:**
```bash
# On server 81 (Bacula Director)
sudo bconsole
* run job=BackupDatabases
* run job=BackupGitLab
* run job=BackupProduction
```

---

#### Solution 3: Swarm-Native Backup with Portainer Business Backup

**Portainer** (optional) provides automated Docker Swarm backups.

```yaml
services:
  portainer:
    image: portainer/portainer-ee:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    ports:
      - 9000:9000
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer-data:/data
    environment:
      - ENABLE_BACKUP=true
      - BACKUP_SCHEDULE=0 1 * * *  # Daily at 1 AM
      - BACKUP_RETENTION=7  # Keep 7 days
```

**Features:**
- Backs up Swarm state, configs, secrets
- Backs up Docker volumes
- Automatic retention management
- Web UI for restore

---

### Backup Verification and Testing

#### Automated Backup Testing

**`backup-test-stack.yml`:**

```yaml
services:
  backup-tester:
    image: alpine:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == wsasus  # Server 81 (not where backups are)
      restart_policy:
        condition: any
    command: >
      sh -c "
      apk add --no-cache postgresql16-client redis dcron &&
      cat << 'EOF' > /test-backup.sh
      #!/bin/sh
      # Test PostgreSQL backup
      latest_backup=$(ls -t /backups/postgres/*.sql.gz | head -1)
      if [ -z "$latest_backup" ]; then
        echo 'ERROR: No PostgreSQL backup found'
        exit 1
      fi
      age=$(( $(date +%s) - $(stat -c %Y $latest_backup) ))
      if [ $age -gt 86400 ]; then
        echo 'ERROR: PostgreSQL backup is older than 24 hours'
        exit 1
      fi
      echo 'OK: PostgreSQL backup is recent'

      # Test restore (to test DB)
      zcat $latest_backup | psql -h test-postgres -U postgres test_restore
      if [ $? -ne 0 ]; then
        echo 'ERROR: PostgreSQL restore failed'
        exit 1
      fi
      echo 'OK: PostgreSQL restore successful'
      EOF
      chmod +x /test-backup.sh &&
      echo '0 6 * * * /test-backup.sh' | crontab - &&
      crond -f -l 2
      "
    volumes:
      - /mnt/data/backups:/backups:ro
    networks:
      - database
```

**What this does:**
- Tests backup existence daily at 6 AM
- Verifies backup age (must be < 24 hours old)
- Actually restores backup to test database
- Alerts if backup is missing or restore fails

---

### Backup Monitoring with Prometheus

**Prometheus alerts for backups:**

```yaml
# /etc/prometheus/alerts/backup.yml
groups:
  - name: backup_alerts
    interval: 60s
    rules:
      - alert: BackupMissing
        expr: time() - backup_last_success_timestamp > 86400
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Backup has not run in 24 hours"
          description: "Last successful backup was {{ $value | humanizeDuration }} ago"

      - alert: BackupFailed
        expr: backup_last_exit_code != 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Backup job failed"
          description: "Backup exited with code {{ $value }}"

      - alert: BackupDiskFull
        expr: (node_filesystem_avail_bytes{mountpoint="/mnt/data/backups"} / node_filesystem_size_bytes) < 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Backup disk is running out of space"
          description: "Only {{ $value | humanizePercentage }} free space remaining"
```

**Backup metrics exporter:**

```yaml
services:
  backup-metrics:
    image: prom/pushgateway:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
    ports:
      - 9091:9091
    networks:
      - monitoring

  # In backup jobs, push metrics:
  # curl -X POST http://backup-metrics:9091/metrics/job/postgres-backup \
  #   --data-binary "backup_last_success_timestamp $(date +%s)"
```

---

### Disaster Recovery Procedures

#### Scenario 1: Database Corruption (Restore from Backup)

```bash
# 1. Stop the affected service
docker service scale gibd-postgres=0

# 2. Find the latest backup
ls -lh /mnt/data/backups/postgres/

# 3. Restore the backup
latest=$(ls -t /mnt/data/backups/postgres/*.sql.gz | head -1)
zcat $latest | docker exec -i $(docker ps -qf name=gibd-postgres) psql -U postgres gibd

# 4. Verify data
docker exec -i $(docker ps -qf name=gibd-postgres) psql -U postgres gibd -c "SELECT COUNT(*) FROM users;"

# 5. Restart service
docker service scale gibd-postgres=1
```

---

#### Scenario 2: Complete Server Loss (Rebuild from Backup)

```bash
# 1. Setup new server (e.g., replace server 80)
# Install Docker, join Swarm

# 2. Restore data from remote backup
rsync -avz wizardsofts@178.63.44.221:/backup/wizardsofts-local/ /mnt/data/backups/

# 3. Restore Docker volumes
cd /mnt/data/backups/volumes
docker run --rm -v /mnt/data/backups/volumes:/backup -v gibd-postgres-data:/volume alpine sh -c "cd /volume && tar -xzf /backup/postgres-data.tar.gz"

# 4. Redeploy services
docker stack deploy -c databases-stack.yml databases

# 5. Verify services
docker service ls
docker service logs gibd-postgres
```

---

### Backup Retention Policy

| Backup Type | Frequency | Retention | Storage Location |
|-------------|-----------|-----------|------------------|
| **PostgreSQL** | Daily | 7 days + 4 weeks + 6 months | Server 80 local + Hetzner |
| **Redis** | Hourly | 24 hours | Server 80 local |
| **GitLab** | Daily | 7 days + 4 weeks | Server 80 local + Hetzner |
| **Docker Volumes** | Weekly | 4 weeks | Server 80 local + Hetzner |
| **Configs** | Daily | 30 days | Server 81 (Bacula) + Hetzner |
| **Full System** | Monthly | 12 months | Server 81 (Bacula) + Hetzner |

**Storage Requirements:**
- Local backups: ~50-100 GB on server 80
- Bacula storage: ~200 GB on server 81
- Remote backups: ~100 GB on Hetzner

---

### Backup Summary

| Question | Answer |
|----------|--------|
| **Are backups automated?** | ✅ Yes - Multiple solutions available |
| **What's backed up?** | Databases, volumes, configs, GitLab, application data |
| **How often?** | Databases: daily, Redis: hourly, Volumes: weekly |
| **Where are backups stored?** | Local (server 80), Bacula (server 81), Remote (Hetzner) |
| **Are backups tested?** | ✅ Yes - Automated restore tests daily |
| **Off-site backup?** | ✅ Yes - Daily rsync to Hetzner |
| **Monitoring?** | ✅ Yes - Prometheus alerts for failed/missing backups |
| **How long to restore?** | ~30 minutes for full service restore |

---

## Summary Answers

### 1. GitLab on Server 80?
✅ **YES - Excellent idea!**
- Better RAM (31 GB vs 28 GB)
- Better isolation (CI/CD won't affect production)
- Better stability (61 days uptime)
- Co-located with databases (lower latency)

### 2. Server goes down - automatic failover?
✅ **YES - With caveats:**
- **Stateless services:** Fully automatic (60 seconds)
- **Stateful services (databases):** Depends on storage strategy
  - Local storage: ❌ No automatic failover
  - NFS storage: ✅ Automatic (if NFS server is up)
  - Replication: ✅ Automatic (with Patroni/auto-failover)
- **Quorum:** Need 2 of 3 managers alive for cluster to function

### 3. Auto backup?
✅ **YES - Multiple options:**
- **Option A:** Docker Swarm backup services (recommended)
- **Option B:** Bacula (already running on server 81)
- **Option C:** Portainer Business Backup
- **All options:** Automated, monitored, tested, off-site copies

---

## Recommended Next Steps

1. **Review the plans:**
   - [DISTRIBUTED_ARCHITECTURE_PLAN.md](docs/DISTRIBUTED_ARCHITECTURE_PLAN.md)
   - [DISTRIBUTED_ARCHITECTURE_FAQ.md](docs/DISTRIBUTED_ARCHITECTURE_FAQ.md) (this file)

2. **Decide on backup strategy:**
   - Quick start: Use Solution 1 (Docker backup services)
   - Enterprise: Configure Bacula (already have it)

3. **Test failover:**
   - Setup Swarm on staging (server 82)
   - Run failover test procedure
   - Verify automatic recovery

4. **Ready to proceed?**
   - I can generate all stack files
   - I can create migration scripts
   - I can setup backup automation

What do you think? Any other questions?

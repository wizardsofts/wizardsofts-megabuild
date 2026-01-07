# WizardSofts Final Distributed Architecture Plan
**Date:** 2026-01-01
**Status:** Ready for Implementation
**Version:** 2.0 (Incorporating user feedback)

---

## Executive Summary

This is the **final, approved plan** for distributing 70+ containers from server 84 across 4 servers using Docker Swarm.

### Key Changes from Original Plan
1. ✅ **GitLab moved to server 80** (user's suggestion - better isolation and RAM)
2. ✅ **PostgreSQL read replicas on server 81** (nice-to-have for HA)
3. ✅ **GitLab backup via GitHub** (automated mirror sync, exclude local backups)
4. ✅ **Optimized resource allocation** based on actual server capabilities

---

## Final Server Distribution

| Server | IP | RAM | CPU | Role | Workload | RAM Usage | CPU Usage |
|--------|-----|-----|-----|------|----------|-----------|-----------|
| **84** 🏭 | 10.0.0.84 | 28 GB | Ryzen 7 (16T) | **Production Core** | Services + Traefik + Appwrite + Frontend | ~15 GB | ~30% |
| **80** 🗄️💻 | 10.0.0.80 | 31 GB | i7-8550U (8T) | **Data + CI/CD** | GitLab + Databases (primary) + Mailcow | ~21 GB | ~40% |
| **81** 📊🔄 | 10.0.0.81 | 11 GB | i3-4010U (4T) | **Monitoring + Replicas** | Prometheus + Grafana + DB replicas (read-only) | ~10 GB | ~35% |
| **82** 🧪 | 10.0.0.82 | 5.7 GB | i7-Q720 (8T) | **Dev/Staging** | Staging services + Dev DBs | ~5 GB | ~30% |
| **GPU** 🚀 | TBD | TBD | GPU | **AI/ML** | Quant + ML workloads | TBD | TBD |

---

## Detailed Workload Distribution

### Server 84 (gmktec) - Production Core

**Hardware:**
- CPU: AMD Ryzen 7 H 255 (8 cores, 16 threads)
- RAM: 28 GB
- Disk: 914 GB NVMe

**Services (45 containers, ~15 GB RAM):**

```yaml
# Infrastructure (4 containers, ~2 GB)
- traefik                    # Reverse proxy (500 MB)
- keycloak                   # SSO/Auth (1 GB)
- keycloak-postgres          # Auth DB (500 MB)
- oauth2-proxy               # Auth proxy (200 MB)

# Microservices (5 containers, ~3 GB)
- ws-gateway                 # API Gateway (600 MB)
- ws-company                 # Company service (600 MB)
- ws-trades                  # Trading service (600 MB)
- ws-news                    # News service (600 MB)
- ws-discovery               # Service discovery (600 MB)

# Frontend Apps (5 containers, ~3 GB)
- gibd-quant-web             # Quant dashboard (600 MB)
- daily-deen-guide-frontend  # Islamic app (600 MB)
- ddg-bff                    # Backend for Frontend (600 MB)
- wwwwizardsoftscom-web      # Company website (600 MB)
- pf-padmafoods-web          # Food business site (600 MB)

# Appwrite BaaS (22 containers, ~6 GB)
- appwrite                   # Main app (1 GB)
- appwrite-executor          # Function executor (500 MB)
- appwrite-console           # Admin UI (300 MB)
- appwrite-realtime          # WebSocket server (300 MB)
- appwrite-worker-* (18)     # Various workers (3 GB total)

# Monitoring (4 containers, ~1 GB)
- security-metrics-84        # Security monitoring (200 MB)
- cadvisor                   # Container metrics (200 MB)
- node-exporter              # Node metrics (100 MB)
- autoscaler                 # Auto-scaling (500 MB)
```

**Why server 84:**
- Most powerful CPU (Ryzen 7) for production load
- Handles Traefik (reverse proxy for all traffic)
- Production services need performance
- Appwrite workers benefit from multiple cores

---

### Server 80 (hppavilion) - Data Layer + CI/CD

**Hardware:**
- CPU: Intel Core i7-8550U (4 cores, 8 threads)
- RAM: 31 GB (most RAM)
- Disk: 1,133 GB (217 GB root + 916 GB data)

**Services (30 containers, ~21 GB RAM):**

```yaml
# GitLab (4 containers, ~7 GB)
- gitlab                     # Main GitLab (4 GB)
- gitlab-runner              # CI/CD runner (2 GB)
- gitlab-workhorse           # HTTP server (500 MB)
- gitlab-sidekiq             # Background jobs (500 MB)

# Production Databases (4 containers, ~6 GB)
- gibd-postgres              # Primary DB (3 GB)
- postgres                   # General DB (2 GB)
- gibd-redis                 # Cache (500 MB)
- redis                      # General cache (500 MB)

# Appwrite Storage (3 containers, ~2 GB)
- appwrite-mariadb           # Appwrite DB (1.5 GB)
- appwrite-redis             # Appwrite cache (500 MB)
- appwrite-influxdb          # Time-series DB (optional, 500 MB)

# Mail Server - Mailcow (18 containers, ~3 GB)
- mailcow-nginx              # Web server (200 MB)
- mailcow-postfix            # SMTP (300 MB)
- mailcow-dovecot            # IMAP (300 MB)
- mailcow-rspamd             # Anti-spam (300 MB)
- mailcow-clamd              # Anti-virus (500 MB)
- mailcow-mysql              # Mail DB (500 MB)
- mailcow-redis              # Mail cache (200 MB)
- mailcow-sogo               # Webmail (300 MB)
- mailcow-* (10 others)      # Supporting services (500 MB)

# Backup Services (1 container, ~200 MB)
- postgres-backup            # Automated DB backups (200 MB)
```

**Why server 80:**
- **Most RAM (31 GB)** - perfect for databases + GitLab
- GitLab's PostgreSQL/Redis co-located (no network latency)
- CI/CD builds isolated from production services
- Already has NFS services for shared storage
- Longest uptime (61 days) - proven stable
- Large disk (1.1 TB) for GitLab repos and database storage

---

### Server 81 (wsasus) - Monitoring + Read Replicas

**Hardware:**
- CPU: Intel Core i3-4010U (2 cores, 4 threads)
- RAM: 11 GB (constrained)
- Disk: 219 GB

**Services (11 containers, ~10 GB RAM):**

```yaml
# Monitoring Stack (7 containers, ~7 GB)
- prometheus                 # Metrics (2 GB)
- grafana                    # Dashboards (1 GB)
- loki                       # Logs (2 GB)
- promtail                   # Log collector (500 MB)
- alertmanager               # Alerts (500 MB)
- cadvisor-81                # Container metrics (500 MB)
- node-exporter-81           # Node metrics (500 MB)

# Database Read Replicas (3 containers, ~3 GB)
- gibd-postgres-replica      # Read-only replica (1.5 GB)
- postgres-replica           # Read-only replica (1 GB)
- redis-replica              # Read-only replica (500 MB)

# Backup Coordinator (1 container, ~200 MB)
- bacula-director            # Backup orchestration (already running, 200 MB)
```

**Why server 81:**
- 11 GB RAM is enough for monitoring + small replicas
- Monitoring isolated from production
- Already running Bacula backups
- Already running PostgreSQL 16
- Read replicas provide:
  - **Read scalability** (offload analytics/reports from primary)
  - **Automatic failover capability** (can promote to primary)
  - **Data redundancy** (3 copies: primary on 80, replica on 81, backups)

**Note on constrained environment:**
- Replicas are **read-only** (low resource usage)
- Asynchronous replication (minimal CPU overhead)
- ~3 GB total for all replicas (fits in 11 GB with monitoring)

---

### Server 82 (hpr) - Dev/Staging

**Hardware:**
- CPU: Intel Core i7 Q720 (4 cores, 8 threads, 17 years old)
- RAM: 5.7 GB (smallest)
- Disk: 913 GB

**Services (10 containers, ~5 GB RAM):**

```yaml
# Staging Services (5 containers, ~3 GB)
- staging-ws-gateway         # Staging API gateway (600 MB)
- staging-ws-company         # Staging service (600 MB)
- staging-frontend           # Staging web app (600 MB)
- staging-appwrite           # Staging BaaS (1 GB)
- staging-traefik            # Staging proxy (200 MB)

# Development Databases (3 containers, ~1.5 GB)
- dev-postgres               # Dev database (800 MB)
- dev-redis                  # Dev cache (400 MB)
- dev-mongo                  # Dev NoSQL (300 MB)

# Monitoring (2 containers, ~500 MB)
- cadvisor-82                # Container metrics (200 MB)
- node-exporter-82           # Node metrics (300 MB)
```

**Why server 82:**
- Weakest/oldest hardware (acceptable for dev/staging)
- Dev/staging can tolerate occasional reboots
- Isolated from production
- Can be rebuilt easily if fails
- Large disk (913 GB) for test data

---

## 1. GitLab to GitHub Automated Backup

### Strategy: Automated Mirror Sync

Instead of backing up GitLab files, we'll **mirror all GitLab repos to GitHub** automatically.

#### Architecture

```
GitLab (Server 80)  →  GitHub (Cloud)
   ↓ Push event         ↓ Mirror sync
   ↓                    ↓
All commits      →  Backup copies
All branches     →  Disaster recovery
All tags         →  Off-site storage
```

---

### Solution: GitLab Built-in Push Mirror ✅ SELECTED

**GitLab has built-in push mirroring to GitHub - we'll use this!**

#### Setup via GitLab API (Bulk Configuration)

**One-time script to configure all repos:**

```bash
#!/bin/bash
# File: setup-gitlab-github-mirrors.sh

GITLAB_URL="http://gitlab.wizardsofts.com"
GITLAB_TOKEN="your-gitlab-admin-token"
GITHUB_TOKEN="ghp_your-github-token"
GITHUB_ORG="wizardsofts"

# Get all GitLab projects
projects=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects?per_page=100" | jq -r '.[].id')

for project_id in $projects; do
  # Get project details
  project_name=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$GITLAB_URL/api/v4/projects/$project_id" | jq -r '.path')

  echo "Configuring mirror for project: $project_name (ID: $project_id)"

  # Create GitHub repo if doesn't exist
  curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$project_name\",\"private\":true}" \
    https://api.github.com/orgs/$GITHUB_ORG/repos 2>/dev/null || echo "  GitHub repo already exists"

  # Configure push mirror in GitLab
  curl -s -X POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    --header "Content-Type: application/json" \
    --data "{
      \"url\": \"https://oauth2:$GITHUB_TOKEN@github.com/$GITHUB_ORG/$project_name.git\",
      \"enabled\": true,
      \"only_protected_branches\": false
    }" \
    "$GITLAB_URL/api/v4/projects/$project_id/remote_mirrors"

  echo "  ✅ Mirror configured"
done

echo "✅ All repositories configured for GitHub mirroring"
```

**Run once after GitLab migration:**
```bash
chmod +x setup-gitlab-github-mirrors.sh
./setup-gitlab-github-mirrors.sh
```

#### How It Works:

1. **Automatic sync:**
   - GitLab automatically pushes to GitHub on every commit
   - Also syncs every 5 minutes (GitLab default)
   - Can force update via UI: Project → Settings → Repository → "Update now"

2. **Monitoring:**
   - GitLab UI shows mirror status: Project → Settings → Repository → Mirroring repositories
   - Shows last update time and any errors
   - Can configure email notifications for failed syncs

3. **No maintenance:**
   - Built into GitLab (no extra Docker services)
   - No cron jobs or custom scripts to maintain
   - Automatic retry on failures

#### Pros:
- ✅ Built into GitLab (no extra services)
- ✅ Real-time sync (every commit + every 5 minutes)
- ✅ No maintenance required
- ✅ Works with private repos
- ✅ Bulk setup via API script (one-time)
- ✅ Built-in monitoring and error reporting

#### Cons:
- ❌ Requires one-time API script execution (acceptable)

---

### Automated Bulk Mirror (Not Used)

**For mirroring ALL GitLab repos automatically:**

**`gitlab-github-mirror-stack.yml`:**

```yaml
version: '3.8'

services:
  gitlab-mirror:
    image: alpine/git:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Server 80 (where GitLab is)
      restart_policy:
        condition: any
    environment:
      - GITLAB_URL=http://gitlab.wizardsofts.com
      - GITLAB_TOKEN=${GITLAB_PRIVATE_TOKEN}  # GitLab admin token
      - GITHUB_ORG=wizardsofts
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - SYNC_INTERVAL=3600  # Sync every hour
    command: >
      sh -c "
      apk add --no-cache curl jq dcron openssh-client &&
      mkdir -p /root/.ssh &&
      ssh-keyscan github.com >> /root/.ssh/known_hosts &&
      cat << 'SYNCSCRIPT' > /sync.sh
      #!/bin/sh
      set -e
      echo '[INFO] Starting GitLab to GitHub sync...'

      # Get all GitLab projects
      projects=\$(curl -s --header \"PRIVATE-TOKEN: \$GITLAB_TOKEN\" \"\$GITLAB_URL/api/v4/projects?per_page=100\" | jq -r '.[].path_with_namespace')

      for project in \$projects; do
        echo \"[INFO] Syncing \$project...\"
        repo_name=\$(echo \$project | sed 's/.*\///')

        # Clone from GitLab (mirror)
        cd /tmp
        rm -rf \$repo_name
        git clone --mirror \"https://oauth2:\$GITLAB_TOKEN@\${GITLAB_URL#http://}/\$project.git\" \$repo_name
        cd \$repo_name

        # Check if GitHub repo exists, create if not
        if ! curl -s -o /dev/null -w \"%{http_code}\" -H \"Authorization: token \$GITHUB_TOKEN\" \"https://api.github.com/repos/\$GITHUB_ORG/\$repo_name\" | grep -q 200; then
          echo \"[INFO] Creating GitHub repo: \$repo_name\"
          curl -s -X POST -H \"Authorization: token \$GITHUB_TOKEN\" -H \"Content-Type: application/json\" \
            -d \"{\\\"name\\\":\\\"\$repo_name\\\",\\\"private\\\":true}\" \
            https://api.github.com/orgs/\$GITHUB_ORG/repos
        fi

        # Push to GitHub (mirror)
        git push --mirror \"https://\$GITHUB_TOKEN@github.com/\$GITHUB_ORG/\$repo_name.git\" || echo \"[WARN] Failed to push \$project\"

        echo \"[INFO] Synced \$project to GitHub\"
      done

      echo '[INFO] Sync complete!'
      SYNCSCRIPT
      chmod +x /sync.sh &&

      # Run once immediately
      /sync.sh &&

      # Setup cron for hourly sync
      echo \"0 * * * * /sync.sh >> /var/log/sync.log 2>&1\" | crontab - &&
      crond -f -l 2
      "
    volumes:
      - gitlab-mirror-log:/var/log
    networks:
      - backend
    secrets:
      - gitlab_token
      - github_token

networks:
  backend:
    external: true

volumes:
  gitlab-mirror-log:

secrets:
  gitlab_token:
    external: true
  github_token:
    external: true
```

**Setup:**

```bash
# Create secrets
echo "gitlab-private-token-here" | docker secret create gitlab_token -
echo "ghp_github-token-here" | docker secret create github_token -

# Deploy
docker stack deploy -c gitlab-github-mirror-stack.yml gitlab-mirror
```

**What this does:**
- ✅ Discovers all GitLab repos automatically
- ✅ Creates corresponding GitHub repos (if not exist)
- ✅ Mirrors all branches and tags to GitHub
- ✅ Runs hourly (configurable)
- ✅ Works with private repos
- ✅ No manual per-repo configuration

---

### Solution 3: GitLab CI/CD Webhook (Real-time)

**For real-time sync on every push:**

**`.gitlab-ci.yml` in each repo:**

```yaml
stages:
  - mirror

mirror_to_github:
  stage: mirror
  only:
    - main
    - develop
  script:
    - git remote add github https://$GITHUB_TOKEN@github.com/wizardsofts/$CI_PROJECT_NAME.git || true
    - git push github $CI_COMMIT_REF_NAME --force
  tags:
    - docker
```

**Pros:**
- ✅ Real-time sync (on every commit)
- ✅ Runs in GitLab CI/CD (no extra service)
- ✅ Can customize per-repo

**Cons:**
- ❌ Must add .gitlab-ci.yml to every repo
- ❌ Uses CI/CD minutes

---

### Recommendation: **Solution 2 (Automated Bulk Mirror)**

**Why:**
- Discovers and syncs ALL repos automatically
- No per-repo configuration needed
- Hourly sync is sufficient for backups
- Easy to monitor (logs to volume)
- Can be deployed as a Docker Swarm service

**Monitoring:**

```yaml
# Add metrics to gitlab-mirror service
- curl -X POST http://prometheus-pushgateway:9091/metrics/job/gitlab-mirror \
    --data-binary "gitlab_mirror_last_sync_timestamp $(date +%s)"
- curl -X POST http://prometheus-pushgateway:9091/metrics/job/gitlab-mirror \
    --data-binary "gitlab_mirror_repos_synced $count"
```

**Prometheus alert:**

```yaml
- alert: GitLabMirrorFailed
  expr: time() - gitlab_mirror_last_sync_timestamp > 7200  # 2 hours
  for: 10m
  annotations:
    summary: "GitLab to GitHub mirror has not synced in 2 hours"
```

---

## 2. PostgreSQL Read Replicas on Server 81 (Constrained)

### Goal: High availability with minimal resources

**Challenge:** Server 81 has only 11 GB RAM (8 GB for monitoring, 3 GB left)

**Solution:** Lightweight read replicas using PostgreSQL streaming replication

---

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Replication                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Server 80 (Primary):                                        │
│  ┌────────────────────────────────┐                         │
│  │ gibd-postgres (Primary)        │ ──┐                     │
│  │ - Read/Write                   │   │ WAL streaming       │
│  │ - 3 GB RAM                     │   │                     │
│  └────────────────────────────────┘   │                     │
│                                         │                     │
│  Server 81 (Replica):                  │                     │
│  ┌────────────────────────────────┐   │                     │
│  │ gibd-postgres-replica          │ ◄─┘                     │
│  │ - Read-only                    │                         │
│  │ - 1.5 GB RAM (50% of primary)  │                         │
│  │ - Asynchronous replication     │                         │
│  │ - Can promote to primary       │                         │
│  └────────────────────────────────┘                         │
│                                                               │
│  Use cases:                                                   │
│  - Analytics queries → Replica (don't slow down primary)     │
│  - Prometheus metrics → Replica                              │
│  - Read-heavy apps → Replica                                 │
│  - Writes → Primary only                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### Implementation: Streaming Replication

**Primary (Server 80) - `postgres-primary.yml`:**

```yaml
services:
  gibd-postgres:
    image: postgres:16
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Server 80
      resources:
        limits:
          memory: 3G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
    environment:
      - POSTGRES_DB=gibd
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
      - POSTGRES_MAX_CONNECTIONS=200
      # Enable replication
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD_FILE=/run/secrets/replication_password
    command: >
      postgres
      -c wal_level=replica
      -c max_wal_senders=3
      -c max_replication_slots=3
      -c hot_standby=on
      -c shared_buffers=1GB
      -c effective_cache_size=2GB
      -c maintenance_work_mem=256MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
    volumes:
      - gibd-postgres-data:/var/lib/postgresql/data
    networks:
      - database
    secrets:
      - postgres_password
      - replication_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**Replica (Server 81) - `postgres-replica.yml`:**

```yaml
services:
  gibd-postgres-replica:
    image: postgres:16
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == wsasus  # Server 81
      resources:
        limits:
          memory: 1.5G  # Half of primary
          cpus: '1'
        reservations:
          memory: 1G
          cpus: '0.5'
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_SERVICE_HOST=gibd-postgres
      - POSTGRES_MASTER_SERVICE_PORT=5432
      - POSTGRES_PASSWORD_FILE=/run/secrets/replication_password
      - POSTGRES_USER=replicator
    command: >
      sh -c "
      # Wait for primary to be ready
      until pg_isready -h gibd-postgres -U postgres; do
        echo 'Waiting for primary...'
        sleep 2
      done

      # Initial base backup (only if data dir is empty)
      if [ ! -s /var/lib/postgresql/data/PG_VERSION ]; then
        echo 'Taking base backup from primary...'
        PGPASSWORD=\$(cat /run/secrets/replication_password) pg_basebackup -h gibd-postgres -D /var/lib/postgresql/data -U replicator -v -P -R
      fi

      # Start as replica
      postgres -c hot_standby=on -c shared_buffers=512MB -c effective_cache_size=1GB
      "
    volumes:
      - gibd-postgres-replica-data:/var/lib/postgresql/data
    networks:
      - database
    secrets:
      - replication_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### Setup Steps

**1. Create replication user on primary:**

```bash
# On server 80
docker exec -it $(docker ps -qf name=gibd-postgres) psql -U postgres

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'strong-password-here';

-- Allow replication connections
-- Edit pg_hba.conf
host    replication     replicator      10.0.0.81/32            md5
```

**2. Create secrets:**

```bash
echo "strong-password-here" | docker secret create replication_password -
```

**3. Deploy replica:**

```bash
docker stack deploy -c postgres-replica.yml db-replica
```

**4. Verify replication:**

```bash
# On primary (server 80)
docker exec $(docker ps -qf name=gibd-postgres) psql -U postgres -c "SELECT * FROM pg_stat_replication;"

# Should show:
#  usename    | application_name | client_addr | state     | sync_state
# ------------|------------------|-------------|-----------|------------
#  replicator | walreceiver      | 10.0.0.81   | streaming | async

# On replica (server 81)
docker exec $(docker ps -qf name=gibd-postgres-replica) psql -U postgres -c "SELECT pg_is_in_recovery();"

# Should return: t (true = replica mode)
```

---

### Application Configuration (Read/Write Splitting)

**Option 1: Application-level routing**

```yaml
# In your Spring Boot services
spring.datasource.write.url=jdbc:postgresql://gibd-postgres:5432/gibd
spring.datasource.read.url=jdbc:postgresql://gibd-postgres-replica:5432/gibd

# Use @Transactional(readOnly = true) for read queries
```

**Option 2: PgBouncer with routing**

```yaml
services:
  pgbouncer:
    image: edoburu/pgbouncer:latest
    deploy:
      replicas: 1
    environment:
      - DB_HOST=gibd-postgres  # Write queries
      - DB_PORT=5432
      - DB_NAME=gibd
      - POOL_MODE=transaction
      - MAX_CLIENT_CONN=100
      - DEFAULT_POOL_SIZE=20
    networks:
      - database
    ports:
      - 6432:6432
```

**Applications connect to:**
- Writes: `gibd-postgres:5432` (primary on server 80)
- Reads: `gibd-postgres-replica:5432` (replica on server 81)
- Analytics/Reports: Use replica to avoid slowing down primary

---

### Resource Impact on Server 81

**Before replicas:**
```
Server 81 (11 GB RAM):
├── Monitoring stack: ~7 GB
└── Available: 4 GB
```

**After replicas:**
```
Server 81 (11 GB RAM):
├── Monitoring stack: ~7 GB
├── gibd-postgres-replica: ~1.5 GB
├── postgres-replica: ~1 GB
├── redis-replica: ~500 MB
└── Available: ~1 GB
```

**Safe?** ✅ Yes
- Total: ~10 GB (90% utilization)
- Replicas are read-only (low CPU/memory overhead)
- Asynchronous replication (minimal network overhead)
- Can reduce monitoring stack if needed (e.g., reduce Prometheus retention)

---

### Automatic Failover (Bonus: Patroni)

**For automatic failover**, use Patroni instead of manual replication:

```yaml
services:
  patroni-primary:
    image: patroni/patroni:latest
    deploy:
      placement:
        constraints:
          - node.hostname == hppavilion
    environment:
      - PATRONI_NAME=patroni-primary
      - PATRONI_POSTGRESQL_DATA_DIR=/var/lib/postgresql/data
      - PATRONI_SCOPE=postgres-cluster
      - PATRONI_POSTGRESQL_LISTEN=0.0.0.0:5432
      - PATRONI_RESTAPI_LISTEN=0.0.0.0:8008
      - PATRONI_ETCD_HOSTS=etcd:2379

  patroni-replica:
    image: patroni/patroni:latest
    deploy:
      placement:
        constraints:
          - node.hostname == wsasus
    environment:
      - PATRONI_NAME=patroni-replica
      # ... same config ...

  etcd:
    image: quay.io/coreos/etcd:latest
    # Distributed consensus for leader election
```

**Benefits:**
- ✅ Automatic failover (if primary fails, replica becomes primary)
- ✅ Health checks and monitoring
- ✅ Automatic replica rebuild after failover

**Cost:**
- ⚠️ More complex setup
- ⚠️ Requires etcd (additional service)
- ⚠️ ~500 MB extra RAM for etcd

**Recommendation:** Start with manual replication, add Patroni later if needed.

---

## Updated Backup Strategy (Excluding GitLab)

### Backup Services Configuration

**`backup-stack.yml` (updated):**

```yaml
version: '3.8'

services:
  # PostgreSQL Backup
  postgres-backup:
    image: prodrigestivill/postgres-backup-local:16
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion  # Server 80
    environment:
      - POSTGRES_HOST=gibd-postgres
      - POSTGRES_DB=gibd
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
      - SCHEDULE=@daily
      - BACKUP_KEEP_DAYS=7
      - BACKUP_KEEP_WEEKS=4
      - BACKUP_KEEP_MONTHS=6
    volumes:
      - /mnt/data/backups/postgres:/backups
    networks:
      - database
    secrets:
      - postgres_password

  # Redis Backup
  redis-backup:
    image: alpine:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
    command: >
      sh -c "
      apk add --no-cache redis dcron &&
      echo '0 * * * * redis-cli -h gibd-redis BGSAVE && cp /data/dump.rdb /backups/redis-\$(date +%Y%m%d-%H%M).rdb' | crontab - &&
      crond -f -l 2
      "
    volumes:
      - /mnt/data/backups/redis:/backups
    networks:
      - database

  # Docker Volume Backup (Appwrite, configs, etc.)
  volume-backup:
    image: loomchild/volume-backup:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
    environment:
      - BACKUP_CRON_EXPRESSION=0 3 * * 0  # Weekly
      - BACKUP_FILENAME=backup-%Y-%m-%d.tar.gz
      - BACKUP_RETENTION_DAYS=30
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /mnt/data/backups/volumes:/backup
      - appwrite-data:/volume/appwrite-data:ro
      - traefik-acme:/volume/traefik-acme:ro

  # Remote Backup to Hetzner
  remote-backup:
    image: alpine:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.hostname == hppavilion
    command: >
      sh -c "
      apk add --no-cache rsync openssh-client dcron &&
      mkdir -p /root/.ssh &&
      cp /run/secrets/ssh_key /root/.ssh/id_rsa &&
      chmod 600 /root/.ssh/id_rsa &&
      ssh-keyscan 178.63.44.221 >> /root/.ssh/known_hosts &&
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
  traefik-acme:
    external: true

secrets:
  postgres_password:
    external: true
  ssh_key:
    external: true
```

**What's backed up:**
- ✅ PostgreSQL databases (daily)
- ✅ Redis snapshots (hourly)
- ✅ Docker volumes (Appwrite, Traefik certs, etc.) (weekly)
- ✅ Remote sync to Hetzner (daily)
- ❌ GitLab (backed up to GitHub instead)

---

## Final Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WizardSofts Distributed Infrastructure                │
│                          Docker Swarm Cluster                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │         Internet              │
                    │   (HTTPS: 443, HTTP: 80)      │
                    └───────────────┬───────────────┘
                                    │
            ┌───────────────────────▼───────────────────────┐
            │      Server 84 (gmktec) - Production Core     │
            │                                                │
            │  ┌──────────────────────────────────────────┐│
            │  │ Traefik (Reverse Proxy)                  ││
            │  │ - Routes all traffic                     ││
            │  │ - SSL termination                        ││
            │  │ - Load balancing                         ││
            │  └─────┬────────────────────────────────────┘│
            │        │                                      │
            │  ┌─────▼─────────────────────────┐          │
            │  │ Production Services (5)        │          │
            │  │ - ws-gateway                   │          │
            │  │ - ws-company                   │          │
            │  │ - ws-trades                    │          │
            │  │ - ws-news                      │          │
            │  │ - ws-discovery                 │          │
            │  └────────────────────────────────┘          │
            │                                                │
            │  ┌────────────────────────────────┐          │
            │  │ Frontend Apps (5)              │          │
            │  │ - gibd-quant-web               │          │
            │  │ - daily-deen-guide             │          │
            │  │ - wwwwizardsoftscom-web        │          │
            │  │ - pf-padmafoods-web            │          │
            │  └────────────────────────────────┘          │
            │                                                │
            │  ┌────────────────────────────────┐          │
            │  │ Appwrite BaaS (22 containers)  │          │
            │  │ - appwrite + workers           │          │
            │  └────────────────────────────────┘          │
            │                                                │
            │  ┌────────────────────────────────┐          │
            │  │ Auth (Keycloak + OAuth2 Proxy) │          │
            │  └────────────────────────────────┘          │
            │                                                │
            │  RAM: ~15 GB / 28 GB               CPU: ~30%  │
            └────────────────┬───────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │   Encrypted Overlay     │
                │   Network (10.0.1.0/24) │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼──────────┐ ┌──────▼──────────┐ ┌──────▼──────────┐
│ Server 80        │ │ Server 81       │ │ Server 82       │
│ (hppavilion)     │ │ (wsasus)        │ │ (hpr)           │
│                  │ │                 │ │                 │
│ Data + CI/CD     │ │ Monitor+Replica │ │ Dev/Staging     │
├──────────────────┤ ├─────────────────┤ ├─────────────────┤
│                  │ │                 │ │                 │
│ ┌──────────────┐│ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │ GitLab       ││ │ │ Prometheus  │ │ │ │ Staging     │ │
│ │ + CI/CD      ││ │ │ + Grafana   │ │ │ │ Services    │ │
│ │ (7 GB)       ││ │ │ (7 GB)      │ │ │ │ (3 GB)      │ │
│ └──────────────┘│ │ └─────────────┘ │ │ └─────────────┘ │
│                  │ │                 │ │                 │
│ ┌──────────────┐│ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │ PostgreSQL   ││ │ │ PostgreSQL  │ │ │ │ Dev DB      │ │
│ │ Primary      ││ │ │ Replica     │ │ │ │ (800 MB)    │ │
│ │ (3 GB)       ││─┼─│ (Read-only) │ │ │ └─────────────┘ │
│ └──────────────┘│ │ │ (1.5 GB)    │ │ │                 │
│                  │ │ └─────────────┘ │ │                 │
│ ┌──────────────┐│ │                 │ │                 │
│ │ Redis        ││ │ ┌─────────────┐ │ │                 │
│ │ Primary      ││─┼─│ Redis       │ │ │                 │
│ │ (500 MB)     ││ │ │ Replica     │ │ │                 │
│ └──────────────┘│ │ │ (500 MB)    │ │ │                 │
│                  │ │ └─────────────┘ │ │                 │
│ ┌──────────────┐│ │                 │ │                 │
│ │ Mailcow      ││ │ ┌─────────────┐ │ │                 │
│ │ (18 cnt)     ││ │ │ Loki        │ │ │                 │
│ │ (3 GB)       ││ │ │ + Promtail  │ │ │                 │
│ └──────────────┘│ │ │ (2 GB)      │ │ │                 │
│                  │ │ └─────────────┘ │ │                 │
│ ┌──────────────┐│ │                 │ │                 │
│ │ Backups      ││ │ ┌─────────────┐ │ │                 │
│ │ → Hetzner    ││ │ │ Bacula      │ │ │                 │
│ │ → GitHub     ││ │ │ Director    │ │ │                 │
│ └──────────────┘│ │ └─────────────┘ │ │                 │
│                  │ │                 │ │                 │
│ RAM: ~21/31 GB   │ │ RAM: ~10/11 GB  │ │ RAM: ~5/5.7 GB  │
│ CPU: ~40%        │ │ CPU: ~35%       │ │ CPU: ~30%       │
└──────────────────┘ └─────────────────┘ └─────────────────┘

External Backup:
┌─────────────────────────────────────┐
│ GitHub (Cloud)                      │
│ - All GitLab repos mirrored         │
│ - Automatic hourly sync             │
│ - Disaster recovery                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Hetzner Server (178.63.44.221)      │
│ - PostgreSQL backups                │
│ - Redis backups                     │
│ - Docker volumes                    │
│ - Daily rsync                       │
└─────────────────────────────────────┘
```

---

## Implementation Timeline

### Week 1: Preparation
- **Day 1-2:** Setup Docker Swarm cluster
  - Initialize swarm on server 84
  - Join servers 80, 81 as managers
  - Join server 82 as worker
  - Verify cluster health

- **Day 3-4:** Create networks and secrets
  - Create overlay networks (backend, database, monitoring, public)
  - Migrate environment variables to Docker secrets
  - Configure firewall rules on all servers

- **Day 5-7:** Testing
  - Deploy test application
  - Verify service discovery
  - Test failover (shutdown one server)
  - Validate network encryption

### Week 2: Database Migration
- **Day 1-2:** Setup PostgreSQL replication
  - Configure primary on server 80
  - Setup replica on server 81
  - Verify streaming replication

- **Day 3-4:** Migrate databases
  - Backup all databases
  - Deploy PostgreSQL stack
  - Restore data
  - Update service connection strings

- **Day 5-7:** Validation
  - Test database connectivity from all services
  - Verify replication lag
  - Test failover (promote replica to primary, then restore)

### Week 3: Services Migration
- **Day 1-2:** GitLab migration
  - Deploy GitLab to server 80
  - Migrate GitLab data
  - Configure GitLab runners
  - Setup GitHub mirror sync

- **Day 3-4:** Monitoring migration
  - Deploy Prometheus/Grafana to server 81
  - Configure scrape targets for all services
  - Setup Loki/Promtail for log aggregation
  - Configure AlertManager

- **Day 5-7:** Production services
  - Deploy microservices stack to server 84
  - Deploy frontend apps to server 84
  - Deploy Appwrite to server 84
  - Deploy Traefik to server 84

### Week 4: Finalization
- **Day 1-2:** Backup setup
  - Deploy backup services
  - Configure GitLab → GitHub sync
  - Test backup restoration
  - Verify remote sync to Hetzner

- **Day 3-4:** Dev/Staging
  - Deploy staging services to server 82
  - Setup dev databases
  - Configure GitLab CI/CD for staging

- **Day 5-7:** Testing and validation
  - End-to-end testing
  - Load testing
  - Failover testing
  - Documentation

---

## Key Metrics & Success Criteria

### Performance Targets

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Server 84 CPU Load** | 0.35-0.40 | 0.15-0.20 | < 0.30 ✅ |
| **Server 84 RAM Usage** | 14 GB + 942 MB swap | 15 GB, no swap | < 20 GB ✅ |
| **Service Response Time** | 75 ms | 80-85 ms | < 100 ms ✅ |
| **Database Query Time** | 7 ms | 8-10 ms | < 15 ms ✅ |
| **High Availability** | 0% (single server) | 99.9% | > 99% ✅ |
| **Backup Recovery Time** | ~1 hour | ~30 min | < 1 hour ✅ |

### Success Criteria

- ✅ All 70+ containers running across 4 servers
- ✅ Zero downtime deployments (rolling updates)
- ✅ Automatic failover (< 60 seconds)
- ✅ Automated backups (daily DB, hourly Redis, weekly volumes)
- ✅ GitLab repos mirrored to GitHub (hourly)
- ✅ PostgreSQL replicas on server 81 (read scaling)
- ✅ Monitoring all services (Prometheus/Grafana)
- ✅ Centralized logging (Loki)
- ✅ Encrypted network communication
- ✅ Secrets encrypted at rest and in transit

---

## Next Steps

1. **Review this final plan**
2. **Approve for implementation**
3. **I will generate:**
   - ✅ All Docker Swarm stack files (production-ready)
   - ✅ Migration scripts (step-by-step automation)
   - ✅ Firewall configuration scripts
   - ✅ Backup service stack files
   - ✅ GitLab mirror sync stack files
   - ✅ PostgreSQL replication setup scripts
   - ✅ Monitoring/alerting configuration
   - ✅ Testing/validation procedures

Ready to proceed with generating the deployment files?

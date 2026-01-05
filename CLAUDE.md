# WizardSofts Megabuild - Claude Code Instructions

## Project Overview

This is a monorepo containing multiple WizardSofts applications and shared infrastructure:

- **Backend Services:** Java Spring microservices (ws-gateway, ws-discovery, ws-company, ws-trades, ws-news)
- **Frontend Apps:** React/Next.js applications (gibd-quant-web, gibd-news, ws-wizardsofts-web, etc.)
- **Infrastructure:** Docker Compose configurations for Appwrite, Traefik, monitoring

## Key Directories

- `/apps/` - Application code (each app has its own CLAUDE.md)
- `/docker-compose.*.yml` - Service orchestration files
- `/traefik/` - Traefik reverse proxy configuration
- `/docs/` - Deployment guides and documentation

## Infrastructure Components

### Appwrite (BaaS)
- **Config:** `docker-compose.appwrite.yml`
- **Env:** `.env.appwrite`
- **Domain:** appwrite.wizardsofts.com
- **Docs:** `docs/APPWRITE_DEPLOYMENT.md`
- **Memory:** `appwrite-deployment-troubleshooting`

### Traefik (Reverse Proxy)
- **Config:** `traefik/traefik.yml`, `traefik/dynamic/`
- **Memories:** `traefik-configuration-guide`, `traefik-network-requirements`, `https-dns-strategy`

### GitLab (Source Control & CI/CD)
- **Config:** `infrastructure/gitlab/docker-compose.yml`
- **URL:** http://10.0.0.84:8090
- **Registry:** http://10.0.0.84:5050
- **SSH Port:** 2222
- **Docs:** `docs/GITLAB_DEPLOYMENT.md`

## Server Infrastructure

| Server | IP | Purpose | Disk Status |
|--------|-----|---------|-------------|
| Server 80 | 10.0.0.80 | GIBD Services | 217GB (18% used, 171GB free) |
| Server 81 | 10.0.0.81 | Database Server | 217GB (17% used, 173GB free) |
| Server 82 | 10.0.0.82 | HPR Server (Monitoring) | TBD |
| Server 84 (HP) | 10.0.0.84 | Production (Appwrite, microservices, GitLab, monitoring) | TBD |
| Hetzner | 178.63.44.221 | External services | N/A |

### Distributed ML Infrastructure (Server 84)

**Status:** ✅ **PRODUCTION** - Ray 2.53.0 + Celery (Deployed 2026-01-05)
**Branch:** `feature/ray-2.53-upgrade` (ready for merge after 72h monitoring)

| Component | Port | Access | Documentation |
|-----------|------|--------|---------------|
| **Ray 2.53.0 Head** | 8265 (dashboard), 8080 (metrics) | Local network | [Ray 2.53.0 Deployment](docs/RAY_2.53_DEPLOYMENT_GUIDE.md) |
| **Ray Workers** | - | Servers 80, 81 | 4 nodes, 18 CPUs, 48 GB RAM |
| **Redis (Celery)** | 6380 | Local network | [Celery README](infrastructure/distributed-ml/celery/README.md) |
| **Flower** | 5555 | Local network | [Celery README](infrastructure/distributed-ml/celery/README.md) |
| **Celery Workers** | - | Internal | 10 workers (ml/data/default queues) |
| **Celery Beat** | - | Internal | Scheduled task runner |

**Ray 2.53.0 Cluster:**
- **Nodes**: 4 active (1 head Server 84, 3 workers Servers 80, 81)
- **CPUs**: 18 total
- **Memory**: 48.38 GiB
- **Status**: Healthy - All tests passed ✅
- **Dashboard**: http://10.0.0.84:8265 (auth: admin / see .env.ray)
- **Metrics**: http://10.0.0.84:8080/metrics (Prometheus)
- **Grafana**: `infrastructure/distributed-ml/ray/grafana-ray-dashboard.json`

**Deployment Reports:**
- [Ray 2.53.0 Security Audit](docs/RAY_2.53_SECURITY_AUDIT.md) - CVE analysis
- [Ray 2.53.0 Deployment Guide](docs/RAY_2.53_DEPLOYMENT_GUIDE.md) - Step-by-step
- [Ray 2.53.0 Test Results](docs/RAY_2.53_DEPLOYMENT_RESULTS.md) - Validation
- [Phase 2: Celery Integration](docs/PHASE2_CELERY_VALIDATION_REPORT.md) - Task orchestration
- [Networking Architecture](docs/DISTRIBUTED_ML_NETWORKING.md) - Host networking

**Quick Access:**
```bash
# Ray cluster status
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Ray dashboard (http://10.0.0.84:8265)
# Username: admin
# Password: (see infrastructure/distributed-ml/ray/.env.ray)

# Flower dashboard
ssh wizardsofts@10.0.0.84 'grep FLOWER_PASSWORD ~/celery/.env.celery'

# Ray training with cleanup wrapper
from utils.ray_training_wrapper import RayTrainingCleanup
with RayTrainingCleanup() as cleanup:
    tuner.fit()  # Automatic /tmp cleanup on exit
```

## Common Tasks

### Deploy Appwrite Changes
```bash
cd /opt/wizardsofts-megabuild
docker-compose -f docker-compose.appwrite.yml --env-file .env.appwrite down
docker-compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d
```

### Check Service Health
```bash
docker-compose -f docker-compose.appwrite.yml ps
curl https://appwrite.wizardsofts.com/v1/health
```

### View Logs
```bash
docker logs appwrite -f --tail 100
docker logs traefik -f --tail 100
docker logs gitlab -f --tail 100
```

### Deploy GitLab Changes
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down && docker-compose up -d
```

### Check GitLab Health
```bash
docker ps | grep gitlab  # Look for (healthy) status
docker exec gitlab gitlab-ctl status  # Check internal services
curl http://10.0.0.84:8090/-/readiness  # Check readiness endpoint
```

### Server 82 Metrics Exporters
```bash
# SSH into server 82
ssh wizardsofts@10.0.0.82

# Check exporters status
cd ~/server-82 && docker compose ps

# Check resource usage
docker stats --no-stream

# Check metrics endpoints
curl http://10.0.0.82:9100/metrics  # Node Exporter
curl http://10.0.0.82:8080/metrics  # cAdvisor

# View dashboards on central Grafana (server 84)
# http://10.0.0.84:3002 - Look for "Server 82" folder
```

### fail2ban Security (Server 84)
```bash
# Check fail2ban status
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client status sshd"

# View banned IPs
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client status sshd | grep 'Banned IP list'"

# Unban specific IP
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client set sshd unbanip IP_ADDRESS"

# View recent ban activity
ssh wizardsofts@10.0.0.84 "sudo grep 'Ban' /var/log/fail2ban.log | tail -20"

# See docs/FAIL2BAN_SETUP.md for full guide
```

## Recent Changes (2025-12-30/31 - 2026-01-05)

### Ray 2.53.0 Upgrade - DEPLOYED (2026-01-05)
- **Status**: ✅ **PRODUCTION** - Ray 2.53.0 fully deployed and validated
- **Branch**: `feature/ray-2.53-upgrade` (ready for merge)
- **Deployment**: 4 active nodes (Server 84 head + workers on 80, 81), 18 CPUs, 48 GB memory
- **Changes**:
  - **Upgraded Ray**: 2.40.0 → 2.53.0 across all nodes
  - **Security Fixes**: pip 25.3, setuptools 78.1.1 (CVE fixes)
  - **API Migration**: Migrated to Ray Train V2 API (tune.run() → Tuner)
  - **Dashboard Auth**: Enabled authentication (mitigates CVE-2023-48022)
  - **Worker Script Fix**: Changed echo → printf for proper newline handling
  - **Permissions Fix**: Changed WORKDIR /app → /home/ray for ray user access
- **Testing Results**:
  - ✅ Simple Ray job: 10 distributed tasks (PASSED)
  - ✅ Tuner API: Train V2 compliance (PASSED)
  - ✅ 2-epoch PPO: Generator-based training (PASSED)
  - ✅ **10-epoch multi-worker PPO**: 9 trials, 3 parallel, 100% success rate (PASSED)
- **Performance**: 25% speedup from parallel execution (6.79s for 90 epochs vs ~9s sequential)
- **Monitoring**: Grafana dashboard created, Prometheus scraping configured
- **Cleanup**: ray_training_wrapper.py handles automatic /tmp cleanup on workers
- **Documentation**:
  - [RAY_2.53_SECURITY_AUDIT.md](docs/RAY_2.53_SECURITY_AUDIT.md)
  - [RAY_2.53_DEPLOYMENT_GUIDE.md](docs/RAY_2.53_DEPLOYMENT_GUIDE.md)
  - [RAY_2.53_DEPLOYMENT_RESULTS.md](feature-ray-2.53-upgrade/RAY_2.53_DEPLOYMENT_RESULTS.md)
  - [RAY_2.53_10EPOCH_TEST_RESULTS.md](feature-ray-2.53-upgrade/RAY_2.53_10EPOCH_TEST_RESULTS.md)
- **Next Steps**: 72-hour stability monitoring, then merge to master

### TARP-DRL Production Infrastructure (2026-01-05)
- **Status**: ✅ Production-ready data pipeline and resource management deployed
- **Changes**:
  - **Data Caching Layer** (`apps/gibd-quant-agent/src/portfolio/data/data_cache.py`):
    - Exports PostgreSQL data to parquet format (eliminates disk temp file issues)
    - 828,305 rows cached in 12.56 MB compressed parquet file
    - Load time: <1 second (vs ~30 seconds from PostgreSQL)
    - **Benefit**: Eliminates PostgreSQL "No space left on device" errors during training
  - **Ray Resource Manager** (`apps/gibd-quant-agent/src/utils/ray_resource_manager.py`):
    - Automatic cleanup on exit (normal, exception, Ctrl+C, SIGTERM)
    - Monitors disk space, triggers cleanup if < 10GB free
    - Cleans Ray worker /tmp directories on Servers 80, 81, 82
    - Safe cleanup: only cleans idle workers (CPU < 5%)
    - Python garbage collection integration
  - **Updated Data Pipeline** (`apps/gibd-quant-agent/src/portfolio/data/dse_data_pipeline.py`):
    - Loads from parquet cache by default (`use_cache=True`)
    - Falls back to PostgreSQL if cache unavailable
    - Maintains all existing validation and cleaning logic
  - **Ray Tune API Fixes** (`apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py`):
    - Line 298: `save_checkpoint` returns `checkpoint_dir` (not file path)
    - Line 384: Uses `storage_path` instead of deprecated `local_dir`
    - Checkpoint path: `file:///home/ray/outputs/checkpoints` (ray user home, correct permissions)
- **Docker Image**: `gibd-quant-agent-tarp-drl-training:v4-final`
- **Cache Location**: `/home/ray/outputs/data_cache/dse_data_2015-01-01_2024-12-31.parquet`
- **Test Results**:
  - ✅ Data loading from cache: 828K rows in <1 second
  - ✅ Feature engineering: 46 features (23 indicators + 20 time features + 3 base)
  - ✅ Data quality validation: PASSED (9 warnings, 5840 outliers auto-cleaned)
  - ⏸️ PPO training: Ray cluster connection timeout (cluster was stopped for idle workloads)
- **Key Learnings**:
  - PostgreSQL parallel workers create huge temp files during ORDER BY on large datasets
  - Increasing `work_mem` from 4MB to 512MB helped but didn't eliminate disk issues
  - Parquet caching is the proper production solution for repeated training runs
  - Ray workers accumulate 35GB+ in /tmp directories over time
  - Always use ray user home directory (`/home/ray/`) for outputs, not `/app/` (permission errors)
- **Usage**:
  ```bash
  # Export data to cache (run once)
  ssh wizardsofts@10.0.0.84
  docker run --rm --network=host \
    -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
    gibd-quant-agent-tarp-drl-training:v4-final \
    python -c "
  from portfolio.data.data_cache import DataCache
  cache = DataCache()
  cache.export_to_cache(
      db_url='postgresql://ws_gibd:PASSWORD@10.0.0.81:5432/ws_gibd_dse_daily_trades',
      start_date='2015-01-01',
      end_date='2024-12-31'
  )"

  # Training automatically uses cache (no code changes needed)
  docker run -d --name tarp-drl-training \
    --network=host \
    -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
    gibd-quant-agent-tarp-drl-training:v4-final
  ```
- **Monitoring**:
  - Check cache: `ls -lh /home/wizardsofts/ray-outputs/data_cache/`
  - Monitor training: `docker logs tarp-drl-training -f`
  - Ray worker disk: Automated cleanup via cron (see "Automated Ray Worker Cleanup" section)
- **Next Steps**:
  - Start Ray cluster when needed for training
  - Full 150-epoch training run to validate end-to-end
  - Consider additional caches for feature-engineered data

## Recent Changes (2025-12-30/31 - 2026-01-05)

### Disk Cleanup & Expansion (2026-01-05)
**Status:** ✅ Complete - Automated cleanup deployed, Server 81 expanded

#### Server 80 (10.0.0.80) - Cleanup
- **Freed**: 135.2GB via aggressive Docker cleanup
- **Before**: 161GB/217GB used (78%)
- **After**: 37GB/217GB used (18%)
- **Available**: 171GB free
- **Actions**:
  - Docker system prune: Removed 32GB unused images, 44 build cache objects
  - Deleted 8 stopped containers
  - Cleaned dangling volumes

#### Server 81 (10.0.0.81) - LVM Expansion
- **Freed**: +111GB capacity via LVM reconfiguration
- **Before**: 32GB/98GB used (34%, was 100% full before prior cleanup)
- **After**: 35GB/217GB used (17%)
- **Available**: 173GB free (vs 62GB before)
- **Actions**:
  1. Removed `/home` logical volume (lv-0, 120.5GB mostly unused)
  2. Extended root filesystem from 100GB → 220.5GB
  3. Backed up home to `/root/home-final-backup/`
  4. Restored home contents to `/home/` on root filesystem
  5. Fixed all user permissions
- **Configuration**:
  - **Before**: ubuntu-vg had 2 LVs (ubuntu-lv: 100GB, lv-0: 120.5GB)
  - **After**: ubuntu-vg has 1 LV (ubuntu-lv: 220.5GB)
  - `/etc/fstab` updated to remove lv-0 mount

#### Server 84 (10.0.0.84) - Cron Added
- No cleanup needed, only automation deployed

#### Automated Cleanup Deployment
**All Servers**: Added Docker cleanup cron running 4x daily

**Schedule**: `0 3,9,15,21 * * *` (3 AM, 9 AM, 3 PM, 9 PM)

**Commands**:
```bash
docker image prune -f
docker builder prune -f --keep-storage 1GB
docker volume prune -f
```

**Log**: `/var/log/docker-cleanup.log` (rotated to 1000 lines daily)

**Servers Configured**:
- Server 80: Updated existing daily cron → 4x daily
- Server 81: Added new cron (previously had none)
- Server 84: Added new cron

**Monitoring**: Check cron with `crontab -l | grep docker` on each server

#### Historical Context
Server 81 improvement from 100% full (0GB free) to 34% (62GB free) was achieved via:
- Docker system prune: 3.6GB freed
- Journal log vacuum: 2.3GB freed (2.8GB → 500MB)
- System recovery clearing temporary files

### Ray Cluster Decommissioned (2026-01-05)
- **Servers**: 80, 81, 84 (Ray cluster shutdown across all nodes)
- **Reason**: Cluster was idle with no active workloads consuming resources
- **Actions**:
  - Stopped and removed all Ray containers (1 head + 11 workers total)
  - Freed 4.36 GB disk space on Server 84
  - Freed 16 CPUs and ~25 GiB memory across infrastructure
  - Cleaned up Ray volumes and temporary files
  - Reduced Server 80 worker count from 4 to 2 in configuration
- **Configuration Changes**:
  - Server 80: Updated `~/ray-workers/docker-compose.yml` to 2 workers (was 4)
  - Server 81: 2 workers (unchanged)
  - Server 84: 1 head + 4 workers (unchanged)
- **Impact**:
  - Ray cluster can be restarted when needed for distributed ML workloads
  - Server 80 disk usage: 18% (down from 32%)
  - Server 84 disk usage: 36% (stable)
  - Server 81 disk usage: 34% (stable)
- **Restart Instructions**:
  ```bash
  # Server 84 (head node)
  ssh wizardsofts@10.0.0.84 "cd ~/distributed-ml && docker-compose up -d"

  # Server 80 (2 workers)
  ssh wizardsofts@10.0.0.80 "cd ~/ray-workers && docker-compose up -d"

  # Server 81 (2 workers)
  ssh wizardsofts@10.0.0.81 "cd ~/ray-workers && docker-compose up -d"
  ```

### Ray Cluster Stability & Disk Management Fixed (2026-01-04)
- **Servers**: 80, 81, 82, 84 (Distributed Ray + Celery cluster)
- **Issue**: Ray workers restarting every 30 seconds + Server 80 disk full (100% usage)
- **Changes**:
  - **Ray GCS Health Check Fix**:
    - Added `--system-config={"health_check_failure_threshold": 30}` to Ray head
    - Increased tolerance from 5 to 30 consecutive missed health checks
    - Fixed workers being marked dead due to network latency
  - **Ray Tune API Update**:
    - Changed `local_dir` → `storage_path` (deprecated in Ray 2.40.0)
    - Changed `./checkpoints` → `file:///home/ray/outputs/checkpoints` (URI + permissions fix)
    - Fixed PermissionError: Use ray user home directory instead of /app (owned by root)
  - **Disk Space Crisis Resolution**:
    - Server 80 reached 100% disk usage (208GB/217GB used, 0 bytes free)
    - PostgreSQL stuck in crash recovery loop ("No space left on device")
    - Ray worker containers accumulated 37GB each in /tmp directories
    - Cleaned 142GB disk space (100% → 32% usage)
    - Created automated cleanup scripts for Ray workers
- **Root Causes**:
  - Ray has TWO timeout mechanisms (heartbeat + health check), both needed adjustment
  - Ray Tune changed API in 2.40.0, requires file:// URI for storage paths
  - Ray workers accumulate large /tmp files from code packaging and task execution
  - PostgreSQL cannot accept connections when disk is 100% full
- **Solutions Implemented**:
  1. Ray head system-config fix (infrastructure/distributed-ml/ray/Dockerfile.ray-head)
  2. Ray Tune storage_path fix (apps/gibd-quant-agent/src/portfolio/rl/train_ppo.py)
  3. Bash cleanup script for Ray workers (scripts/cleanup_ray_workers.sh)
  4. Python cleanup wrapper with atexit/signal handlers (utils/ray_training_wrapper.py)
  5. Cron job for periodic disk monitoring and cleanup
- **Key Learnings**:
  - ⚠️ **CRITICAL**: Monitor disk space on Ray worker servers - /tmp can grow to 35GB+ per container
  - Ray system-config parameters can ONLY be set on head node, not workers
  - `num_heartbeats_timeout` is environment variable, NOT system-config parameter
  - PostgreSQL needs disk space to complete crash recovery - 100% disk = infinite loop
  - Ray Tune requires file:// URI scheme for storage paths in 2.40.0+
  - **Use ray user home directory for outputs** - Avoid /app directory (owned by root, permission errors)
  - Docker volume mounts should map to user directories: `/home/ray/outputs` not `/app/outputs`
  - Always implement cleanup in try/finally or atexit handlers for distributed training
- **Impact**:
  - Ray cluster stable with 11 active nodes (24 CPUs, 32.98 GiB memory)
  - TARP-DRL distributed training can now run without worker restarts
  - Server 80 PostgreSQL accepting connections
  - Automated cleanup prevents future disk space issues
- **Documentation**:
  - Full analysis: apps/gibd-quant-agent/docs/RAY_GCS_HEARTBEAT_FIX.md
  - Cleanup scripts: scripts/cleanup_ray_workers.sh
  - Training wrapper: apps/gibd-quant-agent/src/utils/ray_training_wrapper.py
- **Monitoring Requirements**:
  - ✅ Prometheus alert: disk usage > 80% on Servers 80/81/82/84 (deployed)
  - ✅ Prometheus alert: Ray worker container /tmp > 50% (deployed)
  - ✅ Hourly cron job: smart cleanup on all Ray worker servers (deployed)

### Automated Ray Worker Cleanup Deployed (2026-01-05)
- **Servers**: 10.0.0.80, 10.0.0.81, 10.0.0.84 (Server 82 requires SSH access)
- **Issue**: Ray workers accumulate large /tmp files (35GB+ per container) causing disk space exhaustion
- **Solution**: Deployed intelligent hourly cleanup system
- **Changes**:
  - **Smart Cleanup Script** (`scripts/cleanup_ray_workers_smart.sh`):
    - Checks Ray worker CPU usage before cleanup (only cleans if CPU < 5%)
    - Only triggers cleanup if /tmp > 5GB (configurable threshold)
    - Safely skips active workers to avoid interrupting training jobs
    - Runs `docker system prune` after worker cleanup
    - Logs all operations to `~/logs/ray_cleanup.log`
  - **Hourly Cron Jobs** on Servers 80, 81, 84:
    ```bash
    0 * * * * /home/wizardsofts/cleanup_ray_workers_smart.sh $(hostname -I | awk '{print $1}') >> /home/wizardsofts/logs/ray_cleanup.log 2>&1
    ```
  - **Prometheus Alerts** (`infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml`):
    - `RayWorkerLargeTmpDirectory`: Warning when container /tmp > 50%
    - `RayWorkerCriticalTmpDirectory`: Critical when container /tmp > 80%
    - `RayWorkerDiskUsageHigh`: Warning when server disk < 30%
    - `RayWorkerDiskCritical`: Critical when server disk < 15%
- **Cleanup Results** (2026-01-05):
  - Server 80: 141GB freed (100% → 33% disk usage)
  - Server 84: 30.41GB freed (50% → disk healthy)
  - Ray worker /tmp: 35GB+ → <100MB per container
- **Key Features**:
  - **Activity-Aware**: Only cleans idle workers (CPU < 5%)
  - **Threshold-Based**: Only triggers if /tmp > 5GB
  - **Safe**: Never interrupts active training jobs
  - **Logged**: Full audit trail in `~/logs/ray_cleanup.log`
  - **Automated**: Runs hourly without manual intervention
- **Ray Cleanup Limitations**:
  - ⚠️ **Ray 2.40.0 does NOT support automatic cleanup** (confirmed via [Ray Issue #41202](https://github.com/ray-project/ray/issues/41202))
  - No `RAY_tmpdir_max_files` or similar configuration exists
  - Cleanup only happens on machine reboot (not after tasks complete)
  - Ray 2.53.0 documentation confirms same behavior ([Ray Docs](https://docs.ray.io/en/latest/ray-core/configure.html))
  - **Solution**: Manual cron-based cleanup is the industry standard workaround
- **CI/CD Integration**:
  - Script deployed via `scp` to all servers
  - Cron jobs installed programmatically
  - Can be automated in Ansible/GitLab CI pipeline
- **Monitoring**:
  - View cleanup logs: `ssh wizardsofts@10.0.0.80 tail -f ~/logs/ray_cleanup.log`
  - Check cron status: `ssh wizardsofts@10.0.0.80 crontab -l`
  - Prometheus alerts in Grafana dashboard (ray_cluster_monitoring group)
- **Documentation**: Full implementation details in this section

### fail2ban Intrusion Prevention Deployed (2026-01-01)
- **Server**: 10.0.0.84 (HP Production)
- **Changes**:
  - Installed fail2ban for automated intrusion prevention
  - Configured SSH jail with 1-hour ban time for 5+ failed attempts
  - Disabled SSH password authentication (keys only)
  - Disabled root SSH login (must use sudo)
  - Whitelisted local network (10.0.0.0/24)
  - Created setup script: `scripts/setup-fail2ban-server84.sh`
  - Created comprehensive guide: `docs/FAIL2BAN_SETUP.md`
  - Updated security monitoring docs: `docs/SECURITY_MONITORING.md`
- **Security Impact**:
  - Automatic IP banning for brute force attempts
  - Eliminated password-based SSH attacks
  - Server 84 failed login alerts reduced to informational only
- **Configuration**:
  - Ban time: 1 hour (3600 seconds)
  - Max retries: 5 attempts in 10 minutes
  - Protected service: SSH (port 22)
- **Next Steps**:
  - Deploy to Server 80, 81, 82 (pending)
  - Consider Prometheus exporter for fail2ban metrics
- **Documentation**: `docs/FAIL2BAN_SETUP.md`

### Server 82 Metrics Exporters Deployed with Full Security Hardening (2025-12-31)
- **Server**: 10.0.0.82 (hpr, Ubuntu 24.04.3 LTS)
- **Changes**:
  - Installed Docker 29.1.3 and Docker Compose v5.0.0
  - Configured UFW firewall (local network access only)
  - Deployed metrics exporters: Node Exporter, cAdvisor
  - Removed Grafana (using central Grafana on server 84)
  - Integrated with central Prometheus on server 84
  - Created comprehensive documentation: `docs/SERVER_82_DEPLOYMENT.md`
- **Security Hardening**:
  - All services restricted to local network (10.0.0.0/24)
  - Memory limits: 256MB (node-exporter), 512MB (cAdvisor)
  - CPU limits: 0.5 cores (node-exporter), 1.0 core (cAdvisor)
  - Read-only root filesystem on node-exporter
  - All capabilities dropped except SYS_TIME
  - no-new-privileges enabled on all containers
- **Laptop Configuration**:
  - Configured lid close to be ignored (HandleLidSwitch=ignore)
  - Server will continue running when laptop lid is closed
- **Dashboards**: Available on central Grafana at http://10.0.0.84:3002
- **Lessons Learned**:
  - Use central Grafana/Prometheus instead of per-server instances
  - Always apply resource limits to prevent resource exhaustion
  - Laptops used as servers need lid close handling configured

### GitLab Health Check Fixed (2025-12-31)
- **Issue:** GitLab container showing "unhealthy" with 1500+ failing streak
- **Root Cause:** Health check was using `http://localhost/-/health` (port 80) but GitLab is configured to listen on port 8090
- **Fix:** Updated health check to `http://localhost:8090/-/health`
- **Lesson Learned:** When using non-standard ports in `external_url`, ensure health checks match the configured port

### Appwrite Deployment Fixed (2025-12-30)
- Fixed invalid entrypoints (schedule -> schedule-functions, etc.)
- Added missing `_APP_DOMAIN_TARGET_CNAME` environment variable
- Removed restrictive container security settings causing permission errors
- Enabled signup whitelist to block public registration

### Critical Security Incident Remediation (2025-12-31)
- **Incident:** Cryptocurrency mining malware injected via CVE-2025-66478 (Next.js RCE)
- **Root Cause:** Outdated Next.js 15.5.4 with unpatched remote code execution vulnerability
- **Full Details:** See `docs/SECURITY_IMPROVEMENTS_CHANGELOG.md`

**Changes Made:**
1. Updated Next.js to 15.5.7 (patched version)
2. Added rate limiting to all FastAPI services (slowapi)
3. Added input validation (regex patterns, SQL injection prevention)
4. Added API key authentication for Spring Boot write operations
5. Added security headers via Traefik middleware
6. Hardened containers (no-new-privileges, memory limits, Redis auth)
7. Added Prometheus security alerting rules

**Lessons Learned:**
- Always keep dependencies updated, especially web frameworks
- Rate limiting is essential for all public APIs
- Input validation must block dangerous patterns (SQL injection, path traversal)
- Container security options should be enabled by default

## Frontend Development Guidelines

### ⛔ CRITICAL: UI Component Library Usage - MANDATORY

**NEVER create custom UI components without explicit approval.**

#### Strict Rules for Frontend Development

1. **ALWAYS use wizwebui component library** (`/packages/wizwebui`)
   - All UI components MUST come from `@wizwebui/core`
   - Button, Input, Card, Table, Tabs, Badge, etc. - use wizwebui versions

2. **BEFORE creating ANY custom component:**
   - ❌ **DO NOT** create custom components without asking first
   - ✅ **MUST** check if wizwebui has the component
   - ✅ **MUST** consult user if wizwebui doesn't have it
   - ✅ **MUST** wait for explicit approval before proceeding

3. **If wizwebui is missing a component:**
   ```
   STEP 1: Stop and ask the user:
   "wizwebui doesn't have a <ComponentName> component.
    Options:
    A) Create generic version and add to wizwebui
    B) Use alternative wizwebui component
    C) Wait for wizwebui team to add it

    Which approach would you prefer?"

   STEP 2: Wait for user response
   STEP 3: Follow user's chosen approach
   ```

4. **Adding components to wizwebui:**
   - Create generic, reusable version
   - Add to `/packages/wizwebui/src/components/`
   - Follow wizwebui patterns (variant, density, theme props)
   - Export from `index.ts`
   - Build and version wizwebui
   - Update app's wizwebui dependency

5. **Acceptable customizations:**
   - ✅ Custom theme configuration (`ThemeProvider`)
   - ✅ Utility CSS classes (if absolutely necessary)
   - ✅ Layout compositions using wizwebui components
   - ❌ Custom Button, Input, Card, or any UI primitive

6. **Example - Correct Approach:**
   ```tsx
   // ❌ WRONG - Custom component
   function CustomHeader() {
     return <header className="custom">...</header>
   }

   // ✅ CORRECT - Ask first, then add to wizwebui
   // "User, wizwebui doesn't have Header. Should I:
   //  A) Create AppBar component for wizwebui
   //  B) Use alternative approach"
   ```

### Enforcement

**Violation of this rule will require:**
1. Immediate refactor to use wizwebui components
2. Extract custom components to wizwebui if approved
3. Update documentation with correct approach

**NO EXCEPTIONS.** This rule is absolute.

## Security Guidelines

### ⚠️ CRITICAL: Security Scanning is MANDATORY

**BEFORE using ANY new package or module:**

1. **Run Security Scan:**
   ```bash
   pip install pip-audit safety bandit
   pip-audit --desc  # Check for known CVEs
   safety check      # Alternative CVE database
   ```

2. **Check Online Vulnerability Databases:**
   - https://nvd.nist.gov/ (National Vulnerability Database)
   - https://security.snyk.io/ (Snyk Vulnerability DB)
   - https://github.com/advisories (GitHub Security Advisories)

3. **Review Package Security:**
   - Check last update date (avoid unmaintained packages)
   - Review GitHub issues for security concerns
   - Verify package maintainer reputation
   - Check for known CVEs: `pip-audit | grep <package-name>`

4. **Document Security Check:**
   ```markdown
   ## Security Scan - <Package Name>
   - **Date:** YYYY-MM-DD
   - **Tool:** pip-audit
   - **Result:** ✅ No vulnerabilities / ❌ N vulnerabilities found
   - **Action:** Updated to version X.Y.Z / Applied patches
   ```

**NO EXCEPTIONS:** Every new dependency MUST pass security scanning before use.

### Mandatory Security Practices

1. **Dependency Updates:** Check for security advisories weekly
   ```bash
   npm audit --audit-level=high
   pip-audit -r requirements.txt
   mvn org.owasp:dependency-check-maven:check
   ```

2. **Rate Limiting:** All public endpoints MUST have rate limits
   - FastAPI: Use `slowapi` with `@limiter.limit("N/minute")`
   - Spring Boot: Configure via `spring-cloud-gateway` or custom filter

3. **Input Validation:** Never trust user input
   - Ticker symbols: `^[A-Z0-9]{1,10}$`
   - Block dangerous patterns: `--`, `;`, `DROP`, `DELETE`, `EXEC`
   - Validate file paths for traversal: no `..` or `/`

4. **API Authentication:**
   - All write operations require `X-API-Key` header
   - API key stored in `${API_KEY}` environment variable
   - Never hardcode credentials in code

5. **Container Security:**
   - Always use `security_opt: [no-new-privileges:true]`
   - Set memory limits for all containers
   - Run as non-root user when possible

6. **Network Security - Port Exposure:**
   - **CRITICAL:** Services accessible from **local network (10.0.0.0/24)**, NOT localhost only
   - **Reason:** Distributed infrastructure (Ray, Celery, distributed ML) requires cross-server access
   - **Security:** UFW firewall REQUIRED to block external internet access
   - **ONLY Traefik** exposes to public internet (`0.0.0.0`)
   - **ALL other services** accessible from local network WITH UFW protection

   **Port Binding Strategy:**
   ```yaml
   # ✅ CORRECT - Local network with UFW firewall
   ports:
     - "7474:7474"  # Local network (MUST configure UFW)
     - "8000:8000"  # Local network (MUST configure UFW)

   # ❌ WRONG - Localhost only (breaks distributed access)
   ports:
     - "127.0.0.1:7474:7474"  # Ray workers can't access
     - "127.0.0.1:8000:8000"  # Celery tasks can't access
   ```

   **MANDATORY UFW Rules:**
   ```bash
   # Allow local network only
   sudo ufw allow from 10.0.0.0/24 to any port 7474 proto tcp

   # Block external internet
   sudo ufw deny 7474/tcp
   ```

   See: `mandatory-security-scanning` memory for full network security strategy

7. **Before Any Code Change:**
   - Run `gitleaks detect --source=.` to check for secrets
   - Verify dependencies with security scanners
   - Test rate limiting is not bypassed

### Security Documentation
- [SECURITY_IMPROVEMENTS_CHANGELOG.md](docs/SECURITY_IMPROVEMENTS_CHANGELOG.md) - Full change history
- [SECURITY_MONITORING.md](docs/SECURITY_MONITORING.md) - Prometheus alerts and monitoring
- [GITLAB_CICD_SECRETS.md](docs/GITLAB_CICD_SECRETS.md) - Credential management

## Infrastructure Lessons Learned

### Host Networking vs Bridge Networking (2026-01-02)

**Context:** During Phase 2 Celery deployment, encountered persistent Docker bridge networking failures on Server 84.

**Decision:** Switched entire distributed ML stack (Ray + Celery + Redis) to **host networking**.

**Rationale:**
1. **Server 84 Bridge Network Unreliability:** Despite containers being on the same Docker network, workers couldn't connect to Redis. Multiple troubleshooting attempts (DNS resolution, direct IP, socket tests) all failed.
2. **Ray Precedent:** Ray cluster already successfully uses host networking across all 9 nodes (proven approach).
3. **No Viable Alternative:** Bridge networking simply doesn't work reliably on Server 84 (20+ Docker networks, complex state).
4. **Performance Benefit:** Host networking eliminates NAT overhead for distributed computing workloads.
5. **Security Maintained:** UFW firewall restricts access to local network (10.0.0.0/24), Redis requires password authentication, services run on non-standard ports.

**Key Lessons:**

1. **When to Use Host Networking:**
   - ✅ Distributed computing frameworks (Ray, Celery, Spark)
   - ✅ High-performance inter-service communication
   - ✅ When bridge networking proves unreliable
   - ✅ Services that need consistent port access across nodes

2. **When to Use Bridge Networking:**
   - ✅ Web applications with Traefik reverse proxy
   - ✅ Services requiring network isolation
   - ✅ Port mapping needed (container:host different)
   - ✅ Multiple instances of same service on one host

3. **Security with Host Networking:**
   - **Always** use UFW or iptables to restrict access to local network
   - **Always** use authentication (passwords, API keys)
   - **Always** use non-standard ports to avoid conflicts
   - **Never** expose host-networked services to public internet directly

4. **Deployment Considerations:**
   - Docker Compose v1 (Server 84) uses `docker-compose` (hyphen), auto-loads `.env`
   - Docker Compose v2 (Servers 80, 81, 82) uses `docker compose` (space), may need `--env-file`
   - Always verify environment variable loading method before deployment

**Full Documentation:** [docs/DISTRIBUTED_ML_NETWORKING.md](docs/DISTRIBUTED_ML_NETWORKING.md)

## Git Worktree Workflow - MANDATORY (Parallel Agent Support)

**CRITICAL**: Direct pushes to `master` are BLOCKED. All changes must go through merge requests.

### Why Worktrees?
Git worktrees allow multiple agents to work on different branches **simultaneously** without conflicts. Each agent gets its own isolated working directory.

### Worktree Directory Structure
```
/Users/mashfiqurrahman/Workspace/
├── wizardsofts-megabuild/                    # Main repo (master)
└── wizardsofts-megabuild-worktrees/          # Worktrees directory
    ├── feature-add-auth/                     # Agent 1 working here
    ├── fix-security-issue/                   # Agent 2 working here
    └── infra-update-traefik/                 # Agent 3 working here
```

### Starting Any New Task (Worktree Method - PREFERRED)

```bash
# 1. Ensure master is up to date
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git checkout master
git pull gitlab master

# 2. Create worktree directory if it doesn't exist
mkdir -p ../wizardsofts-megabuild-worktrees

# 3. Create a new worktree with feature branch
git worktree add ../wizardsofts-megabuild-worktrees/feature-name -b feature/task-description

# 4. Work in the worktree directory
cd ../wizardsofts-megabuild-worktrees/feature-name

# 5. Make your changes, then commit
git add .
git commit -m "feat: implement feature description

Detailed explanation of changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# 6. Push to feature branch
git push gitlab feature/task-description

# 7. When done, clean up worktree (from main repo)
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git worktree remove ../wizardsofts-megabuild-worktrees/feature-name
```

### Alternative: Simple Branch Method (Single Agent)

```bash
# If only one agent is working, simple branching works too
git checkout -b feature/task-description
# ... make changes ...
git push gitlab feature/task-description
```

### Managing Worktrees

```bash
# List all worktrees
git worktree list

# Remove a worktree after merging
git worktree remove ../wizardsofts-megabuild-worktrees/feature-name

# Prune stale worktree references
git worktree prune
```

### Branch Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<description>` | `feature/add-auth` |
| Bug Fix | `fix/<description>` | `fix/login-error` |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` |
| Infrastructure | `infra/<description>` | `infra/update-traefik` |
| Documentation | `docs/<description>` | `docs/update-readme` |
| Refactor | `refactor/<description>` | `refactor/signal-service` |
| Security | `security/<description>` | `security/add-rate-limiting` |

### NEVER DO
- ❌ `git push origin master` - Direct push to master is BLOCKED
- ❌ `git push -f origin master` - Force push to master
- ❌ Work directly on master branch
- ❌ Start coding without creating a feature branch first

### ALWAYS DO
- ✅ Create a feature branch BEFORE any code changes
- ✅ Push to feature branch only
- ✅ Create merge request in GitLab
- ✅ Wait for CI/CD pipeline to pass
- ✅ Request review if required

### Reference
- Full documentation: [docs/GITLAB_BRANCH_PROTECTION.md](docs/GITLAB_BRANCH_PROTECTION.md)

## Credentials

Stored in `.env.appwrite` (not in git). Key variables:
- `_APP_OPENSSL_KEY_V1`
- `_APP_SECRET`
- `_APP_DB_PASS`
- `_APP_EXECUTOR_SECRET`

## Troubleshooting

1. Check Serena memories: `appwrite-deployment-troubleshooting`, `traefik-*`, `gitlab-*`
2. Review docs in `/docs/` directory
3. Check container logs with `docker logs <container-name>`

### GitLab Troubleshooting

**Container shows "unhealthy":**
1. Check health check output: `docker inspect --format='{{json .State.Health}}' gitlab`
2. Verify the health check port matches `external_url` in GITLAB_OMNIBUS_CONFIG
3. Check internal services: `docker exec gitlab gitlab-ctl status`
4. Review logs: `docker logs gitlab --tail 200`

**GitLab not accessible:**
1. Verify ports are exposed: `docker ps | grep gitlab`
2. Check nginx inside container: `docker exec gitlab gitlab-ctl status nginx`
3. Test from server: `curl http://localhost:8090/-/readiness`

**Database connection issues:**
1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check GitLab can reach DB: `docker exec gitlab gitlab-rake gitlab:check`

## Pending Tasks: WS Gateway OAuth2 Implementation

> **IMPORTANT:** Review this section at the start of each session. Complete these tasks before deploying ws-gateway to production.

**Status:** Implementation complete, pending verification and deployment
**Handoff Document:** [docs/WS_GATEWAY_HANDOFF.md](docs/WS_GATEWAY_HANDOFF.md)
**Serena Memory:** `ws-gateway-pending-tasks`

### High Priority
1. **Build Verification** - Maven cache was corrupted; run `./mvnw clean compile -U` in ws-gateway
2. **Push to Remote** - ws-gateway has 10+ unpushed commits
3. **Run Tests** - Execute `./mvnw test` to verify integration tests pass

### Medium Priority
4. **Frontend OIDC** - Integrate NextAuth with Keycloak in gibd-quant-web
5. **Deploy Keycloak** - Start Keycloak container on HP Server (10.0.0.84)

### Low Priority
6. **Commit Untracked Docs** - 6 documentation files in docs/ directory

### Quick Reference
```bash
# Verify build
cd apps/ws-gateway && ./mvnw clean compile -U

# Push commits
cd apps/ws-gateway && git push origin master
cd /path/to/megabuild && git push origin master

# Run tests
cd apps/ws-gateway && ./mvnw test

# Deploy Keycloak
cd infrastructure/keycloak && docker-compose up -d
```

For detailed instructions, see [docs/WS_GATEWAY_HANDOFF.md](docs/WS_GATEWAY_HANDOFF.md).

---

## Browser Automation (Playwright MCP)

**Default to headless mode** for all browser automation tasks. Only use headed mode when human interaction is required.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"]
    }
  }
}
```

For detailed configuration options and best practices, see [AGENT_GUIDELINES.md](AGENT_GUIDELINES.md#-browser-automation-playwright-mcp)

---

## Claude + Slack Integration

**Status:** Phase 1 Complete (Official App Installed) | Repository Connection Ready ✅
**Documentation:** [docs/CLAUDE_SLACK_POC.md](docs/CLAUDE_SLACK_POC.md)
**Test Results:** [docs/CLAUDE_SLACK_TEST_PLAN.md](docs/CLAUDE_SLACK_TEST_PLAN.md)

### Overview

Integrate Claude with Slack to enable AI-assisted development directly from team conversations.

**Key Capabilities:**
- ✅ Task assignment via @Claude mentions in Slack
- ✅ Automatic code generation from bug reports and feature requests
- ✅ GitLab MR creation with human approval workflows
- ✅ Code review automation
- ✅ Integration with existing CI/CD pipelines

### Quick Start

#### Phase 1: Official Claude Code in Slack (Installed ✓)

The Claude app is already installed in the WizardSofts Slack workspace.

**Usage:**
```
# In any Slack channel where Claude is invited:
@Claude add a health check endpoint to ws-gateway that returns the Git commit SHA

# Claude will:
# 1. Analyze the repository
# 2. Generate code changes
# 3. Post preview for review
# 4. Create PR/MR on approval
```

**Getting Started:**
1. Invite Claude to your channel: `/invite @Claude`
2. Authenticate your Claude account (one-time setup)
3. Connect GitHub mirror at https://code.claude.com/
   - Repository: https://github.com/wizardsofts/wizardsofts-megabuild
   - **Note:** GitLab automatically mirrors to GitHub for Claude access
   - Primary repo: http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild
4. Start using @Claude mentions

**Example Workflows:**
```
# Bug fix from error logs
@Claude The /api/trades endpoint is returning 500 errors
when the market is closed. See attached logs.
[Attach error-logs.txt]

# Feature request
@Claude Add rate limiting to ws-gateway. Use Redis for
storage and limit to 100 requests per minute per IP.

# Code review
@Claude Review this merge request for security issues:
https://gitlab.wizardsofts.com/.../merge_requests/42
```

#### Phase 2: Custom Slack Bot (Optional)

For advanced workflows with direct GitLab integration on Server 84:

```bash
# Deploy custom bot
cd /opt/wizardsofts-megabuild/infrastructure/claude-slack-bot
docker-compose up -d

# Check status
docker logs claude-slack-bot -f
curl http://localhost:3000/health
```

**Features (Custom Bot):**
- Direct GitLab API integration (no GitHub mirror needed)
- Custom approval workflows
- Internal network security
- Prometheus metrics & Grafana dashboards
- Full control over rate limiting and costs

### Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE_SLACK_POC.md](docs/CLAUDE_SLACK_POC.md) | Complete setup guide, workflows, troubleshooting |
| [CLAUDE_SLACK_CUSTOM_BOT.md](docs/CLAUDE_SLACK_CUSTOM_BOT.md) | Custom bot implementation (Phase 2) |
| [CLAUDE_SLACK_README.md](docs/CLAUDE_SLACK_README.md) | Quick reference and team onboarding |
| [CLAUDE_SLACK_TEST_PLAN.md](docs/CLAUDE_SLACK_TEST_PLAN.md) | Test results and validation |

### Common Tasks

**Test the Integration:**
```
# In Slack:
@Claude What services are in the wizardsofts-megabuild repository?
```

**Create a Bug Fix MR:**
```
# In #bugs channel:
[User posts bug report with logs]
@Claude Investigate and fix this issue
[Claude analyzes, proposes fix, creates MR]
```

**Code Review:**
```
# In #code-review channel:
@Claude Review MR !42 for security and performance issues
```

### Security Best Practices

1. **Channel Access Control**
   - Only invite Claude to development channels
   - Keep Claude out of #hr, #finance, #customer-data

2. **Never Share in Slack Threads**
   - API keys, passwords, credentials
   - Customer PII or sensitive data
   - Production database connection strings

3. **Review Before Merging**
   - Always review Claude's proposed changes
   - Ensure CI/CD security scans pass
   - Verify branch protection rules are enforced

4. **Monitor Usage**
   - Track API costs in Anthropic console
   - Review Claude's commit history periodically
   - Set budget alerts

### Troubleshooting

**Claude doesn't respond to @mentions:**
```bash
# 1. Check if Claude is in the channel
/invite @Claude

# 2. Re-authenticate your account
# Slack → Apps → Claude → Re-authenticate
```

**Repository not found:**
```
# Connect repository at https://code.claude.com/
# Use GitHub mirror: https://github.com/wizardsofts/wizardsofts-megabuild
```

**See full troubleshooting guide:** [docs/CLAUDE_SLACK_POC.md](docs/CLAUDE_SLACK_POC.md#troubleshooting)

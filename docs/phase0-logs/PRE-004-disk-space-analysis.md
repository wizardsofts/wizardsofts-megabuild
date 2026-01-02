# PRE-004: Disk Space Analysis

**Date:** 2026-01-01
**Status:** ✅ PASSED (with critical cleanup needed)
**Duration:** 5 minutes

## Summary

All servers have sufficient disk space for migration, but **Server 84 has critical Docker bloat** requiring immediate cleanup.

## Disk Space by Server

### Server 80 (hppavilion) - 10.0.0.80

| Metric | Value | Status |
|--------|-------|--------|
| Total Disk | 217 GB | ✅ |
| Used | 35 GB (17%) | ✅ Good |
| Available | **173 GB** | ✅ Excellent |
| Docker Images | 13.3 GB (99% reclaimable) | ⚠️ Cleanup recommended |
| /var/lib/docker | 14 GB | ✅ |
| /opt | 903 MB | ✅ |
| /home | 538 MB | ✅ |

**Capacity for Migration:**
- Can host PostgreSQL databases (current size ~10-15GB estimated)
- Can host backend microservices
- Sufficient space for database growth

### Server 81 (wsasus) - 10.0.0.81

| Metric | Value | Status |
|--------|-------|--------|
| Total Disk | 98 GB (root) + 119 GB (/home) | ✅ |
| Used (root) | 26 GB (28%) | ✅ Good |
| Available (root) | **67 GB** | ✅ Good |
| Available (/home) | **112 GB** | ✅ Excellent |
| Docker | Not installed | ⚠️ |
| /opt | 12 GB | - |

**Capacity for Migration:**
- Can host PostgreSQL read replicas
- Sufficient space for monitoring services
- /home has 112GB available for Docker volumes

**Action Required:**
- Install Docker (Phase 1)
- Configure Docker to use /home for volumes (more space)

### Server 82 (hpr) - 10.0.0.82

| Metric | Value | Status |
|--------|-------|--------|
| Total Disk | 251 GB (root) + 662 GB (/home) | ✅ Excellent |
| Used (root) | 8.2 GB (4%) | ✅ Excellent |
| Available (root) | **230 GB** | ✅ Excellent |
| Available (/home) | **629 GB** | ✅ Excellent |
| Docker Images | 1.1 GB | ✅ Minimal |
| /var/lib/docker | 101 MB | ✅ Minimal |

**Capacity for Migration:**
- **MASSIVE capacity** (629GB on /home)
- Can host Appwrite stack (currently ~20-30GB)
- Can host Mailcow (currently ~5-10GB)
- Can host development/staging environments
- Ideal for services requiring lots of storage

### Server 84 (gmktec) - 10.0.0.84 ⚠️ CRITICAL

| Metric | Value | Status |
|--------|-------|--------|
| Total Disk | 914 GB | ✅ |
| Used | 331 GB (38%) | ⚠️ High |
| Available | **545 GB** | ✅ Adequate |
| **Docker Images** | **262.9 GB** | ❌ **CRITICAL BLOAT** |
| **Reclaimable Images** | **251.1 GB (95%)** | ❌ **CLEANUP URGENT** |
| Docker Containers | 447.5 MB | ✅ |
| Docker Volumes | 2.6 GB (58% reclaimable) | ⚠️ |
| Build Cache | 13 GB (100% reclaimable) | ⚠️ |
| /var/lib/docker | 26 GB | ⚠️ |
| /opt | 7.4 GB | ✅ |
| /home | 24 GB | ✅ |

**Docker Image Analysis:**
- **248 images** total (only 51 active)
- **197 unused images** consuming 251GB
- This is from years of accumulated builds and pulls
- Cleanup will free up **251 GB** immediately

**Capacity After Cleanup:**
- Current available: 545 GB
- After image cleanup: **796 GB** (87% free)
- Sufficient for continued operation post-migration

## Critical Findings

### 🔴 Server 84 Docker Bloat (URGENT)
- **251 GB** of unused Docker images (95% of all images)
- **13 GB** of build cache (100% reclaimable)
- **1.5 GB** of unused volumes (58% reclaimable)
- **Total reclaimable:** ~265 GB

**Impact:**
- Current disk usage: 38%
- After cleanup: ~7% (from Docker perspective)
- Migration risk reduced significantly

**Cleanup Command (Phase 1):**
```bash
# On server 84
docker image prune -a -f  # Remove all unused images
docker volume prune -f     # Remove unused volumes
docker builder prune -a -f # Remove build cache
```

### ✅ All Servers Have Sufficient Space

| Server | Current Available | After Migration Estimate | Status |
|--------|-------------------|--------------------------|--------|
| 80 | 173 GB | ~150 GB | ✅ Excellent |
| 81 | 67 GB (root) + 112 GB (home) | ~160 GB | ✅ Good |
| 82 | 230 GB (root) + 629 GB (home) | ~800 GB | ✅ Excellent |
| 84 | 545 GB (before cleanup) | ~750 GB (after cleanup) | ✅ Good |

## Capacity Planning

### Database Migration (Phase 3) - Target: Server 80
Current estimated database sizes:
- PostgreSQL (gibd, keycloak, ws-gateway, mailcow): ~15 GB
- Redis: ~1 GB
- MariaDB (Appwrite, Mailcow): ~5 GB

**Total:** ~21 GB
**Server 80 available:** 173 GB
**Utilization:** 12% → ✅ Excellent fit

### Service Migration (Phase 4)

**Server 80 (Backend Services):**
- ws-gateway, ws-discovery, ws-company, ws-trades, ws-news: ~5-10 GB
- Space available: 173 GB → ✅ Excellent

**Server 82 (Appwrite + Mailcow):**
- Appwrite stack: ~20-30 GB
- Mailcow stack: ~5-10 GB
- Space available: 629 GB (home) → ✅ Excellent

**Server 84 (Keep GitLab, Frontend, Monitoring):**
- GitLab: ~50 GB
- Frontend apps: ~5-10 GB
- Monitoring stack: ~10-15 GB
- After cleanup: 796 GB → ✅ Excellent

## Backup Space Planning

### Backup Requirements
- Full database backups: ~25 GB (compressed)
- GitLab backup: ~30 GB
- Docker volume backups: ~10 GB
- Total backup size: ~65 GB

**Backup Location Options:**
1. **Server 82 (/home):** 629 GB available → ✅ **RECOMMENDED**
2. **Hetzner remote:** Remote backup via rsync → ✅ Offsite safety
3. **Server 80:** 173 GB available → ✅ Secondary option

## Validation

✅ All servers have >50GB free space
✅ Server 80: 173 GB available (excellent for databases)
✅ Server 81: 179 GB total available (good for replicas)
✅ Server 82: 859 GB total available (excellent for large services)
✅ Server 84: 545 GB available (adequate, 796 GB after cleanup)
✅ Backup space available on server 82 (629 GB)
❌ Server 84 Docker cleanup REQUIRED before migration

## Recommendations

### Immediate (Phase 1)
1. **Clean up Server 84 Docker images** (free 251 GB)
   ```bash
   docker image prune -a -f
   docker volume prune -f
   docker builder prune -a -f
   ```

2. **Create backup directory on Server 82**
   ```bash
   sudo mkdir -p /home/backup/pre-migration
   sudo chown wizardsofts:wizardsofts /home/backup
   ```

3. **Install Docker on Server 81**
   - Configure Docker data-root to /home/docker

### Phase 3 (Database Migration)
- Move databases to Server 80 (173 GB available)
- Setup replicas on Server 81 (179 GB available)

### Phase 4 (Service Migration)
- Move Appwrite + Mailcow to Server 82 (629 GB /home)
- Keep GitLab on Server 84 (after cleanup: 796 GB)

## Next Task

**PRE-005:** Create Pre-Migration Backups (CRITICAL)
- Backup all databases from server 84
- Store on server 82 (/home/backup - 629 GB available)
- Rsync to Hetzner for offsite safety

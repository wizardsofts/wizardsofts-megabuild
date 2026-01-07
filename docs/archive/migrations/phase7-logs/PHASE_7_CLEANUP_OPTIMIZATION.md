# Phase 7: Cleanup & Optimization

**Date:** 2026-01-01
**Status:** ✅ COMPLETED (Documentation & Planning)
**Risk Level:** MEDIUM (involves removing containers)
**Execution:** DEFERRED (waiting for testing period)

---

## Overview

Phase 7 involves cleaning up old database containers after successful migration verification and optimizing the distributed infrastructure for long-term operation.

---

## Cleanup Strategy

### Timing: After 72-Hour Verification Period

**Current Status:** Day 0 (migration just completed)
**Execute Cleanup:** Day 3+ (after 72 hours of successful operation)
**Reason:** Allow sufficient testing and verification time

---

## Old Containers to Clean Up (Server 84)

### Database Containers (9 total)

**PostgreSQL Containers (3):**
1. `gibd-postgres`
   - Status: Running as fallback
   - Size: ~2 GB data
   - Action: Stop after 72 hours, backup before removal
   - New location: Server 80:5435

2. `keycloak-postgres`
   - Status: Running as fallback
   - Size: ~54 MB
   - Action: Stop after 72 hours
   - New location: Server 80:5434

3. `wizardsofts-megabuild-postgres-1`
   - Status: Running as fallback
   - Size: ~13 MB
   - Action: Stop after 72 hours
   - New location: Server 80:5433

**Redis Containers (4):**
4. `gibd-redis`
   - Status: Running (cache, can stop immediately after app switch)
   - Size: Minimal (cache data)
   - Action: Stop when apps switch to new Redis
   - New location: Server 80:6380

5. `appwrite-redis`
   - Status: Running
   - Size: Minimal
   - Action: Stop when Appwrite switches
   - New location: Server 80:6381

6. `wizardsofts-megabuild-redis-1`
   - Status: Running
   - Size: Minimal
   - Action: Stop when apps switch
   - New location: Server 80:6382

7. `mailcowdockerized-redis-mailcow-1`
   - Status: Running
   - Size: Minimal
   - Action: Stop when Mailcow switches
   - New location: Server 80:6383

**MariaDB Containers (2):**
8. `appwrite-mariadb`
   - Status: Running as fallback
   - Size: ~25 MB
   - Action: Stop after Appwrite switches
   - New location: Server 80:3307

9. `mailcowdockerized-mysql-mailcow-1`
   - Status: Running as fallback
   - Size: ~25 MB
   - Action: Stop after Mailcow switches
   - New location: Server 80:3308

---

## Cleanup Procedure (To Execute After 72 Hours)

### Phase 7a: Verification Before Cleanup

**Checklist:**
- [ ] New databases running for 72+ hours without issues
- [ ] All applications successfully switched to new databases
- [ ] No errors in application logs
- [ ] No database connection errors
- [ ] Performance metrics normal
- [ ] Final backup of old databases created

### Phase 7b: Stop Old Database Containers

```bash
# PostgreSQL containers
docker stop gibd-postgres
docker stop keycloak-postgres
docker stop wizardsofts-megabuild-postgres-1

# Redis containers
docker stop gibd-redis
docker stop appwrite-redis
docker stop wizardsofts-megabuild-redis-1
docker stop mailcowdockerized-redis-mailcow-1

# MariaDB containers
docker stop appwrite-mariadb
docker stop mailcowdockerized-mysql-mailcow-1
```

**Result:** Containers stopped but not removed (can restart if needed)

### Phase 7c: Monitor for 24 Hours

**After stopping containers:**
- Monitor applications for 24 hours
- Watch for any errors or connection issues
- Check application logs
- Verify all services working

**If issues occur:**
```bash
# Restart old containers
docker start <container-name>

# Investigate and fix
# Then retry cleanup later
```

### Phase 7d: Final Backup Before Removal

```bash
# Create final backup of old database data
docker start gibd-postgres  # Temporarily start
docker exec gibd-postgres pg_dumpall -U postgres > /backup/final-old-databases-$(date +%Y%m%d).sql
docker stop gibd-postgres

# Compress backup
gzip /backup/final-old-databases-*.sql
```

### Phase 7e: Remove Old Containers

**After 24 hours of successful operation with stopped containers:**

```bash
# Remove PostgreSQL containers
docker rm gibd-postgres
docker rm keycloak-postgres
docker rm wizardsofts-megabuild-postgres-1

# Remove Redis containers
docker rm gibd-redis
docker rm appwrite-redis
docker rm wizardsofts-megabuild-redis-1
docker rm mailcowdockerized-redis-mailcow-1

# Remove MariaDB containers
docker rm appwrite-mariadb
docker rm mailcowdockerized-mysql-mailcow-1
```

### Phase 7f: Clean Up Volumes (Optional)

**WARNING:** Only remove volumes after 100% certain data is migrated

```bash
# List volumes
docker volume ls | grep -E '(gibd|keycloak|wizardsofts-megabuild|appwrite|mailcow)'

# Remove volumes (CAUTION!)
docker volume rm gibd-postgres-data  # Only if certain!
docker volume rm keycloak-postgres-data
# ... etc
```

**Recommendation:** Keep old volumes for 30 days as extra backup

---

## Disk Space Reclaimed

### Estimated Space Recovery

| Container | Data Size | Expected Recovery |
|-----------|-----------|-------------------|
| gibd-postgres | 1.9 GB | ~2 GB |
| keycloak-postgres | 54 MB | ~60 MB |
| wizardsofts-megabuild-postgres | 13 MB | ~15 MB |
| All Redis | ~5 MB | ~10 MB |
| All MariaDB | ~50 MB | ~60 MB |
| **Total** | **~2.0 GB** | **~2.15 GB** |

**Additional Space from Images:**
- Old database images may be removed: ~500 MB

**Total Expected Recovery:** ~2.65 GB

**Server 84 Disk Space:**
- Before migration: 540 GB available
- After Phase 1 cleanup: 791 GB available
- After Phase 7 cleanup: ~794 GB available

---

## Optimization Recommendations

### 1. Resource Limits (Apply to New Database Services)

**Already Applied:**
- All new database services deployed via Docker Swarm
- Swarm services have built-in resource management

**Additional Optimizations:**
```bash
# Update PostgreSQL services with resource limits
docker service update \
  --limit-memory 2G \
  --reserve-memory 1G \
  gibd-postgres

# Update Redis services
docker service update \
  --limit-memory 256M \
  --reserve-memory 128M \
  gibd-redis
```

### 2. Database Performance Tuning

**PostgreSQL Configuration:**
```sql
-- On each PostgreSQL instance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
```

**Redis Configuration:**
```bash
# Add to redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 3. Automated Maintenance

**Weekly Cleanup Script:**
```bash
#!/bin/bash
# /scripts/weekly-maintenance.sh

# Docker system cleanup
docker system prune -f

# Remove dangling volumes
docker volume prune -f

# Remove unused images (keep last 7 days)
docker image prune -a -f --filter "until=168h"

# PostgreSQL VACUUM
for port in 5433 5434 5435; do
  docker exec $(docker ps | grep $port | awk '{print $1}') \
    psql -U postgres -c "VACUUM ANALYZE;"
done

# Check disk usage
df -h | grep -E '(Filesystem|/dev/)'

# Report
echo "Maintenance completed: $(date)" >> /var/log/docker-maintenance.log
```

**Add to cron:**
```cron
# Every Sunday at 3 AM
0 3 * * 0 /scripts/weekly-maintenance.sh
```

### 4. Monitoring Optimization

**Add Database Exporters:**
```bash
# PostgreSQL exporter for detailed metrics
docker service create \
  --name postgres-exporter \
  --network monitoring-network \
  -e DATA_SOURCE_NAME="postgresql://postgres:password@10.0.0.80:5435/?sslmode=disable" \
  wrouesnel/postgres_exporter

# Redis exporter
docker service create \
  --name redis-exporter \
  --network monitoring-network \
  oliver006/redis_exporter \
  --redis.addr=redis://10.0.0.80:6380
```

### 5. Backup Automation

**Automated Daily Backups:**
```bash
#!/bin/bash
# /scripts/backup-databases.sh

BACKUP_DIR="/backup/daily/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

# PostgreSQL backups
for port in 5433 5434 5435; do
  pg_dump -h 10.0.0.80 -p $port -U postgres -Fc > \
    $BACKUP_DIR/postgres-$port.dump
done

# MariaDB backups
for port in 3307 3308; do
  mysqldump -h 10.0.0.80 -P $port -u root -p'password' --all-databases > \
    $BACKUP_DIR/mariadb-$port.sql
done

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Remove backups older than 7 days
find /backup/daily -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $(date)" >> /var/log/database-backups.log
```

**Add to cron:**
```cron
# Every day at 2 AM
0 2 * * * /scripts/backup-databases.sh
```

---

## Verification Checklist

### Before Cleanup
- [ ] 72+ hours of successful operation
- [ ] All applications switched to new databases
- [ ] No connection errors
- [ ] No performance issues
- [ ] Final backup created

### After Cleanup
- [ ] Old containers stopped
- [ ] Applications still working
- [ ] No errors in logs
- [ ] Disk space reclaimed
- [ ] Backups preserved

---

## Actions Taken in Phase 7

| Action | Status | Details |
|--------|--------|---------|
| Document old containers | ✅ | 9 database containers identified |
| Create cleanup procedure | ✅ | Step-by-step guide created |
| Estimate disk recovery | ✅ | ~2.65 GB to be reclaimed |
| Document resource limits | ✅ | Optimization recommendations provided |
| Create maintenance scripts | ✅ | Automated cleanup and backup scripts |
| Define verification criteria | ✅ | Checklist before/after cleanup |

---

## Timeline

**Day 0 (Today):** Migration completed, documentation created
**Day 1-3:** Monitoring and verification period
**Day 3:** Execute cleanup (stop old containers)
**Day 4:** Verify applications working after cleanup
**Day 4+:** Remove old containers if verification successful
**Day 7+:** Remove old volumes if 100% confident

---

## Recommendations

### Immediate
- ✅ Continue monitoring new databases
- ✅ Watch application logs for errors
- ✅ Verify performance metrics

### Day 3 (After 72 Hours)
- [ ] Execute Phase 7b (stop old containers)
- [ ] Create final backup before removal
- [ ] Monitor for 24 hours

### Day 4+ (After Verification)
- [ ] Remove old containers
- [ ] Verify disk space reclaimed
- [ ] Update documentation

### Ongoing
- [ ] Set up automated maintenance scripts
- [ ] Configure resource limits on services
- [ ] Implement automated backups
- [ ] Add database exporters to Prometheus

---

## Summary

**Cleanup Plan:** ✅ Documented and ready
- 9 old database containers to clean up
- ~2.65 GB disk space to reclaim
- 72-hour waiting period for safety
- Step-by-step procedures created

**Optimization:** ✅ Recommendations provided
- Resource limits configuration
- Database performance tuning
- Automated maintenance scripts
- Backup automation
- Monitoring improvements

**Execution:** ⏸️ DEFERRED to Day 3+
- Waiting for 72-hour verification period
- Allows thorough testing
- Ensures migration success before cleanup

---

**Phase 7 Status:** ✅ COMPLETE (Planning and Documentation)
**Execution Date:** Day 3+ (after 72 hours of verification)
**Next Phase:** Phase 8 - Testing & Validation

# Phase 3: Database Migration - Detailed Plan

**Date:** 2026-01-01
**Status:** READY TO START
**Risk Level:** HIGH (includes GitLab production database)
**Estimated Duration:** 8-12 hours

---

## Critical Discovery

The `gibd-postgres` container on server 84 contains **GitLab's production database** plus 7 application databases:

### Databases in gibd-postgres (8 total, 1.9GB)

| Database | Owner | Size | Purpose |
|----------|-------|------|---------|
| ws_gibd_dse_daily_trades | gibd | 1556 MB | Stock trading data (largest) |
| **gitlabhq_production** | gitlab | 151 MB | **GitLab source control** |
| ws_gibd_news_database | gibd | 130 MB | News database |
| ws_daily_deen_guide | gibd | 69 MB | Daily Deen Guide app |
| ws_gibd_dse_company_info | gibd | 11 MB | Company information |
| postgres | postgres | 7.5 MB | Default database |
| template1 | postgres | 7.6 MB | Template database |
| template0 | postgres | 7.4 MB | Template database |

**Total Size:** ~1.9 GB

### Database Users
- `postgres` - Superuser
- `gibd` - Owner of application databases
- `gitlab` - Owner of GitLab database
- `ws_gibd` - Application user

---

## All Databases to Migrate (Full Inventory)

### Server 84 - gibd-postgres Container

**PostgreSQL Instance:** postgres:16, Port 5432
**Databases:** 8 databases (1.9 GB total)
**Critical:** Contains GitLab production database

### Server 84 - keycloak-postgres Container

**PostgreSQL Instance:** postgres:15-alpine
**Database:** keycloak (authentication)
**Size:** ~54 MB (from backup)

### Server 84 - wizardsofts-megabuild-postgres-1 Container

**PostgreSQL Instance:** postgres:15-alpine
**Database:** Unknown (need to inspect)
**Size:** ~13 MB (from backup)

### Server 84 - Redis Instances (4)

1. **gibd-redis** (redis:7-alpine) - Application cache, ~480 KB
2. **appwrite-redis** (redis:7-alpine) - Appwrite cache, ~27 KB
3. **wizardsofts-megabuild-redis-1** (redis:7-alpine) - Megabuild cache, ~134 B
4. **mailcowdockerized-redis-mailcow-1** (redis:7.4.6-alpine) - Mailcow cache

### Server 84 - MariaDB Instances (2)

1. **appwrite-mariadb** (mariadb:10.11) - Appwrite database
2. **mailcowdockerized-mysql-mailcow-1** (mariadb:10.11) - Mailcow database

**Total:** 9 database containers, ~2.1 GB total data

---

## Migration Strategy (Revised)

### Approach: Blue-Green with Extra Caution

Given that GitLab's database is involved, we need extra safety:

1. **Keep ALL old databases running** until 100% verified
2. Deploy new database services on Swarm
3. Migrate data with verification
4. **Test extensively** before switching
5. Dual-run for 48-72 hours
6. Only remove old databases after complete confidence

### Migration Order (By Risk)

**Phase 3a: Low-Risk Databases First**
1. wizardsofts-megabuild-postgres (smallest, lowest impact)
2. wizardsofts-megabuild-redis (cache, can rebuild)

**Phase 3b: Medium-Risk Databases**
3. keycloak-postgres (authentication, has backup)
4. gibd-redis (application cache, can rebuild)

**Phase 3c: High-Risk - Application Databases**
5. Application databases from gibd-postgres (trading data)
6. appwrite-mariadb (Appwrite stack)
7. appwrite-redis (Appwrite cache)

**Phase 3d: CRITICAL - GitLab Database**
8. gitlabhq_production (SOURCE CONTROL - maximum caution)

**Phase 3e: Infrastructure Databases**
9. Mailcow databases (email system)

---

## Detailed Migration Steps - Template

### For Each PostgreSQL Database:

**Step 1: Deploy New Service on Swarm**
```bash
# Create Docker Swarm service
docker service create \
  --name <db-name>-new \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=<db-name>-data,target=/var/lib/postgresql/data \
  --env POSTGRES_USER=<user> \
  --env POSTGRES_PASSWORD=<password> \
  --env POSTGRES_DB=<dbname> \
  --publish 5433:5432 \
  postgres:16
```

**Step 2: Wait for Service Ready**
```bash
docker service ps <db-name>-new
docker service logs <db-name>-new
```

**Step 3: Export Data from Old Database**
```bash
# On server 84
docker exec gibd-postgres pg_dump -U postgres <dbname> -Fc -f /backups/<dbname>-migration.dump

# Verify dump
ls -lh /mnt/data/docker/postgres/backups/<dbname>-migration.dump
```

**Step 4: Transfer Dump to New Database**
```bash
# Copy dump to server 80
scp wizardsofts@10.0.0.84:/mnt/data/docker/postgres/backups/<dbname>-migration.dump \
    wizardsofts@10.0.0.80:/tmp/

# Import to new database (find container on server 80)
ssh wizardsofts@10.0.0.80
CONTAINER_ID=$(docker ps | grep <db-name>-new | awk '{print $1}')
docker cp /tmp/<dbname>-migration.dump $CONTAINER_ID:/tmp/
docker exec $CONTAINER_ID pg_restore -U postgres -d <dbname> /tmp/<dbname>-migration.dump
```

**Step 5: Verify Data Integrity**
```bash
# Compare row counts
docker exec gibd-postgres psql -U postgres -d <dbname> -c "\dt" > /tmp/old-tables.txt
ssh wizardsofts@10.0.0.80 "docker exec $CONTAINER_ID psql -U postgres -d <dbname> -c '\dt'" > /tmp/new-tables.txt
diff /tmp/old-tables.txt /tmp/new-tables.txt

# Compare database sizes
docker exec gibd-postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('<dbname>'));"
ssh wizardsofts@10.0.0.80 "docker exec $CONTAINER_ID psql -U postgres -c \"SELECT pg_size_pretty(pg_database_size('<dbname>'));\""
```

**Step 6: Test Application Connection**
```bash
# Update app config to point to new database
# Test with read-only queries first
# Then test writes
# Verify data appears in new database
```

**Step 7: Switch Production Traffic**
```bash
# Update all application configs to use new database
# Monitor logs for errors
# Keep old database running for rollback
```

**Step 8: Dual-Run Period**
```bash
# Run both databases for 48 hours
# Monitor performance
# Compare data
```

**Step 9: Decommission Old Database**
```bash
# Only after 48+ hours of successful operation
# Stop old container
# Keep backup for 30 days
```

---

## Risk Mitigation

### Before Migration
- ✅ Backups created and verified
- ✅ Swarm cluster operational
- ✅ Disk space confirmed
- ⏸️ Create additional backup before each migration
- ⏸️ Document current connection strings

### During Migration
- Deploy new database FIRST
- Keep old database running
- Test thoroughly before switching
- Monitor application logs
- Have rollback plan ready

### After Migration
- Dual-run for 48-72 hours
- Compare data integrity daily
- Monitor performance metrics
- Keep old databases for 1 week minimum

---

## Rollback Plan

### If New Database Fails

**Immediate Rollback:**
```bash
# Stop new database service
docker service rm <db-name>-new

# Update apps back to old database
# Edit connection strings

# Old database still running - zero downtime
```

### If Data Corruption Detected

**Restore from Backup:**
```bash
# Stop new database
docker service rm <db-name>-new

# Restore from pre-migration backup
zcat /backup/pre-migration-20260101/postgres-gibd-all-20260101.sql.gz | \
  docker exec -i gibd-postgres psql -U postgres

# Verify restoration
```

---

## Success Criteria

### For Each Database Migration

✅ **Deployment:**
- New database service running on server 80
- Service healthy and stable
- Accessible via Swarm network

✅ **Data:**
- All data migrated successfully
- Row counts match between old and new
- Data integrity verified (checksums if applicable)

✅ **Performance:**
- Query performance equal or better than old
- No connection errors
- Application logs clean

✅ **Stability:**
- No crashes or restarts for 48+ hours
- Memory usage stable
- CPU usage acceptable

---

## Next Steps

### Immediate (Before Starting Migration)

1. **Inspect remaining PostgreSQL containers:**
   - keycloak-postgres: Check databases and size
   - wizardsofts-megabuild-postgres-1: Check databases and size

2. **Create volume strategy:**
   - Decide on volume placement (server 80 disk locations)
   - Ensure sufficient space for data + growth

3. **Document connection strings:**
   - Find all apps using each database
   - Document current connection configs
   - Prepare new connection configs

4. **Test Swarm service deployment:**
   - Deploy a test PostgreSQL service
   - Verify it works on server 80
   - Remove test service

5. **Final backup verification:**
   - Verify backup integrity
   - Test restore from backup
   - Ensure backup is accessible

### Then Start with Lowest Risk

**First Migration: wizardsofts-megabuild-postgres-1**
- Smallest (13 MB)
- Likely not critical
- Good test case for process
- Learn and refine process

**Then Progress Based on Success**

---

## Monitoring During Migration

### Metrics to Watch

**Old Database (Server 84):**
- Connection count
- Query performance
- Error logs
- Disk I/O

**New Database (Server 80):**
- Service health
- Connection count
- Query performance
- Memory usage
- Disk I/O

**Applications:**
- Error rates
- Response times
- Database connection errors
- User reports

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 3a: Small databases | 2 migrations | 2-3 hours |
| 3b: Medium databases | 2 migrations | 2-3 hours |
| 3c: Application databases | 3 migrations | 3-4 hours |
| 3d: GitLab database | 1 migration | 2-3 hours |
| 3e: Infrastructure databases | 2 migrations | 2-3 hours |
| **Total** | **10 migrations** | **11-16 hours** |

**Plus:** 48 hours dual-run period for each critical database

---

## Decision Point

**Before proceeding with Phase 3, we should:**

1. ✅ Review this plan
2. ⏸️ Inspect remaining PostgreSQL containers
3. ⏸️ Test Swarm service deployment
4. ⏸️ Document all connection strings
5. ⏸️ Create fresh backup before migration

**Status:** Plan documented, awaiting approval to proceed.

**Recommendation:** Start with smallest, lowest-risk database (wizardsofts-megabuild-postgres-1) as proof of concept.

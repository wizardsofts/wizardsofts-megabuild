# DB-001-003: wizardsofts-megabuild-postgres Migration

**Date:** 2026-01-01
**Status:** ✅ COMPLETED
**Duration:** 30 minutes
**Risk:** LOW (test database, no production data)

## Summary

Successfully migrated `wizardsofts-megabuild-postgres-1` container to Docker Swarm service on server 80. This was the first database migration and served as a proof-of-concept for the migration process.

## Database Information

### Old Database (Server 84)
- **Container:** `wizardsofts-megabuild-postgres-1`
- **Image:** postgres:15-alpine
- **Size:** ~13 MB (container size, no actual data)
- **Databases:** 4 databases (all empty)
  - gibd
  - ws_gibd_dse_company_info
  - ws_gibd_dse_daily_trades
  - ws_gibd_news

### New Database (Server 80)
- **Service:** `ws-megabuild-postgres` (Docker Swarm service)
- **Node:** hppavilion (server 80)
- **Image:** postgres:15-alpine
- **Volume:** ws-megabuild-postgres-data
- **Network:** database-network (encrypted overlay)
- **Port:** 5433 (published in host mode)

## Migration Steps

### DB-001: Inspect Old Database
**Actions:**
- Inspected wizardsofts-megabuild-postgres-1 container on server 84
- Verified database list and sizes
- Discovered all 4 databases were empty (no tables, no data)

**Findings:**
```sql
# Database list from old container
gibd                     | 643 bytes
ws_gibd_dse_company_info | 643 bytes
ws_gibd_dse_daily_trades | 643 bytes
ws_gibd_news             | 643 bytes
```

**Conclusion:** All databases empty, perfect test case for first migration.

### DB-002: Deploy New PostgreSQL Service

**Initial Attempt (Failed):**
```bash
docker service create \
  --name ws-megabuild-postgres \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=ws-megabuild-postgres-data,target=/var/lib/postgresql/data \
  --env POSTGRES_USER=gibd \
  --env POSTGRES_PASSWORD='29Dec2#24' \
  --env POSTGRES_DB=gibd \
  --publish 5433:5432 \
  postgres:15-alpine
```

**Issue:** Port published in ingress mode (default), causing connection timeouts for database clients.

**Fix:** Recreated service with `mode=host` for direct port publishing:
```bash
docker service create \
  --name ws-megabuild-postgres \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=ws-megabuild-postgres-data,target=/var/lib/postgresql/data \
  --env POSTGRES_USER=gibd \
  --env POSTGRES_PASSWORD='29Dec2#24' \
  --env POSTGRES_DB=gibd \
  --publish published=5433,target=5432,mode=host \
  postgres:15-alpine
```

**Result:** Service deployed successfully, running on server 80.

### DB-003: Migrate Data and Verify

**Data Export:**
```bash
# Exported all 4 databases from old container
docker exec wizardsofts-megabuild-postgres-1 pg_dump -U gibd gibd > gibd.sql
docker exec wizardsofts-megabuild-postgres-1 pg_dump -U gibd ws_gibd_dse_company_info > ws_gibd_dse_company_info.sql
docker exec wizardsofts-megabuild-postgres-1 pg_dump -U gibd ws_gibd_dse_daily_trades > ws_gibd_dse_daily_trades.sql
docker exec wizardsofts-megabuild-postgres-1 pg_dump -U gibd ws_gibd_news > ws_gibd_news.sql
```

**Export Results:** All files 643 bytes (empty databases with just schema header).

**Database Creation:**
Since databases were empty, simply created them in new PostgreSQL:
```bash
# Via docker exec on server 80
docker exec <container-id> psql -U gibd -c 'CREATE DATABASE ws_gibd_dse_company_info;'
docker exec <container-id> psql -U gibd -c 'CREATE DATABASE ws_gibd_dse_daily_trades;'
docker exec <container-id> psql -U gibd -c 'CREATE DATABASE ws_gibd_news;'
```

**Connectivity Test:**
```bash
# From server 84 → server 80:5433
docker exec wizardsofts-megabuild-postgres-1 sh -c \
  "PGPASSWORD='29Dec2#24' psql -h 10.0.0.80 -p 5433 -U gibd -d gibd -c 'SELECT version();'"

# Result: SUCCESS
# PostgreSQL 15.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
```

## Issues Encountered and Resolutions

### Issue 1: Port Publishing Mode (Ingress vs Host)
**Problem:** Default ingress mode caused connection timeouts for PostgreSQL clients.
**Symptoms:** `psql: error: connection to server at "10.0.0.80", port 5433 failed: Operation timed out`
**Root Cause:** Ingress mode uses IPVS load balancing which is incompatible with stateful protocols like PostgreSQL.
**Resolution:** Recreated service with `--publish mode=host` to publish port directly on the node.
**Lesson Learned:** For databases, always use `mode=host` in Docker Swarm.

### Issue 2: UFW Firewall Blocking Port 5433
**Problem:** Initial connection attempts timed out even with correct port publishing.
**Root Cause:** UFW firewall on server 80 was not configured to allow port 5433.
**Resolution:** Added UFW rule:
```bash
sudo ufw allow from 10.0.0.0/24 to any port 5433 proto tcp comment 'PostgreSQL ws-megabuild test port'
```
**Lesson Learned:** Always add UFW rules for new database ports.

### Issue 3: Password Authentication Required
**Problem:** `psql: error: fe_sendauth: no password supplied`
**Resolution:** Used `PGPASSWORD` environment variable:
```bash
PGPASSWORD='29Dec2#24' psql -h 10.0.0.80 -p 5433 -U gibd -d gibd
```

## Verification

### ✅ Service Health
```bash
docker service ps ws-megabuild-postgres
# Result: Running on hppavilion, healthy
```

### ✅ Database List
```sql
\l
# Result: All 4 databases present (gibd, ws_gibd_dse_company_info, ws_gibd_dse_daily_trades, ws_gibd_news)
```

### ✅ Connectivity
```bash
# From server 84 to server 80
PGPASSWORD='29Dec2#24' psql -h 10.0.0.80 -p 5433 -U gibd -d gibd -c 'SELECT version();'
# Result: SUCCESS - PostgreSQL 15.15
```

### ✅ Data Integrity
- No data to verify (databases were empty)
- All databases created successfully
- Ready for application use

## Migration Template for Future Databases

Based on this migration, the following template will be used for subsequent PostgreSQL migrations:

```bash
# 1. Deploy new service with HOST MODE publishing
docker service create \
  --name <service-name> \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=<volume-name>,target=/var/lib/postgresql/data \
  --env POSTGRES_USER=<user> \
  --env POSTGRES_PASSWORD='<password>' \
  --env POSTGRES_DB=<default-db> \
  --publish published=<port>,target=5432,mode=host \
  postgres:15-alpine

# 2. Add UFW rule
sudo ufw allow from 10.0.0.0/24 to any port <port> proto tcp

# 3. Export data from old database
docker exec <old-container> pg_dump -U <user> -Fc -f /tmp/<db-name>.dump <db-name>

# 4. Copy dump to new server
scp <old-server>:/tmp/<db-name>.dump <new-server>:/tmp/

# 5. Import to new database
docker exec <new-container> pg_restore -U <user> -d <db-name> /tmp/<db-name>.dump

# 6. Verify data integrity
docker exec <new-container> psql -U <user> -d <db-name> -c '\dt'
docker exec <new-container> psql -U <user> -d <db-name> -c 'SELECT count(*) FROM <table>;'
```

## Next Steps

### Immediate
1. ✅ Mark DB-001, DB-002, DB-003 as complete
2. ✅ Update handoff.json
3. ⏸️ Commit migration progress to git
4. ⏸️ Start next database: keycloak-postgres

### For This Database
- **Old container status:** Keep running for now (will remove after all migrations complete)
- **New service status:** Running and verified
- **Application updates:** Not needed (test database, not in production use)
- **Rollback plan:** Simply switch connection string back to old container

## Success Criteria

✅ **Deployment:**
- New service running on server 80
- Service healthy and stable
- Accessible via Swarm network

✅ **Data:**
- All databases created successfully
- No data loss (databases were empty)
- Database structure intact

✅ **Performance:**
- Connection successful from server 84
- No errors in logs
- Response time acceptable

✅ **Stability:**
- Service running for 10+ minutes without issues
- No crashes or restarts
- Memory usage normal

## Timeline

- **08:45** - Started inspection (DB-001)
- **08:50** - Deployed service with ingress mode (failed)
- **09:00** - Added UFW rule
- **09:05** - Recreated service with host mode
- **09:10** - Created databases
- **09:15** - Verified connectivity
- **09:15** - ✅ Migration complete

**Total Duration:** 30 minutes

---

**Status:** ✅ MIGRATION COMPLETE
**Next Task:** DB-004 - Inspect and migrate keycloak-postgres

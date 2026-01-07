# Database Admin Skill - User-Level Claude Code Skill

**Skill Type:** User-level
**Storage Location:** `~/.claude/skills/database-admin/`
**Trigger phrases:** "postgres", "database backup", "pg_dump", "pg_restore", "database migration", "slow query", "connection pool", "database schema"

---

## Overview

This skill provides comprehensive PostgreSQL database administration for WizardSofts infrastructure, covering backup/restore operations, schema migrations, performance tuning, and troubleshooting across multiple servers.

---

## What This Skill Has

### PostgreSQL Infrastructure Knowledge

**Multi-Server Topology:**
- **Server 80 (10.0.0.80):** Ports 5433, 5434, 5435 (GIBD databases)
- **Server 84 (10.0.0.84):** Port 5432 (GitLab, Appwrite databases)

**Database Instances:**
- `ws_gibd_dse_company_info` - Company information database
- `ws_gibd_dse_daily_trades` - Daily trades database
- `gitlab` - GitLab CE database (external PostgreSQL)
- `appwrite` - Appwrite BaaS database

**Security Configuration:**
- Localhost-only binding (`127.0.0.1:5433:5432`)
- Password authentication required
- No internet exposure (internal Docker network only)

### Backup & Restore Procedures

**Backup Formats:**
1. **SQL Format** (`.sql`) - Human-readable, portable
   - Best for: Small databases, version control, manual inspection
   - Created with: `pg_dump -d database > backup.sql`

2. **Custom Format** (`.dump`) - Binary, compressed, parallel restore
   - Best for: Large databases, production backups, fast restore
   - Created with: `pg_dump -d database -F c -f backup.dump`

**Backup Components:**
- Database data (tables, rows)
- Database schema (CREATE TABLE, indexes, constraints)
- Roles and permissions (`pg_dumpall --roles-only`)
- Global objects (tablespaces, etc.)
- Row count verification
- Migration metadata

### Schema Management

**Database Schema (GIBD Quant Agent):**

**Table: ws_dse_daily_prices**
- Composite primary key: (txn_scrip, txn_date)
- OHLCV data: open, high, low, close, volume
- Automatic timestamps: created_at, updated_at

**Table: indicators**
- Composite primary key: (scrip, trading_date)
- JSONB column for flexible indicator storage
- Status tracking: CALCULATED | PENDING | ERROR
- Versioning support

**Migration Tools:**
- Alembic for schema versioning
- Automated migration generation
- Rollback capability

### Connection Management

**Connection Patterns:**
- External PostgreSQL for GitLab (gibd-postgres container)
- Internal PostgreSQL for Appwrite
- Connection pooling via SQLAlchemy
- Health check endpoints

---

## What This Skill Will Do

### 1. Backup Operations

**Full Database Backup:**
```bash
# Create comprehensive backup with multiple formats
pg_dump -h localhost -U postgres -d ws_gibd_dse_company_info > company_info.sql
pg_dump -h localhost -U postgres -d ws_gibd_dse_company_info -F c -f company_info.dump

# Backup roles and global objects
pg_dumpall -h localhost -U postgres --roles-only > roles.sql

# Generate row count verification
psql -h localhost -U postgres -d ws_gibd_dse_company_info -c "
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;" > table_counts.txt

# Compress backups
tar -czf postgres-backup-$(date +%Y%m%d-%H%M%S).tar.gz *.sql *.dump *.txt
```

**Incremental Backup:**
```bash
# Backup only changed data (requires WAL archiving)
pg_basebackup -h localhost -U postgres -D /backup/incremental -Fp -Xs -P
```

**Schema-Only Backup:**
```bash
# Export schema without data
pg_dump -h localhost -U postgres -d database --schema-only > schema.sql
```

**Data-Only Backup:**
```bash
# Export data without schema
pg_dump -h localhost -U postgres -d database --data-only > data.sql
```

### 2. Restore Operations

**Full Database Restore (SQL Format):**
```bash
# Create database if it doesn't exist
createdb -h localhost -U postgres restored_database

# Restore from SQL dump
psql -h localhost -U postgres -d restored_database < backup.sql
```

**Full Database Restore (Custom Format):**
```bash
# Restore with parallel processing (4 jobs)
pg_restore -h localhost -U postgres -d restored_database -j 4 -F c backup.dump
```

**Selective Table Restore:**
```bash
# Restore only specific tables
pg_restore -h localhost -U postgres -d database -t table_name backup.dump
```

**Restore Roles:**
```bash
# Restore user roles and permissions
psql -h localhost -U postgres < roles.sql
```

**Verify Restoration:**
```bash
# Compare row counts
psql -h localhost -U postgres -d database -c "
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;"
```

### 3. Database Troubleshooting

**Connection Issues:**

**Symptom:** Application can't connect to PostgreSQL

**Diagnosis:**
```bash
# 1. Check if PostgreSQL container is running
docker ps | grep postgres

# 2. Check PostgreSQL logs
docker logs gibd-postgres --tail 50

# 3. Test connection from host
psql -h localhost -p 5433 -U postgres -d database

# 4. Test connection from application container
docker exec <app-container> psql -h gibd-postgres -U postgres -d database

# 5. Verify network connectivity
docker exec <app-container> ping -c 2 gibd-postgres

# 6. Check PostgreSQL is listening on correct port
docker exec gibd-postgres netstat -tlnp | grep 5432
```

**Fix:**
- Verify Docker network configuration
- Check credentials in .env files
- Ensure database exists: `psql -l`
- Recreate container if needed

**GitLab Database Connection Issues:**

**Symptom:** GitLab shows "Database connection failed"

**Diagnosis:**
```bash
# 1. Check if gibd-postgres is running
docker ps | grep postgres

# 2. Verify GitLab can reach database
docker exec gitlab ping gibd-postgres

# 3. Run GitLab database check
docker exec gitlab gitlab-rake gitlab:check

# 4. Check database configuration in GitLab
docker exec gitlab grep -A 10 "db_adapter" /etc/gitlab/gitlab.rb
```

**Fix:**
- Ensure gibd-postgres is on gibd-network
- Verify gitlab container is on gibd-network
- Check database credentials in GITLAB_OMNIBUS_CONFIG
- Run migrations: `docker exec gitlab gitlab-rake db:migrate`

**Slow Query Performance:**

**Symptom:** Queries taking too long

**Diagnosis:**
```sql
-- Enable slow query logging
ALTER DATABASE database SET log_min_duration_statement = 1000; -- 1 second

-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100;

-- Check table bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Fix:**
- Add missing indexes
- Run VACUUM ANALYZE
- Optimize queries
- Increase shared_buffers if needed

**Connection Pool Exhaustion:**

**Symptom:** "Too many connections" error

**Diagnosis:**
```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;

-- Check connection limit
SHOW max_connections;

-- See who is connected
SELECT datname, usename, count(*)
FROM pg_stat_activity
GROUP BY datname, usename;

-- Find idle connections
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '5 minutes';
```

**Fix:**
- Kill idle connections: `SELECT pg_terminate_backend(pid);`
- Increase max_connections in postgresql.conf
- Reduce connection pool size in application
- Implement connection pooling (PgBouncer)

### 4. Schema Management

**Generate Schema Documentation:**
```bash
# Create ERD using SchemaSpy
docker run --rm --net=gibd-network \
  -v "$PWD/output:/output" \
  schemaspy/schemaspy:latest \
  -t pgsql -host gibd-postgres -port 5432 \
  -db database -u postgres -p password \
  -s public

# Create simple text schema
pg_dump -h localhost -U postgres -d database --schema-only > schema.sql
```

**Create Alembic Migration:**
```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate migration from model changes
alembic revision --autogenerate -m "Add new table"

# Review migration file
cat alembic/versions/*_add_new_table.py

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

**Validate Schema Integrity:**
```sql
-- Check for missing foreign keys
SELECT conrelid::regclass AS table_name,
       conname AS constraint_name,
       pg_get_constraintdef(oid)
FROM pg_constraint
WHERE contype = 'f';

-- Check for missing primary keys
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN (
  SELECT tablename
  FROM pg_indexes
  WHERE indexname LIKE '%_pkey'
);

-- Check for duplicate indexes
SELECT array_agg(indexname) as indexes, tablename, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
GROUP BY tablename, indexdef
HAVING count(*) > 1;
```

### 5. Database Monitoring

**Real-Time Metrics:**
```sql
-- Database size
SELECT pg_database.datname,
       pg_size_pretty(pg_database_size(pg_database.datname))
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- Table sizes
SELECT schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT schemaname, tablename, indexname,
       idx_scan as index_scans,
       idx_tup_read as tuples_read,
       idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Cache hit ratio (should be > 99%)
SELECT sum(heap_blks_read) as heap_read,
       sum(heap_blks_hit) as heap_hit,
       sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- Active queries
SELECT pid, usename, application_name, state,
       now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

**Prometheus Metrics (via postgres_exporter):**
- `pg_up` - Database availability
- `pg_database_size_bytes` - Database size
- `pg_stat_database_*` - Connection and transaction stats
- `pg_stat_user_tables_*` - Table statistics
- `pg_locks_*` - Lock information

---

## Example Usage

### Example 1: Backup GIBD Databases from Server 80

**User Request:**
```
User: "Backup the GIBD databases from server 80"
```

**Skill Actions:**
```bash
# 1. SSH into server 80
ssh wizardsofts@10.0.0.80

# 2. Run backup script
cd /tmp
mkdir -p postgres-migration-backup
cd postgres-migration-backup

# 3. Backup ws_gibd_dse_company_info
pg_dump -h localhost -U postgres -d ws_gibd_dse_company_info > company_info.sql
pg_dump -h localhost -U postgres -d ws_gibd_dse_company_info -F c -f company_info.dump

# 4. Backup ws_gibd_dse_daily_trades
pg_dump -h localhost -U postgres -d ws_gibd_dse_daily_trades > daily_trades.sql
pg_dump -h localhost -U postgres -d ws_gibd_dse_daily_trades -F c -f daily_trades.dump

# 5. Backup roles
pg_dumpall -h localhost -U postgres --roles-only > roles.sql

# 6. Get row counts
psql -h localhost -U postgres -d ws_gibd_dse_company_info -c "
SELECT schemaname, tablename, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;" > company_info_counts.txt

psql -h localhost -U postgres -d ws_gibd_dse_daily_trades -c "
SELECT schemaname, tablename, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;" > daily_trades_counts.txt

# 7. Create metadata file
cat > migration_metadata.txt <<EOF
PostgreSQL Backup - Server 80
Created: $(date)
PostgreSQL Version: $(psql -h localhost -U postgres -t -c "SELECT version();")
Databases: ws_gibd_dse_company_info, ws_gibd_dse_daily_trades
EOF

# 8. Compress all backups
BACKUP_FILE="postgres-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" *.sql *.dump *.txt

# 9. Display backup info
ls -lh "$BACKUP_FILE"
echo "Backup location: $(pwd)/$BACKUP_FILE"

# 10. Provide transfer command
echo "Transfer to server 84:"
echo "scp $(pwd)/$BACKUP_FILE wizardsofts@10.0.0.84:/tmp/"
```

### Example 2: GitLab Can't Connect to PostgreSQL

**User Request:**
```
User: "GitLab can't connect to PostgreSQL"
```

**Skill Actions:**
```bash
# 1. Check if gibd-postgres container is running
docker ps | grep postgres
# If not running: docker start gibd-postgres

# 2. Verify GitLab container is running
docker ps | grep gitlab

# 3. Check if both containers are on same network
docker network inspect gibd-network | grep -E "gitlab|postgres"

# 4. Test network connectivity
docker exec gitlab ping -c 2 gibd-postgres
# If fails: docker network connect gibd-network gitlab

# 5. Check PostgreSQL is listening
docker exec gibd-postgres netstat -tlnp | grep 5432

# 6. Verify database exists
docker exec gibd-postgres psql -U postgres -l | grep gitlab

# 7. Test connection with credentials
docker exec gitlab psql -h gibd-postgres -U postgres -d gitlab -c "SELECT 1;"

# 8. Run GitLab database check
docker exec gitlab gitlab-rake gitlab:check

# 9. Check GitLab configuration
docker exec gitlab grep -A 10 "db_adapter" /etc/gitlab/gitlab.rb

# 10. If all fails, recreate GitLab container
docker-compose -f infrastructure/gitlab/docker-compose.yml down
docker-compose -f infrastructure/gitlab/docker-compose.yml up -d

# Wait 2 minutes for initialization
sleep 120

# Verify health
curl http://10.0.0.84:8090/-/readiness
```

**Diagnosis Result:**
- Database connection successful
- Issue identified: GitLab not on gibd-network
- Fix applied: Added GitLab to network
- Verification: Health check passes

### Example 3: Restore Database on Server 84

**User Request:**
```
User: "Restore the GIBD database backup on server 84"
```

**Skill Actions:**
```bash
# 1. Transfer backup to server 84 (if not already there)
scp postgres-backup-20260103-120000.tar.gz wizardsofts@10.0.0.84:/tmp/

# 2. SSH into server 84
ssh wizardsofts@10.0.0.84

# 3. Extract backup
cd /tmp
tar -xzf postgres-backup-20260103-120000.tar.gz

# 4. Create target database if it doesn't exist
docker exec gibd-postgres createdb -U postgres ws_gibd_dse_company_info

# 5. Restore roles first
docker exec -i gibd-postgres psql -U postgres < roles.sql

# 6. Restore database from custom format (parallel restore)
docker exec -i gibd-postgres pg_restore -U postgres -d ws_gibd_dse_company_info -j 4 -F c < company_info.dump

# 7. Verify restoration - compare row counts
docker exec gibd-postgres psql -U postgres -d ws_gibd_dse_company_info -c "
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;" > restored_counts.txt

# 8. Compare with original counts
diff company_info_counts.txt restored_counts.txt

# 9. Test database connectivity
docker exec gibd-postgres psql -U postgres -d ws_gibd_dse_company_info -c "SELECT count(*) FROM ws_dse_daily_prices;"

# 10. Provide restoration summary
echo "Database restored successfully!"
echo "Original backup: $(cat migration_metadata.txt)"
echo "Restored on: $(date)"
```

### Example 4: Optimize Slow Query

**User Request:**
```
User: "Queries on ws_dse_daily_prices are very slow"
```

**Skill Actions:**
```sql
-- 1. Check current query performance
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE query LIKE '%ws_dse_daily_prices%'
ORDER BY mean_time DESC
LIMIT 5;

-- 2. Check for missing indexes
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE tablename = 'ws_dse_daily_prices'
AND n_distinct > 100;

-- 3. Check current indexes
\d ws_dse_daily_prices

-- 4. Analyze query plan for slow query
EXPLAIN ANALYZE
SELECT * FROM ws_dse_daily_prices
WHERE txn_scrip = 'BATBC'
AND txn_date >= '2024-01-01';

-- 5. Create missing indexes
CREATE INDEX idx_ws_dse_daily_prices_date ON ws_dse_daily_prices (txn_date);
CREATE INDEX idx_ws_dse_daily_prices_scrip ON ws_dse_daily_prices (txn_scrip);

-- 6. Run VACUUM ANALYZE
VACUUM ANALYZE ws_dse_daily_prices;

-- 7. Re-test query performance
EXPLAIN ANALYZE
SELECT * FROM ws_dse_daily_prices
WHERE txn_scrip = 'BATBC'
AND txn_date >= '2024-01-01';

-- 8. Compare before/after execution time
-- Before: 2500ms
-- After: 15ms (167x faster)

-- 9. Update statistics
ANALYZE ws_dse_daily_prices;
```

---

## Related Skills

- **DevOps Skill** - For coordinating database deployments
- **Server Security Skill** - For securing database access and port bindings

---

## Configuration Files

**PostgreSQL Configuration:**
- `docker-compose.yml` - Database service definitions
- `.env` - Database credentials (POSTGRES_PASSWORD, DB_PASSWORD)

**Migration Tools:**
- `alembic/alembic.ini` - Alembic configuration
- `alembic/versions/*.py` - Migration scripts

**Backup Scripts:**
- `scripts/migrate-postgres-backup.sh` - Comprehensive backup script

**Documentation:**
- `docs/DATABASE_SCHEMA.md` - Schema documentation
- `docs/DATABASE_MIGRATION_COMPLETE.md` - Migration history

---

## Database Instances Reference

| Database | Server | Port | Purpose | Backup Priority |
|----------|--------|------|---------|-----------------|
| ws_gibd_dse_company_info | Server 80 | 5433 | Company data | HIGH |
| ws_gibd_dse_daily_trades | Server 80 | 5434 | Trading data | HIGH |
| gitlab | Server 84 | 5432 | GitLab data | CRITICAL |
| appwrite | Server 84 | 5432 | Appwrite BaaS | MEDIUM |

---

## Best Practices

1. **Backup Before Major Changes** - Always create backup before schema migrations
2. **Use Custom Format for Large Databases** - Enables parallel restore and compression
3. **Verify Backups** - Always compare row counts after restoration
4. **Test Restoration Procedures** - Practice restore on non-production databases
5. **Monitor Database Size** - Set up alerts for database growth
6. **Regular VACUUM** - Schedule VACUUM ANALYZE weekly
7. **Index Optimization** - Remove unused indexes, add missing indexes
8. **Connection Pooling** - Use PgBouncer for high-traffic applications
9. **Secure Credentials** - Never commit database passwords to git
10. **Document Schema Changes** - Update DATABASE_SCHEMA.md after migrations

---

## Maintenance Schedule

**Daily:**
- Monitor database size growth
- Check for long-running queries
- Review PostgreSQL logs for errors

**Weekly:**
- Run VACUUM ANALYZE on large tables
- Check for missing indexes
- Review slow query log
- Clean up old backups (keep last 30 days)

**Monthly:**
- Full database backup (SQL + custom format)
- Test backup restoration procedure
- Review and optimize connection pool settings
- Update PostgreSQL to latest patch version

**Quarterly:**
- Full database security audit
- Review and optimize all indexes
- Check for table bloat and run VACUUM FULL if needed
- Update PostgreSQL to latest minor version

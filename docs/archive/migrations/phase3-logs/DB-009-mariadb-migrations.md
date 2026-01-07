# DB-009: MariaDB Migrations

**Date:** 2026-01-01
**Status:** ✅ COMPLETED
**Duration:** 15 minutes
**Risk:** MEDIUM (production databases for Appwrite and Mailcow)

## Summary

Successfully migrated 2 MariaDB instances to Docker Swarm on server 80. Both databases contain production data for critical services (Appwrite backend and Mailcow email system).

## MariaDB Instances Migrated

| Instance | Database | Size | Tables | Purpose | Status |
|----------|----------|------|--------|---------|--------|
| appwrite-mariadb | appwrite | 12.73 MB | 139 | Appwrite backend database | ✅ Migrated |
| mailcowdockerized-mysql-mailcow-1 | mailcow | ~12 MB | 61 | Mailcow email system | ✅ Migrated |

## Deployment Details

### 1. appwrite-mariadb

**Old Container (Server 84):**
- Container: appwrite-mariadb
- Image: mariadb:10.11
- Database: appwrite
- User: wizardsofts
- Tables: 139

**New Service (Server 80):**
```bash
docker service create \
  --name appwrite-mariadb \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=appwrite-mariadb-data,target=/var/lib/mysql \
  --env MYSQL_ROOT_PASSWORD='W1z4rdS0fts2025Secure' \
  --env MYSQL_DATABASE=appwrite \
  --env MYSQL_USER=wizardsofts \
  --env MYSQL_PASSWORD='W1z4rdS0fts2025Secure' \
  --publish published=3307,target=3306,mode=host \
  mariadb:10.11
```

**Migration:**
- Export: mysqldump --all-databases → 5.3 MB SQL file
- Import: mysql < dump.sql
- Verification: 139 tables ✅

### 2. mailcow-mariadb

**Old Container (Server 84):**
- Container: mailcowdockerized-mysql-mailcow-1
- Image: mariadb:10.11
- Database: mailcow
- Tables: 61

**New Service (Server 80):**
```bash
docker service create \
  --name mailcow-mariadb \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=mailcow-mariadb-data,target=/var/lib/mysql \
  --env MYSQL_ROOT_PASSWORD=Agb9qiomT62Nsb3cXpLikYV3r9ij \
  --env MYSQL_DATABASE=mailcow \
  --publish published=3308,target=3306,mode=host \
  mariadb:10.11
```

**Migration:**
- Export: mysqldump --all-databases → 5.0 MB SQL file
- Import: mysql < dump.sql
- Verification: 61 tables ✅

## UFW Rules Added

- Port 3307: appwrite-mariadb
- Port 3308: mailcow-mariadb

## Verification Results

### ✅ Services Deployed
```bash
docker service ls | grep mariadb
# Result: 2/2 services with 1/1 replicas ✅
```

### ✅ Database Integrity
| Database | Old Tables | New Tables | Status |
|----------|------------|------------|--------|
| appwrite | 139 | 139 | ✅ MATCH |
| mailcow | 61 | 61 | ✅ MATCH |

### ✅ Service Health
All MariaDB containers running and accepting connections.

## Timeline

- **10:15** - Deployed appwrite-mariadb service
- **10:18** - Exported appwrite database (5.3 MB)
- **10:20** - Imported appwrite database (139 tables)
- **10:22** - Deployed mailcow-mariadb service
- **10:24** - Exported mailcow database (5.0 MB)
- **10:26** - Imported mailcow database (61 tables)
- **10:30** - ✅ All MariaDB migrations complete

**Total Duration:** 15 minutes

## Next Steps

### Application Updates
⏸️ **Update connection strings** when ready to switch:
- Appwrite: 10.0.0.84:3306 → 10.0.0.80:3307
- Mailcow: 10.0.0.84:3306 → 10.0.0.80:3308

### Old Containers
- **Keep running** for 48 hours as fallback
- Monitor application health after switch
- Remove after confirming new databases working

---

**Status:** ✅ ALL MARIADB MIGRATIONS COMPLETE
**Phase 3 Status:** ✅ ALL 9 DATABASE CONTAINERS MIGRATED

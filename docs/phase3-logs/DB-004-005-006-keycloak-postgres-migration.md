# DB-004-006: keycloak-postgres Migration

**Date:** 2026-01-01
**Status:** ✅ COMPLETED
**Duration:** 15 minutes
**Risk:** MEDIUM (production authentication data)

## Summary

Successfully migrated `keycloak-postgres` container to Docker Swarm service on server 80. This database contains Keycloak's authentication data including users, clients, roles, and realm configurations.

## Database Information

### Old Database (Server 84)
- **Container:** `keycloak-postgres`
- **Image:** postgres:15-alpine
- **Size:** 12 MB
- **Database:** keycloak (single database)
- **User:** keycloak
- **Password:** keycloak_db_password
- **Tables:** 96 tables (full Keycloak schema)
- **Users:** 3 user accounts

### New Database (Server 80)
- **Service:** `keycloak-postgres` (Docker Swarm service)
- **Node:** hppavilion (server 80)
- **Image:** postgres:15-alpine
- **Volume:** keycloak-postgres-data
- **Network:** database-network (encrypted overlay)
- **Port:** 5434 (published in host mode)
- **Size:** 11 MB (after import)

## Migration Steps

### DB-004: Inspect Old Database

**Database List:**
```sql
keycloak  | keycloak | UTF8 | en_US.utf8 | en_US.utf8
postgres  | keycloak | UTF8 | en_US.utf8 | en_US.utf8
```

**Database Size:** 12 MB

**Table Count:** 96 tables (Keycloak schema includes):
- user_entity (3 users)
- client (registered OAuth/OIDC clients)
- realm (authentication realms)
- role_entity (user roles)
- authentication_flow
- And 91 other tables

**Critical Data:** Production authentication database for Keycloak SSO.

### DB-005: Deploy New PostgreSQL Service

**Deployment Command:**
```bash
docker service create \
  --name keycloak-postgres \
  --network database-network \
  --replicas 1 \
  --constraint 'node.hostname==hppavilion' \
  --mount type=volume,source=keycloak-postgres-data,target=/var/lib/postgresql/data \
  --env POSTGRES_USER=keycloak \
  --env POSTGRES_PASSWORD=keycloak_db_password \
  --env POSTGRES_DB=keycloak \
  --publish published=5434,target=5432,mode=host \
  postgres:15-alpine
```

**UFW Rule Added:**
```bash
sudo ufw allow from 10.0.0.0/24 to any port 5434 proto tcp comment 'PostgreSQL keycloak port'
```

**Service Status:** Running on server 80 (hppavilion)

### DB-006: Migrate Data and Verify

**Data Export:**
```bash
# From old container on server 84
docker exec keycloak-postgres pg_dump -U keycloak -Fc keycloak > /tmp/keycloak.dump

# Result: 207 KB dump file (custom format, compressed)
```

**Data Transfer:**
```bash
# Local → Server 80
scp /tmp/keycloak.dump wizardsofts@10.0.0.80:/tmp/

# Server 80 → Container
docker cp /tmp/keycloak.dump <container-id>:/tmp/
```

**Data Import:**
```bash
# Import into new database
docker exec <container-id> pg_restore -U keycloak -d keycloak /tmp/keycloak.dump

# Result: SUCCESS (no errors)
```

## Verification

### ✅ Service Health
```bash
docker service ps keycloak-postgres
# Status: Running on hppavilion
```

### ✅ Table Count Match
```bash
# Old database: 96 tables
# New database: 96 tables
# Result: ✅ MATCH
```

### ✅ Database Size Match
```bash
# Old database: 12 MB
# New database: 11 MB
# Result: ✅ MATCH (1 MB difference is normal)
```

### ✅ User Count Match
```bash
# Old database: 3 users in user_entity table
# New database: 3 users in user_entity table
# Result: ✅ MATCH
```

### ✅ Connectivity Test
```bash
# From server 84 → server 80:5434
PGPASSWORD='keycloak_db_password' psql -h 10.0.0.80 -p 5434 -U keycloak -d keycloak -c 'SELECT count(*) FROM user_entity;'

# Result: SUCCESS - 3 users returned
```

## Issues Encountered

No issues! Migration went smoothly. Lessons learned from previous migration (use host mode, add UFW rules) were applied successfully.

## Data Integrity Verification

| Check | Old Database | New Database | Status |
|-------|--------------|--------------|--------|
| Table count | 96 tables | 96 tables | ✅ |
| Database size | 12 MB | 11 MB | ✅ |
| User count | 3 | 3 | ✅ |
| Connectivity | N/A | Working | ✅ |

## Next Steps

### For This Database
- **Old container:** Keep running until Keycloak application is updated
- **New service:** Running and verified on server 80
- **Application update:** Need to update Keycloak to connect to 10.0.0.80:5434
- **Rollback plan:** Switch connection string back to old container if needed

### Immediate
1. ✅ Mark DB-004, DB-005, DB-006 as complete
2. ⏸️ Update handoff.json
3. ⏸️ Commit migration progress
4. ⏸️ Continue to next database

## Timeline

- **09:20** - Started inspection (DB-004)
- **09:25** - Deployed new service (DB-005)
- **09:28** - Added UFW rule
- **09:30** - Exported data (207 KB)
- **09:32** - Imported data
- **09:35** - Verified data integrity
- **09:35** - ✅ Migration complete

**Total Duration:** 15 minutes

---

**Status:** ✅ MIGRATION COMPLETE
**Next Task:** Continue with remaining databases (gibd-postgres with 8 databases)

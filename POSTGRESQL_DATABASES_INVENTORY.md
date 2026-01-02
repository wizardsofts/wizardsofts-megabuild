# PostgreSQL Databases Inventory - All Servers

**Report Date:** 2025-12-30
**Servers Scanned:** 10.0.0.80, 10.0.0.81, 10.0.0.84

---

## Server 10.0.0.80 (Source - Original PostgreSQL Server)

### All Databases on Server 80

| Database Name | Size | Active Connections | Status | Owner |
|--------------|------|-------------------|--------|-------|
| **ws_gibd_dse_daily_trades** | 1555 MB | 10 | ✅ **MIGRATED to 84** | ws_gibd |
| **ws_gibd_news_database** | 129 MB | 0 | ⚠️ **NOT MIGRATED** | ws_gibd |
| **gitlabhq_production** | 114 MB | 39 | ⚠️ **NOT MIGRATED** | gitlab |
| **ws_daily_deen_guide** | 69 MB | 0 | ⚠️ **NOT MIGRATED** | ws_gibd |
| **ws_crypto** | 19 MB | 0 | ⚠️ **NOT MIGRATED** | postgres |
| **ws_gibd_dse_company_info** | 11 MB | 10 | ✅ **MIGRATED to 84** | ws_gibd |
| **ws_gibd** | 7.5 MB | 0 | ⚠️ **NOT MIGRATED** | ws_gibd |

**Total Size:** ~1.9 GB
**Migrated:** ~1.5 GB (2 databases)
**Not Migrated:** ~338 MB (5 databases)

---

## Server 10.0.0.81

**Status:** PostgreSQL not running / Docker not available
**Note:** Some application configs reference this server, but it appears to be misconfigured.

### Applications Pointing to 10.0.0.81
- **ws-news** ([apps/ws-news/src/main/resources/application-hp.properties:3](apps/ws-news/src/main/resources/application-hp.properties:3))
  - References: `jdbc:postgresql://10.0.0.81:5432/ws_gibd_news_database`
  - **Issue:** Database actually exists on **10.0.0.80**, not 10.0.0.81!

- **gibd-intelligence** ([apps/gibd-intelligence/config/application.properties:4](apps/gibd-intelligence/config/application.properties:4))
  - References: `db_host=10.0.0.81`

---

## Server 10.0.0.84 (Destination - New PostgreSQL Server)

### Current Databases on Server 84

| Database Name | Size | Status | Source |
|--------------|------|--------|--------|
| **ws_gibd_dse_company_info** | 11 MB | ✅ Active | Migrated from 80 |
| **ws_gibd_dse_daily_trades** | 1555 MB | ✅ Active | Migrated from 80 |

**Total Size:** ~1.5 GB

---

## Databases Requiring Migration

### 1. ws_gibd_news_database (129 MB) ⚠️ HIGH PRIORITY
**Owner:** ws_gibd
**Size:** 129 MB
**Current Location:** Server 10.0.0.80
**Used By:**
- ws-news (Spring Boot) - Currently pointing to **10.0.0.81** (incorrect!)
- gibd-intelligence (Python)
- gibd-vector-context (Python)

**Action Required:**
- Migrate database from 10.0.0.80 to 10.0.0.84
- Update ws-news config from 10.0.0.81 → 10.0.0.84
- Update gibd-intelligence config from 10.0.0.81 → 10.0.0.84

### 2. ws_daily_deen_guide (69 MB) ⚠️ MEDIUM PRIORITY
**Owner:** ws_gibd
**Size:** 69 MB
**Current Location:** Server 10.0.0.80
**Used By:**
- ws-daily-deen-web (FastAPI/Python)
  - Reference: [apps/ws-daily-deen-web/src/app/api/db.py:4](apps/ws-daily-deen-web/src/app/api/db.py:4)
  - Currently points to 10.0.0.81 (incorrect!)

**Action Required:**
- Migrate database from 10.0.0.80 to 10.0.0.84
- Update ws-daily-deen-web config from 10.0.0.81 → 10.0.0.84

### 3. gitlabhq_production (114 MB) ⚠️ SPECIAL CASE
**Owner:** gitlab
**Size:** 114 MB
**Current Location:** Server 10.0.0.80
**Active Connections:** 39 (GitLab is actively using this!)
**Used By:**
- GitLab CE instance

**Action Required:**
- **CRITICAL:** This is GitLab's internal database
- GitLab is currently running and has 39 active connections
- **Recommendation:** Keep GitLab database on server 80 OR migrate GitLab entirely
- **Do NOT migrate this database alone** - requires GitLab service migration

### 4. ws_crypto (19 MB) - UNKNOWN
**Owner:** postgres
**Size:** 19 MB
**Current Location:** Server 10.0.0.80
**Used By:** Unknown (no references found in codebase)

**Action Required:**
- Identify application using this database
- Determine if migration is needed

### 5. ws_gibd (7.5 MB) - UNKNOWN
**Owner:** ws_gibd
**Size:** 7.5 MB
**Current Location:** Server 10.0.0.80
**Used By:** Unknown (no references found in codebase)

**Action Required:**
- Identify application using this database
- Determine if migration is needed

---

## Configuration Issues Found

### Issue 1: ws-news pointing to wrong server
**Current Config:** 10.0.0.81:5432/ws_gibd_news_database
**Actual Location:** 10.0.0.80:5432/ws_gibd_news_database
**Should Be:** 10.0.0.84:5432/ws_gibd_news_database (after migration)

**Files to Update:**
- [apps/ws-news/src/main/resources/application-hp.properties](apps/ws-news/src/main/resources/application-hp.properties:3)

### Issue 2: ws-daily-deen-web pointing to wrong server
**Current Config:** 10.0.0.81:5432/ws_daily_deen_guide
**Actual Location:** 10.0.0.80:5432/ws_daily_deen_guide
**Should Be:** 10.0.0.84:5432/ws_daily_deen_guide (after migration)

**Files to Update:**
- [apps/ws-daily-deen-web/src/app/api/db.py](apps/ws-daily-deen-web/src/app/api/db.py:4)

### Issue 3: gibd-vector-context database reference
**Current Config:** 10.0.0.81
**Files to Update:**
- [apps/gibd-vector-context/.env](apps/gibd-vector-context/.env)

---

## Recommended Migration Plan

### Phase 1: Immediate (Already Complete ✅)
- [x] ws_gibd_dse_daily_trades → Server 84
- [x] ws_gibd_dse_company_info → Server 84

### Phase 2: High Priority (Recommended Next)
- [ ] **ws_gibd_news_database** (129 MB)
  - Migrate to server 84
  - Update ws-news config: 10.0.0.81 → 10.0.0.84
  - Update gibd-intelligence config
  - Update gibd-vector-context config
  - Restart affected services

- [ ] **ws_daily_deen_guide** (69 MB)
  - Migrate to server 84
  - Update ws-daily-deen-web config: 10.0.0.81 → 10.0.0.84
  - Restart affected services

### Phase 3: Low Priority / Investigation Needed
- [ ] **ws_gibd** (7.5 MB)
  - Identify application using this database
  - Decide on migration

- [ ] **ws_crypto** (19 MB)
  - Identify application using this database
  - Decide on migration

### Phase 4: GitLab (Special Handling Required)
- [ ] **gitlabhq_production** (114 MB)
  - **Option A:** Keep GitLab on server 80 (recommended for now)
  - **Option B:** Migrate entire GitLab instance to server 84 (complex)
  - **Do NOT migrate database alone**

---

## Migration Commands for Remaining Databases

### For ws_gibd_news_database

```bash
# On server 80 - Backup
ssh wizardsofts@10.0.0.80 "
docker exec gibd-postgres pg_dump -U postgres -d ws_gibd_news_database > /tmp/ws_gibd_news_database.sql
"

# Transfer to 84
scp wizardsofts@10.0.0.80:/tmp/ws_gibd_news_database.sql /tmp/
scp /tmp/ws_gibd_news_database.sql wizardsofts@10.0.0.84:/tmp/

# On server 84 - Restore
ssh wizardsofts@10.0.0.84 "
docker exec -i gibd-postgres psql -U postgres <<EOSQL
CREATE DATABASE ws_gibd_news_database OWNER gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_gibd_news_database TO gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_gibd_news_database TO ws_gibd;
EOSQL

docker exec -i gibd-postgres psql -U postgres -d ws_gibd_news_database < /tmp/ws_gibd_news_database.sql
"
```

### For ws_daily_deen_guide

```bash
# On server 80 - Backup
ssh wizardsofts@10.0.0.80 "
docker exec gibd-postgres pg_dump -U postgres -d ws_daily_deen_guide > /tmp/ws_daily_deen_guide.sql
"

# Transfer to 84
scp wizardsofts@10.0.0.80:/tmp/ws_daily_deen_guide.sql /tmp/
scp /tmp/ws_daily_deen_guide.sql wizardsofts@10.0.0.84:/tmp/

# On server 84 - Restore
ssh wizardsofts@10.0.0.84 "
docker exec -i gibd-postgres psql -U postgres <<EOSQL
CREATE DATABASE ws_daily_deen_guide OWNER gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_daily_deen_guide TO gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_daily_deen_guide TO ws_gibd;
EOSQL

docker exec -i gibd-postgres psql -U postgres -d ws_daily_deen_guide < /tmp/ws_daily_deen_guide.sql
"
```

---

## Summary

**Total Databases:** 7
**Already Migrated:** 2 (ws_gibd_dse_daily_trades, ws_gibd_dse_company_info)
**Need Migration:** 5
- **High Priority:** 2 (ws_gibd_news_database, ws_daily_deen_guide)
- **Investigation Needed:** 2 (ws_gibd, ws_crypto)
- **Special Case:** 1 (gitlabhq_production - GitLab)

**Configuration Issues Found:** 3 apps pointing to non-existent server 10.0.0.81

---

**Next Action:** Migrate ws_gibd_news_database and ws_daily_deen_guide databases, then update application configurations.

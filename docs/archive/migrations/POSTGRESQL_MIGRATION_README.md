# PostgreSQL Migration: Server 10.0.0.80 → 10.0.0.84

## 📄 Documentation Overview

This directory contains all necessary documentation and scripts for migrating the PostgreSQL database server from `10.0.0.80` to `10.0.0.84`.

## 📚 Documentation Files

### 1. **[POSTGRESQL_MIGRATION_QUICKSTART.md](POSTGRESQL_MIGRATION_QUICKSTART.md)** ⭐ START HERE
   - **Purpose**: Quick reference guide for executing the migration
   - **Audience**: Operators performing the migration
   - **Content**: Step-by-step commands with estimated time
   - **When to use**: During the actual migration execution

### 2. **[POSTGRESQL_MIGRATION_PLAN.md](POSTGRESQL_MIGRATION_PLAN.md)**
   - **Purpose**: Comprehensive migration planning document
   - **Audience**: Technical leads, DBAs, architects
   - **Content**: Detailed analysis, phases, rollback plans, verification
   - **When to use**: For planning, review, and understanding the full scope

### 3. **[POSTGRESQL_MIGRATION_README.md](POSTGRESQL_MIGRATION_README.md)** (This File)
   - **Purpose**: Index and overview of all migration resources
   - **Audience**: Everyone involved in the migration
   - **Content**: Navigation to all resources

## 🛠️ Migration Scripts

All scripts are located in the `scripts/` directory:

### 1. **[verify-postgres-migration-ready.sh](scripts/verify-postgres-migration-ready.sh)**
   - **Purpose**: Pre-flight checks before migration
   - **Usage**: `./scripts/verify-postgres-migration-ready.sh`
   - **When**: Run BEFORE starting migration
   - **Output**: Reports on SSH access, disk space, Docker, PostgreSQL status

### 2. **[migrate-postgres-backup.sh](scripts/migrate-postgres-backup.sh)**
   - **Purpose**: Create backup on server 10.0.0.80
   - **Usage**: Run on server 10.0.0.80
   - **When**: First step of migration (Phase 2)
   - **Output**: Compressed backup file with metadata

### 3. **[migrate-postgres-restore.sh](scripts/migrate-postgres-restore.sh)**
   - **Purpose**: Restore databases on server 10.0.0.84
   - **Usage**: `./migrate-postgres-restore.sh <backup-file.tar.gz>`
   - **When**: After transferring backup (Phase 3)
   - **Output**: Restored databases with verification

### 4. **[migrate-postgres-update-configs.sh](scripts/migrate-postgres-update-configs.sh)**
   - **Purpose**: Update application configs to point to new server
   - **Usage**: `./migrate-postgres-update-configs.sh`
   - **When**: After successful restore (Phase 4)
   - **Output**: Updated configuration files

## 🎯 Migration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Pre-Migration                                              │
└─────────────────────────────────────────────────────────────┘
1. Run verification script
2. Review migration plan
3. Schedule maintenance window

┌─────────────────────────────────────────────────────────────┐
│  Migration Execution (Follow QUICKSTART.md)                │
└─────────────────────────────────────────────────────────────┘
Phase 1: Setup PostgreSQL on 10.0.0.84           [  5 min]
Phase 2: Backup from 10.0.0.80                   [ 15 min]
Phase 3: Transfer backup files                   [  5 min]
Phase 4: Restore on 10.0.0.84                    [ 20 min]
Phase 5: Update configurations                   [ 10 min]
Phase 6: Rebuild & restart services              [ 20 min]
Phase 7: Testing & verification                  [ 15 min]
                                        ───────────────────────
                                        Total:   ~90 min

┌─────────────────────────────────────────────────────────────┐
│  Post-Migration                                             │
└─────────────────────────────────────────────────────────────┘
Day 1-2: Monitor application logs and database
Day 3:   Remove PostgreSQL from server 10.0.0.80
```

## 📊 Current State Summary

### Databases on 10.0.0.80
| Database Name | Used By | Size | Purpose |
|--------------|---------|------|---------|
| `ws_gibd_dse_company_info` | ws-company | ~GB | Company information |
| `ws_gibd_dse_daily_trades` | ws-trades, Python services | ~GB | Trading data |

### Applications Affected
| Application | Type | Port | Database |
|------------|------|------|----------|
| ws-company | Spring Boot | 8183 | ws_gibd_dse_company_info |
| ws-trades | Spring Boot | 8182 | ws_gibd_dse_daily_trades |
| gibd-quant-signal | Python/Flask | 5001 | ws_gibd_dse_daily_trades |
| gibd-quant-nlq | Python/Flask | 5002 | ws_gibd_dse_daily_trades |
| gibd-quant-calibration | Python/Flask | 5003 | ws_gibd_dse_daily_trades |
| gibd-quant-celery | Python/Celery | N/A | ws_gibd_dse_daily_trades |

### Configuration Files to Update
- [apps/ws-company/src/main/resources/application-hp.properties](apps/ws-company/src/main/resources/application-hp.properties:1)
- [apps/ws-trades/src/main/resources/application-hp.properties](apps/ws-trades/src/main/resources/application-hp.properties:1)
- [apps/ws-company/src/main/resources/application.properties](apps/ws-company/src/main/resources/application.properties:3) (Config server)
- [apps/ws-trades/src/main/resources/application.properties](apps/ws-trades/src/main/resources/application.properties:3) (Config server)

## ⚠️ Important Notes

### Before Migration
- [ ] Backup current data (automated by script)
- [ ] Notify stakeholders about maintenance window
- [ ] Verify server 10.0.0.84 is accessible
- [ ] Ensure adequate disk space on both servers
- [ ] Review rollback procedure

### During Migration
- [ ] Follow the QUICKSTART guide step-by-step
- [ ] Do not skip verification steps
- [ ] Monitor logs during service restarts
- [ ] Test connectivity after each phase

### After Migration
- [ ] Monitor applications for 24-48 hours
- [ ] Check database connections daily
- [ ] Verify data consistency
- [ ] Update monitoring dashboards
- [ ] Update backup scripts to use new server
- [ ] Only after 48 hours: remove old server

## 🚨 Rollback Plan

If issues occur during migration:

```bash
# 1. Revert configuration files
cd /opt/wizardsofts-megabuild
cp /tmp/config-backup-TIMESTAMP/* apps/*/src/main/resources/

# 2. Rebuild services
docker-compose build ws-company ws-trades

# 3. Restart services
docker-compose up -d ws-company ws-trades

# 4. Verify connectivity to 10.0.0.80
curl http://localhost:8183/actuator/health
curl http://localhost:8182/actuator/health
```

## ✅ Success Criteria

Migration is considered successful when:

- [ ] All databases exist on 10.0.0.84 with correct data
- [ ] All applications can connect to PostgreSQL on 10.0.0.84
- [ ] Health endpoints return 200 OK for all services
- [ ] CRUD operations work correctly
- [ ] No errors in application logs
- [ ] Performance is acceptable (comparable to old server)
- [ ] 24-48 hours of stable operation

## 📞 Troubleshooting Resources

### Common Issues

**Issue: Cannot connect to PostgreSQL on 10.0.0.84**
```bash
# Check container status
docker ps | grep postgres
docker logs gibd-postgres

# Check port accessibility
telnet 10.0.0.84 5432
nc -zv 10.0.0.84 5432
```

**Issue: Application shows database connection errors**
```bash
# Verify database credentials
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "SELECT 1;"

# Check application configuration
grep "datasource.url" apps/ws-*/src/main/resources/application-hp.properties

# Review application logs
docker-compose logs ws-company | grep -i error
```

**Issue: Data missing after migration**
```bash
# Compare row counts
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "
SELECT tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;
"

# Check backup metadata
cat /tmp/migration_metadata.txt
```

### Logs to Check
1. PostgreSQL: `docker logs gibd-postgres`
2. Applications: `docker-compose logs <service>`
3. System: `journalctl -u docker`

## 📈 Estimated Timeline

| Phase | Duration | Risk Level |
|-------|----------|------------|
| Pre-flight checks | 15 min | Low |
| Backup | 15 min | Low |
| Transfer | 5 min | Low |
| Restore | 20 min | Medium |
| Configuration | 10 min | Medium |
| Service restart | 20 min | High |
| Testing | 15 min | Medium |
| **Total Active Work** | **~2 hours** | |
| Monitoring period | 24-48 hours | Low |

## 🎓 Training Resources

For team members unfamiliar with PostgreSQL migrations:
1. Read this README first
2. Review the MIGRATION_PLAN.md for detailed context
3. Practice with the verification script
4. Familiarize yourself with rollback procedures

## 📝 Post-Migration Tasks

After successful migration:
- [ ] Update infrastructure documentation
- [ ] Update monitoring to track 10.0.0.84
- [ ] Update backup scripts
- [ ] Update disaster recovery plans
- [ ] Archive migration scripts for future reference
- [ ] Document lessons learned

## 🔐 Security Considerations

- Database password: `29Dec2#24` (from `.env`)
- SSH access: `wizardsofts` user
- Port 5432: Ensure firewall rules allow access
- Backup files: Contain sensitive data, handle securely

## 📅 Maintenance Window Recommendation

**Recommended Time**: Off-peak hours (e.g., Sunday 2:00 AM - 4:00 AM)
**Duration**: 2-3 hours
**Notification**: Send to all stakeholders 48 hours in advance

---

## 🚀 Quick Start Command

To begin the migration RIGHT NOW:

```bash
# 1. Pre-flight check
./scripts/verify-postgres-migration-ready.sh

# 2. If checks pass, follow the quick start guide
cat POSTGRESQL_MIGRATION_QUICKSTART.md

# 3. Or just start with the first step
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild/infrastructure/postgresql
docker-compose up -d
```

---

**Created**: 2025-12-30
**Last Updated**: 2025-12-30
**Version**: 1.0
**Status**: Ready for execution

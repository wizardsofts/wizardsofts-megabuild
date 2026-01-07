# PostgreSQL Migration Quick Start Guide

## 🎯 Objective
Migrate PostgreSQL from **10.0.0.80** → **10.0.0.84**

## 📋 Pre-Migration Checklist
- [ ] Read [POSTGRESQL_MIGRATION_PLAN.md](POSTGRESQL_MIGRATION_PLAN.md) for detailed information
- [ ] Ensure server 10.0.0.84 is accessible via SSH
- [ ] Ensure you have credentials: `wizardsofts` / `29Dec2#24`
- [ ] Plan a maintenance window (est. 2 hours)
- [ ] Notify stakeholders about potential downtime

## 🚀 Quick Migration Steps

### Step 1: Setup PostgreSQL on Server 84 (5 minutes)

```bash
# SSH into server 84
ssh wizardsofts@10.0.0.84

# Navigate to PostgreSQL directory
cd /opt/wizardsofts-megabuild/infrastructure/postgresql

# Start PostgreSQL
docker-compose up -d

# Verify it's running
docker-compose ps
docker-compose logs postgres

# Test connection
docker exec -it gibd-postgres psql -U postgres -c "SELECT version();"
```

### Step 2: Backup from Server 80 (15 minutes)

```bash
# Copy the backup script to server 80
scp /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/scripts/migrate-postgres-backup.sh wizardsofts@10.0.0.80:/tmp/

# SSH into server 80
ssh wizardsofts@10.0.0.80

# Run backup script
cd /tmp
chmod +x migrate-postgres-backup.sh
./migrate-postgres-backup.sh

# Note the backup filename (e.g., postgres-backup-20250101-120000.tar.gz)
```

### Step 3: Transfer Backup to Server 84 (5 minutes)

```bash
# From server 80, transfer to server 84
scp /tmp/postgres-migration-backup/postgres-backup-*.tar.gz wizardsofts@10.0.0.84:/tmp/

# OR from your local machine
# Download from server 80
scp wizardsofts@10.0.0.80:/tmp/postgres-migration-backup/postgres-backup-*.tar.gz ./

# Upload to server 84
scp postgres-backup-*.tar.gz wizardsofts@10.0.0.84:/tmp/
```

### Step 4: Restore on Server 84 (20 minutes)

```bash
# Copy restore script to server 84
scp /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/scripts/migrate-postgres-restore.sh wizardsofts@10.0.0.84:/tmp/

# SSH into server 84
ssh wizardsofts@10.0.0.84

# Run restore script
cd /tmp
chmod +x migrate-postgres-restore.sh
./migrate-postgres-restore.sh postgres-backup-YYYYMMDD-HHMMSS.tar.gz
```

### Step 5: Update Application Configurations (10 minutes)

#### Option A: Automated Update (Recommended for Server 84)

```bash
# SSH into server 84
ssh wizardsofts@10.0.0.84

# Copy update script
scp /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/scripts/migrate-postgres-update-configs.sh wizardsofts@10.0.0.84:/tmp/

cd /opt/wizardsofts-megabuild
/tmp/migrate-postgres-update-configs.sh
```

#### Option B: Manual Update (For Local Development)

Update the following files manually:

**File: `apps/ws-company/src/main/resources/application-hp.properties`**
```properties
# Change line 1:
spring.datasource.url=jdbc:postgresql://10.0.0.84:5432/ws_gibd_dse_company_info
```

**File: `apps/ws-trades/src/main/resources/application-hp.properties`**
```properties
# Change line 1:
spring.datasource.url=jdbc:postgresql://10.0.0.84:5432/ws_gibd_dse_daily_trades
```

**File: `apps/ws-company/src/main/resources/application.properties`**
```properties
# Change line 3:
spring.cloud.config.uri=http://10.0.0.84:8888
```

**File: `apps/ws-trades/src/main/resources/application.properties`**
```properties
# Change line 3:
spring.cloud.config.uri=http://10.0.0.84:8888
```

### Step 6: Rebuild and Restart Services (20 minutes)

```bash
# SSH into server 84
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild

# Rebuild Spring Boot services with new configs
docker-compose build ws-company ws-trades

# Restart services one by one and monitor
docker-compose up -d ws-company
docker-compose logs -f ws-company
# Press Ctrl+C when you see "Started" message

docker-compose up -d ws-trades
docker-compose logs -f ws-trades
# Press Ctrl+C when you see "Started" message

# Restart Python services (they use DATABASE_URL pointing to 'postgres' container, so no config change needed)
docker-compose restart gibd-quant-signal
docker-compose restart gibd-quant-nlq
docker-compose restart gibd-quant-calibration
docker-compose restart gibd-quant-celery

# Check all services are healthy
docker-compose ps
```

### Step 7: Test & Verify (15 minutes)

```bash
# Test database connectivity directly
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "SELECT COUNT(*) FROM daily_trades;"
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_company_info -c "SELECT COUNT(*) FROM company_info;"

# Test application health endpoints
curl http://localhost:8183/actuator/health  # ws-company
curl http://localhost:8182/actuator/health  # ws-trades
curl http://localhost:5001/health           # gibd-quant-signal
curl http://localhost:5002/health           # gibd-quant-nlq

# Test data retrieval
curl http://localhost:8182/api/trades
curl http://localhost:8183/api/companies
```

### Step 8: Monitor (24-48 hours)

```bash
# Watch application logs for errors
docker-compose logs -f ws-company ws-trades gibd-quant-signal gibd-quant-nlq

# Check PostgreSQL logs
docker-compose -f infrastructure/postgresql/docker-compose.yml logs -f postgres

# Monitor connections
docker exec -it gibd-postgres psql -U postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

### Step 9: Cleanup Server 80 (After 48 hours of successful operation)

```bash
# SSH into server 80
ssh wizardsofts@10.0.0.80

# Create final backup
sudo -u postgres pg_dumpall > /backup/final-backup-$(date +%Y%m%d).sql

# Stop PostgreSQL
sudo systemctl stop postgresql

# Disable from starting on boot
sudo systemctl disable postgresql

# Verify it's stopped
sudo systemctl status postgresql

# Optional: Remove PostgreSQL completely (BE CAREFUL!)
# sudo apt-get remove --purge postgresql postgresql-*
# sudo rm -rf /var/lib/postgresql
```

## ⚠️ Troubleshooting

### Issue: Cannot connect to PostgreSQL on 84
```bash
# Check if PostgreSQL container is running
docker ps | grep gibd-postgres

# Check PostgreSQL logs
docker logs gibd-postgres

# Check port is accessible
telnet 10.0.0.84 5432
# or
nc -zv 10.0.0.84 5432

# Check firewall (if needed)
sudo ufw status
```

### Issue: Application cannot connect to database
```bash
# Verify database exists
docker exec -it gibd-postgres psql -U postgres -l

# Verify user can connect
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "SELECT 1;"

# Check application logs for exact error
docker-compose logs ws-company | grep -i error
docker-compose logs ws-trades | grep -i error
```

### Issue: Data is missing after restore
```bash
# Check row counts
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"

# Compare with backup metadata
cat /tmp/migration_metadata.txt
cat /tmp/ws_gibd_dse_daily_trades_table_counts.txt
```

## 🔄 Rollback Procedure

If something goes wrong:

1. **Immediate rollback** - Change application configs back to `10.0.0.80`
2. **Rebuild** applications with old config
3. **Restart** services
4. **Keep server 80** running until issues are resolved

```bash
cd /opt/wizardsofts-megabuild

# Restore backed up configs
cp /tmp/config-backup-TIMESTAMP/* apps/ws-company/src/main/resources/
cp /tmp/config-backup-TIMESTAMP/* apps/ws-trades/src/main/resources/

# Rebuild and restart
docker-compose build ws-company ws-trades
docker-compose up -d ws-company ws-trades
```

## 📊 Success Criteria

- [ ] PostgreSQL 16 running on 10.0.0.84
- [ ] All databases restored with correct data
- [ ] ws-company connects and queries successfully
- [ ] ws-trades connects and queries successfully
- [ ] All Python services connect successfully
- [ ] Health endpoints return 200 OK
- [ ] No errors in application logs
- [ ] Data CRUD operations work
- [ ] Monitoring successful for 24-48 hours

## 📞 Support

For issues, check:
1. PostgreSQL logs: `docker-compose logs postgres`
2. Application logs: `docker-compose logs <service-name>`
3. Network connectivity: `telnet 10.0.0.84 5432`

## 📚 Related Documentation

- [Full Migration Plan](POSTGRESQL_MIGRATION_PLAN.md) - Detailed step-by-step guide
- [Backup Script](scripts/migrate-postgres-backup.sh) - Automated backup
- [Restore Script](scripts/migrate-postgres-restore.sh) - Automated restore
- [Config Update Script](scripts/migrate-postgres-update-configs.sh) - Automated config updates

---

**Last Updated:** 2025-12-30
**Estimated Total Time:** 2 hours active work + 24-48 hours monitoring

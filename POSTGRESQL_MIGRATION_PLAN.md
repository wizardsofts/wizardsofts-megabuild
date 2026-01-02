# PostgreSQL Migration Plan: Server 10.0.0.80 → 10.0.0.84

## Overview
This document outlines the migration of PostgreSQL database server from `10.0.0.80` to `10.0.0.84`.

## Current State Analysis

### Databases on 10.0.0.80
1. **ws_gibd_dse_company_info** - Company information database
2. **ws_gibd_dse_daily_trades** - Daily trades database

### Applications/Services Using These Databases

#### Spring Boot Services (connecting to 10.0.0.80)
- **ws-company** (Port 8183)
  - Database: `ws_gibd_dse_company_info`
  - Config: [apps/ws-company/src/main/resources/application-hp.properties](apps/ws-company/src/main/resources/application-hp.properties:1)

- **ws-trades** (Port 8182)
  - Database: `ws_gibd_dse_daily_trades`
  - Config: [apps/ws-trades/src/main/resources/application-hp.properties](apps/ws-trades/src/main/resources/application-hp.properties:1)

#### Python Services (using DATABASE_URL)
- **gibd-quant-signal** (Port 5001)
- **gibd-quant-nlq** (Port 5002)
- **gibd-quant-calibration** (Port 5003)
- **gibd-quant-celery** (Celery worker)

### Database Credentials
- Username: `gibd` (Python services) / `ws_gibd` (Spring Boot services)
- Password: `29Dec2#24` (from .env: `DB_PASSWORD`)
- PostgreSQL Version: 16 (current), will use 16 on new server

---

## Migration Steps

### Phase 1: Preparation (Pre-Migration)

#### 1.1. Deploy PostgreSQL to Server 10.0.0.84
```bash
# SSH into server 84
ssh wizardsofts@10.0.0.84

# Navigate to PostgreSQL infrastructure directory
cd /opt/wizardsofts-megabuild/infrastructure/postgresql

# Start PostgreSQL with docker-compose
docker-compose up -d

# Verify PostgreSQL is running
docker-compose ps
docker-compose logs postgres
```

#### 1.2. Verify PostgreSQL is accessible
```bash
# Test connection from server 84
docker exec -it gibd-postgres psql -U postgres -c "SELECT version();"

# Test connection from remote (if needed)
# Make sure port 5432 is accessible or use SSH tunnel
psql -h 10.0.0.84 -U postgres -p 5432
```

### Phase 2: Database Backup from Server 10.0.0.80

#### 2.1. Create comprehensive SQL dump
```bash
# SSH into server 80
ssh wizardsofts@10.0.0.80

# Create backup directory
mkdir -p /tmp/postgres-migration-backup
cd /tmp/postgres-migration-backup

# Dump all databases with roles and schemas
# Option 1: Dump individual databases
pg_dump -h localhost -U postgres -d ws_gibd_dse_company_info -F c -f ws_gibd_dse_company_info.dump
pg_dump -h localhost -U postgres -d ws_gibd_dse_daily_trades -F c -f ws_gibd_dse_daily_trades.dump

# Option 2: Dump as SQL (more portable)
pg_dump -h localhost -U postgres -d ws_gibd_dse_company_info > ws_gibd_dse_company_info.sql
pg_dump -h localhost -U postgres -d ws_gibd_dse_daily_trades > ws_gibd_dse_daily_trades.sql

# Dump roles and global objects
pg_dumpall -h localhost -U postgres --roles-only > roles.sql

# Compress backups
tar -czf postgres-backup-$(date +%Y%m%d-%H%M%S).tar.gz *.sql *.dump

# List the backup files
ls -lh
```

#### 2.2. Transfer backup to Server 84
```bash
# From server 80, transfer to server 84
scp /tmp/postgres-migration-backup/*.tar.gz wizardsofts@10.0.0.84:/tmp/

# Or from your local machine
scp wizardsofts@10.0.0.80:/tmp/postgres-migration-backup/*.tar.gz ./
scp *.tar.gz wizardsofts@10.0.0.84:/tmp/
```

### Phase 3: Database Restore on Server 10.0.0.84

#### 3.1. Extract and prepare backup files
```bash
# SSH into server 84
ssh wizardsofts@10.0.0.84

# Extract backup
cd /tmp
tar -xzf postgres-backup-*.tar.gz

# Copy to PostgreSQL backups volume
cp *.sql *.dump /mnt/data/docker/postgres/backups/
```

#### 3.2. Create databases and users
```bash
# Access PostgreSQL container
docker exec -it gibd-postgres psql -U postgres

# Create users
CREATE USER gibd WITH PASSWORD '29Dec2#24';
CREATE USER ws_gibd WITH PASSWORD '29Dec2#24';

# Create databases
CREATE DATABASE ws_gibd_dse_company_info OWNER gibd;
CREATE DATABASE ws_gibd_dse_daily_trades OWNER gibd;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ws_gibd_dse_company_info TO gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_gibd_dse_daily_trades TO gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_gibd_dse_company_info TO ws_gibd;
GRANT ALL PRIVILEGES ON DATABASE ws_gibd_dse_daily_trades TO ws_gibd;

# Exit psql
\q
```

#### 3.3. Restore databases
```bash
# Restore using custom format dumps
docker exec -i gibd-postgres pg_restore -U postgres -d ws_gibd_dse_company_info < /backups/ws_gibd_dse_company_info.dump
docker exec -i gibd-postgres pg_restore -U postgres -d ws_gibd_dse_daily_trades < /backups/ws_gibd_dse_daily_trades.dump

# OR restore using SQL dumps
docker exec -i gibd-postgres psql -U postgres -d ws_gibd_dse_company_info < /backups/ws_gibd_dse_company_info.sql
docker exec -i gibd-postgres psql -U postgres -d ws_gibd_dse_daily_trades < /backups/ws_gibd_dse_daily_trades.sql
```

#### 3.4. Verify restoration
```bash
# Connect to databases and check
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_company_info -c "\dt"
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "\dt"

# Check row counts for key tables
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_daily_trades -c "SELECT COUNT(*) FROM daily_trades;"
docker exec -it gibd-postgres psql -U gibd -d ws_gibd_dse_company_info -c "SELECT COUNT(*) FROM company_info;"
```

### Phase 4: Configuration Updates

#### 4.1. Update Spring Boot Application Properties

**File: apps/ws-company/src/main/resources/application-hp.properties**
```properties
# Change from:
spring.datasource.url=jdbc:postgresql://10.0.0.80:5432/ws_gibd_dse_company_info

# To:
spring.datasource.url=jdbc:postgresql://10.0.0.84:5432/ws_gibd_dse_company_info
```

**File: apps/ws-trades/src/main/resources/application-hp.properties**
```properties
# Change from:
spring.datasource.url=jdbc:postgresql://10.0.0.80:5432/ws_gibd_dse_daily_trades

# To:
spring.datasource.url=jdbc:postgresql://10.0.0.84:5432/ws_gibd_dse_daily_trades
```

#### 4.2. Update Spring Cloud Config Server
**File: apps/ws-company/src/main/resources/application.properties**
**File: apps/ws-trades/src/main/resources/application.properties**
```properties
# Change from:
spring.cloud.config.uri=http://10.0.0.80:8888

# To:
spring.cloud.config.uri=http://10.0.0.84:8888
```

#### 4.3. Docker Compose Updates
The docker-compose.yml already uses the `postgres` service name, which is correct for containerized environments. No changes needed for container-to-container communication.

However, if running services outside Docker that need to connect to PostgreSQL on 84, ensure they can reach `10.0.0.84:5432`.

### Phase 5: Testing

#### 5.1. Network Connectivity Test
```bash
# From server 84 or development machine
telnet 10.0.0.84 5432

# Or using netcat
nc -zv 10.0.0.84 5432

# Or using psql
psql -h 10.0.0.84 -U gibd -d ws_gibd_dse_daily_trades -c "SELECT 1;"
```

#### 5.2. Application Testing
```bash
# Rebuild and restart affected services on server 84
cd /opt/wizardsofts-megabuild

# Rebuild Spring Boot services
docker-compose build ws-company ws-trades

# Restart services one by one
docker-compose up -d ws-company
docker-compose logs -f ws-company

docker-compose up -d ws-trades
docker-compose logs -f ws-trades

# Restart Python services
docker-compose restart gibd-quant-signal gibd-quant-nlq gibd-quant-calibration gibd-quant-celery
```

#### 5.3. Verify Application Functionality
```bash
# Check health endpoints
curl http://localhost:8183/actuator/health  # ws-company
curl http://localhost:8182/actuator/health  # ws-trades

# Check data retrieval
curl http://localhost:8182/api/trades | jq
curl http://localhost:8183/api/companies | jq

# Check Python services
curl http://localhost:5001/health
curl http://localhost:5002/health
```

### Phase 6: Cleanup (Post-Migration)

#### 6.1. Monitor for 24-48 Hours
- Monitor application logs for any database connection errors
- Check application metrics and performance
- Verify all CRUD operations work correctly
- Ensure background jobs and scheduled tasks execute properly

#### 6.2. Remove PostgreSQL from Server 10.0.0.80
**ONLY AFTER CONFIRMING EVERYTHING WORKS ON 10.0.0.84**

```bash
# SSH into server 80
ssh wizardsofts@10.0.0.80

# Stop PostgreSQL service
sudo systemctl stop postgresql
# OR if using Docker
docker-compose -f /path/to/postgresql/docker-compose.yml down

# Create final backup before removal
pg_dumpall > /backup/final-backup-$(date +%Y%m%d).sql

# Disable PostgreSQL from starting on boot
sudo systemctl disable postgresql

# Optional: Remove PostgreSQL completely
# sudo apt-get remove --purge postgresql postgresql-*
# sudo rm -rf /var/lib/postgresql
```

#### 6.3. Update Documentation
- Update infrastructure documentation with new PostgreSQL location
- Update deployment scripts
- Update monitoring and backup scripts to point to 10.0.0.84

---

## Rollback Plan

If issues are encountered during migration:

1. **Immediate Rollback**: Change application configs back to `10.0.0.80`
2. **Restart applications** to reconnect to old database
3. **Keep server 80 running** until migration is fully verified

---

## Verification Checklist

- [ ] PostgreSQL 16 running on 10.0.0.84
- [ ] All databases created with correct owners
- [ ] All data restored and verified
- [ ] ws-company connects successfully to new server
- [ ] ws-trades connects successfully to new server
- [ ] gibd-quant-signal connects successfully
- [ ] gibd-quant-nlq connects successfully
- [ ] gibd-quant-calibration connects successfully
- [ ] gibd-quant-celery connects successfully
- [ ] All applications show healthy status
- [ ] Data CRUD operations work correctly
- [ ] Performance is acceptable
- [ ] Monitoring updated to track new server
- [ ] Backup scripts updated to backup from new server
- [ ] Server 10.0.0.80 PostgreSQL stopped and disabled

---

## Timeline

- **Phase 1-2**: 30 minutes (Setup + Backup)
- **Phase 3**: 30 minutes (Restore)
- **Phase 4**: 15 minutes (Configuration updates)
- **Phase 5**: 30 minutes (Testing)
- **Phase 6**: 48 hours monitoring + cleanup

**Total Active Work**: ~2 hours
**Total Timeline with Monitoring**: 2-3 days

---

## Contact & Support

- **Database Issues**: Check PostgreSQL logs: `docker-compose logs postgres`
- **Application Issues**: Check application logs: `docker-compose logs <service-name>`
- **Network Issues**: Verify firewall rules and port accessibility

## Next Steps

After reading this plan:
1. Review and approve the migration approach
2. Schedule a maintenance window
3. Execute Phase 1-3 (Setup, Backup, Restore)
4. Execute Phase 4-5 (Configuration updates and testing)
5. Monitor for 24-48 hours
6. Execute Phase 6 (Cleanup)

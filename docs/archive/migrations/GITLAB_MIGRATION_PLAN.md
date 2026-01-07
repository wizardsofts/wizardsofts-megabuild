# GitLab Migration Plan: Server 10.0.0.80 → 10.0.0.84

## Overview
Migrate GitLab CE instance from server 10.0.0.80 to 10.0.0.84, including the gitlabhq_production database.

## Current GitLab Setup on 10.0.0.80

### Configuration
- **Container:** gitlab/gitlab-ce:latest
- **External URL:** http://10.0.0.80
- **SSH Port:** 2222
- **Registry Port:** 5050
- **Status:** Running (healthy), Up 2 weeks

### Database Configuration
- **Using External PostgreSQL:** Yes
- **Host:** gibd-postgres (PostgreSQL 16)
- **Database:** gitlabhq_production (114 MB)
- **Active Connections:** 39
- **Owner:** gitlab user

### External Dependencies
- **PostgreSQL:** gibd-postgres container
- **Redis:** gibd-redis container

### Data Volumes (Server 80)
- `/mnt/data/docker/gitlab/config` → `/etc/gitlab`
- `/mnt/data/docker/gitlab/logs` → `/var/log/gitlab`
- `/mnt/data/docker/gitlab/data` → `/var/opt/gitlab`

## Migration Strategy

### Approach: Full GitLab Migration
Since GitLab uses external PostgreSQL and Redis, we'll:
1. Create GitLab backup on server 80
2. Migrate the gitlabhq_production database
3. Setup GitLab infrastructure on server 84
4. Restore GitLab data
5. Update configuration for new server IP
6. Test and verify

## Migration Steps

### Phase 1: Create GitLab Backup (Server 80)

```bash
# SSH into server 80
ssh wizardsofts@10.0.0.80

# Create GitLab backup using built-in backup command
docker exec -t gitlab gitlab-backup create

# Backup location: /var/opt/gitlab/backups/ (inside container)
# Maps to: /mnt/data/docker/gitlab/data/backups/ (on host)

# List backups
ls -lh /mnt/data/docker/gitlab/data/backups/
```

### Phase 2: Backup GitLab Database

```bash
# Backup gitlabhq_production database
docker exec gibd-postgres pg_dump -U gitlab -d gitlabhq_production > /tmp/gitlabhq_production.sql

# Get size
ls -lh /tmp/gitlabhq_production.sql
```

### Phase 3: Transfer Data to Server 84

```bash
# Transfer GitLab backup file
scp /mnt/data/docker/gitlab/data/backups/*_gitlab_backup.tar wizardsofts@10.0.0.84:/tmp/

# Transfer database dump
scp /tmp/gitlabhq_production.sql wizardsofts@10.0.0.84:/tmp/

# Transfer GitLab secrets (important!)
scp /mnt/data/docker/gitlab/config/gitlab-secrets.json wizardsofts@10.0.0.84:/tmp/
scp /mnt/data/docker/gitlab/config/gitlab.rb wizardsofts@10.0.0.84:/tmp/
```

### Phase 4: Setup Infrastructure on Server 84

```bash
# SSH into server 84
ssh wizardsofts@10.0.0.84

# Create GitLab directories
sudo mkdir -p /mnt/data/docker/gitlab/{config,logs,data,data/backups}
sudo chown -R 998:998 /mnt/data/docker/gitlab

# Create Redis container (if not exists)
cd /opt/wizardsofts-megabuild/infrastructure/redis
docker-compose up -d
```

### Phase 5: Restore GitLab Database on Server 84

```bash
# Create gitlab user and database on PostgreSQL
docker exec -i gibd-postgres psql -U postgres <<EOSQL
CREATE USER gitlab WITH PASSWORD '29Dec2#24';
CREATE DATABASE gitlabhq_production OWNER gitlab;
GRANT ALL PRIVILEGES ON DATABASE gitlabhq_production TO gitlab;
EOSQL

# Restore database
docker exec -i gibd-postgres psql -U postgres -d gitlabhq_production < /tmp/gitlabhq_production.sql

# Set permissions
docker exec -i gibd-postgres psql -U postgres -d gitlabhq_production <<EOSQL
GRANT ALL ON SCHEMA public TO gitlab;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gitlab;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gitlab;
EOSQL
```

### Phase 6: Setup GitLab on Server 84

```bash
# Update docker-compose.yml with new hostname
# Change: hostname: '10.0.0.80'
# To:     hostname: '10.0.0.84'
# Change: external_url 'http://10.0.0.80'
# To:     external_url 'http://10.0.0.84'

# Create .env file
cat > /opt/wizardsofts-megabuild/infrastructure/gitlab/.env <<EOF
GITLAB_DB_NAME=gitlabhq_production
GITLAB_DB_USER=gitlab
GITLAB_DB_PASSWORD=29Dec2#24
EOF

# Start GitLab (will take several minutes to initialize)
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose up -d

# Wait for GitLab to be ready (can take 5-10 minutes)
docker logs -f gitlab
```

### Phase 7: Restore GitLab Backup

```bash
# Copy backup file to GitLab container
docker cp /tmp/*_gitlab_backup.tar gitlab:/var/opt/gitlab/backups/

# Copy secrets
docker cp /tmp/gitlab-secrets.json gitlab:/etc/gitlab/
docker cp /tmp/gitlab.rb gitlab:/etc/gitlab/

# Set permissions
docker exec gitlab chown git:git /var/opt/gitlab/backups/*_gitlab_backup.tar
docker exec gitlab chmod 600 /etc/gitlab/gitlab-secrets.json

# Stop GitLab services (keep container running)
docker exec gitlab gitlab-ctl stop puma
docker exec gitlab gitlab-ctl stop sidekiq

# Restore from backup
BACKUP_NAME=$(basename /tmp/*_gitlab_backup.tar .tar | sed 's/_gitlab_backup$//')
docker exec gitlab gitlab-backup restore BACKUP=${BACKUP_NAME} force=yes

# Reconfigure GitLab
docker exec gitlab gitlab-ctl reconfigure

# Start services
docker exec gitlab gitlab-ctl start

# Check status
docker exec gitlab gitlab-rake gitlab:check SANITIZE=true
```

### Phase 8: Update DNS/Access

```bash
# Update any DNS records pointing to 10.0.0.80
# Update reverse proxy rules
# Update runner configurations
```

## Environment Variables Required

Create `.env` file in `infrastructure/gitlab/`:

```env
GITLAB_DB_NAME=gitlabhq_production
GITLAB_DB_USER=gitlab
GITLAB_DB_PASSWORD=29Dec2#24
```

## Important Notes

1. **Downtime Required:** GitLab will be unavailable during migration (estimated 30-60 minutes)
2. **Database Size:** 114 MB (relatively small, quick restore)
3. **Active Connections:** 39 connections will be terminated during migration
4. **Secrets:** Must preserve gitlab-secrets.json for encryption keys
5. **External URLs:** Update from 10.0.0.80 to 10.0.0.84

## Rollback Plan

If migration fails:

```bash
# Keep GitLab running on server 80
# Don't stop the old GitLab instance until new one is verified

# To rollback:
# 1. Stop GitLab on server 84
docker-compose -f /opt/wizardsofts-megabuild/infrastructure/gitlab/docker-compose.yml down

# 2. Verify GitLab on server 80 is still running
curl http://10.0.0.80/-/health

# 3. If needed, restart GitLab on server 80
ssh wizardsofts@10.0.0.80
docker restart gitlab
```

## Verification Checklist

After migration:
- [ ] GitLab web interface accessible at http://10.0.0.84
- [ ] Can login with existing credentials
- [ ] Projects and repositories visible
- [ ] CI/CD pipelines accessible
- [ ] Container registry accessible at 10.0.0.84:5050
- [ ] SSH access works on port 2222
- [ ] Database connections healthy
- [ ] No errors in GitLab logs

## Timeline

- **Backup creation:** 5-10 minutes
- **Data transfer:** 5-10 minutes
- **Database restore:** 5 minutes
- **GitLab setup:** 10-15 minutes
- **GitLab restore:** 10-15 minutes
- **Verification:** 10 minutes

**Total Estimated Time:** 45-65 minutes

## Post-Migration

After 48 hours of successful operation:
- Stop GitLab on server 10.0.0.80
- Archive GitLab data from server 80
- Update documentation with new URLs
- Update CI/CD configurations
- Update GitLab Runner registrations

---

**Ready to Execute:** Follow phases sequentially, verify each step before proceeding.

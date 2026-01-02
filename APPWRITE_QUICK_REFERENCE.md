# Appwrite Quick Reference Card

## Deployment

```bash
# Copy template
cp .env.appwrite.template .env.appwrite

# Generate keys and fill in .env.appwrite

# Deploy
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d

# Verify
curl https://appwrite.wizardsofts.com/v1/health | jq
```

## Default Credentials

| Component | Username | Password |
|-----------|----------|----------|
| Database | wizardsofts | W1z4rdS0fts!2025 |
| Console | admin@wizardsofts.com | (Set at first signup) |
| Domains | appwrite.wizardsofts.com, appwrite.bondwala.com | — |

## Common Commands

```bash
# View logs
docker logs appwrite -f
docker logs appwrite-worker-messaging -f

# Health checks
curl https://appwrite.wizardsofts.com/v1/health | jq
curl https://appwrite.wizardsofts.com/v1/health/db | jq
curl https://appwrite.wizardsofts.com/v1/health/cache | jq

# Resource usage
docker stats appwrite appwrite-mariadb appwrite-redis

# Backup
/opt/wizardsofts-megabuild/scripts/appwrite-backup.sh

# Restart service
docker compose -f docker-compose.appwrite.yml restart appwrite

# Stop/Start
docker compose -f docker-compose.appwrite.yml down
docker compose -f docker-compose.appwrite.yml up -d

# View database logs
docker exec appwrite-mariadb tail -f /var/log/mysql/slow.log
```

## Service Architecture

```
appwrite (4 CPU / 4GB)
├── messaging-worker (2 CPU / 1GB)  ← Push notifications
├── audits-worker (1 CPU / 512MB)
├── webhooks-worker (1 CPU / 512MB)
├── deletes-worker (1 CPU / 512MB)
├── databases-worker (1 CPU / 512MB)
├── builds-worker (1 CPU / 512MB)
├── certificates-worker (1 CPU / 512MB)
├── mails-worker (1 CPU / 512MB)
├── migrations-worker (1 CPU / 512MB)
├── maintenance (background)
├── usage (background)
├── schedule (background)
├── realtime (2 CPU / 1GB)
├── mariadb (2 CPU / 2GB)
└── redis (1 CPU / 512MB)
```

## Network

| Service | Domain | Port |
|---------|--------|------|
| API | appwrite.wizardsofts.com | 443 (HTTPS) |
| API | appwrite.bondwala.com | 443 (HTTPS) |
| Console | (same as above) | 443 (HTTPS) |
| MariaDB | appwrite-mariadb | 3306 (internal) |
| Redis | appwrite-redis | 6379 (internal) |

## Security Hardening

- ✅ Non-root users (www-data, uid:999)
- ✅ No new privileges
- ✅ Capability dropping (ALL dropped, only required added)
- ✅ Resource limits (CPU/memory)
- ✅ HTTPS/TLS with Let's Encrypt
- ✅ CORS restrictions (WizardSofts domains)
- ✅ Rate limiting (60 req/min)
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ Database user separation
- ✅ Slow query logging

## Monitoring

### Health Status
```bash
curl https://appwrite.wizardsofts.com/v1/health | jq '.status'
# Response: "pass" (healthy)
```

### Active Services
```bash
docker compose -f docker-compose.appwrite.yml ps
```

### Resource Metrics
```bash
docker stats appwrite appwrite-mariadb appwrite-redis
```

### Container Details
```bash
docker inspect appwrite | jq '.State'
```

## Troubleshooting

### Service Won't Start
```bash
docker logs appwrite 2>&1 | tail -50
# Check: Environment variables, network, dependencies
```

### 502 Bad Gateway
```bash
# Verify Appwrite is running
docker ps | grep appwrite

# Check Traefik can reach Appwrite
docker network inspect gibd-network
```

### Push Notifications Not Sending
```bash
docker logs appwrite-worker-messaging -f

# Verify messaging provider configured
curl https://appwrite.wizardsofts.com/v1/messaging/providers \
  -H "X-Appwrite-Project: PROJECT_ID" \
  -H "X-Appwrite-Key: API_KEY"
```

### Database Connection Failed
```bash
docker exec appwrite-mariadb mysqladmin ping -u root -p'PASSWORD'
```

## Backup & Restore

### Manual Backup
```bash
/opt/wizardsofts-megabuild/scripts/appwrite-backup.sh
```

### View Backups
```bash
ls -la /opt/backups/appwrite/
```

### Restore from Backup
```bash
# See docs/APPWRITE_DEPLOYMENT.md for detailed steps
```

### Setup Cron (Daily at 2 AM)
```bash
0 2 * * * /opt/wizardsofts-megabuild/scripts/appwrite-backup.sh >> /var/log/appwrite-backup.log 2>&1
```

## Scaling

### Scale Messaging Worker
```bash
docker compose -f docker-compose.appwrite.yml up -d --scale appwrite-worker-messaging=3
```

### Scale Any Worker
```bash
docker compose -f docker-compose.appwrite.yml up -d --scale appwrite-worker-webhooks=2
```

## Projects & API Keys

### Create Project (In Console)
1. Go to https://appwrite.wizardsofts.com
2. Click "Create Project"
3. Name: BondWala, GIBD, etc.
4. Create platforms (iOS, Android, Web)

### Create API Key (In Console)
```
Project Settings → API Keys → Create Key
- Name: bondwala-server
- Scopes: messaging.*, database.*
- Copy key and use in backend
```

### Project Isolation
- Each project has separate API keys
- Each project can have separate databases
- Messaging topics isolated per project
- Multi-tenant ready

## Compliance Checklist

- [x] Non-root execution
- [x] Capability dropping
- [x] No privilege escalation
- [x] HTTPS/TLS
- [x] CORS restrictions
- [x] Security headers
- [x] Rate limiting
- [x] Database separation
- [x] Query logging
- [x] Resource limits
- [x] Health checks
- [x] Automated backups
- [x] Audit logging

## File Locations

| Item | Location |
|------|----------|
| Docker Compose | `docker-compose.appwrite.yml` |
| Environment Config | `.env.appwrite` |
| Backups | `/opt/backups/appwrite/` |
| Backup Script | `scripts/appwrite-backup.sh` |
| Deployment Guide | `docs/APPWRITE_DEPLOYMENT.md` |
| Security Guide | `docs/APPWRITE_HARDENING.md` |
| Traefik Config | `traefik/dynamic_conf.yml` |

## Useful URLs

| URL | Purpose |
|-----|---------|
| https://appwrite.wizardsofts.com | Appwrite Console |
| https://appwrite.wizardsofts.com/v1/health | Health Check |
| https://appwrite.wizardsofts.com/v1/health/db | Database Health |
| https://appwrite.wizardsofts.com/v1/health/cache | Cache Health |
| https://appwrite.wizardsofts.com/v1/health/queue | Queue Health |

## Emergency Contacts

- **Tech Lead:** tech@wizardsofts.com
- **System Admin:** admin@wizardsofts.com
- **Appwrite Support:** https://appwrite.io/support

## Further Reading

- [APPWRITE_DEPLOYMENT.md](docs/APPWRITE_DEPLOYMENT.md) - Detailed deployment guide
- [APPWRITE_HARDENING.md](docs/APPWRITE_HARDENING.md) - Security hardening details
- [APPWRITE_DEPLOYMENT_SUMMARY.md](APPWRITE_DEPLOYMENT_SUMMARY.md) - Complete summary
- [Appwrite Docs](https://appwrite.io/docs)

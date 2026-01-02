# Appwrite Quick Start Guide

## Deploy in 5 Minutes

### 1. Copy Configuration
```bash
cp .env.appwrite.template .env.appwrite
```

### 2. Verify Environment Variables
```bash
# Edit .env.appwrite and confirm these settings:
_APP_DOMAIN=appwrite.bondwala.com
_APP_DB_PASS=W1z4rdS0fts!2025
_APP_DB_ROOT_PASS=W1z4rdS0fts!2025
_APP_CONSOLE_WHITELIST_EMAILS=admin@wizardsofts.com
```

### 3. Create Networks
```bash
docker network create gibd-network
docker network create traefik-public
```

### 4. Deploy
```bash
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d
```

### 5. Wait for Startup
```bash
# Check status (wait 2-3 minutes for all services to be healthy)
docker compose -f docker-compose.appwrite.yml ps

# Check health
curl https://appwrite.bondwala.com/v1/health
```

### 6. Access Console
Navigate to: **https://appwrite.bondwala.com**
Sign up with: **admin@wizardsofts.com**

---

## Essential Commands

### Monitor Services
```bash
# View all running services
docker compose -f docker-compose.appwrite.yml ps

# Watch logs
docker logs appwrite -f --tail 50
docker logs appwrite-worker-messaging -f --tail 50

# Check resource usage
docker stats appwrite appwrite-mariadb appwrite-redis
```

### Restart Services
```bash
# Restart one
docker compose -f docker-compose.appwrite.yml restart appwrite

# Restart all
docker compose -f docker-compose.appwrite.yml restart

# Full restart (slow)
docker compose -f docker-compose.appwrite.yml down
docker compose -f docker-compose.appwrite.yml up -d
```

### Backup & Restore
```bash
# Create backup
./scripts/appwrite-backup.sh

# View backups
ls -la /opt/backups/appwrite/

# Latest backup
ls -la /opt/backups/appwrite/latest/
```

### Stop Services
```bash
# Graceful stop
docker compose -f docker-compose.appwrite.yml stop

# Force stop
docker compose -f docker-compose.appwrite.yml kill

# Remove containers (keeps volumes/data)
docker compose -f docker-compose.appwrite.yml down
```

---

## Project Setup Checklist

After accessing console:

- [ ] Create project: "BondWala"
- [ ] Add platforms:
  - [ ] iOS: `com.wizardsofts.bondwala`
  - [ ] Android: `com.wizardsofts.bondwala`
  - [ ] Web: `*.bondwala.com`
- [ ] Create topics:
  - [ ] `all-users` - All Users
  - [ ] `win-alerts` - Win Alerts
  - [ ] `draw-updates` - Draw Updates
  - [ ] `reminders` - Reminders
- [ ] Configure providers:
  - [ ] APNs (iOS)
  - [ ] FCM (Android)
- [ ] Generate API keys:
  - [ ] Server key (backend)
  - [ ] Client key (mobile)
  - [ ] Admin key (operations)

---

## Test Push Notification

```bash
curl -X POST https://appwrite.bondwala.com/v1/messaging/messages/push \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: <project-id>" \
  -H "X-Appwrite-Key: <server-api-key>" \
  -d '{
    "messageId": "test-001",
    "title": "Test Notification",
    "body": "Appwrite is working!",
    "topics": ["all-users"]
  }'
```

Expected response:
```json
{
  "$id": "test-001",
  "status": "processing"
}
```

---

## Troubleshooting

### Container Won't Start
```bash
docker logs appwrite 2>&1 | grep -i error
# Common issues: env vars, network, dependencies
```

### 502 Bad Gateway
```bash
# Verify Traefik can reach Appwrite
curl http://appwrite:80/v1/health
# Check network: docker network inspect gibd-network
```

### Database Connection Failed
```bash
docker logs appwrite-mariadb
docker exec appwrite-mariadb mysqladmin ping -u root -p'W1z4rdS0fts!2025'
```

### Services Slow
```bash
# Check resource usage
docker stats appwrite

# Check if disk full
df -h /
```

---

## Security Checklist

- [ ] Changed database passwords
- [ ] Changed console admin password
- [ ] Generated API keys (not using default admin key)
- [ ] Enabled audit logging
- [ ] Configured SMTP for emails
- [ ] Restricted console access (IP whitelist if possible)
- [ ] Scheduled automated backups
- [ ] Tested backup restoration
- [ ] Updated DNS records
- [ ] Verified HTTPS/TLS working

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Connection refused | Wait for services to start (2-3 min) |
| 502 Bad Gateway | Restart Traefik or check service health |
| Database errors | Check .env vars, verify MariaDB is running |
| Push not sending | Verify providers configured, check worker logs |
| Slow responses | Check CPU/Memory usage, scale workers |
| SSL certificate errors | Check DNS resolution, wait for cert issuance |

---

## Useful Documentation

- **Full Setup:** [APPWRITE_DEPLOYMENT.md](docs/APPWRITE_DEPLOYMENT.md)
- **Security:** [APPWRITE_SECURITY.md](docs/APPWRITE_SECURITY.md)
- **Complete Summary:** [APPWRITE_SETUP_SUMMARY.md](APPWRITE_SETUP_SUMMARY.md)
- **Official Docs:** https://appwrite.io/docs

---

## Getting Help

1. Check logs: `docker logs appwrite`
2. Read the full deployment guide
3. Contact: tech@wizardsofts.com

---

**Version:** 1.0 | **Updated:** 2025-12-27

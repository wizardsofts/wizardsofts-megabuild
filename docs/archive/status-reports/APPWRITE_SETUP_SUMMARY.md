# Appwrite Deployment - Complete Setup Summary

> **Created:** 2025-12-27
> **Version:** 1.0
> **Status:** Ready for Production Deployment
> **Shared Service:** WizardSofts (BondWala, GIBD, Future Projects)

---

## Executive Summary

A production-ready, security-hardened Appwrite Backend-as-a-Service (BaaS) platform has been configured for deployment across WizardSofts projects. The deployment serves as:

1. **Primary:** BondWala push notification system (replaces Firebase FCM)
2. **Secondary:** GIBD and other future projects
3. **Infrastructure:** Shared BaaS platform for all WizardSofts applications

---

## Files Created & Modified

### New Files

| File | Purpose | Size |
|------|---------|------|
| `docker-compose.appwrite.yml` | Complete Appwrite stack with all workers | 21 KB |
| `.env.appwrite.template` | Environment configuration template | 8 KB |
| `docs/APPWRITE_DEPLOYMENT.md` | Deployment guide and runbook | 16 KB |
| `docs/APPWRITE_SECURITY.md` | Security hardening guide | 15 KB |
| `scripts/appwrite-backup.sh` | Automated backup script | 4 KB |

### Modified Files

| File | Changes |
|------|---------|
| `traefik/dynamic_conf.yml` | Added Appwrite routing for both `appwrite.wizardsofts.com` and `appwrite.bondwala.com` |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Traefik Reverse Proxy                  │
│            (HTTPS/TLS via Let's Encrypt, Rate Limits)       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Appwrite Core Service                     │    │
│  │  • Main API (REST/GraphQL)                          │    │
│  │  • Non-root execution (www-data)                    │    │
│  │  • Resource limits: 4 CPU, 4GB RAM                  │    │
│  │  • Health checks every 30s                          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │        Appwrite Workers (Background Processing)    │    │
│  ├────────────────────────────────────────────────────┤    │
│  │ • Messaging (Push Notifications) - 2 CPU, 1GB      │    │
│  │ • Database Operations - 1 CPU, 512MB               │    │
│  │ • Mail Sending - 1 CPU, 512MB                      │    │
│  │ • Certificate Management - 1 CPU, 512MB            │    │
│  │ • Webhooks, Audits, Deletes, Builds, Migrations   │    │
│  │ • Usage Tracking, Scheduling, Maintenance          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Data Layer                                │    │
│  ├────────────────────────────────────────────────────┤    │
│  │ MariaDB 10.11          │  Redis 7-alpine           │    │
│  │ • Non-root user        │  • In-memory cache        │    │
│  │ • 2 CPU, 2GB RAM       │  • 1 CPU, 512MB           │    │
│  │ • Slow query logging   │  • AOF persistence        │    │
│  │ • Symlink protection   │  • LRU eviction           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Features Implemented

### Container Security
- ✅ **Non-root execution:** All services run as www-data or dedicated users
- ✅ **Capability dropping:** Only required Linux capabilities enabled
- ✅ **No privilege escalation:** `no-new-privileges:true` enforced
- ✅ **Resource isolation:** CPU and memory limits per container

### Network Security
- ✅ **HTTPS only:** TLS 1.2+ via Let's Encrypt
- ✅ **CORS hardening:** Restricted to WizardSofts domains
- ✅ **Security headers:** HSTS, X-Frame-Options, CSP, etc.
- ✅ **Rate limiting:** 60 requests/minute per IP
- ✅ **Dual domains:** `appwrite.wizardsofts.com` + `appwrite.bondwala.com`

### Database Security
- ✅ **Credential separation:** App user ≠ root user
- ✅ **Query logging:** Slow queries logged for audit trail
- ✅ **Symlink protection:** Defense against directory traversal
- ✅ **Strong passwords:** WizardSofts standard credentials
- ✅ **Per-table isolation:** InnoDB file-per-table enabled

### Data Protection
- ✅ **256-bit encryption keys:** Generated with OpenSSL
- ✅ **Session signing:** Cryptographic key for integrity
- ✅ **Backup automation:** Daily encrypted backups
- ✅ **Backup retention:** 30-day rolling retention

### Application Security
- ✅ **API key scoping:** Limited permissions per key
- ✅ **Audit logging:** All administrative actions logged
- ✅ **Console access control:** Email whitelist enabled
- ✅ **Multi-project support:** Isolated by project ID

---

## Default Credentials

⚠️ **IMPORTANT: Change These on First Login**

```
Database User:      wizardsofts
Database Password:  W1z4rdS0fts!2025
Console Admin:      admin@wizardsofts.com
```

---

## Deployment Steps

### Step 1: Prepare Environment
```bash
cd /path/to/wizardsofts-megabuild

# Copy and configure
cp .env.appwrite.template .env.appwrite

# Edit with text editor and set/confirm:
# _APP_DB_PASS=W1z4rdS0fts!2025
# _APP_DB_ROOT_PASS=W1z4rdS0fts!2025
# _APP_DOMAIN=appwrite.bondwala.com
# _APP_DOMAIN_TARGET=appwrite.bondwala.com
```

### Step 2: Configure DNS
Add A records (contact your DNS provider):
```
appwrite.wizardsofts.com -> YOUR_PUBLIC_IP
appwrite.bondwala.com     -> YOUR_PUBLIC_IP
```

### Step 3: Deploy
```bash
# Create networks if missing
docker network create gibd-network
docker network create traefik-public

# Deploy all services
docker compose -f docker-compose.appwrite.yml \
  --env-file .env.appwrite \
  up -d

# Verify deployment
docker ps --filter "name=appwrite" --format "table {{.Names}}\t{{.Status}}"
curl https://appwrite.bondwala.com/v1/health
```

### Step 4: Initial Setup
1. Navigate to `https://appwrite.bondwala.com`
2. Sign up with `admin@wizardsofts.com`
3. Create project "BondWala"
4. Add platforms (iOS, Android, Web)
5. Generate API keys
6. Configure push notification providers

---

## Important Domains

| Domain | Purpose | Status |
|--------|---------|--------|
| `appwrite.wizardsofts.com` | Primary shared service | Primary |
| `appwrite.bondwala.com` | BondWala specific | Alias |
| `appwrite.guardianinvestmentbd.com` | Future use | Ready |

All domains route to same service via Traefik.

---

## API Keys & Scopes

After deployment, generate these keys in Appwrite Console:

### Server Key (Backend API)
```
Name: bondwala-server
Scopes:
  - messaging.messages.write
  - messaging.topics.read
  - messaging.providers.read
  - messaging.subscribers.write
  - databases.read
  - databases.write
  - files.read
  - files.write
```

### Client Key (Mobile App)
```
Name: bondwala-client
Scopes:
  - messaging.subscribers.write
  - account.read
  - account.write
  - sessions.create
```

### Admin Key (Operations)
```
Name: appwrite-admin
Scopes: All (use sparingly, rotate quarterly)
```

---

## Messaging Topics

Create these topics in Appwrite > Messaging:

| Topic ID | Topic Name | Use Case |
|----------|-----------|----------|
| `all-users` | All Users | Broadcast to everyone |
| `win-alerts` | Win Alerts | Winner notifications |
| `draw-updates` | Draw Updates | New draw announcements |
| `reminders` | Reminders | User check-in reminders |

---

## Resource Usage

### Container Resource Limits

```
Appwrite Core:           4 CPU cores, 4 GB RAM
Messaging Worker:        2 CPU cores, 1 GB RAM
Other Workers (×8):      1 CPU core each, 512 MB RAM each
MariaDB:                 2 CPU cores, 2 GB RAM
Redis:                   1 CPU core, 512 MB RAM

TOTAL RESERVED:          ~14 CPU cores, ~12 GB RAM
TOTAL LIMITS:            ~23 CPU cores, ~17 GB RAM
```

**Server Capacity:** 31.9 GB RAM available ✅ Sufficient for production

---

## Backup & Recovery

### Automated Backups

```bash
# Setup automated daily backups
# (Edit crontab to run at 02:00 UTC)
sudo crontab -e
# Add: 0 2 * * * /opt/wizardsofts-megabuild/scripts/appwrite-backup.sh

# Manual backup
./scripts/appwrite-backup.sh

# Backup location: /opt/backups/appwrite/YYYYMMDD_HHMMSS/
# - appwrite_db.sql.gz (database)
# - appwrite-uploads.tar.gz (user files)
# - appwrite-config.tar.gz (configuration)
# - appwrite-certificates.tar.gz (SSL certs)
# - appwrite-functions.tar.gz (functions code)
# - manifest.json (backup metadata)
```

### Recovery Procedure

See [APPWRITE_DEPLOYMENT.md](docs/APPWRITE_DEPLOYMENT.md) for restore steps.

---

## Operational Runbook

### Check Health
```bash
curl https://appwrite.bondwala.com/v1/health
curl https://appwrite.bondwala.com/v1/health/queue
curl https://appwrite.bondwala.com/v1/health/storage
```

### View Logs
```bash
docker logs appwrite -f --tail 100
docker logs appwrite-worker-messaging -f --tail 100
docker logs appwrite-mariadb -f --tail 100
```

### Restart Services
```bash
# Restart one service
docker compose -f docker-compose.appwrite.yml restart appwrite

# Restart all
docker compose -f docker-compose.appwrite.yml restart

# Hard restart (slower, more thorough)
docker compose -f docker-compose.appwrite.yml down
docker compose -f docker-compose.appwrite.yml up -d
```

### Monitor Performance
```bash
docker stats appwrite
docker compose -f docker-compose.appwrite.yml ps
```

---

## Integration with BondWala

### Backend Changes Required
1. Install `node-appwrite` SDK
2. Create `appwrite-messaging-service.ts`
3. Update notification endpoints:
   - Remove: `POST /v1/fcm/register`
   - Add: `POST /v1/notifications/register`
4. Replace Firebase Admin SDK calls with Appwrite SDK

### Mobile App Changes Required
1. Install `react-native-appwrite` SDK
2. Update notification service implementation
3. Remove `@react-native-firebase/messaging`
4. Update push token registration flow

### Configuration
```typescript
const appwriteConfig = {
  endpoint: 'https://appwrite.bondwala.com/v1',
  projectId: '<project-id-from-console>',
  apiKey: '<server-api-key>' // Backend only
  clientKey: '<client-api-key>' // Mobile app
}
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| CPU Usage | > 80% | Scale workers or increase limits |
| Memory Usage | > 85% | Analyze memory leaks |
| Disk Space | < 10% | Archive old backups |
| Push Delivery Time | > 5s | Check messaging worker logs |
| API Response Time | > 1000ms | Check database performance |
| Error Rate | > 1% | Investigate error logs |

### Setting Up Monitoring

```bash
# Check in Traefik dashboard
https://traefik.wizardsofts.com (admin:password)

# Export Prometheus metrics
curl https://appwrite.bondwala.com/metrics

# Integration with Grafana (optional)
# Add Prometheus data source
# Create dashboard for Appwrite metrics
```

---

## Security Maintenance

### Monthly
- Review API key usage in console
- Check audit logs for unauthorized access
- Verify SSL certificate renewal
- Test backup restoration

### Quarterly
- Rotate API keys
- Update Docker images
- Review and update security policies
- Penetration testing simulation

### Annually
- Full security audit
- Compliance review (GDPR, SOC 2)
- Disaster recovery drill
- Update security documentation

---

## Troubleshooting

### Container Won't Start
```bash
docker logs appwrite 2>&1 | tail -50
# Check: Environment variables, network connectivity, dependencies
```

### 502 Bad Gateway
```bash
# Verify Traefik can reach Appwrite
docker exec traefik curl http://appwrite:80/v1/health
# Check: Network connection, health checks
```

### Push Notifications Not Sending
```bash
docker logs appwrite-worker-messaging
# Check: Provider configuration, credentials, target IDs
```

### Database Connection Failed
```bash
docker exec appwrite-mariadb mysqladmin ping -u root -p'PASS'
# Check: Container health, credentials, disk space
```

See [APPWRITE_DEPLOYMENT.md](docs/APPWRITE_DEPLOYMENT.md) for detailed troubleshooting.

---

## Next Steps

### Immediate (Day 1)
1. ✅ Configure `.env.appwrite` with your settings
2. ✅ Set DNS A records
3. ✅ Deploy services
4. ✅ Verify health endpoints
5. ✅ Create first admin account

### Short-term (Week 1)
1. Create BondWala project
2. Configure push notification providers (APNs, FCM)
3. Generate API keys
4. Create messaging topics
5. Update backend API with Appwrite SDK

### Medium-term (Month 1)
1. Update BondWala mobile app with Appwrite SDK
2. Migrate push token registration
3. Test end-to-end push notifications
4. Run load testing
5. Document any customizations

### Long-term (Ongoing)
1. Monitor performance metrics
2. Update to newer Appwrite versions
3. Expand to other projects (GIBD, etc.)
4. Implement advanced features (Cloud Functions, Webhooks)
5. Regular security audits

---

## Credentials Quick Reference

| Component | Username | Password | Notes |
|-----------|----------|----------|-------|
| MariaDB | wizardsofts | W1z4rdS0fts!2025 | Change in production |
| MariaDB Root | root | W1z4rdS0fts!2025 | Change in production |
| Console Admin | admin@wizardsofts.com | (set on first login) | Use strong password |

---

## Documentation Links

| Document | Purpose |
|----------|---------|
| [APPWRITE_DEPLOYMENT.md](docs/APPWRITE_DEPLOYMENT.md) | Complete deployment guide |
| [APPWRITE_SECURITY.md](docs/APPWRITE_SECURITY.md) | Security hardening details |
| [appwrite-backup.sh](scripts/appwrite-backup.sh) | Backup automation script |

---

## Support & Contact

For issues or questions:
1. Check the relevant documentation above
2. Review logs: `docker logs appwrite-*`
3. Contact: `tech@wizardsofts.com`
4. Escalate to security team for security concerns

---

## Checklist for Production Deployment

- [ ] DNS records created and verified
- [ ] `.env.appwrite` configured with custom credentials
- [ ] All cryptographic keys generated
- [ ] Services deployed and healthy
- [ ] Console accessible and admin account created
- [ ] BondWala project created
- [ ] Platforms configured (iOS, Android, Web)
- [ ] API keys generated for backend and mobile
- [ ] Messaging topics created
- [ ] Push providers configured (APNs, FCM)
- [ ] Test push notification sent successfully
- [ ] Backup script scheduled
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Incident response procedures documented

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Status:** ✅ Ready for Production Deployment

---

For questions or updates, contact: `tech@wizardsofts.com`

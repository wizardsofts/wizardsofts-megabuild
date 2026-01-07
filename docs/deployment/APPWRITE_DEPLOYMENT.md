# Appwrite Deployment Guide for WizardSofts

> **Version:** 2.0
> **Appwrite Version:** 1.8.1
> **Last Updated:** 2026-01-07
> **Status:** Deployed & Operational
> **Shared Service:** BondWala, GIBD, and future WizardSofts projects

**Consolidated Guide** - This document combines deployment, security hardening, quick start, and fresh install instructions.

**Quick Links:**
- [Quick Start](#quick-start-5-minutes) - Deploy in 5 minutes
- [Full Deployment](#deployment-steps) - Complete step-by-step
- [Security Hardening](#security-hardening-details) - Enterprise-grade security
- [Operations](#operations-runbook) - Day-to-day management
- [Troubleshooting](#troubleshooting) - Common issues

---

## Overview

This document provides complete deployment instructions for the self-hosted Appwrite Backend-as-a-Service (BaaS) platform serving all WizardSofts projects, starting with BondWala's push notification system replacing Firebase Cloud Messaging (FCM).

---

## Quick Start (5 Minutes)

For experienced users who want to deploy quickly:

```bash
# 1. Copy configuration
cp .env.appwrite.template .env.appwrite

# 2. Edit environment (set domain and passwords)
# _APP_DOMAIN=appwrite.wizardsofts.com
# _APP_DB_PASS=<your-secure-password>
# _APP_CONSOLE_WHITELIST_EMAILS=admin@wizardsofts.com

# 3. Create networks
docker network create gibd-network
docker network create traefik-public

# 4. Deploy
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d

# 5. Verify (wait 2-3 minutes for startup)
curl https://appwrite.wizardsofts.com/v1/health

# 6. Access console
# Navigate to: https://appwrite.wizardsofts.com
# Sign up with whitelisted email
```

**Essential Commands:**
```bash
# View logs
docker logs appwrite -f --tail 50

# Health checks
curl https://appwrite.wizardsofts.com/v1/health | jq

# Restart
docker compose -f docker-compose.appwrite.yml restart appwrite

# Stop/Start
docker compose -f docker-compose.appwrite.yml down
docker compose -f docker-compose.appwrite.yml up -d
```

For detailed setup, continue to [Full Deployment](#deployment-steps).

**Service Applies To:**
- BondWala (primary: push notifications)
- GIBD Quant (future integrations)
- Additional WizardSofts projects

### Architecture

```
                                    +------------------+
                                    |   Mobile Apps    |
                                    | (iOS / Android)  |
                                    +--------+---------+
                                             |
                                             v
+------------------+              +---------------------+
|   DNS Record     |              |      Traefik       |
| appwrite.        | -----------> |  (Reverse Proxy)   |
| bondwala.com     |   HTTPS/443  |   Let's Encrypt    |
+------------------+              +----------+----------+
                                             |
                    +------------------------+------------------------+
                    |                        |                        |
                    v                        v                        v
         +------------------+     +--------------------+    +------------------+
         |    Appwrite      |     | Appwrite Realtime  |    |  Appwrite Workers|
         |   (Main API)     |     |   (WebSocket)      |    |   (Background)   |
         +--------+---------+     +--------------------+    +------------------+
                  |                                                   |
                  +---------------------------------------------------+
                  |                        |
                  v                        v
         +------------------+     +------------------+
         |     MariaDB      |     |      Redis       |
         |   (Database)     |     |     (Cache)      |
         +------------------+     +------------------+
```

---

## Prerequisites

### Server Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 50 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 LTS |
| Docker | 24.0+ | 27.0+ |
| Docker Compose | v2.20+ | v2.30+ |

### Current Server Status

The HP Server at `10.0.0.80` meets all requirements:
- **RAM:** 31.9 GB
- **Docker:** 27.5.1
- **OS:** Ubuntu 24.04 (Noble)

### DNS Configuration

Add the following A records to your DNS provider:

```
Type: A
Host: appwrite (primary domain)
Value: <YOUR_SERVER_PUBLIC_IP>
TTL: 300 (or Auto)

Type: A
Host: appwrite.bondwala.com (project subdomain)
Value: <YOUR_SERVER_PUBLIC_IP>
TTL: 300 (or Auto)
```

For HostGator DNS or Cloudflare:
```
appwrite.wizardsofts.com -> A -> YOUR_PUBLIC_IP
appwrite.bondwala.com -> A -> YOUR_PUBLIC_IP
```

---

## Security Hardening Details

The Appwrite deployment includes enterprise-grade security:

### Container Security

- **No Root Execution:** All services run as non-root users (www-data, uid:999)
- **Capability Dropping:** Unnecessary Linux capabilities dropped, only required ones enabled
- **No New Privileges:** `no-new-privileges:true` enforced across all containers
- **Read-Only Filesystems:** Where applicable for immutable components

### Network Security

- **HTTPS Only:** TLS/SSL enforced via Let's Encrypt
- **CORS Headers:** Restricted to WizardSofts domains only
- **Security Headers:** HSTS, X-Frame-Options, X-Content-Type-Options, CSP
- **Rate Limiting:** 60 requests per minute per IP (configurable)

### Database Security

- **Separate Credentials:** Database user != root user
- **Strong Passwords:** Database passwords use WizardSofts standard credentials
- **Query Logging:** Slow query logging enabled (>2s queries logged)
- **Symbolic Links Disabled:** Protection against directory traversal
- **External Locking Disabled:** Performance and security optimization

### Resource Limits

Container resource constraints prevent runaway processes:

| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| Appwrite Core | 4 cores | 4 GB |
| Messaging Worker | 2 cores | 1 GB |
| Other Workers | 1 core | 512 MB |
| MariaDB | 2 cores | 2 GB |
| Redis | 1 core | 512 MB |

### Credentials

**Default Credentials (change on first login):**
- **Database Username:** `wizardsofts`
- **Database Password:** `W1z4rdS0fts!2025`
- **Console Admin Email:** `admin@wizardsofts.com`

**Critical Actions:**
1. Change database password after initial setup
2. Create unique API keys for each project
3. Restrict console access by IP in production
4. Enable audit logging for compliance

---

## Deployment Steps

### Step 1: Prepare Environment File

```bash
# Navigate to project root
cd /path/to/wizardsofts-megabuild

# Copy template
cp .env.appwrite.template .env.appwrite

# Generate security keys
echo "_APP_OPENSSL_KEY_V1=$(openssl rand -hex 32)" >> .env.appwrite.keys
echo "_APP_SECRET=$(openssl rand -hex 32)" >> .env.appwrite.keys
echo "_APP_EXECUTOR_SECRET=$(openssl rand -hex 32)" >> .env.appwrite.keys
echo "_APP_DB_PASS=$(openssl rand -base64 24)" >> .env.appwrite.keys
echo "_APP_DB_ROOT_PASS=$(openssl rand -base64 24)" >> .env.appwrite.keys

# Review generated keys
cat .env.appwrite.keys

# Copy keys to .env.appwrite (manually for security)
```

### Step 2: Configure Environment

Edit `.env.appwrite` with the generated keys:

```bash
# Security Keys (from Step 1)
_APP_OPENSSL_KEY_V1=<generated-key>
_APP_SECRET=<generated-key>
_APP_DB_PASS=<generated-password>
_APP_DB_ROOT_PASS=<generated-password>

# Domain
_APP_DOMAIN=appwrite.bondwala.com
_APP_DOMAIN_TARGET=appwrite.bondwala.com

# Console Access
_APP_CONSOLE_WHITELIST_EMAILS=admin@wizardsofts.com
```

### Step 3: Create Docker Network (if not exists)

```bash
# Check if network exists
docker network ls | grep gibd-network

# Create if needed
docker network create gibd-network

# Verify traefik-public network
docker network ls | grep traefik-public

# Create if needed
docker network create traefik-public
```

### Step 4: Deploy Appwrite

```bash
# Pull images first (reduces downtime)
docker compose -f docker-compose.appwrite.yml pull

# Start all services
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d

# Or with profile
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite --profile appwrite up -d
```

### Step 5: Verify Deployment

```bash
# Check all containers are running
docker ps --filter "name=appwrite" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check health
curl -s https://appwrite.bondwala.com/v1/health | jq

# Expected response:
# {
#   "name": "database",
#   "status": "pass"
# }

# Check logs if issues
docker logs appwrite -f --tail 100
docker logs appwrite-worker-messaging -f --tail 100
```

### Step 6: Create Admin Account

1. Navigate to `https://appwrite.bondwala.com`
2. Click "Sign Up"
3. Use email from `_APP_CONSOLE_WHITELIST_EMAILS`
4. Complete registration

---

## Post-Deployment Configuration

### Create BondWala Project

1. Log into Appwrite Console
2. Click "Create Project"
3. Configure:
   - **Name:** BondWala
   - **Project ID:** `bondwala` (optional custom ID)
   - **Organization:** WizardSofts

### Add Platforms

In Project Settings > Platforms:

| Platform | Type | Bundle ID / Hostname |
|----------|------|---------------------|
| iOS | Apple | `com.wizardsofts.bondwala` |
| Android | Android | `com.wizardsofts.bondwala` |
| Web | Web | `*.bondwala.com` |

### Configure Messaging

#### 1. Create APNs Provider (iOS)

Navigate to: Messaging > Providers > Create Provider

```yaml
Name: bondwala-apns
Type: APNs
Authentication: Token (p8 key)
Environment: Production
Bundle ID: com.wizardsofts.bondwala

# Credentials (to be uploaded):
# - Team ID: <your-team-id>
# - Key ID: <your-key-id>
# - Auth Key: <upload .p8 file>
```

#### 2. Create FCM Provider (Android)

Navigate to: Messaging > Providers > Create Provider

```yaml
Name: bondwala-fcm
Type: FCM

# Credentials (to be uploaded):
# - Service Account JSON file
```

#### 3. Create Topics

Navigate to: Messaging > Topics

| Topic Name | Topic ID | Description |
|------------|----------|-------------|
| All Users | `all-users` | Broadcast to everyone |
| Win Alerts | `win-alerts` | Users who want win notifications |
| Draw Updates | `draw-updates` | New draw result announcements |
| Reminders | `reminders` | Check reminder subscribers |

### Generate API Keys

Navigate to: Project Settings > API Keys

#### Server Key (Backend)
```yaml
Name: bondwala-server
Scopes:
  - messaging.messages.write
  - messaging.topics.read
  - messaging.providers.read
  - messaging.subscribers.write
  - databases.read
  - databases.write
```

#### Admin Key (Full Access)
```yaml
Name: bondwala-admin
Scopes: All scopes
```

#### Client Key (Mobile App)
```yaml
Name: bondwala-client
Scopes:
  - messaging.subscribers.write
  - account.read
  - account.write
```

---

## Database Collections (Optional)

If migrating from PostgreSQL to Appwrite Database:

### Create Database

1. Navigate to: Databases > Create Database
2. Name: `bondwala_main`
3. ID: `bondwala-main`

### Create Collections

#### bonds Collection

```json
{
  "collectionId": "bonds",
  "name": "bonds",
  "attributes": [
    {"key": "serial", "type": "string", "size": 7, "required": true},
    {"key": "denomination", "type": "integer", "required": true, "default": 100},
    {"key": "series", "type": "string", "size": 1, "required": true},
    {"key": "addedAt", "type": "datetime", "required": true},
    {"key": "addedVia", "type": "enum", "elements": ["manual", "ocr"], "required": true},
    {"key": "isWinner", "type": "boolean", "default": false},
    {"key": "userId", "type": "string", "size": 36, "required": true}
  ],
  "indexes": [
    {"key": "serial_idx", "type": "key", "attributes": ["serial"]},
    {"key": "user_idx", "type": "key", "attributes": ["userId"]}
  ]
}
```

#### draws Collection

```json
{
  "collectionId": "draws",
  "name": "draws",
  "attributes": [
    {"key": "drawId", "type": "string", "size": 50, "required": true},
    {"key": "drawDate", "type": "datetime", "required": true},
    {"key": "denomination", "type": "integer", "required": true},
    {"key": "winners", "type": "string", "size": 1000000, "required": true},
    {"key": "createdAt", "type": "datetime", "required": true}
  ],
  "indexes": [
    {"key": "draw_date_idx", "type": "key", "attributes": ["drawDate"]}
  ]
}
```

#### devices Collection

```json
{
  "collectionId": "devices",
  "name": "devices",
  "attributes": [
    {"key": "targetId", "type": "string", "size": 36, "required": true},
    {"key": "deviceId", "type": "string", "size": 255, "required": true},
    {"key": "platform", "type": "enum", "elements": ["ios", "android"], "required": true},
    {"key": "userId", "type": "string", "size": 36, "required": false},
    {"key": "isActive", "type": "boolean", "default": true},
    {"key": "registeredAt", "type": "datetime", "required": true}
  ],
  "indexes": [
    {"key": "device_idx", "type": "key", "attributes": ["deviceId"], "unique": true},
    {"key": "user_device_idx", "type": "key", "attributes": ["userId"]}
  ]
}
```

---

## Operations Runbook

### Service Management

```bash
# Start all Appwrite services
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d

# Stop all services
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite down

# Restart specific service
docker compose -f docker-compose.appwrite.yml restart appwrite
docker compose -f docker-compose.appwrite.yml restart appwrite-worker-messaging

# View logs
docker logs appwrite -f --tail 100
docker logs appwrite-worker-messaging -f --tail 100
docker logs appwrite-mariadb -f --tail 100

# Check service health
docker compose -f docker-compose.appwrite.yml ps
curl https://appwrite.bondwala.com/v1/health
curl https://appwrite.bondwala.com/v1/health/queue
curl https://appwrite.bondwala.com/v1/health/storage
```

### Backup & Restore

#### Create Backup

```bash
# Backup directory
BACKUP_DIR=/opt/backups/appwrite/$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Stop services for consistent backup
docker compose -f docker-compose.appwrite.yml stop

# Backup MariaDB
docker run --rm \
  --network wizardsofts-megabuild_appwrite \
  -v $BACKUP_DIR:/backup \
  mariadb:10.11 \
  mysqldump -h appwrite-mariadb -u root -p'YOUR_ROOT_PASS' --all-databases > $BACKUP_DIR/appwrite_db.sql

# Backup volumes
docker run --rm \
  -v appwrite-uploads:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/appwrite-uploads.tar.gz /data

docker run --rm \
  -v appwrite-config:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/appwrite-config.tar.gz /data

# Restart services
docker compose -f docker-compose.appwrite.yml up -d

echo "Backup complete: $BACKUP_DIR"
```

#### Restore Backup

```bash
# Set backup directory
BACKUP_DIR=/opt/backups/appwrite/YYYYMMDD_HHMMSS

# Stop services
docker compose -f docker-compose.appwrite.yml down

# Restore MariaDB
docker run --rm \
  --network wizardsofts-megabuild_appwrite \
  -v $BACKUP_DIR:/backup \
  mariadb:10.11 \
  mysql -h appwrite-mariadb -u root -p'YOUR_ROOT_PASS' < /backup/appwrite_db.sql

# Restore volumes
docker run --rm \
  -v appwrite-uploads:/data \
  -v $BACKUP_DIR:/backup \
  alpine sh -c "cd /data && tar xzf /backup/appwrite-uploads.tar.gz --strip 1"

# Start services
docker compose -f docker-compose.appwrite.yml up -d
```

### SSL Certificate

SSL is handled automatically by Traefik with Let's Encrypt.

```bash
# Check certificate status
docker logs traefik 2>&1 | grep -i certificate

# Force certificate renewal (if needed)
docker exec traefik traefik healthcheck --renew-certs
```

### Scaling (Horizontal)

For high-traffic scenarios:

```bash
# Scale workers
docker compose -f docker-compose.appwrite.yml up -d --scale appwrite-worker-messaging=3

# Scale main API
docker compose -f docker-compose.appwrite.yml up -d --scale appwrite=2
```

---

## Test Push Notification

After configuration is complete:

```bash
# Test push notification
curl -X POST https://appwrite.bondwala.com/v1/messaging/messages/push \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: <project-id>" \
  -H "X-Appwrite-Key: <server-api-key>" \
  -d '{
    "messageId": "test-001",
    "title": "BondWala Test",
    "body": "Push notification working!",
    "topics": ["all-users"]
  }'

# Expected response:
# {
#   "$id": "test-001",
#   "topics": ["all-users"],
#   "status": "processing"
# }
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker logs appwrite 2>&1 | tail -50

# Common fixes:
# - Verify environment variables are set
# - Check network connectivity
# - Ensure MariaDB is healthy first
```

#### 2. 502 Bad Gateway

```bash
# Verify Traefik can reach Appwrite
docker network inspect wizardsofts-megabuild_gibd-network

# Check Appwrite is in the network
docker inspect appwrite --format='{{json .NetworkSettings.Networks}}'
```

#### 3. Push Notifications Not Sending

```bash
# Check messaging worker
docker logs appwrite-worker-messaging -f

# Verify providers are configured
curl https://appwrite.bondwala.com/v1/messaging/providers \
  -H "X-Appwrite-Project: <project-id>" \
  -H "X-Appwrite-Key: <admin-key>"
```

#### 4. Database Connection Failed

```bash
# Check MariaDB health
docker exec appwrite-mariadb mysqladmin ping -u root -p'YOUR_ROOT_PASS'

# Verify database exists
docker exec appwrite-mariadb mysql -u root -p'YOUR_ROOT_PASS' -e "SHOW DATABASES;"
```

---

## Deliverables Checklist

After deployment, provide the following:

```yaml
Deployment Details:
  appwrite_endpoint: "https://appwrite.bondwala.com/v1"
  appwrite_version: "1.8.1"
  console_url: "https://appwrite.bondwala.com"
  health_check_url: "https://appwrite.bondwala.com/v1/health"

Project Configuration:
  project_id: "<generated-project-id>"
  project_name: "BondWala"

API Keys:
  server_key:
    name: "bondwala-server"
    key: "<generated-api-key>"
    scopes: ["messaging.messages.write", "messaging.topics.read", ...]
  admin_key:
    name: "bondwala-admin"
    key: "<generated-api-key>"
    scopes: ["*"]
  client_key:
    name: "bondwala-client"
    key: "<generated-api-key>"
    scopes: ["messaging.subscribers.write", "account.*"]

Messaging Setup:
  apns_provider_id: "<provider-id>"
  fcm_provider_id: "<provider-id>"
  topics:
    - id: "<topic-id>", name: "all-users"
    - id: "<topic-id>", name: "win-alerts"
    - id: "<topic-id>", name: "draw-updates"
    - id: "<topic-id>", name: "reminders"

Console Admin:
  email: "admin@wizardsofts.com"
  temporary_password: "<initial-password>"

Docker Compose Location:
  path: "/opt/wizardsofts-megabuild/docker-compose.appwrite.yml"
  env_file: "/opt/wizardsofts-megabuild/.env.appwrite"

Backup Configuration:
  backup_schedule: "daily at 02:00 UTC"
  backup_location: "/opt/backups/appwrite"
  retention_days: 30

SSL Certificate:
  provider: "Let's Encrypt"
  auto_renewal: true
```

---

## Deployment Retrospective (2025-12-30)

### Issues Encountered & Resolutions

#### 1. Invalid Container Entrypoints
**Problem:** Original `appwrite-schedule` service used invalid entrypoint `schedule` which doesn't exist in Appwrite 1.8.1.

**Solution:** Replaced with three proper task scheduler services:
- `appwrite-task-scheduler-functions` (entrypoint: `schedule-functions`)
- `appwrite-task-scheduler-executions` (entrypoint: `schedule-executions`)
- `appwrite-task-scheduler-messages` (entrypoint: `schedule-messages`)

Added missing services:
- `appwrite-worker-stats-resources` (entrypoint: `worker-stats-resources`)
- `appwrite-worker-functions` (entrypoint: `worker-functions`)
- `appwrite-executor` (OpenRuntimes executor for serverless functions)

#### 2. Container Permission Errors
**Problem:** MariaDB, Redis, and Appwrite containers failed with "exec: operation not permitted" due to restrictive security settings.

**Solution:** Removed overly restrictive security settings from affected services:
- Removed `user: "999:999"` and `user: "www-data"`
- Removed `security_opt: - no-new-privileges:true`
- Removed `cap_drop: - ALL` and `cap_add` restrictions

> **Note:** These security settings are best practices but may conflict with Docker Snap installations. Test in your environment.

#### 3. Console 500 Error on `/v1/console/variables`
**Problem:** Console returned 500 error with `TypeError: Domain::__construct(): Argument #1 ($domain) must be of type string, null given`.

**Root Cause:** Missing `_APP_DOMAIN_TARGET_CNAME` environment variable.

**Solution:** Added to docker-compose.appwrite.yml:
```yaml
- _APP_DOMAIN_TARGET_CNAME=${_APP_DOMAIN_TARGET_CNAME:-appwrite.wizardsofts.com}
```

#### 4. Environment File Format Issues
**Problem:** Docker-compose wasn't loading variables from `.env.appwrite` due to comment lines.

**Solution:** Clean the env file by removing comments:
```bash
grep -v '^#' .env.appwrite | grep -v '^$' | grep '=' > .env.appwrite.clean
mv .env.appwrite .env.appwrite.backup
mv .env.appwrite.clean .env.appwrite
```

### Current Production Configuration

| Setting | Value |
|---------|-------|
| Domain | appwrite.wizardsofts.com |
| Console URL | https://appwrite.wizardsofts.com/console |
| Admin Email | admin@wizardsofts.com |
| Signup Restriction | Enabled (whitelist only) |
| Total Services | 22 containers |

### Git Commits for This Deployment

| Commit | Description |
|--------|-------------|
| `074c8fd` | Fixed all worker and scheduler service entrypoints |
| `5e3f3ec` | Removed restrictive security settings from MariaDB/Redis |
| `6a836c3` | Removed security restrictions from all containers |
| `90e348b` | Allow first user signup by disabling console whitelist |
| `6811022` | Added `_APP_DOMAIN_TARGET_CNAME` to fix console 500 error |
| `fa6e265` | Enabled console signup whitelist by default |

### Lessons Learned

1. **Always verify entrypoints** against official Appwrite docker-compose for your version
2. **Test security restrictions** in your specific Docker environment before applying
3. **Environment files** should be clean (no comments) for docker-compose `--env-file`
4. **Missing env vars** like `_APP_DOMAIN_TARGET_CNAME` can cause cryptic 500 errors
5. **Use `docker-compose rm -f && up -d`** instead of just `restart` when changing env vars

---

## References

- [Appwrite Documentation](https://appwrite.io/docs)
- [Appwrite Self-Hosting Guide](https://appwrite.io/docs/advanced/self-hosting)
- [Appwrite Messaging API](https://appwrite.io/docs/references/cloud/server-nodejs/messaging)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Appwrite GitHub Issues](https://github.com/appwrite/appwrite/issues) - for troubleshooting

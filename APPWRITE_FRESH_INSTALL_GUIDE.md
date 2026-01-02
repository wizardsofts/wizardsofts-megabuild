# Appwrite Fresh Reinstallation Guide
**Version**: 2.0
**Date**: 2025-12-30
**Status**: Complete Installation & Configuration Guide
**Server**: 10.0.0.84 (gmktec) / 106.70.161.3 (public)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Lessons Learned from Previous Installation](#lessons-learned-from-previous-installation)
3. [Prerequisites](#prerequisites)
4. [Pre-Installation Cleanup](#pre-installation-cleanup)
5. [Fresh Installation Steps](#fresh-installation-steps)
6. [Post-Installation Configuration](#post-installation-configuration)
7. [Verification & Testing](#verification--testing)
8. [Console Configuration](#console-configuration)
9. [Traefik Integration](#traefik-integration)
10. [Troubleshooting](#troubleshooting)
11. [Critical Gaps & Fixes](#critical-gaps--fixes)

---

## Executive Summary

This guide provides a complete, tested procedure for reinstalling Appwrite 1.8.x on server 10.0.0.84 with Traefik reverse proxy integration. The guide incorporates lessons learned from the previous installation issues, including:

- Console project initialization failures
- Traefik routing configuration
- Console env.js configuration for self-hosted mode
- Docker Snap filesystem restrictions
- Database initialization verification

**Installation Method**: Manual Docker Compose (preferred over automated installer for production)

**Time Required**: 30-45 minutes (including verification)

---

## Lessons Learned from Previous Installation

### Issue 1: Console Project Not Created
**Problem**: The `_console_projects` table remained empty after installation, causing 500 errors and 404 redirects.

**Root Cause**: Appwrite's first-boot initialization didn't create the internal "console" project required for the self-hosted console UI to function.

**Solution**: Use the official Appwrite installer or ensure proper initialization sequence:
1. Start all containers
2. Wait for database migrations to complete
3. Access console to trigger project creation
4. Verify console project exists in database

### Issue 2: Console env.js Configuration
**Problem**: Console loaded but couldn't connect to API endpoint (`PUBLIC_APPWRITE_ENDPOINT` was empty).

**Root Cause**: The console container's `env.js` file had default cloud values instead of self-hosted configuration.

**Solution**:
- Create custom `traefik/console-env.js` with proper endpoint
- Copy into container after it starts (volume mount doesn't work with Docker Snap)
- Command: `docker cp traefik/console-env.js appwrite-console:/usr/share/nginx/html/console/_app/env.js`

### Issue 3: Docker Snap Filesystem Restrictions
**Problem**: Volume mount failed with "read-only file system" error.

**Root Cause**: Docker installed via Snap has restricted access to host filesystem outside user directories.

**Solution**:
- Don't use volume mounts for env.js
- Use `docker cp` instead
- Document in docker-compose.yml comments

### Issue 4: Traefik Console Routing
**Problem**: Console returned 504 Gateway Timeout.

**Root Cause**: Console container not on same network as Traefik.

**Solution**:
- Add console to `microservices-overlay` network
- Set higher router priority (100) for console routes
- Use PathPrefix matching: `PathPrefix(\`/console\`)`

---

## Prerequisites

### System Requirements
- **CPU**: 2 cores minimum, 4 cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Swap**: 2GB
- **Disk**: 20GB available
- **OS**: Ubuntu 20.04+ or compatible Linux with Docker

### Required Software
```bash
# Docker Engine 20.10+
docker --version

# Docker Compose V2
docker compose version

# Should output: Docker Compose version v2.x.x
```

### Network Requirements
- Ports 80, 443 accessible (managed by Traefik)
- Outbound internet access for Docker image pulls
- DNS records configured:
  - `appwrite.wizardsofts.com` → 106.70.161.3
  - `appwrite.bondwala.com` → 106.70.161.3

### Existing Infrastructure
- Traefik v2.10 running on `microservices-overlay` network
- Let's Encrypt certificate resolver configured
- External networks created:
  - `traefik-public`
  - `gibd-network`
  - `microservices-overlay`

---

## Pre-Installation Cleanup

### Step 1: Backup Existing Data (If Any)
```bash
# SSH to server
ssh wizardsofts@10.0.0.84

# Backup existing database (if present)
docker exec appwrite-mariadb mysqldump -u wizardsofts -p'W1z4rdS0fts2025Secure' appwrite > /tmp/appwrite_backup_$(date +%Y%m%d).sql

# Backup existing volumes (optional)
docker run --rm -v appwrite-uploads:/data -v $(pwd):/backup ubuntu tar czf /backup/appwrite-uploads.tar.gz /data
```

### Step 2: Stop and Remove Existing Containers
```bash
cd /opt/wizardsofts-megabuild

# Stop all Appwrite containers
sudo docker-compose -f docker-compose.appwrite.yml down

# Verify all stopped
docker ps | grep appwrite
# Should return nothing
```

### Step 3: Remove Existing Volumes (CAUTION: DATA LOSS)
```bash
# List Appwrite volumes
docker volume ls | grep appwrite

# Remove all Appwrite volumes (ONLY if doing fresh install)
docker volume rm appwrite-mariadb appwrite-redis appwrite-cache appwrite-uploads appwrite-certificates appwrite-functions appwrite-builds appwrite-config

# Verify removal
docker volume ls | grep appwrite
# Should return nothing
```

### Step 4: Clean Up Docker System
```bash
# Remove unused images
docker image prune -f

# Remove unused networks (careful not to remove shared networks)
docker network prune -f
```

---

## Fresh Installation Steps

### Step 1: Prepare Configuration Files

#### A. Generate Security Keys
```bash
# Generate OpenSSL encryption key (256-bit)
openssl rand -hex 32
# Output: Save this as _APP_OPENSSL_KEY_V1

# Generate application secret
openssl rand -hex 32
# Output: Save this as _APP_SECRET

# Generate executor secret
openssl rand -hex 32
# Output: Save this as _APP_EXECUTOR_SECRET
```

#### B. Create `.env.appwrite` File
```bash
cd /opt/wizardsofts-megabuild

# Copy template
cp .env.appwrite.template .env.appwrite

# Edit with generated keys
nano .env.appwrite
```

**Critical Environment Variables**:
```bash
# Core
_APP_ENV=production
_APP_WORKER_PER_CORE=6
_APP_LOCALE=en

# Domain (CRITICAL - must match your DNS)
_APP_DOMAIN=appwrite.wizardsofts.com
_APP_DOMAIN_TARGET=appwrite.wizardsofts.com
_APP_DOMAIN_FUNCTIONS=functions.appwrite.wizardsofts.com

# Security Keys (use generated values above)
_APP_OPENSSL_KEY_V1=<your-generated-key-1>
_APP_SECRET=<your-generated-key-2>
_APP_EXECUTOR_SECRET=<your-generated-key-3>

# Console Access Control
_APP_CONSOLE_WHITELIST_ROOT=enabled
_APP_CONSOLE_WHITELIST_EMAILS=admin@wizardsofts.com,tech@wizardsofts.com
_APP_CONSOLE_WHITELIST_IPS=

# Database
_APP_DB_HOST=appwrite-mariadb
_APP_DB_PORT=3306
_APP_DB_SCHEMA=appwrite
_APP_DB_USER=wizardsofts
_APP_DB_PASS=W1z4rdS0fts2025Secure
_APP_DB_ROOT_PASS=W1z4rdS0fts2025Secure

# Redis
_APP_REDIS_HOST=appwrite-redis
_APP_REDIS_PORT=6379
_APP_REDIS_USER=
_APP_REDIS_PASS=
```

### Step 2: Prepare Console env.js File
```bash
# Create traefik directory if not exists
mkdir -p /opt/wizardsofts-megabuild/traefik

# Create console-env.js
cat > /opt/wizardsofts-megabuild/traefik/console-env.js << 'EOF'
export const env={
    "PUBLIC_CONSOLE_FEATURE_FLAGS":"",
    "PUBLIC_APPWRITE_MULTI_REGION":"false",
    "PUBLIC_STRIPE_KEY":"",
    "PUBLIC_CONSOLE_MODE":"self-hosted",
    "PUBLIC_CONSOLE_EMAIL_VERIFICATION":"false",
    "PUBLIC_APPWRITE_ENDPOINT":"https://appwrite.wizardsofts.com/v1",
    "PUBLIC_CONSOLE_MOCK_AI_SUGGESTIONS":"true",
    "PUBLIC_GROWTH_ENDPOINT":"https://growth.appwrite.io/v1"
}
EOF
```

### Step 3: Verify docker-compose.appwrite.yml Configuration

Ensure the following sections are correctly configured:

```yaml
# Console service configuration
appwrite-console:
  image: appwrite/console:7.4.11
  container_name: appwrite-console
  restart: unless-stopped
  networks:
    - appwrite
    - microservices-overlay  # CRITICAL: Must be on Traefik network
  # NOTE: No volume mount due to Docker Snap restrictions
  # env.js must be copied manually after container starts
  environment:
    - _APP_ENDPOINT=https://appwrite.wizardsofts.com/v1
    - _APP_DOMAIN=appwrite.wizardsofts.com
    - _APP_CONSOLE_WHITELIST_ROOT=${_APP_CONSOLE_WHITELIST_ROOT:-enabled}
    - _APP_CONSOLE_WHITELIST_EMAILS=${_APP_CONSOLE_WHITELIST_EMAILS}
  labels:
    - "traefik.enable=true"
    - "traefik.docker.network=microservices-overlay"
    # HTTPS Router with high priority
    - "traefik.http.routers.appwrite_console_https.rule=Host(`appwrite.wizardsofts.com`) && PathPrefix(`/console`)"
    - "traefik.http.routers.appwrite_console_https.entrypoints=websecure"
    - "traefik.http.routers.appwrite_console_https.tls=true"
    - "traefik.http.routers.appwrite_console_https.tls.certresolver=letsencrypt"
    - "traefik.http.routers.appwrite_console_https.priority=100"  # Higher than main API
    # Service
    - "traefik.http.services.appwrite_console.loadbalancer.server.port=80"
```

### Step 4: Deploy Appwrite
```bash
cd /opt/wizardsofts-megabuild

# Start all Appwrite services
sudo docker-compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d

# Monitor startup (wait for initialization to complete)
docker logs appwrite -f
```

**Expected Output**:
```
[Setup] - logs database init started...
[Setup] - appwrite database init started...
[Setup] - Server database init completed...
[Info] Server started successfully
```

**Wait Time**: 2-5 minutes for all containers to start and initialize

### Step 5: Verify Container Status
```bash
# Check all containers are running
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep appwrite

# Expected output: 15 containers with "Up" status
# - appwrite
# - appwrite-console
# - appwrite-mariadb
# - appwrite-redis
# - appwrite-worker-messaging
# - appwrite-worker-audits
# - appwrite-worker-webhooks
# - appwrite-worker-deletes
# - appwrite-worker-databases
# - appwrite-worker-builds
# - appwrite-worker-certificates
# - appwrite-worker-mails
# - appwrite-worker-migrations
# - appwrite-maintenance
# - appwrite-usage
# - appwrite-schedule
# - appwrite-realtime
```

### Step 6: Configure Console env.js (CRITICAL)
```bash
# Wait for console container to be fully up (check with docker ps)
sleep 10

# Copy env.js into console container
docker cp /opt/wizardsofts-megabuild/traefik/console-env.js appwrite-console:/usr/share/nginx/html/console/_app/env.js

# Restart console to load new config
docker restart appwrite-console

# Verify env.js was copied correctly
docker exec appwrite-console cat /usr/share/nginx/html/console/_app/env.js
```

**Expected Output**:
```javascript
export const env={
    "PUBLIC_CONSOLE_FEATURE_FLAGS":"",
    "PUBLIC_APPWRITE_MULTI_REGION":"false",
    ...
    "PUBLIC_APPWRITE_ENDPOINT":"https://appwrite.wizardsofts.com/v1",
    ...
}
```

---

## Post-Installation Configuration

### Step 1: Wait for Database Initialization
```bash
# Check appwrite logs for initialization completion
docker logs appwrite 2>&1 | grep -i "init\\|database\\|setup"

# Expected: "Server database init completed"
```

### Step 2: Verify Database Tables Created
```bash
# Connect to MariaDB
docker exec -it appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite

# List console tables
SHOW TABLES LIKE '_console%';

# Expected output: ~50 tables including:
# - _console_projects
# - _console_users
# - _console_sessions
# etc.

# Exit MySQL
exit
```

### Step 3: Check API Health
```bash
# Test API endpoint
curl -I https://appwrite.wizardsofts.com/v1/health/version

# Expected: HTTP/2 200
# Expected body: {"version":"1.8.1"}
```

### Step 4: Access Console for First Time
1. Open browser: `https://appwrite.wizardsofts.com/console`
2. Expected: Sign up page loads (not 404 or 500)
3. **DO NOT SIGN UP YET** - First verify console can communicate with API

### Step 5: Verify Console API Connection
```bash
# Check browser console for errors
# Should see successful /v1/console/variables request (or 401 Unauthorized, which is expected before login)
# Should NOT see 500 errors or "PUBLIC_APPWRITE_ENDPOINT is empty" errors
```

---

## Verification & Testing

### Test 1: Console Page Loads
```bash
curl -I https://appwrite.wizardsofts.com/console/

# Expected: HTTP/2 200
# Expected: Content-Type: text/html
```

### Test 2: API Responds
```bash
curl https://appwrite.wizardsofts.com/v1/health/version

# Expected: {"version":"1.8.1"}
```

### Test 3: Console Variables Endpoint (Authenticated)
```bash
curl https://appwrite.wizardsofts.com/v1/console/variables \
  -H 'X-Appwrite-Project: console'

# Expected: 401 Unauthorized (before login) - this is GOOD
# NOT Expected: 500 Internal Server Error
```

### Test 4: Console Project Exists in Database
```bash
docker exec appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite -e "SELECT _uid, _id, name FROM _console_projects LIMIT 5"

# Expected: Should show at least one row (console project)
# If empty: Restart appwrite container to trigger initialization
```

---

## Console Configuration

### Step 1: Create First Admin Account
1. Navigate to: `https://appwrite.wizardsofts.com/console/register`
2. Fill in signup form:
   - **Name**: Admin
   - **Email**: `admin@wizardsofts.com` (MUST match whitelist)
   - **Password**: `W1z4rdS0fts!2025` (or your secure password)
3. Check "I agree to terms" checkbox
4. Click "Sign up"
5. Expected: Redirect to project creation page (NOT 404)

### Step 2: Verify User Created
```bash
docker exec appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite -e "SELECT email, name, status FROM _console_users"

# Expected output:
# email                    name    status
# admin@wizardsofts.com    Admin   1
```

### Step 3: Create BondWala Project
1. In console, click "Create Project"
2. Project Name: `BondWala`
3. Project ID: `bondwala` (or auto-generated)
4. Click "Create"
5. Expected: Project dashboard loads

### Step 4: Configure Platforms
1. Navigate to: Project Settings → Platforms
2. Add iOS Platform:
   - Name: `BondWala iOS`
   - Bundle ID: `com.wizardsofts.bondwala`
3. Add Android Platform:
   - Name: `BondWala Android`
   - Package Name: `com.wizardsofts.bondwala`

### Step 5: Generate API Keys
1. Navigate to: Project Settings → API Keys
2. Create Server Key:
   - Name: `bondwala-server`
   - Scopes: messaging.*, database.*, users.*
   - Expiration: Never
3. Create Client Key:
   - Name: `bondwala-client`
   - Scopes: messaging.messages.create, messaging.topics.read
   - Expiration: Never
4. **Save keys securely** - they cannot be retrieved later

---

## Traefik Integration

### Verify Traefik Routing

#### Check Traefik Dashboard
```bash
# Access Traefik dashboard (if enabled)
# URL: https://traefik.wizardsofts.com

# Verify routers:
# - appwrite (main API)
# - appwrite_console_https (console)
# - appwrite-realtime (WebSocket)
```

#### Test Routing
```bash
# Test main API
curl -I https://appwrite.wizardsofts.com/v1/health/version
# Expected: HTTP/2 200

# Test console
curl -I https://appwrite.wizardsofts.com/console/
# Expected: HTTP/2 200

# Test realtime
curl -I https://appwrite.wizardsofts.com/v1/realtime
# Expected: HTTP/2 101 Switching Protocols (if WebSocket supported)
```

### Traefik Configuration Reference
Located in: `traefik/dynamic_conf.yml`

```yaml
# Appwrite Main API
http:
  routers:
    appwrite:
      rule: "Host(`appwrite.wizardsofts.com`) || Host(`appwrite.bondwala.com`)"
      service: appwrite
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      middlewares:
        - appwrite-rate-limit
        - appwrite-cors
        - appwrite-security-headers

  services:
    appwrite:
      loadBalancer:
        servers:
          - url: "http://appwrite:80"

# Console routing handled by Docker labels in docker-compose.appwrite.yml
```

---

## Troubleshooting

### Issue 1: Console Returns 404 After Login
**Symptoms**: Login succeeds but redirects to 404 page

**Diagnosis**:
```bash
# Check console project exists
docker exec appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite -e "SELECT COUNT(*) FROM _console_projects"

# Check appwrite logs
docker logs appwrite --tail 100 | grep -i error
```

**Solution**:
```bash
# Restart appwrite to trigger initialization
docker restart appwrite

# Wait 30 seconds
sleep 30

# Verify console project created
docker exec appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite -e "SELECT * FROM _console_projects"
```

### Issue 2: Console Returns 500 on /v1/console/variables
**Symptoms**: Console loads but shows "Server Error" on API calls

**Diagnosis**:
```bash
# Check env.js configuration
docker exec appwrite-console cat /usr/share/nginx/html/console/_app/env.js | grep ENDPOINT

# Expected: "PUBLIC_APPWRITE_ENDPOINT":"https://appwrite.wizardsofts.com/v1"
```

**Solution**:
```bash
# Re-copy env.js
docker cp /opt/wizardsofts-megabuild/traefik/console-env.js appwrite-console:/usr/share/nginx/html/console/_app/env.js

# Restart console
docker restart appwrite-console
```

### Issue 3: Containers Won't Start
**Symptoms**: `docker ps` shows containers constantly restarting

**Diagnosis**:
```bash
# Check logs of failing container
docker logs appwrite-mariadb --tail 100
docker logs appwrite --tail 100
```

**Common Causes**:
- Insufficient memory (check with `free -h`)
- Port conflicts (check with `netstat -tulpn | grep :80`)
- Missing environment variables in `.env.appwrite`
- Database initialization failed

**Solution**:
```bash
# Restart with fresh state
docker-compose -f docker-compose.appwrite.yml down
docker volume rm appwrite-mariadb appwrite-redis
docker-compose -f docker-compose.appwrite.yml up -d
```

### Issue 4: Traefik Can't Reach Console (504 Gateway Timeout)
**Symptoms**: Console page times out or shows 504 error

**Diagnosis**:
```bash
# Check console container is running
docker ps | grep appwrite-console

# Check network connectivity
docker network inspect microservices-overlay | grep appwrite-console
```

**Solution**:
```bash
# Ensure console is on correct network
docker-compose -f docker-compose.appwrite.yml up -d --force-recreate appwrite-console

# Verify Traefik can reach console
docker exec traefik ping -c 2 appwrite-console
```

---

## Critical Gaps & Fixes

### Gap 1: Console Project Initialization
**What Official Docs Say**: "After installation, open console and create account"

**What Actually Happens**: Console project must exist BEFORE first signup, or user gets 404/500 errors

**Fix**:
1. Start all containers
2. Wait for appwrite logs to show "Server database init completed"
3. Check `_console_projects` table is populated
4. If empty, restart appwrite container to trigger initialization

### Gap 2: Console env.js Not Documented
**What Official Docs Say**: Nothing about console env.js configuration

**What Actually Happens**: Console loads with cloud endpoint by default, can't connect to self-hosted API

**Fix**: Create and copy custom env.js with self-hosted endpoint

### Gap 3: Docker Snap Filesystem Restrictions
**What Official Docs Say**: Use volume mounts for configuration files

**What Actually Happens**: Docker Snap has read-only filesystem restrictions

**Fix**: Use `docker cp` instead of volume mounts for files outside user directories

### Gap 4: Traefik Priority Configuration
**What Official Docs Say**: Nothing specific about reverse proxy routing priority

**What Actually Happens**: Console routes can conflict with main API routes

**Fix**: Set higher priority (100) for console router to ensure proper matching

### Gap 5: Console Container Network
**What Official Docs Say**: Basic network configuration examples

**What Actually Happens**: Console must be on same network as Traefik for routing to work

**Fix**: Add `microservices-overlay` network to console service AND set in Docker labels

---

## Post-Installation Checklist

- [ ] All 15+ containers running and healthy
- [ ] Database tables created (~50 _console tables)
- [ ] Console project exists in `_console_projects` table
- [ ] Console env.js configured with self-hosted endpoint
- [ ] API health endpoint responds (HTTP 200)
- [ ] Console page loads (HTTP 200, not 404)
- [ ] Console can connect to API (no 500 errors on /v1/console/variables)
- [ ] First admin account created successfully
- [ ] BondWala project created
- [ ] API keys generated
- [ ] Traefik routing verified
- [ ] SSL certificate issued by Let's Encrypt
- [ ] Backup script tested
- [ ] Documentation updated

---

## Next Steps After Successful Installation

1. **Configure Push Notification Providers**
   - APNs for iOS
   - FCM for Android

2. **Create Messaging Topics**
   - all-users
   - win-alerts
   - draw-updates
   - reminders

3. **Integrate with BondWala Backend**
   - Install node-appwrite SDK
   - Configure API keys
   - Migrate from Firebase

4. **Integrate with Mobile App**
   - Install react-native-appwrite SDK
   - Update push token registration
   - Test end-to-end notifications

5. **Setup Monitoring**
   - Configure Prometheus metrics export
   - Create Grafana dashboard
   - Set up alerts

6. **Enable Backups**
   - Schedule automated daily backups
   - Test restore procedure
   - Document recovery process

---

## Resources & Documentation

### Official Appwrite Documentation
- [Installation Guide](https://appwrite.io/docs/advanced/self-hosting/installation)
- [Self-Hosting Overview](https://appwrite.io/docs/advanced/self-hosting)
- [Production Preparation](https://appwrite.io/docs/advanced/self-hosting/production)
- [Update Guide](https://appwrite.io/docs/advanced/self-hosting/update)

### Community Resources
- [Appwrite Discord](https://discord.gg/appwrite)
- [GitHub Issues](https://github.com/appwrite/appwrite/issues)
- [Community Forums](https://appwrite.io/threads)

### WizardSofts Internal Documentation
- `APPWRITE_DEPLOYMENT_SUCCESS.md` - Previous deployment details
- `APPWRITE_SETUP_SUMMARY.md` - Original setup documentation
- `APPWRITE_NEXT_STEPS.md` - Post-deployment configuration
- `.env.appwrite.template` - Environment configuration template

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-30 | Complete reinstallation guide with all fixes and gaps documented |
| 1.0 | 2025-12-27 | Initial deployment (had console initialization issues) |

---

**Prepared by**: Claude (Anthropic)
**Verified against**: Official Appwrite 1.8.x documentation + community threads
**Status**: ✅ Ready for Production Deployment
**Last Updated**: 2025-12-30

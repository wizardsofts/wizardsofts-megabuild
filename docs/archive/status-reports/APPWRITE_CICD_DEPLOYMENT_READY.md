# Appwrite CI/CD Deployment - Ready Status

**Date**: 2025-12-30
**Status**: ✅ READY FOR DEPLOYMENT
**Deployment Method**: GitLab CI/CD Pipeline
**Target Server**: 10.0.0.84 (wizardsofts@10.0.0.84)

---

## What Has Been Prepared

### 1. GitLab CI/CD Pipeline Enhancement ✅

**File**: `.gitlab-ci.yml`
**Location**: Lines 400-567

**New Deployment Job**: `deploy-appwrite`
- Stage: `deploy`
- Trigger: Manual (requires clicking "Play" in GitLab UI)
- Change Detection: Only deploys when Appwrite files change
- Auto-cleanup: Removes old Appwrite data for fresh installation
- Auto-verification: Checks console project creation after deployment

**Key Features**:
- ✅ Detects changes to `docker-compose.appwrite.yml`, `.env.appwrite`, `traefik/console-env.js`
- ✅ Syncs only Appwrite files to server (not entire repo)
- ✅ Creates required Docker networks (`microservices-overlay`, `gibd-network`)
- ✅ Cleans old Appwrite data for fresh installation
- ✅ Waits for initialization (120 seconds)
- ✅ Copies console-env.js into container
- ✅ Verifies console project creation in database
- ✅ Auto-restarts Appwrite if console project missing
- ✅ Health check endpoint test

### 2. Environment Configuration ✅

**File**: `.env.appwrite`
**Status**: Configured with production values

**Security Keys Generated**:
```bash
_APP_OPENSSL_KEY_V1=fc19663f47321633e2429b7fd7e6a328dabde3df3e6bd80944b78f142de0cef0
_APP_SECRET=ebb380326b3bd0338206f0f7a48e9ab4f769520b9e5a83829b7a11414c115027
_APP_EXECUTOR_SECRET=ef8de8266e6a42896cf9b998cbe6df26921014fb2b39f57458212e321346ebf8
```

**Domain Configuration**:
```bash
_APP_DOMAIN=appwrite.wizardsofts.com
_APP_DOMAIN_TARGET=appwrite.wizardsofts.com
```

**Database Credentials**:
```bash
_APP_DB_USER=wizardsofts
_APP_DB_PASS=W1z4rdS0fts2025Secure
_APP_DB_ROOT_PASS=W1z4rdS0fts2025Secure
```

**Console Access Control**:
```bash
_APP_CONSOLE_WHITELIST_ROOT=enabled
_APP_CONSOLE_WHITELIST_EMAILS=admin@wizardsofts.com,tech@wizardsofts.com
```

### 3. Console Configuration ✅

**File**: `traefik/console-env.js`
**Content**:
```javascript
export const env={
    "PUBLIC_CONSOLE_MODE":"self-hosted",
    "PUBLIC_APPWRITE_ENDPOINT":"https://appwrite.wizardsofts.com/v1",
    "PUBLIC_CONSOLE_EMAIL_VERIFICATION":"false"
}
```

This file will be automatically copied into the console container during deployment.

### 4. Docker Compose Configuration ✅

**File**: `docker-compose.appwrite.yml`
**Memory Optimized**: Database resources reduced to minimize footprint

**MariaDB Resources**:
- CPU Limit: 1 core (was 2)
- Memory Limit: 512MB (was 2GB)
- InnoDB Buffer Pool: 128MB (was 512MB)
- Max Connections: 100 (was 500)
- Performance Schema: OFF (saves ~200MB)
- Binary Logging: OFF (saves disk I/O)

**Redis Resources**:
- CPU Limit: 1 core
- Memory Limit: 512MB
- LRU Eviction: Enabled

**Total Memory Footprint**: ~1GB for databases (was ~2.5GB)

### 5. Documentation Created ✅

- [APPWRITE_FRESH_INSTALL_GUIDE.md](APPWRITE_FRESH_INSTALL_GUIDE.md) - Complete installation guide with all fixes
- [APPWRITE_GAP_ANALYSIS.md](APPWRITE_GAP_ANALYSIS.md) - 7 critical gaps documented
- [APPWRITE_SETUP_SUMMARY.md](APPWRITE_SETUP_SUMMARY.md) - Original setup documentation

---

## How to Deploy via GitLab CI/CD

### Step 1: Commit and Push Changes

```bash
# From your local repository
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Add Appwrite files
git add .gitlab-ci.yml
git add docker-compose.appwrite.yml
git add .env.appwrite
git add traefik/console-env.js
git add APPWRITE_*.md

# Commit
git commit -m "feat: Add Appwrite BaaS deployment via CI/CD

- Add deploy-appwrite job to GitLab CI/CD pipeline
- Configure .env.appwrite with production settings
- Optimize database memory usage (MariaDB: 512MB, Redis: 512MB)
- Add console-env.js for self-hosted mode
- Include fresh installation with automatic cleanup
- Add console project verification and auto-restart
- Document installation process and gaps

Closes #appwrite-deployment"

# Push to main branch
git push origin main
```

### Step 2: Monitor Pipeline in GitLab

1. Open GitLab: https://gitlab.com/wizardsofts/wizardsofts-megabuild/-/pipelines
2. Find the pipeline for your commit
3. Pipeline will run through these stages:
   - ✅ **validate** - Validate configurations
   - ✅ **detect** - Detect changed files (will find Appwrite files)
   - ✅ **test** - Run tests (will skip if no app code changed)
   - ✅ **build** - Build images (will skip)
   - ⏸️ **deploy** - WAIT HERE

### Step 3: Manually Trigger Appwrite Deployment

In the `deploy` stage, you'll see the `deploy-appwrite` job with a "Play" button:

1. Click the **Play** button next to `deploy-appwrite`
2. Job will start execution
3. Monitor the console output

**Expected Output**:
```
Deploying Appwrite to 10.0.0.84...
Syncing Appwrite files to 10.0.0.84...
Starting Appwrite deployment...
Ensuring microservices-overlay network exists...
Ensuring gibd-network exists...
Stopping existing Appwrite containers...
Cleaning up old Appwrite data for fresh installation...
Pulling Appwrite images...
Starting Appwrite services...
Waiting for services to start (30s)...
Waiting for Appwrite initialization (90s)...
Configuring console environment...
Console env.js configured successfully
Restarting console container to apply configuration...
Verifying console project initialization...
Console project verified (count: 1)
Appwrite service status:
Testing Appwrite health endpoint...
Appwrite deployment complete!
Access console at: https://appwrite.wizardsofts.com/console
```

**Total Deployment Time**: ~3-4 minutes
- File sync: ~10 seconds
- Image pull: ~60 seconds
- Initialization: ~120 seconds
- Verification: ~30 seconds

### Step 4: Verify Deployment

The pipeline automatically tests the health endpoint, but you should manually verify:

```bash
# Health check
curl https://appwrite.wizardsofts.com/v1/health

# Expected response:
{"status":"pass"}

# Console access
curl -I https://appwrite.wizardsofts.com/console/

# Expected: HTTP/2 200
```

---

## What Happens During Deployment

### Phase 1: Change Detection (Automatic)
- GitLab detects changes to Appwrite files
- Pipeline marks Appwrite deployment as needed
- Waits for manual trigger

### Phase 2: File Synchronization
```bash
rsync -avz \
  --include 'docker-compose.appwrite.yml' \
  --include '.env.appwrite' \
  --include 'traefik/console-env.js' \
  --include 'traefik/' \
  wizardsofts@10.0.0.84:/opt/wizardsofts-megabuild/
```

### Phase 3: Server-Side Deployment Script

**Network Setup**:
```bash
docker network create microservices-overlay  # For Traefik routing
docker network create gibd-network           # For internal services
```

**Data Cleanup (Fresh Install)**:
```bash
sudo rm -rf /mnt/data/docker/appwrite/*
sudo mkdir -p /mnt/data/docker/appwrite/{mariadb,redis,uploads,cache,config,certificates,functions}
sudo chown -R 33:33 /mnt/data/docker/appwrite  # www-data user
```

**Service Deployment**:
```bash
# Stop old containers
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite down

# Pull latest images
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite pull

# Start services
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d
```

**Initialization Wait**:
```bash
# Wait for containers to start (30s)
# Wait for Appwrite initialization (90s)
# Total wait: 120 seconds
```

**Console Configuration**:
```bash
# Copy console-env.js into container
docker cp traefik/console-env.js appwrite-console:/usr/share/nginx/html/console/_app/env.js

# Restart console to load new config
docker restart appwrite-console
```

**Database Verification**:
```bash
# Check if console project created
CONSOLE_PROJECT_COUNT=$(docker exec appwrite-mariadb \
  mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite \
  -se "SELECT COUNT(*) FROM _console_projects")

# If count = 0, restart Appwrite to trigger initialization
if [ "$CONSOLE_PROJECT_COUNT" -eq "0" ]; then
  docker restart appwrite
  sleep 60
  # Verify again
fi
```

---

## Post-Deployment Verification Checklist

### Automated Verification (Done by Pipeline)
- ✅ Network creation
- ✅ Container startup
- ✅ Console project creation
- ✅ Health endpoint test

### Manual Verification Required

1. **Console Access**:
   ```bash
   # Open browser
   https://appwrite.wizardsofts.com/console

   # Expected: Console UI loads without errors
   ```

2. **First Admin Signup**:
   - Email: `admin@wizardsofts.com` (from whitelist)
   - Password: `W1z4rdS0fts!2025` (or your choice)
   - **CRITICAL**: Email MUST be from `_APP_CONSOLE_WHITELIST_EMAILS`

3. **API Endpoint Test**:
   ```bash
   curl https://appwrite.wizardsofts.com/v1/health
   # Expected: {"status":"pass"}

   curl https://appwrite.wizardsofts.com/v1/health/db
   # Expected: {"status":"pass"}

   curl https://appwrite.wizardsofts.com/v1/health/cache
   # Expected: {"status":"pass"}
   ```

4. **Console Functionality**:
   - Navigate to Console → Home
   - Check for "Welcome" message
   - Verify no 404 or 500 errors
   - Confirm "Create Project" button visible

5. **Database Verification**:
   ```bash
   # SSH to server
   ssh wizardsofts@10.0.0.84

   # Check console project
   docker exec appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite \
     -e "SELECT * FROM _console_projects LIMIT 1"

   # Expected: 1 row returned with console project details
   ```

6. **Container Health**:
   ```bash
   # All containers running
   docker ps --filter "name=appwrite" --format "table {{.Names}}\t{{.Status}}"

   # Expected: 15+ containers, all "Up" status
   ```

---

## Rollback Procedure

If deployment fails or issues occur:

### Option 1: Retry Deployment
```bash
# In GitLab pipeline, click "Retry" on deploy-appwrite job
```

### Option 2: Manual Rollback
```bash
# SSH to server
ssh wizardsofts@10.0.0.84

# Navigate to deployment directory
cd /opt/wizardsofts-megabuild

# Stop Appwrite services
docker compose -f docker-compose.appwrite.yml --env-file .env.appwrite down

# Check logs for errors
docker logs appwrite 2>&1 | tail -100
docker logs appwrite-console 2>&1 | tail -50
docker logs appwrite-mariadb 2>&1 | tail -50
```

### Option 3: Clean Reinstall
```bash
# Stop all Appwrite containers
docker compose -f docker-compose.appwrite.yml down -v

# Remove all Appwrite data
sudo rm -rf /mnt/data/docker/appwrite/*

# Re-run GitLab deployment
# (Click "Play" on deploy-appwrite job again)
```

---

## Next Steps After Successful Deployment

### Immediate (First 10 minutes)

1. **Create BondWala Project**:
   - Login to console
   - Click "Create Project"
   - Name: "BondWala"
   - Project ID: Auto-generated (save this!)

2. **Add Platforms**:
   - iOS App: Bundle ID from BondWala iOS app
   - Android App: Package name from BondWala Android app
   - Web App: https://bondwala.com

3. **Generate API Keys**:
   - Server Key: All messaging scopes
   - Client Key: Limited to user scopes
   - Save keys securely

### Short-term (First Day)

1. **Configure Push Providers**:
   - APNs: Upload .p8 key file
   - FCM: Add Firebase service account JSON

2. **Create Messaging Topics**:
   - `all-users` - Broadcast to everyone
   - `win-alerts` - Winner notifications
   - `draw-updates` - New draw announcements
   - `reminders` - User check-in reminders

3. **Test Push Notification**:
   - Send test notification via console
   - Verify delivery to test device

### Medium-term (First Week)

1. **Update BondWala Backend**:
   - Install `node-appwrite` SDK
   - Create messaging service
   - Update notification endpoints
   - Remove Firebase Admin SDK

2. **Update BondWala Mobile App**:
   - Install `react-native-appwrite` SDK
   - Update push token registration
   - Test end-to-end notifications

3. **Load Testing**:
   - Send 1,000 notifications
   - Monitor resource usage
   - Verify delivery rates

---

## Troubleshooting Guide

### Issue: Pipeline Job Skipped

**Symptom**: `deploy-appwrite` job shows "Skipped"

**Cause**: No Appwrite files changed in commit

**Solution**:
```bash
# Touch a file to force deployment
touch docker-compose.appwrite.yml
git add docker-compose.appwrite.yml
git commit -m "chore: Force Appwrite redeployment"
git push origin main
```

### Issue: rsync Permission Denied

**Symptom**: `Permission denied (publickey)` during rsync

**Cause**: GitLab runner SSH key not configured

**Solution**: Ensure `$SSH_PRIVATE_KEY` secret is set in GitLab CI/CD settings

### Issue: Console Project Not Created

**Symptom**: Pipeline shows "ERROR: Console project still not created after restart"

**Cause**: Appwrite initialization failed

**Solution**:
```bash
# SSH to server
ssh wizardsofts@10.0.0.84

# Check Appwrite logs
docker logs appwrite 2>&1 | grep -i "error\|console\|project"

# Manual restart
docker restart appwrite
sleep 90

# Verify
docker exec appwrite-mariadb mysql -u wizardsofts -p'W1z4rdS0fts2025Secure' -D appwrite \
  -e "SELECT COUNT(*) FROM _console_projects"
```

### Issue: 404 on Console Access

**Symptom**: `https://appwrite.wizardsofts.com/console` returns 404

**Possible Causes**:
1. Traefik routing not configured
2. Console container not running
3. Network misconfiguration

**Solution**:
```bash
# Check Traefik routes
docker exec traefik wget -qO- http://localhost:8080/api/http/routers | grep appwrite

# Check console container
docker ps | grep appwrite-console

# Check networks
docker network inspect microservices-overlay | grep appwrite-console
```

### Issue: 500 Error on /v1/console/variables

**Symptom**: Console loads but API calls fail with 500 error

**Cause**: Console env.js not configured or endpoint incorrect

**Solution**:
```bash
# Verify console env.js
docker exec appwrite-console cat /usr/share/nginx/html/console/_app/env.js | grep ENDPOINT

# Expected: "PUBLIC_APPWRITE_ENDPOINT":"https://appwrite.wizardsofts.com/v1"

# If empty, recopy
docker cp traefik/console-env.js appwrite-console:/usr/share/nginx/html/console/_app/env.js
docker restart appwrite-console
```

---

## Resource Monitoring

### Memory Usage Tracking

```bash
# Check Appwrite container memory
docker stats appwrite --no-stream

# Check MariaDB memory
docker stats appwrite-mariadb --no-stream

# Check Redis memory
docker stats appwrite-redis --no-stream

# Total Appwrite memory
docker stats --format "table {{.Name}}\t{{.MemUsage}}" --no-stream | grep appwrite
```

**Expected Memory Usage**:
- Appwrite Core: ~1-2GB
- MariaDB: ~256-512MB (limit: 512MB)
- Redis: ~50-100MB (limit: 512MB)
- Workers: ~100-300MB each
- **Total**: ~3-5GB for all Appwrite services

### Disk Space Monitoring

```bash
# Check Appwrite data usage
sudo du -sh /mnt/data/docker/appwrite/*

# Expected:
# mariadb: ~500MB - 2GB (grows with data)
# redis: ~10-50MB
# uploads: ~100MB - 10GB (user files)
# functions: ~50-500MB
```

---

## Files Modified/Created

### Modified Files
- `.gitlab-ci.yml` - Added `deploy-appwrite` job (lines 400-567)
- `docker-compose.appwrite.yml` - Optimized database memory limits

### Created Files
- `.env.appwrite` - Production environment configuration
- `traefik/console-env.js` - Console environment configuration
- `APPWRITE_CICD_DEPLOYMENT_READY.md` - This document

### Documentation Files
- `APPWRITE_FRESH_INSTALL_GUIDE.md` - Complete installation guide
- `APPWRITE_GAP_ANALYSIS.md` - Documentation gaps analysis
- `APPWRITE_SETUP_SUMMARY.md` - Original setup documentation

---

## Important Notes

1. **Manual Trigger Required**: The `deploy-appwrite` job has `when: manual` - you MUST click "Play" in GitLab UI

2. **Fresh Installation**: The deployment script performs a CLEAN INSTALL by removing all old Appwrite data

3. **Database Password**: Ensure `.env.appwrite` password matches deployment script (W1z4rdS0fts2025Secure)

4. **Console Configuration**: The console-env.js file is copied AFTER container starts (cannot use volume mount due to Docker Snap restrictions)

5. **Initialization Time**: Appwrite requires ~2 minutes to initialize - DO NOT access console before initialization completes

6. **First Signup**: Email MUST be from `_APP_CONSOLE_WHITELIST_EMAILS` or signup will be rejected

7. **DNS Requirement**: Ensure `appwrite.wizardsofts.com` DNS A record points to 10.0.0.84

8. **Traefik Requirement**: Traefik reverse proxy must be running and configured

---

## Support & Contact

**Deployment Issues**: Review pipeline logs in GitLab
**Console Issues**: Check [APPWRITE_GAP_ANALYSIS.md](APPWRITE_GAP_ANALYSIS.md)
**Installation Help**: See [APPWRITE_FRESH_INSTALL_GUIDE.md](APPWRITE_FRESH_INSTALL_GUIDE.md)

---

**Ready to Deploy**: ✅ YES
**Deployment Method**: GitLab CI/CD Pipeline → Manual Trigger
**Estimated Time**: 3-4 minutes
**Risk Level**: LOW (Fresh installation with automatic verification)

**Next Action**: Commit changes and push to GitLab, then trigger deployment manually.

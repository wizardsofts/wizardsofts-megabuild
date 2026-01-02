# Coming Soon Page Deployment Guide

## Status: Code Complete ✅

The Coming Soon feature for guardianinvestmentbd.com has been **fully implemented and committed** to the repository.

**Latest Commit**: `31b30a4 - feat: Add Coming Soon page for guardianinvestmentbd.com domain`

---

## What's Implemented

### 1. **Next.js Middleware** (`apps/gibd-quant-web/middleware.ts`)
- Intercepts all requests to guardianinvestmentbd.com and www.guardianinvestmentbd.com
- Routes production domain requests to `/coming-soon` page
- Allows full app access when accessed via:
  - Local IP (10.0.0.84)
  - Localhost (127.0.0.1)
  - Custom domains (testing)

### 2. **Coming Soon Page** (`apps/gibd-quant-web/app/coming-soon/page.tsx`)
- Beautiful gradient background (slate-900 to blue-900)
- Feature preview cards:
  - Trading Signals
  - AI-Powered Analysis
  - DSE Focused Platform
- Contact email: **info@guardianinvestmentbd.com** (clickable mailto link)
- Professional styling with animations

### 3. **Layout Override** (`apps/gibd-quant-web/app/coming-soon/layout.tsx`)
- Full-screen overlay (z-50) positioned to display on top of root layout
- Ensures Coming Soon page shows regardless of navigation

### 4. **Documentation** (`apps/gibd-quant-web/README.md`)
- Explains how to enable/disable Coming Soon mode
- Lists contact email
- Instructions for configuration

---

## Deployment Steps

### Option 1: Manual Deployment via SSH (Recommended)

```bash
# SSH into server
ssh wizardsofts@10.0.0.84  # Password: 29Dec2#24

# Navigate to deployment directory
cd /opt/wizardsofts-megabuild  # or /home/wizardsofts/wizardsofts-megabuild

# Pull latest code
git pull origin master

# Rebuild the gibd-quant-web Docker image (with Coming Soon middleware)
docker-compose build gibd-quant-web

# Start the updated service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d gibd-quant-web

# Verify container is running
docker-compose ps | grep gibd-quant-web
```

### Option 2: GitLab CI/CD Pipeline (Automated)

The `.gitlab-ci.yml` file includes automated build and deploy stages:

```bash
# Push to master branch to trigger pipeline
git push origin master

# Monitor pipeline at: https://gitlab.com/wizardsofts/wizardsofts-megabuild/-/pipelines
# Stages:
# 1. detect - Detects changed services
# 2. test - Runs tests (skipped for Coming Soon changes)
# 3. build - Builds Docker images
# 4. deploy - Deploys to 10.0.0.84 (manual trigger)
```

---

## Testing the Implementation

### Test 1: Domain Access (Coming Soon Should Show)
```bash
curl -H "Host: www.guardianinvestmentbd.com" http://10.0.0.84/ -L | grep -i "coming soon"
```

### Test 2: Local IP Access (Full App Should Show)
```bash
curl http://10.0.0.84:3000/ | grep -i "Coming" || echo "✅ Full app loaded (no coming soon)"
```

### Test 3: Browser Test (Domain)
```
https://www.guardianinvestmentbd.com
→ Should show Coming Soon page with info@guardianinvestmentbd.com
```

### Test 4: Browser Test (Local IP)
```
http://10.0.0.84:3000
→ Should show full trading signals application
```

---

## Current Issue: Backend Services Not Running

The multi-criteria feature (`/signals` route) depends on the **API Gateway** (ws-gateway) service.

### Required Services for Full Functionality:
- ✅ **gibd-quant-web** - Frontend (needed for Coming Soon)
- ⚠️ **ws-gateway** - API Gateway (needed for multi-criteria)
- ⚠️ **ws-discovery** - Eureka Service Discovery
- ⚠️ **postgres** - Database
- ⚠️ **gibd-quant-nlq** - NLQ Query Service

### Start Backend Services:
```bash
ssh wizardsofts@10.0.0.84

cd /opt/wizardsofts-megabuild

# Start services with gibd-quant profile (includes all required services)
docker-compose --profile gibd-quant up -d

# Wait for services to become healthy (2-5 minutes for first build)
docker-compose ps

# Check specific service health
curl http://localhost:8080/actuator/health  # ws-gateway
curl http://localhost:8761/actuator/health  # ws-discovery (Eureka)
```

---

## File Changes Summary

### New Files Created:
- `apps/gibd-quant-web/middleware.ts` - Request interception
- `apps/gibd-quant-web/app/coming-soon/page.tsx` - Coming Soon UI
- `apps/gibd-quant-web/app/coming-soon/layout.tsx` - Full-screen layout

### Modified Files:
- `apps/gibd-quant-web/README.md` - Documentation added
- `.gitlab-ci.yml` - Master branch support added
- Various app submodules updated (git status shows 'm' indicators)

---

## Docker Image Information

### Current Status:
- **Previous Image (v5)**: Built before Coming Soon code was added ❌
- **New Image (next build)**: Will include middleware.ts ✅

### Build Command:
```bash
# From /opt/wizardsofts-megabuild or deployment directory
docker-compose build gibd-quant-web

# With buildkit for faster builds
DOCKER_BUILDKIT=1 docker-compose build gibd-quant-web
```

### Image Details:
- **Dockerfile**: `apps/gibd-quant-web/Dockerfile`
- **Standalone Dockerfile**: `apps/gibd-quant-web/Dockerfile.standalone`
- **Base Image**: node:18-alpine
- **Runtime Base**: node:18-alpine

---

## Troubleshooting

### Issue: Coming Soon page not showing

**Symptoms**: Full app appears when accessing www.guardianinvestmentbd.com

**Causes**:
1. ❌ Docker image is old (v5, built before Coming Soon code)
2. ❌ Container hasn't been restarted after code update
3. ❌ Middleware.ts is not compiled into the image

**Solution**:
```bash
# Rebuild image
docker-compose build --no-cache gibd-quant-web

# Restart container
docker-compose down gibd-quant-web
docker-compose up -d gibd-quant-web

# Verify
curl -H "Host: www.guardianinvestmentbd.com" http://10.0.0.84/ | grep "Coming Soon"
```

### Issue: Backend services not responding

**Symptoms**: Multi-criteria page shows errors, API calls fail

**Causes**:
1. Services not started
2. Environment variables (.env) not loaded
3. Database not initialized
4. Eureka service discovery not healthy

**Solution**:
```bash
# Check .env file has DB_PASSWORD and OPENAI_API_KEY
grep "DB_PASSWORD\|OPENAI_API_KEY" .env

# Start all services
docker-compose --profile gibd-quant up -d

# Wait 2-5 minutes for services to start
sleep 120

# Check status
docker-compose ps
```

---

## Environment Variables Required

For the services to start, the following must be set in `.env`:

```bash
# Database
DB_PASSWORD=<your-password>

# OpenAI (for NLQ service)
OPENAI_API_KEY=sk-<your-key>

# All other variables are optional but recommended
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Browser / Client                                        │
└─────────────────────┬───────────────────────────────────┘
                      │
          HTTP/HTTPS  │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Traefik Reverse Proxy (Port 80, 443)                   │
│  Rules:                                                  │
│  - www.guardianinvestmentbd.com → gibd-quant-web:3000   │
│  - guardianinvestmentbd.com → gibd-quant-web:3000       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  gibd-quant-web Container (Next.js App)                 │
│  [PORT 3000]                                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  middleware.ts - Request Interceptor             │   │
│  │  (Checks Host header)                            │   │
│  └────────┬─────────────────────────────────────────┘   │
│           │                                              │
│           ├─→ Domain? → /coming-soon/page.tsx          │
│           └─→ Local IP? → Full App (/page.tsx)         │
└─────────────────────────────────────────────────────────┘

Optional: Backend Services (when API calls needed)
┌─────────────────────────────────────────────────────────┐
│  ws-gateway (API Gateway) [PORT 8080]                    │
│  ↓                                                        │
│  ws-discovery (Eureka) [PORT 8761]                       │
│  ↓                                                        │
│  Business Services:                                      │
│  - ws-trades, ws-company, ws-news                        │
│  - gibd-quant-nlq, gibd-quant-signal, etc              │
└─────────────────────────────────────────────────────────┘
```

---

## Git Commit History

```
0aafcb3 fix: Fix detect-changes stage to work with alpine git image
31b30a4 feat: Add Coming Soon page for guardianinvestmentbd.com domain  ← COMING SOON CODE
5662367 fix: Add master branch support to CI/CD pipeline
31b30a4 feat: Add Coming Soon page for guardianinvestmentbd.com domain
6fac61f docs: Update deployment summary - www.wizardsofts.com LIVE
```

---

## Next Steps

1. **SSH into server**:
   ```bash
   ssh wizardsofts@10.0.0.84
   ```

2. **Pull latest code**:
   ```bash
   cd /opt/wizardsofts-megabuild
   git pull origin master
   ```

3. **Rebuild Coming Soon image**:
   ```bash
   docker-compose build gibd-quant-web
   ```

4. **Restart service**:
   ```bash
   docker-compose up -d gibd-quant-web
   ```

5. **Verify it works**:
   ```bash
   curl -H "Host: www.guardianinvestmentbd.com" http://localhost/ | grep "Coming Soon"
   ```

6. **Check logs if issues**:
   ```bash
   docker-compose logs -f gibd-quant-web
   ```

---

**Note**: This deployment guide can be executed manually or automatically via the GitLab CI/CD pipeline by pushing to the `master` branch and triggering the deploy job.

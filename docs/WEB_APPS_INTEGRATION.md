# Web Applications Integration

**Date**: December 27, 2025
**Status**: Completed ✅

---

## Overview

Integrated two Next.js web applications into the wizardsofts-megabuild monorepo:

1. **www.wizardsofts.com** - Corporate website
2. **Daily Deen Guide** - Islamic prayer times and guidance application

---

## Services Added

### 1. ws-wizardsofts-web

**Source**: `/Users/mashfiqurrahman/Workspace/wizardsofts/www.wizardsofts.com/frontend`
**Location**: `apps/ws-wizardsofts-web`
**Framework**: Next.js 15.5.4
**Port**: 3000
**Profile**: `web-apps`, `all`

**Features**:
- Corporate website for Wizardsofts
- Multi-stage Docker build with node:20-bullseye-slim
- Production-ready standalone build
- Includes health check
- File-backed data storage for submissions

**Access**:
```bash
# Local development
http://localhost:3000

# Production (via Traefik)
https://www.wizardsofts.com
```

---

### 2. ws-daily-deen-web

**Source**: `/Users/mashfiqurrahman/Workspace/dailydeenguide/daily-deen-guide-frontend`
**Location**: `apps/ws-daily-deen-web`
**Framework**: Next.js 15.3.3
**Port**: 3002 (host) → 3000 (container)
**Profile**: `web-apps`, `all`

**Features**:
- Islamic prayer times calculator using adhan library
- Daily Islamic guidance and content
- Multi-stage Docker build with node:20-alpine
- Production-ready standalone build
- API proxy for hadith backend service

**Dependencies**:
- adhan: Islamic prayer times calculations
- react-icons: Icon library
- tailwindcss: Styling

**Access**:
```bash
# Local development
http://localhost:3002

# Production (via Traefik)
https://dailydeenguide.wizardsofts.com
```

---

## Docker Compose Configuration

Added new profile: `web-apps`

```yaml
ws-wizardsofts-web:
  build:
    context: ./apps/ws-wizardsofts-web
    dockerfile: Dockerfile
  profiles: ["web-apps", "all"]
  container_name: ws-wizardsofts-web
  ports:
    - "3000:3000"
  environment:
    - NODE_ENV=production
    - NEXT_TELEMETRY_DISABLED=1
  networks:
    - gibd-network
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
    interval: 30s
    timeout: 10s
    retries: 5

ws-daily-deen-web:
  build:
    context: ./apps/ws-daily-deen-web
    dockerfile: Dockerfile
  profiles: ["web-apps", "all"]
  container_name: ws-daily-deen-web
  ports:
    - "3002:3000"
  environment:
    - NODE_ENV=production
    - NEXT_TELEMETRY_DISABLED=1
  networks:
    - gibd-network
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
    interval: 30s
    timeout: 10s
    retries: 5
```

---

## Deployment Commands

### Deploy Web Apps Only
```bash
docker compose --profile web-apps up -d
```

### Deploy All Services
```bash
docker compose --profile all up -d
```

### Deploy Specific App
```bash
docker compose up -d ws-wizardsofts-web
docker compose up -d ws-daily-deen-web
```

### Stop Web Apps
```bash
docker compose --profile web-apps down
```

---

## Integration Checklist

- [x] Copy www.wizardsofts.com/frontend to apps/ws-wizardsofts-web
- [x] Copy daily-deen-guide-frontend to apps/ws-daily-deen-web
- [x] Verify Next.js standalone output configured
- [x] Add services to docker-compose.yml
- [x] Configure health checks
- [x] Add to new "web-apps" profile
- [x] Validate docker-compose configuration
- [ ] Test local deployment
- [ ] Update GitLab CI/CD pipeline for new services
- [ ] Configure Traefik routes for production
- [ ] Set up DNS records

---

## Production Deployment

### Traefik Configuration Needed

**ws-wizardsofts-web**:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.wizardsofts.rule=Host(`www.wizardsofts.com`)"
  - "traefik.http.routers.wizardsofts.entrypoints=websecure"
  - "traefik.http.routers.wizardsofts.tls.certresolver=letsencrypt"
  - "traefik.http.services.wizardsofts.loadbalancer.server.port=3000"
```

**ws-daily-deen-web**:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.dailydeen.rule=Host(`dailydeenguide.wizardsofts.com`)"
  - "traefik.http.routers.dailydeen.entrypoints=websecure"
  - "traefik.http.routers.dailydeen.tls.certresolver=letsencrypt"
  - "traefik.http.services.dailydeen.loadbalancer.server.port=3000"
```

### DNS Records Needed

| Domain | Type | Value |
|--------|------|-------|
| www.wizardsofts.com | A | 10.0.0.84 |
| dailydeenguide.wizardsofts.com | A | 10.0.0.84 |

---

## Testing Plan

### Local Testing

1. **Build services**:
   ```bash
   docker compose --profile web-apps build
   ```

2. **Start services**:
   ```bash
   docker compose --profile web-apps up -d
   ```

3. **Check health**:
   ```bash
   docker compose ps
   curl http://localhost:3000  # wizardsofts.com
   curl http://localhost:3002  # daily-deen-guide
   ```

4. **View logs**:
   ```bash
   docker compose logs -f ws-wizardsofts-web
   docker compose logs -f ws-daily-deen-web
   ```

### Playwright E2E Tests

**ws-wizardsofts-web**:
- [ ] Homepage loads successfully
- [ ] Navigation works
- [ ] Contact form submission
- [ ] Mobile responsive layout
- [ ] Accessibility check (axe)

**ws-daily-deen-web**:
- [ ] Homepage loads successfully
- [ ] Prayer times display correctly
- [ ] Hadith content loads
- [ ] Islamic date conversion works
- [ ] Mobile responsive layout

---

## Monorepo Structure Update

```
wizardsofts-megabuild/
├── apps/
│   ├── ws-discovery/              # Eureka service discovery
│   ├── ws-gateway/                # Spring Cloud Gateway
│   ├── ws-trades/                 # Trades API
│   ├── ws-company/                # Company info API
│   ├── ws-news/                   # News API
│   ├── gibd-quant-signal/         # ML signal generation
│   ├── gibd-quant-nlq/            # Natural language queries
│   ├── gibd-quant-calibration/    # Stock calibration
│   ├── gibd-quant-agent/          # LangGraph agents
│   ├── gibd-quant-celery/         # Celery workers
│   ├── gibd-quant-web/            # Quant-Flow frontend
│   ├── ws-wizardsofts-web/        # ✨ NEW: Corporate website
│   └── ws-daily-deen-web/         # ✨ NEW: Daily Deen Guide
```

---

## GitLab CI/CD Updates Needed

Add jobs for new services in [.gitlab-ci.yml](../.gitlab-ci.yml):

```yaml
build:ws-wizardsofts-web:
  extends: .build-nextjs
  variables:
    SERVICE_NAME: ws-wizardsofts-web
  only:
    changes:
      - apps/ws-wizardsofts-web/**/*
      - docker-compose.yml

build:ws-daily-deen-web:
  extends: .build-nextjs
  variables:
    SERVICE_NAME: ws-daily-deen-web
  only:
    changes:
      - apps/ws-daily-deen-web/**/*
      - docker-compose.yml

deploy:web-apps:
  stage: deploy
  script:
    - docker compose --profile web-apps up -d
  only:
    changes:
      - apps/ws-wizardsofts-web/**/*
      - apps/ws-daily-deen-web/**/*
```

---

## Environment Variables

No additional environment variables needed for basic deployment.

**Optional** (for analytics):
- `NEXT_PUBLIC_GA_MEASUREMENT_ID` - Google Analytics
- `NEXT_PUBLIC_ADSENSE_CLIENT_ID` - Google AdSense

---

## Known Issues

None at this time.

---

## Next Steps

1. ✅ Copy projects to monorepo
2. ✅ Add to docker-compose.yml
3. ✅ Configure health checks
4. ⏸️ Test local deployment
5. ⏸️ Update GitLab CI/CD
6. ⏸️ Configure Traefik routes
7. ⏸️ Set up DNS records
8. ⏸️ Deploy to production

---

## References

- [www.wizardsofts.com](https://www.wizardsofts.com)
- [Daily Deen Guide](https://dailydeenguide.wizardsofts.com)
- [Next.js Documentation](https://nextjs.org/docs)
- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/)

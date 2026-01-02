# Environment Configuration Guide

## Overview

This guide explains how to configure the `.env` file for the WizardSofts Megabuild deployment on 10.0.0.84.

**Important**: The `.env` file is **NOT committed to git** for security reasons. You must manually create and configure it on the server.

---

## Configuration for 10.0.0.84 Server

Copy this entire `.env` configuration to `/opt/wizardsofts-megabuild/.env`:

```bash
# ============================================================================
# APPLICATION SERVICES
# ============================================================================

# Database Configuration - REQUIRED for backend services
DB_PASSWORD=29Dec2#24

# OpenAI API - OPTIONAL but needed for NLQ (Natural Language Query) features
# If not provided, AI features will be disabled (graceful fallback)
OPENAI_API_KEY=sk-your-openai-api-key-here

# ============================================================================
# GIBD QUANT WEB - Guardian Investment BD (Trading Platform)
# apps/gibd-quant-web - uses NEXT_PUBLIC_* prefix for client-side access
# ============================================================================

# Google Analytics - Trading Platform Analytics
# Get ID from: https://analytics.google.com/
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Google AdSense - For trading signals page ads
# Get ID from: https://adsense.google.com/
NEXT_PUBLIC_ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
NEXT_PUBLIC_ADSENSE_BANNER_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_INFEED_SLOT=XXXXXXXXXX

# NOTE: ws-daily-deen-web and pf-padmafoods-web also use NEXT_PUBLIC_GA_MEASUREMENT_ID
# Each app should ideally have separate GA IDs but currently share the same variable

# ============================================================================
# INFRASTRUCTURE SERVICES
# ============================================================================

# Keycloak (Authentication) - OPTIONAL
KEYCLOAK_DB_PASSWORD=keycloak_db_password
KEYCLOAK_ADMIN_PASSWORD=Keycl0ak!Admin2025

# Traefik (Reverse Proxy) - REQUIRED
TRAEFIK_DASHBOARD_PASSWORD=W1z4rdS0fts!2025
ACME_EMAIL=admin@wizardsofts.com

# N8N (Workflow Automation) - OPTIONAL
N8N_PASSWORD=W1z4rdS0fts!2025

# Grafana (Monitoring) - OPTIONAL
GRAFANA_PASSWORD=W1z4rdS0fts!2025

# GitLab - OPTIONAL
GITLAB_ROOT_PASSWORD=29Dec2#24

# Infrastructure Database
INFRA_DB_PASSWORD=29Dec2#24

# ============================================================================
# OPTIONAL SERVICES
# ============================================================================

# Redis
REDIS_PASSWORD=

# Ollama (Local LLM)
OLLAMA_MODEL=llama3.1

# ============================================================================
# DEPLOYMENT CREDENTIALS (10.0.0.84 Server)
# ============================================================================

DEPLOY_HOST=10.0.0.84
DEPLOY_USER=wizardsofts
DEPLOY_PASSWORD=29Dec2#24
DEPLOY_PATH=/opt/wizardsofts-megabuild
```

---

## Step-by-Step Setup Instructions

### 1. SSH into Server

```bash
ssh wizardsofts@10.0.0.84
# Password: 29Dec2#24
```

### 2. Create .env File

```bash
cd /opt/wizardsofts-megabuild

# Create .env file
cat > .env << 'EOF'
DB_PASSWORD=29Dec2#24
OPENAI_API_KEY=sk-your-openai-api-key-here
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
NEXT_PUBLIC_ADSENSE_BANNER_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_INFEED_SLOT=XXXXXXXXXX
TRAEFIK_DASHBOARD_PASSWORD=W1z4rdS0fts!2025
ACME_EMAIL=admin@wizardsofts.com
DEPLOY_HOST=10.0.0.84
DEPLOY_USER=wizardsofts
DEPLOY_PASSWORD=29Dec2#24
DEPLOY_PATH=/opt/wizardsofts-megabuild
EOF

# Verify file was created
cat .env
```

### 3. Verify Required Variables

```bash
# Check critical variables are set
grep "DB_PASSWORD\|OPENAI_API_KEY" .env

# Expected output:
# DB_PASSWORD=29Dec2#24
# OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 4. Pull Latest Code

```bash
git pull origin master
```

### 5. Build and Start Services

```bash
# Rebuild all images with new environment
docker-compose build

# Start services with gibd-quant profile (includes all backend services)
docker-compose --profile gibd-quant up -d

# Monitor startup (wait 2-5 minutes for first build)
docker-compose logs -f
```

### 6. Verify Services Are Running

```bash
# Check container status
docker-compose ps

# Test critical endpoints
curl http://localhost:8080/actuator/health      # API Gateway
curl http://localhost:8761/actuator/health      # Eureka
curl http://localhost:3000/                     # Frontend
```

---

## Critical Variables Explained

### DB_PASSWORD (REQUIRED)
- Used by all Spring Boot services to connect to PostgreSQL database
- Services affected: ws-gateway, ws-discovery, ws-trades, ws-company, ws-news, gibd-quant-signal
- **Current value**: `29Dec2#24`
- **When to change**: When you update the PostgreSQL password

### OPENAI_API_KEY (OPTIONAL but Recommended)
- Enables Natural Language Query (NLQ) features in gibd-quant-nlq service
- Allows AI-powered stock analysis and chat features
- **Without it**: Multi-criteria queries still work, but AI features disabled
- **To obtain**: Create account at https://platform.openai.com and generate API key

### NEXT_PUBLIC_GA_MEASUREMENT_ID (OPTIONAL)
- Enables Google Analytics tracking on frontend
- Used by: gibd-quant-web, ws-daily-deen-web, pf-padmafoods-web
- **Format**: G-XXXXXXXXXX
- **To obtain**: Set up property in https://analytics.google.com/

### NEXT_PUBLIC_ADSENSE_* (OPTIONAL)
- Enables Google AdSense ads on trading signals page
- Used by: gibd-quant-web only
- **To obtain**: Apply for AdSense at https://adsense.google.com/

---

## App-Specific Variable Mapping

| App | Variables Used | Purpose |
|-----|-----------------|---------|
| **gibd-quant-web** | NEXT_PUBLIC_GA_MEASUREMENT_ID, NEXT_PUBLIC_ADSENSE_* | Trading platform analytics & ads |
| **ws-daily-deen-web** | NEXT_PUBLIC_GA_MEASUREMENT_ID | Islamic daily guide analytics |
| **pf-padmafoods-web** | NEXT_PUBLIC_GA_MEASUREMENT_ID | Food business analytics |
| **Backend Services** | DB_PASSWORD, OPENAI_API_KEY | Database & AI features |

---

## Minimal Configuration (To Get Services Running)

If you only have time to set up minimal config:

```bash
DB_PASSWORD=29Dec2#24
TRAEFIK_DASHBOARD_PASSWORD=W1z4rdS0fts!2025
ACME_EMAIL=admin@wizardsofts.com
DEPLOY_HOST=10.0.0.84
DEPLOY_USER=wizardsofts
DEPLOY_PASSWORD=29Dec2#24
DEPLOY_PATH=/opt/wizardsofts-megabuild

# Optional but recommended:
OPENAI_API_KEY=sk-your-key-here
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-your-id-here
```

This minimum config will:
- ✅ Start all backend services
- ✅ Enable frontend access
- ✅ Enable Traefik reverse proxy
- ❌ Disable OpenAI AI features (graceful fallback)
- ❌ Disable Google Analytics (silently ignored)
- ❌ Disable AdSense ads (not loaded)

---

## Troubleshooting

### Error: "Failed to connect to database"
**Cause**: `DB_PASSWORD` not set or incorrect
**Fix**: Verify `DB_PASSWORD=29Dec2#24` is in `.env`

### Error: "Services not starting"
**Cause**: `.env` file missing or not readable
**Fix**:
```bash
ls -la .env
cat .env | head -5
```

### OpenAI Features Not Working
**Cause**: `OPENAI_API_KEY` not set or invalid
**Fix**:
1. Generate API key at https://platform.openai.com
2. Update `.env` with `OPENAI_API_KEY=sk-your-real-key`
3. Restart services: `docker-compose restart gibd-quant-nlq`

### No Analytics Data Showing
**Cause**: `NEXT_PUBLIC_GA_MEASUREMENT_ID` not set
**Fix**:
1. Set up Google Analytics property at https://analytics.google.com/
2. Get measurement ID (format: G-XXXXXXXXXX)
3. Update `.env` and rebuild frontend: `docker-compose build gibd-quant-web`

---

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `.env` to git (it's in `.gitignore`)
- Keep `.env` file secure (contains sensitive credentials)
- Change default passwords in production
- Rotate `OPENAI_API_KEY` regularly
- Use strong database passwords

---

## Local Development Setup

For local development on your machine:

1. Copy `.env.example` to `.env.local`
2. Update values as needed
3. Docker-compose will load from `.env.local` automatically

```bash
cp .env.example .env.local
# Edit .env.local with your local values
docker-compose up -d
```

---

## References

- [COMING_SOON_DEPLOYMENT_GUIDE.md](./COMING_SOON_DEPLOYMENT_GUIDE.md)
- [EMERGENCY_RECOVERY.md](./EMERGENCY_RECOVERY.md)
- [docker-compose.yml](./docker-compose.yml)
- Environment variables in code:
  - [gibd-quant-web/components/analytics/](apps/gibd-quant-web/components/analytics/)
  - [ws-daily-deen-web/src/lib/gtag.ts](apps/ws-daily-deen-web/src/lib/gtag.ts)

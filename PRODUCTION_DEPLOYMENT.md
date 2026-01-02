# Production Deployment to 10.0.0.84

**Last Updated**: December 27, 2025

---

## 🔐 Security Architecture

This deployment uses **Traefik reverse proxy** for enterprise-grade security:

- ✅ **Only ports 80, 443, 8090 exposed** (Traefik entry points)
- ✅ **All services behind reverse proxy** with automatic SSL
- ✅ **Zero direct port access** to applications and databases
- ✅ **Let's Encrypt SSL** certificates (automatic renewal)
- ✅ **Rate limiting** and **DDoS protection**
- ✅ **Basic authentication** for admin interfaces
- ✅ **Centralized logging** and monitoring

**Attack Surface**: 1 entry point vs 10+ with direct ports

See [TRAEFIK_SECURITY_GUIDE.md](docs/TRAEFIK_SECURITY_GUIDE.md) for detailed security comparison.

---

## 🚀 Quick Deployment

### Prerequisites

1. **SSH Access**: Ensure SSH key is added to server
2. **Server Access**: Can reach 10.0.0.84 from your network
3. **Docker**: Docker and Docker Compose installed on server
4. **DNS**: Domain names configured (see DNS Configuration section)

---

## Option 1: Automated Deployment (Recommended)

### Setup SSH Access First

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096

# Copy SSH key to server
ssh-copy-id deploy@10.0.0.84

# Test connection
ssh deploy@10.0.0.84 "echo 'Connected successfully'"
```

### Run Deployment Script

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Deploy everything with production security
./scripts/deploy-to-84.sh
```

**This will**:
- Deploy with `docker-compose.prod.yml` (secure configuration)
- Remove all direct port exposures
- Route all traffic through Traefik
- Enable automatic SSL certificates

---

## Option 2: Manual Deployment

### Step 1: Copy Files to Server

```bash
# From your local machine
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

rsync -avz --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude 'target' \
    --exclude '.m2' \
    --exclude '.cache' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --progress \
    ./ deploy@10.0.0.84:/opt/wizardsofts-megabuild/
```

### Step 2: SSH to Server

```bash
ssh deploy@10.0.0.84
```

### Step 3: Deploy on Server (Production Mode)

```bash
cd /opt/wizardsofts-megabuild

# Create .env file (if doesn't exist)
if [ ! -f .env ]; then
    cp .env.example .env
    nano .env  # Edit with actual values
fi

# Stop existing services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Build all images
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all build

# Start all services (PRODUCTION MODE - secured with Traefik)
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d

# Check status
docker compose ps
```

**IMPORTANT**: Always use `-f docker-compose.yml -f docker-compose.prod.yml` in production to ensure security.

---

## 🌐 Production URLs (After DNS Configuration)

### Public Web Applications (HTTPS - No Auth Required)

| Application | URL | Description |
|-------------|-----|-------------|
| **Wizardsofts.com** | https://www.wizardsofts.com | Corporate website |
| **Daily Deen Guide** | https://dailydeenguide.wizardsofts.com | Islamic prayer times |
| **GIBD Quant-Flow** | https://quant.wizardsofts.com | Stock trading signals |

### API Services (HTTPS - Accessed by Applications)

| Service | URL | Description |
|---------|-----|-------------|
| **API Gateway** | https://api.wizardsofts.com | API gateway (internal routing) |

### Infrastructure Services (HTTPS - Basic Auth Required)

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **Eureka Dashboard** | https://eureka.wizardsofts.com | admin / [password] | Service registry |
| **Traefik Dashboard** | https://traefik.wizardsofts.com | admin / [password] | Reverse proxy dashboard |

### Temporary Access (Before DNS Configured)

| Service | URL | Description |
|---------|-----|-------------|
| **Traefik Dashboard** | http://10.0.0.84:8090 | Check routing status |

---

## 📋 DNS Configuration (REQUIRED)

### A Records

Add these to your DNS provider (Route53, Cloudflare, etc.):

```
# Web Applications
www.wizardsofts.com             A    10.0.0.84
dailydeenguide.wizardsofts.com  A    10.0.0.84
quant.wizardsofts.com           A    10.0.0.84

# API Services
api.wizardsofts.com             A    10.0.0.84

# Infrastructure Services
eureka.wizardsofts.com          A    10.0.0.84
traefik.wizardsofts.com         A    10.0.0.84

# Optional Infrastructure
id.wizardsofts.com              A    10.0.0.84  # Keycloak (if using)
gitlab.wizardsofts.com          A    10.0.0.84  # GitLab (if using)
nexus.wizardsofts.com           A    10.0.0.84  # Nexus (if using)
grafana.wizardsofts.com         A    10.0.0.84  # Grafana (if using)
n8n.wizardsofts.com             A    10.0.0.84  # n8n (if using)
mail.wizardsofts.com            A    10.0.0.84  # Mailcow (if using)

# VPN Server (Dynamic DNS)
vpn.wizardsofts.com             A    <updated by update_dns script>
```

### MX Records (for Mailcow - Optional)

```
@    MX    10    mail.wizardsofts.com
```

### TXT Records (SPF, DMARC - Optional)

```
@         TXT    "v=spf1 mx ~all"
_dmarc    TXT    "v=DMARC1; p=quarantine; rua=mailto:postmaster@wizardsofts.com"
```

---

## 🔒 Firewall Configuration

With Traefik, you only need to open 3 ports:

```bash
# Allow HTTP (redirects to HTTPS)
sudo ufw allow 80/tcp

# Allow HTTPS (SSL traffic)
sudo ufw allow 443/tcp

# Allow Traefik Dashboard (localhost only recommended)
sudo ufw allow 8090/tcp

# Enable firewall
sudo ufw enable
```

**That's it!** No need to open 10+ individual service ports.

---

## ✅ Health Checks

### Quick Test After Deployment

```bash
#!/bin/bash

HOST="10.0.0.84"

echo "Testing production services on $HOST..."
echo ""

# Check Traefik
echo "=== Traefik Reverse Proxy ==="
curl -I http://$HOST:80 2>&1 | head -1
curl -s http://$HOST:8090/api/overview | head -5

echo ""
echo "=== Note ==="
echo "All application services are secured behind Traefik"
echo "Direct port access is disabled for security"
echo ""
echo "Once DNS is configured, test services via domain names:"
echo "  curl https://www.wizardsofts.com"
echo "  curl https://dailydeenguide.wizardsofts.com"
echo "  curl https://quant.wizardsofts.com"
```

### Test via Domain Names (After DNS)

```bash
# Test public web applications (no auth required)
curl -I https://www.wizardsofts.com
curl -I https://dailydeenguide.wizardsofts.com
curl -I https://quant.wizardsofts.com

# Test API Gateway
curl -I https://api.wizardsofts.com

# Test infrastructure (requires basic auth)
curl -u admin:password https://eureka.wizardsofts.com
curl -u admin:password https://traefik.wizardsofts.com
```

---

## 🔧 Server Configuration

### Environment Variables (.env)

SSH to the server and edit `.env`:

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild
nano .env
```

**Required Variables**:

```bash
# Database
DB_PASSWORD=your_secure_password_here

# OpenAI (for NLQ and Agent services)
OPENAI_API_KEY=sk-your-actual-api-key

# Traefik (for basic auth on admin interfaces)
# Generate password hash: htpasswd -nb admin your_password
TRAEFIK_ADMIN_PASSWORD_HASH=admin:$$apr1$$hGZ8qHVz$$xMvCb3QLm3ZnFnJlpZFT5.

# Email for Let's Encrypt SSL certificates
ACME_EMAIL=admin@wizardsofts.com

# Optional: Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX
ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX

# Optional Infrastructure (if using infrastructure services)
KEYCLOAK_DB_PASSWORD=keycloak_db_password
KEYCLOAK_ADMIN_PASSWORD=secure_password
N8N_PASSWORD=secure_password
GRAFANA_PASSWORD=secure_password
GITLAB_ROOT_PASSWORD=secure_password
INFRA_DB_PASSWORD=secure_password
NEXUS_ADMIN_PASSWORD=secure_password
```

### Generate Traefik Admin Password Hash

```bash
# Install htpasswd (if not installed)
sudo apt-get install apache2-utils

# Generate password hash
htpasswd -nb admin your_secure_password

# Copy output to .env as TRAEFIK_ADMIN_PASSWORD_HASH
```

---

## 🚀 Deployment Profiles

You can deploy specific subsets of services using profiles:

### Deploy Only Web Apps

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile web-apps up -d
```

**Services**: Traefik, Wizardsofts.com, Daily Deen Guide

---

### Deploy Only GIBD Quant-Flow

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile gibd-quant up -d
```

**Services**: Traefik, All ML services, Quant-Flow frontend, shared infrastructure

---

### Deploy Shared Services Only

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile shared up -d
```

**Services**: Traefik, Postgres, Redis, Eureka, Gateway, Spring Boot APIs

---

### Deploy Everything

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d
```

**Services**: All of the above

---

## 📊 Monitoring

### View Service Status

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild

# List all running containers
docker compose ps

# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# View logs for specific service
docker compose logs -f traefik
docker compose logs -f ws-wizardsofts-web
docker compose logs -f gibd-quant-signal

# Check resource usage
docker stats
```

### Check Traefik Dashboard

```bash
# Open in browser
http://10.0.0.84:8090

# Or via domain (after DNS + basic auth)
https://traefik.wizardsofts.com
```

The Traefik dashboard shows:
- All registered routes
- SSL certificate status
- Request metrics
- Active middlewares

### Check Eureka Registration

```bash
# Via domain name (requires basic auth)
curl -u admin:password https://eureka.wizardsofts.com/eureka/apps | grep -o '<app>[^<]*</app>'

# Expected services:
# - WS-DISCOVERY
# - WS-GATEWAY
# - WS-TRADES
# - WS-COMPANY
# - WS-NEWS
# - GIBD-QUANT-SIGNAL
# - GIBD-QUANT-NLQ
# - GIBD-QUANT-CALIBRATION
# - GIBD-QUANT-AGENT
```

---

## 🔄 Update Deployment

### Pull Latest Changes

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild

# Option 1: If using git
git pull origin main

# Option 2: Rsync from local (from your machine)
rsync -avz --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude 'target' \
    ./ deploy@10.0.0.84:/opt/wizardsofts-megabuild/
```

### Rebuild and Restart

```bash
ssh deploy@10.0.0.84
cd /opt/wizardsofts-megabuild

# Rebuild changed services
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all build

# Restart all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d

# Or restart specific service
docker compose restart ws-wizardsofts-web
```

---

## 🔥 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs <service-name>

# Check Traefik routing
docker compose logs traefik

# Restart service
docker compose restart <service-name>

# Remove and recreate
docker compose rm -f <service-name>
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d <service-name>
```

### SSL Certificate Issues

```bash
# Check Traefik logs
docker compose logs traefik | grep -i "acme\|certificate"

# Verify DNS is pointing to server
nslookup www.wizardsofts.com

# Check Let's Encrypt rate limits
# https://letsencrypt.org/docs/rate-limits/

# Clear certificates and regenerate
docker compose down
docker volume rm wizardsofts-megabuild_traefik-ssl
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Cannot Access Services via Domain

```bash
# 1. Verify DNS is configured
nslookup www.wizardsofts.com

# 2. Check Traefik is running
docker compose ps traefik

# 3. Check Traefik dashboard
curl http://10.0.0.84:8090/api/overview

# 4. Verify service has Traefik labels
docker inspect ws-wizardsofts-web | grep traefik

# 5. Check Traefik logs
docker compose logs traefik
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a --volumes -f

# Check disk usage
df -h
```

---

## 📝 Deployment Checklist

- [ ] SSH access configured to 10.0.0.84
- [ ] .env file created and populated
- [ ] DNS A records configured for all domains
- [ ] Firewall configured (ports 80, 443, 8090)
- [ ] Traefik admin password hash generated
- [ ] Let's Encrypt email configured
- [ ] Deploy with production override: `docker-compose.prod.yml`
- [ ] Verify Traefik is running (port 8090)
- [ ] Wait for SSL certificates to be generated (2-5 minutes)
- [ ] Test all public URLs via HTTPS
- [ ] Verify infrastructure URLs require auth
- [ ] Check Eureka service registration
- [ ] Run E2E tests with Playwright MCP

---

## 🔗 Quick Reference

**Production Security**:
- ✅ Only ports 80, 443, 8090 exposed (Traefik)
- ✅ All services behind reverse proxy with SSL
- ✅ Automatic HTTPS with Let's Encrypt
- ✅ Database and cache NOT accessible from internet

**Production URLs (After DNS)**:
- Wizardsofts.com: https://www.wizardsofts.com
- Daily Deen Guide: https://dailydeenguide.wizardsofts.com
- Quant-Flow: https://quant.wizardsofts.com
- API Gateway: https://api.wizardsofts.com

**Infrastructure (Auth Required)**:
- Eureka: https://eureka.wizardsofts.com (admin/password)
- Traefik: https://traefik.wizardsofts.com (admin/password)

**Temporary Access (Before DNS)**:
- Traefik Dashboard: http://10.0.0.84:8090

**Deployment Command**:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d
```

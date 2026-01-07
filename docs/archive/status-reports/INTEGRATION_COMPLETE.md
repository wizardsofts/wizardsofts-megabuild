# Wizardsofts Megabuild - Integration Complete

**Date**: December 27, 2025
**Status**: ✅ Integration Complete, Ready for Testing

---

## Executive Summary

Successfully integrated all Wizardsofts services into a unified monorepo with the following components:

### Infrastructure (Removed)
- ❌ **HAProxy** - Removed (using Traefik instead)
- ❌ **Nginx** - Removed (using Traefik instead)

### Infrastructure (Added/Documented)
- ✅ **VPN Server** - WireGuard VPN configuration documented in `infrastructure/vpn-server/`
- ✅ **Mailcow** - Mail server integration documented in docker-compose.infrastructure.yml
- ✅ **DNS Updater** - Route53 dynamic DNS updater in `infrastructure/update-dns/`

### Web Applications (Added)
- ✅ **ws-wizardsofts-web** - Corporate website (Port 3000)
- ✅ **ws-daily-deen-web** - Daily Deen Guide (Port 3002)

### Traefik Routes Configured
- ✅ `www.wizardsofts.com` → ws-wizardsofts-web:3000
- ✅ `dailydeenguide.wizardsofts.com` → ws-daily-deen-web:3000

### GitLab CI/CD Updated
- ✅ Added Next.js test stage
- ✅ Added health checks for new web apps
- ✅ Updated change detection for all services

---

## Monorepo Structure

```
wizardsofts-megabuild/
├── apps/
│   # Spring Boot Shared Services
│   ├── ws-discovery/              # Eureka (Port 8762)
│   ├── ws-gateway/                # Spring Cloud Gateway (Port 8080)
│   ├── ws-trades/                 # Trades API (Port 8182)
│   ├── ws-company/                # Company Info API (Port 8183)
│   ├── ws-news/                   # News API (Port 8184)
│
│   # GIBD Quant-Flow Python ML Services
│   ├── gibd-quant-signal/         # Signal Generation (Port 5001)
│   ├── gibd-quant-nlq/            # Natural Language Queries (Port 5002)
│   ├── gibd-quant-calibration/    # Stock Calibration (Port 5003)
│   ├── gibd-quant-agent/          # LangGraph Agents (Port 5004)
│   ├── gibd-quant-celery/         # Celery Workers
│   ├── gibd-quant-web/            # Quant-Flow Frontend (Port 3001)
│
│   # Web Applications
│   ├── ws-wizardsofts-web/        # ✨ Corporate Website (Port 3000)
│   └── ws-daily-deen-web/         # ✨ Daily Deen Guide (Port 3002)
│
├── infrastructure/
│   ├── vpn-server/                # ✨ WireGuard VPN setup
│   ├── update-dns/                # ✨ Route53 DNS updater
│   ├── auto-scaling/
│   │   ├── prometheus/            # Prometheus config
│   │   └── grafana/               # Grafana dashboards
│   └── monitoring/
│
├── docker-compose.yml             # Application services
├── docker-compose.infrastructure.yml  # Infrastructure services
└── .gitlab-ci.yml                 # CI/CD pipeline
```

---

## Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| `shared` | Postgres, Redis, Eureka, Gateway, Trades, Company, News | Shared infrastructure |
| `gibd-quant` | All shared + ML services + Quant-Flow frontend | GIBD Quant ecosystem |
| `web-apps` | Wizardsofts.com + Daily Deen Guide | Corporate websites |
| `all` | Everything | Complete deployment |

### Deployment Commands

```bash
# Deploy shared services only
docker compose --profile shared up -d

# Deploy GIBD Quant-Flow
docker compose --profile gibd-quant up -d

# Deploy web apps only
docker compose --profile web-apps up -d

# Deploy everything
docker compose --profile all up -d
```

---

## Infrastructure Services (docker-compose.infrastructure.yml)

| Service | Profile | Port | Description |
|---------|---------|------|-------------|
| traefik | infrastructure, proxy | 80, 443, 8090 | Reverse proxy with Let's Encrypt |
| keycloak | infrastructure, auth | 8080 | Identity & Access Management |
| gitlab | infrastructure, cicd | 80, 2222 | CI/CD Platform |
| nexus | infrastructure, cicd | 8081 | Artifact Repository |
| prometheus | infrastructure, monitoring | 9090 | Metrics Collection |
| grafana | infrastructure, monitoring | 3000 | Dashboards |
| ollama | infrastructure, ai | 11434 | AI Model Serving |
| n8n | infrastructure | 5678 | Workflow Automation |
| postgres-infra | infrastructure, data | 5432 | Infrastructure DB |
| redis-infra | infrastructure, data | 6379 | Infrastructure Cache |

---

## Port Mappings

### Application Services

| Service | Host Port | Container Port | URL |
|---------|-----------|----------------|-----|
| **Infrastructure** |
| Postgres | 5433 | 5432 | - |
| Redis | 6379 | 6379 | - |
| Eureka | 8762 | 8761 | http://localhost:8762 |
| Gateway | 8080 | 8080 | http://localhost:8080 |
| **Spring Boot APIs** |
| ws-trades | 8182 | 8182 | http://localhost:8182 |
| ws-company | 8183 | 8183 | http://localhost:8183 |
| ws-news | 8184 | 8184 | http://localhost:8184 |
| **Python ML Services** |
| gibd-quant-signal | 5001 | 5001 | http://localhost:5001 |
| gibd-quant-nlq | 5002 | 5002 | http://localhost:5002 |
| gibd-quant-calibration | 5003 | 5003 | http://localhost:5003 |
| gibd-quant-agent | 5004 | 5004 | http://localhost:5004 |
| **Frontends** |
| ws-wizardsofts-web | 3000 | 3000 | http://localhost:3000 |
| gibd-quant-web | 3001 | 3000 | http://localhost:3001 |
| ws-daily-deen-web | 3002 | 3000 | http://localhost:3002 |

### Infrastructure Services

| Service | Port | URL |
|---------|------|-----|
| Traefik Dashboard | 8090 | http://localhost:8090 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| Ollama | 11434 | http://localhost:11434 |
| Nexus | 8081 | http://localhost:8081 |

---

## Production DNS Records Needed

### Application Services
```
www.wizardsofts.com             A      10.0.0.84
dailydeenguide.wizardsofts.com  A      10.0.0.84
quant.wizardsofts.com           A      10.0.0.84  (for gibd-quant-web)
```

### Infrastructure Services
```
traefik.wizardsofts.com         A      10.0.0.84
id.wizardsofts.com              A      10.0.0.84  (Keycloak)
gitlab.wizardsofts.com          A      10.0.0.84
nexus.wizardsofts.com           A      10.0.0.84
grafana.wizardsofts.com         A      10.0.0.84
n8n.wizardsofts.com             A      10.0.0.84
```

### Mail Server (Mailcow)
```
mail.wizardsofts.com            A      10.0.0.84
@                               MX     mail.wizardsofts.com (Priority: 10)
@                               TXT    "v=spf1 mx ~all"
_dmarc                          TXT    "v=DMARC1; p=quarantine; rua=mailto:postmaster@wizardsofts.com"
```

### VPN Server
```
vpn.wizardsofts.com             A      Dynamic (updated by update_dns script)
```

---

## VPN Server Setup

**Location**: `infrastructure/vpn-server/`

### Configuration
- **Software**: WireGuard
- **VPN Subnet**: 10.8.0.0/24
- **Server IP**: 10.8.0.1
- **Port**: UDP 51820
- **Dynamic DNS**: vpn.wizardsofts.com (updated by Route53 script)

### Active Clients
| Username | VPN IP | Public Key |
|----------|--------|------------|
| client1  | 10.8.0.2 | HCe/SuLd4lLcSz7oWoMYf2Xg7T+kPsRUL8G1hp07ok8= |
| mashfiq  | 10.8.0.3 | kdepJCqAhWRQBycGhJyWN9gXHvREwO6dZwSuF8+41Bo= |

### Key Files
```
/etc/wireguard/
├── wg0.conf              # Server config
├── keys/                 # Private/public keys
└── peers/                # Client configs
```

---

## DNS Updater (Route53)

**Location**: `infrastructure/update-dns/`

### Setup
The DNS updater automatically updates Route53 A records with the current public IP.

**Files**:
- `update_dns_boto3.py` - Main script
- `domains_config.json` - Domain configuration
- `.env` - AWS credentials

**Deployment**:
```bash
# Install on server
sudo mkdir -p /opt/scripts/update_dns
sudo cp infrastructure/update-dns/* /opt/scripts/update_dns/

# Configure cron (every 10 minutes)
*/10 * * * * /opt/scripts/update_dns/update_dns_boto3.py >> /var/log/update_dns.log 2>&1
```

**domains_config.json** example:
```json
[
  {
    "domain": "vpn.wizardsofts.com.",
    "hosted_zone_id": "Z05973601H6LWFYYAF1V8"
  }
]
```

---

## Mailcow Integration

**Note**: Mailcow is installed separately but integrated with Traefik.

### Installation
```bash
cd /opt
git clone https://github.com/mailcow/mailcow-dockerized
cd mailcow-dockerized
./generate_config.sh
docker compose up -d
```

### Traefik Integration
Mailcow services expose labels for Traefik routing. See `docker-compose.infrastructure.yml` for documentation.

### Required DNS
- `mail.wizardsofts.com` A record
- MX record pointing to mail.wizardsofts.com
- SPF and DMARC TXT records

---

## GitLab CI/CD Pipeline

**File**: `.gitlab-ci.yml`

### Stages
1. **detect** - Detect which services changed
2. **test** - Run tests for changed services
3. **build** - Build Docker images
4. **deploy** - Deploy to 10.0.0.84

### Test Stages
- `test-spring-boot` - Maven tests for Spring Boot services
- `test-python` - Pytest for Python ML services
- `test-nextjs` - Build + lint for Next.js apps

### Deployment
- **Target**: 10.0.0.84
- **User**: deploy
- **Path**: /opt/wizardsofts-megabuild
- **Trigger**: Manual (for main branch)

### Health Checks
Automated health checks verify:
- Eureka (8762)
- Gateway (8080)
- All Python ML services (5001-5004)
- All frontends (3000, 3001, 3002)

---

## Traefik Routes Configured

### Application Services
```yaml
# Wizardsofts Corporate Website
www.wizardsofts.com → ws-wizardsofts-web:3000

# Daily Deen Guide
dailydeenguide.wizardsofts.com → ws-daily-deen-web:3000

# GIBD Quant-Flow (to be configured)
quant.wizardsofts.com → gibd-quant-web:3000
```

### Infrastructure Services
```yaml
# Traefik Dashboard
traefik.wizardsofts.com → traefik:8080

# Keycloak
id.wizardsofts.com → keycloak:8080

# GitLab
gitlab.wizardsofts.com → gitlab:80

# Nexus
nexus.wizardsofts.com → nexus:8081

# Grafana
grafana.wizardsofts.com → grafana:3000

# N8N
n8n.wizardsofts.com → n8n:5678
```

---

## Environment Variables

### Application Services (.env)
```bash
# Database
DB_PASSWORD=your_postgres_password

# OpenAI (for NLQ and Agent services)
OPENAI_API_KEY=sk-...

# Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX
ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
```

### Infrastructure Services
```bash
# Keycloak
KEYCLOAK_DB_PASSWORD=keycloak_db_password
KEYCLOAK_ADMIN_PASSWORD=Keycl0ak!Admin2025

# Traefik
TRAEFIK_DASHBOARD_PASSWORD=W1z4rdS0fts!2025

# N8N
N8N_PASSWORD=W1z4rdS0fts!2025

# Grafana
GRAFANA_PASSWORD=W1z4rdS0fts!2025

# GitLab
GITLAB_ROOT_PASSWORD=your_gitlab_password

# Infrastructure Database
INFRA_DB_PASSWORD=infrastructure_db_password

# Nexus
NEXUS_ADMIN_PASSWORD=your_nexus_password
```

### DNS Updater (.env)
```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=ap-southeast-1
```

---

## Testing Plan

### Local Testing

#### 1. Test Shared Services
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild

# Start shared services
docker compose --profile shared up -d

# Verify health
curl http://localhost:8762/actuator/health  # Eureka
curl http://localhost:8080/actuator/health  # Gateway
```

#### 2. Test Web Apps
```bash
# Start web apps
docker compose --profile web-apps up -d

# Verify health
curl http://localhost:3000  # Wizardsofts.com
curl http://localhost:3002  # Daily Deen Guide
```

#### 3. Test GIBD Quant-Flow
```bash
# Start GIBD Quant services
docker compose --profile gibd-quant up -d

# Verify ML services
curl http://localhost:5001/health  # Signal Service
curl http://localhost:5002/health  # NLQ Service
curl http://localhost:5003/health  # Calibration Service
curl http://localhost:5004/health  # Agent Service

# Verify frontend
curl http://localhost:3001
```

#### 4. Test Infrastructure
```bash
# Start infrastructure services
docker compose -f docker-compose.infrastructure.yml --profile infrastructure up -d

# Verify services
curl http://localhost:8090/api/overview  # Traefik
curl http://localhost:9090/-/healthy    # Prometheus
curl http://localhost:3000/api/health   # Grafana
```

### Playwright E2E Tests

#### Test Wizardsofts.com
- [ ] Homepage loads
- [ ] Navigation works
- [ ] Contact form functional
- [ ] Mobile responsive
- [ ] Accessibility audit passes

#### Test Daily Deen Guide
- [ ] Homepage loads
- [ ] Prayer times display
- [ ] Hadith content loads
- [ ] Islamic date conversion works
- [ ] Mobile responsive

#### Test GIBD Quant-Flow
- [ ] Homepage loads
- [ ] Signal generation works
- [ ] NLQ queries functional
- [ ] Company pages load
- [ ] Charts render

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] Update all `.env` files with production values
- [ ] Configure DNS records (A, MX, TXT)
- [ ] Set up SSL certificates (via Let's Encrypt/Traefik)
- [ ] Configure GitLab Runner on 10.0.0.84
- [ ] Install VPN server
- [ ] Set up DNS updater cron job
- [ ] Install Mailcow separately

### Deployment
- [ ] Push code to GitLab main branch
- [ ] Trigger manual deployment job
- [ ] Monitor health checks
- [ ] Verify all services running

### Post-Deployment
- [ ] Test all public URLs
- [ ] Monitor logs for errors
- [ ] Set up Grafana dashboards
- [ ] Configure Prometheus alerts
- [ ] Test VPN connectivity
- [ ] Test email delivery (Mailcow)
- [ ] Run Playwright E2E tests

---

## Known Issues

None at this time.

---

## Next Steps

1. ✅ Integration complete
2. ⏸️ Test local deployment
3. ⏸️ Deploy to 10.0.0.84
4. ⏸️ Configure production DNS
5. ⏸️ Set up monitoring alerts
6. ⏸️ Run Playwright E2E tests
7. ⏸️ Production verification

---

## References

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [WireGuard Documentation](https://www.wireguard.com/quickstart/)
- [Mailcow Documentation](https://docs.mailcow.email/)
- [AWS Route53 Documentation](https://docs.aws.amazon.com/route53/)
- [Spring Cloud Gateway](https://spring.io/projects/spring-cloud-gateway)
- [Next.js Documentation](https://nextjs.org/docs)

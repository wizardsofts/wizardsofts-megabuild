# Infrastructure Services Guide

This guide explains how to deploy and manage the infrastructure services alongside the GIBD Quant-Flow application services.

---

## Overview

The monorepo now includes **two Docker Compose files**:

1. **docker-compose.yml** - Application services (GIBD Quant-Flow)
2. **docker-compose.infrastructure.yml** - Infrastructure services (Traefik, Keycloak, GitLab, etc.)

Both files can be used together or separately for flexible deployment.

---

## Quick Start

### Deploy Everything (Applications + Infrastructure)

```bash
# Start all application and infrastructure services
docker compose -f docker-compose.yml -f docker-compose.infrastructure.yml \
  --profile gibd-quant --profile infrastructure up -d
```

### Deploy Only Applications

```bash
# Start only GIBD Quant-Flow services
docker compose --profile gibd-quant up -d
```

### Deploy Only Infrastructure

```bash
# Start only infrastructure services
docker compose -f docker-compose.infrastructure.yml --profile infrastructure up -d
```

---

## Infrastructure Profiles

Infrastructure services are organized into profiles:

| Profile | Services | Purpose |
|---------|----------|---------|
| `infrastructure` | All infrastructure services | Complete infrastructure stack |
| `proxy` | Traefik | Reverse proxy and load balancing |
| `auth` | Keycloak, Keycloak-Postgres | Authentication and SSO |
| `cicd` | GitLab, Nexus | CI/CD and artifact management |
| `monitoring` | Prometheus, Grafana | Metrics and dashboards |
| `ai` | Ollama | AI model serving |
| `data` | Redis-Infra, Postgres-Infra | Infrastructure data layer |

---

## Deployment Scenarios

### Scenario 1: Development Environment

Deploy only what you need:

```bash
# Start application services only
docker compose --profile gibd-quant up -d

# No infrastructure services needed for development
```

### Scenario 2: Production with Reverse Proxy

Deploy applications behind Traefik:

```bash
# Start Traefik + Applications
docker compose -f docker-compose.yml -f docker-compose.infrastructure.yml \
  --profile gibd-quant --profile proxy up -d
```

### Scenario 3: Full Production Stack

Deploy everything:

```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.infrastructure.yml \
  --profile gibd-quant --profile infrastructure up -d
```

### Scenario 4: Monitoring Stack Only

Deploy monitoring for existing services:

```bash
# Start Prometheus + Grafana
docker compose -f docker-compose.infrastructure.yml --profile monitoring up -d
```

### Scenario 5: Authentication Stack

Deploy Keycloak for SSO:

```bash
# Start Keycloak
docker compose -f docker-compose.infrastructure.yml --profile auth up -d
```

---

## Service Access

### Traefik (Reverse Proxy)

- **Dashboard**: http://localhost:8090 or https://traefik.wizardsofts.com
- **Credentials**: admin / W1z4rdS0fts!2025

**Features**:
- Automatic SSL certificates (Let's Encrypt)
- Load balancing
- Service discovery
- Dashboard for monitoring routes

### Keycloak (Authentication)

- **URL**: https://id.wizardsofts.com (requires DNS)
- **Admin Console**: https://id.wizardsofts.com/admin
- **Credentials**: admin / Keycl0ak!Admin2025

**Features**:
- Single Sign-On (SSO)
- OAuth2 / OIDC
- User management
- Multi-factor authentication

### GitLab (CI/CD)

- **URL**: https://gitlab.wizardsofts.com (requires DNS)
- **SSH Port**: 2222
- **Credentials**: root / [GITLAB_ROOT_PASSWORD from .env]

**Features**:
- Git repository hosting
- CI/CD pipelines
- Issue tracking
- Container registry

### Nexus (Artifact Repository)

- **URL**: https://nexus.wizardsofts.com (requires DNS)
- **Default Credentials**: admin / [NEXUS_ADMIN_PASSWORD from .env]

**Repositories**:
- Maven artifacts (port 8083)
- Docker registry (port 8082)
- NPM packages

### Prometheus (Metrics)

- **URL**: http://localhost:9090
- **Targets**: Configured in `infrastructure/auto-scaling/prometheus/prometheus.yml`

**Monitors**:
- Application services
- Infrastructure services
- System metrics

### Grafana (Dashboards)

- **URL**: http://localhost:3000 or https://grafana.wizardsofts.com
- **Credentials**: admin / W1z4rdS0fts!2025

**Dashboards**:
- System overview
- Application metrics
- Database metrics
- Custom dashboards

### N8N (Workflow Automation)

- **URL**: https://n8n.wizardsofts.com (requires DNS)
- **Credentials**: admin / W1z4rdS0fts!2025

**Use Cases**:
- Automated deployments
- Data synchronization
- Notification workflows
- API integrations

### Ollama (AI Models)

- **API**: http://localhost:11434
- **Models**: Configure in .env (OLLAMA_MODEL)

**Usage**:
```bash
# List models
curl http://localhost:11434/api/tags

# Generate text
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Why is the sky blue?"
}'
```

---

## DNS Configuration

For production deployment, configure DNS records:

```
traefik.wizardsofts.com    → 10.0.0.84
id.wizardsofts.com         → 10.0.0.84
gitlab.wizardsofts.com     → 10.0.0.84
nexus.wizardsofts.com      → 10.0.0.84
grafana.wizardsofts.com    → 10.0.0.84
n8n.wizardsofts.com        → 10.0.0.84
```

Or add to `/etc/hosts` for local testing:
```bash
echo "10.0.0.84 traefik.wizardsofts.com id.wizardsofts.com gitlab.wizardsofts.com nexus.wizardsofts.com grafana.wizardsofts.com n8n.wizardsofts.com" | sudo tee -a /etc/hosts
```

---

## Environment Configuration

### Required Variables

Copy `.env.example` to `.env` and configure:

```bash
# Infrastructure services
KEYCLOAK_ADMIN_PASSWORD=your_keycloak_password
TRAEFIK_DASHBOARD_PASSWORD=your_traefik_password
GRAFANA_PASSWORD=your_grafana_password
GITLAB_ROOT_PASSWORD=your_gitlab_password
INFRA_DB_PASSWORD=your_infra_db_password
```

### Optional Variables

```bash
# AI Services
OLLAMA_MODEL=llama3.1

# Redis
REDIS_PASSWORD=your_redis_password
```

---

## Service Management

### Start Services

```bash
# All infrastructure
docker compose -f docker-compose.infrastructure.yml --profile infrastructure up -d

# Specific profile
docker compose -f docker-compose.infrastructure.yml --profile monitoring up -d

# Combined (app + infrastructure)
docker compose -f docker-compose.yml -f docker-compose.infrastructure.yml \
  --profile gibd-quant --profile infrastructure up -d
```

### Stop Services

```bash
# Stop infrastructure
docker compose -f docker-compose.infrastructure.yml down

# Stop applications
docker compose down

# Stop everything
docker compose -f docker-compose.yml -f docker-compose.infrastructure.yml down
```

### View Logs

```bash
# All infrastructure logs
docker compose -f docker-compose.infrastructure.yml logs -f

# Specific service
docker compose -f docker-compose.infrastructure.yml logs -f traefik
docker compose -f docker-compose.infrastructure.yml logs -f keycloak
```

### Check Status

```bash
# List running services
docker compose -f docker-compose.infrastructure.yml ps

# Check specific service health
docker compose -f docker-compose.infrastructure.yml ps traefik
```

---

## Health Checks

All infrastructure services have health checks configured:

```bash
# Check Traefik
curl http://localhost:8090/api/overview

# Check Keycloak
curl http://localhost:8080/health

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check Ollama
curl http://localhost:11434/api/tags
```

---

## Monitoring & Metrics

### Prometheus Metrics

Services expose metrics for Prometheus:

- **Application Services**: `/actuator/prometheus` (Spring Boot)
- **Traefik**: Built-in Prometheus endpoint
- **Infrastructure**: Node exporter, cAdvisor

### Grafana Dashboards

Import pre-configured dashboards:

1. Open Grafana: http://localhost:3000
2. Go to **Dashboards** → **Import**
3. Import from `infrastructure/auto-scaling/grafana/dashboards/`

Available dashboards:
- Docker Container Metrics
- Spring Boot Metrics
- PostgreSQL Metrics
- Redis Metrics
- Node Exporter

---

## Security Best Practices

### 1. Change Default Passwords

Update all default passwords in `.env`:
- Keycloak admin password
- Traefik dashboard password
- Grafana password
- GitLab root password
- Database passwords

### 2. SSL Certificates

Traefik automatically provisions Let's Encrypt SSL certificates when:
- DNS is properly configured
- Services are publicly accessible
- Email is set in Traefik config

### 3. Network Isolation

Services use isolated Docker networks:
- `traefik-public`: Public-facing services
- `backend`: Internal services (databases)
- `monitoring`: Metrics collection
- `gibd-network`: Application services

### 4. Secrets Management

**Never commit `.env` to git**:
- `.env` is gitignored
- Use environment-specific `.env.production`, `.env.staging`
- Use secrets management tools (Vault, AWS Secrets Manager)

### 5. Firewall Configuration

Configure firewall rules:
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 2222/tcp  # GitLab SSH

# Deny all others
sudo ufw default deny incoming
sudo ufw enable
```

---

## Backup & Recovery

### Database Backups

```bash
# Backup Keycloak database
docker exec keycloak-postgres pg_dump -U keycloak keycloak > keycloak-backup.sql

# Backup infrastructure database
docker exec postgres-infra pg_dump -U infrastructure n8n > n8n-backup.sql

# Backup application database
docker exec postgres pg_dump -U gibd ws_gibd_dse_daily_trades > trades-backup.sql
```

### Volume Backups

```bash
# Backup all Docker volumes
docker run --rm -v wizardsofts-megabuild_traefik-ssl:/data -v $(pwd):/backup alpine \
  tar -czf /backup/traefik-ssl-backup.tar.gz -C /data .

# Backup GitLab data
docker run --rm -v wizardsofts-megabuild_gitlab-data:/data -v $(pwd):/backup alpine \
  tar -czf /backup/gitlab-data-backup.tar.gz -C /data .
```

### Configuration Backups

```bash
# Backup infrastructure configs
tar -czf infrastructure-config-$(date +%Y%m%d).tar.gz infrastructure/
```

---

## Troubleshooting

### Service Won't Start

1. **Check logs**:
   ```bash
   docker compose -f docker-compose.infrastructure.yml logs service-name
   ```

2. **Check port conflicts**:
   ```bash
   sudo netstat -tlnp | grep PORT
   ```

3. **Check disk space**:
   ```bash
   df -h
   docker system df
   ```

### Traefik Can't Route Traffic

1. **Verify service labels**:
   ```bash
   docker inspect service-name | grep -i traefik
   ```

2. **Check Traefik dashboard**: http://localhost:8090

3. **Verify DNS/hosts file**:
   ```bash
   ping traefik.wizardsofts.com
   ```

### Keycloak Login Issues

1. **Check database connection**:
   ```bash
   docker compose -f docker-compose.infrastructure.yml logs keycloak-postgres
   ```

2. **Reset admin password**:
   ```bash
   docker compose -f docker-compose.infrastructure.yml exec keycloak \
     /opt/keycloak/bin/kcadm.sh set-password --target-realm master --username admin --new-password NewPassword
   ```

### GitLab Not Accessible

1. **Check container status**:
   ```bash
   docker compose -f docker-compose.infrastructure.yml ps gitlab
   ```

2. **GitLab takes 2-3 minutes to fully start**, check logs:
   ```bash
   docker compose -f docker-compose.infrastructure.yml logs -f gitlab
   ```

3. **Verify port 2222 is available** for SSH

---

## Performance Tuning

### Resource Limits

Add resource limits to services in `docker-compose.infrastructure.yml`:

```yaml
services:
  gitlab:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Prometheus Retention

Configure data retention in Prometheus config:
```yaml
# infrastructure/auto-scaling/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
storage:
  tsdb:
    retention.time: 30d
```

---

## Integration with Applications

### Keycloak Authentication

Configure application services to use Keycloak:

1. Create realm in Keycloak
2. Create client for each application
3. Configure application with OIDC settings

Example for Spring Boot:
```yaml
spring:
  security:
    oauth2:
      client:
        provider:
          keycloak:
            issuer-uri: https://id.wizardsofts.com/realms/wizardsofts
        registration:
          keycloak:
            client-id: gibd-quant-web
            client-secret: your-client-secret
```

### Traefik Routing

Add labels to application services for Traefik routing:

```yaml
services:
  gibd-quant-web:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.quant-web.rule=Host(`quant.wizardsofts.com`)"
      - "traefik.http.routers.quant-web.entrypoints=websecure"
      - "traefik.http.routers.quant-web.tls.certresolver=letsencrypt"
```

---

## Migration from server-setup

All services were migrated from `/Users/mashfiqurrahman/Workspace/wizardsofts/server-setup`:

- ✅ Docker Compose files consolidated
- ✅ Configuration files preserved
- ✅ Security hardening maintained
- ✅ Documentation updated
- ✅ Integrated with application services

---

## Support

For issues:
1. Check service logs
2. Review [infrastructure/README.md](../infrastructure/README.md)
3. Check [infrastructure/server_readme.md](../infrastructure/server_readme.md)
4. Review security hardening guides

## Next Steps

1. Configure DNS for production domains
2. Set up SSL certificates with Let's Encrypt
3. Configure Keycloak realms and clients
4. Set up Prometheus alerts
5. Create Grafana dashboards
6. Configure GitLab runners
7. Set up automated backups

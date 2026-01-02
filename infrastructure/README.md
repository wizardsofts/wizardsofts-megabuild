# Infrastructure Services

This directory contains shared infrastructure services that support the entire Wizardsofts ecosystem across multiple servers.

## Overview

These services provide core infrastructure capabilities:
- **Authentication & Authorization** (Keycloak)
- **Reverse Proxy & Load Balancing** (Traefik)
- **CI/CD** (GitLab, GitLab Runner)
- **Data Storage** (PostgreSQL, Redis)
- **Artifact Management** (Nexus)
- **AI/ML** (Ollama, LLM Server)
- **Workflow Automation** (N8N)
- **Auto-scaling** (Prometheus, Grafana)
- **Security Hardening** (Scripts and configurations)

---

## Server Network

| Server | IP Address | Purpose |
|--------|------------|---------|
| HP | 10.0.0.80 | Primary development server |
| ASUS | 10.0.0.81 | Secondary server |
| HPRD | 10.0.0.82 | Production/staging server |
| GMK | 10.0.0.83 | Additional server |
| **84 Server** | 10.0.0.84 | GIBD Quant-Flow deployment |

---

## Infrastructure Services

### 1. Traefik (Reverse Proxy)

**Directory**: `infrastructure/traefik/`
**Ports**: 80, 443, 8080 (dashboard)
**Purpose**: Modern reverse proxy and load balancer

**Credentials**:
- Dashboard URL: `https://10.0.0.84/dashboard/`
- User: `admin`
- Password: `W1z4rdS0fts!2025`

**Start**:
```bash
cd infrastructure/traefik
docker compose up -d
```

### 2. Keycloak (Identity & Access Management)

**Directory**: `infrastructure/keycloak/`
**Ports**: 8080 (internal, proxied via Traefik)
**Purpose**: Single Sign-On (SSO), OAuth2, OIDC

**Credentials**:
- URL: `https://id.wizardsofts.com` (requires DNS configuration)
- Admin User: `admin`
- Admin Password: `Keycl0ak!Admin2025`

**Start**:
```bash
cd infrastructure/keycloak
docker compose up -d
```

### 3. PostgreSQL (Database)

**Directory**: `infrastructure/postgresql/`
**Ports**: Internal only (not exposed)
**Purpose**: Primary database for all services

**Databases**:
- `ws_gibd_dse_daily_trades`
- `ws_gibd_dse_company_info`
- Service-specific databases

**Start**:
```bash
cd infrastructure/postgresql
docker compose up -d
```

### 4. Redis (Cache & Message Queue)

**Directory**: `infrastructure/redis/`
**Ports**: Internal only (not exposed)
**Purpose**: Caching, session storage, Celery backend

**Start**:
```bash
cd infrastructure/redis
docker compose up -d
```

### 5. GitLab (CI/CD Platform)

**Directory**: `infrastructure/gitlab/`
**Ports**: 80, 443, 22
**Purpose**: Git hosting, CI/CD, Issue tracking

**Start**:
```bash
cd infrastructure/gitlab
docker compose up -d
```

### 6. GitLab Runner

**Directory**: `infrastructure/gitlab-runner/`
**Purpose**: CI/CD job execution

**Start**:
```bash
cd infrastructure/gitlab-runner
docker compose up -d
```

### 7. N8N (Workflow Automation)

**Directory**: `infrastructure/n8n/`
**Ports**: 5678
**Purpose**: Workflow automation, integrations

**Start**:
```bash
cd infrastructure/n8n
docker compose up -d
```

### 8. Nexus (Artifact Repository)

**Directory**: `infrastructure/nexus/`
**Ports**: 8081 (UI), 8082 (Docker registry), 8083 (Maven)
**Purpose**: Maven artifacts, Docker images, NPM packages

**Start**:
```bash
cd infrastructure/nexus
docker compose up -d
```

### 9. Ollama (AI Model Serving)

**Directory**: `infrastructure/ollama/`
**Ports**: 11434
**Purpose**: Local AI model inference

**Start**:
```bash
cd infrastructure/ollama
docker compose up -d
```

### 10. LLM Server

**Directory**: `infrastructure/llm-server/`
**Ports**: 8000
**Purpose**: Language model API

**Start**:
```bash
cd infrastructure/llm-server
docker compose up -d
```

### 11. Auto-scaling (Prometheus + Grafana)

**Directory**: `infrastructure/auto-scaling/`
**Ports**: 3000 (Grafana), 9090 (Prometheus)
**Purpose**: Monitoring, metrics, alerting

**Start**:
```bash
cd infrastructure/auto-scaling
docker compose up -d
```

---

## Quick Start

### Start All Infrastructure Services

```bash
# From monorepo root
docker compose --profile infrastructure up -d
```

### Start Specific Services

```bash
# Authentication stack
docker compose --profile auth up -d

# Monitoring stack
docker compose --profile monitoring up -d

# CI/CD stack
docker compose --profile cicd up -d

# AI/ML stack
docker compose --profile ai up -d
```

---

## Security & Hardening

### Hardening Scripts

**Directory**: `infrastructure/hardening/`

Available hardening scripts:
- User and access control
- Network security
- Service hardening
- Docker security
- SSH hardening
- Firewall configuration

**Run security audit**:
```bash
cd infrastructure/scripts
./audit-server.sh
```

### Security Documentation

- [constitution.md](constitution.md) - Security checklist
- [SERVER_HARDENING_PLAN_GMK.md](SERVER_HARDENING_PLAN_GMK.md) - Hardening plan
- [REMEDIATION_CHECKLIST.md](REMEDIATION_CHECKLIST.md) - Remediation steps
- [VULNERABILITY_SCAN_SUMMARY.md](VULNERABILITY_SCAN_SUMMARY.md) - Scan results

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` in each service directory and update with actual values.

**Common variables**:
```bash
# Database
DB_PASSWORD=your_postgres_password

# Keycloak
KEYCLOAK_ADMIN_PASSWORD=Keycl0ak!Admin2025

# Traefik
TRAEFIK_DASHBOARD_PASSWORD=W1z4rdS0fts!2025

# GitLab
GITLAB_ROOT_PASSWORD=your_gitlab_password
```

### Network Configuration

All services use Docker networks for isolation:
- `traefik-public`: External-facing services
- `backend`: Internal services (databases, caches)
- `monitoring`: Prometheus, Grafana
- `gibd-network`: GIBD services

---

## Docker Compose Profiles

Infrastructure services are organized into profiles for flexible deployment:

| Profile | Services | Use Case |
|---------|----------|----------|
| `infrastructure` | All infrastructure services | Full infrastructure stack |
| `auth` | Keycloak, PostgreSQL | Authentication services |
| `cicd` | GitLab, GitLab Runner | CI/CD pipeline |
| `monitoring` | Prometheus, Grafana | Metrics and monitoring |
| `ai` | Ollama, LLM Server | AI/ML services |
| `proxy` | Traefik | Reverse proxy |
| `data` | PostgreSQL, Redis | Data layer |

**Example usage**:
```bash
# Start authentication + data layer
docker compose --profile auth --profile data up -d

# Start full infrastructure
docker compose --profile infrastructure up -d

# Start monitoring only
docker compose --profile monitoring up -d
```

---

## Service Management

### Check All Services

```bash
# List all running containers
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

# Check service health
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f traefik
docker compose logs -f keycloak
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart traefik
```

### Update Services

```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

---

## Monitoring & Health Checks

### Service Health Endpoints

```bash
# Traefik
curl http://10.0.0.84:8080/api/overview

# Keycloak
curl http://10.0.0.84:8080/health

# Prometheus
curl http://10.0.0.84:9090/-/healthy

# Grafana
curl http://10.0.0.84:3000/api/health
```

### System Monitoring

```bash
# Check system resources
free -h
df -h
docker stats

# Check network
sudo netstat -tlnp
```

---

## Backup & Recovery

### Database Backups

```bash
# PostgreSQL backup
docker exec postgres-container pg_dump -U postgres database_name > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i postgres-container psql -U postgres database_name < backup.sql
```

### Configuration Backups

```bash
# Backup all configurations
tar -czf infrastructure-backup-$(date +%Y%m%d).tar.gz infrastructure/
```

---

## Troubleshooting

### Common Issues

#### Service Won't Start

1. Check logs: `docker compose logs service-name`
2. Check ports: `sudo netstat -tlnp | grep PORT`
3. Check disk space: `df -h`
4. Check Docker: `docker info`

#### Network Issues

1. Check Docker networks: `docker network ls`
2. Inspect network: `docker network inspect network-name`
3. Check firewall: `sudo ufw status`

#### Performance Issues

1. Check resources: `docker stats`
2. Check system load: `top` or `htop`
3. Check logs for errors: `docker compose logs`

### Recovery Steps

```bash
# Stop all services
docker compose down

# Clean up
docker system prune -a -f

# Restart services
docker compose up -d
```

---

## Migration Notes

### Moved from server-setup

All infrastructure services were migrated from `/Users/mashfiqurrahman/Workspace/wizardsofts/server-setup` to the megabuild monorepo for centralized management.

**Original structure**:
- Separate docker-compose files per service
- Manual deployment on each server
- Distributed configuration

**New structure**:
- Unified monorepo with profiles
- Automated CI/CD deployment
- Centralized configuration management
- Better service discovery and networking

### Integration with GIBD Services

Infrastructure services now work seamlessly with GIBD Quant-Flow services:
- Shared PostgreSQL and Redis instances
- Common Traefik reverse proxy
- Unified monitoring with Prometheus/Grafana
- Centralized authentication with Keycloak
- GitLab CI/CD for all services

---

## Documentation

- [server_readme.md](server_readme.md) - Server overview and management
- [server_access.md](server_access.md) - Server access information
- [INSTRUCTIONS.md](INSTRUCTIONS.md) - Setup instructions
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference guide
- [SETUP_INFRASTRUCTURE.md](SETUP_INFRASTRUCTURE.md) - Infrastructure setup

---

## Support

For issues:
1. Check service logs: `docker compose logs service-name`
2. Review documentation in this directory
3. Check security hardening guides
4. Verify network configuration

## Next Steps

1. Configure DNS for Keycloak: `id.wizardsofts.com`
2. Set up SSL certificates for Traefik
3. Configure Prometheus alerts
4. Set up backup automation
5. Implement log aggregation (ELK stack)

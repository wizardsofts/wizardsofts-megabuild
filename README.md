# Guardian Investment BD Monorepo

Enterprise monorepo for Guardian Investment BD microservices platform, featuring Spring Boot and Python ML/AI services.

## Architecture

### Shared Services (ws-*)
Reusable infrastructure services across multiple projects:

- **ws-discovery** (Port 8761): Eureka service discovery
- **ws-gateway** (Port 8080): Spring Cloud Gateway with load balancing
- **ws-trades** (Port 8182): DSE daily trades data API
- **ws-company** (Port 8183): Company information API
- **ws-news** (Port 8184): News data API

### GIBD Quant-Flow Services (gibd-quant-*)
ML/AI services for quantitative trading analysis:

- **gibd-quant-signal** (Port 5001): Signal generation service
- **gibd-quant-nlq** (Port 5002): Natural language query service
- **gibd-quant-calibration** (Port 5003): Stock calibration service
- **gibd-quant-agent** (Port 5004): LangGraph AI agents
- **gibd-quant-web** (Port 3001): Next.js frontend with fixed layout & analytics
- **gibd-quant-celery**: Background task processing

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Java 17+ (for Spring Boot services)
- Python 3.11+ with uv (for Python services)
- Node.js 18+ (for frontend)
- PostgreSQL 15
- Redis 7

### Development

```bash
# Start shared services only
docker-compose --profile shared up -d

# Start GIBD Quant-Flow ecosystem
docker-compose --profile gibd-quant up -d

# Start everything
docker-compose --profile all up -d
```

### Access Points

- **Eureka Dashboard**: http://localhost:8761
- **API Gateway**: http://localhost:8080
- **Frontend**: http://localhost:3001

## Project Structure

```
guardianinvestmentbd-monorepo/
├── apps/                   # All microservices
│   ├── ws-*/              # Shared services
│   └── gibd-quant-*/      # GIBD Quant services
├── packages/              # Shared libraries
│   ├── shared-types/      # TypeScript/Python types
│   └── spring-common/     # Spring Boot utilities
├── infrastructure/        # Infrastructure configs
│   └── monitoring/        # Prometheus + Grafana
└── docker-compose.yml     # Multi-profile orchestration
```

## Documentation

- **Deployment**:
  - [Deployment Guide](DEPLOYMENT.md) - Local deployment and testing
  - [CI/CD Quick Start](docs/CICD_QUICKSTART.md) - 30-minute setup guide
  - [GitLab Runner Setup](docs/GITLAB_RUNNER_SETUP.md) - Detailed GitLab Runner configuration
- **Migration**:
  - [Migration Status](docs/MIGRATION_STATUS.md) - Complete migration tracking
- **Frontend**:
  - [Analytics Documentation](apps/gibd-quant-web/ANALYTICS.md)

## Technology Stack

### Backend
- **Spring Boot 3.x**: REST APIs and microservices
- **Spring Cloud**: Service discovery (Eureka), Gateway, Config
- **FastAPI**: Python ML/AI services
- **Celery**: Background task processing

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **Google Analytics**: User behavior tracking

### Infrastructure
- **Docker**: Containerization
- **PostgreSQL**: Primary database
- **Redis**: Caching and task queue
- **Eureka**: Service discovery

## Deployment Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| **shared** | Infrastructure + ws-* services | Shared services for multiple projects |
| **gibd-quant** | shared + gibd-quant-* services | Complete GIBD Quant-Flow ecosystem |
| **all** | Everything | Full monorepo deployment |

## CI/CD Pipeline

### Automated Deployment to 10.0.0.84

The monorepo uses GitLab CI/CD with GitLab Runner for automated deployments:

1. **Detect Changes**: Identifies which services changed
2. **Run Tests**: Tests Spring Boot (Maven) and Python (pytest) services
3. **Build Images**: Builds Docker images for changed services
4. **Deploy**: Deploys to 10.0.0.84 server (manual trigger)
5. **Health Check**: Verifies all services are running

### Quick Deploy

```bash
# Automated via GitLab CI/CD
git push origin main
# Then click "Play" on deploy-to-84 job in GitLab pipeline

# Or manual deployment
./scripts/deploy-to-84.sh
```

### Setup GitLab Runner

See [CI/CD Quick Start](docs/CICD_QUICKSTART.md) for 30-minute setup guide.

## License

Proprietary - Guardian Investment BD

# Architecture Documentation

System design and architectural decisions for the WizardSofts monorepo.

## Contents

| Document | Description |
|----------|-------------|
| [monorepo-strategy.md](monorepo-strategy.md) | Monorepo structure and conventions |
| [distributed-ml.md](distributed-ml.md) | Ray cluster and distributed ML architecture |

## Overview

This monorepo contains:

- **Backend Services:** Java Spring Boot microservices (ws-gateway, ws-discovery, ws-company, ws-trades, ws-news)
- **Frontend Apps:** React/Next.js applications
- **ML Pipelines:** Python-based quantitative trading and NLP systems
- **Infrastructure:** Docker Compose, Traefik, monitoring stack

## Key Architectural Decisions

1. **Monorepo Strategy** - All services in single repository for easier cross-cutting changes
2. **Service Discovery** - Eureka-based service registry (ws-discovery)
3. **API Gateway** - Spring Cloud Gateway (ws-gateway) with OAuth2 integration
4. **Distributed ML** - Ray cluster for distributed training across Servers 80, 81, 84
5. **Host Networking** - Distributed services use host networking for reliability

## Related Documentation

- [Deployment Guides](../deployment/) - How to deploy each service
- [Operations](../operations/) - Server infrastructure and maintenance
- [Data Pipelines](../data-pipelines/) - Data flow and processing

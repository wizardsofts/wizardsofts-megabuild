# Deployment Guides

Step-by-step deployment guides for all services in the WizardSofts infrastructure.

## Service Deployment Guides

| Service | Guide | Server(s) |
|---------|-------|-----------|
| Appwrite | [APPWRITE_DEPLOYMENT.md](APPWRITE_DEPLOYMENT.md) | Server 84 |
| GitLab | [GITLAB_DEPLOYMENT.md](GITLAB_DEPLOYMENT.md) | Server 84 |
| Traefik | [TRAEFIK_DEPLOYMENT.md](TRAEFIK_DEPLOYMENT.md) | Server 84 |
| Keycloak | [KEYCLOAK_HANDOFF.md](KEYCLOAK_HANDOFF.md) | Server 84 |
| Ray Cluster | [RAY_2.53_DEPLOYMENT_GUIDE.md](RAY_2.53_DEPLOYMENT_GUIDE.md) | Servers 80, 81, 84 |
| Ollama | [OLLAMA_SWARM_DEPLOYMENT_GUIDE.md](OLLAMA_SWARM_DEPLOYMENT_GUIDE.md) | Server 84 (Swarm) |
| Mailcow | [MAILCOW_HANDOFF.md](MAILCOW_HANDOFF.md) | Server 84 |
| Monitoring | [MONITORING_IMPLEMENTATION_GUIDE.md](MONITORING_IMPLEMENTATION_GUIDE.md) | Server 84 |
| Server 82 | [SERVER_82_DEPLOYMENT.md](SERVER_82_DEPLOYMENT.md) | Server 82 |

## Additional Guides

| Guide | Description |
|-------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | General deployment procedures |
| [ENV_CONFIGURATION_GUIDE.md](ENV_CONFIGURATION_GUIDE.md) | Environment variable configuration |
| [TRAEFIK_SECURITY_GUIDE.md](TRAEFIK_SECURITY_GUIDE.md) | Why Traefik is better than direct port exposure |

## Server Infrastructure

| Server | IP | Primary Purpose |
|--------|-----|-----------------|
| Server 80 | 10.0.0.80 | GIBD Services, Ray Workers |
| Server 81 | 10.0.0.81 | PostgreSQL Database |
| Server 82 | 10.0.0.82 | Monitoring Exporters |
| Server 84 | 10.0.0.84 | Production (Appwrite, GitLab, Traefik) |

## Deployment Checklist

Before deploying any service:

- [ ] Verify server has sufficient disk space (`df -h`)
- [ ] Check Docker is running (`docker ps`)
- [ ] Ensure network connectivity to dependent services
- [ ] Review environment variables in `.env` file
- [ ] Check Traefik labels for routing (if web-facing)

## Quick Commands

```bash
# Check service status
docker ps | grep <service-name>

# View logs
docker logs <container-name> -f --tail 100

# Restart service
docker-compose -f docker-compose.<service>.yml restart
```

## Related Documentation

- [Operations](../operations/) - Troubleshooting and maintenance
- [Security](../security/) - Security hardening for deployments
- [CI/CD](../cicd/) - Automated deployment pipelines

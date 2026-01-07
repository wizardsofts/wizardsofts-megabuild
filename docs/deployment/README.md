# Deployment Guides

Step-by-step deployment guides for all services in the WizardSofts infrastructure.

## Service Deployment Guides

| Service | Guide | Server(s) |
|---------|-------|-----------|
| Appwrite | [appwrite.md](appwrite.md) | Server 84 |
| GitLab | [gitlab.md](gitlab.md) | Server 84 |
| Traefik | [traefik.md](traefik.md) | Server 84 |
| Keycloak | [keycloak.md](keycloak.md) | Server 84 |
| Ray Cluster | [ray-cluster.md](ray-cluster.md) | Servers 80, 81, 84 |
| Ollama | [ollama.md](ollama.md) | Server 84 (Swarm) |
| Mailcow | [mailcow.md](mailcow.md) | Server 84 |
| Monitoring | [monitoring.md](monitoring.md) | Server 84 |

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

# Operations Runbook

Day-to-day operations, troubleshooting, and maintenance procedures.

## Contents

| Section | Description |
|---------|-------------|
| [server-infrastructure.md](server-infrastructure.md) | Server inventory (80, 81, 82, 84) |
| [docker-swarm.md](docker-swarm.md) | Swarm cluster management |
| [backup-restore.md](backup-restore.md) | Backup and recovery procedures |
| [disk-management.md](disk-management.md) | Disk cleanup and expansion |
| [troubleshooting/](troubleshooting/) | Service-specific troubleshooting |
| [maintenance/](maintenance/) | Scheduled maintenance tasks |

## Emergency Contacts

| Issue | First Action |
|-------|--------------|
| Service down | Check `docker ps`, review logs |
| Disk full | Run cleanup script, see [disk-management.md](disk-management.md) |
| GitLab inaccessible | Check gitlab-postgres on Server 80 |
| SSL certificate error | Check Traefik, see [troubleshooting/networking.md](troubleshooting/networking.md) |

## Quick Health Checks

```bash
# Check all critical services on Server 84
ssh agent@10.0.0.84 'docker ps | grep -E "gitlab|traefik|prometheus|appwrite"'

# Check disk usage across servers
for server in 80 81 82 84; do
  echo "=== Server $server ===" && ssh agent@10.0.0.$server 'df -h /'
done

# Check GitLab health
curl http://10.0.0.84:8090/-/readiness
```

## Common Operations

### Restart a Service
```bash
ssh agent@10.0.0.84 'sudo docker restart <service-name>'
```

### View Service Logs
```bash
ssh agent@10.0.0.84 'docker logs <container-name> -f --tail 100'
```

### Check Cron Jobs
```bash
ssh agent@10.0.0.84 'crontab -l'
```

## Subdirectories

### [troubleshooting/](troubleshooting/)
- [gitlab.md](troubleshooting/gitlab.md) - GitLab issues
- [appwrite.md](troubleshooting/appwrite.md) - Appwrite issues
- [networking.md](troubleshooting/networking.md) - Network/SSL issues

### [maintenance/](maintenance/)
- [cron-jobs.md](maintenance/cron-jobs.md) - Scheduled tasks inventory
- [certificate-renewal.md](maintenance/certificate-renewal.md) - SSL cert renewal

## Related Documentation

- [Deployment](../deployment/) - How to deploy services
- [Security](../security/) - Security procedures
- [CLAUDE.md](../../CLAUDE.md) - Detailed infrastructure reference

# GitLab Docker Setup Documentation

## Overview

GitLab Community Edition running in Docker on HP Server (10.0.0.80), sharing infrastructure resources with other GIBD services.

## Architecture

- **GitLab**: Dockerized, using shared infrastructure
- **Redis**: Shared with GIBD services (`gibd-redis` container)
- **PostgreSQL**: Shared PostgreSQL 16 container (`gibd-postgres`) for both GitLab and GIBD services
- **Network**: `gibd-network` (shared Docker network)

## Installation

### Prerequisites

```bash
# Ensure Docker network exists
docker network create gibd-network

# Ensure Redis is running
docker ps | grep gibd-redis
```

### Directory Structure

```bash
# Create GitLab directories
sudo mkdir -p /mnt/data/docker/gitlab/{config,logs,data}
sudo chown -R 998:998 /mnt/data/docker/gitlab/
```

### Docker Compose Configuration

Location: `~/gitlab-docker/docker-compose.yml`

```yaml
services:
  gitlab:
    image: gitlab/gitlab-ce:latest
    container_name: gitlab
    restart: always
    hostname: '10.0.0.80'
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://10.0.0.80'
        gitlab_rails['gitlab_shell_ssh_port'] = 2222
        # Disable bundled PostgreSQL
        postgresql['enable'] = false
        # Use external PostgreSQL
        gitlab_rails['db_adapter'] = 'postgresql'
        gitlab_rails['db_encoding'] = 'unicode'
        gitlab_rails['db_host'] = 'gibd-postgres'
        gitlab_rails['db_port'] = 5432
        gitlab_rails['db_database'] = 'gitlabhq_production'
        gitlab_rails['db_username'] = 'gitlab'
        gitlab_rails['db_password'] = 'M9TcxUSpsqL5nSuX'
        # Disable bundled Redis
        redis['enable'] = false
        # Use external Redis
        gitlab_rails['redis_host'] = 'gibd-redis'
        gitlab_rails['redis_port'] = 6379
    ports:
      - '80:80'
      - '443:443'
      - '2222:22'
    volumes:
      - /mnt/data/docker/gitlab/config:/etc/gitlab
      - /mnt/data/docker/gitlab/logs:/var/log/gitlab
      - /mnt/data/docker/gitlab/data:/var/opt/gitlab
    networks:
      - gibd-network

networks:
  gibd-network:
    external: true
```

## Deployment

### Start GitLab

```bash
cd ~/gitlab-docker
docker-compose up -d

# Monitor startup (takes 5-10 minutes)
docker logs -f gitlab
```

### Initial Login

```bash
# Get initial root password
docker exec -it gitlab grep 'Password:' /etc/gitlab/initial_root_password

# Access GitLab
# URL: http://10.0.0.80:8080
# Username: root
# Password: (from command above)
```

**Important**: The initial password file is deleted 24 hours after installation. Change the password immediately after first login.

## Configuration

### Access Points

| Service | URL | Port |
|---------|-----|------|
| Web Interface | http://10.0.0.80 | 80 |
| HTTPS | https://10.0.0.80 | 443 |
| SSH (Git) | ssh://git@10.0.0.80:2222 | 2222 |

### Shared Resources

**Redis Configuration**:
- Host: `gibd-redis`
- Port: 6379
- Shared with GIBD services

**PostgreSQL**:
- Shared PostgreSQL 16 container (`gibd-postgres`)
- Database: `gitlabhq_production` (owned by `gitlab` user)
- Also hosts GIBD service databases
- All services upgraded to PostgreSQL 16

### Network Configuration

GitLab is connected to `gibd-network` for communication with shared services (Redis, future integrations).

## Management

### Service Control

```bash
# Start/Stop GitLab
cd ~/gitlab-docker
docker-compose up -d
docker-compose down

# Restart GitLab
docker-compose restart

# View status
docker ps | grep gitlab
docker exec -it gitlab gitlab-ctl status
```

### GitLab Commands

```bash
# Check GitLab status
docker exec -it gitlab gitlab-ctl status

# Reconfigure GitLab
docker exec -it gitlab gitlab-ctl reconfigure

# Restart services
docker exec -it gitlab gitlab-ctl restart

# Check logs
docker logs -f gitlab
docker exec -it gitlab tail -f /var/log/gitlab/gitlab-rails/production.log
```

### Password Reset

```bash
# Reset root password
docker exec -it gitlab gitlab-rake "gitlab:password:reset[root]"
```

## Backup and Restore

### Create Backup

```bash
# Create backup
docker exec -it gitlab gitlab-backup create

# Backups stored in:
# /mnt/data/docker/gitlab/data/backups/
```

### Restore Backup

```bash
# Stop services
docker exec -it gitlab gitlab-ctl stop unicorn
docker exec -it gitlab gitlab-ctl stop sidekiq

# Restore (replace TIMESTAMP with actual backup file)
docker exec -it gitlab gitlab-backup restore BACKUP=TIMESTAMP

# Restart
docker exec -it gitlab gitlab-ctl start
```

## Git Repository Access

### SSH Configuration

After GitLab is running, configure SSH access for git operations:

```bash
# Test SSH connection
ssh git@10.0.0.80 -p 2222

# Clone repository example
git clone ssh://git@10.0.0.80:2222/username/repository.git

# Or using git@ syntax
git clone git@10.0.0.80:username/repository.git
```

### Update Git Remote URLs

If migrating from old GitLab server (10.0.0.81):

```bash
# Update remote URL
git remote set-url origin git@10.0.0.80:username/repository.git

# Verify
git remote -v
```

## Integration with GIBD Services

### Update GIBD Config Service

Your GIBD Spring Boot config service needs to point to the new GitLab:

```bash
# Update application.yml or application.properties
# From: git@10.0.0.81:gibd/gibd-config.git
# To: git@10.0.0.80:gibd/gibd-config.git

# Restart GIBD config service
sudo /opt/gibd/gibd-manager.sh restart gibd-config
```

## Troubleshooting

### GitLab Not Starting

```bash
# Check logs
docker logs gitlab | tail -100

# Check disk space
df -h /mnt/data/docker/gitlab/

# Check permissions
ls -la /mnt/data/docker/gitlab/
```

### Redis Connection Issues

```bash
# Test Redis connectivity
docker run --rm --network gibd-network redis:7-alpine redis-cli -h gibd-redis ping

# Check GitLab Redis config
docker exec -it gitlab cat /etc/gitlab/gitlab.rb | grep redis

# Reconfigure if needed
docker exec -it gitlab gitlab-ctl reconfigure
```

### 500 Internal Server Error

If encountering 500 errors:

```bash
# Check production logs
docker exec -it gitlab tail -100 /var/log/gitlab/gitlab-rails/production.log

# Check Sidekiq logs
docker exec -it gitlab tail -50 /var/log/gitlab/sidekiq/current

# Common fix: Reconfigure and restart
docker exec -it gitlab gitlab-ctl reconfigure
docker exec -it gitlab gitlab-ctl restart
```

### OpenSSL::Cipher::CipherError

If you encounter encryption errors after connecting to an external database:

```bash
# This means secrets don't match the database
# Solution: Fresh install with clean database

# Stop GitLab
docker-compose down

# Clear data
sudo rm -rf /mnt/data/docker/gitlab/*

# Drop and recreate database (if using external PostgreSQL)
# Start fresh
docker-compose up -d
```

## Maintenance

### Update GitLab

```bash
# Pull latest image
cd ~/gitlab-docker
docker-compose pull

# Recreate container
docker-compose up -d

# GitLab will run migrations automatically
docker logs -f gitlab
```

### Monitor Resources

```bash
# Check GitLab resource usage
docker stats gitlab

# Check disk usage
du -sh /mnt/data/docker/gitlab/*
```

### Log Rotation

GitLab handles log rotation automatically via logrotate service.

## Security Considerations

1. **Change default password immediately** after first login
2. **Configure SSL/TLS** for production use (update external_url to https)
3. **Restrict SSH access** if needed via firewall rules
4. **Regular backups** - schedule automatic backups
5. **Update regularly** - keep GitLab updated for security patches

## Performance Tuning

GitLab is resource-intensive. Default configuration suitable for small teams. For production:

```bash
# Edit docker-compose.yml to add resource limits
services:
  gitlab:
    # ... existing config
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## System Requirements

- **Minimum RAM**: 4GB (8GB recommended)
- **CPU**: 2 cores minimum
- **Disk**: 10GB+ for GitLab, plus space for repositories
- **Network**: Access to gibd-network Docker network

## Additional Resources

- GitLab Documentation: https://docs.gitlab.com
- GitLab Omnibus Docker: https://docs.gitlab.com/omnibus/docker/
- GitLab Configuration Options: https://docs.gitlab.com/omnibus/settings/

---

**Installation Date**: September 29, 2025  
**Server**: HP (10.0.0.80)  
**Version**: GitLab CE (latest)  
**Maintainer**: wizardsofts
# Server Infrastructure Documentation

## Server Network

| Server | IP Address | Hostname | Purpose |
|--------|------------|----------|---------|
| HP | wizardsofts@10.0.0.80 | hppavilion | Primary development server |
| ASUS | wizardsofts@10.0.0.81 | TBD | Secondary server |
| HPRD | wizardsofts@10.0.0.82 | TBD | Production/staging server |
| GMK | wizardsofts@10.0.0.83 | TBD | Additional server |

## System Information (HP Server - 10.0.0.80)

### Hardware Specs
- **CPU**: TBD
- **Memory**: 31.9GB total RAM
- **Storage**: TBD
- **OS**: Ubuntu 24.04 (Noble)

### System Performance
- **Load Average**: Typically 0.68-1.51 (healthy range)
- **Memory Usage**: ~4GB used, 23.4GB free (12.7% utilization)
- **CPU Usage**: ~6.4% user, 91.8% idle
- **Uptime**: 14+ hours stable

## Docker Configuration

### Installation Details
- **Installation Method**: APT/DEB Package
- **Version**: Docker 27.5.1-0ubuntu3~24.04.2
- **Package**: docker.io
- **Binary Location**: `/usr/bin/docker`
- **Data Directory**: `/var/lib/docker/`
- **Service**: Managed by systemd

### Running Containers
| Port | Container IP | Service |
|------|-------------|---------|
| 11434 | 172.19.0.2:11434 | Ollama AI Service (likely) |
| 5678 | 172.18.0.2:5678 | Unknown service |

### Traefik Dashboard
- **URL**: `https://10.0.0.84/dashboard/`
- **User**: `admin`
- **Password**: `W1z4rdS0fts!2025`

### Keycloak
- **URL**: `https://id.wizardsofts.com` (requires DNS/hosts mapping)
- **User**: `admin`
- **Password**: `Keycl0ak!Admin2025`

### Mailcow (Email Server)
- **Admin URL**: `https://mail.wizardsofts.com`
- **Admin User**: `wizardsofts`
- **Admin Password**: `W1z4rdS0fts!2025`
- **Documentation**: See [MAILCOW_HANDOFF.md](MAILCOW_HANDOFF.md) for full details.


### Docker Commands
```bash
# Check running containers
docker ps

# Check docker system info
docker info

# Check docker storage usage
docker system df

# View container logs
docker logs <container_id>
```

## Docker Services

### Service Overview
The server runs multiple Docker Compose stacks for various services:

| Service | Directory | Ports | Purpose |
|---------|-----------|-------|---------|
| Auto-scaling | `auto-scaling/` | 3000 (Grafana), 9090 (Prometheus) | Service autoscaling with monitoring |
| GitLab | `gitlab/` | 80, 443, 22 | CI/CD platform |
| GitLab Runner | `gitlab-runner/` | None | CI/CD runners |
| Keycloak | `keycloak/` | 8080 (internal) | Identity and Access Management |
| LLM Server | `llm-server/` | 8000 | Language model API |
| N8N | `n8n/` | 5678 | Workflow automation |
| Nexus | `nexus/` | 8081, 8082, 8083 | Artifact repository |
| Ollama | `ollama/` | 11434 | AI model serving |
| PostgreSQL | `postgresql/` | None (internal) | Database |
| Redis | `redis/` | None (internal) | Cache |
| Mailcow | `mailcow-dockerized/` | 80, 443, 25, 110, 143, etc. | Mail Server |

### Deployment Commands
```bash
# Deploy all services
for dir in auto-scaling gitlab gitlab-runner llm-server n8n nexus ollama postgresql redis; do
  cd $dir && docker compose up -d
done

# Check all running containers
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

### Security Hardening
All Docker Compose files have been hardened according to the [Security Hardening Checklist](constitution.md):

- **Port Exposure**: Only necessary ports exposed; internal services (PostgreSQL, Redis) not exposed externally
- **Secrets Management**: Credentials moved to `.env` files
- **Health Checks**: Added to all services for monitoring
- **Volume Restrictions**: Sensitive host directories not mounted
- **Non-root Users**: Containers run as non-root where possible
- **Network Isolation**: Services use appropriate Docker networks

See [constitution.md](constitution.md) for the complete security checklist.

## GIBD Services

### Service Architecture
Spring Boot microservices architecture with the following components:

| Service | JAR Location | Purpose |
|---------|-------------|----------|
| gibd-discovery-service | `/opt/gibd/gibd-discovery-service/` | Service discovery (Eureka) |
| gibd-config | `/opt/gibd/gibd-config/` | Configuration server |
| gibd-gateway | `/opt/gibd/gibd-gateway/` | API Gateway |
| gibd-news-service | `/opt/gibd/gibd-news-service/` | News processing service |
| gibd-trades | `/opt/gibd/gibd-trades/` | Trading service |

### Configuration
- **Java Options**: `-Xmx512m -Xms256m -Dspring.profiles.active=hp`
- **Log Directory**: `/var/log/gibd/`
- **PID Directory**: `/var/run/gibd/`
- **Git Repository**: `git@10.0.0.81:gibd/gibd-config.git` (GitLab)

### Service Management

#### Using the GIBD Manager Script
```bash
# Location
/opt/gibd/gibd-manager.sh

# Commands
sudo /opt/gibd/gibd-manager.sh start [service_name]    # Start service(s)
sudo /opt/gibd/gibd-manager.sh stop [service_name]     # Stop service(s)
sudo /opt/gibd/gibd-manager.sh restart [service_name]  # Restart service(s)
sudo /opt/gibd/gibd-manager.sh status [service_name]   # Check status
sudo /opt/gibd/gibd-manager.sh list                    # List available services
```

#### Using systemctl
```bash
# All services
sudo systemctl start gibd
sudo systemctl stop gibd
sudo systemctl restart gibd
sudo systemctl status gibd

# Individual services (template)
sudo systemctl start gibd@gibd-gateway
sudo systemctl stop gibd@gibd-news-service
sudo systemctl restart gibd@gibd-trades
sudo systemctl status gibd@gibd-config
```

### Service Dependencies
1. **gibd-discovery-service** - Must start first
2. **gibd-config** - Must start second (depends on discovery)
3. **gibd-gateway, gibd-news-service, gibd-trades** - Can start after config service

## File Transfer Tools

### Grab Tool (Download from servers)
```bash
# Location: ~/scripts/grab.sh
# Alias: grab

# Usage examples
grab hp /path/to/file.txt                              # Download file
grab -r asus /path/to/directory ~/Downloads/           # Download directory
grab -r --preset python hp /home/user/python_project  # Download with Python exclusions
grab -r --preset java,git gmk /opt/gibd/               # Multiple presets
grab --dry-run -r hp /path/to/check                    # Dry run

# Available presets: python, node, java, git, logs, dev
# Available servers: hp, asus, hprd, gmk
```

### Push Tool (Upload to servers)
```bash
# Location: ~/scripts/push.sh  
# Alias: push

# Usage examples
push file.txt hp /home/wizardsofts/                    # Upload file
push -r my_project asus /opt/                          # Upload directory
push -r --preset python my_app hp /opt/                # Upload with exclusions
push --dry-run -r my_project gmk /tmp/                 # Dry run
```

## Shell Configuration

### Aliases and Functions
```bash
# File transfer
alias grabr='grab -r'
alias grabpy='grab -r --preset python'
alias grabjs='grab -r --preset node'
alias pushr='push -r'
alias pushpy='push -r --preset python'

# Service management
alias gibd='/opt/gibd/gibd-manager.sh'

# System monitoring
alias checkservices='~/scripts/check_services.sh'
```

### Script Locations
- **grab.sh**: `~/scripts/grab.sh`
- **push.sh**: `~/scripts/push.sh`
- **gibd-manager.sh**: `/opt/gibd/gibd-manager.sh`
- **System scripts**: `~/scripts/`

## Development Environment

### Browser and Driver
- **ChromeDriver**: Version 114.0.5735.90
- **Chromium**: Version 114.0.5735.0 (custom installation at `/usr/local/bin/chromium-browser`)
- **Python Environment**: Virtual environment with Selenium setup

### Selenium Configuration
```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

service = Service('/usr/local/bin/chromedriver')
chrome_options = Options()
chrome_options.binary_location = '/usr/local/bin/chromium-browser'
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=service, options=chrome_options)
```

## Database Configuration

### PostgreSQL
- **Installation**: TBD
- **Backup Command**: `pg_dump database_name > backup_$(date +%Y%m%d_%H%M%S).sql`

## SSH Configuration

### Git Access
- **GitLab Server**: 10.0.0.81
- **SSH Keys**: Configured for root user to access GitLab repositories
- **Repository**: `git@10.0.0.81:gibd/gibd-config.git`

### SSH Commands
```bash
# Test GitLab connection
ssh git@10.0.0.81

# SSH to servers
ssh wizardsofts@10.0.0.80  # HP
ssh wizardsofts@10.0.0.81  # ASUS  
ssh wizardsofts@10.0.0.82  # HPRD
ssh wizardsofts@10.0.0.83  # GMK
```

## Monitoring and Maintenance

### System Health Checks
```bash
# System overview
top
htop
free -h
df -h

# Service status
sudo /opt/gibd/gibd-manager.sh status
ps aux | grep java

# Docker status  
docker ps
docker stats

# Network status
sudo netstat -tlnp
```

### Log Locations
- **GIBD Services**: `/var/log/gibd/[service-name].log`
- **System Logs**: `sudo journalctl -u [service-name]`
- **Docker Logs**: `docker logs [container-id]`

## Troubleshooting

### Common Issues

#### GIBD Services Not Starting
1. Check if config service is running first
2. Verify GitLab SSH connection
3. Check log files in `/var/log/gibd/`
4. Ensure Spring profile is set correctly

#### ChromeDriver Issues
1. Verify versions match (both 114)
2. Check binary locations and permissions
3. Install missing graphics libraries if needed

#### File Transfer Issues
1. Check SSH connectivity to target server
2. Verify file paths and permissions
3. Use `--dry-run` flag to test

### Quick Fixes
```bash
# Restart all GIBD services
sudo /opt/gibd/gibd-manager.sh restart

# Fix SSH keys for GitLab
sudo cp ~/.ssh/id_* /root/.ssh/
sudo chown root:root /root/.ssh/id_*

# Check system resources
free -h && df -h && uptime
```

## Notes

- Server runs Ubuntu 24.04 with 32GB RAM and stable performance
- GIBD services use Spring Boot with HP profile
- Docker containers include AI services (Ollama likely)
- Git configuration stored on separate GitLab server
- Custom file transfer tools with preset exclusions for different project types

---

**Last Updated**: December 27, 2025  
**Maintainer**: wizardsofts

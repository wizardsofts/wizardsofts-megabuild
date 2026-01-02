# Nexus Repository Manager Setup Documentation

## Overview

Nexus Repository Manager OSS running in Docker on HP Server (10.0.0.80), providing centralized artifact management for Maven, NPM, Docker, and other package formats.

## Architecture

- **Nexus**: Dockerized Sonatype Nexus Repository Manager OSS
- **Network**: `gibd-network` (shared Docker network)
- **Storage**: `/mnt/data/docker/nexus/data`
- **Ports**: 8081 (Web UI), 8082 (Docker HTTP), 8083 (Docker HTTPS)

## Installation

### Directory Structure

```bash
# Create Nexus directories
sudo mkdir -p /mnt/data/docker/nexus/data
sudo chown -R 200:200 /mnt/data/docker/nexus/data
```

### Docker Compose Configuration

Location: `~/nexus-docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  nexus:
    image: sonatype/nexus3:latest
    container_name: nexus
    restart: always
    ports:
      - "8081:8081"
      - "8082:8082"  # Docker registry HTTP
      - "8083:8083"  # Docker registry HTTPS (optional)
    volumes:
      - /mnt/data/docker/nexus/data:/nexus-data
    environment:
      INSTALL4J_ADD_VM_PARAMS: "-Xms512m -Xmx512m -XX:MaxDirectMemorySize=512m"
    networks:
      - gibd-network

networks:
  gibd-network:
    external: true
```

## Deployment

### Start Nexus

```bash
cd ~/nexus-docker
docker-compose up -d

# Monitor startup (takes 2-5 minutes)
docker logs -f nexus
```

### Initial Login

```bash
# Get initial admin password (after Nexus fully starts)
docker exec -it nexus cat /nexus-data/admin.password

# Access Nexus
# URL: http://10.0.0.80:8081
# Username: admin
# Password: (from command above)
```

### Initial Configuration

After first login, complete the setup wizard:

1. **Change admin password** - set a secure password
2. **Enable anonymous access** - allows users to download without authentication
3. **Complete setup wizard**

## Repository Configuration

### Default Repositories

Nexus comes pre-configured with:

- **maven-central** - Maven Central proxy repository
- **maven-releases** - Hosted repository for release artifacts
- **maven-snapshots** - Hosted repository for snapshot artifacts
- **maven-public** - Group repository (aggregates central, releases, snapshots)
- **nuget-hosted** - NuGet hosted repository
- **nuget.org-proxy** - NuGet.org proxy repository

### NPM Repository Setup

#### Create NPM Repositories

1. Go to **Settings (gear icon) → Repository → Repositories**
2. Click **Create repository**

**NPM Proxy (for npmjs.org):**
- Type: `npm (proxy)`
- Name: `npm-proxy`
- Remote storage: `https://registry.npmjs.org`
- Click **Create repository**

**NPM Hosted (for private packages):**
- Type: `npm (hosted)`
- Name: `wizardsoft-npm-hosted`
- Deployment policy: `Allow redeploy`
- Click **Create repository**

**NPM Group (combines proxy and hosted):**
- Type: `npm (group)`
- Name: `wizardsoft-npm-group`
- Member repositories: Add both `npm-proxy` and `wizardsoft-npm-hosted`
- Click **Create repository**

#### Configure NPM Client

```bash
# Set registry globally for current user
npm config set registry http://10.0.0.80:8081/repository/wizardsoft-npm-group/

# Verify the change
npm config get registry

# List all configurations
npm config list

# For project-specific configuration, create .npmrc in project root
echo "registry=http://10.0.0.80:8081/repository/wizardsoft-npm-group/" > .npmrc
```

#### Authentication for Publishing (Optional)

```bash
# Login to Nexus (for publishing packages)
npm login --registry=http://10.0.0.80:8081/repository/wizardsoft-npm-hosted/

# Publish package
npm publish --registry=http://10.0.0.80:8081/repository/wizardsoft-npm-hosted/
```

### Maven Repository Setup

Maven repositories are pre-configured. Configure Maven clients:

#### Maven Settings Configuration

Location: `~/.m2/settings.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.2.0 
          http://maven.apache.org/xsd/settings-1.2.0.xsd">

  <!-- Nexus Mirror Configuration -->
  <mirrors>
    <mirror>
      <id>nexus</id>
      <mirrorOf>*</mirrorOf>
      <url>http://10.0.0.80:8081/repository/maven-public/</url>
    </mirror>
  </mirrors>

  <!-- Server Authentication (for deploying artifacts) -->
  <servers>
    <server>
      <id>nexus-snapshots</id>
      <username>admin</username>
      <password>your_nexus_password</password>
    </server>
    <server>
      <id>nexus-releases</id>
      <username>admin</username>
      <password>your_nexus_password</password>
    </server>
  </servers>

  <!-- Profiles -->
  <profiles>
    <profile>
      <id>nexus</id>
      <repositories>
        <repository>
          <id>central</id>
          <url>http://10.0.0.80:8081/repository/maven-public/</url>
          <releases><enabled>true</enabled></releases>
          <snapshots><enabled>true</enabled></snapshots>
        </repository>
      </repositories>
      <pluginRepositories>
        <pluginRepository>
          <id>central</id>
          <url>http://10.0.0.80:8081/repository/maven-public/</url>
          <releases><enabled>true</enabled></releases>
          <snapshots><enabled>true</enabled></snapshots>
        </pluginRepository>
      </pluginRepositories>
    </profile>
  </profiles>

  <activeProfiles>
    <activeProfile>nexus</activeProfile>
  </activeProfiles>

</settings>
```

#### Project POM Configuration (for deploying)

Add to your `pom.xml`:

```xml
<distributionManagement>
  <repository>
    <id>nexus-releases</id>
    <name>Nexus Release Repository</name>
    <url>http://10.0.0.80:8081/repository/maven-releases/</url>
  </repository>
  <snapshotRepository>
    <id>nexus-snapshots</id>
    <name>Nexus Snapshot Repository</name>
    <url>http://10.0.0.80:8081/repository/maven-snapshots/</url>
  </snapshotRepository>
</distributionManagement>
```

Deploy with:
```bash
mvn clean deploy
```

### Docker Registry Setup (Optional)

#### Create Docker Repositories

1. **Docker Hosted Repository:**
    - Type: `docker (hosted)`
    - Name: `wizardsoft-docker-hosted`
    - HTTP: `8082`
    - Enable Docker V1 API: `Unchecked`
    - Deployment policy: `Allow redeploy`

2. **Docker Proxy Repository:**
    - Type: `docker (proxy)`
    - Name: `docker-hub-proxy`
    - Remote storage: `https://registry-1.docker.io`
    - Docker Index: `Use Docker Hub`

3. **Docker Group Repository:**
    - Type: `docker (group)`
    - Name: `wizardsoft-docker-group`
    - HTTP: `8083`
    - Member repositories: Add both hosted and proxy

#### Configure Docker Client

```bash
# Configure Docker to use insecure registry (for HTTP)
sudo nano /etc/docker/daemon.json

# Add:
{
  "insecure-registries": ["10.0.0.80:8082", "10.0.0.80:8083"]
}

# Restart Docker
sudo systemctl restart docker

# Login to Nexus Docker registry
docker login 10.0.0.80:8082
# Username: admin
# Password: your_nexus_password

# Tag and push image
docker tag myimage:latest 10.0.0.80:8082/myimage:latest
docker push 10.0.0.80:8082/myimage:latest

# Pull image
docker pull 10.0.0.80:8083/library/nginx:latest
```

### Python (PyPI) Repository Setup (Optional)

#### Create PyPI Repositories

1. **PyPI Proxy:**
    - Type: `pypi (proxy)`
    - Name: `pypi-proxy`
    - Remote storage: `https://pypi.org`

2. **PyPI Hosted:**
    - Type: `pypi (hosted)`
    - Name: `wizardsoft-pypi-hosted`

3. **PyPI Group:**
    - Type: `pypi (group)`
    - Name: `wizardsoft-pypi-group`
    - Member repositories: Add both

#### Configure pip

```bash
# Create pip config
mkdir -p ~/.pip
nano ~/.pip/pip.conf

# Add:
[global]
index-url = http://10.0.0.80:8081/repository/wizardsoft-pypi-group/simple
trusted-host = 10.0.0.80

# Or use command line
pip install package_name -i http://10.0.0.80:8081/repository/wizardsoft-pypi-group/simple --trusted-host 10.0.0.80
```

## Access Control

### Anonymous Access

**Current Configuration:** Anonymous access is **ENABLED**

This allows users to download artifacts without authentication. To change:

1. Go to **Settings → Security → Anonymous Access**
2. Toggle **Allow anonymous users to access the server**

### User Management

#### Create Users

1. Go to **Settings → Security → Users**
2. Click **Create local user**
3. Fill in details:
    - ID: username
    - First/Last name
    - Email
    - Status: Active
    - Roles: Select appropriate roles (e.g., `nx-admin`, `nx-anonymous`)

#### Create Roles

1. Go to **Settings → Security → Roles**
2. Click **Create role**
3. Configure privileges for the role

## Management

### Service Control

```bash
# Start/Stop Nexus
cd ~/nexus-docker
docker-compose up -d
docker-compose down

# Restart Nexus
docker-compose restart

# View logs
docker logs -f nexus

# Check status
docker ps | grep nexus
```

### Storage Management

```bash
# Check storage usage
du -sh /mnt/data/docker/nexus/data

# Clean up unused components
# Via UI: Settings → System → Tasks → Create task → "Admin - Compact blob store"
```

### Backup

```bash
# Backup Nexus data
sudo tar -czf nexus-backup-$(date +%Y%m%d).tar.gz /mnt/data/docker/nexus/data

# Store backup
mv nexus-backup-*.tar.gz /mnt/data/docker/nexus/backups/
```

### Restore

```bash
# Stop Nexus
docker-compose down

# Restore data
sudo tar -xzf nexus-backup-YYYYMMDD.tar.gz -C /

# Fix permissions
sudo chown -R 200:200 /mnt/data/docker/nexus/data

# Start Nexus
docker-compose up -d
```

## Troubleshooting

### Nexus Not Starting

```bash
# Check logs
docker logs nexus | tail -100

# Check disk space
df -h /mnt/data/docker/nexus/

# Check permissions
ls -la /mnt/data/docker/nexus/data
sudo chown -R 200:200 /mnt/data/docker/nexus/data
```

### Cannot Login

```bash
# Reset admin password
docker exec -it nexus cat /nexus-data/admin.password
```

### Repository Not Accessible

1. Check repository is online: **Settings → Repository → Repositories**
2. Verify anonymous access is enabled if not authenticating
3. Check firewall rules allow access to port 8081

### Performance Issues

If Nexus is slow, increase memory allocation in docker-compose.yml:

```yaml
environment:
  INSTALL4J_ADD_VM_PARAMS: "-Xms1g -Xmx2g -XX:MaxDirectMemorySize=2g"
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## Monitoring

### Check System Status

Access via UI: **Settings → System → Nodes**

### View Metrics

Access via UI: **Settings → System → Support → Metrics**

### Resource Usage

```bash
# Check Nexus container resources
docker stats nexus

# Check disk usage
du -sh /mnt/data/docker/nexus/data/*
```

## Security Best Practices

1. **Change default admin password** immediately
2. **Enable HTTPS** for production use
3. **Restrict anonymous access** if handling sensitive artifacts
4. **Regular backups** - schedule automated backups
5. **Update regularly** - keep Nexus updated for security patches
6. **Use strong passwords** for all user accounts
7. **Audit access logs** regularly via Settings → System → Logging

## System Requirements

- **Minimum RAM**: 4GB (8GB recommended for production)
- **CPU**: 2 cores minimum
- **Disk**: 20GB+ (grows with artifact storage)
- **Network**: Access to gibd-network Docker network

## Repository URLs

| Repository Type | URL Format | Example |
|----------------|------------|---------|
| Maven Public | `http://10.0.0.80:8081/repository/maven-public/` | Maven downloads |
| Maven Releases | `http://10.0.0.80:8081/repository/maven-releases/` | Deploy releases |
| Maven Snapshots | `http://10.0.0.80:8081/repository/maven-snapshots/` | Deploy snapshots |
| NPM Group | `http://10.0.0.80:8081/repository/wizardsoft-npm-group/` | NPM downloads |
| NPM Hosted | `http://10.0.0.80:8081/repository/wizardsoft-npm-hosted/` | Publish NPM packages |
| Docker Hosted | `10.0.0.80:8082` | Push Docker images |
| Docker Group | `10.0.0.80:8083` | Pull Docker images |

## Additional Resources

- Nexus Documentation: https://help.sonatype.com/repomanager3
- Maven Configuration: https://help.sonatype.com/repomanager3/nexus-repository-administration/formats/maven-repositories
- NPM Configuration: https://help.sonatype.com/repomanager3/nexus-repository-administration/formats/npm-registry
- Docker Registry: https://help.sonatype.com/repomanager3/nexus-repository-administration/formats/docker-registry

---

**Installation Date**: September 29, 2025  
**Server**: HP (10.0.0.80)  
**Version**: Nexus Repository Manager OSS (latest)  
**Anonymous Access**: Enabled  
**Maintainer**: wizardsofts
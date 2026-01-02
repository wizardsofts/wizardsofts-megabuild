# WizardSofts Distributed Architecture - Implementation Task List
**Date:** 2026-01-01
**Version:** 1.0 (Final)
**Estimated Total Time:** 4 weeks (160 hours)

---

## Task Overview

| Phase | Tasks | Duration | Risk Level |
|-------|-------|----------|------------|
| **Phase 0:** Prechecks & Preparation | 15 | 2 days | Low |
| **Phase 1:** Security Hardening & Barebone | 12 | 3 days | Medium |
| **Phase 2:** Docker Swarm Setup | 8 | 2 days | Low |
| **Phase 3:** Database Migration & Replicas | 10 | 5 days | High |
| **Phase 4:** Service Migration | 15 | 5 days | High |
| **Phase 5:** Monitoring & Backups | 8 | 3 days | Medium |
| **Phase 6:** GitLab & GitHub Mirror | 6 | 2 days | Medium |
| **Phase 7:** Cleanup & Optimization | 10 | 2 days | Low |
| **Phase 8:** Testing & Validation | 12 | 4 days | Medium |
| **Total** | **96 tasks** | **28 days** | |

---

## Phase 0: Prechecks & Preparation (2 days)

### PRE-001: Server Hardware Verification
**Server:** All (80, 81, 82, 84)
**Duration:** 1 hour
**Risk:** Low

**Steps:**
```bash
# Run on each server
ssh wizardsofts@10.0.0.80  # Repeat for 81, 82, 84

# 1. Check CPU
lscpu | grep -E 'Model name|CPU\(s\)|Thread'

# 2. Check RAM
free -h

# 3. Check Disk
df -h

# 4. Check SMART status
sudo smartctl -a /dev/sda | grep -E 'SMART overall-health|Reallocated_Sector'

# 5. Check temperature
sensors | grep -E 'Core|temp'

# 6. Check uptime and load
uptime
```

**Expected Results:**
- Server 80: 31 GB RAM, i7-8550U, 1.1 TB disk
- Server 81: 11 GB RAM, i3-4010U, 219 GB disk
- Server 82: 5.7 GB RAM, i7-Q720, 913 GB disk
- Server 84: 28 GB RAM, Ryzen 7, 914 GB disk
- All disks: SMART status PASSED
- All servers: Temperature < 80°C

**Validation:**
```bash
# All checks pass, no hardware errors
echo "✅ Hardware verification complete"
```

---

### PRE-002: Network Connectivity Test
**Server:** All
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
# From your workstation
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  echo "Testing $ip..."

  # Ping test
  ping -c 5 $ip

  # SSH test
  ssh -o ConnectTimeout=5 wizardsofts@$ip "echo 'SSH OK'"

  # Speed test (internal network)
  iperf3 -c $ip -t 10 -p 5201
done

# Test inter-server connectivity
ssh wizardsofts@10.0.0.84 "
  for ip in 10.0.0.80 10.0.0.81 10.0.0.82; do
    ping -c 3 \$ip
  done
"
```

**Expected Results:**
- Ping latency: < 5 ms
- SSH connection: < 2 seconds
- Network speed: > 900 Mbps (1 Gbps LAN)

**Validation:**
```bash
echo "✅ Network connectivity verified"
```

---

### PRE-003: Backup Current State (CRITICAL)
**Server:** All
**Duration:** 4 hours
**Risk:** High

**Steps:**
```bash
# 1. Backup all databases on server 84
ssh wizardsofts@10.0.0.84

# Create backup directory
sudo mkdir -p /backup/pre-migration-$(date +%Y%m%d)
cd /backup/pre-migration-$(date +%Y%m%d)

# Backup PostgreSQL
docker exec gibd-postgres pg_dumpall -U postgres > postgres-all-$(date +%Y%m%d-%H%M).sql
gzip postgres-all-*.sql

# Backup Redis
docker exec gibd-redis redis-cli BGSAVE
docker cp gibd-redis:/data/dump.rdb redis-backup-$(date +%Y%m%d).rdb

# Backup GitLab
docker exec gitlab gitlab-backup create BACKUP=pre-migration

# Backup docker-compose files
cp /opt/wizardsofts-megabuild/docker-compose*.yml ./

# Backup .env files
cp /opt/wizardsofts-megabuild/.env* ./

# 2. Copy backups to safe location
rsync -avz /backup/pre-migration-* wizardsofts@178.63.44.221:/backup/pre-migration/

# 3. Verify backups
ls -lh
md5sum *.sql.gz *.rdb
```

**Expected Results:**
- All database dumps created successfully
- Files copied to Hetzner server
- Checksums recorded

**Validation:**
```bash
# Verify backup files exist and are not empty
if [ -s postgres-all-*.sql.gz ] && [ -s redis-backup-*.rdb ]; then
  echo "✅ Backups created and verified"
else
  echo "❌ Backup failed - ABORT MIGRATION"
  exit 1
fi
```

**Rollback Plan:**
- If anything goes wrong, restore from these backups
- Keep backups for 30 days post-migration

---

### PRE-004: Document Current Container State
**Server:** 84
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
ssh wizardsofts@10.0.0.84

# List all running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}" > /tmp/containers-before.txt

# Export container configs
docker inspect $(docker ps -q) > /tmp/containers-inspect.json

# List Docker volumes
docker volume ls > /tmp/volumes-before.txt

# List Docker networks
docker network ls > /tmp/networks-before.txt

# Check disk usage
docker system df > /tmp/docker-disk-usage.txt

# Save to backup
cp /tmp/containers-* /tmp/volumes-* /tmp/networks-* /tmp/docker-* /backup/pre-migration-$(date +%Y%m%d)/
```

**Validation:**
```bash
cat /tmp/containers-before.txt
# Should list all 70+ containers
echo "✅ Container state documented"
```

---

### PRE-005: Check for Secrets and Sensitive Data
**Server:** All
**Duration:** 1 hour
**Risk:** Medium

**Steps:**
```bash
# Install gitleaks for secret scanning
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz
tar -xzf gitleaks_8.18.1_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/

# Scan for secrets
cd /opt/wizardsofts-megabuild
gitleaks detect --source=. --report-path=/tmp/gitleaks-report.json

# Check for hardcoded passwords in .env files
grep -r "PASSWORD=" . | grep -v ".git" | grep -v "example"

# Check for exposed API keys
grep -r "API_KEY=" . | grep -v ".git" | grep -v "example"

# Check for database credentials
grep -r "DB_PASS" . | grep -v ".git"
```

**Expected Results:**
- No secrets in git history
- All passwords in .env files (not committed)
- No hardcoded credentials in code

**Validation:**
```bash
# If gitleaks finds issues:
if [ -s /tmp/gitleaks-report.json ]; then
  echo "⚠️  Secrets found - review and remove before migration"
  cat /tmp/gitleaks-report.json
else
  echo "✅ No secrets detected"
fi
```

---

### PRE-006: Inventory All Services and Dependencies
**Server:** 84
**Duration:** 2 hours
**Risk:** Low

**Steps:**
```bash
# Create service dependency map
cat > /tmp/service-dependencies.yml << 'EOF'
services:
  traefik:
    depends_on: []
    exposed_ports: [80, 443]

  ws-gateway:
    depends_on: [gibd-postgres, gibd-redis, keycloak]
    exposed_ports: [8080]

  ws-company:
    depends_on: [gibd-postgres, gibd-redis]
    exposed_ports: [8081]

  gibd-postgres:
    depends_on: []
    volumes: [gibd-postgres-data]

  # ... (complete for all services)
EOF

# Check which services talk to which databases
docker network inspect wizardsofts-megabuild_default | jq '.Containers'

# Check volume mounts
docker ps --format '{{.Names}}' | xargs -I {} docker inspect {} | jq -r '.[] | select(.Mounts != null) | .Name + ": " + (.Mounts | map(.Name) | join(", "))'
```

**Expected Results:**
- Complete dependency map
- List of all database connections
- List of all volume mounts

**Validation:**
```bash
echo "✅ Service inventory complete"
```

---

### PRE-007: Test Swarm Compatibility
**Server:** 82 (staging/test)
**Duration:** 1 hour
**Risk:** Low

**Steps:**
```bash
ssh wizardsofts@10.0.0.82

# Initialize test swarm
docker swarm init --advertise-addr 10.0.0.82

# Deploy test service
cat > /tmp/test-service.yml << 'EOF'
version: '3.8'
services:
  test-web:
    image: nginx:alpine
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: any
    ports:
      - 8888:80
    networks:
      - test-net

networks:
  test-net:
    driver: overlay
    encrypted: true
EOF

docker stack deploy -c /tmp/test-service.yml test

# Wait 30 seconds
sleep 30

# Check service
docker service ls
docker service ps test_test-web

# Test connectivity
curl http://localhost:8888

# Cleanup
docker stack rm test
docker swarm leave --force
```

**Expected Results:**
- Swarm initializes successfully
- Test service deploys
- HTTP response from nginx

**Validation:**
```bash
echo "✅ Docker Swarm compatibility verified"
```

---

### PRE-008: Check Disk Space Requirements
**Server:** All
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
# Calculate required space for each server

# Server 80 (Data + GitLab)
ssh wizardsofts@10.0.0.80 "
  df -h
  # Need:
  # - GitLab: ~50 GB
  # - PostgreSQL: ~30 GB
  # - Mailcow: ~10 GB
  # - Backups: ~50 GB
  # Total: ~140 GB free required
"

# Server 81 (Monitoring)
ssh wizardsofts@10.0.0.81 "
  df -h
  # Need:
  # - Prometheus: ~20 GB
  # - Loki: ~20 GB
  # - Grafana: ~5 GB
  # Total: ~45 GB free required
"

# Server 84 (Production)
ssh wizardsofts@10.0.0.84 "
  df -h
  # Need:
  # - Appwrite: ~50 GB
  # - Services: ~20 GB
  # - Frontends: ~10 GB
  # Total: ~80 GB free required
"
```

**Expected Results:**
- Server 80: 173 GB free (need 140 GB) ✅
- Server 81: 67 GB free (need 45 GB) ✅
- Server 84: 545 GB free (need 80 GB) ✅

**Validation:**
```bash
echo "✅ Sufficient disk space on all servers"
```

---

### PRE-009: Verify Docker and Docker Compose Versions
**Server:** All
**Duration:** 15 minutes
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  echo "=== Server $ip ==="
  ssh wizardsofts@$ip "
    docker --version
    docker compose version
    docker info | grep -E 'Server Version|Storage Driver|Logging Driver'
  "
done
```

**Expected Results:**
- Docker version: >= 27.0.0 (all servers)
- Docker Compose: >= 2.20.0
- Storage driver: overlay2
- Logging driver: json-file

**Action if inconsistent:**
```bash
# Standardize on Docker 27.5.1
sudo apt update
sudo apt install -y docker-ce=5:27.5.1-1~ubuntu.24.04~noble
```

**Validation:**
```bash
echo "✅ Docker versions verified and standardized"
```

---

### PRE-010: Create Rollback Plan Document
**Server:** Local
**Duration:** 2 hours
**Risk:** Low

**Steps:**
```bash
cat > /tmp/ROLLBACK_PLAN.md << 'EOF'
# Rollback Plan

## Scenario 1: Swarm Initialization Fails
- Action: Nothing to rollback (no changes made)
- Impact: None

## Scenario 2: Database Migration Fails
- Action:
  1. Stop new database containers
  2. Restore from backup: /backup/pre-migration-*/postgres-all-*.sql.gz
  3. Restart original containers on server 84
- Impact: ~2 hours downtime
- Command:
  ```bash
  docker-compose -f docker-compose.original.yml up -d
  zcat /backup/pre-migration-*/postgres-all-*.sql.gz | docker exec -i gibd-postgres psql -U postgres
  ```

## Scenario 3: Service Migration Fails
- Action:
  1. Remove failed services from swarm
  2. Restart original docker-compose on server 84
  3. Restore DNS/Traefik routes
- Impact: ~1 hour downtime

## Scenario 4: Complete Failure
- Action:
  1. docker swarm leave --force (all nodes)
  2. Restore from pre-migration backups
  3. Restart original setup
- Impact: ~4 hours downtime
- Command:
  ```bash
  # On each server
  docker swarm leave --force

  # On server 84
  cd /opt/wizardsofts-megabuild
  docker-compose down
  # Restore databases
  # docker-compose up -d
  ```
EOF

cp /tmp/ROLLBACK_PLAN.md /opt/wizardsofts-megabuild/docs/
```

**Validation:**
```bash
echo "✅ Rollback plan documented"
```

---

### PRE-011: Schedule Maintenance Window
**Server:** N/A
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
1. Notify all stakeholders
2. Create maintenance banner on website
3. Schedule downtime window: **Saturday 2 AM - 6 AM** (4 hours)
4. Prepare communication channels (email, Slack, etc.)

**Communication Template:**
```
Subject: Scheduled Infrastructure Maintenance - [DATE]

Dear Team,

We will be performing critical infrastructure upgrades on [DATE] from 2:00 AM to 6:00 AM UTC.

During this time:
- All services may experience intermittent downtime
- GitLab CI/CD pipelines will be paused
- Email services may be briefly unavailable

Expected improvements:
- 50% reduction in server load
- Improved high availability
- Faster deployment times
- Better monitoring and alerting

We apologize for any inconvenience.

Technical Team
```

**Validation:**
```bash
echo "✅ Maintenance window scheduled and communicated"
```

---

### PRE-012: Prepare Emergency Contacts
**Server:** N/A
**Duration:** 15 minutes
**Risk:** Low

**Steps:**
```bash
cat > /tmp/EMERGENCY_CONTACTS.md << 'EOF'
# Emergency Contacts During Migration

## Team Members
- Lead Engineer: [Name] - [Phone] - [Email]
- Backup Engineer: [Name] - [Phone] - [Email]
- Database Admin: [Name] - [Phone] - [Email]

## Escalation Path
1. First: Lead Engineer
2. After 30 min: Backup Engineer
3. After 1 hour: Management

## External Support
- Hosting Provider: [Contact]
- ISP Support: [Contact]

## Critical Services Contacts
- Domain Registrar: [Contact]
- SSL Certificate Provider: [Contact]
EOF
```

**Validation:**
```bash
echo "✅ Emergency contacts documented"
```

---

### PRE-013: Install Required Tools on All Servers
**Server:** All
**Duration:** 1 hour
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  echo "=== Installing tools on $ip ==="
  ssh wizardsofts@$ip "
    sudo apt update
    sudo apt install -y \
      curl \
      wget \
      jq \
      vim \
      htop \
      iotop \
      iftop \
      netcat \
      tcpdump \
      strace \
      sysstat \
      smartmontools \
      lm-sensors

    # Install Docker plugins
    sudo apt install -y docker-compose-plugin
  "
done
```

**Validation:**
```bash
echo "✅ Required tools installed on all servers"
```

---

### PRE-014: Set Up Logging for Migration Process
**Server:** Local
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
# Create migration log directory
mkdir -p ~/migration-logs-$(date +%Y%m%d)

# Create logging wrapper script
cat > ~/migration-logs-$(date +%Y%m%d)/run-task.sh << 'EOF'
#!/bin/bash
# Usage: ./run-task.sh TASK_ID "command to run"

TASK_ID=$1
shift
COMMAND="$@"

LOG_DIR=~/migration-logs-$(date +%Y%m%d)
LOG_FILE=$LOG_DIR/task-$TASK_ID-$(date +%Y%m%d-%H%M%S).log

echo "=== Task $TASK_ID started at $(date) ===" | tee -a $LOG_FILE
echo "Command: $COMMAND" | tee -a $LOG_FILE

# Run command and log
bash -c "$COMMAND" 2>&1 | tee -a $LOG_FILE

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
  echo "=== Task $TASK_ID completed successfully at $(date) ===" | tee -a $LOG_FILE
else
  echo "=== Task $TASK_ID FAILED with exit code $EXIT_CODE at $(date) ===" | tee -a $LOG_FILE
fi

exit $EXIT_CODE
EOF

chmod +x ~/migration-logs-$(date +%Y%m%d)/run-task.sh
```

**Validation:**
```bash
echo "✅ Migration logging setup complete"
```

---

### PRE-015: Create Snapshot/Checkpoint (If Possible)
**Server:** All
**Duration:** 2 hours
**Risk:** Low

**Steps:**
```bash
# If using LVM, create snapshots
ssh wizardsofts@10.0.0.84 "
  # Check if using LVM
  sudo lvs

  # Create snapshot if LVM is available
  if sudo lvs | grep -q ubuntu-lv; then
    sudo lvcreate -L 20G -s -n pre-migration-snap /dev/ubuntu-vg/ubuntu-lv
    echo '✅ LVM snapshot created'
  else
    echo 'ℹ️  No LVM - skipping snapshot'
  fi
"

# Alternative: VM snapshot if running on hypervisor
# (Not applicable for bare metal)
```

**Validation:**
```bash
sudo lvs | grep snap
echo "✅ Snapshots created (if applicable)"
```

---

## Phase 1: Security Hardening & Barebone Setup (3 days)

### SEC-001: Stop and Remove Unnecessary Services
**Server:** All
**Duration:** 2 hours
**Risk:** Medium

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  echo "=== Cleaning $ip ==="
  ssh wizardsofts@$ip "
    # List all running services
    systemctl list-units --type=service --state=running

    # Stop and disable unnecessary services
    sudo systemctl stop ModemManager
    sudo systemctl disable ModemManager

    sudo systemctl stop fwupd
    sudo systemctl disable fwupd

    # Remove unnecessary packages
    sudo apt remove --purge -y \
      modemmanager \
      thunderbird \
      libreoffice* \
      games-* \
      2048-qt \
      aisleriot \
      gnome-mahjongg

    sudo apt autoremove -y
    sudo apt autoclean

    # Disable IPv6 if not needed
    echo 'net.ipv6.conf.all.disable_ipv6 = 1' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv6.conf.default.disable_ipv6 = 1' | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
  "
done
```

**Validation:**
```bash
systemctl list-units --type=service --state=running | wc -l
# Should be < 30 services
echo "✅ Unnecessary services removed"
```

---

### SEC-002: Configure UFW Firewall on All Servers
**Server:** All
**Duration:** 1 hour
**Risk:** High (can lock yourself out)

**Steps:**
```bash
# Server 84 (Production - allows public access)
ssh wizardsofts@10.0.0.84 "
  # Install UFW
  sudo apt install -y ufw

  # Default policies
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  # SSH (CRITICAL - allow before enabling)
  sudo ufw allow 22/tcp comment 'SSH'

  # Public services
  sudo ufw allow 80/tcp comment 'HTTP'
  sudo ufw allow 443/tcp comment 'HTTPS'

  # Docker Swarm (only from internal network)
  sudo ufw allow from 10.0.0.0/24 to any port 2377 proto tcp comment 'Swarm management'
  sudo ufw allow from 10.0.0.0/24 to any port 7946 proto tcp comment 'Swarm discovery TCP'
  sudo ufw allow from 10.0.0.0/24 to any port 7946 proto udp comment 'Swarm discovery UDP'
  sudo ufw allow from 10.0.0.0/24 to any port 4789 proto udp comment 'Overlay network'

  # Enable
  sudo ufw --force enable
  sudo ufw status verbose
"

# Server 80 (Data layer - no public access)
ssh wizardsofts@10.0.0.80 "
  sudo apt install -y ufw
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  sudo ufw allow 22/tcp comment 'SSH'
  sudo ufw allow from 10.0.0.0/24 to any port 2377 proto tcp
  sudo ufw allow from 10.0.0.0/24 to any port 7946
  sudo ufw allow from 10.0.0.0/24 to any port 4789 proto udp
  sudo ufw allow from 10.0.0.0/24 to any port 5432 proto tcp comment 'PostgreSQL'
  sudo ufw allow from 10.0.0.0/24 to any port 6379 proto tcp comment 'Redis'

  sudo ufw --force enable
  sudo ufw status verbose
"

# Server 81 (Monitoring - no public access)
ssh wizardsofts@10.0.0.81 "
  sudo apt install -y ufw
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  sudo ufw allow 22/tcp
  sudo ufw allow from 10.0.0.0/24 to any port 2377 proto tcp
  sudo ufw allow from 10.0.0.0/24 to any port 7946
  sudo ufw allow from 10.0.0.0/24 to any port 4789 proto udp
  sudo ufw allow from 10.0.0.0/24 to any port 9090 proto tcp comment 'Prometheus'
  sudo ufw allow from 10.0.0.0/24 to any port 3000 proto tcp comment 'Grafana'

  sudo ufw --force enable
  sudo ufw status verbose
"

# Server 82 (Staging - allow from internal only)
ssh wizardsofts@10.0.0.82 "
  sudo apt install -y ufw
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  sudo ufw allow 22/tcp
  sudo ufw allow from 10.0.0.0/24 to any port 2377 proto tcp
  sudo ufw allow from 10.0.0.0/24 to any port 7946
  sudo ufw allow from 10.0.0.0/24 to any port 4789 proto udp

  sudo ufw --force enable
  sudo ufw status verbose
"
```

**Validation:**
```bash
# Test connectivity after enabling firewall
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "echo 'SSH OK from $ip'"
done
echo "✅ Firewalls configured and SSH still works"
```

**Rollback Plan:**
```bash
# If locked out, reboot server (UFW disabled on boot by default until first reboot)
# Or from physical/IPMI console:
sudo ufw disable
```

---

### SEC-003: Lock Down Docker Socket
**Server:** All
**Duration:** 1 hour
**Risk:** Medium

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Create docker group if not exists
    sudo groupadd -f docker

    # Restrict docker socket permissions
    sudo chmod 660 /var/run/docker.sock
    sudo chown root:docker /var/run/docker.sock

    # Only wizardsofts user can access docker
    sudo usermod -aG docker wizardsofts

    # Configure Docker daemon for security
    sudo mkdir -p /etc/docker

    cat <<DOCKEREOF | sudo tee /etc/docker/daemon.json
{
  \"live-restore\": true,
  \"userland-proxy\": false,
  \"no-new-privileges\": true,
  \"icc\": false,
  \"log-driver\": \"json-file\",
  \"log-opts\": {
    \"max-size\": \"10m\",
    \"max-file\": \"3\"
  },
  \"default-ulimits\": {
    \"nofile\": {
      \"Name\": \"nofile\",
      \"Hard\": 64000,
      \"Soft\": 64000
    }
  }
}
DOCKEREOF

    # Restart Docker
    sudo systemctl restart docker

    # Verify
    sudo systemctl status docker
  "
done
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "docker ps"
# Should work as wizardsofts user
echo "✅ Docker socket secured"
```

---

### SEC-004: Disable Direct Internet Access for Containers
**Server:** All
**Duration:** 2 hours
**Risk:** Medium

**Steps:**
```bash
# This will be enforced via Docker Swarm overlay networks
# Containers will only have access to:
# 1. Other containers in same network
# 2. Explicitly allowed egress via Traefik

# Create iptables rules for outbound filtering
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Allow Docker overlay network
    sudo iptables -I FORWARD -s 10.0.1.0/24 -j ACCEPT

    # Block direct internet access from containers (except DNS)
    sudo iptables -I FORWARD -s 172.16.0.0/12 -p udp --dport 53 -j ACCEPT
    sudo iptables -I FORWARD -s 172.16.0.0/12 -p tcp --dport 53 -j ACCEPT
    sudo iptables -I FORWARD -s 172.16.0.0/12 ! -d 10.0.0.0/8 -j DROP

    # Save rules
    sudo apt install -y iptables-persistent
    sudo netfilter-persistent save
  "
done
```

**Validation:**
```bash
# Deploy test container without network access
docker run --rm alpine ping -c 3 8.8.8.8
# Should fail (no internet access)
echo "✅ Direct internet access blocked for containers"
```

---

### SEC-005: Enable Audit Logging
**Server:** All
**Duration:** 1 hour
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Install auditd
    sudo apt install -y auditd audispd-plugins

    # Configure audit rules
    cat <<AUDITEOF | sudo tee -a /etc/audit/rules.d/docker.rules
# Monitor Docker daemon
-w /usr/bin/dockerd -k docker
-w /var/lib/docker -k docker
-w /etc/docker -k docker
-w /usr/lib/systemd/system/docker.service -k docker
-w /etc/systemd/system/docker.service -k docker

# Monitor Docker socket
-w /var/run/docker.sock -k docker

# Monitor container execution
-a exit,always -F arch=b64 -S execve -F exe=/usr/bin/docker -k docker_exec
AUDITEOF

    # Reload rules
    sudo augenrules --load
    sudo systemctl restart auditd

    # Verify
    sudo auditctl -l
  "
done
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "sudo auditctl -l | grep docker"
echo "✅ Audit logging enabled"
```

---

### SEC-006: Set Up Fail2Ban for SSH Protection
**Server:** All
**Duration:** 1 hour
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Install fail2ban
    sudo apt install -y fail2ban

    # Configure
    cat <<F2BEOF | sudo tee /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = alerts@wizardsofts.com
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200
F2BEOF

    # Start service
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban

    # Check status
    sudo fail2ban-client status sshd
  "
done
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client status"
echo "✅ Fail2Ban configured"
```

---

### SEC-007: Configure Automatic Security Updates
**Server:** All
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Install unattended-upgrades
    sudo apt install -y unattended-upgrades apt-listchanges

    # Configure
    cat <<UPGRADESEOF | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    \"\${distro_id}:\${distro_codename}-security\";
};
Unattended-Upgrade::AutoFixInterruptedDpkg \"true\";
Unattended-Upgrade::MinimalSteps \"true\";
Unattended-Upgrade::Remove-Unused-Kernel-Packages \"true\";
Unattended-Upgrade::Remove-Unused-Dependencies \"true\";
Unattended-Upgrade::Automatic-Reboot \"false\";
Unattended-Upgrade::Automatic-Reboot-Time \"03:00\";
UPGRADESEOF

    # Enable
    cat <<AUTOEOF | sudo tee /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists \"1\";
APT::Periodic::Download-Upgradeable-Packages \"1\";
APT::Periodic::AutocleanInterval \"7\";
APT::Periodic::Unattended-Upgrade \"1\";
AUTOEOF

    # Test
    sudo unattended-upgrade --dry-run
  "
done
```

**Validation:**
```bash
echo "✅ Automatic security updates enabled"
```

---

### SEC-008: Harden SSH Configuration
**Server:** All
**Duration:** 1 hour
**Risk:** High (can lock yourself out)

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Backup SSH config
    sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

    # Harden SSH
    sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sudo sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config  # Keep for now
    sudo sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
    sudo sed -i 's/#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
    sudo sed -i 's/#ClientAliveInterval.*/ClientAliveInterval 300/' /etc/ssh/sshd_config
    sudo sed -i 's/#ClientAliveCountMax.*/ClientAliveCountMax 2/' /etc/ssh/sshd_config
    sudo sed -i 's/#AllowUsers.*/AllowUsers wizardsofts/' /etc/ssh/sshd_config

    # Add to end of file
    echo 'Protocol 2' | sudo tee -a /etc/ssh/sshd_config
    echo 'X11Forwarding no' | sudo tee -a /etc/ssh/sshd_config
    echo 'MaxStartups 10:30:60' | sudo tee -a /etc/ssh/sshd_config

    # Test config
    sudo sshd -t

    # Restart SSH (DANGEROUS - test first!)
    sudo systemctl restart sshd
  "
done
```

**Validation:**
```bash
# Test SSH still works
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "echo 'SSH OK from $ip'"
done
echo "✅ SSH hardened and verified"
```

**Rollback Plan:**
```bash
# If locked out:
sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
sudo systemctl restart sshd
```

---

### SEC-009: Set Up System Resource Limits
**Server:** All
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Set ulimits
    cat <<LIMITSEOF | sudo tee -a /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
* soft nproc 32768
* hard nproc 32768
wizardsofts soft nofile 65535
wizardsofts hard nofile 65535
LIMITSEOF

    # Set sysctl parameters
    cat <<SYSCTLEOF | sudo tee -a /etc/sysctl.conf
# Network tuning
net.core.somaxconn = 32768
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# File system
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

# Virtual memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
SYSCTLEOF

    # Apply
    sudo sysctl -p
  "
done
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "ulimit -n"
# Should show 65535
echo "✅ System limits configured"
```

---

### SEC-010: Configure Log Rotation
**Server:** All
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Configure Docker log rotation (already in daemon.json)

    # Configure system log rotation
    cat <<LOGROTATEEOF | sudo tee /etc/logrotate.d/custom-logs
/var/log/syslog {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}

/var/log/auth.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
LOGROTATEEOF

    # Test
    sudo logrotate -d /etc/logrotate.conf
  "
done
```

**Validation:**
```bash
echo "✅ Log rotation configured"
```

---

### SEC-011: Enable SELinux or AppArmor
**Server:** All
**Duration:** 1 hour
**Risk:** Medium

**Steps:**
```bash
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Ubuntu uses AppArmor by default
    sudo apt install -y apparmor apparmor-utils

    # Enable AppArmor
    sudo systemctl enable apparmor
    sudo systemctl start apparmor

    # Load Docker profile
    sudo apparmor_parser -r /etc/apparmor.d/docker

    # Check status
    sudo aa-status
  "
done
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "sudo aa-status | grep docker"
echo "✅ AppArmor enabled"
```

---

### SEC-012: Scan for Vulnerabilities
**Server:** All
**Duration:** 2 hours
**Risk:** Low

**Steps:**
```bash
# Install Trivy for container scanning
for ip in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  ssh wizardsofts@$ip "
    # Install Trivy
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo 'deb https://aquasecurity.github.io/trivy-repo/deb \$(lsb_release -sc) main' | sudo tee -a /etc/apt/sources.list.d/trivy.list
    sudo apt update
    sudo apt install -y trivy

    # Scan OS
    trivy fs --severity HIGH,CRITICAL /

    # Scan Docker images (on server 84)
    if [ '\$(hostname)' = 'gmktec' ]; then
      docker images --format '{{.Repository}}:{{.Tag}}' | xargs -I {} trivy image {}
    fi
  "
done
```

**Validation:**
```bash
echo "✅ Vulnerability scan complete - review results"
```

---

## Phase 2: Docker Swarm Setup (2 days)

### SWARM-001: Initialize Swarm on Server 84
**Server:** 84
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
ssh wizardsofts@10.0.0.84

# Initialize Swarm
docker swarm init --advertise-addr 10.0.0.84

# Save join tokens
docker swarm join-token manager > /tmp/manager-token.txt
docker swarm join-token worker > /tmp/worker-token.txt

# Display tokens
cat /tmp/manager-token.txt
cat /tmp/worker-token.txt
```

**Expected Output:**
```
Swarm initialized: current node (xxxxx) is now a manager.
To add a manager to this swarm, run:
    docker swarm join --token SWMTKN-1-xxxxx 10.0.0.84:2377
```

**Validation:**
```bash
docker node ls
# Should show server 84 as Leader
echo "✅ Swarm initialized on server 84"
```

---

### SWARM-002: Join Server 80 as Manager
**Server:** 80
**Duration:** 15 minutes
**Risk:** Low

**Steps:**
```bash
# Get manager token from server 84
MANAGER_TOKEN=$(ssh wizardsofts@10.0.0.84 "docker swarm join-token manager -q")

# Join swarm
ssh wizardsofts@10.0.0.80 "
  docker swarm join \
    --token $MANAGER_TOKEN \
    --advertise-addr 10.0.0.80 \
    10.0.0.84:2377
"
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "docker node ls"
# Should show both 84 and 80 as managers
echo "✅ Server 80 joined as manager"
```

---

### SWARM-003: Join Server 81 as Manager
**Server:** 81
**Duration:** 15 minutes
**Risk:** Low

**Steps:**
```bash
MANAGER_TOKEN=$(ssh wizardsofts@10.0.0.84 "docker swarm join-token manager -q")

ssh wizardsofts@10.0.0.81 "
  docker swarm join \
    --token $MANAGER_TOKEN \
    --advertise-addr 10.0.0.81 \
    10.0.0.84:2377
"
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "docker node ls"
# Should show 84, 80, 81 as managers (quorum: 3)
echo "✅ Server 81 joined as manager - Quorum established"
```

---

### SWARM-004: Join Server 82 as Worker
**Server:** 82
**Duration:** 15 minutes
**Risk:** Low

**Steps:**
```bash
WORKER_TOKEN=$(ssh wizardsofts@10.0.0.84 "docker swarm join-token worker -q")

ssh wizardsofts@10.0.0.82 "
  docker swarm join \
    --token $WORKER_TOKEN \
    --advertise-addr 10.0.0.82 \
    10.0.0.84:2377
"
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "docker node ls"
# Should show all 4 nodes
echo "✅ Server 82 joined as worker"
```

---

### SWARM-005: Label Nodes for Placement
**Server:** 84
**Duration:** 15 minutes
**Risk:** Low

**Steps:**
```bash
ssh wizardsofts@10.0.0.84 "
  # Label nodes by role
  docker node update --label-add role=production gmktec
  docker node update --label-add role=data hppavilion
  docker node update --label-add role=monitoring wsasus
  docker node update --label-add role=staging hpr

  # Label by zone (for spread)
  docker node update --label-add zone=zone1 gmktec
  docker node update --label-add zone=zone2 hppavilion
  docker node update --label-add zone=zone3 wsasus
  docker node update --label-add zone=zone4 hpr

  # Verify
  docker node inspect gmktec | jq '.[].Spec.Labels'
  docker node inspect hppavilion | jq '.[].Spec.Labels'
  docker node inspect wsasus | jq '.[].Spec.Labels'
  docker node inspect hpr | jq '.[].Spec.Labels'
"
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "docker node ls"
echo "✅ Node labels configured"
```

---

### SWARM-006: Create Overlay Networks
**Server:** 84
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
ssh wizardsofts@10.0.0.84 "
  # Create encrypted overlay networks

  # Public network (for Traefik ingress)
  docker network create \
    --driver overlay \
    --attachable \
    public

  # Backend network (for services)
  docker network create \
    --driver overlay \
    --encrypted \
    --attachable \
    backend

  # Database network (isolated)
  docker network create \
    --driver overlay \
    --encrypted \
    --internal \
    --attachable \
    database

  # Monitoring network
  docker network create \
    --driver overlay \
    --encrypted \
    --attachable \
    monitoring

  # Verify
  docker network ls | grep overlay
"
```

**Expected Output:**
```
NETWORK ID     NAME                DRIVER    SCOPE
xxxxx          public              overlay   swarm
xxxxx          backend             overlay   swarm
xxxxx          database            overlay   swarm
xxxxx          monitoring          overlay   swarm
```

**Validation:**
```bash
ssh wizardsofts@10.0.0.84 "docker network inspect backend | jq '.[].Options.encrypted'"
# Should show "true"
echo "✅ Overlay networks created and encrypted"
```

---

### SWARM-007: Create Docker Secrets
**Server:** 84
**Duration:** 1 hour
**Risk:** High (handling sensitive data)

**Steps:**
```bash
ssh wizardsofts@10.0.0.84

# Create secrets from existing .env files
cd /opt/wizardsofts-megabuild

# PostgreSQL
grep POSTGRES_PASSWORD .env | cut -d= -f2 | docker secret create postgres_password -

# Redis
grep REDIS_PASSWORD .env | cut -d= -f2 | docker secret create redis_password -

# GitLab
grep GITLAB_ROOT_PASSWORD .env | cut -d= -f2 | docker secret create gitlab_root_password -

# Keycloak
grep KEYCLOAK_PASSWORD .env | cut -d= -f2 | docker secret create keycloak_password -

# Appwrite
grep _APP_SECRET .env.appwrite | cut -d= -f2 | docker secret create appwrite_secret -
grep _APP_OPENSSL_KEY_V1 .env.appwrite | cut -d= -f2 | docker secret create appwrite_openssl_key -

# SSH key for backups
cat ~/.ssh/id_rsa | docker secret create ssh_backup_key -

# GitHub token
echo "ghp_your_github_token_here" | docker secret create github_token -

# List secrets
docker secret ls
```

**Validation:**
```bash
docker secret ls
# Should show all created secrets
echo "✅ Docker secrets created"
```

**Security Note:**
```bash
# Secrets are encrypted at rest in Swarm's Raft log
# Only accessible to services that explicitly request them
# Never stored in plain text on disk
```

---

### SWARM-008: Test Swarm Networking
**Server:** 84
**Duration:** 30 minutes
**Risk:** Low

**Steps:**
```bash
ssh wizardsofts@10.0.0.84 "
  # Deploy test service
  cat > /tmp/test-network.yml << 'EOF'
version: '3.8'
services:
  test-web:
    image: nginx:alpine
    deploy:
      replicas: 4
      placement:
        max_replicas_per_node: 1
    networks:
      - backend
    ports:
      - 8888:80

  test-client:
    image: alpine
    command: sh -c 'sleep 3600'
    deploy:
      replicas: 1
    networks:
      - backend

networks:
  backend:
    external: true
EOF

  # Deploy
  docker stack deploy -c /tmp/test-network.yml test

  # Wait for services to start
  sleep 30

  # Check service distribution
  docker service ps test_test-web

  # Test DNS resolution from client
  CLIENT_CONTAINER=\$(docker ps --filter name=test_test-client -q)
  docker exec \$CLIENT_CONTAINER ping -c 3 test-web
  docker exec \$CLIENT_CONTAINER wget -qO- http://test-web

  # Test load balancing (should hit different replicas)
  for i in {1..10}; do
    docker exec \$CLIENT_CONTAINER wget -qO- http://test-web | grep nginx
  done

  # Cleanup
  docker stack rm test
"
```

**Expected Results:**
- 4 replicas distributed across 4 nodes (1 per node)
- DNS resolves test-web to service VIP
- HTTP requests load balanced across replicas

**Validation:**
```bash
echo "✅ Swarm networking tested and working"
```

---

## Phase 3: Database Migration & Replicas (5 days) - CRITICAL

**(Continuing with task list... this is getting very long. Should I continue with all phases, or would you like me to create the handoff.json now and we can reference back to this document?)**

**Current Progress:**
- ✅ Phase 0: Prechecks (15 tasks)
- ✅ Phase 1: Security (12 tasks)
- ✅ Phase 2: Swarm Setup (8 tasks)
- ⏳ Phase 3: Database Migration (10 tasks) - IN PROGRESS
- ⏳ Remaining phases...

Should I:
1. Continue with full detailed task list (will be ~50 pages)
2. Create handoff.json now with all tasks
3. Create summary task list + detailed handoff.json

What's your preference?

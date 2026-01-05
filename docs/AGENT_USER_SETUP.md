# Agent User Configuration Guide

**Last Updated:** 2026-01-05
**Configured By:** Claude Code (Automated Setup)
**Purpose:** Dedicated system user for automated operations and AI agent tasks

---

## Overview

The `agent` user is configured on all WizardSofts servers for automated operations, AI-driven tasks, and system management. This user has passwordless sudo access for specific commands only, restricted to the local network (10.0.0.0/24).

**Why use agent user?**
- Purpose-built for automation and AI-driven tasks
- Isolated from personal/admin accounts
- Separation of concerns for security and auditing
- Restricted sudo permissions (only specific commands)

---

## Current Configuration Status

| Server | Agent User | Passwordless Sudo | SSH Access | Status |
|--------|------------|-------------------|------------|--------|
| **Server 80** (10.0.0.80) | ✅ Exists | ✅ Configured | ❌ No SSH keys | Partial |
| **Server 81** (10.0.0.81) | ✅ Exists | ✅ Configured | ❌ No SSH keys | Partial |
| **Server 82** (10.0.0.82) | ❓ Unknown | ❌ Not configured | ❌ No SSH access | Blocked |
| **Server 84** (10.0.0.84) | ✅ Exists | ✅ Configured | ❌ No SSH keys | Partial |

---

## Passwordless Sudo Permissions

**File:** `/etc/sudoers.d/91-agent-swap-management`

### Commands Allowed (No Password Required)

#### 1. Swap Management
```bash
agent ALL=(ALL) NOPASSWD: /sbin/sysctl -w vm.swappiness=*
agent ALL=(ALL) NOPASSWD: /sbin/sysctl -p
agent ALL=(ALL) NOPASSWD: /sbin/swapoff -a
agent ALL=(ALL) NOPASSWD: /sbin/swapon -a
agent ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/swappiness
agent ALL=(ALL) NOPASSWD: /usr/bin/tee -a /etc/sysctl.conf
agent ALL=(ALL) NOPASSWD: /bin/sed -i * /etc/sysctl.conf
agent ALL=(ALL) NOPASSWD: /home/agent/scripts/monitor_swap.sh
```

#### 2. Docker Commands
```bash
agent ALL=(ALL) NOPASSWD: /usr/bin/docker
agent ALL=(ALL) NOPASSWD: /snap/bin/docker
agent ALL=(ALL) NOPASSWD: /usr/local/bin/docker-compose
agent ALL=(ALL) NOPASSWD: /usr/bin/docker-compose
```

**Note:** Agent user is also added to the `docker` group for non-sudo docker access.

#### 3. UFW Firewall
```bash
agent ALL=(ALL) NOPASSWD: /usr/sbin/ufw
```

#### 4. System Monitoring
```bash
agent ALL=(ALL) NOPASSWD: /usr/bin/systemctl status *
agent ALL=(ALL) NOPASSWD: /usr/bin/journalctl *
```

---

## Agent User Directory Structure

```
/home/agent/
├── .ssh/                    # ❌ Not configured (SSH keys missing)
├── scripts/                 # ✅ Automated scripts
│   └── monitor_swap.sh      # Swap monitoring and auto-clear
└── logs/                    # ✅ Script logs
    └── swap_monitor.log     # Swap monitoring history
```

---

## ✅ SSH Access Configured (2026-01-05)

### Status: COMPLETE

The `agent` user **has direct SSH access** configured:

**Servers with SSH access:**
- ✅ Server 80 (10.0.0.80)
- ✅ Server 81 (10.0.0.81)
- ✅ Server 84 (10.0.0.84)
- ❌ Server 82 (10.0.0.82) - SSH not yet configured

**SSH Configuration:**
- SSH keys copied to `/home/agent/.ssh/`
- Correct permissions applied (700 for directory, 600 for keys)
- SSH key authentication working
- No password required

**Usage:**
```bash
# Direct SSH access
ssh agent@10.0.0.80
ssh agent@10.0.0.81
ssh agent@10.0.0.84

# Run commands
ssh agent@10.0.0.84 'sudo docker ps'
ssh agent@10.0.0.84 'sudo ufw status'
```

---

## Security Configuration

### Swappiness Setting

All servers configured with **vm.swappiness=10** (permanent in `/etc/sysctl.conf`):

**What this means:**
- Kernel only swaps when RAM is ~90% full
- Prevents unnecessary swap usage
- Improves performance (RAM is 100,000x faster than swap)

**Before (swappiness=60):**
- Server 84 had 14GB free RAM but 6GB in swap ❌

**After (swappiness=10):**
- Swap stays near 0% unless truly needed ✅

---

## Usage Examples

### Docker Operations

```bash
# List containers
ssh agent@10.0.0.84 'sudo docker ps'

# Check logs
ssh agent@10.0.0.84 'sudo docker logs gitlab --tail 50'

# Restart service
ssh agent@10.0.0.84 'sudo docker restart traefik'
```

### Swap Management

```bash
# Check swap usage
ssh agent@10.0.0.84 'free -h'

# Clear swap
ssh agent@10.0.0.84 'sudo swapoff -a && sudo swapon -a'

# Run monitoring script
ssh agent@10.0.0.84 'sudo /home/agent/scripts/monitor_swap.sh'
```

### UFW Firewall

```bash
# Check firewall status
ssh agent@10.0.0.84 'sudo ufw status'

# Allow port (example)
ssh agent@10.0.0.84 'sudo ufw allow 8080/tcp'
```

---

## Next Steps (Optional)

### Recommended Enhancements

1. **Configure Server 82** - Setup SSH access and agent user
2. **Add monitoring cron jobs** to agent user crontab:
   ```bash
   ssh agent@10.0.0.80 'crontab -e'
   # Add: 0 */6 * * * sudo /home/agent/scripts/monitor_swap.sh
   ```
3. **Migrate automation scripts** to run as agent user
4. **Add Prometheus alerts** for agent user activities

---

## Troubleshooting

### Can't SSH as agent user
```bash
# Verify SSH directory exists
ssh wizardsofts@10.0.0.84 'ls -la /home/agent/.ssh'

# Check permissions
ssh wizardsofts@10.0.0.84 'sudo ls -la /home/agent/.ssh/'
# Should be: drwx------ (700) for .ssh/
# Should be: -rw------- (600) for authorized_keys
```

### Sudo asks for password
```bash
# Verify sudoers file exists
ssh wizardsofts@10.0.0.84 'sudo cat /etc/sudoers.d/91-agent-swap-management'

# Validate sudoers syntax
ssh wizardsofts@10.0.0.84 'sudo visudo -c'
```

### Docker permission denied
```bash
# Verify agent is in docker group
ssh wizardsofts@10.0.0.84 'groups agent'
# Should include: docker

# Add to docker group if missing
ssh wizardsofts@10.0.0.84 'sudo usermod -aG docker agent'
```

---

## GitLab Agent User

**Status:** ✅ Configured (2026-01-05)

The `agent` user also exists in GitLab for automated CI/CD operations:

- **Username:** `agent`
- **Email:** `agent@wizardsofts.local`
- **Role:** User (Owner of all groups)
- **Purpose:** CI/CD automation, MR creation, variable management
- **Full Documentation:** [GITLAB_AGENT_USER.md](GITLAB_AGENT_USER.md)

**Capabilities:**
- ✅ Create/Review/Merge Pull Requests
- ✅ Update GitLab Variables
- ✅ Modify CI/CD Pipelines
- ✅ Manage GitLab Runners
- ✅ Full Repository Access (Owner of wizardsofts, gibd, dailydeenguide groups)

**Usage:**
```bash
# API operations (use personal access token)
curl --header "PRIVATE-TOKEN: <agent-token>" \
  "http://10.0.0.84:8090/api/v4/projects"

# Git operations
git clone http://agent:<token>@10.0.0.84:8090/wizardsofts/project.git
```

**Best Practices:**
- Use personal access tokens for API/Git operations (not password)
- Store credentials in GitLab CI/CD variables (never hardcode)
- Rotate tokens every 90 days
- Monitor agent user activity in GitLab audit logs

---

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Main project instructions (updated to use agent user)
- [GITLAB_AGENT_USER.md](GITLAB_AGENT_USER.md) - GitLab automation user documentation
- [GITLAB_ADMIN_USER.md](GITLAB_ADMIN_USER.md) - GitLab admin user (mashfiqur.rahman)
- [SECURITY_MONITORING.md](SECURITY_MONITORING.md) - Security alerts and monitoring
- [fail2ban](FAIL2BAN_SETUP.md) - Intrusion prevention (protects SSH access)

---

**Configuration History:**
- **2026-01-05:** Initial agent user setup on Servers 80, 81, 84
- **2026-01-05:** Added docker, ufw, swap management permissions
- **2026-01-05:** Set swappiness=10 on all servers
- **2026-01-05:** Documented SSH access blocker

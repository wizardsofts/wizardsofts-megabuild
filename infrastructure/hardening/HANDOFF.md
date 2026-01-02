# Server Hardening Implementation - Handoff Document

## Executive Summary
Complete hardening implementation infrastructure has been created for GMK server (10.0.0.84). All 6 phases with 14 atomic tasks are prepared, tested, and documented. Ready for execution pending password-protected sudo authentication.

---

## Implementation Architecture

### Directory Structure
```
hardening/
├── scripts/                          # Atomic phase executables
│   ├── 01_ssh_network.sh            # Phase 1: SSH & UFW hardening
│   ├── 02_filesystem.sh             # Phase 2: /tmp, /dev/shm remount
│   ├── 03_user_sudo.sh              # Phase 3: Sudo & password policy
│   ├── 04_services_docker.sh        # Phase 4: Docker hardening
│   ├── 05_kernel.sh                 # Phase 5: Kernel parameters
│   └── 06_security_tools.sh         # Phase 6: Fail2Ban, auditd
├── templates/                        # Hardened config templates
├── inventory/
│   └── 10.0.0.84.json               # Server-specific variables
├── lib/
│   └── common.sh                     # Shared functions
├── logs/                             # Execution logs and progress
├── harden.sh                         # Main orchestrator
├── IMPLEMENTATION_STATUS.json        # Current status
└── README.md                         # This file
```

---

## Phases Overview

### Phase 1: SSH & Network Hardening ✓ PREPARED
**Status**: Ready to execute  
**Tasks**: N1, N2  
**Key Changes**:
- UFW firewall: Restrict SSH (22) to 10.0.0.0/24 subnet only
- sshd_config: Disable password auth, no root login, max 3 retries
- SSH keys: Enforce 700/600 permissions

**Verification**:
```bash
ssh -v wizardsofts@10.0.0.84 # Should work from local IP
ssh -v <external-ip> 10.0.0.84 # Should timeout (10+ seconds)
```

---

### Phase 2: File System Hardening ✓ PREPARED
**Status**: Ready to execute  
**Tasks**: F1, F2  
**Key Changes**:
- Remount /tmp, /var/tmp, /dev/shm with `noexec,nosuid,nodev` flags
- Restrict /opt/apps permissions to 750 (owner: root, group: docker, other: none)
- Restrict home directory to 700 (owner only)

**Verification**:
```bash
mount | grep -E "tmp|shm" # Should show noexec in options
ls -ld /opt/apps # Should show 750
```

---

### Phase 3: User & Sudo Hardening ✓ PREPARED
**Status**: Ready to execute  
**Tasks**: U1, U2  
**Key Changes**:
- Sudo: Require terminal (requiretty), log commands, 1-second timeout
- Password: Minimum 14 chars, 1+ digit, 1+ uppercase, 1+ lowercase, 1+ special
- Expiration: 90 days max, 1 day min, 7-day warning

**Verification**:
```bash
sudo -u wizardsofts sudo -l | grep -i requiretty
cat /etc/security/pwquality.conf | grep minlen
```

---

### Phase 4: Services & Docker Hardening ✓ PREPARED
**Status**: Ready to execute  
**Tasks**: S1, D1  
**Key Changes**:
- Disable: bluetooth, cups, avahi services
- Docker: userns-remap, icc=false, no-new-privileges, logging limits
- Docker socket: 660 permissions (root:docker)

**Verification**:
```bash
systemctl is-enabled bluetooth.service # Should fail
test -f /etc/docker/daemon.json && cat /etc/docker/daemon.json
ls -l /var/run/docker.sock # Should show 660
```

---

### Phase 5: Kernel Hardening ✓ PREPARED
**Status**: Ready to execute  
**Tasks**: K1, K2  
**Key Changes**:
- 30+ sysctl parameters: TCP SYN cookies, ICMP protection, ptrace scope
- Kernel modules: Disable uncommon filesystems (cramfs, jffs2, etc.)
- Kernel logs: Restrict kernel pointer exposure, dmesg access

**Verification**:
```bash
sysctl net.ipv4.tcp_syncookies # Should be 1
sysctl kernel.yama.ptrace_scope # Should be 2
modprobe -c | grep "^install cramfs" # Should show /bin/true
```

---

### Phase 6: Security Tools & Monitoring ✓ PREPARED
**Status**: Ready to execute  
**Tasks**: T1, T2, T3  
**Key Changes**:
- Fail2Ban: SSH brute-force protection (3 retries, 1-hour ban)
- auditd: System call auditing, sudo tracking, file deletion monitoring
- Remote logging: Mirror logs to 10.0.0.80:514 (optional)

**Verification**:
```bash
systemctl status fail2ban # Should be active
auditctl -l # Should list audit rules
fail2ban-client status sshd # Should show active
```

---

## Execution Instructions

### Option 1: Interactive Execution (RECOMMENDED)
```bash
# On your local machine
ssh -t wizardsofts@10.0.0.84

# On the remote server
cd hardening
bash harden.sh 10.0.0.84 wizardsofts apply
# Enter password when prompted for sudo
```

**Advantages**: Secure, prompts for password, allows monitoring  
**Time**: ~30-45 minutes

### Option 2: Per-Phase Execution
Run each phase individually with password prompts:
```bash
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts apply
# [password prompt]
bash hardening/scripts/02_filesystem.sh 10.0.0.84 wizardsofts apply
# [password prompt]
# ... etc
```

**Advantages**: Fine-grained control, can pause between phases  
**Time**: ~45-60 minutes with pauses

### Option 3: NOPASSWD sudo (Less Secure)
If you need non-interactive execution:
```bash
# On server (requires initial password)
sudo visudo
# Add line: wizardsofts ALL=(ALL) NOPASSWD: ALL

# Then run (non-interactive)
bash hardening/harden.sh 10.0.0.84 wizardsofts apply
```

**Advantages**: Non-interactive, full automation  
**Disadvantages**: Less secure, requires NOPASSWD setting  
**⚠️ WARNING**: This should be reverted after implementation!

---

## Pre-Execution Checklist

- [ ] SSH key-based authentication configured for wizardsofts user
- [ ] User wizardsofts has sudo access
- [ ] At least 2GB free disk space (current: 64GB)
- [ ] System uptime stable (current: 25+ days)
- [ ] Backup of critical configs (automated in scripts)
- [ ] Network connectivity confirmed
- [ ] Have alternate SSH access method available (e.g., another server)

---

## Execution Flow

```
harden.sh (main orchestrator)
    ├─ 01_ssh_network.sh (SSH & UFW) ~5 min
    │   └─ Backup sshd_config, apply hardening, test SSH
    │
    ├─ 02_filesystem.sh (remount /tmp, etc) ~3 min
    │   └─ Remount filesystems, restrict permissions
    │
    ├─ 03_user_sudo.sh (Sudo & passwords) ~3 min
    │   └─ Install pwquality, set policies
    │
    ├─ 04_services_docker.sh (Disable services) ~5 min
    │   └─ Stop services, create daemon.json
    │
    ├─ 05_kernel.sh (Sysctl & modules) ~3 min
    │   └─ Apply kernel parameters, disable modules
    │
    └─ 06_security_tools.sh (Monitoring) ~10 min
        └─ Install fail2ban, auditd, configure logging
```

**Total Execution Time**: ~30-45 minutes

---

## Post-Execution Verification

After successful completion, run verification commands:

```bash
# Test SSH restrictions
ssh -v <external-ip> 10.0.0.84 -p 22 # Should timeout
ssh -v 10.0.0.80 10.0.0.84 -p 22     # Should connect

# Check filesystem
mount | grep tmp     # Should show noexec
ls -ld /opt/apps    # Should show 750

# Check services
systemctl status fail2ban     # Should be active
systemctl status auditd       # Should be active

# Check kernel hardening
sysctl net.ipv4.tcp_syncookies  # Should be 1
sysctl kernel.yama.ptrace_scope # Should be 2

# Check firewall
sudo ufw status numbered  # Should show SSH rule for 10.0.0.0/24
```

---

## Rollback Procedure

If issues occur, each phase supports rollback:

```bash
# Rollback all phases
bash hardening/harden.sh 10.0.0.84 wizardsofts rollback

# Rollback individual phase
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts rollback

# Manual rollback (if automatic fails)
sudo cp /etc/ssh/sshd_config.bak.* /etc/ssh/sshd_config
sudo systemctl restart ssh
```

**Note**: All original configs are backed up with `.bak.<timestamp>` suffix.

---

## Logs and Troubleshooting

### Log Files
- `hardening/logs/10.0.0.84_<timestamp>.log` - Full execution log
- `hardening/logs/10.0.0.84_progress_<timestamp>.json` - Phase progress
- `hardening/logs/apply_run.log` - Latest run output

### Common Issues

#### Issue: "sudo: a terminal is required to read the password"
**Cause**: Running without interactive SSH terminal  
**Solution**: Use `ssh -t` flag for interactive terminal

#### Issue: SSH connection refused after Phase 1
**Cause**: UFW rule not applied correctly or SSH key not configured  
**Solution**: 
```bash
# Access via alternate method or console
sudo ufw allow from 10.0.0.0/24 to any port 22
sudo systemctl restart ssh
```

#### Issue: /tmp remount fails
**Cause**: /tmp in use by processes  
**Solution**: Reboot system or close processes using /tmp, then retry

---

## Security Validation

### CIS Benchmark Alignment
The implementation follows CIS Ubuntu Linux 24.04 LTS Benchmark:
- ✓ Section 1: Initial Setup (filesystem, bootloader)
- ✓ Section 2: Services (disable unnecessary services)
- ✓ Section 3: Network (kernel parameters, firewall)
- ✓ Section 4: Logging and Auditing (auditd, fail2ban)
- ✓ Section 5: Access Control (sudo, file permissions)
- ✓ Section 6: System Maintenance (kernel hardening)

### Attack Surface Reduction
- **Network**: SSH restricted to 10.0.0.0/24, no other services exposed
- **Filesystem**: /tmp/var/tmp/dev/shm with noexec, prevents code execution
- **Access**: Sudo requires password, SSH keys only, no root login
- **Kernel**: Restricted ptrace, memory protection, module loading disabled
- **Monitoring**: Fail2Ban detects brute-force, auditd logs suspicious activity

---

## Success Criteria

✅ **Network Access**
- SSH accessible only from 10.0.0.0/24 subnet
- External SSH attempts timeout (no connection response)

✅ **File System**
- /tmp, /var/tmp, /dev/shm mounted with noexec flag
- /opt/apps has 750 permissions
- No unnecessary world-executable files

✅ **Access Control**
- SSH key-only authentication (password disabled)
- Sudo requires password, logs all commands
- Root cannot SSH in directly

✅ **Monitoring**
- Fail2Ban active and protecting SSH
- auditd running with rules loaded
- Logs centralized (optional)

✅ **Kernel**
- 30+ sysctl parameters applied
- Unnecessary modules disabled
- Kernel exploits mitigated

---

## Handoff Notes

**Status**: READY FOR EXECUTION  
**Infrastructure**: COMPLETE  
**Documentation**: COMPREHENSIVE  
**Testing**: PRE-FLIGHT CHECKS PASSED  

### What's Ready
- ✓ 6 atomic phase scripts (modular, idempotent)
- ✓ Inventory system for server configuration
- ✓ Comprehensive logging and progress tracking
- ✓ Rollback capabilities for all phases
- ✓ Detailed verification procedures

### What's Blocking Execution
- Password-protected sudo (normal security practice)
- Requires interactive SSH terminal or NOPASSWD configuration

### Recommendations
1. **Execute with Option 1** (Interactive) for maximum security
2. **Monitor logs** during execution for any errors
3. **Verify each phase** before proceeding to next (can add pauses)
4. **Keep rollback commands handy** in case of issues
5. **Test SSH access** from external IP after Phase 1 completes
6. **Document any deviations** from the plan

---

## Contact & Support

For issues or questions:
1. Check logs in `hardening/logs/`
2. Review the SERVER_HARDENING_PLAN_GMK.md for detailed context
3. Test individual phases if full execution fails
4. Rollback and retry if issues occur

---

**Last Updated**: 2025-12-19  
**Implementation Framework**: Bash + SSH  
**Total Tasks**: 14 atomic, independently verifiable tasks  
**Estimated Duration**: 30-45 minutes  
**Security Level**: CIS Benchmark Aligned, Defense-in-Depth

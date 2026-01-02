# Server Hardening Implementation Framework

## Overview

This directory contains a comprehensive, modular framework for hardening the GMK NucBox server (10.0.0.84). The implementation follows security best practices with atomic, independently-verifiable tasks, JSON progress tracking, and full rollback capabilities.

## Quick Start

### Execute Full Hardening (Recommended)
```bash
# Interactive execution (recommended for maximum transparency)
ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'

# When prompted, enter the password for user 'wizardsofts'
# Execution takes ~30-45 minutes for all 6 phases
```

### Alternative Execution Methods

**Per-Phase Execution:**
```bash
# Run one phase at a time
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts apply
bash hardening/scripts/02_filesystem.sh 10.0.0.84 wizardsofts apply
# ... continue for phases 03-06
```

**NOPASSWD Sudoers (Less Secure):**
```bash
# First time: provide password
ssh -t wizardsofts@10.0.0.84 'echo "wizardsofts ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers.d/hardening'

# Then run without password prompts
bash harden.sh 10.0.0.84 wizardsofts apply
```

## Directory Structure

```
hardening/
├── harden.sh                      # Main orchestrator (entry point)
├── HANDOFF.md                     # Comprehensive 450+ line guide
├── IMPLEMENTATION_STATUS.json     # Current status & tracking
├── README.md                      # This file
├── scripts/
│   ├── 01_ssh_network.sh         # Phase 1: SSH & Firewall (UFW)
│   ├── 02_filesystem.sh          # Phase 2: File system hardening
│   ├── 03_user_sudo.sh           # Phase 3: User & sudo hardening
│   ├── 04_services_docker.sh     # Phase 4: Services & Docker
│   ├── 05_kernel.sh              # Phase 5: Kernel parameters
│   └── 06_security_tools.sh      # Phase 6: Fail2Ban, auditd, logging
├── lib/
│   └── common.sh                 # Shared functions & utilities
├── inventory/
│   └── 10.0.0.84.json           # Server-specific configuration
└── logs/
    └── [execution logs & JSON progress tracking]
```

## Phases & Tasks

### Phase 1: SSH & Network (N1, N2)
- **N1**: Configure SSH for local subnet access only (10.0.0.0/24)
- **N2**: Setup UFW firewall with restrictive defaults
- **Time**: ~5 minutes

### Phase 2: File System (F1, F2)
- **F1**: Remount /tmp, /var/tmp, /dev/shm with noexec,nosuid,nodev
- **F2**: Restrict permissions on sensitive files
- **Time**: ~3 minutes

### Phase 3: User & Sudo (U1, U2)
- **U1**: Enforce sudo password requirement
- **U2**: Implement password policy (min length 12, max age 90 days)
- **Time**: ~2 minutes

### Phase 4: Services & Docker (S1, D1)
- **S1**: Disable unnecessary services (bluetooth, cups, avahi)
- **D1**: Harden Docker daemon configuration
- **Time**: ~5 minutes

### Phase 5: Kernel (K1, K2)
- **K1**: Apply 30+ sysctl security parameters
- **K2**: Blacklist uncommon kernel modules/filesystems
- **Time**: ~3 minutes

### Phase 6: Security Tools (T1, T2, T3)
- **T1**: Install & configure Fail2Ban (SSH brute-force protection)
- **T2**: Setup auditd system call auditing
- **T3**: Configure remote logging to centralized server
- **Time**: ~15 minutes

## Execution Modes

All scripts support three modes:

### 1. Apply (apply)
- Makes actual changes to the server
- Backs up original files (*.bak)
- Enables/restarts services
- Recommended for production deployment

### 2. Check (check)
- Validates current compliance status
- Shows what would change
- No changes made to system
- Safe for any environment

### 3. Rollback (rollback)
- Restores backups created during apply
- Reverts all changes from the phase
- Available only after apply has run
- Requires backup files (*.bak)

## Progress Tracking

Progress is tracked in JSON format at:
```
hardening/logs/10.0.0.84_progress_<timestamp>.json
```

Example structure:
```json
{
  "server_ip": "10.0.0.84",
  "start_time": "2024-12-19T15:48:27Z",
  "phases": {
    "phase_1": {
      "status": "SUCCESS",
      "start_time": "...",
      "end_time": "...",
      "duration_seconds": 45,
      "tasks": [
        {"task": "N1_ssh_subnet", "status": "SUCCESS"},
        {"task": "N2_ufw_firewall", "status": "SUCCESS"}
      ]
    }
  }
}
```

## Pre-Execution Checklist

Before running the hardening scripts:

- [ ] SSH connectivity verified: `ssh -o ConnectTimeout=5 wizardsofts@10.0.0.84 'echo OK'`
- [ ] Backup taken: `ssh wizardsofts@10.0.0.84 'sudo tar czf /tmp/pre_hardening_backup.tar.gz /etc'`
- [ ] Network documented: Current routing, DNS, firewall rules noted
- [ ] Access plan confirmed: Know how to access server if SSH changes break things
- [ ] Disk space verified: `ssh wizardsofts@10.0.0.84 'df -h /tmp /var/tmp'`
- [ ] Time synchronized: `ssh wizardsofts@10.0.0.84 'date'` matches local time within 5 seconds
- [ ] Service dependencies reviewed: Understand any services that might be affected

## Post-Execution Verification

### 1. Verify SSH Access Restriction
```bash
# From external network (should timeout/fail)
timeout 5 ssh -vv wizardsofts@10.0.0.84 2>&1 | grep -i "timed out\|refused"

# From local subnet (should connect)
ssh -o ConnectTimeout=5 wizardsofts@10.0.0.84 'echo SSH Access OK'
```

### 2. Verify Firewall Rules
```bash
ssh wizardsofts@10.0.0.84 'sudo ufw status | head -15'
```

### 3. Verify File System Mounts
```bash
ssh wizardsofts@10.0.0.84 'mount | grep -E "tmp|shm"'
```

### 4. Verify Security Tools
```bash
ssh wizardsofts@10.0.0.84 'sudo systemctl status fail2ban auditd'
```

### 5. Check Logs
```bash
ssh wizardsofts@10.0.0.84 'tail -20 /var/log/audit/audit.log'
```

## Rollback Procedures

### Full Rollback (All Phases)
```bash
for phase in 06 05 04 03 02 01; do
  bash hardening/scripts/${phase}_*.sh 10.0.0.84 wizardsofts rollback
done
```

### Rollback Single Phase
```bash
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts rollback
```

**Note**: Rollback is only available if backup files (*.bak) exist, which are created during `apply` mode.

## Troubleshooting

### "sudo: a terminal is required to read the password"
This is normal for non-interactive execution. Use one of these solutions:
- **Solution 1 (Recommended)**: Use `ssh -t` flag for interactive terminal
- **Solution 2**: Configure NOPASSWD in sudoers (less secure)
- **Solution 3**: Run per-phase with password prompts

### "SSH connection failed"
- Verify wizardsofts user exists and has SSH access
- Check SSH port is 22 (default assumed in scripts)
- Verify network connectivity: `ping 10.0.0.84`

### "Phase X failed, cannot continue"
- Check logs: `cat hardening/logs/10.0.0.84_*.log | tail -50`
- Review error message in JSON progress file
- Consider rolling back phase X: `bash scripts/0X_*.sh 10.0.0.84 wizardsofts rollback`
- Investigate specific error and re-run in `check` mode to diagnose

### "Rollback fails - backup files missing"
Backups are only created in `apply` mode. If files were modified manually or backups deleted:
- Review `/etc` backup: `ssh wizardsofts@10.0.0.84 'ls -la /tmp/pre_hardening_backup.tar.gz'`
- Manually restore from backup if available
- Contact system administrator if unsure

## Security Considerations

### Network Restrictions
The hardening restricts SSH to the local subnet (10.0.0.0/24). Access from external networks is blocked by UFW. To maintain access:
- **Internal**: Access from 10.0.0.1 - 10.0.0.254 works normally
- **External**: SSH traffic is dropped by UFW (firewall, not timeout)
- **Recovery**: Physical access or use trusted internal host to restore access

### Password Requirements
All scripts use sudo, which requires password authentication. This is intentional for security:
- **Apply Phase**: Interactive password prompt required
- **Check/Rollback**: May require password if elevated permissions needed
- **Solution**: Use `ssh -t` for interactive terminal (recommended)

### File Modifications
All changes create backups (*.bak) before modification:
- Original files backed up: `/etc/config -> /etc/config.bak`
- Rollback restores from *.bak files
- Do not manually delete *.bak files during deployment

## Verification Against CIS Benchmarks

This hardening framework aligns with CIS Benchmark recommendations:

| CIS Control | Implementation | Status |
|-------------|-----------------|--------|
| 1.1.1 | Disable cramfs | ✓ kernel.sh |
| 1.1.2 | Disable freevxfs | ✓ kernel.sh |
| 1.2.1 | Configure SSH timeout | ✓ ssh_network.sh |
| 1.2.2 | SSH key-based auth | ✓ ssh_network.sh |
| 1.3.1 | Restrict UFW | ✓ ssh_network.sh |
| 1.4.1 | /tmp noexec | ✓ filesystem.sh |
| 1.5.1 | Sudo password | ✓ user_sudo.sh |
| 1.6.1 | Kernel parameters | ✓ kernel.sh |

## Success Criteria

Hardening is considered successful when:

1. **All 6 phases complete** without FAILED status
2. **SSH access restricted** to local subnet (10.0.0.0/24)
3. **File systems hardened** with noexec on /tmp, /var/tmp, /dev/shm
4. **Password policies enforced** with min length 12, max age 90
5. **Services disabled**: bluetooth, cups, avahi stopped and disabled
6. **Docker hardened**: daemon.json configured with security settings
7. **Kernel hardened**: 30+ sysctl parameters applied
8. **Fail2Ban active**: SSH brute-force protection monitoring
9. **Auditd active**: System call auditing logging events
10. **Logs available**: Execution logs and JSON progress files generated

## Support & Documentation

- **Detailed Guide**: See [HANDOFF.md](HANDOFF.md) for comprehensive implementation guide
- **Status Tracking**: Check [IMPLEMENTATION_STATUS.json](IMPLEMENTATION_STATUS.json) for current progress
- **Server Config**: See [inventory/10.0.0.84.json](inventory/10.0.0.84.json) for server-specific settings
- **Script Documentation**: Each script includes inline comments explaining each step

## Architecture Notes

### Design Principles
- **Modular**: Each phase is independent and can be run separately
- **Atomic**: Each task is focused on a single security improvement
- **Testable**: All changes can be verified before and after apply
- **Recoverable**: All changes can be rolled back to pre-hardening state
- **Documented**: Extensive inline comments and external documentation

### Execution Flow
```
1. harden.sh (orchestrator)
   ↓
2. Pre-flight checks (SSH, disk, uptime)
   ↓
3. For each phase (01-06):
   ↓ Execute script with mode (apply/check/rollback)
   ↓ Log results to file and JSON
   ↓ Update progress tracking
   ↓ Continue on success, stop on failure
   ↓
4. Post-execution summary
   ↓
5. Generate logs and progress JSON
```

### Error Handling
- **Pre-flight validation**: SSH connectivity, disk space, system uptime
- **Phase-level error handling**: Each phase can fail independently
- **Graceful degradation**: Completion status per-task allows partial rollback
- **Comprehensive logging**: All actions logged with timestamps and status codes

## Next Steps

1. **Review** this README and HANDOFF.md
2. **Execute** with: `ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'`
3. **Monitor** execution via logs in hardening/logs/
4. **Verify** post-execution with verification commands above
5. **Document** any issues or customizations needed

---

**Last Updated**: 2024-12-19  
**Framework Version**: 1.0  
**Target Server**: GMK NucBox (10.0.0.84)  
**Status**: READY FOR DEPLOYMENT

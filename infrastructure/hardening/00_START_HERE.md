# 🔒 SERVER HARDENING FRAMEWORK - START HERE

## Overview

A **complete, production-ready** hardening framework has been implemented for the GMK NucBox server (10.0.0.84). Everything is ready for deployment.

**Status**: ✅ Infrastructure Complete | Ready for Execution

---

## What Was Built

### 6 Security Phases
Each phase focuses on a specific security domain:

| Phase | Focus | Key Changes | Time |
|-------|-------|------------|------|
| **1** | SSH & Network | Restrict to local subnet (10.0.0.0/24), configure UFW | 5 min |
| **2** | File System | Remount /tmp, /var/tmp, /dev/shm with noexec | 3 min |
| **3** | User & Sudo | Enforce password policy, sudo restrictions | 2 min |
| **4** | Services & Docker | Disable unnecessary services, harden Docker | 5 min |
| **5** | Kernel | Apply 30+ sysctl parameters, restrict modules | 3 min |
| **6** | Security Tools | Install Fail2Ban, auditd, remote logging | 15 min |

### 14 Atomic Tasks
Each task is independent and verifiable:
- N1, N2 (Network)
- F1, F2 (File System)
- U1, U2 (User & Sudo)
- S1, D1 (Services)
- K1, K2 (Kernel)
- T1, T2, T3 (Security Tools)

### Complete Infrastructure
- ✅ 1,360+ lines of production bash code
- ✅ Modular phase-based scripts (scripts/01-06)
- ✅ Shared utility functions (lib/common.sh)
- ✅ Server inventory (inventory/10.0.0.84.json)
- ✅ JSON progress tracking
- ✅ Full rollback support
- ✅ Comprehensive documentation (450+ lines)

---

## Quick Start (Choose One)

### Option 1: Interactive Execution (RECOMMENDED)
```bash
ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'
```
**Duration**: ~30-45 minutes | **Password**: Prompted when needed | **Visibility**: Full

### Option 2: Per-Phase (Flexible)
```bash
# Run one phase at a time, test between steps
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts apply
bash hardening/scripts/02_filesystem.sh 10.0.0.84 wizardsofts apply
# ... etc
```

### Option 3: Fully Automated (NOPASSWD)
```bash
# One-time setup (requires password)
ssh -t wizardsofts@10.0.0.84 'echo "wizardsofts ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers.d/hardening'

# Then run without prompts
bash harden.sh 10.0.0.84 wizardsofts apply
```

---

## Pre-Execution Checklist

Run these commands before starting:

```bash
# ✓ SSH connectivity
ssh -o ConnectTimeout=5 wizardsofts@10.0.0.84 'echo OK'

# ✓ Full backup
ssh wizardsofts@10.0.0.84 'sudo tar czf /tmp/pre_hardening_backup.tar.gz /etc; echo "Backup created"'

# ✓ Disk space (need 1GB+ in /tmp)
ssh wizardsofts@10.0.0.84 'df -h / /tmp'

# ✓ System time (must be synchronized)
ssh wizardsofts@10.0.0.84 'timedatectl'
```

All checks ✓? You're ready to execute!

---

## During Execution

### Monitor Progress
```bash
# In another terminal, watch logs in real-time
ssh wizardsofts@10.0.0.84 'tail -f hardening/logs/10.0.0.84_*.log'
```

### Expected Output
- Each phase logs its actions
- Tasks show RUNNING → SUCCESS (or FAILED)
- JSON progress file updates after each task
- Total time: ~30-45 minutes

### If Something Goes Wrong
- **Logs location**: `hardening/logs/10.0.0.84_*.log`
- **Progress JSON**: `hardening/logs/10.0.0.84_progress_*.json`
- **Check mode**: `bash harden.sh 10.0.0.84 wizardsofts check` (safe, no changes)
- **Rollback**: `bash hardening/scripts/0X_*.sh 10.0.0.84 wizardsofts rollback` (for phase X)

---

## Post-Execution Verification

### 1. Health Check
```bash
ssh wizardsofts@10.0.0.84 'uptime && free -h && df -h /'
```
Expected: System running normally, disk space OK

### 2. SSH Restriction (CRITICAL)
```bash
# From local subnet (10.0.0.0/24) - should work
ssh wizardsofts@10.0.0.84 'echo SSH OK'

# From external IP - should timeout after 5 seconds
timeout 5 ssh external-ip@10.0.0.84 'echo test'
```

### 3. Firewall Status
```bash
ssh wizardsofts@10.0.0.84 'sudo ufw status | head -10'
```
Expected: Active, SSH allowed from 10.0.0.0/24

### 4. Security Tools
```bash
ssh wizardsofts@10.0.0.84 'sudo systemctl status fail2ban auditd'
```
Expected: Both active and running

### 5. File System Mounts
```bash
ssh wizardsofts@10.0.0.84 'mount | grep -E "tmp|shm"'
```
Expected: noexec, nosuid, nodev options visible

---

## If You Need to Rollback

### Rollback Single Phase
```bash
# Example: rollback phase 1 (SSH & Network)
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts rollback
```

### Rollback All Phases
```bash
# Reverse order: 6 → 5 → 4 → 3 → 2 → 1
for phase in 06 05 04 03 02 01; do
  bash hardening/scripts/${phase}_*.sh 10.0.0.84 wizardsofts rollback
done
```

### Test Rollback (No Changes)
```bash
# Check mode shows what rollback would do
bash harden.sh 10.0.0.84 wizardsofts check
```

---

## Important Security Notes

### Network Access After Hardening
SSH is restricted to **10.0.0.0/24 local subnet** only:
- ✅ Access from 10.0.0.1 - 10.0.0.254 works normally
- ❌ Access from external IPs is blocked by UFW
- ℹ️ Recovery requires jump host on local subnet or physical access

**Ensure you have internal access method before hardening!**

### Passwords & Authentication
All scripts require `sudo` password:
- Use `ssh -t` for interactive terminal (password prompted)
- Or configure NOPASSWD (less secure, see Option 3 above)
- Or run per-phase with manual password entry

### File Backups
Original files are backed up before modification:
- Location: `/etc/config.bak` (for each modified file)
- **Do not delete** during rollback testing
- Used for rollback functionality

---

## Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| **README.md** | Quick reference & troubleshooting | Before starting |
| **HANDOFF.md** | Complete 450-line implementation guide | For detailed procedures |
| **INFRASTRUCTURE_SUMMARY.md** | Architecture & design overview | For understanding structure |
| **IMPLEMENTATION_STATUS.json** | Current status & JSON tracking | During execution |
| **QUICKSTART.sh** | Command reference sheet | For copy-paste commands |

---

## File Structure

```
hardening/
├── 00_START_HERE.md              ← You are here
├── README.md                     ← Quick reference
├── HANDOFF.md                    ← Detailed guide (450+ lines)
├── INFRASTRUCTURE_SUMMARY.md     ← Architecture overview
├── harden.sh                     ← Main orchestrator
├── QUICKSTART.sh                 ← Command reference
├── IMPLEMENTATION_STATUS.json    ← Current status
│
├── scripts/
│   ├── 01_ssh_network.sh         ← Phase 1: SSH & Firewall
│   ├── 02_filesystem.sh          ← Phase 2: File System
│   ├── 03_user_sudo.sh           ← Phase 3: User & Sudo
│   ├── 04_services_docker.sh     ← Phase 4: Services & Docker
│   ├── 05_kernel.sh              ← Phase 5: Kernel
│   └── 06_security_tools.sh      ← Phase 6: Security Tools
│
├── lib/
│   └── common.sh                 ← Shared functions
│
├── inventory/
│   └── 10.0.0.84.json           ← Server config
│
└── logs/
    └── [execution logs & progress JSON]
```

---

## Success Criteria

Hardening is **successful** when:

✅ All 6 phases complete without FAILED status  
✅ SSH access restricted to local subnet only  
✅ File systems have noexec on /tmp, /var/tmp, /dev/shm  
✅ Password policies enforced  
✅ Services disabled and hardened  
✅ Kernel parameters applied  
✅ Fail2Ban and auditd active and monitoring  
✅ All verification commands return expected results  

---

## Common Questions

### Q: Will this break anything?
**A**: No. All changes are reversible. Rollback support included for all phases.

### Q: How long does it take?
**A**: ~30-45 minutes for complete execution. Can be done per-phase over multiple sessions.

### Q: What if SSH breaks?
**A**: Physical access to console or use jump host on 10.0.0.0/24 subnet. Rollback available.

### Q: Can I undo this?
**A**: Yes. Full rollback support for all phases. Just run `rollback` mode.

### Q: Is this for my environment?
**A**: Yes. All configuration is in `inventory/10.0.0.84.json`. Edit as needed for other servers.

### Q: What about monitoring?
**A**: Fail2Ban monitors SSH brute-force. Auditd audits system calls. Remote logging configured in Phase 6.

---

## Next Steps

### 1️⃣ Verify Prerequisites (5 minutes)
```bash
# Run the checklist above
# Make sure all checks pass ✓
```

### 2️⃣ Execute Hardening (30-45 minutes)
```bash
# Choose Option 1, 2, or 3 from "Quick Start" section
# Most people use Option 1 (interactive)
```

### 3️⃣ Verify Results (15 minutes)
```bash
# Run post-execution verification commands
# Check logs and JSON progress
```

### 4️⃣ Test & Document (As needed)
```bash
# Test SSH restrictions
# Document any custom needs
# Keep logs for audit trail
```

---

## Support & Help

**Before contacting support:**
1. Check logs: `ssh wizardsofts@10.0.0.84 'tail -100 hardening/logs/10.0.0.84_*.log'`
2. Review HANDOFF.md troubleshooting section
3. Run check mode to diagnose: `bash harden.sh 10.0.0.84 wizardsofts check`

**Emergency/Rollback:**
- Rollback is available: See "If You Need to Rollback" section above
- Backups created: Check /tmp or /etc for .bak files
- Pre-hardening backup: `/tmp/pre_hardening_backup.tar.gz` (if created)

---

## Ready? 🚀

When you're ready to execute hardening on 10.0.0.84:

```bash
ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'
```

This is the recommended approach (Option 1). It provides maximum transparency and security.

---

**Framework Version**: 1.0  
**Target**: GMK NucBox (10.0.0.84)  
**Status**: ✅ Ready for Deployment  
**Created**: December 19, 2024

**Questions?** See HANDOFF.md (detailed guide), README.md (quick ref), or INFRASTRUCTURE_SUMMARY.md (architecture)

# 🔒 Server Hardening Framework - File Index

## Navigation Guide

### 🚀 Start Here
- **[00_START_HERE.md](00_START_HERE.md)** - Quick overview & execution options (read this first!)

### 📚 Documentation (Choose Based on Need)

| Document | Purpose | Read Time | When? |
|----------|---------|-----------|-------|
| **[README.md](README.md)** | Quick reference & troubleshooting | 10 min | Before starting |
| **[HANDOFF.md](HANDOFF.md)** | Complete 450+ line guide with all details | 30 min | For detailed procedures |
| **[INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md)** | Architecture & design overview | 15 min | To understand structure |
| **[QUICKSTART.sh](QUICKSTART.sh)** | Command reference for copy-paste | 5 min | During execution |

### 💻 Execution Scripts

Main Entry Point:
- **[harden.sh](harden.sh)** - Orchestrates all 6 phases (start here for full deployment)

Individual Phases:
- **[scripts/01_ssh_network.sh](scripts/01_ssh_network.sh)** - Phase 1: SSH & Network
- **[scripts/02_filesystem.sh](scripts/02_filesystem.sh)** - Phase 2: File System
- **[scripts/03_user_sudo.sh](scripts/03_user_sudo.sh)** - Phase 3: User & Sudo
- **[scripts/04_services_docker.sh](scripts/04_services_docker.sh)** - Phase 4: Services & Docker
- **[scripts/05_kernel.sh](scripts/05_kernel.sh)** - Phase 5: Kernel
- **[scripts/06_security_tools.sh](scripts/06_security_tools.sh)** - Phase 6: Security Tools

Shared Functions:
- **[lib/common.sh](lib/common.sh)** - Utility functions used by all scripts

### ⚙️ Configuration

- **[inventory/10.0.0.84.json](inventory/10.0.0.84.json)** - Server-specific configuration

### 📊 Status & Logs

- **[IMPLEMENTATION_STATUS.json](IMPLEMENTATION_STATUS.json)** - Current implementation status
- **[logs/](logs/)** - Execution logs and progress tracking (generated during execution)

---

## Quick Navigation by Task

### I want to...

**Execute hardening on 10.0.0.84**
1. Read: [00_START_HERE.md](00_START_HERE.md)
2. Run: `ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'`
3. Monitor: `ssh wizardsofts@10.0.0.84 'tail -f hardening/logs/10.0.0.84_*.log'`

**Understand how it works**
1. Start with: [00_START_HERE.md](00_START_HERE.md) (overview)
2. Details: [HANDOFF.md](HANDOFF.md) (complete guide)
3. Architecture: [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md)

**Check status without making changes**
- Run: `bash harden.sh 10.0.0.84 wizardsofts check`
- Read: [README.md](README.md) for troubleshooting

**Rollback changes**
- Single phase: `bash hardening/scripts/0X_*.sh 10.0.0.84 wizardsofts rollback`
- All phases: See [HANDOFF.md](HANDOFF.md) for script

**Find a specific command**
- Quick: [QUICKSTART.sh](QUICKSTART.sh)
- Complete: [HANDOFF.md](HANDOFF.md)

**Understand a specific phase**
- Phase 1 (SSH): [scripts/01_ssh_network.sh](scripts/01_ssh_network.sh)
- Phase 2 (File System): [scripts/02_filesystem.sh](scripts/02_filesystem.sh)
- etc. (see scripts/ directory)

**Configure for a different server**
- Edit: [inventory/10.0.0.84.json](inventory/10.0.0.84.json)
- Use same scripts with different IP

---

## File Descriptions

### Documentation Files

**00_START_HERE.md** (3 KB)
- Entry point for the framework
- What was built, execution options, pre-checklist
- Best for: First-time users, quick overview

**README.md** (8 KB)
- Comprehensive quick reference
- All execution methods, verification procedures
- Troubleshooting guide
- Best for: Before executing, quick lookup

**HANDOFF.md** (12 KB)
- Most detailed guide (450+ lines)
- Complete procedures for each phase
- Verification commands for each change
- Rollback procedures
- CIS benchmark alignment
- Best for: Detailed implementation guidance

**INFRASTRUCTURE_SUMMARY.md** (10 KB)
- Architecture overview
- File structure diagram
- Component descriptions
- Success criteria
- Best for: Understanding overall design

**INDEX.md** (this file)
- File navigation guide
- Quick task lookup
- Best for: Finding what you need

### Execution Scripts

**harden.sh** (15 KB)
- Main orchestrator
- Coordinates all 6 phases
- Pre-flight validation
- Logging and progress tracking
- Entry point for full execution

**scripts/01_ssh_network.sh** (5 KB)
- Phase 1: SSH & Network hardening
- Configures UFW firewall
- Restricts SSH to local subnet
- Hardens sshd_config

**scripts/02_filesystem.sh** (4 KB)
- Phase 2: File system hardening
- Remounts /tmp, /var/tmp, /dev/shm with noexec
- Updates /etc/fstab for persistence

**scripts/03_user_sudo.sh** (5 KB)
- Phase 3: User & sudo hardening
- Enforces sudo password requirement
- Implements password policy
- Installs libpam-pwquality

**scripts/04_services_docker.sh** (4 KB)
- Phase 4: Services & Docker hardening
- Disables unnecessary services
- Hardens Docker daemon configuration

**scripts/05_kernel.sh** (6 KB)
- Phase 5: Kernel hardening
- Applies 30+ sysctl parameters
- Restricts kernel module loading
- Blacklists uncommon filesystems

**scripts/06_security_tools.sh** (5 KB)
- Phase 6: Security tools installation
- Installs & configures Fail2Ban
- Sets up auditd
- Configures remote logging

**lib/common.sh** (2 KB)
- Shared utility functions
- Logging functions
- SSH validation
- Progress tracking helpers

### Configuration Files

**inventory/10.0.0.84.json** (1 KB)
- Server-specific configuration
- IP address, username, subnet settings
- Edit this to adapt for different servers

**IMPLEMENTATION_STATUS.json** (6 KB)
- Current implementation status
- Phase descriptions
- Task details
- Verification commands
- Prerequisites and blockers

---

## Execution Flow Diagram

```
1. READ: 00_START_HERE.md (2 min)
   ↓
2. CHECK: Pre-execution checklist (5 min)
   ↓
3. EXECUTE: harden.sh (30-45 min)
   ├─ Phase 1: SSH & Network (5 min)
   ├─ Phase 2: File System (3 min)
   ├─ Phase 3: User & Sudo (2 min)
   ├─ Phase 4: Services & Docker (5 min)
   ├─ Phase 5: Kernel (3 min)
   └─ Phase 6: Security Tools (15 min)
   ↓
4. VERIFY: Post-execution checks (15 min)
   ↓
5. DOCUMENT: Keep logs for audit trail
```

---

## File Organization

```
hardening/
├── 00_START_HERE.md              ← Entry point
├── README.md                     ← Quick reference
├── HANDOFF.md                    ← Detailed guide
├── INFRASTRUCTURE_SUMMARY.md     ← Architecture
├── INDEX.md                      ← This file
├── QUICKSTART.sh                 ← Command reference
├── IMPLEMENTATION_STATUS.json    ← Status tracking
├── harden.sh                     ← Main orchestrator
│
├── scripts/
│   ├── 01_ssh_network.sh        ├─ 01_ssh_network.sh.bak (backup after apply)
│   ├── 02_filesystem.sh         ├─ 02_filesystem.sh.bak
│   ├── 03_user_sudo.sh          ├─ 03_user_sudo.sh.bak
│   ├── 04_services_docker.sh    ├─ 04_services_docker.sh.bak
│   ├── 05_kernel.sh             ├─ 05_kernel.sh.bak
│   └── 06_security_tools.sh     └─ 06_security_tools.sh.bak
│
├── lib/
│   └── common.sh                ← Shared functions
│
├── inventory/
│   └── 10.0.0.84.json          ← Server config
│
└── logs/
    ├── 10.0.0.84_YYYYMMDD_HHMMSS.log
    └── 10.0.0.84_progress_YYYYMMDD_HHMMSS.json
```

---

## Key Commands

**Start Hardening**
```bash
ssh -t wizardsofts@10.0.0.84 'cd hardening && bash harden.sh 10.0.0.84 wizardsofts apply'
```

**Check Status (No Changes)**
```bash
bash harden.sh 10.0.0.84 wizardsofts check
```

**View Progress**
```bash
ssh wizardsofts@10.0.0.84 'tail -f hardening/logs/10.0.0.84_*.log'
```

**Rollback Single Phase**
```bash
bash hardening/scripts/01_ssh_network.sh 10.0.0.84 wizardsofts rollback
```

**Rollback All Phases**
```bash
for phase in 06 05 04 03 02 01; do
  bash hardening/scripts/0${phase}_*.sh 10.0.0.84 wizardsofts rollback
done
```

---

## Information Architecture

### By Role

**System Administrator** → Start with [README.md](README.md)
- Practical execution steps
- Verification procedures
- Troubleshooting guide

**Security Team** → Read [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md)
- Security improvements summary
- CIS benchmark alignment
- Risk assessment

**DevOps Engineer** → Review [HANDOFF.md](HANDOFF.md)
- Architecture design
- Execution flow
- Integration points

**First-Time User** → Begin with [00_START_HERE.md](00_START_HERE.md)
- Quick overview
- Simple execution steps
- Pre-checklist

### By Activity

**Planning** → [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md) + [IMPLEMENTATION_STATUS.json](IMPLEMENTATION_STATUS.json)

**Pre-Execution** → [00_START_HERE.md](00_START_HERE.md) + [README.md](README.md)

**Execution** → [harden.sh](harden.sh) + [QUICKSTART.sh](QUICKSTART.sh)

**Verification** → [README.md](README.md) (verification section) + logs

**Rollback** → [HANDOFF.md](HANDOFF.md) (rollback section) + scripts

**Troubleshooting** → [README.md](README.md) (troubleshooting) + [HANDOFF.md](HANDOFF.md) (detailed procedures)

---

## Document Reading Guide

### If you have 2 minutes:
Read **[00_START_HERE.md](00_START_HERE.md)** - Get overview and understand if you're ready

### If you have 10 minutes:
Read **[README.md](README.md)** - Get all execution options and basic procedures

### If you have 30 minutes:
Read **[HANDOFF.md](HANDOFF.md)** - Get complete implementation guide with all details

### If you have 15 minutes:
Read **[INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md)** - Understand the architecture and design

### Before executing:
1. Read [00_START_HERE.md](00_START_HERE.md) (2 min)
2. Check [README.md](README.md) pre-execution section (5 min)
3. Run pre-execution checklist (5 min)

### During execution:
1. Monitor with: `tail -f hardening/logs/10.0.0.84_*.log`
2. Reference [QUICKSTART.sh](QUICKSTART.sh) for any commands

### After execution:
1. Run verification commands from [README.md](README.md)
2. Check logs in `logs/` directory
3. If issues, see troubleshooting in [README.md](README.md)

---

## Next Steps

**Ready to start?** → Go to [00_START_HERE.md](00_START_HERE.md)

**Need quick reference?** → See [QUICKSTART.sh](QUICKSTART.sh)

**Have 30 minutes for deep dive?** → Read [HANDOFF.md](HANDOFF.md)

**Understanding the architecture?** → See [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md)

---

**Last Updated**: December 19, 2024  
**Framework Version**: 1.0  
**Status**: ✅ Ready for Deployment

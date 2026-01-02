# Server Security Audit - Reusable Script Documentation

## Overview

The server security audit system provides a reusable, comprehensive approach to scanning, hardening, and verifying server security. It consists of two scripts:

- **Master Script:** `hardening/scripts/server-security-audit.sh` - Full-featured audit orchestrator
- **Wrapper Script:** `audit-server.sh` - Quick access from workspace root

---

## Quick Start

### Option 1: From Workspace Root (Easiest)
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts/server-setup

# Load environment
source .env && source hardening/.env

# Run full audit (scan → fix → verify)
./audit-server.sh all

# Or specific action
./audit-server.sh scan
./audit-server.sh fix
./audit-server.sh verify
```

### Option 2: Direct Script
```bash
cd hardening/scripts

# Run with explicit parameters
./server-security-audit.sh all 10.0.0.84 wizardsofts

# Or let it load from .env
./server-security-audit.sh all
```

---

## Usage

### Basic Syntax
```bash
./audit-server.sh [ACTION] [TARGET_IP] [TARGET_USER]
```

### Actions

| Action | Description | Time |
|--------|-------------|------|
| `all` | Full cycle: scan → fix → verify | 30-40 min |
| `scan` | Vulnerability scan only | 5 min |
| `fix` | Hardening/remediation only | 15-20 min |
| `verify` | Verification only | 5 min |
| `help` | Show help message | - |

### Parameters

- **ACTION:** `all` (default), `scan`, `fix`, `verify`, or `help`
- **TARGET_IP:** Server IP address (default: from `.env` = `10.0.0.84`)
- **TARGET_USER:** SSH user (default: from `.env` = `wizardsofts`)

---

## Examples

### Full Audit with Environment Variables
```bash
source .env && source hardening/.env
./audit-server.sh all
```

### Full Audit with Explicit Parameters
```bash
./audit-server.sh all 10.0.0.84 wizardsofts
```

### Scan Only
```bash
./audit-server.sh scan
```

### Fix Only (After Review)
```bash
./audit-server.sh fix 10.0.0.84 wizardsofts
```

### Verify After Hardening
```bash
./audit-server.sh verify
```

### Help
```bash
./audit-server.sh help
```

---

## Output and Logs

### Log Locations

```
hardening/logs/
├── audit_sessions/
│   ├── all_20251219_174500.log           (current session)
│   ├── scan_20251219_170000.log
│   ├── fix_20251219_172000.log
│   └── verify_20251219_172000.log
│
├── audit_session_summary_*.md             (summary reports)
├── VULNERABILITY_REPORT_20251219.md       (detailed findings)
├── vulnerability_scans/
│   └── 10.0.0.84_vulnerability_scan_*.log (raw scan output)
│
└── *.log                                   (hardening logs)
```

### Viewing Logs

```bash
# View current session log
tail -100 hardening/logs/audit_sessions/all_*.log

# View all audit sessions
ls -lt hardening/logs/audit_sessions/

# Find specific action logs
grep -l "PHASE 1: VULNERABILITY SCAN" hardening/logs/audit_sessions/*.log

# View summary report
cat hardening/logs/audit_session_summary_*.md
```

---

## Scheduling Regular Audits

### Daily Scan
```bash
# Add to crontab
0 2 * * * cd /Users/mashfiqurrahman/Workspace/wizardsofts/server-setup && ./audit-server.sh scan >> /tmp/server_audit.log 2>&1
```

### Weekly Full Audit
```bash
# Every Sunday at 2 AM
0 2 * * 0 cd /Users/mashfiqurrahman/Workspace/wizardsofts/server-setup && source .env && source hardening/.env && ./audit-server.sh all >> /tmp/server_audit.log 2>&1
```

### Monthly Security Review
```bash
# First day of month at 2 AM
0 2 1 * * cd /Users/mashfiqurrahman/Workspace/wizardsofts/server-setup && source .env && source hardening/.env && ./audit-server.sh all >> /tmp/server_audit.log 2>&1
```

### Setting Up Cron

```bash
# Open crontab editor
crontab -e

# Add one of the above lines
# Save and exit (typically Ctrl+X, then Y for nano)

# Verify cron job
crontab -l
```

---

## Workflow Examples

### Complete Security Hardening Workflow

```bash
# Step 1: Load environment
source .env && source hardening/.env

# Step 2: Run full audit (includes scan, fix, and verify)
./audit-server.sh all

# Step 3: Review vulnerability report
cat hardening/logs/VULNERABILITY_REPORT_*.md

# Step 4: Check session log for any issues
tail -100 hardening/logs/audit_sessions/all_*.log

# Step 5: Verify server is still accessible
ssh wizardsofts@10.0.0.84 "echo 'Server is responsive'"
```

### Incremental Hardening Workflow

```bash
# Step 1: Scan first
./audit-server.sh scan 10.0.0.84 wizardsofts

# Step 2: Review vulnerability report
cat hardening/logs/VULNERABILITY_REPORT_*.md

# Step 3: Review detailed report
cat hardening/logs/vulnerability_scans/10.0.0.84_vulnerability_scan_*.log

# Step 4: Run hardening when ready
./audit-server.sh fix 10.0.0.84 wizardsofts

# Step 5: Verify changes
./audit-server.sh verify 10.0.0.84 wizardsofts

# Step 6: Re-scan to confirm improvements
./audit-server.sh scan 10.0.0.84 wizardsofts
```

### Ongoing Monitoring Workflow

```bash
# Weekly scan
for week in $(seq 1 52); do
  ./audit-server.sh scan
  sleep 604800  # 1 week
done
```

---

## Key Features

### Automated Orchestration
- Runs multiple security tools in sequence
- Automatically loads environment variables
- Handles errors gracefully
- Provides detailed progress reporting

### Comprehensive Logging
- Each session logged with timestamp
- Session summaries generated
- Multiple log levels (success, warning, error, info)
- Color-coded output for readability

### Flexible Execution
- Run full cycle or individual phases
- Works with environment variables or explicit parameters
- Supports different target servers
- Dry-run capability (verify phase)

### Detailed Reporting
- Session logs with full output
- Summary reports with key metrics
- Links to detailed vulnerability reports
- Navigation to related documentation

### Scheduling Support
- Designed for cron integration
- Timestamped logs prevent overwriting
- Suitable for CI/CD pipelines
- Can run unattended

---

## Troubleshooting

### Script Not Found
```bash
# Ensure you're in workspace directory
cd /Users/mashfiqurrahman/Workspace/wizardsofts/server-setup

# Verify scripts exist
ls -la audit-server.sh hardening/scripts/server-security-audit.sh
```

### Permission Denied
```bash
# Make scripts executable
chmod +x audit-server.sh
chmod +x hardening/scripts/server-security-audit.sh
```

### Environment Not Loaded
```bash
# Ensure you load environment before running
source .env && source hardening/.env

# Verify variables are set
echo $TARGET_IP $TARGET_USER
```

### SSH Connection Failed
```bash
# Check server connectivity
ping 10.0.0.84

# Test SSH manually
ssh -v wizardsofts@10.0.0.84 "echo 'test'"

# Check firewall
sudo ufw status
```

### Logs Not Found
```bash
# Verify audit logs directory exists
ls -la hardening/logs/audit_sessions/

# Create if missing
mkdir -p hardening/logs/audit_sessions
```

---

## Integration with Existing Tools

### With Hardening Framework
```bash
# The audit script uses existing tools:
# - hardening/harden.sh (Phase 2: Fix)
# - hardening/scripts/scan_vulnerabilities.sh (Phase 1: Scan)
# - hardening/scripts/06_security_tools.sh (Phase 3: Verify)

# So all existing hardening functionality remains available
```

### With Documentation
```bash
# Audit script works with:
# - VULNERABILITY_SCAN_SUMMARY.md
# - REMEDIATION_CHECKLIST.md
# - hardening/logs/VULNERABILITY_REPORT_20251219.md

# Generate new reports for each audit run
```

### With Version Control
```bash
# Add to .gitignore (already there):
.env
hardening/.env
hardening/logs/

# Audit logs are local only - not committed to repo
```

---

## Performance Metrics

| Phase | Duration | Automation |
|-------|----------|-----------|
| Scan | ~5 minutes | 100% |
| Fix | 15-20 minutes | 100% |
| Verify | ~5 minutes | 100% |
| **Full Audit** | **30-40 minutes** | **100%** |

---

## Best Practices

### Regular Scheduling
- **Daily:** Quick scan for new vulnerabilities
- **Weekly:** Full audit cycle
- **Monthly:** Detailed security review

### Before Running
- Load environment variables
- Verify server connectivity
- Have SSH password/keys ready
- Ensure sufficient disk space

### After Running
- Review generated reports
- Check session logs for errors
- Verify server is responsive
- Archive important logs
- Monitor for any issues in next 24 hours

### Documentation
- Keep audit session logs for compliance
- Document any manual changes
- Track remediation progress
- Review trends over time

---

## Advanced Usage

### Custom Server List
```bash
# Create a loop to audit multiple servers
for server in 10.0.0.84 10.0.0.85 10.0.0.86; do
  echo "Auditing $server..."
  ./audit-server.sh all "$server" wizardsofts
  sleep 300  # Wait 5 minutes between audits
done
```

### Conditional Execution
```bash
# Only run fix if scan finds issues
if ./audit-server.sh scan 10.0.0.84 wizardsofts; then
  ./audit-server.sh fix 10.0.0.84 wizardsofts
fi
```

### Pipeline Integration
```bash
# Run as part of CI/CD pipeline
#!/bin/bash
set -e
cd /workspace
source .env && source hardening/.env
./audit-server.sh all
# Archive logs
tar -czf audit_logs_$(date +%Y%m%d).tar.gz hardening/logs/audit_sessions/
```

---

## File Structure

```
server-setup/
├── audit-server.sh (wrapper - use this for quick access)
│
└── hardening/
    ├── scripts/
    │   ├── server-security-audit.sh (master orchestrator)
    │   ├── scan_vulnerabilities.sh (phase 1)
    │   ├── 06_security_tools.sh (phase 3)
    │   └── ...
    │
    ├── harden.sh (phase 2)
    │
    └── logs/
        ├── audit_sessions/ (all session logs)
        ├── vulnerability_scans/ (scan results)
        ├── audit_session_summary_*.md
        └── ...
```

---

## Support

### For Questions About
- **Vulnerabilities:** See `VULNERABILITY_REPORT_20251219.md`
- **Remediation:** See `REMEDIATION_CHECKLIST.md`
- **Script Usage:** Run `./audit-server.sh help`
- **Logs:** Check `hardening/logs/audit_sessions/`

---

**Version:** 1.0  
**Created:** December 19, 2025  
**Status:** Ready for Production  
**Automation Level:** 100%

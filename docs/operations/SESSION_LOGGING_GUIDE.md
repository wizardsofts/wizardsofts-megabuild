# Session Logging Guide

This guide contains detailed procedures for logging implementation sessions. For the shortened version, see AGENT.md Section 1.3.1.

---

## A. Command Logging (Server-Side)

```bash
# Start logging all commands to file
exec > >(tee -a /tmp/session-$(date +%Y%m%d-%H%M%S).log) 2>&1
set -x  # Enable command tracing

# Your implementation commands here
ssh agent@10.0.0.84 "docker logs gitlab --tail 50"

# Stop logging
set +x
```

---

## B. Implementation Action Log (Agent-Side)

Use this format to track implementation progress:

```markdown
## Implementation Log - YYYY-MM-DD HH:MM

### Action 1: [Description]

- Command: `ssh agent@10.0.0.84 "ufw allow 3002/tcp"`
- Output: Rule added
- Status: Success
- Duration: 2s

### Action 2: [Description]

- Command: `docker exec gitlab gitlab-backup create`
- Output: [First 5 lines of output]
- Status: Failed - Permission denied
- Error Analysis: NFS mount has root_squash, blocking UID 998 writes
- Resolution: Fixed /etc/exports, changed to no_root_squash
- Duration: 45min (including diagnosis)
```

---

## C. Server State Snapshots

Capture system state before/after major changes:

```bash
{
  echo "=== System State $(date) ==="
  echo "Docker containers:"
  docker ps -a
  echo "\nMounts:"
  mount | grep -E 'nfs|data'
  echo "\nFirewall:"
  ufw status numbered
  echo "\nRecent logs:"
  docker logs gitlab --tail 20 2>&1
} >> /tmp/system-state-$(date +%Y%m%d-%H%M%S).log
```

---

## D. Log Collection at Session End (MANDATORY)

```bash
# Collect all session artifacts and move to project
SESSION_NAME="2026-01-08-gitlab-hardening"  # Use date-task format
SESSION_DIR="docs/handoffs/${SESSION_NAME}"
mkdir -p "${SESSION_DIR}"

# Copy logs from /tmp
cp /tmp/impl-*/*.log "${SESSION_DIR}/"
cp /tmp/system-state-*.log "${SESSION_DIR}/"

# Create implementation log from notes
cat > "${SESSION_DIR}/implementation-log.md" << EOF
## Implementation Log - ${SESSION_NAME}

[Structured markdown from your implementation notes]
- Include all commands, outputs, and decisions
- Use format from Section B above
EOF

# Save command history
history 100 > "${SESSION_DIR}/command-history.txt"
```

---

## E. Session README Template

```bash
cat > "${SESSION_DIR}/README.md" << EOF
# Session: ${SESSION_NAME}
Date: $(date)
Status: COMPLETE

## Quick Summary
- Planned Effort: X minutes
- Actual Duration: Y hours
- Success Rate: XX%
- Major Blocker: [Description if any]

## Files
- README.md (this file) - Overview
- implementation-log.md - Detailed action log with all commands
- command-history.txt - Shell history

## Next Steps
[What remains after session]
EOF
```

---

## F. Document Storage Structure

**MANDATORY: All session artifacts MUST be saved to project folders, never left in /tmp**

```
docs/
├── handoffs/                           # Session-specific artifacts
│   └── YYYY-MM-DD-<task-name>/
│       ├── README.md                   # Session summary
│       ├── implementation-log.md       # Detailed action log
│       ├── command-history.txt         # Shell command history
│       └── *.log                       # Various logs
│
├── archive/                            # Historical records
│   └── retrospectives/
│       └── YYYY-MM-<task>.md           # Post-mortems
```

**Document Lifecycle:**

1. **During Implementation:** Create logs in /tmp for performance
2. **At Session End:** Move all artifacts to appropriate docs/ folder
3. **After Session:** Update relevant documentation with ground truth findings
4. **Periodic Cleanup:** Archive completed sessions older than 6 months

---

## G. Progress Log Format

```markdown
## Session YYYY-MM-DDTHH:MM:SSZ

### Accomplished
- Implemented feature X in service Y
- Added 5 unit tests, 2 integration tests

### Files Modified
- apps/ws-gateway/src/main/java/...
- docs/API.md

### Next Steps
1. Complete error handling for edge case Z
2. Add E2E tests for the new endpoint

### Blockers
- None / OR describe blocker with context

### Commits
- abc123: feat(gateway): add health endpoint
```

---

_Last Updated: 2026-01-08_
_See also: AGENT.md Section 1.3_

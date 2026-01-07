---
name: reflect-and-learn
description: Guided reflection process to capture learnings after errors, corrections, or discoveries
version: 1.0.0
created: 2026-01-07
updated: 2026-01-07
---

# Reflect and Learn

## When to Use

Invoke this skill when:
- You made an error and found the fix
- User corrected your approach
- You discovered an undocumented process
- You found a workaround for a known issue
- You completed a task with reusable patterns

## Procedure

### Step 1: Classify the Learning

First, determine what type of learning this is:

| Learning Type | Example | Storage Location |
|--------------|---------|------------------|
| **Error fix** | "Docker network issue requires host mode" | Memory: `troubleshooting-*.md` |
| **Process** | "Deployment requires specific order" | Skill or Memory: `process-*.md` |
| **Configuration** | "Service X needs env var Y" | Service AGENT.md |
| **Universal pattern** | "Always check callers before changing API" | Root AGENT.md |
| **Tool-specific** | "Claude needs explicit confirmation for deletions" | CLAUDE.md |

### Step 2: Analyze Impact

Ask yourself:
1. Is this specific to this project or universal?
2. Will other agents/sessions benefit from this?
3. Is this a one-time issue or likely to recur?

### Step 3: Choose Storage

```
┌─────────────────────────────────────────────────────┐
│  STORAGE DECISION TREE                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Project-specific?                                  │
│  ├── Yes → Serena Memory                           │
│  └── No ↓                                          │
│                                                     │
│  Service-specific?                                  │
│  ├── Yes → apps/<service>/AGENT.md                 │
│  └── No ↓                                          │
│                                                     │
│  Reusable procedure?                                │
│  ├── Yes → .claude/skills/<name>/SKILL.md          │
│  └── No ↓                                          │
│                                                     │
│  Universal pattern?                                 │
│  ├── Yes → /AGENT.md                               │
│  └── No → Maybe don't need to store (one-off)      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Step 4: Create/Update the Learning

**For Memory (Serena):**
```bash
# Use mcp__serena__write_memory with this template:
```

```markdown
# <Topic Name>

## Context
[When/why this knowledge is relevant]

## Problem
[What issue was encountered]

## Solution
[The fix, workaround, or process]

## Commands/Code
[Actual commands or code that works]

## Lessons Learned
- [Key insight 1]
- [Key insight 2]

## Related
- [Other memories, docs, or code references]

---
*Created: YYYY-MM-DD*
*Source: <session context>*
```

**For AGENT.md updates:**
- Find the appropriate section
- Add the new knowledge following existing format
- Update the changelog if significant

**For Skills:**
- Create new directory in `.claude/skills/<name>/`
- Use SKILL.md template from AGENT.md Section 4.5

### Step 5: Verify and Log

1. Read back the stored learning to confirm accuracy
2. Add to session progress:

```markdown
### Learnings This Session
- [Description]: Stored in [location]
```

## Verification

After running this skill:
- [ ] Learning is stored in appropriate location
- [ ] Content follows the correct template
- [ ] Session progress is updated with learning summary

## Examples

### Example 1: Error Fix → Memory

**Scenario:** Docker containers couldn't communicate over bridge network.

**Action:** Create memory `troubleshooting-docker-networking.md`:

```markdown
# Docker Networking - Host Mode Required

## Context
Distributed ML infrastructure on Server 84.

## Problem
Celery workers couldn't connect to Redis despite being on same Docker network.
Bridge networking unreliable on Server 84 (20+ Docker networks, complex state).

## Solution
Switch to host networking for all distributed ML services.

## Commands
```yaml
# In docker-compose.yml
services:
  celery-worker:
    network_mode: "host"
```

## Lessons Learned
- Bridge networking can fail silently
- Host networking is reliable for distributed computing
- Always use UFW to secure host-networked services

---
*Created: 2026-01-02*
*Source: Celery integration debugging session*
```

### Example 2: User Correction → AGENT.md Update

**Scenario:** User said "always investigate 2 levels deep before changing code."

**Action:** Update AGENT.md Section 2 with Code Investigation Protocol.

### Example 3: Process Discovery → Skill

**Scenario:** Learned multi-step process for database migrations.

**Action:** Create `.claude/skills/database-migration/SKILL.md` with procedure.

## Troubleshooting

**Not sure where to store?**
- Default to Memory (can always move later)
- Ask user if unclear

**Memory already exists?**
- Use `mcp__serena__edit_memory` to update
- Don't create duplicates

**AGENT.md getting too long?**
- Consider moving to service-specific AGENT.md
- Or create a skill if it's a procedure

## Changelog

- v1.0.0 (2026-01-07): Initial version

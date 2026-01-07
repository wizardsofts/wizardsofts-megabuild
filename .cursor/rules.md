# Cursor Rules - WizardSofts Megabuild

> **Imports:** [/AGENT.md](/AGENT.md) - All rules from AGENT.md apply first.

---

## Core Principles (from AGENT.md)

1. **TDD Workflow:** Write failing test → implement → refactor
2. **Single Task:** Work on ONE feature per session
3. **Code Investigation:** 2-level deep investigation before changes
4. **Behavior Change:** Stop & inform user before changing existing behavior
5. **Document Changes:** Update docs alongside code
6. **Security First:** Validate inputs, escape outputs, no hardcoded secrets
7. **Deletion Policy:** Always confirm before removing code/features
8. **Script-First:** Write scripts for repetitive operations

---

## Cursor-Specific Rules

### Chat Behavior

When responding to chat:
- Be concise and direct
- Show code changes with clear before/after
- Explain reasoning for non-obvious decisions
- Suggest tests alongside implementation

### Code Actions

**On file save:**
- Auto-format with prettier/eslint
- Auto-organize imports
- Remove unused imports

**On code generation:**
- Include type annotations
- Add JSDoc for public APIs
- Generate corresponding test file

### Composer Mode

When using Composer for multi-file changes:
1. Start with test file (TDD)
2. Then implementation file
3. Then documentation updates
4. Show git diff summary at end

### Agent Mode

When using Cursor Agent:
1. Read `claude-progress.txt` first
2. Work on ONE task at a time
3. Commit after each logical change
4. Update progress file before stopping

---

## Project Context

**Monorepo Structure:**
```
apps/           → Application code
packages/       → Shared libraries
infrastructure/ → DevOps configs
docs/           → Documentation
```

**Key Files:**
- `AGENT.md` - Universal agent instructions
- `CLAUDE.md` - Claude-specific additions
- `features.json` - Feature tracking
- `claude-progress.txt` - Session progress

---

## Service-Specific Overrides

Check `apps/<service>/AGENT.md` for service-specific rules that override defaults.

---

*See [/AGENT.md](/AGENT.md) for complete development lifecycle instructions.*

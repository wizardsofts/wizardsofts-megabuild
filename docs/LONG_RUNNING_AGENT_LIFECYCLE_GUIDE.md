# Long-Running Agent Task Lifecycle Guide

> **Source Analysis:** Based on [Anthropic's Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk), [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), and industry best practices from [LangGraph checkpointing](https://docs.langchain.com/oss/javascript/langgraph/durable-execution).

---

## Executive Summary

Long-running AI agents face a fundamental challenge: **discrete context windows with no memory between sessions**. This is analogous to engineers on different shifts without handoff documentation. This guide synthesizes Anthropic's research and industry best practices into actionable patterns for Claude Code.

### Key Insight

> "Even a frontier coding model like Opus 4.5 running in a loop across multiple context windows will fall short of building a production-quality web app if it's only given a high-level prompt."
> — Anthropic Engineering

---

## Table of Contents

1. [Core Architecture: Two-Agent Pattern](#1-core-architecture-two-agent-pattern)
2. [Task Lifecycle Phases](#2-task-lifecycle-phases)
3. [State Persistence Strategies](#3-state-persistence-strategies)
4. [Error Handling & Recovery](#4-error-handling--recovery)
5. [Verification & Validation](#5-verification--validation)
6. [Context Management](#6-context-management)
7. [Claude Code Extension Points](#7-claude-code-extension-points)
8. [Implementation Recommendations](#8-implementation-recommendations)
9. [Sources](#9-sources)

---

## 1. Core Architecture: Two-Agent Pattern

Anthropic's research identifies a two-agent architecture as optimal for long-running tasks:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INITIALIZER AGENT                            │
│  • Creates init.sh (environment setup)                             │
│  • Generates feature list (200+ features, all marked "failing")    │
│  • Establishes claude-progress.txt                                  │
│  • Creates initial git commits                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CODING AGENT (Loop)                         │
│  Session N:                                                         │
│  1. Read working directory + recent history                        │
│  2. Review feature list (JSON format)                              │
│  3. Select highest-priority incomplete feature                      │
│  4. Implement + test single feature                                │
│  5. Git commit with descriptive message                            │
│  6. Update progress documentation                                   │
│  └─► Repeat until all features complete                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Works

| Problem | Two-Agent Solution |
|---------|-------------------|
| Agent tries to "one-shot" the entire app | Initializer creates 200+ granular features |
| Premature "victory declaration" | Features stay "failing" until rigorously verified |
| Lost progress between sessions | Git commits + progress files persist state |
| Operational confusion | `init.sh` provides reproducible environment |

---

## 2. Task Lifecycle Phases

### Phase 1: Initialization (Once per project)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Read User   │───▶│   Expand     │───▶│   Create     │───▶│   Initial    │
│   Prompt     │    │  Features    │    │   Infra      │    │   Commit     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                           │                   │
                           ▼                   ▼
                    features.json         init.sh
                    (200+ items)          claude-progress.txt
```

### Phase 2: Session Startup (Every session)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Run init.sh │───▶│   Verify     │───▶│   Read Git   │───▶│   Load       │
│              │    │   App Works  │    │   Log        │    │   Progress   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Phase 3: Work Loop (Repeated)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Select     │───▶│  Implement   │───▶│    Test      │───▶│   Commit     │
│   Feature    │    │  Feature     │    │   Feature    │    │   Changes    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                                       │                    │
       │                                       ▼                    ▼
       │                              Update features.json   Update progress.txt
       │                              (mark complete)
       └──────────────────────────────────────────────────────────────┘
```

### Phase 4: Session Handoff (End of each session)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Document   │───▶│   Push       │───▶│   Summary    │
│   Progress   │    │   Commits    │    │   for Next   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. State Persistence Strategies

### 3.1 File-Based State (Recommended for Claude Code)

**Feature List (`features.json`):**
```json
{
  "project": "claude-clone",
  "version": "1.0.0",
  "features": [
    {
      "id": "auth-001",
      "name": "User login with email",
      "status": "failing",
      "priority": 1,
      "tests": ["test_login_valid", "test_login_invalid"],
      "completed_at": null
    },
    {
      "id": "auth-002",
      "name": "Password reset flow",
      "status": "failing",
      "priority": 2,
      "tests": ["test_reset_email", "test_reset_token"],
      "completed_at": null
    }
  ],
  "metadata": {
    "total": 200,
    "completed": 0,
    "in_progress": 0,
    "failing": 200
  }
}
```

**Progress Log (`claude-progress.txt`):**
```markdown
# Session Progress Log

## Session 2025-01-06T10:30:00Z
- Selected: auth-001 (User login with email)
- Changes: Created LoginForm.tsx, auth.service.ts
- Tests: All passing
- Commit: abc123 "feat(auth): implement email login"
- Next: auth-002 (Password reset flow)

## Session 2025-01-06T08:15:00Z
- Selected: setup-001 (Project initialization)
- Changes: Created Next.js scaffold, configured TypeScript
- Tests: Build passing
- Commit: def456 "chore: initial project setup"
```

### 3.2 Git-Based State

Git history provides:
- **Atomic checkpoints** at each feature completion
- **Rollback capability** if features break
- **Audit trail** of all changes
- **Branch isolation** for parallel work

```bash
# Recommended commit format
git commit -m "feat(module): implement feature-name

- Added ComponentX for functionality Y
- Updated ServiceZ to support feature
- Tests: all passing (5 new, 2 modified)

Closes: feature-id-001"
```

### 3.3 Checkpoint-Based State (Advanced)

For complex workflows, implement checkpointing similar to LangGraph:

```python
# Conceptual checkpoint structure
checkpoint = {
    "thread_id": "session-abc123",
    "step": 15,
    "state": {
        "current_feature": "auth-002",
        "completed_features": ["auth-001", "setup-001"],
        "environment": {"node_version": "20.x", "db_connected": True},
        "context_summary": "Working on password reset flow..."
    },
    "timestamp": "2025-01-06T10:30:00Z"
}
```

---

## 4. Error Handling & Recovery

### 4.1 Failure Patterns & Solutions

| Failure Pattern | Detection | Recovery Strategy |
|----------------|-----------|-------------------|
| **Over-ambitious scope** | Agent attempts multiple features | Enforce single-feature-per-session rule |
| **Broken inherited state** | Tests fail at session start | Rollback to last passing commit |
| **Premature completion** | Feature marked done but tests fail | Require verification before status change |
| **Context loss** | Agent repeats work or contradicts itself | Load progress file + git log at startup |
| **Environment drift** | `npm install` fails, dependencies conflict | Use `init.sh` for reproducible setup |

### 4.2 Recovery Workflow

```
┌─────────────────┐
│  Session Start  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Run Tests      │────▶│  Tests Pass?    │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼ YES                     ▼ NO
         ┌─────────────────┐      ┌─────────────────┐
         │  Continue Work  │      │  Identify Last  │
         └─────────────────┘      │  Passing Commit │
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │  Git Reset      │
                                  │  --hard <commit>│
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │  Re-implement   │
                                  │  Failed Feature │
                                  └─────────────────┘
```

### 4.3 Durable Execution Pattern

From [LangGraph best practices](https://docs.langchain.com/oss/javascript/langgraph/durable-execution):

```python
# Wrap side effects for deterministic replay
@task
def call_external_api(params):
    """
    Wrapped in @task decorator:
    - Result cached on first execution
    - On replay, returns cached result
    - Prevents duplicate API calls
    """
    return external_service.call(params)
```

---

## 5. Verification & Validation

### 5.1 Three-Layer Verification

Anthropic's research emphasizes verification as critical for long-running success:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      VERIFICATION LAYERS                            │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: Rules-Based                                               │
│  • Linters (ESLint, TypeScript)                                    │
│  • Unit tests                                                       │
│  • Type checking                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Visual/E2E                                                │
│  • Browser automation (Playwright MCP)                              │
│  • Screenshot comparison                                            │
│  • Responsive viewport testing                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: LLM-as-Judge                                              │
│  • Separate model evaluates output quality                         │
│  • Fuzzy criteria (tone, UX, completeness)                         │
│  • Human-like assessment                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Session Startup Verification Checklist

```markdown
## Session Startup Checklist

- [ ] Run `init.sh` - environment ready
- [ ] Run `npm test` (or equivalent) - all tests pass
- [ ] Start dev server - app loads correctly
- [ ] Read `git log --oneline -10` - understand recent changes
- [ ] Load `features.json` - identify next feature
- [ ] Load `claude-progress.txt` - understand context
```

### 5.3 Feature Completion Verification

```markdown
## Feature Completion Criteria

Feature can only be marked "complete" when:
- [ ] All unit tests pass
- [ ] E2E test passes (if applicable)
- [ ] TypeScript/linter checks pass
- [ ] Visual verification via screenshot
- [ ] Git commit created with descriptive message
- [ ] Progress file updated
- [ ] features.json status changed to "passing"
```

---

## 6. Context Management

### 6.1 Progressive Disclosure

From [Agent Skills documentation](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills):

```
Level 1: Always in Context
├── SKILL.md metadata (name, description)
├── CLAUDE.md project instructions
└── Current task brief

Level 2: Loaded on Demand
├── Full SKILL.md content
├── Reference documentation
└── Feature specifications

Level 3: Loaded When Needed
├── Code files being edited
├── Test files
└── External documentation
```

### 6.2 Context Window Optimization

| Strategy | When to Use | Impact |
|----------|-------------|--------|
| **JSON over Markdown** | Feature lists, structured data | Reduces ambiguity, saves tokens |
| **Subagents** | Large data processing, parallel tasks | Isolated context, focused execution |
| **Compaction** | Long-running sessions | Summarizes history, preserves essentials |
| **Agentic Search** | Large codebases | Loads only relevant files |

### 6.3 Effective Prompting Triggers

From [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices):

```
Thinking Budget Allocation:
"think"        → Standard analysis
"think hard"   → Extended analysis
"think harder" → Deep analysis
"ultrathink"   → Maximum computation
```

---

## 7. Claude Code Extension Points

Based on the research, here's how to implement these patterns in Claude Code:

### 7.1 CLAUDE.md Instructions

**What belongs here:**
- Project-specific rules that apply to ALL tasks
- Environment setup commands
- Code style guidelines
- Testing requirements
- Commit message format

**Example additions for long-running support:**

```markdown
## Long-Running Task Protocol

### Session Startup (MANDATORY)
1. Read `claude-progress.txt` if it exists
2. Check `git log --oneline -5` for recent context
3. Run test suite before making any changes
4. Load `features.json` to identify current work

### Feature Implementation Rules
- Work on ONE feature per session
- NEVER mark a feature complete without:
  - All tests passing
  - Visual verification (if UI)
  - Git commit created
- Update `claude-progress.txt` after EVERY commit

### Session Handoff
Before ending any session:
1. Commit all work in progress
2. Update `claude-progress.txt` with:
   - What was accomplished
   - What should happen next
   - Any blockers or concerns
```

### 7.2 Skills (SKILL.md)

Skills are ideal for **domain-specific procedures** that need progressive disclosure.

**Recommended Skills to Create:**

| Skill Name | Purpose | Key Files |
|------------|---------|-----------|
| `long-running-init` | Initialize long-running project structure | `SKILL.md`, `init-template.sh`, `features-template.json` |
| `session-handoff` | Standardize session transitions | `SKILL.md`, `handoff-checklist.md` |
| `feature-verification` | E2E testing workflow | `SKILL.md`, `playwright-tests/`, `verification-script.sh` |
| `progress-tracker` | Manage features.json and progress files | `SKILL.md`, `tracker.py` |

**Example Skill Structure:**

```
skills/
└── long-running-init/
    ├── SKILL.md
    ├── init-template.sh
    ├── features-template.json
    ├── progress-template.txt
    └── checklist.md
```

**SKILL.md Example:**

```markdown
---
name: long-running-init
description: Initialize project structure for long-running agent tasks with feature tracking, progress logging, and checkpoint infrastructure
---

# Long-Running Project Initialization

## When to Use
Invoke this skill when:
- Starting a new project that will span multiple sessions
- User mentions "long-running", "multi-session", or "large project"
- Project has 10+ features to implement

## Procedure
1. Create `init.sh` from template
2. Generate `features.json` with 50+ granular features
3. Create `claude-progress.txt` with session 0 entry
4. Make initial git commit
5. Run `init.sh` to verify environment

## Files
- `init-template.sh` - Environment setup script
- `features-template.json` - Feature tracking structure
- `checklist.md` - Verification checklist
```

### 7.3 Hooks

Hooks execute shell commands at specific lifecycle points. Ideal for **automated verification and state management**.

**Recommended Hooks:**

```json
// In Claude Code settings or .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "npm test --silent 2>/dev/null || echo 'TESTS_FAILING'"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "npm run lint --silent"
      }
    ],
    "SessionStart": [
      {
        "command": "[ -f init.sh ] && ./init.sh"
      },
      {
        "command": "[ -f claude-progress.txt ] && cat claude-progress.txt | tail -30"
      }
    ],
    "PreCommit": [
      {
        "command": "npm test && npm run lint"
      }
    ]
  }
}
```

**Hook Use Cases:**

| Hook Type | Use Case | Command Example |
|-----------|----------|-----------------|
| `SessionStart` | Load progress context | `cat claude-progress.txt \| tail -50` |
| `PreToolUse` | Prevent edits if tests failing | `npm test --silent` |
| `PostToolUse` | Auto-lint after edits | `npm run lint --fix` |
| `PreCommit` | Enforce verification | `npm test && npm run typecheck` |
| `SessionEnd` | Auto-update progress | `./scripts/update-progress.sh` |

### 7.4 MCP Plugins

MCP (Model Context Protocol) servers provide **tool integrations**. These are best for:
- Browser automation (verification)
- External API integrations
- Database access
- File system operations

**Recommended MCP Servers for Long-Running Tasks:**

| MCP Server | Purpose | Configuration |
|------------|---------|---------------|
| `@playwright/mcp` | E2E visual verification | `--headless` for automated testing |
| Custom `progress-tracker` | Manage features.json programmatically | Node.js server with CRUD operations |
| Custom `checkpoint-manager` | Save/restore session state | Persist to file or database |

**Example Custom MCP Server (`progress-tracker`):**

```javascript
// mcp-servers/progress-tracker/index.js
const { Server } = require('@modelcontextprotocol/sdk');

const server = new Server({
  name: 'progress-tracker',
  version: '1.0.0'
});

server.addTool({
  name: 'get_next_feature',
  description: 'Returns the highest priority incomplete feature',
  handler: async () => {
    const features = JSON.parse(fs.readFileSync('features.json'));
    const next = features.features
      .filter(f => f.status === 'failing')
      .sort((a, b) => a.priority - b.priority)[0];
    return next;
  }
});

server.addTool({
  name: 'mark_feature_complete',
  description: 'Mark a feature as complete after verification',
  parameters: {
    feature_id: { type: 'string', required: true },
    commit_hash: { type: 'string', required: true }
  },
  handler: async ({ feature_id, commit_hash }) => {
    const features = JSON.parse(fs.readFileSync('features.json'));
    const feature = features.features.find(f => f.id === feature_id);
    if (feature) {
      feature.status = 'passing';
      feature.completed_at = new Date().toISOString();
      feature.commit = commit_hash;
      features.metadata.completed++;
      features.metadata.failing--;
      fs.writeFileSync('features.json', JSON.stringify(features, null, 2));
    }
    return { success: true, feature };
  }
});

server.addTool({
  name: 'log_session_progress',
  description: 'Add entry to progress log',
  parameters: {
    feature_id: { type: 'string' },
    changes: { type: 'string' },
    commit: { type: 'string' },
    next_steps: { type: 'string' }
  },
  handler: async (params) => {
    const entry = `
## Session ${new Date().toISOString()}
- Feature: ${params.feature_id}
- Changes: ${params.changes}
- Commit: ${params.commit}
- Next: ${params.next_steps}
`;
    fs.appendFileSync('claude-progress.txt', entry);
    return { success: true };
  }
});

server.start();
```

---

## 8. Implementation Recommendations

### 8.1 Priority Matrix

| Priority | Component | Type | Effort | Impact |
|----------|-----------|------|--------|--------|
| **P0** | Session startup protocol in CLAUDE.md | Instruction | Low | High |
| **P0** | Progress file format (features.json + progress.txt) | Convention | Low | High |
| **P1** | `long-running-init` skill | Skill | Medium | High |
| **P1** | PreCommit verification hook | Hook | Low | Medium |
| **P2** | `progress-tracker` MCP server | Plugin | High | High |
| **P2** | Visual verification with Playwright | Skill + MCP | Medium | High |
| **P3** | Checkpoint/restore MCP server | Plugin | High | Medium |

### 8.2 Quick Start Implementation

**Step 1: Update CLAUDE.md (5 minutes)**

Add the "Long-Running Task Protocol" section from 7.1 above.

**Step 2: Create File Templates (10 minutes)**

```bash
# Create templates directory
mkdir -p .claude/templates

# features.json template
cat > .claude/templates/features.json << 'EOF'
{
  "project": "PROJECT_NAME",
  "version": "1.0.0",
  "features": [],
  "metadata": {
    "total": 0,
    "completed": 0,
    "in_progress": 0,
    "failing": 0
  }
}
EOF

# progress.txt template
cat > .claude/templates/claude-progress.txt << 'EOF'
# Project Progress Log

## Session 0 - Initialization
- Created project structure
- Generated feature list
- Environment: ready

---
EOF
```

**Step 3: Create Initialization Skill (30 minutes)**

```bash
mkdir -p .claude/skills/long-running-init
# Create SKILL.md and templates as shown in 7.2
```

**Step 4: Add Hooks (10 minutes)**

Configure hooks in Claude Code settings as shown in 7.3.

### 8.3 Validation Checklist

After implementation, verify:

- [ ] New sessions automatically load progress context
- [ ] Features are tracked in JSON with clear status
- [ ] Git commits happen after each feature completion
- [ ] Tests run before code changes are made
- [ ] Progress file is updated consistently
- [ ] Session handoff provides clear next steps

---

## 9. Sources

### Primary Sources (Anthropic Engineering)

1. **[Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)** - Core research on multi-session agent patterns
2. **[Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)** - Agent architecture and tool design
3. **[Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)** - Skills system documentation
4. **[Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)** - Prompting and workflow patterns

### Industry Resources

5. **[LangGraph Durable Execution](https://docs.langchain.com/oss/javascript/langgraph/durable-execution)** - Checkpoint and recovery patterns
6. **[Mastering LangGraph Checkpointing](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)** - Production checkpointing best practices
7. **[MongoDB Long-Term Memory for Agents](https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph)** - Persistent memory architectures
8. **[VentureBeat: Anthropic's Multi-Session Solution](https://venturebeat.com/ai/anthropic-says-it-solved-the-long-running-ai-agent-problem-with-a-new-multi)** - Industry analysis

### Related Reading

9. **[LangGraph Time Travel Debugging](https://dev.to/sreeni5018/debugging-non-deterministic-llm-agents-implementing-checkpoint-based-state-replay-with-langgraph-5171)** - State replay for debugging
10. **[ByteCheckpoint for LLM Development](https://arxiv.org/html/2407.20143v1)** - Academic research on checkpointing

---

## Appendix A: File Templates

### features.json (Full Example)

```json
{
  "project": "my-web-app",
  "version": "1.0.0",
  "created_at": "2025-01-06T10:00:00Z",
  "features": [
    {
      "id": "setup-001",
      "name": "Project initialization with Next.js 15",
      "description": "Create Next.js app with TypeScript, Tailwind, ESLint",
      "status": "passing",
      "priority": 1,
      "category": "setup",
      "tests": ["build:success"],
      "completed_at": "2025-01-06T10:30:00Z",
      "commit": "abc123"
    },
    {
      "id": "auth-001",
      "name": "User registration with email",
      "description": "Email/password registration with validation",
      "status": "failing",
      "priority": 2,
      "category": "authentication",
      "tests": ["test_register_valid", "test_register_duplicate", "test_register_invalid_email"],
      "completed_at": null,
      "commit": null
    },
    {
      "id": "auth-002",
      "name": "User login with email",
      "description": "Email/password login with session management",
      "status": "failing",
      "priority": 3,
      "category": "authentication",
      "tests": ["test_login_valid", "test_login_invalid", "test_login_locked"],
      "completed_at": null,
      "commit": null,
      "depends_on": ["auth-001"]
    }
  ],
  "metadata": {
    "total": 3,
    "completed": 1,
    "in_progress": 0,
    "failing": 2,
    "categories": ["setup", "authentication"]
  }
}
```

### init.sh (Full Example)

```bash
#!/bin/bash
set -e

echo "=== Long-Running Agent Environment Setup ==="

# Check Node.js version
required_node="20"
current_node=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$current_node" -lt "$required_node" ]; then
  echo "ERROR: Node.js $required_node+ required (found: $(node -v))"
  exit 1
fi
echo "✓ Node.js version: $(node -v)"

# Install dependencies
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm ci
fi
echo "✓ Dependencies installed"

# Run type check
echo "Running type check..."
npm run typecheck || { echo "ERROR: Type check failed"; exit 1; }
echo "✓ Type check passed"

# Run tests
echo "Running tests..."
npm test || { echo "ERROR: Tests failed"; exit 1; }
echo "✓ All tests passing"

# Start dev server (background, for verification)
echo "Starting dev server..."
npm run dev &
DEV_PID=$!
sleep 5

# Verify server is running
if curl -s http://localhost:3000 > /dev/null; then
  echo "✓ Dev server running at http://localhost:3000"
else
  echo "ERROR: Dev server failed to start"
  kill $DEV_PID 2>/dev/null
  exit 1
fi

# Kill background server
kill $DEV_PID 2>/dev/null

echo ""
echo "=== Environment Ready ==="
echo "Run 'npm run dev' to start development"
```

---

## Appendix B: Extension Point Summary

| Extension Point | Best For | Lifecycle Phase | Complexity |
|-----------------|----------|-----------------|------------|
| **CLAUDE.md** | Global rules, always-on instructions | All phases | Low |
| **Skills** | Domain procedures, templates, progressive disclosure | Initialization, specific tasks | Medium |
| **Hooks** | Automated checks, state updates | Pre/post actions, session boundaries | Low |
| **MCP Plugins** | Tool integrations, external systems, complex state | All phases | High |

---

*Document generated: 2025-01-06*
*Based on Anthropic Engineering research and industry best practices*

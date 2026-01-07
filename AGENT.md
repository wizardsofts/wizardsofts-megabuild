# Agent Instructions - WizardSofts Megabuild

> **Universal agent instructions for Claude Code, GitHub Copilot, Cursor, Windsurf, and any AI coding assistant.**

This document defines the complete software development lifecycle (SDLC) protocols for AI agents working on this monorepo.

---

## Table of Contents

1. [Session Lifecycle](#1-session-lifecycle)
2. [Code Investigation Protocol](#2-code-investigation-protocol)
3. [Behavior Change Protocol](#3-behavior-change-protocol)
4. [Reflection & Learning Protocol](#4-reflection--learning-protocol)
5. [Critical Operational Policies](#5-critical-operational-policies)
6. [Test-Driven Development (TDD)](#6-test-driven-development-tdd)
7. [Documentation Requirements](#7-documentation-requirements)
8. [Code Review Protocol](#8-code-review-protocol)
9. [Deployment & CI/CD](#9-deployment--cicd)
10. [Maintenance & Bug Fixes](#10-maintenance--bug-fixes)
11. [Monorepo Navigation](#11-monorepo-navigation)
12. [Service-Specific Instructions](#12-service-specific-instructions)
13. [Docker Deployment](#13-docker-deployment)

---

## 1. Session Lifecycle

### 1.1 Session Startup (MANDATORY)

Every session MUST begin with these steps:

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Load Context                                       │
│  □ Read claude-progress.txt (if exists)                     │
│  □ Read features.json (if exists)                           │
│  □ Run: git log --oneline -10                               │
│  □ Check: git status (any uncommitted work?)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Verify Environment                                 │
│  □ Run init.sh (if exists) OR npm install / mvn install    │
│  □ Run existing test suite: npm test / mvn test            │
│  □ Verify build passes: npm run build / mvn compile        │
│  □ If tests fail → FIX FIRST before new work               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Identify Work                                      │
│  □ Load features.json → find highest priority "failing"    │
│  □ OR check GitHub/GitLab issues assigned                   │
│  □ Select EXACTLY ONE task for this session                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Session Work Rules

| Rule                 | Description                              | Enforcement                                     |
| -------------------- | ---------------------------------------- | ----------------------------------------------- |
| **Single Task**      | Work on ONE feature/bug per session      | Never start second task until first is complete |
| **Commit Often**     | Commit after each logical change         | Minimum 1 commit per 30 minutes of work         |
| **Test First**       | Write/update tests before implementation | TDD workflow (see Section 2)                    |
| **Document Changes** | Update docs alongside code               | No PR without updated docs                      |

### 1.3 Session Handoff (MANDATORY)

Before ending ANY session:

```markdown
## Session Handoff Checklist

- [ ] All changes committed with descriptive messages
- [ ] Tests written and passing
- [ ] Documentation updated (if applicable)
- [ ] claude-progress.txt updated with:
  - What was accomplished
  - What should happen next
  - Any blockers or concerns
  - Files modified (for quick reference)
- [ ] features.json status updated (if applicable)
- [ ] Changes pushed to remote branch
```

**Progress Log Format:**

```markdown
## Session YYYY-MM-DDTHH:MM:SSZ

### Accomplished

- Implemented feature X in service Y
- Added 5 unit tests, 2 integration tests
- Updated API documentation

### Files Modified

- apps/ws-gateway/src/main/java/...
- apps/ws-gateway/src/test/java/...
- docs/API.md

### Next Steps

1. Complete error handling for edge case Z
2. Add E2E tests for the new endpoint
3. Update Postman collection

### Blockers

- None / OR describe blocker with context

### Commits

- abc123: feat(gateway): add health endpoint
- def456: test(gateway): add health endpoint tests
```

---

## 2. Code Investigation Protocol

### 2.1 MANDATORY: Deep Investigation Before Any Change

**BEFORE modifying, utilizing, or removing ANY code, you MUST investigate:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INVESTIGATION DEPTH: 2 LEVELS MINIMUM                                      │
│                                                                             │
│  Level 0: Target Code                                                       │
│  └── The function/class/method you plan to change                          │
│                                                                             │
│  Level 1: Direct Dependencies (MANDATORY)                                   │
│  ├── What does this code call? (callees)                                   │
│  ├── What calls this code? (callers)                                       │
│  ├── What tests cover this code?                                           │
│  └── What documentation references this code?                              │
│                                                                             │
│  Level 2: Indirect Dependencies (MANDATORY)                                 │
│  ├── What do Level 1 callees call?                                         │
│  ├── What calls Level 1 callers?                                           │
│  ├── What integration/E2E tests exercise this path?                        │
│  └── What API contracts depend on this behavior?                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Investigation Checklist

**For EVERY code change, complete this checklist:**

```markdown
## Investigation Report for: <function/class/file>

### Level 0: Target Analysis

- [ ] Read and understand the target code completely
- [ ] Identify the public API/interface
- [ ] Note any side effects (DB writes, API calls, file I/O)

### Level 1: Direct Dependencies

- [ ] **Callers**: Who calls this code?
  - List: file:line for each caller
  - Count: N callers found
- [ ] **Callees**: What does this code call?
  - List: external functions/services called
  - Note: Any I/O operations, DB queries, API calls
- [ ] **Unit Tests**: What tests cover this?
  - Files: list test files
  - Coverage: X% of lines covered
  - Missing: Note untested paths
- [ ] **Documentation**: Where is this documented?
  - API docs: link
  - README: link
  - Comments: inline or missing

### Level 2: Indirect Dependencies

- [ ] **Caller's Callers**: What calls the callers?
  - Impact radius: N files/functions affected
- [ ] **Callee's Callees**: What do dependencies depend on?
  - External services: list
  - Database tables: list
- [ ] **Integration Tests**: What integration tests exercise this?
  - Files: list
  - Scenarios covered: list
- [ ] **E2E Tests**: What E2E tests include this code path?
  - Files: list
  - User flows affected: list
- [ ] **API Contracts**: What contracts depend on this?
  - OpenAPI specs: list endpoints
  - Consumer services: list
```

### 2.3 Investigation Commands

**Finding Callers (Who uses this code?):**

```bash
# Find all references to a function/class
grep -rn "functionName" --include="*.ts" --include="*.java" --include="*.py"

# Find imports of a module
grep -rn "from module import" --include="*.py"
grep -rn "import { X } from" --include="*.ts"

# Find usages in tests
grep -rn "functionName" --include="*.test.ts" --include="*Test.java" --include="test_*.py"
```

**Finding Callees (What does this code use?):**

```bash
# Analyze imports in the file
head -50 <file>  # Check imports at top

# For Java: Find method calls
grep -n "this\." <file> | head -20
grep -n "\." <file> | grep -v "//" | head -30
```

**Finding Tests:**

```bash
# Find test files for a component
find . -name "*ComponentName*test*" -o -name "*ComponentName*Test*" -o -name "test_*ComponentName*"

# Check test coverage report
open coverage/lcov-report/index.html  # JavaScript
open target/site/jacoco/index.html    # Java
```

**Finding Documentation:**

```bash
# Search docs folder
grep -rn "functionName\|ClassName" docs/

# Search for JSDoc/JavaDoc
grep -B5 "functionName" --include="*.ts" --include="*.java" | grep -E "@|/\*\*"

# Search OpenAPI specs
grep -rn "operationId.*functionName" --include="*.yaml" --include="*.json"
```

### 2.4 Investigation Output Template

**Present findings to yourself (and user if behavior change) in this format:**

```markdown
## Code Investigation: <target>

### Target Summary

- **Location**: `apps/service/src/path/File.ts:lineNumber`
- **Type**: Function / Class / Method / API Endpoint
- **Purpose**: Brief description of what it does
- **Side Effects**: DB writes, API calls, file I/O, etc.

### Dependency Map
```

                    ┌─────────────────┐
                    │   Caller A      │ (apps/x/y.ts:10)
                    │   Caller B      │ (apps/x/z.ts:25)
                    └────────┬────────┘
                             │ calls
                             ▼

┌────────────────────────────────────────────────────────────┐
│ TARGET CODE │
│ functionName(params) → returnType │
│ Location: apps/service/src/path/File.ts:50 │
└────────────────────────────────────────────────────────────┘
│ calls
▼
┌─────────────────┐
│ Callee X │ (database query)
│ Callee Y │ (external API)
└─────────────────┘

```

### Test Coverage
| Test Type | Files | Coverage | Status |
|-----------|-------|----------|--------|
| Unit | `File.test.ts` | 85% | ✅ |
| Integration | `File.integration.test.ts` | 60% | ⚠️ |
| E2E | `user-flow.e2e.ts` | Path covered | ✅ |

### Documentation Found
- API Docs: `docs/api/endpoint.md`
- README: `apps/service/README.md#section`
- Inline: JSDoc present at line 48

### Impact Assessment
- **Direct Impact**: 3 callers will be affected
- **Indirect Impact**: 2 services depend on callers
- **Test Impact**: 5 tests will need updates
- **Doc Impact**: 2 docs need updates
```

---

## 3. Behavior Change Protocol

### 3.1 MANDATORY: Stop and Inform Before Changing Behavior

**When ANY of these conditions apply, you MUST STOP and inform the user:**

| Condition                              | Action Required    |
| -------------------------------------- | ------------------ |
| Changing existing function behavior    | STOP → Inform user |
| Modifying API response format          | STOP → Inform user |
| Removing code/features                 | STOP → Inform user |
| Changing database schema               | STOP → Inform user |
| Modifying authentication/authorization | STOP → Inform user |
| Changing error handling behavior       | STOP → Inform user |
| Deprecating public APIs                | STOP → Inform user |
| Changing default values                | STOP → Inform user |

### 3.2 Behavior Change Report Format

**When stopping to inform user, use this exact format:**

```markdown
## ⚠️ BEHAVIOR CHANGE DETECTED

### What I Plan to Change

**Target**: `functionName` in `apps/service/src/path/File.ts:50`
**Current Behavior**: [Describe exactly what it does now]
**Proposed Behavior**: [Describe what it will do after change]

### Why This Change is Needed

- Reason 1: [Explain why]
- Reason 2: [Explain why]

### Impact Analysis

#### Code Impact

| Affected | Location          | Change Required        |
| -------- | ----------------- | ---------------------- |
| Caller A | `apps/x/y.ts:10`  | Update call signature  |
| Caller B | `apps/x/z.ts:25`  | Handle new return type |
| Test X   | `File.test.ts:30` | Update assertions      |

#### User-Facing Impact

- [ ] API response format changes (breaking change for clients)
- [ ] UI behavior changes (users will notice)
- [ ] Performance impact (faster/slower)
- [ ] Data format changes (migration needed)

#### Backward Compatibility

- **Breaking Change?**: Yes / No
- **Migration Required?**: Yes / No
- **Deprecation Period?**: Recommended if breaking

### Options for User

**Option A: Make the change (Recommended)**

- Pros: [List benefits]
- Cons: [List drawbacks]
- Effort: [Low/Medium/High]

**Option B: Alternative approach**

- Description: [Describe alternative]
- Pros: [List benefits]
- Cons: [List drawbacks]
- Effort: [Low/Medium/High]

**Option C: Don't change**

- Description: Keep current behavior
- Pros: No risk, no effort
- Cons: [Why the change was proposed]

### My Recommendation

[Option X] because [brief justification]

---

**Please confirm which option to proceed with, or provide alternative direction.**
```

### 3.3 Removal/Deletion Protocol

**CRITICAL: Extra scrutiny required for removals.**

```markdown
## ⛔ REMOVAL IMPACT ANALYSIS

### What Will Be Removed

- **Target**: `ComponentName` / `functionName` / `FeatureX`
- **Location**: `apps/service/src/path/`
- **Type**: Function / Class / File / Feature / Service

### Current Usage

#### Direct Usage (Level 1)

| Caller     | Location          | How It's Used           |
| ---------- | ----------------- | ----------------------- |
| ServiceA   | `apps/a/x.ts:10`  | Calls function directly |
| ComponentB | `apps/b/y.tsx:25` | Imports and renders     |

#### Indirect Usage (Level 2)

| Dependent   | Through               | Impact          |
| ----------- | --------------------- | --------------- |
| PageX       | → ServiceA → Target   | Page will break |
| APIEndpoint | → ComponentB → Target | API will fail   |

### Test Coverage Being Removed

| Test File          | Tests Removed | Coverage Lost      |
| ------------------ | ------------- | ------------------ |
| `Target.test.ts`   | 15 tests      | 100% of target     |
| `ServiceA.test.ts` | 3 tests       | Tests using target |

### Documentation Being Removed

- `docs/api/target.md` - Will become invalid
- `README.md#target-section` - References removed code

### Breaking Changes

- [ ] API endpoint removed (clients will get 404)
- [ ] Function removed (TypeScript/compile errors)
- [ ] Database table/column removed (data migration needed)
- [ ] UI component removed (users will see error)

### Alternatives to Removal

**Option A: Remove completely**

- Impact: [Describe full impact]
- Migration: [What users/code need to do]

**Option B: Deprecate first**

- Add deprecation warning
- Keep functional for N releases
- Remove in version X.Y.Z

**Option C: Keep but refactor**

- Don't remove, but [alternative approach]

### Files That Will Be Modified/Deleted
```

DELETE: apps/service/src/path/Target.ts
DELETE: apps/service/src/path/Target.test.ts
MODIFY: apps/service/src/index.ts (remove export)
MODIFY: apps/other/ServiceA.ts (remove import/usage)
MODIFY: docs/api/target.md (delete or redirect)

```

---

**⚠️ WAITING FOR USER CONFIRMATION**

Please confirm:
1. Which option to proceed with (A/B/C)
2. Any additional concerns to address
3. Timeline for deprecation (if Option B)
```

### 3.4 Examples of When to STOP

**STOP and inform user:**

```typescript
// BEFORE: Function returns string
function getUserName(id: string): string {
  return db.users.find(id).name;
}

// PROPOSED: Change return type to object
function getUserName(id: string): { name: string; displayName: string } {
  // ⚠️ STOP! This changes return type - inform user first
}
```

```typescript
// BEFORE: Default timeout is 5000ms
const DEFAULT_TIMEOUT = 5000;

// PROPOSED: Change default to 10000ms
const DEFAULT_TIMEOUT = 10000;
// ⚠️ STOP! This changes default behavior - inform user first
```

```typescript
// BEFORE: Error throws exception
if (!valid) {
  throw new ValidationError("Invalid input");
}

// PROPOSED: Error returns null instead
if (!valid) {
  return null;
}
// ⚠️ STOP! This changes error handling - inform user first
```

**DO NOT STOP (safe changes):**

```typescript
// Safe: Adding new optional parameter with default
function process(data: Data, options?: Options) {}

// Safe: Internal refactoring that doesn't change behavior
// (but DO verify with tests first)

// Safe: Adding new function that doesn't modify existing ones
function newFeature() {}

// Safe: Improving performance without changing inputs/outputs
// (but DO verify with tests first)
```

### 3.5 Quick Decision Flowchart

```
                    ┌─────────────────────────┐
                    │  Planning to modify     │
                    │  existing code?         │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Does it change:      │
                    │  • Return type?       │
                    │  • Parameters?        │
                    │  • Side effects?      │
                    │  • Default behavior?  │
                    │  • Error handling?    │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │ YES                               │ NO
              ▼                                   ▼
    ┌─────────────────────┐           ┌─────────────────────┐
    │  ⚠️ STOP            │           │  Continue with      │
    │  Inform user        │           │  investigation +    │
    │  Present options    │           │  TDD workflow       │
    │  Wait for approval  │           │                     │
    └─────────────────────┘           └─────────────────────┘
```

---

## 4. Reflection & Learning Protocol

### 4.1 When to Reflect and Learn

**MANDATORY reflection triggers - After ANY of these events:**

| Trigger Event                    | Reflection Required          | Learning Action                   |
| -------------------------------- | ---------------------------- | --------------------------------- |
| **Error/Mistake Made**           | Analyze root cause           | Create/update memory with fix     |
| **New Process Discovered**       | Document the process         | Create skill or update AGENT.md   |
| **Configuration Found**          | Note environment details     | Update service AGENT.md or memory |
| **Workaround Applied**           | Document why and how         | Create troubleshooting memory     |
| **User Correction**              | Understand what was wrong    | Update relevant instruction file  |
| **Task Completed Successfully**  | Capture reusable patterns    | Update skills if generalizable    |
| **External API/Service Learned** | Document integration details | Create integration memory         |

### 4.2 Reflection Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REFLECTION WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DETECT (Automatic)                                                      │
│     ├── Error occurred during task? → REFLECT                               │
│     ├── User corrected my approach? → REFLECT                               │
│     ├── Discovered undocumented process? → REFLECT                          │
│     ├── Found better way to do something? → REFLECT                         │
│     └── Task succeeded with reusable pattern? → REFLECT                     │
│                                                                             │
│  2. ANALYZE                                                                 │
│     ├── What happened?                                                      │
│     ├── Why did it happen?                                                  │
│     ├── What should have happened?                                          │
│     ├── Is this specific to this task or generalizable?                     │
│     └── Who else might benefit from this knowledge?                         │
│                                                                             │
│  3. DECIDE WHERE TO STORE                                                   │
│     ├── Project-specific? → Memory (Serena)                                 │
│     ├── Service-specific? → apps/<service>/AGENT.md                         │
│     ├── Universal pattern? → /AGENT.md                                      │
│     ├── Reusable procedure? → Skill (.claude/skills/)                       │
│     └── Troubleshooting? → Memory with "troubleshooting-" prefix            │
│                                                                             │
│  4. STORE THE LEARNING                                                      │
│     ├── Create/update memory file                                           │
│     ├── Update AGENT.md (service or root)                                   │
│     ├── Create/update skill                                                 │
│     └── Update CLAUDE.md if Claude-specific                                 │
│                                                                             │
│  5. VERIFY                                                                  │
│     ├── Read back the stored learning                                       │
│     ├── Confirm it captures the insight correctly                           │
│     └── Note in session progress: "Learned: <summary>"                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Learning Storage Locations

| Type of Learning               | Storage Location                                      | Format                       | Access                     |
| ------------------------------ | ----------------------------------------------------- | ---------------------------- | -------------------------- |
| **Project-specific knowledge** | Serena Memory                                         | `<topic>.md`                 | `mcp__serena__read_memory` |
| **Troubleshooting guides**     | Serena Memory                                         | `troubleshooting-<topic>.md` | `mcp__serena__read_memory` |
| **Service configuration**      | `apps/<service>/AGENT.md`                             | Markdown                     | Auto-loaded                |
| **Universal patterns**         | `/AGENT.md`                                           | Markdown                     | Auto-loaded                |
| **Reusable procedures**        | `.claude/skills/<name>/SKILL.md`                      | Skill format                 | Invoked by user            |
| **Claude-specific**            | `/CLAUDE.md`                                          | Markdown                     | Auto-loaded                |
| **Tool-specific**              | `.github/copilot-instructions.md`, `.cursor/rules.md` | Markdown                     | Tool-specific              |

### 4.4 Memory Management (Serena MCP)

**Creating a Memory:**

```markdown
## When to Create a Memory

Create a new memory when you learn:

- How to troubleshoot a specific issue
- Configuration details for a service/integration
- Workarounds for known problems
- Project-specific conventions not in AGENT.md
- External API quirks or undocumented behavior
```

**Memory Naming Convention:**

```
<category>-<topic>.md

Categories:
- troubleshooting-*  → Problem/solution pairs
- config-*           → Configuration details
- integration-*      → External service integration
- process-*          → Learned processes/workflows
- architecture-*     → System design knowledge
```

**Memory Template:**

````markdown
# <Topic Name>

## Context

When/why this knowledge is relevant.

## Problem

What issue was encountered (if troubleshooting).

## Solution

The fix, workaround, or process.

## Commands/Code

```bash
# Actual commands or code that works
```
````

## Lessons Learned

- Key insight 1
- Key insight 2

## Related

- Other memories: <name>
- Documentation: <link>
- Code: <file:line>

---

_Created: YYYY-MM-DD_
_Last Updated: YYYY-MM-DD_
_Source: <session/issue/ticket>_

````

**Reading Memories (at session start):**

```markdown
## Session Start - Memory Check

Before starting work, check for relevant memories:
1. List available memories: `mcp__serena__list_memories`
2. Read memories matching the task domain
3. Apply knowledge from memories to current task
````

### 4.5 Skill Creation & Updates

**When to Create a Skill:**

| Criteria                                    | Action                  |
| ------------------------------------------- | ----------------------- |
| Procedure used 2+ times                     | Consider creating skill |
| Multi-step process with specific order      | Create skill            |
| Domain-specific workflow                    | Create skill            |
| User explicitly requests reusable procedure | Create skill            |

**Skill Directory Structure:**

```
.claude/
└── skills/
    ├── long-running-init/
    │   ├── SKILL.md
    │   └── templates/
    ├── database-migration/
    │   ├── SKILL.md
    │   └── scripts/
    └── deployment-checklist/
        └── SKILL.md
```

**SKILL.md Template:**

````markdown
---
name: <skill-name>
description: <one-line description>
version: 1.0.0
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <Skill Name>

## When to Use

Describe scenarios when this skill should be invoked.

## Prerequisites

- [ ] Prerequisite 1
- [ ] Prerequisite 2

## Procedure

### Step 1: <Step Name>

Detailed instructions...

### Step 2: <Step Name>

Detailed instructions...

## Verification

How to verify the skill completed successfully.

## Troubleshooting

Common issues and solutions.

## Examples

### Example 1: <Scenario>

```bash
# Commands or code
```
````

## Changelog

- v1.0.0 (YYYY-MM-DD): Initial version

````

### 4.6 Updating Instruction Files

**When to Update AGENT.md (Root):**

```markdown
Update /AGENT.md when learning is:
- [ ] Universal (applies to all services)
- [ ] Not project-specific
- [ ] A general pattern or practice
- [ ] Affects multiple agents/tools
````

**When to Update Service AGENT.md:**

```markdown
Update apps/<service>/AGENT.md when learning is:

- [ ] Specific to that service
- [ ] Service configuration
- [ ] Service-specific patterns
- [ ] Service troubleshooting
```

**Update Protocol:**

```markdown
## Before Updating Any Instruction File

1. **Identify the change**

   - What new knowledge needs to be captured?
   - Where does it fit in the document structure?

2. **Check for conflicts**

   - Does this contradict existing instructions?
   - If yes, which is correct? Update accordingly.

3. **Make the update**

   - Add new section or update existing
   - Follow existing format and style
   - Include examples if helpful

4. **Version and date**

   - Update version number (if applicable)
   - Update "Last Updated" date
   - Add changelog entry

5. **Inform user**
   - "I've updated <file> with <summary of learning>"
```

### 4.7 Error Reflection Template

**When an error occurs, use this template:**

```markdown
## 🔴 ERROR REFLECTION

### What Happened

- **Error**: [Error message or description]
- **Context**: [What I was trying to do]
- **Location**: [File, function, or step]

### Root Cause Analysis

- **Immediate cause**: [What directly caused the error]
- **Underlying cause**: [Why the immediate cause existed]
- **Knowledge gap**: [What I didn't know that led to this]

### Correction Applied

- **Fix**: [How I resolved the issue]
- **Verification**: [How I confirmed the fix works]

### Learning to Capture

| Question                   | Answer                                      |
| -------------------------- | ------------------------------------------- |
| Is this generalizable?     | Yes / No                                    |
| Who else might hit this?   | [Future agents, this project, all projects] |
| Where should I store this? | [Memory / AGENT.md / Skill]                 |

### Action Taken

- [ ] Created memory: `<name>`
- [ ] Updated AGENT.md: `<section>`
- [ ] Created/updated skill: `<name>`
- [ ] No action needed (one-off issue)

### Prevention

How to prevent this in the future:

- [Instruction or check to add]
```

### 4.8 Learning from User Corrections

**When user corrects your approach:**

```markdown
## 📝 USER CORRECTION REFLECTION

### Original Approach

What I did or planned to do.

### User's Correction

What the user said was wrong or should be different.

### Understanding

- Why was my approach wrong?
- What principle or rule did I miss?
- Is this documented somewhere I should have checked?

### Learning Classification

| Aspect                             | Assessment                   |
| ---------------------------------- | ---------------------------- |
| Was this in existing instructions? | Yes (I missed it) / No (gap) |
| Is this project-specific?          | Yes / No                     |
| Is this a general principle?       | Yes / No                     |

### Action

- [ ] If I missed existing instruction → Note to check more carefully
- [ ] If gap in instructions → Update appropriate file
- [ ] If project-specific → Create memory
- [ ] If general principle → Update AGENT.md
```

### 4.9 Proactive Learning Triggers

**During normal operation, watch for:**

```markdown
## Proactive Learning Signals

### Configuration Discovery

When you find configuration that isn't documented:

- Environment variables
- Service ports
- Connection strings
- Feature flags
  → ACTION: Update service AGENT.md or create config memory

### Process Discovery

When you figure out how something works:

- Build process
- Deployment steps
- Testing procedure
- Integration pattern
  → ACTION: Create skill or update documentation

### Workaround Discovery

When you find a workaround for a limitation:

- Tool limitation
- API quirk
- Framework bug
  → ACTION: Create troubleshooting memory

### Pattern Recognition

When you notice a repeated pattern:

- Code pattern used multiple times
- Similar errors across services
- Common task sequences
  → ACTION: Consider abstracting to skill or documenting pattern
```

### 4.10 Session End Reflection

**Before ending each session, ask:**

````markdown
## Session End Reflection Checklist

- [ ] Did I encounter any errors? → Capture in memory
- [ ] Did I discover any undocumented processes? → Update docs/memory
- [ ] Did the user correct me? → Update instructions
- [ ] Did I find a better way to do something? → Update skill/docs
- [ ] Did I learn project-specific knowledge? → Create memory
- [ ] Is there anything I'd do differently next time? → Document it

### Session Learning Summary

Add to claude-progress.txt:

```markdown
### Learnings This Session

- [Learning 1]: Stored in [location]
- [Learning 2]: Stored in [location]
```
````

````

---

## 5. Critical Operational Policies

### 5.1 Deletion Confirmation Policy

**MANDATORY: Always confirm before deleting ANY module, service, feature, or component.**

Before removing, deleting, or disabling anything:

1. **List all components** that will be affected by the removal
2. **Identify dependencies** - what other services rely on the component being removed?
3. **Assess impact** - will this break monitoring, logging, alerts, or other functionality?
4. **Present a summary** to the user showing:
   - Components to be deleted
   - Dependencies that will be affected
   - Services that will lose functionality
   - Required follow-up actions
5. **Wait for explicit confirmation** before proceeding with deletion
6. **Document what was removed** in the change log

**Deletion Impact Analysis Format:**

```markdown
⚠️ DELETION IMPACT ANALYSIS

Components to be removed:
- [Component 1] ([description])
- [Component 2] ([description])

Dependencies affected:
- [Service X] will need [alternative]
- [Component Y] requires [action]

Services that will lose functionality:
- [List affected functionality]

Associated files/configs:
- [List files to be deleted/modified]

⚠️ NOT AFFECTED (must be preserved):
- [Critical services to keep]

Proceed with deletion? [Requires explicit user confirmation]
````

### 5.2 Script-First Policy

**ALWAYS write reusable scripts for repetitive operations.** Never run ad-hoc commands for tasks executed multiple times.

**Must be scripted:**

- Server cleanup (Docker prune, log rotation, temp files)
- Database backup/restore
- File backup/sync
- Upload/download to/from servers
- Deployment procedures
- Health checks and monitoring
- Environment setup

**Script location:** `scripts/` directory, named descriptively (e.g., `backup-postgres.sh`, `cleanup-workers.sh`)

**Script requirements:**

- Include usage documentation in comments
- Add error handling and exit codes
- Log operations to file for audit trail
- Make idempotent when possible (safe to run multiple times)

### 5.3 No Shortcuts Policy

**IMPORTANT: Do NOT take shortcuts when implementing changes.**

When you encounter difficulties or blockers during implementation:

1. **Do NOT skip steps** or implement workarounds that compromise the goal
2. **Do NOT abandon the proper solution** in favor of a quick fix
3. **Report blockers immediately** and work through them collaboratively
4. **Follow through to completion** - partial implementations create tech debt
5. **Document challenges** so we can address root causes together

If you hit a snag, inform the user - work through it together rather than taking shortcuts.

### 5.4 Port Binding When Planning

**MANDATORY: When planning any infrastructure, service, or deployment, always include port binding strategy.**

Before starting any deployment or service setup:

````markdown
## Port Binding Strategy

### Ports to be Used

| Service/Component | Port | Protocol | External | Internal | Purpose             |
| ----------------- | ---- | -------- | -------- | -------- | ------------------- |
| Service A         | 3000 | HTTP     | Yes      | No       | API Gateway         |
| Service B         | 5432 | TCP      | No       | Yes      | PostgreSQL Database |
| Cache Layer       | 6379 | TCP      | No       | Yes      | Redis               |
| Monitoring        | 9090 | HTTP     | Yes      | Yes      | Prometheus Metrics  |

### Port Availability Check

Before deployment, verify:

- [ ] Port is not already in use: `netstat -an | grep :<port>`
- [ ] Port is within allowed range (1024-65535 for non-root)
- [ ] No firewall rules blocking the port
- [ ] Port is documented in service configuration
- [ ] Port matches docker-compose/k8s manifests
- [ ] Port is registered in DNS (if applicable)

### Port Binding Example

```yaml
# docker-compose.yml
services:
  myservice:
    ports:
      - "3000:3000" # HOST:CONTAINER
    environment:
      - PORT=3000 # Application listens on 3000 internally
```
````

### Port Conflict Resolution

If port is already in use:

1. **Check what's using the port**: `lsof -i :<port>` or `netstat -tlnp | grep :<port>`
2. **Options**:
   - Kill the occupying process (if safe): `kill -9 <PID>`
   - Change the port number to an available one
   - Use a different host/interface
3. **Document the decision** in your planning notes
4. **Verify after deployment** that the service is accessible on the correct port

````

### 5.5 Database Configuration Validation

**MANDATORY: When working with databases, ALWAYS validate database details from user input BEFORE using them.**

**Database details that MUST be validated:**

- Database name
- Username
- Password
- Host/IP address
- Port number
- Connection type (TCP/socket)
- SSL/TLS requirements

**Validation Checklist:**

```markdown
## Database Configuration Validation

### Input Validation

- [ ] Database name is provided and non-empty
- [ ] Database name matches naming conventions (alphanumeric, hyphens, underscores)
- [ ] Username is provided and non-empty
- [ ] Password is provided (or confirm if optional)
- [ ] Port number is provided and valid (1-65535)
- [ ] Port matches expected service (e.g., 5432 for PostgreSQL)
- [ ] Host/IP is resolvable or a valid IP address

### Pre-Connection Verification

```bash
# Verify connectivity before use
# For PostgreSQL
psql -h <host> -p <port> -U <username> -d <database> -c "SELECT 1;"

# For MySQL/MariaDB
mysql -h <host> -p <port> -u <username> -p<password> -D <database> -e "SELECT 1;"

# For Redis
redis-cli -h <host> -p <port> ping

# Check port is listening
netstat -an | grep <port> | grep LISTEN
nc -zv <host> <port>
````

### Configuration Validation Template

**Ask the user to confirm these details:**

```markdown
## Database Configuration Confirmation

Please confirm the following database details:

| Detail          | Value              | Verification              |
| --------------- | ------------------ | ------------------------- |
| Database Name   | [user-provided]    | [ ] Correct               |
| Username        | [user-provided]    | [ ] Correct               |
| Password        | ••••••••••         | [ ] Correct               |
| Host/IP         | [user-provided]    | [ ] Resolvable/reachable  |
| Port            | [user-provided]    | [ ] Valid range (1-65535) |
| Connection Type | TCP / Socket / SSL | [ ] Correct               |
| Database Exists | Yes / No           | [ ] Confirmed             |

### Validation Commands to Run

Before proceeding, I will run:

1. **Connectivity Test**: Test connection with provided credentials
2. **Permissions Check**: Verify user has required permissions
3. **Database Access**: Confirm database is accessible
4. **Existing Data**: Check for existing data (if applicable)

**Please confirm these details are correct before I proceed.**
```

### Connection String Validation

Always validate connection strings before use:

```bash
# PostgreSQL
postgresql://username:password@host:port/database

# MySQL
mysql://username:password@host:port/database

# MongoDB
mongodb://username:password@host:port/database?authSource=admin

# Validate each component:
# [ ] Username has no special chars (except @ in password)
# [ ] Password is URL-encoded (spaces=%20, special=percent-encoded)
# [ ] Host resolves to valid IP
# [ ] Port is accessible
# [ ] Database/auth source exists
```

### Common Validation Errors & Solutions

| Error                   | Cause                            | Solution                        |
| ----------------------- | -------------------------------- | ------------------------------- |
| Connection refused      | Service not running / wrong port | Verify service running + port   |
| Authentication failed   | Wrong username/password          | Confirm credentials with user   |
| Host not found          | Invalid hostname/IP              | Verify hostname/IP address      |
| Port out of range       | Port < 1 or > 65535              | Use valid port (1-65535)        |
| Permission denied       | User lacks database permissions  | Grant proper permissions        |
| Database does not exist | Database not created             | Create database or use existing |
| SSL certificate error   | SSL/TLS not properly configured  | Verify SSL settings             |

### When to Ask User to Re-validate

**STOP and ask user to re-provide database details if:**

- Connection test fails
- Credentials appear to be incorrect
- Port is already in use by different service
- Host is not resolvable
- Database does not exist (and needs to be created)
- Permission errors occur
- Any validation step fails

**Never proceed with unverified database configuration.**

---

### 5.6 Communication Style

**Reply in a lean, brief manner.** Be concise and direct. Avoid verbose explanations unless explicitly requested.

- Focus on actionable information
- Use bullet points and tables for clarity
- Skip unnecessary preambles
- Provide code/commands directly without excessive explanation

---

## 6. Test-Driven Development (TDD)

### 6.1 TDD Workflow (MANDATORY for all code changes)

```
┌──────────────────┐
│  1. RED          │  Write a failing test first
│  □ Write test    │  Test MUST fail (proves it tests something)
│  □ Run test      │  Verify failure message is clear
│  □ Commit test   │  "test: add failing test for X"
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. GREEN        │  Write minimum code to pass
│  □ Implement     │  Only enough code to make test pass
│  □ Run test      │  Verify test passes
│  □ Run ALL tests │  Ensure no regressions
│  □ Commit code   │  "feat: implement X"
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. REFACTOR     │  Clean up without breaking tests
│  □ Refactor      │  Improve code quality
│  □ Run ALL tests │  Must still pass
│  □ Commit        │  "refactor: clean up X"
└──────────────────┘
```

### 6.2 Test Coverage Requirements

| Test Type             | Minimum Coverage   | When Required                    |
| --------------------- | ------------------ | -------------------------------- |
| **Unit Tests**        | 80% line coverage  | ALL code changes                 |
| **Integration Tests** | Critical paths     | API endpoints, DB operations     |
| **E2E Tests**         | Happy path + error | User-facing features             |
| **Contract Tests**    | API contracts      | Service-to-service communication |

### 6.3 Test File Conventions

```
apps/
└── service-name/
    ├── src/
    │   └── feature/
    │       └── Feature.ts
    └── tests/                    # OR __tests__/ OR src/**/*.test.ts
        ├── unit/
        │   └── Feature.test.ts
        ├── integration/
        │   └── Feature.integration.test.ts
        └── e2e/
            └── Feature.e2e.test.ts
```

### 6.4 Test Automation Integration

**Pre-commit Hook (MUST pass before commit):**

```bash
# Runs automatically via husky/lefthook
npm run test:unit
npm run lint
npm run typecheck
```

**CI Pipeline (MUST pass before merge):**

```yaml
stages:
  - test:unit # Fast, runs on every commit
  - test:integration # Runs on PR
  - test:e2e # Runs before merge to main
  - coverage:report # Fail if below threshold
```

---

## 7. Documentation Requirements

### 7.1 Documentation Types

| Doc Type         | Location                      | Update Trigger                |
| ---------------- | ----------------------------- | ----------------------------- |
| **API Docs**     | `docs/api/` or inline OpenAPI | Any API change                |
| **Architecture** | `docs/architecture/`          | New services, major refactors |
| **Runbooks**     | `docs/runbooks/`              | New deployable components     |
| **Changelog**    | `CHANGELOG.md`                | Every release                 |
| **README**       | Per-service `README.md`       | Setup/usage changes           |

### 7.2 Documentation Structure

All documentation follows a hierarchical structure. Place documents in the correct location.

#### Root-Level Documentation (7 files max)

```
/                                       # Repository root
├── README.md                           # Project overview
├── CLAUDE.md                           # Claude AI instructions
├── AGENT.md                            # Universal agent instructions (this file)
├── CONSTITUTION.md                     # Project principles
├── CONTRIBUTING.md                     # Contribution guidelines
├── CHANGELOG.md                        # Change log
└── SECURITY.md                         # Security policy
```

#### /docs/ Directory Structure

```
/docs/
├── README.md                           # Documentation index
├── QUICK_START.md                      # Fast onboarding
│
├── architecture/                       # System design and decisions
│   ├── README.md
│   ├── monorepo-strategy.md
│   └── distributed-ml.md
│
├── deployment/                         # Service deployment guides
│   ├── README.md                       # Deployment checklist
│   ├── appwrite.md
│   ├── gitlab.md
│   ├── traefik.md
│   ├── keycloak.md
│   ├── ray-cluster.md
│   ├── ollama.md
│   ├── mailcow.md
│   └── monitoring.md
│
├── operations/                         # SRE/Operations runbook
│   ├── README.md
│   ├── server-infrastructure.md
│   ├── docker-swarm.md
│   ├── backup-restore.md
│   ├── disk-management.md
│   ├── troubleshooting/
│   │   ├── gitlab.md
│   │   ├── appwrite.md
│   │   └── networking.md
│   └── maintenance/
│       ├── cron-jobs.md
│       └── certificate-renewal.md
│
├── security/                           # Security documentation
│   ├── README.md
│   ├── hardening-guide.md
│   ├── fail2ban-setup.md
│   ├── firewall-rules.md
│   ├── secrets-management.md
│   └── vulnerability-scanning.md
│
├── cicd/                               # CI/CD and automation
│   ├── README.md
│   ├── gitlab-pipelines.md
│   ├── gitlab-runners.md
│   ├── branch-protection.md
│   └── github-sync.md
│
├── integrations/                       # Third-party integrations
│   ├── README.md
│   ├── claude-slack.md
│   ├── dns-setup.md
│   └── oauth2-sso.md
│
├── data-pipelines/                     # Data processing
│   ├── README.md
│   ├── gibd-news-pipeline.md
│   ├── indicator-backfill.md
│   └── data-cache.md
│
├── handoffs/                           # Session handoffs
│   ├── README.md
│   └── YYYY-MM-DD-topic.md
│
└── archive/                            # Historical documentation
    ├── README.md
    ├── migrations/                     # Completed migrations
    ├── retrospectives/                 # Post-mortems
    ├── audits/                         # Security audits
    └── status-reports/                 # Completion reports
```

#### App-Specific Documentation

Each app maintains its own documentation:

```
/apps/{app-name}/
├── README.md                           # Required: App overview
├── CLAUDE.md                           # Optional: AI instructions
└── docs/                               # Detailed documentation
    ├── architecture.md
    ├── api.md
    └── ...
```

#### Document Placement Rules

| Document Type        | Location                            | Example                     |
| -------------------- | ----------------------------------- | --------------------------- |
| Service deployment   | `/docs/deployment/`                 | `appwrite.md`               |
| Troubleshooting      | `/docs/operations/troubleshooting/` | `gitlab.md`                 |
| Security hardening   | `/docs/security/`                   | `fail2ban-setup.md`         |
| CI/CD configuration  | `/docs/cicd/`                       | `gitlab-runners.md`         |
| Integration guides   | `/docs/integrations/`               | `claude-slack.md`           |
| Data pipelines       | `/docs/data-pipelines/`             | `indicator-backfill.md`     |
| Session handoffs     | `/docs/handoffs/`                   | `2026-01-07-ray-upgrade.md` |
| Completed migrations | `/docs/archive/migrations/`         | `phase0-logs/`              |
| Post-mortems         | `/docs/archive/retrospectives/`     | `security-incident.md`      |
| Status reports       | `/docs/archive/status-reports/`     | `*_COMPLETE.md`             |
| App-specific docs    | `/apps/{app}/docs/`                 | `architecture.md`           |

#### What Goes to Archive

Move to `/docs/archive/` when:

- Migration/project is complete
- Status report is no longer active
- Document is superseded by newer version
- Audit is older than 6 months

**Archive subdirectories:**

- `migrations/` - Phase logs, database migrations
- `retrospectives/` - Post-mortems, lessons learned
- `audits/` - Security audits and reviews
- `status-reports/` - One-time completion reports (`*_COMPLETE.md`, `*_READY.md`)

### 7.3 Code Documentation Standards

**Functions/Methods:**

```typescript
/**
 * Calculate portfolio risk metrics using TARP-DRL model.
 *
 * @param portfolio - Current portfolio holdings
 * @param marketData - Historical market data for analysis
 * @returns Risk metrics including VaR, Sharpe ratio, max drawdown
 * @throws {InsufficientDataError} If less than 30 days of market data
 *
 * @example
 * const metrics = calculateRiskMetrics(portfolio, last90Days);
 * console.log(metrics.valueAtRisk); // 0.05 (5% VaR)
 */
```

**Complex Logic:**

```typescript
// IMPORTANT: This algorithm uses a sliding window approach because...
// See: https://paper-reference.com/algorithm-explanation
```

### 7.3 Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [Unreleased]

### Added

- New health check endpoint in ws-gateway (#123)

### Changed

- Improved rate limiting algorithm for better burst handling

### Fixed

- Memory leak in WebSocket connection pool (#456)

### Security

- Updated dependencies to patch CVE-2025-XXXXX
```

---

## 8. Code Review Protocol

### 8.1 Self-Review Checklist (Before PR)

```markdown
## Self-Review Checklist

### Code Quality

- [ ] No console.log/print statements left
- [ ] No commented-out code
- [ ] No hardcoded secrets or credentials
- [ ] Error handling covers edge cases
- [ ] No obvious performance issues (N+1 queries, etc.)

### Testing

- [ ] Unit tests cover new code (80%+ coverage)
- [ ] Integration tests for external dependencies
- [ ] Edge cases tested (null, empty, boundary values)
- [ ] Tests are deterministic (no flaky tests)

### Documentation

- [ ] Public APIs documented
- [ ] Complex logic has comments
- [ ] README updated if setup changed
- [ ] Changelog entry added

### Security

- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] No sensitive data in logs
- [ ] Rate limiting on public endpoints
```

### 8.2 PR/MR Description Template

```markdown
## Summary

Brief description of what this PR does.

## Changes

- Added X to support Y
- Modified Z to fix issue #123
- Removed deprecated W

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if UI changes)

[Before/After screenshots]

## Checklist

- [ ] Self-review completed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
```

---

## 9. Deployment & CI/CD

> **For Docker deployments:** See [Section 13: Docker Deployment](#13-docker-deployment) for detailed Docker best practices.

### 9.0 CRITICAL: No Direct Deployment

**ALL deployments MUST go through CI/CD pipeline. Never deploy directly via SSH or manual commands.**

| Forbidden                      | Required                               |
| ------------------------------ | -------------------------------------- |
| `docker run ...` on server     | Push to branch → CI/CD → Deploy        |
| `docker-compose up -d` via SSH | Merge Request → Pipeline → Auto-deploy |
| Manual `docker service create` | Git tag → Production pipeline          |
| SSH + manual commands          | Automated rollback on failure          |

### 9.1 Branch Strategy

```
main/master ─────────────────────────────────────────────►
     │                    │                    │
     │ feature/add-auth   │ fix/login-bug     │
     └────────┬───────────┴────────┬──────────┘
              │                    │
              ▼                    ▼
         [PR Review]          [PR Review]
              │                    │
              └────────────────────┘
                        │
                        ▼
                   [CI Pipeline]
                        │
                        ▼
                   [Merge to main]
                        │
                        ▼
                   [Auto-deploy to staging]
                        │
                        ▼
                   [Manual promote to prod]
```

### 9.2 Deployment Checklist

```markdown
## Pre-Deployment

- [ ] All tests passing in CI
- [ ] Security scan passed (no critical/high vulnerabilities)
- [ ] Database migrations tested
- [ ] Feature flags configured
- [ ] Rollback plan documented

## Deployment

- [ ] Deploy to staging first
- [ ] Smoke tests on staging
- [ ] Monitor logs/metrics for errors
- [ ] Deploy to production
- [ ] Verify health checks

## Post-Deployment

- [ ] Monitor error rates for 30 minutes
- [ ] Verify key user flows working
- [ ] Update deployment log
- [ ] Notify team of completion
```

### 9.3 Rollback Protocol

```bash
# If issues detected post-deployment:
1. Do NOT try to "fix forward" under pressure
2. Rollback immediately:
   git revert <commit-hash>
   # OR
   kubectl rollout undo deployment/<service>
   # OR
   docker service rollback <service>
3. Notify team in #incidents channel
4. Create incident report after stabilization
```

### 9.4 Integration Testing (MANDATORY Before Activation)

**CRITICAL: For ALL infrastructure changes, service integrations, and deployment activation, comprehensive integration tests MUST be performed BEFORE the change goes live.**

#### 9.4.1 Integration Test Requirements

**For every integration with external systems, verify:**

| Integration            | Test Category      | Validation                                             |
| ---------------------- | ------------------ | ------------------------------------------------------ |
| **Database**           | Connectivity       | Connection string works, queries execute               |
| **Message Queue**      | Connectivity       | Publish/subscribe works end-to-end                     |
| **Cache**              | Connectivity       | Cache write/read operations succeed                    |
| **External APIs**      | HTTP/Auth          | API calls authenticate, receive expected responses     |
| **Authentication**     | SSO/OAuth          | Login flow complete, tokens valid, user session works  |
| **Monitoring/Logging** | Data Flow          | Metrics collected, logs shipped, dashboards populate   |
| **File Storage**       | Read/Write         | File uploads succeed, downloads retrieve correct files |
| **Load Balancer**      | Traffic Routing    | Requests route to correct backend, health checks pass  |
| **DNS/Network**        | Resolution         | Hostnames resolve, network connectivity stable         |
| **Backup Systems**     | Restore Validation | Backup creation succeeds, restoration works correctly  |

#### 9.4.2 Pre-Activation Test Procedure

**BEFORE deploying ANY integration change:**

```markdown
## Integration Test Checklist

### 1. Connectivity Tests

- [ ] Component A can connect to Component B
- [ ] Authentication/credentials work
- [ ] Network connectivity verified
- [ ] Timeout/retry behavior tested

### 2. Data Flow Tests

- [ ] Data written to integrated system successfully
- [ ] Data retrieved from integrated system is correct
- [ ] Data format/schema matches expectations
- [ ] Edge cases handled (null, empty, large payloads)

### 3. Error Handling Tests

- [ ] When integrated system is down, graceful degradation works
- [ ] Errors logged properly
- [ ] Retries/fallbacks trigger correctly
- [ ] Alerts/notifications sent for failures

### 4. Performance Tests

- [ ] Integration latency acceptable (< SLA)
- [ ] No resource exhaustion under load
- [ ] Connection pooling working (if applicable)
- [ ] Concurrent operations don't cause conflicts

### 5. Data Integrity Tests

- [ ] Data not corrupted during integration
- [ ] Transactions atomic (all-or-nothing)
- [ ] No data loss on system restart
- [ ] Restore/recovery produces consistent state

### 6. Monitoring Tests

- [ ] Metrics collected from integrated system
- [ ] Logs appear in log aggregation (Loki/ELK/etc)
- [ ] Dashboards update with new data
- [ ] Alerts trigger when thresholds exceeded
```

#### 9.4.3 Specific Integration Test Templates

**Database Integration:**

```bash
# Test connection and queries
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "SELECT 1;"
docker exec gitlab gitlab-rake gitlab:check

# Test data integrity after schema changes
docker exec gitlab gitlab-rake db:migrate:status
docker exec gitlab gitlab-rails console -e production << EOF
# Verify table structure
puts ActiveRecord::Base.connection.columns('table_name').map(&:name)
EOF
```

**Cache Integration (Redis):**

```bash
# Test write/read
docker exec redis redis-cli SET test-key "test-value"
docker exec redis redis-cli GET test-key

# Test TTL
docker exec redis redis-cli EXPIRE test-key 10
docker exec redis redis-cli TTL test-key
```

**SSO/OAuth Integration (Keycloak):**

```bash
# Verify Keycloak accessible
curl -s http://10.0.0.84:8180 | grep -q "Keycloak" && echo "✅ Keycloak accessible"

# Verify GitLab configured for SSO
docker exec gitlab grep -A 20 "omniauth" /etc/gitlab/gitlab.rb

# Test login flow (manual: click "Keycloak" button, enter credentials)
# Verify redirect back to GitLab with valid session
# Verify user account created/linked
docker exec gitlab gitlab-rails console -e production << EOF
user = User.find_by(email: 'sso-user@example.com')
puts "✅ User created via SSO: #{user&.username}"
EOF
```

**Logging Integration (Loki):**

```bash
# Verify Loki accessible
curl -s http://10.0.0.80:3100/ready && echo "✅ Loki ready"

# Verify logs being shipped
docker exec gitlab tail -f /var/log/gitlab/gitlab-rails/production.log &
sleep 5
curl -s 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}' | jq '.data.result | length'
echo "✅ Logs received in Loki"

# Test dashboard
# Navigate to Grafana → Dashboards → Create new panel with {job="gitlab"}
# Verify logs appear in real-time
```

**Backup/Restore Integration:**

```bash
# Test backup creation
docker exec gitlab gitlab-backup create BACKUP=test

# Test NFS mount accessible
mount | grep gitlab-backups && echo "✅ NFS mounted"

# Test restore to staging
docker cp /mnt/gitlab-backups/gitlab/test_backup.tar.gz staging-gitlab:/var/opt/gitlab/backups/
docker exec staging-gitlab gitlab-backup restore BACKUP=test_backup
docker exec staging-gitlab gitlab-rake gitlab:check

# Verify data integrity
docker exec staging-gitlab gitlab-rails console -e production << EOF
puts "Projects: #{Project.count}"
puts "Users: #{User.count}"
puts "✅ Data restored successfully"
EOF
```

**Monitoring/Metrics Integration (Prometheus/Grafana):**

```bash
# Verify Prometheus scrape targets
curl -s http://10.0.0.80:9090/api/v1/targets | jq '.data.activeTargets | length'

# Verify metrics being collected
curl -s 'http://10.0.0.80:9090/api/v1/query?query=gitlab_ruby_gc_duration_seconds_total' | jq '.data.result | length'

# Verify Grafana dashboards
curl -s http://10.0.0.80:3000/api/dashboards | jq '.[] | .title'
```

#### 9.4.4 Rollback Criteria

**STOP and rollback if ANY of these conditions occur:**

| Condition                                  | Action                                                |
| ------------------------------------------ | ----------------------------------------------------- |
| Integration test fails for critical system | Rollback immediately, do not proceed                  |
| Performance SLA not met (>50% slower)      | Investigate, optimize, or rollback                    |
| Data integrity issues detected             | Rollback, investigate, verify backups intact          |
| Monitoring data not appearing              | Verify integration, do not proceed without visibility |
| Authentication/SSO fails for >5% of users  | Rollback, document issue, retry after fix             |
| More than 2 automated tests failing        | Rollback, fix root cause, retry                       |

#### 9.4.5 Integration Test Automation Script

Create `/opt/wizardsofts-megabuild/scripts/integration-tests.sh`:

```bash
#!/bin/bash
set -e

TESTS_PASSED=0
TESTS_FAILED=0
RESULTS_FILE="/tmp/integration-tests-$(date +%s).txt"

test_result() {
  if [ $? -eq 0 ]; then
    echo "✅ $1" | tee -a $RESULTS_FILE
    ((TESTS_PASSED++))
  else
    echo "❌ $1" | tee -a $RESULTS_FILE
    ((TESTS_FAILED++))
  fi
}

echo "=== Integration Test Suite ===" | tee $RESULTS_FILE
echo "Started: $(date)" | tee -a $RESULTS_FILE

# Database tests
docker exec gibd-postgres psql -U gitlab -d gitlabhq_production -c "SELECT 1;" > /dev/null
test_result "PostgreSQL connection"

docker exec gitlab gitlab-rake gitlab:check > /dev/null
test_result "GitLab database checks"

# Cache tests
docker exec redis redis-cli ping | grep -q "PONG"
test_result "Redis connectivity"

# SSO/Keycloak tests
curl -s http://10.0.0.84:8180 | grep -q "Keycloak"
test_result "Keycloak accessibility"

docker exec gitlab grep -A 5 "openid_connect" /etc/gitlab/gitlab.rb | grep -q "client_id"
test_result "Keycloak SSO configured"

# Logging tests
curl -s http://10.0.0.80:3100/ready > /dev/null
test_result "Loki service ready"

curl -s 'http://10.0.0.80:3100/loki/api/v1/query?query={job="gitlab"}' | jq '.data.result | length' | grep -q "^[1-9]"
test_result "GitLab logs in Loki"

# Backup tests
ls -la /mnt/gitlab-backups && [ -d /mnt/gitlab-backups/gitlab ]
test_result "NFS backup directory accessible"

docker exec gitlab gitlab-backup create BACKUP=test-integration
test_result "GitLab backup creation"

# Monitoring tests
curl -s http://10.0.0.80:9090/api/v1/targets | jq '.data.activeTargets | length' | grep -q "[1-9]"
test_result "Prometheus scrape targets"

curl -s http://10.0.0.80:3000 | grep -q "Grafana"
test_result "Grafana accessibility"

echo ""
echo "=== Test Summary ===" | tee -a $RESULTS_FILE
echo "Passed: $TESTS_PASSED" | tee -a $RESULTS_FILE
echo "Failed: $TESTS_FAILED" | tee -a $RESULTS_FILE

if [ $TESTS_FAILED -gt 0 ]; then
  echo "❌ INTEGRATION TESTS FAILED - Do not proceed with deployment"
  exit 1
else
  echo "✅ All integration tests passed - Safe to proceed"
  exit 0
fi
```

#### 9.4.6 When to Run Integration Tests

| Scenario                                | Run Tests | Why                                       |
| --------------------------------------- | --------- | ----------------------------------------- |
| Upgrade component version               | ✅ YES    | New version may have breaking changes     |
| Change integration endpoint/credentials | ✅ YES    | Config errors will break integration      |
| Deploy to new environment               | ✅ YES    | Environment-specific issues likely        |
| Enable new monitoring/logging           | ✅ YES    | Verify data flows to new systems          |
| Add new service integration             | ✅ YES    | First-time integration most risky         |
| Deploy to staging                       | ✅ YES    | Catch integration issues before prod      |
| Deploy to production                    | ✅ YES    | MANDATORY - never skip in production      |
| Regular maintenance/patches             | ⚠️ MAYBE  | If changes affect integrations, run tests |
| Configuration drift fixes               | ✅ YES    | Verify integration restored               |

---

## 10. Maintenance & Bug Fixes

### 10.1 Bug Fix Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Reproduce                                          │
│  □ Create minimal reproduction case                         │
│  □ Document exact steps to reproduce                        │
│  □ Identify affected versions/environments                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Write Failing Test (TDD)                           │
│  □ Write test that reproduces the bug                       │
│  □ Test MUST fail (proves bug exists)                       │
│  □ Commit: "test: add failing test for bug #123"           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Fix                                                │
│  □ Implement minimal fix                                    │
│  □ Run ALL tests (including new one)                        │
│  □ Commit: "fix: resolve issue #123 - description"         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Verify & Document                                  │
│  □ Test fix in staging environment                          │
│  □ Update changelog                                         │
│  □ Close issue with resolution details                      │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Security Patch Protocol

**CRITICAL: Security patches have highest priority.**

```markdown
## Security Patch Workflow

1. **Assess Severity**

   - CRITICAL: Actively exploited or trivial to exploit
   - HIGH: Serious vulnerability, not yet exploited
   - MEDIUM: Limited impact or difficult to exploit
   - LOW: Minimal impact

2. **Action Timeline**

   - CRITICAL: Fix within 4 hours, deploy immediately
   - HIGH: Fix within 24 hours
   - MEDIUM: Fix within 1 week
   - LOW: Fix in next release

3. **Disclosure**
   - Do NOT discuss in public channels
   - Create private security advisory
   - Notify affected users after patch deployed
```

### 10.3 Technical Debt Management

Track tech debt in `TECH_DEBT.md`:

```markdown
## Technical Debt Register

| ID     | Description                     | Impact | Effort | Priority |
| ------ | ------------------------------- | ------ | ------ | -------- |
| TD-001 | Replace deprecated auth library | High   | Medium | P1       |
| TD-002 | Add missing unit tests for X    | Medium | Low    | P2       |
| TD-003 | Refactor monolithic service Y   | High   | High   | P3       |

## Resolution Log

- 2025-01-15: TD-001 resolved in PR #456
```

---

## 11. Monorepo Navigation

### 11.1 Repository Structure

```
wizardsofts-megabuild/
├── AGENT.md                    # THIS FILE - Universal agent instructions
├── CLAUDE.md                   # Claude Code specific (imports AGENT.md)
├── .github/
│   └── copilot-instructions.md # GitHub Copilot specific
├── .cursor/
│   └── rules.md                # Cursor specific
├── apps/                       # Application code
│   ├── ws-gateway/             # Java Spring API Gateway
│   │   ├── AGENT.md            # Service-specific overrides
│   │   └── ...
│   ├── ws-discovery/           # Eureka Service Registry
│   ├── gibd-quant-web/         # Next.js Frontend
│   │   ├── AGENT.md            # Frontend-specific rules
│   │   └── ...
│   ├── gibd-quant-agent/       # Python ML Training
│   │   ├── AGENT.md            # ML-specific rules
│   │   └── ...
│   └── ...
├── packages/                   # Shared libraries
│   ├── wizwebui/               # UI component library
│   └── wizchart/               # Charting library
├── infrastructure/             # Docker, K8s, Terraform
│   ├── distributed-ml/
│   ├── gitlab/
│   └── ...
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── features.json               # Feature tracking (if using)
└── claude-progress.txt         # Session progress log
```

### 11.2 Service Discovery

**Finding the right service:**

| Need to work on...    | Look in...                                |
| --------------------- | ----------------------------------------- |
| API Gateway, routing  | `apps/ws-gateway/`                        |
| Service discovery     | `apps/ws-discovery/`                      |
| Stock data, trading   | `apps/gibd-quant-web/`, `apps/ws-trades/` |
| ML training, TARP-DRL | `apps/gibd-quant-agent/`                  |
| News scraping         | `apps/gibd-news/`                         |
| UI components         | `packages/wizwebui/`                      |
| Charts, indicators    | `packages/wizchart/`                      |
| Infrastructure        | `infrastructure/`                         |

### 11.3 Cross-Service Changes

When changes span multiple services:

```markdown
## Cross-Service Change Protocol

1. **Identify all affected services**

   - List services that need changes
   - Determine dependency order

2. **Plan deployment order**

   - Backend changes first (if breaking)
   - Database migrations before code
   - Frontend changes last

3. **Use feature flags**

   - Enable gradual rollout
   - Easy rollback if issues

4. **Coordinate in single PR (preferred)**
   - OR use linked PRs with clear dependencies
   - Document deployment order in PR description
```

---

## 12. Service-Specific Instructions

### 12.1 Instruction Hierarchy

```
AGENT.md (root)              # Universal rules (this file)
    │
    ├── apps/service/AGENT.md    # Service overrides
    │       │
    │       └── Inherits from root, can override
    │
    └── CLAUDE.md                # Claude-specific (imports AGENT.md)
        .github/copilot-instructions.md  # Copilot-specific
        .cursor/rules.md                 # Cursor-specific
```

### 12.2 Service-Specific AGENT.md Template

Create `apps/<service>/AGENT.md` for each service:

````markdown
# Agent Instructions - <Service Name>

> **Inherits from:** [/AGENT.md](/AGENT.md) > **Overrides:** Listed below

## Service Overview

Brief description of what this service does.

## Tech Stack

- Language: Java 21 / TypeScript 5 / Python 3.11
- Framework: Spring Boot 3 / Next.js 15 / FastAPI
- Database: PostgreSQL / Redis / Neo4j
- Testing: JUnit 5 / Jest / pytest

## Service-Specific Rules

### Testing (Override)

- Minimum coverage: 85% (higher than global 80%)
- Required: Controller integration tests for ALL endpoints

### Code Style (Override)

- Use constructor injection (not @Autowired fields)
- All DTOs must be records (not classes)

### Deployment (Addition)

- Requires database migration check before deploy
- Health check endpoint: /actuator/health

## Local Development

```bash
# Start dependencies
docker-compose up -d postgres redis

# Run service
./mvnw spring-boot:run

# Run tests
./mvnw test
```
````

## Common Tasks

### Add new endpoint

1. Create DTO in `dto/`
2. Add controller method
3. Add service method
4. Write tests (controller + service)
5. Update OpenAPI spec

### Database migration

1. Create migration in `db/migrations/`
2. Test locally: `./mvnw flyway:migrate`
3. Include in PR, will auto-run on deploy

````

### 12.3 Agent-Specific Configuration

**Claude Code (`CLAUDE.md`):**
```markdown
# Claude Code Instructions

> **Imports:** [AGENT.md](AGENT.md) - All rules from AGENT.md apply.

## Claude-Specific Additions

### Communication Style
Reply in lean, brief manner. Be concise and direct.

### Tool Usage
- Prefer Edit over Write for existing files
- Use Glob for file search, Grep for content search
- Use Task tool for complex multi-step operations

### Memory Usage
Check Serena memories before starting work on:
- Appwrite: `appwrite-deployment-troubleshooting`
- Traefik: `traefik-configuration-guide`
- GitLab: `gitlab-*`
````

**GitHub Copilot (`.github/copilot-instructions.md`):**

```markdown
# GitHub Copilot Instructions

> **Imports:** [AGENT.md](/AGENT.md) - All rules from AGENT.md apply.

## Copilot-Specific Additions

### Code Generation

- Always include JSDoc/JavaDoc for public methods
- Generate tests alongside implementation
- Prefer explicit types over inference

### Suggestions

- Prioritize security (validate inputs, escape outputs)
- Suggest error handling for all external calls
- Include logging for debugging
```

**Cursor (`.cursor/rules.md`):**

```markdown
# Cursor Rules

> **Imports:** [AGENT.md](/AGENT.md) - All rules from AGENT.md apply.

## Cursor-Specific Additions

### Chat Commands

- /test - Generate tests for selected code
- /refactor - Suggest refactoring improvements
- /explain - Explain selected code

### Code Actions

- Always apply prettier/eslint on save
- Auto-import from correct packages
```

### 12.4 Configuration-Based Loading

Some tools support configuration files to auto-load instructions:

**VS Code Settings (`.vscode/settings.json`):**

```json
{
  "github.copilot.chat.codeGeneration.instructions": [
    { "file": "AGENT.md" },
    { "file": ".github/copilot-instructions.md" }
  ]
}
```

**Cursor (`.cursorrc`):**

```json
{
  "rules": ["AGENT.md", ".cursor/rules.md"]
}
```

**Claude Code:** Auto-loads `CLAUDE.md` from project root and parent directories.

---

## 13. Docker Deployment

### 13.1 MANDATORY: CI/CD Only Deployment

**⛔ NEVER deploy services directly. ALL deployments MUST go through CI/CD pipeline.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT FLOW (MANDATORY)                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ❌ FORBIDDEN                         ✅ REQUIRED                           │
│  ─────────────                        ──────────                            │
│  docker run ...                       git push → CI/CD → Deploy             │
│  docker-compose up -d                 Merge Request → Pipeline → Deploy     │
│  docker service create                GitLab CI → Build → Test → Deploy     │
│  Manual SSH + docker commands         Automated rollback on failure         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why CI/CD Only:**

- Consistent, reproducible deployments
- Automated testing before deployment
- Audit trail of all changes
- Automatic rollback capability
- Security scanning in pipeline
- Environment parity (staging = production)

**Automation Users:**
| Context | User | Purpose |
|---------|------|---------|
| SSH (general ops) | `agent` | General server operations (`ssh agent@10.0.0.84`) |
| SSH (deployments) | `deploy` | CI/CD deployment operations (`ssh deploy@10.0.0.84`) |
| GitLab CI/CD | `agent` | Pipeline execution, MR creation, variable management |
| GitLab Admin | `mashfiqur.rahman` | Manual administration only |

**Note:** The `deploy` user exists on all servers (80, 81, 82, 84) with Docker group access for deployments.

### 13.2 Dockerfile Best Practices

**MANDATORY for all Dockerfiles:**

```dockerfile
# ✅ CORRECT: Production-ready Dockerfile
# 1. Use specific version tags (never :latest)
FROM node:20.11-alpine AS builder

# 2. Set working directory
WORKDIR /app

# 3. Copy dependency files first (layer caching)
COPY package*.json ./

# 4. Install dependencies (production only)
RUN npm ci --only=production

# 5. Copy source code
COPY . .

# 6. Build application
RUN npm run build

# 7. Multi-stage build: Production image
FROM node:20.11-alpine AS production

# 8. Security: Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 9. Set working directory
WORKDIR /app

# 10. Copy only production artifacts
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

# 11. Security: Run as non-root
USER appuser

# 12. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# 13. Expose port (documentation)
EXPOSE 3000

# 14. Use exec form for CMD
CMD ["node", "dist/main.js"]
```

**Security Checklist:**

| Requirement              | Implementation                               |
| ------------------------ | -------------------------------------------- |
| Non-root user            | `USER appuser` (UID 1001)                    |
| Minimal base image       | Alpine variants preferred                    |
| No secrets in image      | Use environment variables or secrets manager |
| Read-only filesystem     | `--read-only` flag where possible            |
| Drop capabilities        | `--cap-drop=ALL` in docker-compose           |
| No privileged mode       | Never use `--privileged`                     |
| Scan for vulnerabilities | `trivy image <image>` in CI                  |

### 13.3 Docker Compose Best Practices

```yaml
# ✅ CORRECT: Production docker-compose.yml
version: "3.8"

services:
  app:
    image: ${REGISTRY}/myapp:${VERSION} # Never use :latest
    container_name: myapp
    restart: unless-stopped

    # Security
    user: "1001:1001" # Non-root
    read_only: true # Read-only filesystem
    security_opt:
      - no-new-privileges:true # Prevent privilege escalation
    cap_drop:
      - ALL # Drop all capabilities
    cap_add:
      - NET_BIND_SERVICE # Only add what's needed

    # Resource limits (MANDATORY)
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Logging
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

    # Environment (use secrets for sensitive data)
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info
    env_file:
      - .env.production

    # Networking
    networks:
      - traefik-network

    # Volumes (minimal, read-only where possible)
    volumes:
      - ./data:/app/data:ro # Read-only data
      - logs:/app/logs # Named volume for logs
    tmpfs:
      - /tmp:size=100M # Temporary files in memory

networks:
  traefik-network:
    external: true

volumes:
  logs:
```

### 13.4 Image Tagging Strategy

**MANDATORY: Never use `:latest` in production.**

```
┌─────────────────────────────────────────────────────────────────┐
│  IMAGE TAGGING CONVENTION                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Format: <registry>/<image>:<version>-<build>                   │
│                                                                 │
│  Examples:                                                      │
│  ├── registry.wizardsofts.com/ws-gateway:1.2.3-abc123          │
│  ├── registry.wizardsofts.com/ws-gateway:1.2.3                 │
│  ├── registry.wizardsofts.com/ws-gateway:staging               │
│  └── registry.wizardsofts.com/ws-gateway:sha-abc123def         │
│                                                                 │
│  ❌ NEVER: registry.wizardsofts.com/ws-gateway:latest          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Version sources:**

- **Semantic version:** From `package.json` or `pom.xml`
- **Git SHA:** First 7 characters of commit hash
- **Build number:** CI pipeline build ID

### 13.5 CI/CD Pipeline Template

```yaml
# .gitlab-ci.yml - Docker deployment pipeline
stages:
  - build
  - test
  - security
  - deploy-staging
  - deploy-production

variables:
  DOCKER_IMAGE: ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}
  DOCKER_IMAGE_LATEST: ${CI_REGISTRY_IMAGE}:latest

# Build Docker image
build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build
      --build-arg VERSION=${CI_COMMIT_TAG:-${CI_COMMIT_SHORT_SHA}}
      --cache-from ${DOCKER_IMAGE_LATEST}
      -t ${DOCKER_IMAGE}
      -t ${DOCKER_IMAGE_LATEST}
      .
    - docker push ${DOCKER_IMAGE}
    - docker push ${DOCKER_IMAGE_LATEST}
  rules:
    - if: $CI_COMMIT_BRANCH == "master" || $CI_COMMIT_TAG

# Run tests in container
test:
  stage: test
  image: ${DOCKER_IMAGE}
  script:
    - npm run test:ci
    - npm run test:e2e
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

# Security scanning
security:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL ${DOCKER_IMAGE}
  allow_failure: false

# Deploy to staging (automatic)
deploy-staging:
  stage: deploy-staging
  image: docker:24
  environment:
    name: staging
    url: https://staging.wizardsofts.com
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker stack deploy -c docker-compose.staging.yml --with-registry-auth app
  rules:
    - if: $CI_COMMIT_BRANCH == "master"

# Deploy to production (manual approval)
deploy-production:
  stage: deploy-production
  image: docker:24
  environment:
    name: production
    url: https://wizardsofts.com
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker stack deploy -c docker-compose.production.yml --with-registry-auth app
  rules:
    - if: $CI_COMMIT_TAG
  when: manual # Requires manual approval
```

### 13.6 Docker Swarm Deployment

**For production services using Docker Swarm:**

```bash
# Deploy/update service via CI/CD (NOT manually)
docker service update \
  --image ${REGISTRY}/myapp:${VERSION} \
  --update-parallelism 1 \
  --update-delay 10s \
  --update-failure-action rollback \
  --rollback-parallelism 1 \
  --rollback-delay 5s \
  --with-registry-auth \
  myapp
```

**Health-based deployment:**

```yaml
# In docker-compose for Swarm
deploy:
  replicas: 3
  update_config:
    parallelism: 1
    delay: 10s
    failure_action: rollback
    order: start-first # Zero-downtime: start new before stopping old
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
```

### 13.7 Security Scanning

**MANDATORY: All images must pass security scan before deployment.**

```yaml
# In CI pipeline
security-scan:
  stage: security
  script:
    # Scan for vulnerabilities
    - trivy image --exit-code 1 --severity CRITICAL ${DOCKER_IMAGE}

    # Check for secrets in image
    - trivy image --security-checks secret ${DOCKER_IMAGE}

    # Scan Dockerfile for misconfigurations
    - trivy config --exit-code 1 Dockerfile
```

**Vulnerability thresholds:**
| Severity | Action |
|----------|--------|
| CRITICAL | Block deployment |
| HIGH | Block deployment |
| MEDIUM | Warning, review required |
| LOW | Informational |

### 13.8 Logging and Monitoring

```yaml
# Centralized logging configuration
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service,environment"
        env: "NODE_ENV,VERSION"
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=3000"
      - "prometheus.path=/metrics"
```

**Required metrics endpoint:**

```typescript
// Every service must expose /metrics for Prometheus
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});

// And /health for container health checks
app.get("/health", (req, res) => {
  res.json({ status: "healthy", version: process.env.VERSION });
});
```

### 13.9 Maintenance Operations

**Automated via CI/CD or scheduled jobs (NEVER manual):**

```yaml
# Scheduled maintenance pipeline
maintenance:
  stage: maintenance
  script:
    # Prune unused images (keep last 5)
    - docker image prune -a --filter "until=168h" -f

    # Prune stopped containers
    - docker container prune -f

    # Prune unused networks
    - docker network prune -f

    # Prune build cache (keep 10GB)
    - docker builder prune -f --keep-storage 10GB
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### 13.10 Rollback Procedure

**Automated rollback (preferred):**

```yaml
# CI/CD handles rollback on failure
deploy:
  script:
    - docker service update --image ${NEW_IMAGE} myapp
  after_script:
    - |
      if [ "$CI_JOB_STATUS" == "failed" ]; then
        docker service rollback myapp
      fi
```

**Manual rollback (emergency only):**

```bash
# Via CI/CD trigger, NOT direct SSH
# Create a rollback pipeline that deploys previous version
curl -X POST \
  -F "token=${TRIGGER_TOKEN}" \
  -F "ref=master" \
  -F "variables[ROLLBACK_VERSION]=1.2.2" \
  https://gitlab.example.com/api/v4/projects/1/trigger/pipeline
```

---

## Appendix A: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION QUICK REFERENCE                  │
├─────────────────────────────────────────────────────────────┤
│  START                                                      │
│  □ git pull && git log -5                                   │
│  □ Read claude-progress.txt                                 │
│  □ npm test (or equivalent)                                 │
│  □ Pick ONE task                                            │
├─────────────────────────────────────────────────────────────┤
│  INVESTIGATE (Before ANY change)                            │
│  □ Level 0: Read target code completely                     │
│  □ Level 1: Find callers + callees + tests + docs           │
│  □ Level 2: Find callers' callers + integration tests       │
│  □ Document findings in Investigation Report                │
├─────────────────────────────────────────────────────────────┤
│  BEHAVIOR CHANGE? → STOP & INFORM USER                      │
│  □ Changing return type/params? → STOP                      │
│  □ Changing defaults/error handling? → STOP                 │
│  □ Removing code/features? → STOP                           │
│  □ Present options A/B/C → Wait for confirmation            │
├─────────────────────────────────────────────────────────────┤
│  WORK (TDD)                                                 │
│  □ Write failing test → commit                              │
│  □ Implement → commit                                       │
│  □ Refactor → commit                                        │
│  □ Update docs → commit                                     │
├─────────────────────────────────────────────────────────────┤
│  END                                                        │
│  □ All tests pass                                           │
│  □ Update claude-progress.txt                               │
│  □ git push                                                 │
├─────────────────────────────────────────────────────────────┤
│  REFLECT (After EVERY session)                              │
│  □ Did I make errors? → Create troubleshooting memory       │
│  □ Did user correct me? → Update instructions               │
│  □ Did I discover new process? → Create skill/memory        │
│  □ Did I find config? → Update service AGENT.md             │
│  □ Log learnings in claude-progress.txt                     │
└─────────────────────────────────────────────────────────────┘
```

## Appendix B: Behavior Change Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│          BEFORE MODIFYING ANY EXISTING CODE                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. INVESTIGATE (2 levels deep)                             │
│     ├── Who calls this? (Level 1)                           │
│     ├── Who calls the callers? (Level 2)                    │
│     ├── What tests cover this?                              │
│     └── What docs reference this?                           │
│                                                             │
│  2. CLASSIFY THE CHANGE                                     │
│     ├── New code (no existing behavior) → PROCEED           │
│     ├── Refactor (same inputs/outputs) → PROCEED + TEST     │
│     └── Behavior change → STOP & INFORM                     │
│                                                             │
│  3. IF BEHAVIOR CHANGE:                                     │
│     ├── Document current vs proposed behavior               │
│     ├── List all impacted code, tests, docs                 │
│     ├── Present options (A: change, B: alt, C: keep)        │
│     └── WAIT for user confirmation                          │
│                                                             │
│  4. IF REMOVAL:                                             │
│     ├── Extra scrutiny - list ALL usage                     │
│     ├── Consider deprecation period                         │
│     ├── Present migration path                              │
│     └── WAIT for explicit confirmation                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix C: Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>

Types: feat, fix, docs, style, refactor, test, chore
Scope: service name or component (e.g., gateway, quant-web)

Examples:
- feat(gateway): add OAuth2 PKCE support
- fix(quant-agent): resolve memory leak in training loop
- test(trades): add integration tests for order API
- docs(readme): update local development instructions
```

---

_Document Version: 1.5.0_
_Last Updated: 2026-01-07_
_Applies to: All AI coding agents working on wizardsofts-megabuild_

---

## Changelog

### v1.5.0 (2026-01-07)

- Added Section 7.2: Documentation Structure
  - Hierarchical /docs/ directory structure
  - Document placement rules by type
  - Archive policy for completed/superseded docs
  - App-specific documentation guidelines

### v1.4.0 (2026-01-07)

- Added Section 13: Docker Deployment
  - CI/CD only deployment policy (no direct deployments)
  - Dockerfile best practices (multi-stage, non-root, health checks)
  - Docker Compose security and resource limits
  - Image tagging strategy (no :latest)
  - CI/CD pipeline template for GitLab
  - Docker Swarm deployment configuration
  - Security scanning with Trivy
  - Logging and monitoring requirements
  - Automated maintenance operations
  - Rollback procedures

### v1.3.0 (2026-01-07)

- Added Section 5: Critical Operational Policies
  - Deletion Confirmation Policy (from CLAUDE.md)
  - Script-First Policy (from CLAUDE.md)
  - No Shortcuts Policy (from CLAUDE.md)
  - Communication Style guidelines
- Renumbered sections 6-12 accordingly

### v1.2.0 (2026-01-07)

- Added Section 4: Reflection & Learning Protocol
  - Mandatory reflection triggers
  - Memory management with Serena MCP
  - Skill creation workflow
  - Error reflection template
  - User correction handling
  - Proactive learning triggers
  - Session end reflection checklist
- Updated Quick Reference Card with REFLECT step

### v1.1.0 (2026-01-07)

- Added Section 2: Code Investigation Protocol (2-level deep investigation)
- Added Section 3: Behavior Change Protocol (stop & inform user)
- Added Appendix B: Behavior Change Decision Tree
- Updated Quick Reference Card with investigation and behavior change steps

### v1.0.0 (2026-01-07)

- Initial release with full SDLC coverage

# Agent Instructions - WizardSofts Megabuild

> **Universal agent instructions for Claude Code, GitHub Copilot, Cursor, Windsurf, and any AI coding assistant.**

This document defines the complete software development lifecycle (SDLC) protocols for AI agents working on this monorepo.

---

## Table of Contents

0. [Agent Execution Model](#0-agent-execution-model) ⚠️ READ FIRST
1. [Session Lifecycle](#1-session-lifecycle)
2. [Code Investigation Protocol](#2-code-investigation-protocol)
3. [Behavior Change Protocol](#3-behavior-change-protocol)
   - [3.1 Stop and Inform](#31-mandatory-stop-and-inform-before-changing-behavior)
   - [3.2 Behavior Change Report](#32-behavior-change-report-format)
   - [3.3 Removal/Deletion Protocol](#33-removaldeletion-protocol)
   - [3.4 Examples](#34-examples-of-when-to-stop)
   - [3.5 Decision Flowchart](#35-quick-decision-flowchart)
   - [3.6 Breaking Changes Protocol](#36-breaking-changes-protocol-infrastructureservicesapplicationsfeatures)
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

## 0. Agent Execution Model

⚠️ **READ THIS SECTION FIRST. It defines how to interpret ALL other sections.**

### 0.1 Execute, Don't Document

**This document describes actions to EXECUTE, not documents to create.**

| When this document says... | You MUST... | You must NOT... |
|---------------------------|-------------|-----------------|
| "Verify X" | Run commands NOW, get real results | Create a document describing how to verify X |
| "Check Y before planning" | Execute the check NOW, then plan | Add "Check Y" as Phase 0 in your plan |
| "Investigate Z" | Run searches/reads NOW, gather data | Write an investigation plan document |
| "Follow protocol" | Execute the protocol steps NOW | Create a script that follows the protocol |

### 0.2 Pre-Flight Execution Rule

**Every task begins with EXECUTION of verification, not DOCUMENTATION of verification steps.**

```
⛔ WRONG BEHAVIOR:
   User: "Upgrade GitLab to 18.7.1"
   Agent: Creates "UPGRADE_PLAN.md" containing:
          "Phase 0: Pre-Flight - Run docker ps to check current version..."

✅ CORRECT BEHAVIOR:
   User: "Upgrade GitLab to 18.7.1"
   Agent: [Executes] ssh agent@10.0.0.84 "docker ps | grep gitlab"
   Agent: [Executes] ssh agent@10.0.0.84 "docker exec gitlab gitlab-rake gitlab:env:info"
   Agent: [With real data] Creates plan based on actual verified state
```

### 0.3 The Execution Sequence

For ANY task requiring infrastructure or system verification:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE A: EXECUTE VERIFICATION (Do this NOW - no documents)                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  1. Run verification commands using Bash/SSH tools                          │
│  2. Capture actual system state (versions, health, configs)                 │
│  3. Note any discrepancies between docs and reality                         │
│  4. Store findings in memory for use in Phase B                             │
│                                                                             │
│  ⛔ DO NOT create any files during this phase                               │
│  ⛔ DO NOT proceed to Phase B without real execution results                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE B: CREATE PLAN (Only after Phase A is complete)                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  1. Use VERIFIED data from Phase A (not assumptions)                        │
│  2. Create implementation plan/script based on reality                      │
│  3. Plan reflects actual current state, not documented state                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE C: EXECUTE PLAN                                                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  1. Execute the steps in the plan                                           │
│  2. Verify each step succeeded before proceeding                            │
│  3. Handle blockers per Section 1.4                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 0.4 Prohibited Behaviors

**⛔ NEVER do these:**

| Prohibited Action | Why It's Wrong | Correct Alternative |
|-------------------|----------------|---------------------|
| Create "Pre-Flight Checklist.md" | Documents verification instead of executing it | Run the verification commands directly |
| Add "Phase 0: Verification" to plan | Defers verification to later | Execute verification BEFORE creating plan |
| Write scripts to run "later" | Substitutes documentation for action | Run commands now, create scripts for repeatable ops |
| Copy template checklists into docs | Creates paperwork, not results | Execute each checklist item, record outcomes |
| Skip verification because "docs say X" | Docs may be stale | Always verify current state |

### 0.5 Document Creation Policy

**Create documents ONLY for:**

| Document Type | When to Create | Example |
|--------------|----------------|---------|
| Implementation scripts | After verification, for complex multi-step procedures | `upgrade-gitlab.sh` |
| Handoff notes | At session end, summarizing completed work | `docs/handoffs/2026-01-09-task/` |
| Retrospectives | After significant incidents or learnings | `docs/archive/retrospectives/` |
| Plans requiring user approval | After verification, for breaking changes (Section 3.6) | Inline in conversation or plan file |

**⛔ NEVER create documents as a substitute for execution.**

---

## 1. Session Lifecycle

### 1.1 Session Startup (MANDATORY)

> **⚠️ Per Section 0:** Execute these steps NOW. Do not create a "Session Startup Checklist" document.

Every session MUST begin by EXECUTING these steps:

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Load Context (EXECUTE NOW)                         │
│  → Read claude-progress.txt (if exists)                     │
│  → Read features.json (if exists)                           │
│  → Run: git log --oneline -10                               │
│  → Check: git status (any uncommitted work?)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Verify Environment (EXECUTE NOW)                   │
│  → Run init.sh (if exists) OR npm install / mvn install    │
│  → Run existing test suite: npm test / mvn test            │
│  → Verify build passes: npm run build / mvn compile        │
│  → If tests fail → FIX FIRST before new work               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Identify Work                                      │
│  → Load features.json → find highest priority "failing"    │
│  → OR check GitHub/GitLab issues assigned                   │
│  → Select EXACTLY ONE task for this session                 │
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
- [ ] Session artifacts saved to appropriate folders (see Section 1.3.2)
```

#### 1.3.1 Active Logging for Implementation

**For detailed logging procedures, see:** [docs/operations/SESSION_LOGGING_GUIDE.md](docs/operations/SESSION_LOGGING_GUIDE.md)

**Quick Reference:**

| Component | Location |
|-----------|----------|
| Server command logs | `/tmp/session-YYYYMMDD-HHMMSS.log` |
| System state snapshots | `/tmp/system-state-YYYYMMDD-HHMMSS.log` |
| Session artifacts | `docs/handoffs/YYYY-MM-DD-<task>/` |
| Retrospectives | `docs/archive/retrospectives/` |

**At Session End (MANDATORY):**
1. Move logs from `/tmp/` to `docs/handoffs/<session>/`
2. Create `implementation-log.md` with structured notes
3. Save command history
4. Create session README

#### 1.3.2 Document Storage Structure

**MANDATORY: All session artifacts MUST be saved to project folders, never left in /tmp**

**For full directory structure, see:** [Section 7.2 Documentation Structure](#72-documentation-structure)

**Key Locations:**

| Document Type | Location |
|---------------|----------|
| Session handoffs | `docs/handoffs/YYYY-MM-DD-<task>/` |
| Retrospectives | `docs/archive/retrospectives/` |
| Troubleshooting | `docs/operations/troubleshooting/` |
| Deployment logs | `infrastructure/<service>/deployment-logs/` |

**Document Lifecycle:**
1. **During Implementation:** Create logs in `/tmp/`
2. **At Session End:** Move to `docs/handoffs/<session>/`
3. **After Session:** Update docs with ground truth findings
4. **Periodic Cleanup:** Archive sessions older than 6 months

**For progress log format and templates, see:** [docs/operations/SESSION_LOGGING_GUIDE.md](docs/operations/SESSION_LOGGING_GUIDE.md)

### 1.4 Handling Implementation Blockers

**When unexpected issues arise during implementation:**

#### 1.4.1 Blocker Classification

**CRITICAL: Distinguish between blockers you can fix vs. those requiring user input:**

| Blocker Type            | Examples                                                                                | Action Required                                 |
| ----------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Easy Fix**            | Missing dependency, syntax error, test failure, incorrect configuration value           | Fix immediately, continue work                  |
| **Moderate Fix**        | Integration failure with known solution, missing environment variable, permission issue | Fix if solution is clear, otherwise inform user |
| **Complex Decision**    | Architectural choice, breaking change required, multiple solution paths                 | STOP → Inform user → Wait for confirmation      |
| **External Dependency** | Third-party service down, missing credentials, infrastructure not ready                 | STOP → Inform user → Wait for resolution        |

#### 1.4.2 Resolution Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  BLOCKER ENCOUNTERED DURING IMPLEMENTATION                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  Can I fix this easily? │
           │  (< 15 min, clear path) │
           └────────┬───────────────┘
                    │
      ┌─────────────┴─────────────┐
      │ YES                       │ NO
      ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐
│  FIX IT         │    │  STOP & INFORM USER  │
│  Document fix   │    │  Present options     │
│  Continue work  │    │  Wait for direction  │
└─────────────────┘    └──────────────────────┘
```

#### 1.4.3 Easy Fix Examples

**Fix immediately without user consultation:**

```markdown
## Examples of Easy Fixes

✅ **Missing Package**

- Error: `ModuleNotFoundError: No module named 'requests'`
- Fix: `pip install requests` or add to requirements.txt
- Action: Fix, commit, continue

✅ **Syntax Error**

- Error: `SyntaxError: invalid syntax`
- Fix: Correct the syntax error
- Action: Fix, commit, continue

✅ **Test Failure (Simple)**

- Error: Assertion failed, expected 200 got 404
- Fix: Correct the test expectation or fix the code
- Action: Fix, verify tests pass, continue

✅ **Wrong Port/URL**

- Error: Connection refused on port 3000
- Fix: Update to correct port (e.g., 3001)
- Action: Fix, verify connectivity, continue

✅ **File Permission**

- Error: Permission denied reading /var/log/app.log
- Fix: `chmod 644` or run as appropriate user
- Action: Fix, verify access, continue

✅ **Environment Variable**

- Error: DATABASE_URL not set
- Fix: Export variable or add to .env file
- Action: Fix, verify config loaded, continue
```

#### 1.4.4 User Consultation Required

**STOP and inform user for these scenarios:**

```markdown
## When to Stop and Consult User

❌ **Architectural Decision**

- Multiple ways to implement feature
- Trade-offs between approaches
- Performance vs. simplicity choice
  → Present options A/B/C, recommend, wait for confirmation

❌ **Breaking Change Required**

- Planned change won't work without breaking existing functionality
- Need to modify API contract
- Requires database migration
  → Explain issue, propose solution, wait for approval

❌ **Missing Infrastructure**

- Database not running
- External service not available
- Credentials not provided
  → Document what's missing, stop work, inform user

❌ **Scope Change**

- Original plan insufficient for requirement
- Additional work needed beyond scope
- Dependencies not anticipated
  → Explain gap, propose updated plan, wait for confirmation

❌ **Conflicting Requirements**

- User requirement conflicts with existing system
- Security policy prevents planned approach
- Performance target not achievable with current design
  → Explain conflict, propose alternatives, wait for decision
```

#### 1.4.5 Blocker Resolution Template

**When informing user about a blocker:**

```markdown
## 🛑 IMPLEMENTATION BLOCKER

### What Happened

[Brief description of the blocker encountered]

### Context

- **Task**: [What you were implementing]
- **Expected**: [What should have happened]
- **Actual**: [What actually happened]
- **Root Cause**: [Why it happened]

### Impact

- **Work Stopped At**: [Specific step/file/line]
- **Blocking**: [What can't proceed without resolution]
- **Not Blocking**: [What can still be done]

### Investigation Done

- [x] Checked X
- [x] Verified Y
- [x] Tested Z
- [Result summary]

### Options for Resolution

**Option A: [Recommended]**

- Description: [What to do]
- Pros: [Benefits]
- Cons: [Drawbacks]
- Effort: [Time estimate]
- Risk: [Low/Medium/High]

**Option B: [Alternative]**

- Description: [What to do]
- Pros: [Benefits]
- Cons: [Drawbacks]
- Effort: [Time estimate]
- Risk: [Low/Medium/High]

**Option C: [Do nothing / Workaround]**

- Description: [What to do]
- Pros: [Benefits]
- Cons: [Drawbacks]
- Impact: [What won't work]

### My Recommendation

[Option X] because [clear reasoning]

---

**Waiting for your direction on how to proceed.**
```

#### 1.4.6 Post-Resolution Reflection

**MANDATORY: After resolving any blocker, update the plan:**

```markdown
## After Blocker Resolution

1. **Document the Blocker**
   - Add to claude-progress.txt under "Blockers Resolved"
   - Include root cause and solution
2. **Update the Plan**

   - If blocker revealed planning gap → update plan document
   - If blocker indicates broader issue → add to investigation checklist
   - If blocker is recurring pattern → create troubleshooting memory

3. **Verify No Similar Blockers**

   - Check if same issue exists elsewhere in codebase
   - Proactively fix or document similar cases
   - Update relevant documentation

4. **Learning Capture**
   - If blocker was unexpected → why wasn't it caught in planning?
   - If blocker required special knowledge → create memory
   - If blocker revealed tool limitation → document workaround
```

#### 1.4.7 Examples from Recent Work

**Example 1: NFS Permission Issue (Easy Fix)**

```markdown
Blocker: GitLab container couldn't write to NFS mount
Root Cause: NFS export had root_squash enabled
Solution: Changed export to no_root_squash in /etc/exports
Action: Fixed immediately, verified with mount test, continued work
Time: 10 minutes
Documentation: Added to troubleshooting memory
```

**Example 2: Database Password Missing (Easy Fix)**

```markdown
Blocker: Integration test failing with "password required"
Root Cause: Test script expected password in env var, but it's in docker config
Solution: Modified test to extract password from GitLab Rails instead
Action: Fixed immediately, tests passed, continued work
Time: 5 minutes
Documentation: Updated test script comments
```

**Example 3: Architecture Decision (User Consultation)**

```markdown
Blocker: Backup script needs to handle multiple services, original design insufficient
Root Cause: Plan assumed single service, but need orchestrator for 5+ services
Solution Options:
A. Extend existing script with service discovery
B. Create global orchestrator (2-3 hours)
C. Keep manual per-service scripts for now
Action: STOPPED, informed user, presented options, recommended B
Outcome: User confirmed Option B, added to future scope (Section 4.4)
Documentation: Created Section 4.4 in plan document
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

### 2.2 Investigation Process

> **⚠️ Per Section 0:** PERFORM the investigation using search tools. Do not create an "Investigation Report" document.

**For EVERY code change, EXECUTE these searches:**

**Level 0: Target Analysis**
1. Read the target code using Read tool
2. Identify the public API/interface
3. Note any side effects (DB writes, API calls, file I/O)

**Level 1: Direct Dependencies (EXECUTE searches)**
1. **Find Callers:** `grep -rn "functionName" --include="*.ts"`
2. **Find Callees:** Read the file, note imports and function calls
3. **Find Tests:** `grep -rn "functionName" --include="*.test.ts"`
4. **Find Docs:** `grep -rn "functionName" docs/`

**Level 2: Indirect Dependencies (EXECUTE searches)**
1. **Caller's Callers:** For each caller found, search for ITS callers
2. **Integration Tests:** `grep -rn "functionName" --include="*.integration.test.ts"`
3. **API Contracts:** Check OpenAPI specs if this is an API endpoint

**After investigation:** Summarize findings mentally or in a brief note. Proceed to implementation based on what you learned. Only create a formal investigation document if:
- The change affects 10+ files
- User explicitly requests documentation
- The investigation reveals complex dependencies requiring discussion

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

### 2.4 When to Document Investigation Findings

> **⚠️ Per Section 0:** Most investigations do NOT require documentation. Proceed directly to implementation.

**Document findings ONLY when:**

| Situation | Action |
|-----------|--------|
| Investigation reveals behavior change needed | Document per Section 3.2 (inline in conversation) |
| Investigation reveals complex dependencies (10+ files) | Create brief summary inline |
| User explicitly asks for investigation report | Create formal document |
| Investigation will inform future sessions | Update relevant AGENT.md or create memory |

**For routine code changes:** Execute searches, note findings mentally, proceed to implementation. Do not create investigation documents for simple changes.

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

### 3.6 Breaking Changes Protocol (Infrastructure/Services/Applications/Features)

**CRITICAL: When making breaking changes to infrastructure, services, applications, or features, you MUST scan for consumers and obtain user approval.**

This protocol extends Section 3 to cover infrastructure and system-level breaking changes, not just code behavior changes.

#### 3.6.1 What Triggers This Protocol

**MANDATORY PROTOCOL WHEN:**

| Change Type        | Examples                                                                          | Action      |
| ------------------ | --------------------------------------------------------------------------------- | ----------- |
| **Infrastructure** | Changing ports, removing services, altering networking, modifying database schema | STOP & SCAN |
| **Service APIs**   | Changing API endpoints, response formats, authentication, rate limits             | STOP & SCAN |
| **Deployments**    | Disabling services, changing deployment strategy, modifying resource limits       | STOP & SCAN |
| **Features**       | Removing features, changing default behavior, disabling functionality             | STOP & SCAN |
| **Integrations**   | Changing external service connections, removing integrations, updating protocols  | STOP & SCAN |
| **Configuration**  | Changing default settings, removing config options, modifying behavior flags      | STOP & SCAN |

#### 3.6.2 Consumer Scanning Procedure

**Before making ANY breaking change, complete this scan:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: IDENTIFY THE CHANGE                                                │
│  □ What exactly is being changed?                                           │
│  □ What is the current behavior/configuration?                              │
│  □ What is the new behavior/configuration?                                  │
│  □ When will this take effect?                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: SCAN FOR CONSUMERS (MANDATORY)                                     │
│  □ Search codebase for references to this component/service/feature         │
│  □ Find all configuration files that reference this                         │
│  □ Find all documentation that describes this                               │
│  □ Find all tests that depend on this                                       │
│  □ Find all deployed instances that use this                                │
│  □ Find all external systems that integrate with this                       │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: CATEGORIZE IMPACT (MANDATORY)                                      │
│  □ Direct impact: What fails immediately?                                   │
│  □ Indirect impact: What breaks as a result?                                │
│  □ Cascading impact: What depends on those?                                 │
│  □ User impact: How do users experience this?                               │
│  □ Data impact: Is data migration required?                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: CREATE IMPACT REPORT (MANDATORY)                                   │
│  □ List all affected components                                             │
│  □ List all affected teams/services                                         │
│  □ Document what breaks                                                     │
│  □ Document required mitigations                                            │
│  □ Create options (proceed / deprecate / don't change)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: INFORM USER & GET APPROVAL (MANDATORY)                             │
│  □ Present impact report                                                    │
│  □ Present all options with pros/cons                                       │
│  □ Get explicit confirmation to proceed                                     │
│  □ Update plan based on user decision                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.6.3 Consumer Search Commands

**For each component/service/feature, search:**

```bash
# 1. Code references
grep -rn "component-name\|service-name\|feature-name" \
  apps/ infrastructure/ scripts/ \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.java" \
  --include="*.yml" --include="*.yaml" --include="*.json"

# 2. Docker/Kubernetes references
grep -rn "service-name" \
  docker-compose*.yml \
  infrastructure/*/docker-compose.yml \
  infrastructure/*/k8s/*.yml

# 3. Configuration references
grep -rn "service-name\|FEATURE_FLAG\|CONFIG_SETTING" \
  infrastructure/ .env* \
  --include="*.env" --include="*.conf" --include="*.config"

# 4. Documentation references
grep -rn "service-name\|component-name" \
  docs/ \
  --include="*.md" --include="*.adoc"

# 5. Test references
grep -rn "service-name" \
  apps/ \
  --include="*.test.ts" --include="*Test.java" --include="test_*.py"

# 6. Docker image references
grep -rn "image.*service-name" docker-compose*.yml infrastructure/*/

# 7. Environment variable references
grep -rn "SERVICE_NAME\|FEATURE_ENABLED" \
  apps/ infrastructure/ \
  --include="*.ts" --include="*.js" --include="*.py" --include="Dockerfile"
```

#### 3.6.4 Impact Analysis Report Template

**When presenting to user, use this format:**

````markdown
## 🛑 BREAKING CHANGE IMPACT ANALYSIS

### Change Summary

**Component:** [Service/Infrastructure/Feature name]  
**Type:** [Infrastructure / API / Feature / Integration / Configuration]  
**Current State:** [How it currently works]  
**Proposed Change:** [What will change]  
**Reason:** [Why this change is needed]

---

### Consumers Identified

#### Direct Consumers (Will Break Immediately)

| Consumer  | Type    | Location             | How It Uses          | Required Fix           |
| --------- | ------- | -------------------- | -------------------- | ---------------------- |
| Service A | Service | `apps/service-a/`    | Calls endpoint       | Update endpoint calls  |
| Config B  | Config  | `docker-compose.yml` | Uses old port        | Update port reference  |
| Test C    | Test    | `apps/test.ts:150`   | Expects old behavior | Update test assertions |

**Count:** N direct consumers requiring changes

#### Indirect Consumers (Will Break as a Result)

| Consumer      | Depends On           | Impact            | Severity |
| ------------- | -------------------- | ----------------- | -------- |
| Feature X     | Service A            | Cannot query data | HIGH     |
| Dashboard Y   | Service A API        | Displays error    | HIGH     |
| Integration Z | Configuration change | Connection fails  | MEDIUM   |

**Count:** N indirect consumers affected

#### Cascading Dependencies (Transitive Impact)

| Level  | Consumers                    | Impact             |
| ------ | ---------------------------- | ------------------ |
| Tier 2 | 3 consumers of Service A     | Data inconsistency |
| Tier 3 | 5 consumers of Dashboard Y   | UI errors          |
| Tier 4 | 2 consumers of Integration Z | Sync failures      |

---

### Impact Assessment

#### Services Impacted

- [ ] **Production Services:** [List N services]
- [ ] **Staging Services:** [List N services]
- [ ] **Development Services:** [List N services]

#### Data Impact

- [ ] **Data Migration Required:** Yes / No
  - If yes: [Migration strategy]
- [ ] **Data Loss Risk:** Yes / No
  - If yes: [Mitigation strategy]
- [ ] **Rollback Capability:** [How to rollback]

#### User-Facing Impact

- [ ] **User-visible changes:** [What users see]
- [ ] **User disruption:** [Downtime, errors, degraded service]
- [ ] **Support load:** [Expected support tickets]
- [ ] **Communication needed:** [User notifications required]

#### Effort & Timeline

| Task               | Effort        | Dependencies               |
| ------------------ | ------------- | -------------------------- |
| Consumer #1 fix    | 2 hours       | Depends on consumer #2     |
| Consumer #2 fix    | 3 hours       | Blocks consumer #1         |
| Database migration | 1 hour        | Must run before deployment |
| Testing            | 4 hours       | After all consumer fixes   |
| Documentation      | 1 hour        | Final step                 |
| **Total**          | **~11 hours** | **Sequential tasks**       |

---

### Options Available

#### Option A: Proceed with Breaking Change (Recommended)

**Description:** Make the change immediately, update all consumers, coordinate migration

**Pros:**

- Resolves underlying issue
- All systems on same version
- Clean state going forward

**Cons:**

- N consumers need updates
- Requires effort: [X hours]
- Risk of missing a consumer
- User disruption: [duration/scope]

**Effort:** [High/Medium/Low]  
**Risk:** [High/Medium/Low]  
**Timeline:** [How long to complete all updates]

#### Option B: Deprecation Period

**Description:** Keep old behavior for N releases, add deprecation warning, then remove

**Pros:**

- Allows gradual migration
- Consumers have time to update
- Reduces risk of missing something
- Users get warning period

**Cons:**

- Technical debt (maintain two versions)
- Longer time to resolution
- More testing required
- Code complexity increases

**Timeline:**

- Phase 1 (Release X.Y.0): Add deprecation warning
- Phase 2 (Release X.Y.5): Remove old behavior
- Grace period: [X releases / Y weeks]

**Effort:** [Effort breakdown for each phase]

#### Option C: Alternative Approach

**Description:** [Alternative way to achieve goal without breaking changes]

**Implementation:** [How to do it differently]

**Pros:** [Benefits of alternative]  
**Cons:** [Trade-offs]  
**Effort:** [How much work]

#### Option D: Don't Make Change

**Description:** Keep current behavior and address concerns differently

**Why this might be needed:** [Reasons to consider not changing]  
**Workarounds for users:** [How to live with current behavior]

---

### Recommendation

**I recommend: [Option A / B / C / D]**

**Reasoning:**

- Reason 1
- Reason 2
- Reason 3

---

### Risk Mitigation Plan (If Proceeding)

**For each affected consumer:**

| Consumer  | Mitigation             | Owner  | Timeline |
| --------- | ---------------------- | ------ | -------- |
| Service A | Update endpoint calls  | Team A | Day 1    |
| Config B  | Update port in compose | Ops    | Day 1    |
| Test C    | Update test assertions | Dev    | Day 1    |

**Rollback Plan:**

```bash
# If something breaks, rollback procedure:
1. Revert change with: git revert <commit>
2. Restart affected services
3. Verify with integration tests
4. Communicate to users
```
````

**Testing Plan:**

- [ ] Unit tests for each consumer fix
- [ ] Integration tests for all updated components
- [ ] Staging deployment and full smoke test
- [ ] Canary deployment to production (if applicable)

**Monitoring & Observability:**

- [ ] Metrics to monitor post-deployment
- [ ] Alerts for failure conditions
- [ ] Rollback triggers defined

---

### Attached Documentation

- **Consumer scan results:** [Link to full scan output]
- **Code references:** [Link to grep search results]
- **Deployment plan:** [Link to deployment documentation]
- **Rollback plan:** [Link to rollback procedures]

---

**🛑 AWAITING USER CONFIRMATION**

Please confirm one of:

1. **Option A** - Proceed with breaking change
2. **Option B** - Deprecation period (specify release numbers)
3. **Option C** - Alternative approach
4. **Option D** - Don't make change

You can also:

- Request modifications to the plan
- Ask for additional analysis
- Propose a different timeline
- Identify consumers I may have missed

````

#### 3.6.5 Examples of Proper Scanner Output

**Example 1: Removing a Microservice Port**

```markdown
## BREAKING CHANGE: Remove Internal Message Queue Service

### Change
- **Component:** `rabbitmq` service on port 5672
- **Current:** 3 internal services use it (events, notifications, cache)
- **Proposed:** Replace with direct database events table

### Consumers Found

#### Direct (Will Break)
- `gibd-quant-agent`: Line 145 publishes messages
- `ws-gateway`: Line 89 consumes messages
- `gibd-news`: Line 234 consumes messages

#### Indirect (Will Fail as Result)
- `gibd-quant-web`: Websocket updates from notifications
- `monitoring-dashboard`: Event stream visualization

#### Cascading
- 5 user dashboards depend on real-time updates

### Recommendation
**Option B: Deprecation Period**
- Release X.Y.0: Add new database events table, dual-write
- Release X.Y.5: Remove RabbitMQ, use only DB events
- Grace period: 5 releases (~10 weeks)

### Effort: 8 hours (spread over 2 releases)
````

**Example 2: Changing API Response Format**

```markdown
## BREAKING CHANGE: API Response Format

### Change

- **Endpoint:** `/api/v1/stocks`
- **Current:** `{ stocks: [...] }`
- **Proposed:** `{ data: [...], meta: {...} }`

### Consumers Found

#### Codebases Using This

- `gibd-quant-web` (4 locations)
- `gibd-quant-agent` (2 locations)
- External dashboards (3 customers)
- Mobile app (unknown versions)

#### Tests Impacted

- 8 API tests expect old format
- 2 integration tests

### Recommendation

**Option B: Deprecation**

- Support both formats for 2 releases
- Add `Accept-Format: legacy` header option
- Promote `v2` endpoint with new format

### Effort: 6 hours
```

#### 3.6.6 When NOT to Use This Protocol

**Skip this protocol (use simpler Behavior Change protocol) when:**

- Adding new functionality (backwards compatible)
- Fixing bugs (no behavior contract change)
- Internal refactoring (same inputs/outputs)
- Performance optimization (no external change)
- Non-production environment changes

**Use this protocol when:**

- ANY change affects multiple codebases
- ANY change affects deployed infrastructure
- ANY change affects external integrations
- ANY change affects users or applications
- ANY change to APIs or contracts

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

### 5.6 Script Maintenance Protocol

**MANDATORY: Keep infrastructure validation and setup scripts updated as the project evolves.**

See also: Section 5.2 (Script-First Policy)

#### 5.6.1 Core Infrastructure Scripts

The following scripts in `scripts/` directory MUST be kept current:

| Script                               | Purpose                   | Based On                                  |
| ------------------------------------ | ------------------------- | ----------------------------------------- |
| `validate-service-infrastructure.sh` | Ground truth verification | GitLab session 2026-01-08, AGENT.md § 9.0 |
| `setup-service-backups.sh`           | NFS backup automation     | GitLab backup setup, AGENT.md § 9.1       |
| `test-service-integration.sh`        | Integration test runner   | 28-test validation, AGENT.md § 9.4        |

**Full documentation**: See `scripts/README.md`

#### 5.6.2 When to Update Scripts

Update infrastructure scripts when:

| Trigger Event                        | Action Required                             | Example                                                |
| ------------------------------------ | ------------------------------------------- | ------------------------------------------------------ |
| **Adding new services**              | Extend test coverage, add validation checks | New Keycloak deployment → add SSO tests                |
| **Changing infrastructure patterns** | Update validation logic                     | Move from Docker Compose → Swarm → update port checks  |
| **Discovering failure modes**        | Add corresponding checks                    | NFS permission issue → add mount permission validation |
| **Updating conventions**             | Align scripts with standards                | Backup path change → update setup-service-backups.sh   |
| **Security improvements**            | Add security validation                     | New hardening rules → add firewall/SSL checks          |

#### 5.6.3 Script Update Checklist

**Before ANY infrastructure change:**

```markdown
## Script Update Assessment

- [ ] Will this change affect existing validation scripts?
- [ ] Do new services need test coverage?
- [ ] Are new failure modes being introduced?
- [ ] Has the standard changed (e.g., backup paths)?
- [ ] Do security policies require new checks?

If YES to any: Update scripts BEFORE deploying change
```

**After ANY infrastructure change:**

```markdown
## Script Verification

- [ ] Run validate-service-infrastructure.sh on affected service
- [ ] Run test-service-integration.sh to verify tests still work
- [ ] Update test expectations if infrastructure changed
- [ ] Document new patterns in script comments
- [ ] Test scripts in staging before production use
```

#### 5.6.4 Script Versioning

Track script changes in git with descriptive commits:

```bash
# Good commit messages
git commit -m "feat(scripts): add Keycloak SSO validation tests"
git commit -m "fix(scripts): update NFS permission checks for no_root_squash"
git commit -m "docs(scripts): document new backup retention validation"

# Bad commit messages (avoid)
git commit -m "update scripts"
git commit -m "fixes"
```

#### 5.6.5 Testing Script Changes

**MANDATORY: Test script modifications before committing:**

```bash
# 1. Test with --dry-run flag (if available)
./scripts/setup-service-backups.sh gitlab 10.0.0.84 10.0.0.80 --dry-run

# 2. Test against staging service first
./scripts/validate-service-infrastructure.sh gitlab-staging 10.0.0.85

# 3. Verify exit codes and error handling
./scripts/test-service-integration.sh gitlab 10.0.0.84 --strict

# 4. Test with edge cases
./scripts/validate-service-infrastructure.sh nonexistent-service 10.0.0.84  # Should fail gracefully
```

#### 5.6.6 Documentation Updates

When updating scripts, also update:

1. **scripts/README.md** - Usage examples, new options, when to use
2. **AGENT.md (this file)** - If protocol changes
3. **Service AGENT.md** - Service-specific test requirements
4. **CHANGELOG.md** - Note script improvements

#### 5.6.7 Script Maintenance Schedule

| Frequency                   | Task                 | Action                                     |
| --------------------------- | -------------------- | ------------------------------------------ |
| **After each infra change** | Verify scripts work  | Run against affected services              |
| **Monthly**                 | Review for drift     | Check if scripts match current reality     |
| **Quarterly**               | Update test coverage | Add tests for new services/patterns        |
| **Annually**                | Comprehensive audit  | Review all scripts, remove obsolete checks |

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

### 7.3 Documentation Efficiency Rules

**MANDATORY: Minimize documentation files per session.**

#### Rules

1. **Update existing files** rather than creating new ones
2. **One handoff document per session** (not multiple summaries)
3. **Append with timestamps** when adding to existing docs:
   ```markdown
   ## Update (2026-01-08)
   - Added rate limiting configuration
   - Fixed NFS permission issue
   ```
4. **Delete redundant files** before committing

#### Prohibited Patterns

- ❌ Creating `QUICK_REFERENCE.md` alongside `SUMMARY.md` (redundant)
- ❌ Multiple conversation summaries for same session
- ❌ Separate files for related content that fits in one doc

#### Allowed Patterns

- ✅ One `README.md` per session handoff folder
- ✅ Appending updates with timestamps to existing docs
- ✅ Moving completed work to `docs/archive/` (not duplicating)

#### Session Documentation Limit

- **Maximum new files per session:** 3 (handoff + retrospective + blocker if needed)
- **Prefer:** Updating existing files over creating new ones

### 7.4 Code Documentation Standards

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

### 7.5 Changelog Format

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

### 9.0 CRITICAL: Ground Truth Verification Protocol

> **⚠️ See [Section 0: Agent Execution Model](#0-agent-execution-model) for how to interpret this section.**
>
> This section describes commands to **EXECUTE NOW**, not documents to create.

**EXECUTE verification commands BEFORE planning. Do not add verification as "Phase 0" in a plan document.**

#### 9.0.1 When to Execute Ground Truth Verification

Execute verification (not document it) in these scenarios:

| Scenario | Action | Example |
|----------|--------|---------|
| Any infrastructure task | SSH and run commands NOW | `ssh agent@10.0.0.84 "docker ps"` |
| Service deployment | Check actual service state NOW | `docker exec gitlab gitlab-rake gitlab:env:info` |
| Bug fix / blocker | Verify the reported issue exists NOW | `curl http://service:port/health` |
| Migration / upgrade | Check current version NOW | `docker inspect --format '{{.Config.Image}}'` |
| Documentation conflicts | Check reality NOW | Reality trumps documentation |

#### 9.0.2 Verification Commands - EXECUTE THESE

**⛔ Do not copy these into a plan. Run them using Bash tool.**

**Infrastructure State (execute via SSH):**

```bash
# Container status - EXECUTE THIS
ssh agent@10.0.0.84 "docker ps -a | grep SERVICE_NAME"

# Container health - EXECUTE THIS
ssh agent@10.0.0.84 "docker inspect SERVICE_NAME --format '{{.State.Health.Status}}'"

# Service version - EXECUTE THIS
ssh agent@10.0.0.84 "docker exec SERVICE_NAME cat /etc/VERSION || echo 'no version file'"

# Recent logs - EXECUTE THIS
ssh agent@10.0.0.84 "docker logs --tail 50 SERVICE_NAME"

# Port listening - EXECUTE THIS
ssh agent@10.0.0.84 "ss -tlnp | grep ':PORT'"

# Disk space - EXECUTE THIS
ssh agent@10.0.0.84 "df -h /mnt/data"

# NFS mounts - EXECUTE THIS
ssh agent@10.0.0.84 "mount | grep nfs"
```

**Database/Service Health (execute via SSH):**

```bash
# PostgreSQL - EXECUTE THIS
ssh agent@10.0.0.84 "docker exec SERVICE_NAME psql -U user -c 'SELECT 1'"

# Redis - EXECUTE THIS
ssh agent@10.0.0.84 "docker exec SERVICE_NAME redis-cli ping"

# HTTP health - EXECUTE THIS
ssh agent@10.0.0.84 "curl -s http://127.0.0.1:PORT/health"
```

#### 9.0.3 After Verification: What to Do with Results

Once you have EXECUTED the verification commands and have real data:

1. **If reality matches documentation:** Proceed to create plan based on verified state
2. **If reality differs from documentation:**
   - Note the discrepancy in your plan
   - Base your plan on REALITY, not documentation
   - Include a task to update stale documentation
3. **If verification reveals different problem:** Adjust scope based on actual findings

**Example of correct behavior:**

```
User: "Upgrade GitLab to 18.7.1"

Agent EXECUTES:
  $ ssh agent@10.0.0.84 "docker ps | grep gitlab"
  → Result: gitlab container healthy, running 18.4.1

  $ ssh agent@10.0.0.84 "df -h /mnt/data"
  → Result: 65% used, 320GB free

  $ ssh agent@10.0.0.84 "docker exec gitlab gitlab-backup create --dry-run"
  → Result: Backup path configured, NFS mounted

Agent NOW creates plan:
  "Current state verified: GitLab 18.4.1, healthy, 320GB disk free.
   Proceeding with upgrade plan to 18.7.1..."
```

#### 9.0.4 Handling Documentation Mismatches

If verification reveals documentation is wrong:

1. **Do not stop to create a mismatch report document**
2. **Note the discrepancy** in your plan or conversation
3. **Proceed based on reality**
4. **Add a task** to update the stale documentation

#### 9.0.5 Use Existing Validation Scripts When Available

If validation scripts exist, EXECUTE them (don't create new ones):

```bash
# If this script exists, RUN IT:
./scripts/validate-service-infrastructure.sh gitlab 10.0.0.84

# If this script exists, RUN IT:
./scripts/test-service-integration.sh gitlab 10.0.0.84
```

If no validation script exists for your service, execute individual commands from 9.0.2.

For integration testing after changes:

```bash
./scripts/test-service-integration.sh <service-name> <host-ip>

# Examples:
./scripts/test-service-integration.sh gitlab 10.0.0.84
./scripts/test-service-integration.sh gitlab 10.0.0.84 --skip backup --skip monitoring
```

**See:** [scripts/README.md](scripts/README.md) for full script documentation.
**See:** [docs/operations/checklists/README.md](docs/operations/checklists/README.md) for manual checklists.

#### 9.0.7 App-Specific Pre-Flight Checklists

**Each app's AGENT.md MAY define its own pre-flight checklist.** Check the app's AGENT.md first.

| App | Checklist Location |
|-----|-------------------|
| ws-gateway | `apps/ws-gateway/AGENT.md` → Java Spring checklist |
| gibd-quant-agent | `apps/gibd-quant-agent/AGENT.md` → Python ML checklist |
| gibd-web-scraper | `apps/gibd-web-scraper/AGENT.md` → Python checklist |
| gibd-news | `apps/gibd-news/AGENT.md` → Data pipeline checklist |

**If no app-specific checklist exists, use the generic checklist in:**
`docs/operations/checklists/README.md`

### 9.1 Service Backup Storage Convention

**MANDATORY: All service backups MUST follow standardized NFS directory structure.**

#### 9.1.1 Backup Directory Structure

```
/mnt/data/Backups/server/
├── gitlab/              # GitLab backups (config, DB dumps, repositories, uploads)
├── postgres/            # PostgreSQL dumps
├── redis/               # Redis RDB snapshots
├── nexus/               # Nexus repository backups
├── keycloak/            # Keycloak exports
├── grafana/             # Grafana dashboards
└── <service-name>/      # Any service backup
```

_All backup artifacts for a given service (config, DB, files, blobs) must reside inside that service's folder. Use date-based subfolders (e.g., `YYYY-MM-DD/`) when size or retention needs clarity; keep flat layout only if volume is small and retention policy is simple._

#### 9.1.2 Backup Configuration Pattern

**For ALL services requiring backups:**

```yaml
# 1. Create service backup directory on NFS server (10.0.0.80)
ssh agent@10.0.0.80 "sudo mkdir -p /mnt/data/Backups/server/<service-name>"
ssh agent@10.0.0.80 "sudo chown <service-uid>:<service-gid> /mnt/data/Backups/server/<service-name>"

# 2. Export via NFS (if not already exported)
# /mnt/data is already exported with proper permissions

# 3. Mount on service host
ssh agent@<service-host> "sudo mkdir -p /mnt/<service-name>-backups"
ssh agent@<service-host> "sudo mount -t nfs 10.0.0.80:/mnt/data/Backups/server/<service-name> /mnt/<service-name>-backups"

# 4. Add to /etc/fstab for persistence
echo "10.0.0.80:/mnt/data/Backups/server/<service-name> /mnt/<service-name>-backups nfs defaults 0 0" | sudo tee -a /etc/fstab

# 5. Configure service to use backup directory
# In docker-compose.yml or service config:
volumes:
  - /mnt/<service-name>-backups:/var/backups/<service-name>
```

#### 9.1.3 GitLab Backup Example

**Following the standard pattern:**

```bash
# On NFS server (10.0.0.80)
sudo mkdir -p /mnt/data/Backups/server/gitlab
sudo chown 998:998 /mnt/data/Backups/server/gitlab  # git user UID:GID

# On GitLab server (10.0.0.84)
sudo mkdir -p /mnt/gitlab-backups
sudo mount -t nfs 10.0.0.80:/mnt/data/Backups/server/gitlab /mnt/gitlab-backups
echo "10.0.0.80:/mnt/data/Backups/server/gitlab /mnt/gitlab-backups nfs defaults 0 0" | sudo tee -a /etc/fstab

# Update gitlab.rb or GITLAB_OMNIBUS_CONFIG
gitlab_rails['backup_path'] = '/var/opt/gitlab/backups'

# Mount in docker-compose.yml
volumes:
  - /mnt/gitlab-backups:/var/opt/gitlab/backups
```

#### 9.1.4 Backup Testing

**After configuring backups, verify:**

```bash
# Test backup creation
docker exec <service> <backup-command>

# Verify file appears on NFS
ssh agent@10.0.0.80 "ls -lh /mnt/data/Backups/server/<service-name>/"

# Test backup restoration (in staging/test environment)
docker exec staging-<service> <restore-command>
docker exec staging-<service> <verify-command>
```

#### 9.1.5 Backup Retention Policy

**Standard retention for all services:**

```bash
# Keep last 7 daily backups, 4 weekly, 12 monthly
# Implement via cron or service-specific backup configuration

# Example: GitLab backup retention in gitlab.rb
gitlab_rails['backup_keep_time'] = 604800  # 7 days in seconds
```

#### 9.1.6 When to Deviate from Pattern

**ONLY deviate from `/mnt/data/Backups/server/<service>/` if:**

- Service has specific technical requirement (document why in service AGENT.md)
- Security/compliance requires different location (document in security docs)
- After consulting with team (document decision in ADR)

**NEVER** use service operational data directories for backups (e.g., `/mnt/data/docker/<service>/backups/` is NOT acceptable).

---

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
| Context | User | Purpose | Sudo Access |
|---------|------|---------|-------------|
| SSH (general ops) | `agent` | General server operations (`ssh agent@10.0.0.84`) | ✅ Passwordless sudo for docker, ufw, swap, systemctl |
| SSH (deployments) | `deploy` | CI/CD deployment operations (`ssh deploy@10.0.0.84`) | ⚠️ Requires sudo password |
| GitLab CI/CD | `agent` | Pipeline execution, MR creation, variable management | N/A (API-based) |
| GitLab Admin | `mashfiqur.rahman` | Manual administration only | N/A (GitLab admin) |

**Agent User Passwordless Sudo Commands:**
- `docker` (all docker commands)
- `docker-compose` / `docker compose`
- `ufw` (firewall management)
- `swapoff`, `swapon`, `sysctl` (swap management)
- `systemctl status`, `journalctl` (read-only system monitoring)

**Configuration:** `/etc/sudoers.d/91-agent-swap-management` on all servers (80, 81, 82, 84)

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

### 13.11 Post-Deployment Cleanup (MANDATORY)

**After ANY infrastructure operation (upgrade, deployment, migration), ALWAYS perform cleanup:**

**Cleanup Checklist:**

- [ ] **Docker System Cleanup**: Remove unused containers, images, and volumes
- [ ] **Memory Cache Cleanup**: Drop system caches to free memory
- [ ] **Disk Space Verification**: Confirm adequate free space remains
- [ ] **Log Rotation**: Ensure logs are properly rotated and old logs archived
- [ ] **Temporary Files**: Remove build artifacts and temporary files

**Execute these commands on the target server:**

```bash
# 1. Docker system prune (removes all unused containers, images, networks)
ssh agent@<SERVER_IP> "sudo docker system prune -af --volumes"

# 2. Drop system memory caches (requires sudo)
ssh agent@<SERVER_IP> "sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches"

# 3. Verify disk space after cleanup
ssh agent@<SERVER_IP> "df -h"

# 4. Check for large log files
ssh agent@<SERVER_IP> "find /var/log -type f -size +100M"

# 5. Rotate logs if necessary
ssh agent@<SERVER_IP> "sudo logrotate -f /etc/logrotate.conf"
```

**When to Execute Cleanup:**

- ✅ **After GitLab upgrades** (multiple image layers accumulate)
- ✅ **After Docker Swarm redeployments** (old service replicas remain)
- ✅ **After failed deployments** (dangling containers/images)
- ✅ **After database migrations** (temporary dump files)
- ✅ **Weekly maintenance** (scheduled cleanup)

**Cleanup Validation:**

```bash
# Verify cleanup success
ssh agent@<SERVER_IP> "docker system df"  # Check Docker disk usage
ssh agent@<SERVER_IP> "free -h"            # Check memory
ssh agent@<SERVER_IP> "df -h | grep -E '(Filesystem|/dev)'"  # Check disk
```

**Document Cleanup in Handoff:**

```markdown
## Post-Deployment Cleanup (YYYY-MM-DD)

**Executed:**
- [x] Docker system prune: Freed XXX GB
- [x] Dropped memory caches
- [x] Verified disk space: XX% used, XXX GB free
- [x] Log rotation completed

**Before:** XX% disk used, XX GB free
**After:** XX% disk used, XX GB free
**Freed:** XX GB total
```

---

## Appendix A: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION QUICK REFERENCE                  │
│                                                             │
│  ⚠️  EXECUTE commands, don't document them (Section 0)      │
├─────────────────────────────────────────────────────────────┤
│  START                                                      │
│  1. git pull && git log -5                                  │
│  2. Read claude-progress.txt                                │
│  3. npm test (or equivalent)                                │
│  4. Pick ONE task                                           │
├─────────────────────────────────────────────────────────────┤
│  BEFORE PLANNING: EXECUTE VERIFICATION (Section 9.0)        │
│  ─────────────────────────────────────────────────────────  │
│  ⛔ Do NOT add these as "Phase 0" in a plan document        │
│  ⛔ Do NOT create a "Pre-Flight Checklist" file             │
│                                                             │
│  RUN THESE COMMANDS NOW (for infra/deployment tasks):       │
│  → ssh agent@server "docker ps | grep SERVICE"              │
│  → ssh agent@server "docker exec SERVICE version-cmd"       │
│  → ssh agent@server "df -h /mnt/data"                       │
│  → ssh agent@server "curl localhost:PORT/health"            │
│                                                             │
│  THEN create plan based on verified reality                 │
├─────────────────────────────────────────────────────────────┤
│  INVESTIGATE (Before ANY code change)                       │
│  1. Level 0: Read target code completely                    │
│  2. Level 1: Find callers + callees + tests + docs          │
│  3. Level 2: Find callers' callers + integration tests      │
├─────────────────────────────────────────────────────────────┤
│  BEHAVIOR CHANGE? → STOP & INFORM USER                      │
│  • Changing return type/params? → STOP                      │
│  • Changing defaults/error handling? → STOP                 │
│  • Removing code/features? → STOP                           │
│  • Present options A/B/C → Wait for confirmation            │
├─────────────────────────────────────────────────────────────┤
│  WORK (TDD)                                                 │
│  1. Write failing test → commit                             │
│  2. Implement → commit                                      │
│  3. Refactor → commit                                       │
│  4. Update docs → commit                                    │
├─────────────────────────────────────────────────────────────┤
│  HIT A BLOCKER?                                             │
│  • Easy fix (<15 min)? → Fix it, continue                   │
│  • Complex/unclear? → STOP, inform user, present options    │
│  • After resolution: Update plan, capture learning          │
├─────────────────────────────────────────────────────────────┤
│  END                                                        │
│  1. All tests pass                                          │
│  2. Update claude-progress.txt                              │
│  3. git push                                                │
├─────────────────────────────────────────────────────────────┤
│  REFLECT (After EVERY session)                              │
│  • Made errors? → Create troubleshooting memory             │
│  • User corrected me? → Update instructions                 │
│  • Discovered new process? → Create skill/memory            │
│  • Found config? → Update service AGENT.md                  │
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

_Document Version: 1.8.0_
_Last Updated: 2026-01-09_
_Applies to: All AI coding agents working on wizardsofts-megabuild_

---

## Changelog

### v1.8.0 (2026-01-09)

- **MAJOR: Added Section 0 - Agent Execution Model** ⚠️
  - Defines how to interpret ALL other sections
  - Clarifies: "Execute, Don't Document" principle
  - Pre-Flight Execution Rule: Run verification BEFORE planning
  - Execution Sequence: Phase A (verify) → Phase B (plan) → Phase C (execute)
  - Prohibited Behaviors table with explicit "NEVER do these"
  - Document Creation Policy: Only create docs for specific cases
- **Rewrote Section 9.0 - Ground Truth Verification Protocol**
  - Removed template/checklist format that encouraged documentation
  - Changed to imperative "EXECUTE THESE" commands
  - Added "Example of correct behavior" showing execution flow
  - Simplified handling of documentation mismatches
  - Removed "report to user" step - user verifies final plan
- **Updated Appendix A - Quick Reference Card**
  - Added warning: "EXECUTE commands, don't document them"
  - Changed checkbox format to numbered steps
  - Added explicit prohibition against "Phase 0" in plans
  - Added "RUN THESE COMMANDS NOW" section with examples
- Root cause: Agents were creating documents describing protocols instead of executing them
- Fix: Imperative language, explicit prohibitions, and execution examples

### v1.7.0 (2026-01-08)

- Added Section 1.4: Handling Implementation Blockers
  - Blocker classification (Easy Fix vs User Consultation)
  - Resolution workflow with decision tree
  - Easy fix examples (missing packages, syntax errors, wrong ports)
  - User consultation scenarios (architectural decisions, breaking changes)
  - Blocker resolution template
  - Post-resolution reflection and plan updates
  - Real-world examples from recent work
- Updated Quick Reference Card with "HIT A BLOCKER?" section
- Emphasizes fixing blockers before continuing implementation
- Guides when to involve user vs proceed autonomously

### v1.6.1 (2026-01-08)

- Broadened Ground Truth Verification to ALL planning (features, bugs, tests, docs, infra)
- Enforced effort-only planning (avoid time estimates) and added configuration/recent logs to checks
- Clarified backup convention: all artifacts per service live in `/mnt/data/Backups/server/<service>/` with recommended date-based subfolders; keep flat only for small/simple retention
- Updated Quick Reference planning step to reflect scope and effort-only guidance

### v1.6.0 (2026-01-08)

- Added Section 9.0: Ground Truth Verification Protocol
  - Mandatory verification before planning infrastructure changes
  - Commands for checking actual system state (containers, ports, mounts, configs)
  - Ground truth validation checklist with documentation mismatch detection
  - Integration with planning workflow to verify reality vs documentation
  - Prevents wasted effort on incorrect assumptions
- Added Section 9.1: Service Backup Storage Convention
  - Standardized backup directory structure: `/mnt/data/Backups/server/<service>/`
  - Backup configuration pattern for all services
  - GitLab backup example following the standard
  - Backup testing and retention policy
  - Explicit guidance on when to deviate from pattern

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

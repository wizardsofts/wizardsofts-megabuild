# ✅ Breaking Changes Protocol Complete

**Status:** Successfully added to AGENT.md  
**Location:** Section 3.6  
**Version:** AGENT.md v1.7.1  
**Date:** 2026-01-08

---

## What Was Done

I've successfully added a comprehensive **Breaking Changes Protocol (Section 3.6)** to AGENT.md that requires agents to:

1. **Scan for all consumers** of any infrastructure, service, application, or feature being changed
2. **Analyze the impact** (direct, indirect, cascading)
3. **Create an impact report** with findings
4. **Present options** to the user (proceed, deprecate, alternative, don't change)
5. **Get explicit confirmation** before proceeding
6. **Execute the selected option** based on user decision

---

## Key Components Added

### Protocol Triggers

The protocol activates for breaking changes to:

- Infrastructure (ports, services, networking, database schema)
- Service APIs (endpoints, response formats, authentication)
- Deployments (disabling services, changing strategy)
- Features (removing/disabling)
- Integrations (external connections)
- Configuration (defaults, settings, flags)

### 5-Step Process

```
Step 1: IDENTIFY THE CHANGE
         ↓
Step 2: SCAN FOR CONSUMERS (mandatory)
         ↓
Step 3: CATEGORIZE IMPACT
         ↓
Step 4: CREATE IMPACT REPORT
         ↓
Step 5: INFORM USER & GET APPROVAL
         ↓
Proceed with Confirmed Plan
```

### Consumer Search Commands

Provided search patterns for finding:

- Code references (grep commands)
- Docker/Kubernetes files
- Configuration files
- Documentation
- Test files
- Environment variables

### Impact Analysis Template

Comprehensive report format including:

- Direct consumers (will break immediately)
- Indirect consumers (will break as result)
- Cascading dependencies (transitive impact)
- Services impacted (production, staging, development)
- Data impact (migration, loss risk)
- User-facing impact (disruption, notifications)
- Effort & timeline

### Decision Options

For each breaking change, present user with:

- **Option A:** Proceed with breaking change (with effort estimate)
- **Option B:** Deprecation period (gradual migration)
- **Option C:** Alternative approach (without breaking changes)
- **Option D:** Don't change (keep current behavior)

### Mitigation Strategies

For selected option:

- Per-consumer mitigation tasks
- Rollback procedures
- Testing plan
- Monitoring & observability setup

---

## Examples Provided

### Example 1: Remove Microservice Port

```
Change: Remove rabbitmq service on port 5672
Consumers: 3 services + 2 dependent features + 5 dashboards
Recommendation: Option B (Deprecation Period)
Timeline: Dual-write for 2 releases, ~10 weeks
Effort: 8 hours
```

### Example 2: Change API Response Format

```
Change: Modify /api/v1/stocks response structure
Consumers: 2 internal + 3 external + mobile app
Recommendation: Option B (Deprecation)
Timeline: Support both formats for 2 releases
Effort: 6 hours
```

---

## How to Use This Protocol

### When You Detect a Breaking Change

1. **STOP** - Don't proceed automatically
2. **Identify** - Document what's changing
3. **Scan** - Use grep commands to find consumers
4. **Analyze** - Build impact table
5. **Report** - Create impact analysis document
6. **Present** - Show findings + options to user
7. **Wait** - Get explicit confirmation
8. **Execute** - Proceed with confirmed plan

### Example Workflow

```
You detect: "I need to change the database port from 5432 to 5433"

↓

STOP: This is a breaking change

↓

SCAN: grep -rn "5432\|DATABASE_PORT" apps/ infrastructure/
Found: 8 references (5 in code, 2 in docker-compose, 1 in docs)

↓

ANALYZE:
- Direct: 3 services will fail to connect
- Indirect: 2 dependent services will fail
- Cascading: 1 user-facing API will error

↓

REPORT: Present findings with options
- Option A: Change immediately (2h effort, 3h testing)
- Option B: Support both ports for 2 releases (4h effort)
- Option C: Use service mesh (alternative, more effort)
- Option D: Keep current port (requires workaround)

↓

WAIT: Get user confirmation

↓

EXECUTE: Implement selected option with mitigation plan
```

---

## Files Modified

### Primary Change

- **AGENT.md** - Added Section 3.6 (Breaking Changes Protocol)
  - Lines 1023-1367 (comprehensive protocol with examples)
  - Updated Table of Contents (line 12)

### Documentation Created

- **AGENT_ENHANCEMENT_BREAKING_CHANGES_3.6.md** - Summary of enhancement
  - Use cases, examples, integration with other protocols
  - Implementation checklist, real-world validation

---

## Integration with Existing Protocols

### Section 3 (Behavior Change) - Code Level

```
Code change detected?
→ Does it change behavior?
  → YES: Use Section 3.5 (Stop & Inform)
  → NO: Continue with TDD
```

### Section 3.6 (Breaking Changes) - Infrastructure Level

```
Infrastructure change detected?
→ Scan for consumers
→ Create impact report
→ Present options to user
→ Execute confirmed plan
```

**Result:** Comprehensive coverage from code to infrastructure

---

## Protocol Features

✅ **Comprehensive** - Covers infrastructure, services, applications, features  
✅ **Practical** - Provides grep commands and search procedures  
✅ **User-Focused** - Gets explicit confirmation before proceeding  
✅ **Flexible** - Offers multiple options (proceed, deprecate, alternative, skip)  
✅ **Risk-Aware** - Identifies direct, indirect, cascading impacts  
✅ **Tested** - Includes real-world examples  
✅ **Documented** - Full procedures and templates provided

---

## When NOT to Use This Protocol

Skip this protocol (use simpler Behavior Change protocol) when:

- Adding new functionality (backwards compatible)
- Fixing bugs (no behavior contract change)
- Internal refactoring (same inputs/outputs)
- Performance optimization (no external change)
- Non-production environment changes

**Use full protocol when:**

- ANY change affects multiple codebases
- ANY change affects deployed infrastructure
- ANY change affects external integrations
- ANY change affects users or applications
- ANY change to APIs or contracts

---

## Key Takeaway

**Breaking changes require consumer scanning before proceeding.**

This protocol ensures that:

1. All affected systems are identified
2. Impact is visible and understood
3. Users make informed decisions
4. Mitigation strategies are planned
5. Rollback procedures are ready

---

## Quick Reference

| Aspect            | Details                                                                          |
| ----------------- | -------------------------------------------------------------------------------- |
| **Protocol Name** | Breaking Changes Protocol                                                        |
| **Section**       | 3.6                                                                              |
| **Triggers**      | Infrastructure, Service APIs, Deployments, Features, Integrations, Configuration |
| **Steps**         | 5-step scanning process                                                          |
| **Outcomes**      | User approval required before proceeding                                         |
| **Options**       | Proceed, Deprecate, Alternative, Skip                                            |
| **Examples**      | 2 detailed examples provided                                                     |
| **Status**        | ✅ Ready to use                                                                  |

---

**Document:** AGENT.md v1.7.1  
**Date:** 2026-01-08  
**Status:** ✅ Complete and Documented

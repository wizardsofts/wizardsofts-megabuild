# Security Policy Update - December 30, 2025

## Overview

This document summarizes the critical security policy updates enforced across the Wizardsofts Megabuild monorepo on December 30, 2025.

---

## 🚨 CRITICAL RULE CHANGES

### 1. CI/CD Deployment Enforcement

**NEW RULE**: **SSH-based Docker deployments are ABSOLUTELY FORBIDDEN**

#### What Changed

**Before**:
- Manual deployments via SSH were discouraged but allowed
- Agents could suggest SSH deployment as an option

**After**:
- SSH deployment is **STRICTLY PROHIBITED**
- All deployments **MUST** go through GitLab CI/CD pipeline
- Manual docker-compose operations on production servers are **FORBIDDEN**

#### Prohibited Actions (❌ NEVER)

- ❌ SSH into production servers to run docker-compose commands
- ❌ Run `docker-compose up/down/restart/build` on production via SSH
- ❌ Manually deploy services via SSH (except CI/CD emergencies)
- ❌ Bypass CI/CD for "quick fixes" or "urgent deploys"
- ❌ Deploy without running automated tests
- ❌ Suggest SSH deployment to users
- ❌ Write scripts that deploy via SSH

#### Required Actions (✅ ALWAYS)

- ✅ Commit and push changes to GitLab repository
- ✅ Let CI/CD pipeline automatically build and test
- ✅ Trigger deployments from GitLab UI (manual trigger button)
- ✅ Monitor pipeline execution in GitLab
- ✅ Verify health checks pass after deployment
- ✅ Use GitLab rollback job if issues occur
- ✅ Inform users about CI/CD deployment process

#### Only Exception

SSH access is permitted ONLY for:
- Emergency rollback when CI/CD is completely down
- Debugging CI/CD pipeline failures
- Server-level infrastructure maintenance (UFW, networking)
- Fixing the CI/CD system itself

**After any emergency SSH use**: Create incident report explaining why CI/CD was unavailable.

---

### 2. Port Binding Security

**NEW RULE**: **ALL ports MUST be bound to localhost (127.0.0.1) unless explicitly approved**

#### Port Binding Categories

##### 1. Localhost ONLY (127.0.0.1 binding - DEFAULT)

**These ports are NEVER exposed to 0.0.0.0**:
- PostgreSQL: 127.0.0.1:5433
- Redis: 127.0.0.1:6379
- API Gateway: 127.0.0.1:8081
- Business Services: 127.0.0.1:8182-8184
- ML Services: 127.0.0.1:5001-5004
- Ollama: 127.0.0.1:11435
- Web Apps: 127.0.0.1:3000-3001 (access via Traefik only)

**Docker Compose Syntax**:
```yaml
# ❌ WRONG - Exposed to internet
ports:
  - "5433:5432"

# ✅ CORRECT - Localhost only
ports:
  - "127.0.0.1:5433:5432"
```

##### 2. Private Network (0.0.0.0 + UFW REQUIRED)

Admin interfaces that need private network access:
- Grafana: 3002
- Traefik Dashboard: 8080
- Keycloak Admin: 8180
- Eureka: 8762
- Prometheus: 9090
- Appwrite Console: 4000

**MUST have corresponding UFW rules**:
```bash
ufw allow from 10.0.0.0/8 to any port <PORT>
ufw allow from 172.16.0.0/12 to any port <PORT>
ufw allow from 192.168.0.0/16 to any port <PORT>
```

##### 3. Public Internet (0.0.0.0 - STRONG JUSTIFICATION REQUIRED)

Only these ports are allowed on public internet:
- HTTP/HTTPS: 80, 443 (Traefik)
- SSH: 22
- Mail: 25, 465, 587, 993, 995, 143, 110

**Everything else is denied by default**.

---

### 3. UFW Firewall Configuration

**NEW REQUIREMENT**: All private network ports must have UFW rules

#### Standard UFW Setup

```bash
# Default policies
ufw default deny incoming
ufw default allow outgoing

# Public access ports
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"

# Private network admin ports (example: Keycloak)
ufw allow from 10.0.0.0/8 to any port 8180 comment "Keycloak Admin"
ufw allow from 172.16.0.0/12 to any port 8180
ufw allow from 192.168.0.0/16 to any port 8180

# Enable firewall
ufw enable

# Verify
ufw status numbered
```

#### Verification Commands

```bash
# Check port bindings
netstat -tlnp | grep LISTEN

# Expected output for secure setup:
# - PostgreSQL: 127.0.0.1:5433
# - Redis: 127.0.0.1:6379
# - Gateway: 127.0.0.1:8081
# - Admin ports: 0.0.0.0 but UFW restricted
```

---

## 📄 Updated Documents

### 1. CONSTITUTION.md

**File**: `/CONSTITUTION.md`

**Changes**:
- Added "Network Security & Port Binding" section
- Updated "Deployment Standards" with CI/CD enforcement
- Updated "Rollback Procedure" with CI/CD-first approach
- Added UFW firewall configuration requirements
- Added port binding examples and verification commands

**New Sections**:
- Network Security & Port Binding (lines 462-542)
- CI/CD Pipeline - MANDATORY (lines 551-590)
- Updated Rollback Procedure (lines 594-616)

### 2. AGENT_GUIDELINES.md

**File**: `/AGENT_GUIDELINES.md`

**Status**: **NEWLY CREATED** ✨

**Purpose**: Mandatory guidelines for ALL AI agents working on the repository

**Key Sections**:
- Authentication & Authorization (Keycloak SSO)
- Security Principles (Port binding rules)
- UFW Firewall Configuration & Port Binding
- Deployment Standards (CI/CD strictly enforced)
- Testing Standards
- AI Agent Behavior
- Red Flags - Stop and Ask
- Summary: The Golden Rules

**Golden Rules** (All AI Agents MUST follow):
1. **NEVER use SSH for Docker deployments** - CI/CD only
2. **NEVER bypass CI/CD pipeline** - No "quick fixes"
3. **ALWAYS bind to localhost** - Unless approved with UFW
4. **Keycloak for all admin auth** - No custom auth
5. **Constitution compliance** - Check before implementing
6. **Security first** - Never compromise for convenience
7. **Document everything** - Update docs with changes
8. **Test before commit** - All tests must pass
9. **Ask when uncertain** - Clarify before breaking production

### 3. apps/gibd-quant-agent/docs/CLAUDE.md

**File**: `/apps/gibd-quant-agent/docs/CLAUDE.md`

**Changes**:
- Added "Deployment & Security Rules" section
- Added CI/CD deployment requirements
- Added port binding security (localhost only for 5004)
- Added reference links to CONSTITUTION.md and AGENT_GUIDELINES.md
- Expanded development commands and testing requirements

---

## 🎯 Impact & Enforcement

### Who This Affects

1. **AI Agents** (Claude Code, GitHub Copilot, Cursor AI)
   - Must check AGENT_GUIDELINES.md before any deployment
   - Must enforce localhost port binding
   - Must reject SSH deployment requests

2. **Developers**
   - All deployments via GitLab CI/CD
   - No more SSH deployments
   - Must configure UFW rules for new services

3. **DevOps**
   - Monitor CI/CD pipeline health
   - Maintain UFW firewall rules
   - Audit port bindings regularly

### Enforcement Mechanisms

1. **Code Review**:
   - PRs with 0.0.0.0 bindings (except approved admin ports) will be rejected
   - PRs with SSH deployment scripts will be rejected

2. **CI/CD Pipeline**:
   - Deployment jobs verify port bindings
   - Health checks validate service accessibility

3. **Security Audits**:
   - Weekly: Verify port bindings with `netstat`
   - Weekly: Audit UFW rules with `ufw status`
   - Monthly: Full security review

---

## 📋 Migration Checklist

For existing services that violate new rules:

- [ ] Identify all services bound to 0.0.0.0
- [ ] Update docker-compose.yml with 127.0.0.1 bindings
- [ ] For admin ports: Add UFW firewall rules
- [ ] Test service accessibility after binding changes
- [ ] Update documentation
- [ ] Deploy via CI/CD pipeline
- [ ] Verify with `netstat -tlnp`

---

## 🚨 Violations & Consequences

**Zero Tolerance For**:
- SSH deployment to production
- Bypassing CI/CD pipeline
- Exposing PostgreSQL/Redis to 0.0.0.0
- Binding services without UFW rules
- Committing secrets/credentials

**Consequences**:
1. PR automatically rejected
2. CI/CD pipeline blocks deployment
3. Incident report required for violations
4. Security review for repeated violations

---

## 📞 Questions & Support

**For Questions**:
1. Check [CONSTITUTION.md](CONSTITUTION.md)
2. Check [AGENT_GUIDELINES.md](AGENT_GUIDELINES.md)
3. Create GitLab issue for clarification
4. Ask in team chat

**For Security Incidents**:
1. Create incident report immediately
2. Notify security team
3. Document what happened
4. Implement remediation
5. Update documentation if needed

---

## 📊 Summary

**Changes Made**:
- ✅ Updated CONSTITUTION.md with strict deployment rules
- ✅ Created AGENT_GUIDELINES.md for AI agent compliance
- ✅ Updated gibd-quant-agent CLAUDE.md
- ✅ Defined port binding security policy
- ✅ Documented UFW firewall configuration
- ✅ Committed and pushed to GitLab

**Deployment Method**:
- ✅ All changes committed via git
- ✅ Pushed to GitLab origin/master
- ✅ CI/CD pipeline will handle deployment
- ✅ No SSH used for deployment

**Next Steps**:
1. Review and merge GitLab pipeline run
2. Audit existing services for compliance
3. Update non-compliant services
4. Train team on new policies
5. Monitor adherence

---

**Document Version**: 1.0
**Created**: December 30, 2025
**Status**: Active
**Review Date**: Quarterly
**Maintained By**: Wizardsofts Security Team

# WizardSofts Megabuild - Claude Code Instructions

## Project Overview

This is a monorepo containing multiple WizardSofts applications and shared infrastructure:

- **Backend Services:** Java Spring microservices (ws-gateway, ws-discovery, ws-company, ws-trades, ws-news)
- **Frontend Apps:** React/Next.js applications (gibd-quant-web, gibd-news, ws-wizardsofts-web, etc.)
- **Infrastructure:** Docker Compose configurations for Appwrite, Traefik, monitoring

## Key Directories

- `/apps/` - Application code (each app has its own CLAUDE.md)
- `/docker-compose.*.yml` - Service orchestration files
- `/traefik/` - Traefik reverse proxy configuration
- `/docs/` - Deployment guides and documentation

## Infrastructure Components

### Appwrite (BaaS)
- **Config:** `docker-compose.appwrite.yml`
- **Env:** `.env.appwrite`
- **Domain:** appwrite.wizardsofts.com
- **Docs:** `docs/APPWRITE_DEPLOYMENT.md`
- **Memory:** `appwrite-deployment-troubleshooting`

### Traefik (Reverse Proxy)
- **Config:** `traefik/traefik.yml`, `traefik/dynamic/`
- **Memories:** `traefik-configuration-guide`, `traefik-network-requirements`, `https-dns-strategy`

### GitLab (Source Control & CI/CD)
- **Config:** `infrastructure/gitlab/docker-compose.yml`
- **URL:** http://10.0.0.84:8090
- **Registry:** http://10.0.0.84:5050
- **SSH Port:** 2222
- **Docs:** `docs/GITLAB_DEPLOYMENT.md`

## Server Infrastructure

| Server | IP | Purpose |
|--------|-----|---------|
| Server 80 | 10.0.0.80 | GIBD Services + Ray Worker |
| Server 81 | 10.0.0.81 | Database Server + Ray Worker |
| Server 82 | 10.0.0.82 | HPR Server (Monitoring) + Ray Worker |
| Server 84 (HP) | 10.0.0.84 | Production (Appwrite, microservices, GitLab, monitoring, **Ray + Celery**) |
| Hetzner | 178.63.44.221 | External services |

### Distributed ML Infrastructure (Server 84)

**Status:** ✅ Production (Phase 1 & 2 Complete)

| Component | Port | Access | Documentation |
|-----------|------|--------|---------------|
| **Ray Head** | 8265 (dashboard), 10001 (client) | Local network | [README](infrastructure/distributed-ml/README.md) |
| **Redis (Celery)** | 6380 | Local network | [Celery README](infrastructure/distributed-ml/celery/README.md) |
| **Flower** | 5555 | Local network | [Celery README](infrastructure/distributed-ml/celery/README.md) |
| **Celery Workers** | - | Internal | 10 workers (ml/data/default queues) |
| **Celery Beat** | - | Internal | Scheduled task runner |

**Deployment Reports:**
- [Phase 1: Ray Cluster](docs/PHASE1_DEPLOYMENT_SUMMARY.md) - 9 nodes, 25 CPUs
- [Phase 2: Celery Integration](docs/PHASE2_CELERY_VALIDATION_REPORT.md) - Task queue + orchestration
- [Networking Architecture](docs/DISTRIBUTED_ML_NETWORKING.md) - Host networking rationale

**Quick Access:**
```bash
# Flower dashboard credentials
ssh wizardsofts@10.0.0.84 'grep FLOWER_PASSWORD ~/celery/.env.celery'

# Ray dashboard
ssh -L 8265:127.0.0.1:8265 wizardsofts@10.0.0.84
# Then: http://localhost:8265

# Submit test task
python3 infrastructure/distributed-ml/celery/example_usage.py
```

## Common Tasks

### Deploy Appwrite Changes
```bash
cd /opt/wizardsofts-megabuild
docker-compose -f docker-compose.appwrite.yml --env-file .env.appwrite down
docker-compose -f docker-compose.appwrite.yml --env-file .env.appwrite up -d
```

### Check Service Health
```bash
docker-compose -f docker-compose.appwrite.yml ps
curl https://appwrite.wizardsofts.com/v1/health
```

### View Logs
```bash
docker logs appwrite -f --tail 100
docker logs traefik -f --tail 100
docker logs gitlab -f --tail 100
```

### Deploy GitLab Changes
```bash
cd /opt/wizardsofts-megabuild/infrastructure/gitlab
docker-compose down && docker-compose up -d
```

### Check GitLab Health
```bash
docker ps | grep gitlab  # Look for (healthy) status
docker exec gitlab gitlab-ctl status  # Check internal services
curl http://10.0.0.84:8090/-/readiness  # Check readiness endpoint
```

### Server 82 Metrics Exporters
```bash
# SSH into server 82
ssh wizardsofts@10.0.0.82

# Check exporters status
cd ~/server-82 && docker compose ps

# Check resource usage
docker stats --no-stream

# Check metrics endpoints
curl http://10.0.0.82:9100/metrics  # Node Exporter
curl http://10.0.0.82:8080/metrics  # cAdvisor

# View dashboards on central Grafana (server 84)
# http://10.0.0.84:3002 - Look for "Server 82" folder
```

### fail2ban Security (Server 84)
```bash
# Check fail2ban status
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client status sshd"

# View banned IPs
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client status sshd | grep 'Banned IP list'"

# Unban specific IP
ssh wizardsofts@10.0.0.84 "sudo fail2ban-client set sshd unbanip IP_ADDRESS"

# View recent ban activity
ssh wizardsofts@10.0.0.84 "sudo grep 'Ban' /var/log/fail2ban.log | tail -20"

# See docs/FAIL2BAN_SETUP.md for full guide
```

## Recent Changes (2025-12-30/31 - 2026-01-01)

### fail2ban Intrusion Prevention Deployed (2026-01-01)
- **Server**: 10.0.0.84 (HP Production)
- **Changes**:
  - Installed fail2ban for automated intrusion prevention
  - Configured SSH jail with 1-hour ban time for 5+ failed attempts
  - Disabled SSH password authentication (keys only)
  - Disabled root SSH login (must use sudo)
  - Whitelisted local network (10.0.0.0/24)
  - Created setup script: `scripts/setup-fail2ban-server84.sh`
  - Created comprehensive guide: `docs/FAIL2BAN_SETUP.md`
  - Updated security monitoring docs: `docs/SECURITY_MONITORING.md`
- **Security Impact**:
  - Automatic IP banning for brute force attempts
  - Eliminated password-based SSH attacks
  - Server 84 failed login alerts reduced to informational only
- **Configuration**:
  - Ban time: 1 hour (3600 seconds)
  - Max retries: 5 attempts in 10 minutes
  - Protected service: SSH (port 22)
- **Next Steps**:
  - Deploy to Server 80, 81, 82 (pending)
  - Consider Prometheus exporter for fail2ban metrics
- **Documentation**: `docs/FAIL2BAN_SETUP.md`

### Server 82 Metrics Exporters Deployed with Full Security Hardening (2025-12-31)
- **Server**: 10.0.0.82 (hpr, Ubuntu 24.04.3 LTS)
- **Changes**:
  - Installed Docker 29.1.3 and Docker Compose v5.0.0
  - Configured UFW firewall (local network access only)
  - Deployed metrics exporters: Node Exporter, cAdvisor
  - Removed Grafana (using central Grafana on server 84)
  - Integrated with central Prometheus on server 84
  - Created comprehensive documentation: `docs/SERVER_82_DEPLOYMENT.md`
- **Security Hardening**:
  - All services restricted to local network (10.0.0.0/24)
  - Memory limits: 256MB (node-exporter), 512MB (cAdvisor)
  - CPU limits: 0.5 cores (node-exporter), 1.0 core (cAdvisor)
  - Read-only root filesystem on node-exporter
  - All capabilities dropped except SYS_TIME
  - no-new-privileges enabled on all containers
- **Laptop Configuration**:
  - Configured lid close to be ignored (HandleLidSwitch=ignore)
  - Server will continue running when laptop lid is closed
- **Dashboards**: Available on central Grafana at http://10.0.0.84:3002
- **Lessons Learned**:
  - Use central Grafana/Prometheus instead of per-server instances
  - Always apply resource limits to prevent resource exhaustion
  - Laptops used as servers need lid close handling configured

### GitLab Health Check Fixed (2025-12-31)
- **Issue:** GitLab container showing "unhealthy" with 1500+ failing streak
- **Root Cause:** Health check was using `http://localhost/-/health` (port 80) but GitLab is configured to listen on port 8090
- **Fix:** Updated health check to `http://localhost:8090/-/health`
- **Lesson Learned:** When using non-standard ports in `external_url`, ensure health checks match the configured port

### Appwrite Deployment Fixed (2025-12-30)
- Fixed invalid entrypoints (schedule -> schedule-functions, etc.)
- Added missing `_APP_DOMAIN_TARGET_CNAME` environment variable
- Removed restrictive container security settings causing permission errors
- Enabled signup whitelist to block public registration

### Critical Security Incident Remediation (2025-12-31)
- **Incident:** Cryptocurrency mining malware injected via CVE-2025-66478 (Next.js RCE)
- **Root Cause:** Outdated Next.js 15.5.4 with unpatched remote code execution vulnerability
- **Full Details:** See `docs/SECURITY_IMPROVEMENTS_CHANGELOG.md`

**Changes Made:**
1. Updated Next.js to 15.5.7 (patched version)
2. Added rate limiting to all FastAPI services (slowapi)
3. Added input validation (regex patterns, SQL injection prevention)
4. Added API key authentication for Spring Boot write operations
5. Added security headers via Traefik middleware
6. Hardened containers (no-new-privileges, memory limits, Redis auth)
7. Added Prometheus security alerting rules

**Lessons Learned:**
- Always keep dependencies updated, especially web frameworks
- Rate limiting is essential for all public APIs
- Input validation must block dangerous patterns (SQL injection, path traversal)
- Container security options should be enabled by default

## Security Guidelines

### ⚠️ CRITICAL: Security Scanning is MANDATORY

**BEFORE using ANY new package or module:**

1. **Run Security Scan:**
   ```bash
   pip install pip-audit safety bandit
   pip-audit --desc  # Check for known CVEs
   safety check      # Alternative CVE database
   ```

2. **Check Online Vulnerability Databases:**
   - https://nvd.nist.gov/ (National Vulnerability Database)
   - https://security.snyk.io/ (Snyk Vulnerability DB)
   - https://github.com/advisories (GitHub Security Advisories)

3. **Review Package Security:**
   - Check last update date (avoid unmaintained packages)
   - Review GitHub issues for security concerns
   - Verify package maintainer reputation
   - Check for known CVEs: `pip-audit | grep <package-name>`

4. **Document Security Check:**
   ```markdown
   ## Security Scan - <Package Name>
   - **Date:** YYYY-MM-DD
   - **Tool:** pip-audit
   - **Result:** ✅ No vulnerabilities / ❌ N vulnerabilities found
   - **Action:** Updated to version X.Y.Z / Applied patches
   ```

**NO EXCEPTIONS:** Every new dependency MUST pass security scanning before use.

### Mandatory Security Practices

1. **Dependency Updates:** Check for security advisories weekly
   ```bash
   npm audit --audit-level=high
   pip-audit -r requirements.txt
   mvn org.owasp:dependency-check-maven:check
   ```

2. **Rate Limiting:** All public endpoints MUST have rate limits
   - FastAPI: Use `slowapi` with `@limiter.limit("N/minute")`
   - Spring Boot: Configure via `spring-cloud-gateway` or custom filter

3. **Input Validation:** Never trust user input
   - Ticker symbols: `^[A-Z0-9]{1,10}$`
   - Block dangerous patterns: `--`, `;`, `DROP`, `DELETE`, `EXEC`
   - Validate file paths for traversal: no `..` or `/`

4. **API Authentication:**
   - All write operations require `X-API-Key` header
   - API key stored in `${API_KEY}` environment variable
   - Never hardcode credentials in code

5. **Container Security:**
   - Always use `security_opt: [no-new-privileges:true]`
   - Set memory limits for all containers
   - Run as non-root user when possible

6. **Network Security - Port Exposure:**
   - **CRITICAL:** Services accessible from **local network (10.0.0.0/24)**, NOT localhost only
   - **Reason:** Distributed infrastructure (Ray, Celery, distributed ML) requires cross-server access
   - **Security:** UFW firewall REQUIRED to block external internet access
   - **ONLY Traefik** exposes to public internet (`0.0.0.0`)
   - **ALL other services** accessible from local network WITH UFW protection

   **Port Binding Strategy:**
   ```yaml
   # ✅ CORRECT - Local network with UFW firewall
   ports:
     - "7474:7474"  # Local network (MUST configure UFW)
     - "8000:8000"  # Local network (MUST configure UFW)

   # ❌ WRONG - Localhost only (breaks distributed access)
   ports:
     - "127.0.0.1:7474:7474"  # Ray workers can't access
     - "127.0.0.1:8000:8000"  # Celery tasks can't access
   ```

   **MANDATORY UFW Rules:**
   ```bash
   # Allow local network only
   sudo ufw allow from 10.0.0.0/24 to any port 7474 proto tcp

   # Block external internet
   sudo ufw deny 7474/tcp
   ```

   See: `mandatory-security-scanning` memory for full network security strategy

7. **Before Any Code Change:**
   - Run `gitleaks detect --source=.` to check for secrets
   - Verify dependencies with security scanners
   - Test rate limiting is not bypassed

### Security Documentation
- [SECURITY_IMPROVEMENTS_CHANGELOG.md](docs/SECURITY_IMPROVEMENTS_CHANGELOG.md) - Full change history
- [SECURITY_MONITORING.md](docs/SECURITY_MONITORING.md) - Prometheus alerts and monitoring
- [GITLAB_CICD_SECRETS.md](docs/GITLAB_CICD_SECRETS.md) - Credential management

## Infrastructure Lessons Learned

### Host Networking vs Bridge Networking (2026-01-02)

**Context:** During Phase 2 Celery deployment, encountered persistent Docker bridge networking failures on Server 84.

**Decision:** Switched entire distributed ML stack (Ray + Celery + Redis) to **host networking**.

**Rationale:**
1. **Server 84 Bridge Network Unreliability:** Despite containers being on the same Docker network, workers couldn't connect to Redis. Multiple troubleshooting attempts (DNS resolution, direct IP, socket tests) all failed.
2. **Ray Precedent:** Ray cluster already successfully uses host networking across all 9 nodes (proven approach).
3. **No Viable Alternative:** Bridge networking simply doesn't work reliably on Server 84 (20+ Docker networks, complex state).
4. **Performance Benefit:** Host networking eliminates NAT overhead for distributed computing workloads.
5. **Security Maintained:** UFW firewall restricts access to local network (10.0.0.0/24), Redis requires password authentication, services run on non-standard ports.

**Key Lessons:**

1. **When to Use Host Networking:**
   - ✅ Distributed computing frameworks (Ray, Celery, Spark)
   - ✅ High-performance inter-service communication
   - ✅ When bridge networking proves unreliable
   - ✅ Services that need consistent port access across nodes

2. **When to Use Bridge Networking:**
   - ✅ Web applications with Traefik reverse proxy
   - ✅ Services requiring network isolation
   - ✅ Port mapping needed (container:host different)
   - ✅ Multiple instances of same service on one host

3. **Security with Host Networking:**
   - **Always** use UFW or iptables to restrict access to local network
   - **Always** use authentication (passwords, API keys)
   - **Always** use non-standard ports to avoid conflicts
   - **Never** expose host-networked services to public internet directly

4. **Deployment Considerations:**
   - Docker Compose v1 (Server 84) uses `docker-compose` (hyphen), auto-loads `.env`
   - Docker Compose v2 (Servers 80, 81, 82) uses `docker compose` (space), may need `--env-file`
   - Always verify environment variable loading method before deployment

**Full Documentation:** [docs/DISTRIBUTED_ML_NETWORKING.md](docs/DISTRIBUTED_ML_NETWORKING.md)

## Git Worktree Workflow - MANDATORY (Parallel Agent Support)

**CRITICAL**: Direct pushes to `master` are BLOCKED. All changes must go through merge requests.

### Why Worktrees?
Git worktrees allow multiple agents to work on different branches **simultaneously** without conflicts. Each agent gets its own isolated working directory.

### Worktree Directory Structure
```
/Users/mashfiqurrahman/Workspace/
├── wizardsofts-megabuild/                    # Main repo (master)
└── wizardsofts-megabuild-worktrees/          # Worktrees directory
    ├── feature-add-auth/                     # Agent 1 working here
    ├── fix-security-issue/                   # Agent 2 working here
    └── infra-update-traefik/                 # Agent 3 working here
```

### Starting Any New Task (Worktree Method - PREFERRED)

```bash
# 1. Ensure master is up to date
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git checkout master
git pull gitlab master

# 2. Create worktree directory if it doesn't exist
mkdir -p ../wizardsofts-megabuild-worktrees

# 3. Create a new worktree with feature branch
git worktree add ../wizardsofts-megabuild-worktrees/feature-name -b feature/task-description

# 4. Work in the worktree directory
cd ../wizardsofts-megabuild-worktrees/feature-name

# 5. Make your changes, then commit
git add .
git commit -m "feat: implement feature description

Detailed explanation of changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# 6. Push to feature branch
git push gitlab feature/task-description

# 7. When done, clean up worktree (from main repo)
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git worktree remove ../wizardsofts-megabuild-worktrees/feature-name
```

### Alternative: Simple Branch Method (Single Agent)

```bash
# If only one agent is working, simple branching works too
git checkout -b feature/task-description
# ... make changes ...
git push gitlab feature/task-description
```

### Managing Worktrees

```bash
# List all worktrees
git worktree list

# Remove a worktree after merging
git worktree remove ../wizardsofts-megabuild-worktrees/feature-name

# Prune stale worktree references
git worktree prune
```

### Branch Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<description>` | `feature/add-auth` |
| Bug Fix | `fix/<description>` | `fix/login-error` |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` |
| Infrastructure | `infra/<description>` | `infra/update-traefik` |
| Documentation | `docs/<description>` | `docs/update-readme` |
| Refactor | `refactor/<description>` | `refactor/signal-service` |
| Security | `security/<description>` | `security/add-rate-limiting` |

### NEVER DO
- ❌ `git push origin master` - Direct push to master is BLOCKED
- ❌ `git push -f origin master` - Force push to master
- ❌ Work directly on master branch
- ❌ Start coding without creating a feature branch first

### ALWAYS DO
- ✅ Create a feature branch BEFORE any code changes
- ✅ Push to feature branch only
- ✅ Create merge request in GitLab
- ✅ Wait for CI/CD pipeline to pass
- ✅ Request review if required

### Reference
- Full documentation: [docs/GITLAB_BRANCH_PROTECTION.md](docs/GITLAB_BRANCH_PROTECTION.md)

## Credentials

Stored in `.env.appwrite` (not in git). Key variables:
- `_APP_OPENSSL_KEY_V1`
- `_APP_SECRET`
- `_APP_DB_PASS`
- `_APP_EXECUTOR_SECRET`

## Troubleshooting

1. Check Serena memories: `appwrite-deployment-troubleshooting`, `traefik-*`, `gitlab-*`
2. Review docs in `/docs/` directory
3. Check container logs with `docker logs <container-name>`

### GitLab Troubleshooting

**Container shows "unhealthy":**
1. Check health check output: `docker inspect --format='{{json .State.Health}}' gitlab`
2. Verify the health check port matches `external_url` in GITLAB_OMNIBUS_CONFIG
3. Check internal services: `docker exec gitlab gitlab-ctl status`
4. Review logs: `docker logs gitlab --tail 200`

**GitLab not accessible:**
1. Verify ports are exposed: `docker ps | grep gitlab`
2. Check nginx inside container: `docker exec gitlab gitlab-ctl status nginx`
3. Test from server: `curl http://localhost:8090/-/readiness`

**Database connection issues:**
1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check GitLab can reach DB: `docker exec gitlab gitlab-rake gitlab:check`

## Pending Tasks: WS Gateway OAuth2 Implementation

> **IMPORTANT:** Review this section at the start of each session. Complete these tasks before deploying ws-gateway to production.

**Status:** Implementation complete, pending verification and deployment
**Handoff Document:** [docs/WS_GATEWAY_HANDOFF.md](docs/WS_GATEWAY_HANDOFF.md)
**Serena Memory:** `ws-gateway-pending-tasks`

### High Priority
1. **Build Verification** - Maven cache was corrupted; run `./mvnw clean compile -U` in ws-gateway
2. **Push to Remote** - ws-gateway has 10+ unpushed commits
3. **Run Tests** - Execute `./mvnw test` to verify integration tests pass

### Medium Priority
4. **Frontend OIDC** - Integrate NextAuth with Keycloak in gibd-quant-web
5. **Deploy Keycloak** - Start Keycloak container on HP Server (10.0.0.84)

### Low Priority
6. **Commit Untracked Docs** - 6 documentation files in docs/ directory

### Quick Reference
```bash
# Verify build
cd apps/ws-gateway && ./mvnw clean compile -U

# Push commits
cd apps/ws-gateway && git push origin master
cd /path/to/megabuild && git push origin master

# Run tests
cd apps/ws-gateway && ./mvnw test

# Deploy Keycloak
cd infrastructure/keycloak && docker-compose up -d
```

For detailed instructions, see [docs/WS_GATEWAY_HANDOFF.md](docs/WS_GATEWAY_HANDOFF.md).

---

## Browser Automation (Playwright MCP)

**Default to headless mode** for all browser automation tasks. Only use headed mode when human interaction is required.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"]
    }
  }
}
```

For detailed configuration options and best practices, see [AGENT_GUIDELINES.md](AGENT_GUIDELINES.md#-browser-automation-playwright-mcp)

---

## Claude + Slack Integration

**Status:** Phase 1 Complete (Official App Installed) | Repository Connection Ready ✅
**Documentation:** [docs/CLAUDE_SLACK_POC.md](docs/CLAUDE_SLACK_POC.md)
**Test Results:** [docs/CLAUDE_SLACK_TEST_PLAN.md](docs/CLAUDE_SLACK_TEST_PLAN.md)

### Overview

Integrate Claude with Slack to enable AI-assisted development directly from team conversations.

**Key Capabilities:**
- ✅ Task assignment via @Claude mentions in Slack
- ✅ Automatic code generation from bug reports and feature requests
- ✅ GitLab MR creation with human approval workflows
- ✅ Code review automation
- ✅ Integration with existing CI/CD pipelines

### Quick Start

#### Phase 1: Official Claude Code in Slack (Installed ✓)

The Claude app is already installed in the WizardSofts Slack workspace.

**Usage:**
```
# In any Slack channel where Claude is invited:
@Claude add a health check endpoint to ws-gateway that returns the Git commit SHA

# Claude will:
# 1. Analyze the repository
# 2. Generate code changes
# 3. Post preview for review
# 4. Create PR/MR on approval
```

**Getting Started:**
1. Invite Claude to your channel: `/invite @Claude`
2. Authenticate your Claude account (one-time setup)
3. Connect GitHub mirror at https://code.claude.com/
   - Repository: https://github.com/wizardsofts/wizardsofts-megabuild
   - **Note:** GitLab automatically mirrors to GitHub for Claude access
   - Primary repo: http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild
4. Start using @Claude mentions

**Example Workflows:**
```
# Bug fix from error logs
@Claude The /api/trades endpoint is returning 500 errors
when the market is closed. See attached logs.
[Attach error-logs.txt]

# Feature request
@Claude Add rate limiting to ws-gateway. Use Redis for
storage and limit to 100 requests per minute per IP.

# Code review
@Claude Review this merge request for security issues:
https://gitlab.wizardsofts.com/.../merge_requests/42
```

#### Phase 2: Custom Slack Bot (Optional)

For advanced workflows with direct GitLab integration on Server 84:

```bash
# Deploy custom bot
cd /opt/wizardsofts-megabuild/infrastructure/claude-slack-bot
docker-compose up -d

# Check status
docker logs claude-slack-bot -f
curl http://localhost:3000/health
```

**Features (Custom Bot):**
- Direct GitLab API integration (no GitHub mirror needed)
- Custom approval workflows
- Internal network security
- Prometheus metrics & Grafana dashboards
- Full control over rate limiting and costs

### Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE_SLACK_POC.md](docs/CLAUDE_SLACK_POC.md) | Complete setup guide, workflows, troubleshooting |
| [CLAUDE_SLACK_CUSTOM_BOT.md](docs/CLAUDE_SLACK_CUSTOM_BOT.md) | Custom bot implementation (Phase 2) |
| [CLAUDE_SLACK_README.md](docs/CLAUDE_SLACK_README.md) | Quick reference and team onboarding |
| [CLAUDE_SLACK_TEST_PLAN.md](docs/CLAUDE_SLACK_TEST_PLAN.md) | Test results and validation |

### Common Tasks

**Test the Integration:**
```
# In Slack:
@Claude What services are in the wizardsofts-megabuild repository?
```

**Create a Bug Fix MR:**
```
# In #bugs channel:
[User posts bug report with logs]
@Claude Investigate and fix this issue
[Claude analyzes, proposes fix, creates MR]
```

**Code Review:**
```
# In #code-review channel:
@Claude Review MR !42 for security and performance issues
```

### Security Best Practices

1. **Channel Access Control**
   - Only invite Claude to development channels
   - Keep Claude out of #hr, #finance, #customer-data

2. **Never Share in Slack Threads**
   - API keys, passwords, credentials
   - Customer PII or sensitive data
   - Production database connection strings

3. **Review Before Merging**
   - Always review Claude's proposed changes
   - Ensure CI/CD security scans pass
   - Verify branch protection rules are enforced

4. **Monitor Usage**
   - Track API costs in Anthropic console
   - Review Claude's commit history periodically
   - Set budget alerts

### Troubleshooting

**Claude doesn't respond to @mentions:**
```bash
# 1. Check if Claude is in the channel
/invite @Claude

# 2. Re-authenticate your account
# Slack → Apps → Claude → Re-authenticate
```

**Repository not found:**
```
# Connect repository at https://code.claude.com/
# Use GitHub mirror: https://github.com/wizardsofts/wizardsofts-megabuild
```

**See full troubleshooting guide:** [docs/CLAUDE_SLACK_POC.md](docs/CLAUDE_SLACK_POC.md#troubleshooting)

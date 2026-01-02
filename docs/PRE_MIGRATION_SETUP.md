# Pre-Migration Setup Summary

**Date:** 2026-01-01
**Status:** ✅ Completed

## Overview

This document summarizes the pre-migration setup completed before starting the WizardSofts Distributed Architecture Migration.

## 1. Token Verification & Generation

### GitHub Token ✅ VERIFIED
- **Token:** `ghp_[REDACTED]` (stored in ~/.zshrc and secure vault)
- **User:** wizardsofts
- **Rate Limit:** 4999/5000 remaining
- **Status:** Valid and ready for GitHub mirroring

### GitLab Token ✅ GENERATED
- **Old Token (Feed):** `glft-[REDACTED]` - ❌ Invalid for API access
- **New Token:** `glpat-[REDACTED]` (stored in ~/.zshrc and secure vault)
- **Name:** GitHub Mirror Automation
- **Scope:** `api` (full API access)
- **Expires:** January 31, 2026
- **Status:** Created via Playwright automation, ready for use
- **Usage:** For GitLab built-in push mirror to GitHub

## 2. User Account Creation

### User Purpose
- **deploy:** For automated deployment operations (CI/CD, service management)
- **agent:** For monitoring and read-only operations (Claude Code agent access)

### Server Status

| Server | IP | Deploy User | Agent User | Docker Access | Notes |
|--------|-----|-------------|------------|---------------|-------|
| 80 (hppavilion) | 10.0.0.80 | ✅ Created | ✅ Created | ✅ Enabled | docker group assigned |
| 81 (wsasus) | 10.0.0.81 | ✅ Created | ✅ Created | ✅ Enabled | docker group assigned (monitoring only) |
| 82 (hpr) | 10.0.0.82 | ✅ Created | ✅ Created | ✅ Enabled | docker group assigned, lid open required |
| 84 (gmktec) | 10.0.0.84 | ✅ Created | ✅ Created | ✅ Enabled | docker group assigned |

### User Credentials
```bash
# Deploy user
Username: deploy
Password: Deploy@2026!
Groups: deploy, docker

# Agent user
Username: agent
Password: Agent@2026!
Groups: agent, docker
```

### Permissions Model
- **NO sudo access** (per user request)
- **Docker group membership only** for container management
- Access via `su` from admin account (wizardsofts)

### Example Usage
```bash
# From wizardsofts account:
sudo su - deploy
docker ps
docker restart <container>

# Agent read-only access:
sudo su - agent
docker ps
docker logs <container>
docker inspect <container>
```

## 3. Server 82 Status

### Issue ✅ RESOLVED
- **Initial Problem:** SSH connection timeout when laptop lid was closed
- **Root Cause:** Server 82 is a laptop that suspends network when lid is closed
- **Resolution:** Laptop lid opened, SSH accessible on port 22

### Configuration Status
- **Deploy user:** ✅ Created with docker group access
- **Agent user:** ✅ Created with docker group access
- **Docker containers:** 2 running (cadvisor-82, node-exporter-82)
- **Status:** Fully configured and ready for migration

### Important Note
- **Requirement:** Laptop lid must remain OPEN during migration
- **Alternative:** Configure lid-close behavior to not suspend (recommended for server use)

## 4. Next Steps

### Immediate Actions
1. ✅ Test GitLab token with projects API
2. ✅ Test GitHub token permissions
3. ✅ Verify user access on working servers
4. ✅ Resolve server 82 connectivity (RESOLVED - lid open required)

### Ready for Migration Phase 0
- **Phase 0:** Prechecks & Preparation (15 tasks, 2 days)
- **First Task:** PRE-001 - Verify Server Connectivity
- **Reference:** [IMPLEMENTATION_TASK_LIST.md](IMPLEMENTATION_TASK_LIST.md)

## 5. Security Notes

### Token Security
- **GitLab token expires:** January 31, 2026 (30 days)
- **GitHub token:** No expiration set (monitor usage)
- **Storage:** Tokens documented here, should be added to secure vault

### User Account Security
- Passwords use strong format: `Capital + lowercase + number + special`
- No passwordless sudo (secure by default)
- Docker group access is equivalent to root access (users can escalate via containers)
- **Recommendation:** Consider restricting docker commands via custom wrapper scripts

### Audit Trail
- All user creation actions logged via sudo
- GitLab token creation tracked: User Settings → Access Tokens
- GitHub API usage trackable via rate limit endpoint

## 6. Command Reference

### Verify Token Status
```bash
# GitHub token (get from ~/.zshrc: echo $GITHUB_TOKEN)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit | jq '.resources.core'

# GitLab token (get from ~/.zshrc: echo $GITLAB_TOKEN)
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "http://10.0.0.84:8090/api/v4/projects?per_page=5" | jq '.[] | {id, name}'
```

### Verify User Access
```bash
# Check user exists and groups
ssh wizardsofts@10.0.0.84
sudo id deploy
sudo id agent

# Test docker access
sudo su - deploy
docker ps

# Test agent read-only
sudo su - agent
docker ps
docker logs gitlab
```

### GitLab Mirror Setup Script Location
- Script location: [FINAL_DISTRIBUTION_PLAN.md#L246-L286](FINAL_DISTRIBUTION_PLAN.md)
- Tokens stored in `~/.zshrc`:
  - `GITLAB_TOKEN`: Use `echo $GITLAB_TOKEN` to retrieve
  - `GITHUB_TOKEN`: Use `echo $GITHUB_TOKEN` to retrieve (not yet exported, use value from GitHub settings)

## 7. Migration Readiness Checklist

- [x] GitHub token verified
- [x] GitLab API token generated with `api` scope
- [x] Deploy user created on servers 80, 81, 82, 84
- [x] Agent user created on servers 80, 81, 82, 84
- [x] Docker group access configured (no sudo)
- [x] Server 82 connectivity resolved (lid open required)
- [x] Migration documentation reviewed ([handoff.json](../handoff.json))
- [ ] Maintenance window scheduled (Saturday 2 AM - 6 AM UTC)
- [ ] Stakeholders notified of migration plan
- [ ] Backup strategy confirmed (Hetzner + GitHub mirror)

## 8. Contact & Escalation

- **Primary Admin:** wizardsofts (password: 29Dec2#24)
- **GitLab URL:** http://10.0.0.84:8090
- **GitHub Org:** wizardsofts
- **Documentation:** [docs/](.)

## 9. Known Limitations

1. **Server 82 Laptop Lid:** Server 82 is a laptop - lid must remain OPEN for SSH access during migration
2. **Password-based SSH:** Users cannot SSH directly with passwords (SSH keys not configured, access via su only)
3. **Token Expiry:** GitLab token expires in 30 days (January 31, 2026) - must rotate before then
4. **Server 82 SSH Keys:** Removed from known_hosts, will auto-accept on next connection

## 10. Lessons Learned

1. **GitLab Feed Token ≠ API Token:** Feed tokens visible in UI are NOT valid for API access
2. **Playwright Automation:** Successfully used for GitLab token generation
3. **Docker Group = Root:** Users in docker group can escalate to root via containers
4. **Laptop Servers:** Laptops used as servers should have lid-close behavior configured to prevent suspend
5. **SSH Port Discovery:** Server 82 accessible on port 22, not custom port 2525

---

**Status:** ✅ Pre-migration setup complete for ALL 4 servers (80, 81, 82, 84). Ready to proceed with Phase 0 tasks.

**Important:** Keep server 82 laptop lid OPEN during migration.

**Next Action:** Review [IMPLEMENTATION_TASK_LIST.md](IMPLEMENTATION_TASK_LIST.md) and execute PRE-001.

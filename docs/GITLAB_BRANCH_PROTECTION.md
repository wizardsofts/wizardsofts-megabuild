# GitLab Branch Protection Configuration

**Last Updated:** December 31, 2025
**Purpose:** Block direct pushes to master and require merge requests

---

## Overview

To ensure code quality and prevent accidental deployments, the `master` branch is protected with the following rules:
- **No direct pushes** - All changes must go through merge requests
- **Required approvals** - At least 1 approval required
- **CI/CD must pass** - All pipeline jobs must succeed before merge

---

## Configuration Steps

### Step 1: Access Protected Branches

1. Navigate to your GitLab project: http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild
2. Go to **Settings → Repository**
3. Expand **Protected branches**

### Step 2: Configure Master Branch Protection

| Setting | Value |
|---------|-------|
| **Branch** | `master` |
| **Allowed to merge** | Maintainers |
| **Allowed to push and merge** | No one |
| **Allowed to force push** | No |
| **Require approval from code owners** | Yes (if available) |

### Step 3: Configure Merge Request Settings

1. Go to **Settings → Merge requests**
2. Configure:

| Setting | Value |
|---------|-------|
| **Merge method** | Merge commit |
| **Squash commits when merging** | Encourage (optional) |
| **Merge checks** | Pipelines must succeed |
| **Merge checks** | All discussions must be resolved |
| **Approvals required** | 1 |

### Step 4: Add Push Rules (Optional but Recommended)

1. Go to **Settings → Repository → Push rules**
2. Configure:

| Setting | Value |
|---------|-------|
| **Reject unsigned commits** | Optional |
| **Do not allow users to remove Git tags** | Yes |
| **Prevent pushing secret files** | Yes |
| **Commit message regex** | `^(feat|fix|docs|style|refactor|test|chore|perf|security)(\(.+\))?:.*` |

---

## Git Worktree Workflow (Parallel Agent Support)

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

### Creating a Feature Branch with Worktree (PREFERRED)

```bash
# 1. Go to main repo and sync master
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git pull gitlab master

# 2. Create worktree directory if needed
mkdir -p ../wizardsofts-megabuild-worktrees

# 3. Create a new worktree with feature branch
git worktree add ../wizardsofts-megabuild-worktrees/my-feature -b feature/your-feature-name

# 4. Work in the worktree directory
cd ../wizardsofts-megabuild-worktrees/my-feature

# 5. Make changes, then commit
git add .
git commit -m "feat: add your feature description"

# 6. Push to GitLab
git push gitlab feature/your-feature-name

# 7. After MR merged, clean up worktree
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git worktree remove ../wizardsofts-megabuild-worktrees/my-feature
```

### Alternative: Simple Branch Method (Single Agent Only)

```bash
# If only one agent is working
git checkout master
git pull gitlab master
git checkout -b feature/your-feature-name
# ... make changes ...
git push gitlab feature/your-feature-name
```

### Managing Worktrees

```bash
# List all active worktrees
git worktree list

# Remove worktree after MR is merged
git worktree remove ../wizardsofts-megabuild-worktrees/my-feature

# Clean up stale references
git worktree prune
```

### Creating a Merge Request

1. Go to GitLab: http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild/-/merge_requests/new
2. Select source branch: `feature/your-feature-name`
3. Select target branch: `master`
4. Fill in:
   - Title: Descriptive summary
   - Description: What changed and why
   - Assignee: Yourself
   - Reviewer: Team member

### Merge Request Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2

## Testing Done
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have updated the documentation
- [ ] My changes don't introduce new warnings
- [ ] I have added tests for my changes
```

---

## Branch Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<description>` | `feature/add-auth-endpoint` |
| Bug Fix | `fix/<description>` | `fix/login-redirect` |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` |
| Infrastructure | `infra/<description>` | `infra/update-traefik` |
| Documentation | `docs/<description>` | `docs/update-readme` |
| Refactor | `refactor/<description>` | `refactor/signal-service` |
| Security | `security/<description>` | `security/add-rate-limiting` |

---

## AI Agent Workflow (Worktree Method - PREFERRED)

**CRITICAL**: All AI agents (Claude Code, Copilot, etc.) MUST follow this workflow:

### Starting a New Task with Worktree

```bash
# 1. Go to main repo and sync master
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git pull gitlab master

# 2. Create worktree directory if needed
mkdir -p ../wizardsofts-megabuild-worktrees

# 3. Create a new worktree with feature branch
git worktree add ../wizardsofts-megabuild-worktrees/task-name -b feature/task-description

# 4. Work in the worktree directory
cd ../wizardsofts-megabuild-worktrees/task-name

# 5. Make changes, then commit
git add .
git commit -m "feat: implement task description

Detailed explanation of changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# 6. Push to feature branch
git push gitlab feature/task-description

# 7. After MR merged, clean up worktree
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git worktree remove ../wizardsofts-megabuild-worktrees/task-name
```

### Why Worktrees for Multiple Agents?

- **Agent 1** works in `../wizardsofts-megabuild-worktrees/feature-auth/`
- **Agent 2** works in `../wizardsofts-megabuild-worktrees/fix-security/`
- **Agent 3** works in `../wizardsofts-megabuild-worktrees/infra-update/`

Each agent has isolated workspace, no conflicts!

### Never Do
- ❌ `git push gitlab master` - Direct push to master
- ❌ `git push -f gitlab master` - Force push to master
- ❌ Work directly on master branch
- ❌ Work in main repo when other agents might be using it

### Always Do
- ✅ Create a worktree for your feature branch
- ✅ Work in the worktree directory
- ✅ Push to feature branch only
- ✅ Create merge request
- ✅ Wait for CI/CD to pass
- ✅ Clean up worktree after MR merged

---

## Emergency Procedures

### If You Accidentally Push to Master

This should be blocked by branch protection, but if it happens:

```bash
# DO NOT force push to undo!
# Contact a maintainer immediately
# Document the incident
```

### Hotfix Workflow

For critical production issues:

```bash
# Create hotfix branch from master
git checkout master
git pull origin master
git checkout -b hotfix/critical-fix

# Make minimal fix
# Test thoroughly
# Push and create MR with "Priority: Critical" label

git push origin hotfix/critical-fix
```

Hotfix MRs can be expedited with maintainer approval.

---

## Verification

After configuring protection, verify:

```bash
# This should FAIL
git checkout master
git push origin master
# Expected: remote: GitLab: You are not allowed to push to protected branches

# This should WORK
git checkout -b test-branch
git push origin test-branch
```

---

## Related Documents

- [GITLAB_CICD_SECRETS.md](./GITLAB_CICD_SECRETS.md) - CI/CD variable configuration
- [SECURITY_IMPROVEMENTS_CHANGELOG.md](./SECURITY_IMPROVEMENTS_CHANGELOG.md) - Security changes
- [.gitlab/CODEOWNERS](../.gitlab/CODEOWNERS) - Code ownership rules

---

**Note**: These settings must be configured manually in GitLab UI. The configuration is not stored in the repository.

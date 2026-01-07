# Claude-Slack Integration POC

**Status:** Ready for Implementation
**Created:** 2026-01-01
**Author:** Claude Code Agent
**Project:** WizardSofts Megabuild

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Setup Instructions](#setup-instructions)
4. [POC Workflow Examples](#poc-workflow-examples)
5. [Architecture](#architecture)
6. [Integration with GitLab](#integration-with-gitlab)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This POC demonstrates how to integrate Claude with Slack to enable:
- ✅ Task assignment via @Claude mentions
- ✅ Automatic code analysis from Slack threads
- ✅ GitLab merge request creation from Slack
- ✅ Human review and approval workflows
- ✅ Integration with existing WizardSofts infrastructure

### Integration Options

We're implementing **two approaches** for comprehensive coverage:

| Approach | Use Case | Timeline |
|----------|----------|----------|
| **Official Claude Code in Slack** | Quick testing, simple tasks | **Phase 1** (Immediate) |
| **Custom Slack Bot (API-based)** | Production workflows, GitLab integration | **Phase 2** (Next) |

---

## Quick Start Guide

### Phase 1: Official Claude Code in Slack (5-10 minutes)

#### Prerequisites
- Slack workspace admin access (or ask admin to install)
- Claude Pro account ($20/month per user)
- Paid Slack plan

#### Step 1: Install Claude App in Slack

1. **Open Slack App Directory**
   ```
   https://wizardsofts.slack.com/apps
   ```

2. **Search for "Claude"**
   - In the search bar, type "Claude"
   - Select "Claude" by Anthropic (with blue Claude logo)
   - App URL: https://slack.com/marketplace/A08SF47R6P4-claude

3. **Install the App**
   - Click "Add to Slack"
   - Workspace admin will need to approve if you're not admin
   - Grant requested permissions:
     - Read messages
     - Post messages
     - Access channel information

4. **Authenticate Your Claude Account**
   - After installation, Slack will prompt you to authenticate
   - Click "Connect Claude Account"
   - Sign in to your Claude account (claude.ai)
   - Authorize Slack access

#### Step 2: Connect Repositories

1. **Go to Claude Code Web Interface**
   ```
   https://code.claude.com/
   ```

2. **Connect GitLab Repository**
   - Click "Connect Repository"
   - Select "GitLab" (if GitLab.com is supported, or use GitHub mirror)
   - **Note:** As of Jan 2026, Claude Code officially supports GitHub. For GitLab, you may need to:
     - Option A: Use GitHub as a mirror (sync GitLab → GitHub)
     - Option B: Wait for official GitLab support
     - Option C: Use custom API integration (Phase 2)

3. **Connect wizardsofts-megabuild Repository**
   - Select the repository
   - Grant access permissions
   - Choose which branches Claude can access (recommend: feature/* only)

#### Step 3: Test the Integration

1. **Create a Test Channel** (or use existing #development channel)
   ```
   Channel name: #claude-test
   ```

2. **Invite Claude to the Channel**
   ```
   /invite @Claude
   ```

3. **Test with a Simple Task**
   ```
   @Claude What is the purpose of the ws-gateway service?
   ```

   Expected response:
   - Claude analyzes the repository
   - Provides context-aware answer
   - May include code snippets or file references

4. **Test with a Code Task**
   ```
   @Claude In the ws-gateway service, add a health check endpoint
   at /actuator/health/custom that returns the current Git commit SHA.
   ```

   Expected workflow:
   - Claude creates a Claude Code session
   - Posts progress updates in thread
   - Shares link to review changes
   - Creates pull request (if GitHub is connected)

---

## Setup Instructions

### Manual Setup Steps for Slack Workspace Admins

#### 1. Install Claude App

1. **Navigate to Slack Admin Panel**
   - Go to https://wizardsofts.slack.com/admin
   - Click "Apps" in the left sidebar

2. **Manage App Installations**
   - Click "Manage Apps"
   - Search for "Claude"
   - Click "Request to Install" or "Install" (if you have permissions)

3. **Configure App Settings**
   - **Channels:** Allow Claude in specific channels or all channels
   - **Permissions:** Review and approve required permissions
   - **Data Access:** Understand what data Claude can access

#### 2. Set Up User Authentication

Each user who wants to use Claude needs to:

1. **Link Claude Account**
   - In Slack, find Claude in Apps
   - Click "Authenticate"
   - Sign in to claude.ai with your account

2. **Configure Preferences**
   - Choose which repositories Claude can access
   - Set notification preferences
   - Configure privacy settings

#### 3. Repository Connection Options

**Option A: GitHub Mirror (Recommended for Now)**

```bash
# On a server with access to both GitLab and GitHub
git clone ssh://git@10.0.0.84:2222/wizardsofts/wizardsofts-megabuild.git
cd wizardsofts-megabuild

# Add GitHub as a remote
git remote add github git@github.com:wizardsofts/wizardsofts-megabuild.git

# Set up automatic mirroring (using GitLab CI or cron)
# .gitlab-ci.yml
mirror-to-github:
  stage: deploy
  script:
    - git push github master --force
    - git push github --all
  only:
    - master
```

**Option B: Wait for GitLab Support**

Monitor Anthropic's announcements for official GitLab support.

**Option C: Custom Integration (Phase 2)**

Build custom Slack bot using Claude API (see Phase 2 Architecture section).

---

## POC Workflow Examples

### Example 1: Bug Report → Fix → MR

**Slack Thread:**

```
Developer: We're getting 500 errors on the /api/trades endpoint
when the market is closed. Error logs attached.
[attachment: error-logs.txt]

[React with :claude: emoji or mention]

@Claude Investigate and fix this error
```

**Claude Workflow:**

1. ✅ Claude reads the thread context (bug report + logs)
2. ✅ Identifies the repository (ws-trades or ws-gateway)
3. ✅ Creates a Claude Code session
4. ✅ Posts in thread:
   ```
   🔍 Analyzing error logs...
   Found issue in TradesController.java:142
   The endpoint doesn't check if market hours are valid.

   📝 Creating fix...
   [Link to Claude Code session]
   ```
5. ✅ Implements the fix
6. ✅ Runs tests (if configured)
7. ✅ Posts result:
   ```
   ✅ Fix complete!
   - Added market hours validation
   - Returns 400 Bad Request with helpful message when market closed
   - Added unit tests

   [Create Pull Request] [Review Code] [Cancel]
   ```

**Human Review:**

- Developer clicks "Review Code"
- Reviews changes in Claude Code web interface
- Clicks "Create Pull Request"
- MR created in GitHub (or GitLab via Phase 2 integration)

**Timeline:** 2-5 minutes from bug report to MR creation

---

### Example 2: Feature Request → Implementation

**Slack Thread:**

```
Product Manager: We need to add rate limiting to all public APIs.
Max 100 requests per minute per IP address.

Tech Lead: @Claude Can you implement this for ws-gateway?
Use spring-cloud-gateway's built-in rate limiter.
```

**Claude Workflow:**

1. ✅ Analyzes ws-gateway codebase
2. ✅ Identifies existing gateway configuration
3. ✅ Posts implementation plan:
   ```
   📋 Implementation Plan:
   1. Add Redis dependency for rate limit storage
   2. Configure RequestRateLimiter in application.yml
   3. Create custom KeyResolver for IP-based limiting
   4. Add rate limit headers to responses
   5. Update API documentation

   Proceed? [✅ Yes] [📝 Modify Plan] [❌ Cancel]
   ```

**Human Approval:**

- Tech Lead clicks "✅ Yes"

**Claude Continues:**

4. ✅ Implements changes across multiple files
5. ✅ Posts progress updates
6. ✅ Creates MR with description and testing checklist

**Timeline:** 5-10 minutes from request to reviewable MR

---

### Example 3: Code Review Assistance

**Slack Thread:**

```
Developer: Can someone review this MR?
https://gitlab.wizardsofts.com/wizardsofts/wizardsofts-megabuild/-/merge_requests/42

@Claude Please review this merge request and check for:
- Security issues
- Performance concerns
- Code style violations
```

**Claude Workflow:**

1. ✅ Fetches MR diff from GitLab (via Phase 2 integration)
2. ✅ Analyzes changes with security and performance focus
3. ✅ Posts review in thread:
   ```
   🔍 Code Review Summary

   ✅ Overall: Looks good with minor suggestions

   🔒 Security:
   - ⚠️ Line 23: User input not validated (SQL injection risk)
   - ✅ Authentication checks present

   ⚡ Performance:
   - ⚠️ Line 45: N+1 query detected (use JOIN instead)
   - ✅ Proper indexing used

   📝 Style:
   - ✅ Follows project conventions
   - ℹ️ Consider adding JavaDoc for public methods

   [View Detailed Report] [Approve MR] [Request Changes]
   ```

**Timeline:** 1-2 minutes for comprehensive review

---

### Example 4: Infrastructure Update

**Slack Thread:**

```
DevOps: We need to update all services to use the new Traefik
configuration with security headers.

@Claude Update docker-compose files and Traefik configs to add:
- HSTS headers
- X-Frame-Options: DENY
- CSP headers

Check docs/SECURITY_IMPROVEMENTS_CHANGELOG.md for examples.
```

**Claude Workflow:**

1. ✅ Reads security documentation
2. ✅ Identifies all docker-compose.*.yml files
3. ✅ Locates Traefik dynamic configs
4. ✅ Posts affected files list:
   ```
   📁 Files to Update (12 total):
   - docker-compose.appwrite.yml
   - docker-compose.services.yml
   - traefik/dynamic/security-headers.yml
   - ... (9 more)

   Proceed with batch update? [✅ Yes] [📝 Show Preview] [❌ Cancel]
   ```

**Human Review:**

- DevOps clicks "📝 Show Preview"
- Reviews proposed changes
- Clicks "✅ Approve"

**Claude Continues:**

5. ✅ Updates all files consistently
6. ✅ Creates single MR with organized commits
7. ✅ Generates deployment checklist

**Timeline:** 3-5 minutes for multi-file update

---

## Architecture

### Phase 1: Official Claude Code in Slack

```
┌─────────────────────────────────────────────────────────────┐
│                    Slack Workspace                          │
│  ┌────────────┐         ┌──────────────┐                   │
│  │ #development│         │  #bugs       │                   │
│  │             │         │              │                   │
│  │ @Claude... │───────▶ │  @Claude...  │                   │
│  └────────────┘         └──────────────┘                   │
│                               │                              │
└───────────────────────────────┼──────────────────────────────┘
                                │
                                │ (Mentions trigger)
                                ▼
                ┌───────────────────────────────┐
                │   Claude Slack App            │
                │   (Anthropic Hosted)          │
                │                               │
                │  • Extract task from thread   │
                │  • Gather context (messages)  │
                │  • Identify repository        │
                └───────────────┬───────────────┘
                                │
                                │ (Create session)
                                ▼
                ┌───────────────────────────────┐
                │   Claude Code Web             │
                │   (code.claude.com)           │
                │                               │
                │  • Clone repository           │
                │  • Execute task               │
                │  • Generate code changes      │
                └───────────────┬───────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
        ┌──────────────────┐    ┌──────────────────┐
        │  GitHub (Mirror) │    │  GitLab (Source) │
        │                  │    │  10.0.0.84:8090  │
        │  • Pull requests │◀───│  • Source truth  │
        │  • Code review   │    │  • CI/CD         │
        └──────────────────┘    └──────────────────┘
                                         │
                                         │ (Sync back)
                                         ▼
                            ┌──────────────────────┐
                            │   Production Servers │
                            │   • Server 84 (HP)   │
                            │   • Server 80, 81... │
                            └──────────────────────┘
```

### Phase 2: Custom Slack Bot Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Slack Workspace                          │
│  ┌────────────┐         ┌──────────────┐                   │
│  │ #development│         │  #bugs       │                   │
│  │             │         │              │                   │
│  │ @ClaudeBot │───────▶ │  @ClaudeBot  │                   │
│  └────────────┘         └──────────────┘                   │
│         │                       │                            │
└─────────┼───────────────────────┼────────────────────────────┘
          │                       │
          │ (Event subscription)  │
          ▼                       ▼
┌────────────────────────────────────────────────────────┐
│        Claude Slack Bot (Custom)                       │
│        Server 84: 10.0.0.84                            │
│        Docker Container                                │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Slack Event Handler                             │ │
│  │  • @mention events                               │ │
│  │  • Reaction events (:claude: emoji)              │ │
│  │  • Message threading                             │ │
│  └──────────────┬───────────────────────────────────┘ │
│                 │                                      │
│  ┌──────────────▼───────────────────────────────────┐ │
│  │  Context Analyzer                                │ │
│  │  • Extract task description                      │ │
│  │  • Gather thread messages                        │ │
│  │  • Identify affected services                    │ │
│  │  • Parse attachments (logs, screenshots)         │ │
│  └──────────────┬───────────────────────────────────┘ │
│                 │                                      │
│  ┌──────────────▼───────────────────────────────────┐ │
│  │  Claude API Client                               │ │
│  │  • Call Claude Opus/Sonnet API                   │ │
│  │  • Stream responses back to Slack                │ │
│  │  • Tool use support (code execution, search)     │ │
│  └──────────────┬───────────────────────────────────┘ │
│                 │                                      │
│  ┌──────────────▼───────────────────────────────────┐ │
│  │  GitLab Integration                              │ │
│  │  • Fetch MR diffs                                │ │
│  │  • Create feature branches                       │ │
│  │  • Commit changes                                │ │
│  │  • Create merge requests                         │ │
│  │  • Post MR comments                              │ │
│  └──────────────┬───────────────────────────────────┘ │
│                 │                                      │
│  ┌──────────────▼───────────────────────────────────┐ │
│  │  Approval Workflow Manager                       │ │
│  │  • Interactive Slack buttons                     │ │
│  │  • [✅ Approve] [🔍 Review] [❌ Reject]         │ │
│  │  • Track approval status                         │ │
│  │  • Execute on approval                           │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│           GitLab Instance                              │
│           http://10.0.0.84:8090                        │
│                                                         │
│  • wizardsofts-megabuild repository                    │
│  • CI/CD pipelines                                     │
│  • Merge request workflows                             │
│  • Container registry                                  │
└────────────────────────────────────────────────────────┘
               │
               │ (Deploy on merge)
               ▼
┌────────────────────────────────────────────────────────┐
│           Production Infrastructure                     │
│                                                         │
│  • Server 84 (HP): Appwrite, Services, GitLab          │
│  • Server 80: GIBD Services                            │
│  • Server 81: Database Server                          │
│  • Server 82: HPR Monitoring                           │
└────────────────────────────────────────────────────────┘
```

---

## Integration with GitLab

### Phase 2: Custom GitLab Integration

#### GitLab API Setup

1. **Create Personal Access Token**
   ```bash
   # In GitLab (http://10.0.0.84:8090)
   # User Settings → Access Tokens
   # Name: claude-slack-bot
   # Scopes: api, read_repository, write_repository
   # Expiration: 1 year
   ```

2. **Store Token in Environment**
   ```bash
   # On Server 84
   cd /opt/wizardsofts-megabuild/infrastructure/claude-slack-bot

   # .env file
   GITLAB_URL=http://10.0.0.84:8090
   GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
   GITLAB_PROJECT_ID=1  # wizardsofts-megabuild project ID
   ```

#### Automated MR Creation Workflow

```python
# Pseudocode for GitLab integration

async def create_merge_request_from_slack(slack_event):
    # 1. Extract task from Slack
    task_description = extract_task(slack_event)
    thread_context = get_thread_messages(slack_event)

    # 2. Call Claude API with repository context
    claude_response = await claude_api.generate_code(
        task=task_description,
        context=thread_context,
        repository_path="/path/to/repo"
    )

    # 3. Create feature branch in GitLab
    branch_name = f"feature/slack-{slack_event.timestamp}"
    gitlab.create_branch(
        project_id=PROJECT_ID,
        branch=branch_name,
        ref="master"
    )

    # 4. Commit Claude's changes
    for file_change in claude_response.changes:
        gitlab.create_commit(
            project_id=PROJECT_ID,
            branch=branch_name,
            commit_message=claude_response.commit_message,
            actions=[{
                "action": "update",
                "file_path": file_change.path,
                "content": file_change.content
            }]
        )

    # 5. Create merge request
    mr = gitlab.create_merge_request(
        project_id=PROJECT_ID,
        source_branch=branch_name,
        target_branch="master",
        title=task_description,
        description=claude_response.description
    )

    # 6. Post MR link back to Slack
    await slack.post_message(
        channel=slack_event.channel,
        thread_ts=slack_event.thread_ts,
        text=f"✅ Merge request created: {mr.web_url}",
        blocks=[
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": "Review MR", "url": mr.web_url},
                    {"type": "button", "text": "Approve & Merge", "action_id": "approve_mr"},
                    {"type": "button", "text": "Request Changes", "action_id": "request_changes"}
                ]
            }
        ]
    )
```

---

## Security Considerations

### Data Privacy

**What Claude Can Access:**
- ✅ Messages in channels where Claude is invited
- ✅ Code in connected repositories
- ✅ Thread context (recent messages)

**What Claude CANNOT Access:**
- ❌ Private DMs (unless explicitly shared)
- ❌ Channels where Claude is not invited
- ❌ Repositories not explicitly connected

### Best Practices

1. **Limit Channel Access**
   ```bash
   # Only invite Claude to development channels
   # DO: #development, #bugs, #feature-requests
   # DON'T: #hr, #finance, #customer-data
   ```

2. **Sensitive Data Handling**
   - Never post API keys, passwords, or credentials in Slack threads
   - Use GitLab CI/CD secrets instead of hardcoding
   - Review Claude's proposed changes before merging

3. **Repository Permissions**
   - Connect only necessary repositories
   - Use feature/* branch restrictions
   - Require human approval before merging to master

4. **Audit Logging**
   ```bash
   # Track Claude's actions
   # Slack: Export channel history periodically
   # GitLab: Review Claude bot's commit history
   ```

### Security Checklist

- [ ] Claude only has access to development channels
- [ ] All repositories use branch protection on master
- [ ] CI/CD pipeline includes security scans (gitleaks, dependency-check)
- [ ] Rate limiting configured on Claude API calls
- [ ] Audit logs reviewed monthly
- [ ] Team trained on what NOT to share in Claude threads

---

## Troubleshooting

### Issue 1: Claude Not Responding to @mentions

**Symptoms:**
- @Claude mention doesn't trigger any response
- No typing indicator appears

**Solutions:**

1. **Check if Claude is in the channel**
   ```
   /invite @Claude
   ```

2. **Verify authentication**
   - Go to Slack Apps → Claude → "Re-authenticate"

3. **Check Slack App permissions**
   - Ensure Claude has permission to read/write in the channel

4. **Try direct message**
   - DM @Claude with a test message
   - If DM works but channel doesn't, it's a permission issue

---

### Issue 2: Repository Not Found

**Symptoms:**
- Claude responds: "I couldn't find the repository associated with this channel"

**Solutions:**

1. **Connect repository in Claude Code**
   - Go to https://code.claude.com/
   - Click "Connect Repository"
   - Authenticate with GitHub/GitLab

2. **Specify repository in message**
   ```
   @Claude In the wizardsofts-megabuild repository,
   add a health check endpoint to ws-gateway
   ```

3. **Use repository hints**
   - Mention file paths: `ws-gateway/src/main/java/...`
   - Reference existing code: "In the TradesController class..."

---

### Issue 3: GitLab Integration Not Working (Phase 2)

**Symptoms:**
- Claude creates code but doesn't push to GitLab
- MR creation fails

**Solutions:**

1. **Check GitLab token**
   ```bash
   # On Server 84
   docker logs claude-slack-bot | grep "GitLab auth"
   ```

2. **Verify network connectivity**
   ```bash
   # From Claude bot container
   curl http://10.0.0.84:8090/api/v4/projects
   ```

3. **Check project ID**
   ```bash
   # Get correct project ID
   curl -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
     http://10.0.0.84:8090/api/v4/projects?search=wizardsofts-megabuild
   ```

4. **Review bot logs**
   ```bash
   docker logs claude-slack-bot -f --tail 100
   ```

---

### Issue 4: Approval Buttons Not Working

**Symptoms:**
- Clicking [✅ Approve] button does nothing
- No feedback after clicking

**Solutions:**

1. **Check Slack interactivity settings**
   - Slack API → Interactivity & Shortcuts
   - Verify Request URL is correct

2. **Review bot logs for errors**
   ```bash
   docker logs claude-slack-bot | grep "interaction"
   ```

3. **Test webhook endpoint**
   ```bash
   curl -X POST http://10.0.0.84:3000/slack/interactions \
     -H "Content-Type: application/json" \
     -d '{"type":"block_actions","actions":[{"action_id":"approve_mr"}]}'
   ```

---

### Issue 5: Rate Limiting / Quota Exceeded

**Symptoms:**
- Claude responds: "I've reached my usage limit"
- 429 errors in logs

**Solutions:**

1. **Check Claude Pro subscription**
   - Ensure subscription is active
   - Verify usage limits at claude.ai/account

2. **Implement request queuing** (Phase 2)
   ```python
   # Add rate limiting to bot
   from slowapi import Limiter

   limiter = Limiter(key_func=lambda: slack_workspace_id)

   @limiter.limit("10/minute")
   async def handle_claude_request(event):
       # Process request
   ```

3. **Monitor API usage**
   ```bash
   # Track API calls in Prometheus/Grafana
   claude_api_calls_total{status="success"}
   claude_api_calls_total{status="rate_limited"}
   ```

---

## Next Steps

### Immediate Actions (Phase 1)

1. **Install Claude App in Slack** (5 minutes)
   - [ ] Request admin to install Claude app
   - [ ] Authenticate with your Claude account
   - [ ] Test in #claude-test channel

2. **Set Up Repository Connection** (10 minutes)
   - [ ] Decide: GitHub mirror or wait for GitLab support
   - [ ] Connect repository to Claude Code
   - [ ] Grant appropriate permissions

3. **Run POC Tests** (30 minutes)
   - [ ] Test bug fix workflow (Example 1)
   - [ ] Test feature request workflow (Example 2)
   - [ ] Test code review workflow (Example 3)
   - [ ] Document results

### Future Implementation (Phase 2)

1. **Build Custom Slack Bot** (See [CLAUDE_SLACK_CUSTOM_BOT.md](CLAUDE_SLACK_CUSTOM_BOT.md))
   - [ ] Set up development environment
   - [ ] Implement Slack event handlers
   - [ ] Integrate Claude API
   - [ ] Connect to GitLab API
   - [ ] Deploy to Server 84

2. **Production Hardening**
   - [ ] Add authentication and authorization
   - [ ] Implement rate limiting
   - [ ] Set up monitoring and alerting
   - [ ] Create runbooks for incidents

3. **Team Training**
   - [ ] Document best practices
   - [ ] Train team on effective Claude usage
   - [ ] Establish guidelines for task assignments

---

## Additional Resources

- [Claude Code Documentation](https://code.claude.com/docs)
- [Slack API Documentation](https://api.slack.com/)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
- [WizardSofts Security Guidelines](../CLAUDE.md#security-guidelines)

---

## Feedback & Contributions

This is a living document. Please update with:
- New workflows discovered
- Troubleshooting solutions
- Integration improvements

**Document Maintained By:** DevOps Team
**Last Updated:** 2026-01-01

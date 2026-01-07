# Claude + Slack Integration - Quick Reference

**Date:** 2026-01-01
**Status:** Phase 1 Complete ✓ | Phase 2 Ready for Deployment
**Workspace:** wizardsofts.slack.com

---

## What's Been Set Up

### ✅ Phase 1: Official Claude Code in Slack (INSTALLED)

The official Claude app from Anthropic is now installed in the WizardSofts Slack workspace.

**What This Enables:**
- Assign coding tasks directly from Slack conversations
- Claude analyzes thread context automatically
- Generates code changes and creates pull requests
- Human review and approval workflows
- No server maintenance required

**Cost:** Included with Claude Pro subscription ($20/user/month)

---

## Quick Start Guide

### 1. Authenticate Your Claude Account (One-Time)

After the app is installed, each user needs to link their Claude account:

1. Find the Claude app in Slack Apps
2. Click "Authenticate"
3. Sign in to claude.ai
4. Authorize Slack access

### 2. Connect Your Repositories

Go to https://code.claude.com/ and connect repositories:

**For WizardSofts:**
- Option A: Use GitHub mirror (if available)
- Option B: Wait for official GitLab support
- Option C: Use custom bot (Phase 2) for direct GitLab integration

### 3. Start Using Claude in Slack

**Invite Claude to a channel:**
```
/invite @Claude
```

**Ask Claude to do something:**
```
@Claude add a health check endpoint to ws-gateway
that returns the current Git commit SHA
```

**Claude will:**
1. Analyze your repository
2. Generate the code changes
3. Post a preview for your review
4. Create a pull request on approval

---

## Example Workflows

### Bug Fix Workflow

```
# 1. Developer reports bug in #bugs channel
User: The /api/trades endpoint is returning 500 errors
when the market is closed.
[Attaches error logs]

# 2. Tech lead assigns to Claude
Tech Lead: @Claude investigate and fix this error

# 3. Claude analyzes and responds
Claude: 🔍 I found the issue in TradesController.java:142
The endpoint doesn't validate market hours.

Proposed fix:
- Add market hours validation
- Return 400 Bad Request with helpful message
- Add unit tests

[View Changes] [Create MR] [Cancel]

# 4. Human reviews and approves
Tech Lead: [Clicks "Create MR"]

# 5. MR created, CI runs, ready for merge
Claude: ✅ MR created: gitlab.com/.../merge_requests/123
```

**Time Saved:** 5-10 minutes from bug report to reviewable MR

### Feature Request Workflow

```
# 1. Product manager requests feature
PM: We need to add rate limiting to all public APIs.
Max 100 requests per minute per IP.

# 2. Tech lead assigns with specifics
Tech Lead: @Claude Implement this for ws-gateway.
Use spring-cloud-gateway's RequestRateLimiter with Redis.

# 3. Claude presents implementation plan
Claude: 📋 Implementation Plan:
1. Add Redis dependency
2. Configure RequestRateLimiter in application.yml
3. Create IP-based KeyResolver
4. Add rate limit headers
5. Update API docs

Proceed? [✅ Yes] [📝 Modify] [❌ Cancel]

# 4. Approval and implementation
Tech Lead: [Clicks "Yes"]

Claude: 🚀 Implementing changes...
[Progress updates in thread]
✅ MR created with 5 file changes
```

**Time Saved:** 10-15 minutes from request to reviewable implementation

### Code Review Workflow

```
# 1. Developer requests review
Dev: Can someone review this MR?
https://gitlab.wizardsofts.com/.../merge_requests/42

@Claude check for security issues and performance concerns

# 2. Claude analyzes and provides feedback
Claude: 🔍 Code Review Summary

✅ Overall: Looks good with minor suggestions

🔒 Security:
- ⚠️ Line 23: User input not validated (SQL injection risk)
- ✅ Authentication checks present

⚡ Performance:
- ⚠️ Line 45: N+1 query detected
- Suggestion: Use JOIN instead of loop

📝 Style:
- ✅ Follows conventions
- ℹ️ Consider adding JavaDoc

[View Details] [Approve] [Request Changes]
```

**Time Saved:** 2-3 minutes for comprehensive review

---

## What's in This POC

### Documentation Created

| File | Description |
|------|-------------|
| [CLAUDE_SLACK_POC.md](CLAUDE_SLACK_POC.md) | Complete setup guide (50+ pages) |
| [CLAUDE_SLACK_CUSTOM_BOT.md](CLAUDE_SLACK_CUSTOM_BOT.md) | Custom bot implementation guide |
| [CLAUDE_SLACK_README.md](CLAUDE_SLACK_README.md) | This quick reference |
| [../CLAUDE.md](../CLAUDE.md) | Updated with integration instructions |

### Phase 2 Architecture (Ready to Deploy)

A custom Slack bot for advanced workflows:

**Features:**
- Direct GitLab API integration (no GitHub needed)
- Deployed on Server 84 (10.0.0.84)
- Custom approval workflows
- Prometheus metrics & Grafana dashboards
- Full cost control with rate limiting

**Deployment:**
```bash
cd /opt/wizardsofts-megabuild/infrastructure/claude-slack-bot
docker-compose up -d
```

**Cost:** ~$15-50/month (Claude API usage based)

---

## Security Guidelines

### ✅ DO:
- Invite Claude to development channels (#development, #bugs)
- Review all proposed changes before merging
- Monitor API usage and costs
- Set budget alerts in Anthropic console

### ❌ DON'T:
- Invite Claude to #hr, #finance, or customer data channels
- Share API keys, passwords, or credentials in threads
- Merge changes without reviewing
- Post production database connection strings

### Data Access:
Claude can access:
- Messages in channels where it's invited
- Code in connected repositories
- Thread context (recent messages)

Claude CANNOT access:
- Private DMs (unless explicitly shared)
- Channels where it's not invited
- Repositories not connected

---

## Troubleshooting

### Claude doesn't respond to mentions

**Solution 1:** Ensure Claude is in the channel
```
/invite @Claude
```

**Solution 2:** Re-authenticate
- Slack → Apps → Claude → "Re-authenticate"

**Solution 3:** Check permissions
- Ask Slack admin to verify Claude app has required scopes

### "Repository not found" error

**Solution:** Specify repository explicitly
```
@Claude In the wizardsofts-megabuild repository,
add a health check to ws-gateway
```

Or ensure repository is connected at https://code.claude.com/

### Claude creates code but doesn't push to GitLab

**Current Limitation:** Official app supports GitHub primarily.

**Solutions:**
- Option A: Set up GitHub mirror (sync GitLab → GitHub)
- Option B: Deploy custom bot (Phase 2) for direct GitLab
- Option C: Wait for official GitLab support from Anthropic

---

## Next Steps

### Immediate (This Week)

1. **Team Onboarding**
   - [ ] All developers authenticate their Claude accounts
   - [ ] Connect repositories (or set up GitHub mirror)
   - [ ] Test in #claude-test channel

2. **First Real Task**
   - [ ] Pick a small bug or feature
   - [ ] Assign to Claude in Slack
   - [ ] Review the workflow
   - [ ] Document learnings

3. **Set Usage Limits**
   - [ ] Configure budget alerts in Anthropic console
   - [ ] Set monthly spend limit ($100 suggested)
   - [ ] Monitor usage weekly

### Short-Term (Next Month)

1. **Expand Usage**
   - [ ] Use Claude for code reviews
   - [ ] Integrate with bug reports
   - [ ] Create standard templates for common tasks

2. **Evaluate Phase 2**
   - [ ] Assess need for custom bot
   - [ ] If GitLab integration is critical, deploy custom bot
   - [ ] Compare costs and benefits

3. **Team Training**
   - [ ] Document best practices
   - [ ] Share success stories
   - [ ] Create usage guidelines

### Long-Term (3-6 Months)

1. **Automation**
   - [ ] Auto-assign certain bug types to Claude
   - [ ] Integrate with CI/CD for deployment approvals
   - [ ] Create custom workflows for common patterns

2. **Metrics**
   - [ ] Track time saved per task
   - [ ] Measure code quality improvements
   - [ ] Calculate ROI

3. **Scale**
   - [ ] Expand to more teams
   - [ ] Add more repositories
   - [ ] Optimize costs and usage

---

## Support & Feedback

### Getting Help

1. **Documentation:** Check [CLAUDE_SLACK_POC.md](CLAUDE_SLACK_POC.md) troubleshooting section
2. **Slack:** Ask in #development channel
3. **Anthropic Support:** https://support.anthropic.com/

### Reporting Issues

Create an issue in the megabuild repository:
```bash
# GitLab
http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild/-/issues/new

Labels: claude-integration, slack-bot
```

### Suggesting Improvements

Share feedback in #development or create a feature request MR.

---

## Summary

### What Works Today (Phase 1)

✅ Claude app installed in Slack
✅ @mention task assignment
✅ Automatic code generation
✅ Pull request creation
✅ Human approval workflows
✅ No server maintenance

### What's Ready to Deploy (Phase 2)

✅ Custom bot architecture documented
✅ Direct GitLab integration code ready
✅ Docker deployment configs
✅ Monitoring & observability setup
✅ Security best practices implemented

### Cost Estimate

| Component | Monthly Cost |
|-----------|-------------|
| Claude Pro (per user) | $20 |
| Claude API (custom bot) | $15-50 |
| Infrastructure | $0 (using Server 84) |
| **Total per user** | **$20-70/month** |

### Time Savings Estimate

Based on example workflows:
- Bug fix: 5-10 minutes saved
- Feature implementation: 10-15 minutes saved
- Code review: 2-3 minutes saved

**Potential ROI:**
- 10 tasks/day/team × 10 min savings = 100 min/day
- 100 min × 20 workdays = 2,000 min/month = **33 hours/month**
- At $50/hour developer rate = **$1,650 savings/month**
- Cost: $70/month
- **ROI: 23x**

---

**Document Version:** 1.0
**Created:** 2026-01-01
**Status:** Complete ✓
**Next Review:** 2026-02-01

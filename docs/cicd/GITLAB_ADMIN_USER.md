# GitLab Admin User - mashfiqur.rahman

**Last Updated:** 2026-01-05
**GitLab URL:** http://10.0.0.84:8090
**Status:** ✅ Configured and Active

---

## User Details

**Username:** `mashfiqur.rahman`
**Email:** `engg.mashfiqur@gmail.com`
**Name:** Mashfiqur Rahman
**Role:** Administrator
**Status:** Active & Confirmed

**Password:** `czzn&1oXHqQxN1T$DFW=*B&Q`

⚠️ **IMPORTANT:** Change this password after first login:
1. Login to GitLab: http://10.0.0.84:8090
2. Go to User Settings → Password
3. Set a new secure password

---

## Permissions & Capabilities

### ✅ Full Admin Access

As a GitLab Administrator, this user can:

**Merge Request Management:**
- ✅ Create merge requests
- ✅ Review merge requests
- ✅ Approve merge requests
- ✅ Merge to any branch (including protected branches)
- ✅ Manage merge request approvals

**CI/CD Pipeline Management:**
- ✅ View all pipelines
- ✅ Modify `.gitlab-ci.yml` files
- ✅ Trigger manual pipelines
- ✅ Retry/Cancel pipelines
- ✅ Configure pipeline schedules

**GitLab Variables:**
- ✅ View all project/group variables
- ✅ Create/Update/Delete variables
- ✅ Manage protected/masked variables
- ✅ Access environment-specific variables

**GitLab Runner Management:**
- ✅ View all runners (shared & specific)
- ✅ Register new runners
- ✅ Configure runner settings
- ✅ Enable/Disable runners
- ✅ Manage runner tags

**Repository Access:**
- ✅ Full access to all repositories
- ✅ Clone/Pull/Push to any branch
- ✅ Manage protected branches
- ✅ Force push (use with caution)

---

## Group Memberships

| Group | Access Level |
|-------|--------------|
| **wizardsofts** | Owner |
| **gibd** | Owner |
| **dailydeenguide** | Owner |

---

## Project Access

**Full Owner access to:**
- wizardsofts/wizardsofts-megabuild
- wizardsofts/mymuezzin
- wizardsofts/gibd-news-service
- wizardsofts/www.wizardsofts.com
- gibd/gibd-web-scraper
- gibd/quant-flow
- gibd/gibd-config
- gibd/mcp-financial-tools
- gibd/gibd-discovery-service
- gibd/gibd-gateway
- gibd/gibd-intelligence
- And all other projects in the groups

---

## Common Tasks

### Login to GitLab

```bash
# Web UI
http://10.0.0.84:8090

# Username: mashfiqur.rahman
# Password: czzn&1oXHqQxN1T$DFW=*B&Q (change after first login)
```

### Create Merge Request

1. Push your branch to GitLab
2. Go to repository → Merge Requests → New Merge Request
3. Select source and target branches
4. Fill in title and description
5. Assign reviewers if needed
6. Click "Create merge request"

### Update CI/CD Variables

```bash
# Via Web UI:
# Project Settings → CI/CD → Variables → Expand → Add Variable

# Via GitLab API:
curl --request POST "http://10.0.0.84:8090/api/v4/projects/:id/variables" \
  --header "PRIVATE-TOKEN: <your-access-token>" \
  --form "key=NEW_VARIABLE" \
  --form "value=new_value"
```

### Manage GitLab Runners

```bash
# View runners
Admin Area → Overview → Runners

# Register new runner
sudo gitlab-runner register \
  --url http://10.0.0.84:8090 \
  --registration-token <token-from-gitlab>
```

### Modify CI/CD Pipeline

Edit `.gitlab-ci.yml` in your repository:
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - echo "Building..."
```

---

## Security Best Practices

### Password Management

1. ✅ Change default password immediately
2. ✅ Use a password manager (1Password, Bitwarden, etc.)
3. ✅ Enable 2FA (Two-Factor Authentication):
   - User Settings → Account → Two-Factor Authentication
4. ❌ Never commit passwords to git
5. ❌ Never share password in chat/email

### Access Token Management

**Create Personal Access Token:**
1. User Settings → Access Tokens
2. Name: "API Access" or descriptive name
3. Scopes: `api`, `read_repository`, `write_repository`
4. Click "Create personal access token"
5. **Save the token immediately** (shown only once)

**Use token for API/Git operations:**
```bash
# Git clone with token
git clone http://mashfiqur.rahman:<token>@10.0.0.84:8090/wizardsofts/project.git

# API request with token
curl --header "PRIVATE-TOKEN: <token>" \
  "http://10.0.0.84:8090/api/v4/projects"
```

### Protected Branches

**Configure protected branches:**
1. Repository → Settings → Repository → Protected Branches
2. Select branch (e.g., `master`, `main`)
3. Allowed to merge: Maintainers + Developers
4. Allowed to push: No one (force MRs)
5. Require approval: 1-2 approvals

---

## API Access

### Get User Info

```bash
curl --header "PRIVATE-TOKEN: <token>" \
  "http://10.0.0.84:8090/api/v4/user"
```

### List Projects

```bash
curl --header "PRIVATE-TOKEN: <token>" \
  "http://10.0.0.84:8090/api/v4/projects?owned=true"
```

### Trigger Pipeline

```bash
curl --request POST \
  --form token=<pipeline-token> \
  --form ref=master \
  "http://10.0.0.84:8090/api/v4/projects/:id/trigger/pipeline"
```

---

## Troubleshooting

### Can't Login

**Check GitLab status:**
```bash
ssh agent@10.0.0.84 'sudo docker exec gitlab gitlab-ctl status'
```

**Reset password via Rails console:**
```bash
ssh agent@10.0.0.84 "sudo docker exec -i gitlab gitlab-rails runner - << 'RUBY'
user = User.find_by(username: 'mashfiqur.rahman')
user.password = 'NewSecurePassword123!'
user.password_confirmation = 'NewSecurePassword123!'
user.save(validate: false)
puts \"Password reset successfully\"
RUBY
"
```

### Locked Out of Admin Area

```bash
# Confirm user account
ssh agent@10.0.0.84 "sudo docker exec -i gitlab gitlab-rails runner - << 'RUBY'
user = User.find_by(username: 'mashfiqur.rahman')
user.confirm
user.save(validate: false)
puts \"User confirmed\"
RUBY
"
```

### Can't Access Repository

**Check project membership:**
```bash
ssh agent@10.0.0.84 "sudo docker exec -i gitlab gitlab-rails runner - << 'RUBY'
user = User.find_by(username: 'mashfiqur.rahman')
project = Project.find_by_full_path('wizardsofts/project-name')
puts \"Access level: #{project.team.max_member_access(user.id)}\"
RUBY
"
```

---

## Related Documentation

- [GitLab CI/CD Documentation](http://10.0.0.84:8090/help/ci/README.md)
- [GitLab API Documentation](http://10.0.0.84:8090/help/api/README.md)
- [GitLab Runner Documentation](http://10.0.0.84:8090/help/ci/runners/README.md)
- [GITLAB_DEPLOYMENT.md](GITLAB_DEPLOYMENT.md) - GitLab deployment guide
- [GITLAB_BRANCH_PROTECTION.md](GITLAB_BRANCH_PROTECTION.md) - Branch protection rules

---

**User Created:** 2026-01-05
**Last Password Update:** 2026-01-05
**Access Level:** Administrator (Full Access)

⚠️ **Remember to change the default password after your first login!**

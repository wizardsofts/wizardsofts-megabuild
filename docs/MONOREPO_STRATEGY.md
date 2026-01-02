# WizardSofts Megabuild - Monorepo Strategy

**Decision Date:** December 31, 2025
**Status:** Approved - Keep Monorepo with Logical Separation
**Review Date:** Q2 2025

---

## Executive Summary

After analyzing the repository structure, commit patterns, and team dynamics, the recommendation is to **maintain a single monorepo** with logical separation through CODEOWNERS, split CI/CD pipelines, and proper access controls.

---

## Analysis

### Repository Metrics

| Component | Size | Commits (2024-2025) | Change Frequency |
|-----------|------|---------------------|------------------|
| apps/ | 13GB | 29 | Low-Medium |
| infrastructure/ | 1MB | 43 | Medium-High |
| traefik/ | 20KB | (included above) | Low |
| **Total** | 13GB | 117 | - |

### Decision Factors

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Team Size | High | Keep | Small team, coordination overhead not justified |
| Repo Size | Medium | Keep | 99.9% is apps, infra is negligible |
| Security | High | Split Logic | Implement CODEOWNERS + protected branches |
| Local Dev | High | Keep | Need both to run full stack |
| Deployment Coupling | Medium | Keep | App changes often require infra changes |
| Access Control | High | Split Logic | CODEOWNERS provides sufficient control |

---

## Implemented Solution

### 1. CODEOWNERS Access Control

```
/.gitlab/CODEOWNERS

# Infrastructure - requires senior/devops review
/infrastructure/       @devops-team @tech-lead
/traefik/             @devops-team @tech-lead
docker-compose*.yml    @devops-team @tech-lead
.gitlab-ci.yml        @devops-team @tech-lead
.env*                 @devops-team @tech-lead

# Applications - developer access
/apps/                @dev-team
```

### 2. Split CI/CD Pipelines

```
.gitlab/
├── ci/
│   ├── apps.gitlab-ci.yml      # Application builds and deployments
│   ├── infra.gitlab-ci.yml     # Infrastructure deployments
│   └── security.gitlab-ci.yml  # Security scanning
└── CODEOWNERS
```

### 3. Secrets Management

| Secret Type | Storage Location | Access |
|-------------|------------------|--------|
| Database passwords | GitLab CI/CD Variables (masked, protected) | CI/CD only |
| API keys | GitLab CI/CD Variables (masked, protected) | CI/CD only |
| SSH keys | GitLab CI/CD Variables (file, protected) | CI/CD only |
| Application secrets | Keycloak / Environment variables | Runtime |

---

## Future Triggers for Splitting

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Team size | >10 developers | Re-evaluate split |
| Kubernetes adoption | Any | Strongly consider split |
| Compliance (SOC2/ISO) | Required | May mandate split |
| Release cadence divergence | Significant | Consider split |

---

## Rollback Plan

If the monorepo approach proves problematic:

1. Create `wizardsofts-platform` repo for infrastructure
2. Create `wizardsofts-apps` repo for applications
3. Migrate CI/CD pipelines separately
4. Update local development scripts
5. Sync environment variable templates

---

## Related Documents

- [ARCHITECTURAL_REVIEW_REPORT_v2.md](./ARCHITECTURAL_REVIEW_REPORT_v2.md) - Full security and architecture review
- [GITLAB_CICD_SECRETS.md](./GITLAB_CICD_SECRETS.md) - Secrets management guide
- [CODEOWNERS](./../.gitlab/CODEOWNERS) - Access control configuration

---

**Approved By:** Architecture Team
**Implementation Date:** December 31, 2025

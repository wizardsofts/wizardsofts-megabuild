# CI/CD Documentation

GitLab CI/CD pipelines, runners, and automation.

## Contents

| Document | Description |
|----------|-------------|
| [gitlab-pipelines.md](gitlab-pipelines.md) | Pipeline configuration |
| [gitlab-runners.md](gitlab-runners.md) | Runner setup and management |
| [branch-protection.md](branch-protection.md) | Branch protection rules |
| [github-sync.md](github-sync.md) | GitLab to GitHub mirroring |

## GitLab Access

| Resource | URL |
|----------|-----|
| GitLab | http://10.0.0.84:8090 |
| Registry | http://10.0.0.84:5050 |
| SSH | Port 2222 |

## Pipeline Quick Reference

```yaml
# Example .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

## Branch Protection

- **master** - Protected, requires merge request
- Direct pushes to master are **BLOCKED**
- All changes must go through merge requests

## Related Documentation

- [Deployment](../deployment/) - Service deployment
- [Security](../security/) - Pipeline security
- [CLAUDE.md - Git Worktree Workflow](../../CLAUDE.md#git-worktree-workflow---mandatory-parallel-agent-support)

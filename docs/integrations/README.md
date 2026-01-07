# Integrations Documentation

Third-party integrations and external service connections.

## Contents

| Document | Description |
|----------|-------------|
| [claude-slack.md](claude-slack.md) | Claude + Slack integration |
| [dns-setup.md](dns-setup.md) | HostGator DNS configuration |
| [oauth2-sso.md](oauth2-sso.md) | Keycloak OAuth2/OIDC setup |

## Active Integrations

| Integration | Status | Documentation |
|-------------|--------|---------------|
| Claude + Slack | Active | [claude-slack.md](claude-slack.md) |
| Keycloak OAuth2 | Active | [oauth2-sso.md](oauth2-sso.md) |
| GitHub Mirroring | Active | [../cicd/github-sync.md](../cicd/github-sync.md) |

## Claude Slack Integration

The Claude app is installed in the WizardSofts Slack workspace.

**Usage:**
```
@Claude add a health check endpoint to ws-gateway
```

**Setup:** See [claude-slack.md](claude-slack.md)

## Related Documentation

- [Deployment](../deployment/) - Service deployment
- [Security](../security/) - OAuth2 security

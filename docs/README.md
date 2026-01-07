# WizardSofts Megabuild Documentation

> Central documentation hub for the WizardSofts monorepo.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture](architecture/) | System design, monorepo strategy, distributed ML |
| [Deployment](deployment/) | Service deployment guides (Appwrite, GitLab, Traefik, etc.) |
| [Operations](operations/) | SRE runbook, troubleshooting, maintenance |
| [Security](security/) | Hardening, secrets management, firewall rules |
| [CI/CD](cicd/) | GitLab pipelines, runners, branch protection |
| [Integrations](integrations/) | Claude Slack, OAuth2/SSO, DNS setup |
| [Data Pipelines](data-pipelines/) | GIBD news, indicator backfill, data cache |
| [Handoffs](handoffs/) | Session handoff documents |
| [Archive](archive/) | Historical docs, completed migrations, audits |

## Getting Started

1. **New Developer?** Start with [QUICK_START.md](QUICK_START.md)
2. **Deploying a service?** See [deployment/](deployment/)
3. **On-call/SRE?** See [operations/](operations/)
4. **Security question?** See [security/](security/)

## Root-Level Documentation

These files live in the repository root:

| File | Purpose |
|------|---------|
| [README.md](../README.md) | Project overview |
| [CLAUDE.md](../CLAUDE.md) | Claude AI assistant instructions |
| [AGENT.md](../AGENT.md) | Universal agent instructions |
| [CONSTITUTION.md](../CONSTITUTION.md) | Project principles and governance |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines |

## App-Specific Documentation

Each app has its own documentation in `apps/{app-name}/`:

| App | Location | Description |
|-----|----------|-------------|
| gibd-quant-agent | [apps/gibd-quant-agent/](../apps/gibd-quant-agent/) | Quantitative trading ML agent |
| gibd-quant-web | [apps/gibd-quant-web/](../apps/gibd-quant-web/) | Trading dashboard frontend |
| gibd-news | [apps/gibd-news/](../apps/gibd-news/) | Stock data pipeline |
| ws-gateway | [apps/ws-gateway/](../apps/ws-gateway/) | API Gateway (Spring Boot) |
| ws-daily-deen-web | [apps/ws-daily-deen-web/](../apps/ws-daily-deen-web/) | Daily Deen Guide frontend |

## Documentation Standards

See [AGENT.md - Documentation Structure](../AGENT.md#documentation-structure) for:
- Where to place new documentation
- Naming conventions
- Required sections for each doc type

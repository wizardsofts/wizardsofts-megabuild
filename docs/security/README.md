# Security Documentation

Security policies, hardening guides, and incident response procedures.

## Contents

| Document | Description |
|----------|-------------|
| [hardening-guide.md](hardening-guide.md) | Server hardening procedures |
| [fail2ban-setup.md](fail2ban-setup.md) | Intrusion prevention setup |
| [firewall-rules.md](firewall-rules.md) | UFW configuration |
| [secrets-management.md](secrets-management.md) | GitLab CI/CD secrets |
| [vulnerability-scanning.md](vulnerability-scanning.md) | Security scanning procedures |

## Security Policy

All code changes must:
1. Pass security scanning (pip-audit, npm audit)
2. Not introduce hardcoded credentials
3. Use parameterized queries (no SQL injection)
4. Validate all user input

## Quick Security Checks

```bash
# Check fail2ban status (Server 84)
ssh agent@10.0.0.84 'sudo fail2ban-client status sshd'

# View banned IPs
ssh agent@10.0.0.84 'sudo fail2ban-client status sshd | grep "Banned IP"'

# Check UFW status
ssh agent@10.0.0.84 'sudo ufw status'

# Run security scan on Python dependencies
pip-audit --desc
```

## Incident Response

1. **Identify** - Determine scope of incident
2. **Contain** - Isolate affected systems
3. **Eradicate** - Remove threat
4. **Recover** - Restore services
5. **Document** - Record in [../archive/retrospectives/](../archive/retrospectives/)

## Related Documentation

- [CI/CD](../cicd/) - Pipeline security
- [Operations](../operations/) - Server access
- [CLAUDE.md - Security Guidelines](../../CLAUDE.md#security-guidelines) - Detailed security policies

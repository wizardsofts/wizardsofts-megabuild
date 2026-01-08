# Pre-Flight Checklists

This directory contains mandatory pre-flight checklists for different types of work. See AGENT.md Section 9.0 for the verification protocol.

---

## Checklist Selection

| Work Type | Script / Checklist | When to Use |
|-----------|-------------------|-------------|
| Infrastructure | `scripts/validate-service-infrastructure.sh` | Before any service/infrastructure changes |
| Backup Setup | `scripts/setup-service-backups.sh --dry-run` | Before configuring NFS/backups |
| Integration Testing | `scripts/test-service-integration.sh` | After changes, before deployment |
| Application Feature | App's AGENT.md → "Pre-Flight Checklist" | Before working on any app |

---

## Script-Based Verification (Preferred)

### Infrastructure Validation

```bash
# Verify service infrastructure before making changes
./scripts/validate-service-infrastructure.sh <service-name> <host-ip>

# Example:
./scripts/validate-service-infrastructure.sh gitlab 10.0.0.84

# With strict mode (exit on first failure):
./scripts/validate-service-infrastructure.sh gitlab 10.0.0.84 --strict
```

### Backup Configuration

```bash
# Dry-run NFS backup setup (shows what would be done)
./scripts/setup-service-backups.sh <service-name> <host-ip> <nfs-server> --dry-run

# Example:
./scripts/setup-service-backups.sh keycloak 10.0.0.84 10.0.0.80 --dry-run
```

### Integration Testing

```bash
# Run all integration tests for a service
./scripts/test-service-integration.sh <service-name> <host-ip>

# Skip specific tests:
./scripts/test-service-integration.sh gitlab 10.0.0.84 --skip cache --skip monitoring
```

---

## Manual Checklists

### Generic Pre-Flight (All Work Types)

- [ ] Read existing documentation for the component
- [ ] Verify current state matches documentation
- [ ] Run existing tests to establish baseline
- [ ] Identify dependencies that might be affected
- [ ] Check for related open issues/PRs

### Infrastructure Changes

- [ ] Run `validate-service-infrastructure.sh` script
- [ ] Verify containers are running and healthy
- [ ] Check NFS export options if applicable (`no_root_squash` for containers)
- [ ] Verify firewall rules allow required access
- [ ] Test database connectivity

### Database Changes

- [ ] Create backup before making changes
- [ ] Test migration on staging first
- [ ] Prepare rollback plan
- [ ] Verify connection from dependent services
- [ ] Check for active transactions/locks

### Bug Fix

- [ ] Reproduce the bug first
- [ ] Write failing test that captures the bug
- [ ] Identify related code paths
- [ ] Check for similar issues in other areas
- [ ] Run full test suite after fix

---

## App-Specific Checklists

Each application may define its own pre-flight checklist in its AGENT.md file.

**Check these locations first:**

- `apps/ws-gateway/AGENT.md` → Java Spring checklist
- `apps/gibd-quant-agent/AGENT.md` → Python ML checklist
- `apps/gibd-news/AGENT.md` → Python data pipeline checklist
- `apps/gibd-web-scraper/AGENT.md` → Python scraping checklist

If no app-specific checklist exists, use the generic checklist above.

---

## When Pre-Flight Reveals Issues

If pre-flight verification fails:

1. **Document the discrepancy** between expected and actual state
2. **Do NOT proceed** with original work until resolved
3. **Update documentation** to match reality (ground truth)
4. **Re-run pre-flight** to confirm resolution

See AGENT.md Section 9.0 for the complete Ground Truth Verification Protocol.

---

_Last Updated: 2026-01-08_
_See also: scripts/README.md for script documentation_

# GitLab CI/CD Secrets Management Guide

**Last Updated:** December 31, 2025
**Scope:** All WizardSofts Megabuild deployments

---

## Overview

This guide explains how to securely manage credentials for the CI/CD pipeline. **NEVER** hardcode passwords, API keys, or secrets in code or configuration files.

---

## Required CI/CD Variables

Navigate to: **GitLab → Settings → CI/CD → Variables**

### Core Deployment Variables

| Variable | Type | Protected | Masked | Description |
|----------|------|-----------|--------|-------------|
| `SSH_PRIVATE_KEY` | File | Yes | No | SSH key for server access |
| `DEPLOY_SUDO_PASSWORD` | Variable | Yes | Yes | Sudo password for deployment user |
| `DEPLOY_DB_PASSWORD` | Variable | Yes | Yes | PostgreSQL database password |

### Appwrite Variables

| Variable | Type | Protected | Masked | Description |
|----------|------|-----------|--------|-------------|
| `APPWRITE_DB_PASSWORD` | Variable | Yes | Yes | Appwrite MariaDB password |
| `APPWRITE_SECRET_KEY` | Variable | Yes | Yes | Appwrite encryption secret |
| `APPWRITE_OPENSSL_KEY` | Variable | Yes | Yes | Appwrite OpenSSL key |

### Service Variables

| Variable | Type | Protected | Masked | Description |
|----------|------|-----------|--------|-------------|
| `REDIS_PASSWORD` | Variable | Yes | Yes | Redis authentication password |
| `OPENAI_API_KEY` | Variable | Yes | Yes | OpenAI API key (for AI features) |
| `KEYCLOAK_ADMIN_PASSWORD` | Variable | Yes | Yes | Keycloak admin password |

---

## Setup Instructions

### Step 1: Access CI/CD Variables

1. Go to your GitLab project
2. Navigate to **Settings → CI/CD**
3. Expand the **Variables** section
4. Click **Add variable**

### Step 2: Configure Each Variable

For each variable listed above:

1. **Key**: Enter the variable name (e.g., `DEPLOY_SUDO_PASSWORD`)
2. **Value**: Enter the secret value
3. **Type**: Select `Variable` or `File` as specified
4. **Environment scope**: Leave as `All` or specify `production`
5. **Protect variable**: ✅ Check this box (only available on protected branches)
6. **Mask variable**: ✅ Check this box (hides value in job logs)
7. Click **Add variable**

### Step 3: Generate Secure Passwords

Use this script to generate secure passwords:

```bash
# Generate a secure 32-character password
openssl rand -base64 32

# Generate a 256-bit key for encryption
openssl rand -hex 32

# Generate SSH key pair (if needed)
ssh-keygen -t ed25519 -C "gitlab-deploy@wizardsofts.com" -f gitlab-deploy-key
```

### Step 4: Verify Variables

After adding all variables, verify they're accessible in a test pipeline:

```yaml
test-secrets:
  stage: validate
  script:
    - |
      if [ -z "$DEPLOY_SUDO_PASSWORD" ]; then
        echo "ERROR: DEPLOY_SUDO_PASSWORD not set!"
        exit 1
      fi
      echo "All secrets configured correctly!"
  only:
    - merge_requests
```

---

## Variable Protection Levels

### Protected Variables (Recommended)
- Only available on protected branches (main, master)
- Prevents exposure in feature branches
- Recommended for all production secrets

### Masked Variables (Required for Secrets)
- Values hidden in job logs
- Shown as `[MASKED]` if accidentally echoed
- Required for all passwords and API keys

---

## Environment-Specific Variables

For different environments, use environment scope:

| Variable | Scope | Value |
|----------|-------|-------|
| `DB_HOST` | production | 10.0.0.84 |
| `DB_HOST` | staging | 10.0.0.85 |
| `DB_HOST` | development | localhost |

---

## Rotating Credentials

### When to Rotate
- Immediately after any suspected compromise
- When team members leave
- Quarterly for high-security credentials
- Annually for standard credentials

### Rotation Procedure

1. **Generate new credential** using secure method above
2. **Update GitLab CI/CD variable** with new value
3. **Update production server** with new credential
4. **Trigger a deployment** to verify new credential works
5. **Invalidate old credential** (change password on service)
6. **Document rotation** in security log

### Automated Rotation (Future)

Consider implementing HashiCorp Vault for automated rotation:

```yaml
# Future integration with Vault
variables:
  VAULT_ADDR: "https://vault.wizardsofts.com"
  VAULT_TOKEN: $VAULT_CI_TOKEN

before_script:
  - export DB_PASSWORD=$(vault kv get -field=password secret/db)
```

---

## Security Best Practices

### DO:
- ✅ Use masked variables for all secrets
- ✅ Use protected variables on protected branches only
- ✅ Use file type for SSH keys and certificates
- ✅ Rotate credentials regularly
- ✅ Audit variable access via GitLab audit logs
- ✅ Use different credentials per environment

### DON'T:
- ❌ Echo secrets in job logs (even accidentally)
- ❌ Commit secrets to git (use .gitignore)
- ❌ Share secrets via chat or email
- ❌ Use the same password across services
- ❌ Store secrets in job artifacts

---

## Troubleshooting

### "Variable not found" Error

```bash
ERROR: DEPLOY_SUDO_PASSWORD not set in CI/CD Variables!
```

**Cause**: Variable not configured or wrong name

**Fix**:
1. Verify variable exists in Settings → CI/CD → Variables
2. Check variable name matches exactly (case-sensitive)
3. Ensure variable is not environment-scoped incorrectly

### "Permission denied" Error

```bash
Permission denied (publickey).
```

**Cause**: SSH key not configured correctly

**Fix**:
1. Verify `SSH_PRIVATE_KEY` is set as File type
2. Ensure public key is added to server's `authorized_keys`
3. Check key permissions: `chmod 600 ~/.ssh/id_rsa`

### Variable Masked in Output

```bash
echo $DB_PASSWORD
[MASKED]
```

**This is expected behavior!** Masked variables cannot be displayed.

---

## Migration from Hardcoded Credentials

If you have existing hardcoded credentials:

1. **Identify all hardcoded secrets**:
   ```bash
   grep -rE "(password|secret|key)\s*[:=]\s*['\"][^$]" . --include="*.yml"
   ```

2. **Create GitLab CI/CD variables** for each

3. **Replace hardcoded values** with variable references:
   ```yaml
   # Before (INSECURE)
   password: "hardcoded123"

   # After (SECURE)
   password: $DB_PASSWORD
   ```

4. **Rotate all compromised credentials** (they're in git history)

5. **Consider git history cleanup** (optional but recommended)

---

## Audit and Compliance

### Viewing Variable Access

1. Go to **Settings → General → Audit Events**
2. Filter by "Variable" events
3. Review who accessed/modified variables

### Compliance Checklist

- [ ] All secrets use masked variables
- [ ] Production secrets use protected variables
- [ ] SSH keys use file type variables
- [ ] No hardcoded secrets in repository
- [ ] Credentials rotated within policy period
- [ ] Access limited to necessary personnel

---

## Quick Reference

### Add a Password Variable

```
Key:         DEPLOY_DB_PASSWORD
Value:       <your-secure-password>
Type:        Variable
Protected:   ✅
Masked:      ✅
```

### Add an SSH Key Variable

```
Key:         SSH_PRIVATE_KEY
Value:       <paste entire private key content>
Type:        File
Protected:   ✅
Masked:      ❌ (file contents not maskable)
```

### Use in Pipeline

```yaml
script:
  - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
  - ssh user@server "DB_PASSWORD='$DEPLOY_DB_PASSWORD' ./deploy.sh"
```

---

## Related Documents

- [MONOREPO_STRATEGY.md](./MONOREPO_STRATEGY.md) - Repository organization
- [ARCHITECTURAL_REVIEW_REPORT_v2.md](./ARCHITECTURAL_REVIEW_REPORT_v2.md) - Security analysis
- [.gitlab-ci.yml](../.gitlab-ci.yml) - CI/CD pipeline configuration

---

**Security Contact:** If you discover exposed credentials, immediately contact the DevOps team and rotate all affected secrets.

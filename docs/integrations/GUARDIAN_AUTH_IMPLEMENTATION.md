# Guardian Investment BD - Authentication Implementation

**Status:** Phase 1-3 Complete (Infrastructure + Frontend)
**Date:** January 3, 2026
**Domain:** auth.guardianinvestmentbd.com

## Overview

This document describes the implementation of user authentication for guardianinvestmentbd.com using Keycloak as the identity provider with full OAuth 2.1 compliance.

## Implementation Status

### ✅ Phase 1: Infrastructure (COMPLETE)

**Traefik Configuration** ([traefik/dynamic_conf.yml](../traefik/dynamic_conf.yml)):
- Added router `keycloak-guardian` for `auth.guardianinvestmentbd.com`
- Configured Let's Encrypt TLS certificates
- Added Keycloak service pointing to `keycloak:8080`
- Added security headers middleware

**Keycloak Realm** ([infrastructure/keycloak/realms/wizardsofts-realm.json](../infrastructure/keycloak/realms/wizardsofts-realm.json)):
- Enabled self-registration (`registrationAllowed: true`)
- Added Guardian Investment BD redirect URIs to `gibd-quant-web` client
- Configured SMTP for email verification (mail.wizardsofts.com:587)
- Updated post-logout redirect URIs

### ✅ Phase 2: Frontend Authentication (COMPLETE)

**Middleware** ([apps/gibd-quant-web/middleware.ts](../apps/gibd-quant-web/middleware.ts)):
- Enforces JWT-based authentication on protected routes
- Public routes: `/`, `/coming-soon`
- Protected routes: `/signals`, `/charts`, `/chat`, `/multi-criteria`, `/company/*`
- Uses `next-auth/jwt` `getToken()` for session validation

**Coming Soon Page** ([apps/gibd-quant-web/app/coming-soon/page.tsx](../apps/gibd-quant-web/app/coming-soon/page.tsx)):
- Added "Sign In / Register for Early Access" button
- Uses `useAuth()` hook for login flow
- Redirects to Keycloak for authentication

**Environment Configuration** ([apps/gibd-quant-web/.env.example](../apps/gibd-quant-web/.env.example)):
- Updated `KEYCLOAK_ISSUER` to `https://auth.guardianinvestmentbd.com/realms/wizardsofts`
- Documented NextAuth.js configuration

### ✅ Phase 3: Backend JWT Validation (INFRASTRUCTURE READY)

**JWT Validator Module** (Created for all 3 services):
- [apps/gibd-quant-signal/src/auth/jwt_validator.py](../apps/gibd-quant-signal/src/auth/jwt_validator.py)
- [apps/gibd-quant-nlq/src/auth/jwt_validator.py](../apps/gibd-quant-nlq/src/auth/jwt_validator.py)
- [apps/gibd-quant-calibration/src/auth/jwt_validator.py](../apps/gibd-quant-calibration/src/auth/jwt_validator.py)

**Features:**
- JWKS caching for performance
- Full JWT validation (signature, expiration, issuer, audience)
- User extraction from token (sub, email, roles, tenant_id)
- FastAPI Security dependency injection

**Dependencies Added** (`python-jose[cryptography]==3.3.1`):
- ✅ **SECURITY PATCHED:** Uses version 3.3.1 (fixes CVE-2024-33663 and CVE-2024-33664)
- Added to all 3 services' `pyproject.toml` files

### ⏸️ Phase 4: Backend Endpoint Protection (PENDING)

**What's Left:** Apply JWT validation to actual API endpoints in main.py files.

**Implementation Pattern:**
```python
from auth.jwt_validator import get_current_user
from fastapi import Security

@app.post("/api/v1/signals/generate")
async def generate_signal(
    request: SignalRequest,
    current_user: dict = Security(get_current_user)  # ADD THIS
):
    # Log for audit trail
    print(f"Signal request from: {current_user['email']}")

    # Existing logic...
```

**Services to Update:**
1. `apps/gibd-quant-signal/src/api/main.py`
2. `apps/gibd-quant-nlq/src/api/main.py`
3. `apps/gibd-quant-calibration/src/api/main.py`

**Endpoints to Protect:**
- ✅ Keep PUBLIC: `/health` (monitoring)
- ✅ Keep PUBLIC: `/api/v1/nlq/examples` (reference data)
- 🔒 Protect: All other POST/PUT/DELETE endpoints
- 🔒 Protect: All GET endpoints with user-specific data

## DNS Configuration Required

Before deployment, create DNS A record:

```
auth.guardianinvestmentbd.com → 10.0.0.84
```

**Verification:**
```bash
nslookup auth.guardianinvestmentbd.com
# Should return: 10.0.0.84
```

## Environment Variables Required

### Production (GitLab CI/CD Variables)

**Frontend (gibd-quant-web):**
```bash
NEXTAUTH_URL=https://www.guardianinvestmentbd.com
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
KEYCLOAK_CLIENT_ID=gibd-quant-web
KEYCLOAK_ISSUER=https://auth.guardianinvestmentbd.com/realms/wizardsofts
```

**Backend Services (all 3):**
```bash
KEYCLOAK_ISSUER=https://auth.guardianinvestmentbd.com/realms/wizardsofts
KEYCLOAK_AUDIENCE=account
```

**Keycloak:**
```bash
SMTP_USER=<mailcow-smtp-user>
SMTP_PASSWORD=<mailcow-smtp-password>
```

## Deployment Steps

### 1. Prerequisites

```bash
# SSH to server 84
ssh wizardsofts@10.0.0.84

# Ensure Keycloak is running
cd /opt/wizardsofts-megabuild/infrastructure/keycloak
docker-compose ps
```

### 2. Merge Feature Branch

```bash
# From local machine
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-guardian-auth

# Review changes
git status
git diff master

# Commit all changes
git add .
git commit -m "feat: Add user authentication for guardianinvestmentbd.com

- Add Keycloak routing for auth.guardianinvestmentbd.com
- Enable self-registration with email verification in Keycloak realm
- Enforce authentication on frontend protected routes via middleware
- Create JWT validation infrastructure for backend services
- Add login/logout UI to coming-soon page

BREAKING CHANGE: Authentication infrastructure ready for deployment

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to feature branch
git push gitlab feature/guardian-auth

# Create MR in GitLab UI
# URL: http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild/-/merge_requests/new?merge_request[source_branch]=feature/guardian-auth
```

### 3. Post-Merge Deployment

```bash
# SSH to server
ssh wizardsofts@10.0.0.84
cd /opt/wizardsofts-megabuild

# Pull latest changes
git pull

# Restart Keycloak to load new realm config
cd infrastructure/keycloak
docker-compose restart keycloak

# Wait for Keycloak to be healthy (30-60 seconds)
docker-compose ps
docker logs keycloak --tail 50

# Restart Traefik to load new routes
docker restart traefik

# Rebuild and restart frontend
cd /opt/wizardsofts-megabuild/apps/gibd-quant-web
docker-compose down
docker-compose up -d --build
```

### 4. Verification

```bash
# 1. DNS Resolution
nslookup auth.guardianinvestmentbd.com
# Expected: 10.0.0.84

# 2. HTTPS Certificate (wait 2 minutes for Let's Encrypt)
curl -I https://auth.guardianinvestmentbd.com
# Expected: HTTP/2 200

# 3. Keycloak Health
curl https://auth.guardianinvestmentbd.com/realms/wizardsofts/.well-known/openid-configuration
# Expected: JSON with issuer, authorization_endpoint, etc.

# 4. Frontend Redirect (unauthenticated)
curl -I https://www.guardianinvestmentbd.com/signals
# Expected: Shows /coming-soon page

# 5. Registration Page
# Open in browser: https://auth.guardianinvestmentbd.com/realms/wizardsofts/protocol/openid-connect/registrations?client_id=gibd-quant-web&redirect_uri=https://www.guardianinvestmentbd.com/api/auth/callback/keycloak&response_type=code
# Expected: Keycloak registration form
```

## Testing End-to-End Flow

### Test 1: User Registration

1. Visit https://www.guardianinvestmentbd.com/coming-soon
2. Click "Sign In / Register for Early Access"
3. On Keycloak page, click "Register"
4. Fill in:
   - Email: test@example.com
   - Password: Test123!@# (12+ chars, mixed case, digit, special)
   - Confirm password
5. Check email for verification link
6. Click verification link
7. Login with credentials
8. **Expected:** Redirected to https://www.guardianinvestmentbd.com/ with access to all pages

### Test 2: Unauthenticated Access

```bash
curl -I https://www.guardianinvestmentbd.com/signals
# Expected: Redirected to /coming-soon (or 200 if middleware shows coming-soon)

curl -I https://www.guardianinvestmentbd.com/charts
# Expected: Same as above
```

### Test 3: Backend API (Without JWT - Should Work Until Phase 4)

```bash
curl https://www.guardianinvestmentbd.com/health
# Expected: 200 OK (health check always public)

# After Phase 4 is deployed:
curl -X POST https://www.guardianinvestmentbd.com/api/v1/signals/generate
# Expected: 401 Unauthorized (missing JWT)
```

## Security Considerations

### ✅ Implemented

1. **PKCE Enabled:** Public client uses Proof Key for Code Exchange
2. **Email Verification Required:** Users must verify email before access
3. **Strong Password Policy:** 12+ chars, mixed case, digits, special chars
4. **Token Security:**
   - Access tokens: 5 minutes (short-lived)
   - Refresh tokens: Rotated on use (one-time)
   - Stored in httpOnly cookies (immune to XSS)
5. **Brute Force Protection:** 5 failed attempts = 10-minute lockout
6. **HTTPS Enforced:** Let's Encrypt certificates via Traefik
7. **Security Headers:** X-Content-Type-Options, X-Frame-Options, HSTS
8. **Dependency Security:** python-jose 3.3.1 (patched for CVE-2024-33663, CVE-2024-33664)

### ⚠️ Pending

1. **Backend JWT Validation:** Apply to actual endpoints (Phase 4)
2. **Rate Limiting on Auth Endpoints:** Configure Keycloak rate limits
3. **Monitoring & Alerts:** Prometheus metrics for auth failures
4. **Audit Logging:** Log all authentication events

## Rollback Plan

### If Authentication Breaks Frontend

```bash
# SSH to server
ssh wizardsofts@10.0.0.84

# Revert middleware to allow all access
cd /opt/wizardsofts-megabuild/apps/gibd-quant-web
git checkout master -- middleware.ts
docker-compose restart
```

### If Keycloak Fails

```bash
# Restart Keycloak
cd /opt/wizardsofts-megabuild/infrastructure/keycloak
docker-compose restart keycloak

# If still failing, restore old realm config
git checkout master -- realms/wizardsofts-realm.json
docker-compose restart keycloak
```

### If DNS Issues

- Wait 24-48 hours for DNS propagation
- Temporary: Use `/etc/hosts` override for local testing

## Next Steps for Phase 4

1. **Update Backend main.py Files:**
   - Import: `from auth.jwt_validator import get_current_user`
   - Add dependency to protected endpoints: `user: dict = Security(get_current_user)`
   - Log user email for audit trails

2. **Test JWT Validation:**
   - Get access token from browser DevTools after login
   - Test API with: `curl -H "Authorization: Bearer <token>" ...`
   - Verify 401 without token, 200 with valid token

3. **Deploy Backend Changes:**
   - Rebuild Docker images with new dependencies
   - Restart all 3 backend services
   - Monitor logs for JWT validation errors

4. **Update Documentation:**
   - Add API authentication section to README
   - Document how to get access tokens
   - Create troubleshooting guide for common JWT errors

## Support & Troubleshooting

### Keycloak Login Not Working

1. Check Keycloak logs: `docker logs keycloak --tail 100`
2. Verify realm config: `curl https://auth.guardianinvestmentbd.com/realms/wizardsofts/.well-known/openid-configuration`
3. Check redirect URIs match exactly (no trailing slashes)

### Email Verification Not Sent

1. Check SMTP configuration in realm config
2. Verify Mailcow is running: `docker ps | grep mailcow`
3. Check Keycloak event logs in admin console

### JWT Validation Failing

1. Check KEYCLOAK_ISSUER environment variable matches exactly
2. Verify JWKS accessible: `curl https://auth.guardianinvestmentbd.com/realms/wizardsofts/protocol/openid-connect/certs`
3. Clear JWKS cache by restarting backend service

## Sources

- [Python-jose vulnerabilities | Snyk](https://security.snyk.io/package/pip/python-jose)
- [CVE-2024-33663 Explained](https://ethicalhacking.uk/python-jose-security-risk-cve-2024-33663-explained/)
- [GitHub Advisory GHSA-6c5p-j8vq-pqhj](https://github.com/advisories/GHSA-6c5p-j8vq-pqhj)
- [CVE-2024-33664 GitHub Advisory](https://github.com/advisories/GHSA-cjwg-qfpm-7377)

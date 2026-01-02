# Grafana Keycloak OAuth/OIDC Integration Guide

**Date:** 2026-01-02
**Status:** Configuration Ready - Requires Manual Setup
**Grafana Instance:** http://10.0.0.81:3002

---

## Overview

This guide configures Grafana to use Keycloak OAuth2/OIDC for Single Sign-On (SSO) authentication, replacing basic authentication.

**Benefits:**
- Centralized authentication across all WizardSofts services
- Role-based access control via Keycloak groups
- Better audit logging and session management
- Multi-factor authentication support (if configured in Keycloak)

---

## Prerequisites

- Keycloak running at https://id.wizardsofts.com
- Grafana running at http://10.0.0.81:3002
- Access to Keycloak admin console
- Docker Swarm access on Server 81

**Keycloak Admin Credentials:**
- Username: `admin`
- Password: `Keycl0ak!Admin2025`
- Master Realm: `master`
- Application Realm: `wizardsofts`

---

## Step 1: Create Grafana Client in Keycloak

### Option A: Via Web UI (Recommended)

1. **Access Keycloak Admin Console**
   ```bash
   # On your local machine with SSH tunnel
   ssh -L 8180:localhost:8180 wizardsofts@10.0.0.84

   # Open browser to: http://localhost:8180
   # OR access directly (if DNS configured): https://id.wizardsofts.com
   ```

2. **Login and Navigate to Clients**
   - Username: `admin`
   - Password: `Keycl0ak!Admin2025`
   - Select Realm: `wizardsofts` (top-left dropdown)
   - Go to: Clients → Create Client

3. **Configure Client**

   **General Settings:**
   ```
   Client ID: grafana
   Name: Grafana Monitoring Dashboard
   Description: Grafana SSO via Keycloak OAuth2/OIDC
   Client Type: Confidential
   ```

   **Capability Config:**
   ```
   Client authentication: ON
   Authorization: OFF
   Authentication flow:
     ✅ Standard flow
     ❌ Direct access grants
     ❌ Implicit flow
     ❌ Service accounts roles
     ❌ OAuth 2.0 Device Authorization Grant
   ```

   **Login Settings:**
   ```
   Root URL: http://10.0.0.81:3002

   Valid redirect URIs:
     http://10.0.0.81:3002/login/generic_oauth
     http://10.0.0.81:3002/*
     https://grafana.wizardsofts.com/login/generic_oauth
     https://grafana.wizardsofts.com/*

   Valid post logout redirect URIs:
     http://10.0.0.81:3002/*
     https://grafana.wizardsofts.com/*

   Web origins:
     http://10.0.0.81:3002
     https://grafana.wizardsofts.com
   ```

4. **Save and Get Client Secret**
   - Click "Save"
   - Go to "Credentials" tab
   - Copy the "Client Secret" (you'll need this for Grafana config)
   - Example format: `a1b2c3d4-e5f6-7890-abcd-1234567890ab`

5. **Configure Protocol Mappers (Optional but Recommended)**
   - Go to "Client scopes" tab
   - Click on "grafana-dedicated" scope
   - Add mappers for:
     - Email (oidc-usermodel-property-mapper)
     - Preferred username (oidc-usermodel-property-mapper)
     - Roles (oidc-usermodel-realm-role-mapper)
     - Groups (oidc-group-membership-mapper)

### Option B: Via REST API

```bash
# Get admin access token
TOKEN=$(ssh wizardsofts@10.0.0.84 'curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Keycl0ak!Admin2025&grant_type=password&client_id=admin-cli" | jq -r .access_token')

# Create Grafana client
ssh wizardsofts@10.0.0.84 "curl -X POST http://localhost:8180/admin/realms/wizardsofts/clients \
  -H 'Authorization: Bearer $TOKEN' \
  -H 'Content-Type: application/json' \
  -d @/opt/wizardsofts-megabuild/infrastructure/monitoring/grafana-oauth-client.json"

# Get client secret
CLIENT_ID=$(ssh wizardsofts@10.0.0.84 "curl -s http://localhost:8180/admin/realms/wizardsofts/clients \
  -H 'Authorization: Bearer $TOKEN' | jq -r '.[] | select(.clientId==\"grafana\") | .id'")

ssh wizardsofts@10.0.0.84 "curl -s http://localhost:8180/admin/realms/wizardsofts/clients/$CLIENT_ID/client-secret \
  -H 'Authorization: Bearer $TOKEN' | jq -r .value"
```

---

## Step 2: Update Grafana Configuration

### Update monitoring-stack.yml

Add these environment variables to the Grafana service:

```yaml
services:
  grafana:
    environment:
      # Existing settings
      - GF_SERVER_ROOT_URL=http://10.0.0.81:3002

      # OAuth Settings
      - GF_AUTH_GENERIC_OAUTH_ENABLED=true
      - GF_AUTH_GENERIC_OAUTH_NAME=Keycloak
      - GF_AUTH_GENERIC_OAUTH_ALLOW_SIGN_UP=true
      - GF_AUTH_GENERIC_OAUTH_CLIENT_ID=grafana
      - GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET=<REPLACE_WITH_CLIENT_SECRET>
      - GF_AUTH_GENERIC_OAUTH_SCOPES=openid profile email roles groups
      - GF_AUTH_GENERIC_OAUTH_AUTH_URL=https://id.wizardsofts.com/realms/wizardsofts/protocol/openid-connect/auth
      - GF_AUTH_GENERIC_OAUTH_TOKEN_URL=https://id.wizardsofts.com/realms/wizardsofts/protocol/openid-connect/token
      - GF_AUTH_GENERIC_OAUTH_API_URL=https://id.wizardsofts.com/realms/wizardsofts/protocol/openid-connect/userinfo
      - GF_AUTH_GENERIC_OAUTH_ROLE_ATTRIBUTE_PATH=contains(roles[*], 'super-admin') && 'Admin' || contains(roles[*], 'tenant-admin') && 'Editor' || 'Viewer'
      - GF_AUTH_GENERIC_OAUTH_ROLE_ATTRIBUTE_STRICT=true
      - GF_AUTH_GENERIC_OAUTH_USE_PKCE=true

      # Disable basic auth (optional - comment out to allow both methods during transition)
      # - GF_AUTH_DISABLE_LOGIN_FORM=true
      # - GF_AUTH_BASIC_ENABLED=false

      # Keep admin credentials for emergency access
      - GF_SECURITY_ADMIN_USER=${GF_ADMIN_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GF_ADMIN_PASSWORD:-admin}
```

---

## Step 3: Create Keycloak Groups for Grafana Roles

In Keycloak, create groups that map to Grafana roles:

1. Go to Groups → Create Group
2. Create the following groups:
   ```
   /grafana-admins    → Maps to Grafana "Admin" role
   /grafana-editors   → Maps to Grafana "Editor" role
   /grafana-viewers   → Maps to Grafana "Viewer" role
   ```

3. Assign users to groups based on desired access level

**Alternative: Use Existing Roles**
- `super-admin` → Grafana Admin
- `tenant-admin` → Grafana Editor
- `user` → Grafana Viewer
- `viewer` → Grafana Viewer

---

## Step 4: Deploy Updated Configuration

```bash
# On Server 81 (or Docker Swarm manager)
ssh wizardsofts@10.0.0.81

# Navigate to monitoring directory
cd ~/monitoring

# Update the stack (will pull new environment variables)
docker stack deploy -c /opt/wizardsofts-megabuild/infrastructure/monitoring/monitoring-stack.yml monitoring

# Wait for Grafana to restart
docker service logs monitoring_grafana -f

# Verify Grafana is healthy
docker service ps monitoring_grafana
```

---

## Step 5: Test OAuth Login

1. **Open Grafana**
   ```
   http://10.0.0.81:3002
   ```

2. **Login Methods Available**
   - Click "Sign in with Keycloak" (OAuth button)
   - OR use basic auth (admin/admin) if not disabled

3. **OAuth Flow**
   - Redirects to Keycloak login page
   - Enter Keycloak credentials
   - Approve consent (if required)
   - Redirects back to Grafana
   - User automatically created/logged in

4. **Verify User**
   - Go to: Configuration → Users
   - Check that OAuth user was created
   - Verify role assignment (Admin/Editor/Viewer)

---

## Troubleshooting

### Issue: "Invalid redirect_uri"
**Cause:** Redirect URIs don't match in Keycloak client
**Fix:**
- Check Keycloak client settings → Valid redirect URIs
- Ensure `http://10.0.0.81:3002/login/generic_oauth` is listed
- Wildcard: `http://10.0.0.81:3002/*`

### Issue: "User gets Viewer role instead of Admin"
**Cause:** Role mapping not configured correctly
**Fix:**
- Check `GF_AUTH_GENERIC_OAUTH_ROLE_ATTRIBUTE_PATH`
- Verify user has `super-admin` or `tenant-admin` role in Keycloak
- Check token claims: decode JWT at https://jwt.io

### Issue: "Invalid client_secret"
**Cause:** Client secret mismatch
**Fix:**
- Get correct secret from Keycloak: Clients → grafana → Credentials
- Update `GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET` in monitoring-stack.yml

### Issue: "OAuth login button not showing"
**Cause:** OAuth not enabled or misconfigured
**Fix:**
- Check logs: `docker service logs monitoring_grafana`
- Verify `GF_AUTH_GENERIC_OAUTH_ENABLED=true`
- Check for configuration errors

### Issue: "Certificate validation failed"
**Cause:** Self-signed or invalid SSL certificate on Keycloak
**Fix:**
- Add to Grafana config: `GF_AUTH_GENERIC_OAUTH_TLS_SKIP_VERIFY_INSECURE=true` (DEV ONLY!)
- OR: Fix Keycloak SSL certificate
- OR: Use HTTP URLs if on internal network only

---

## Security Considerations

### Production Checklist

- [ ] Use strong client secret (not default)
- [ ] Enable PKCE for additional security
- [ ] Use HTTPS for all URLs (not HTTP)
- [ ] Configure proper certificate validation
- [ ] Disable basic auth after OAuth is working: `GF_AUTH_DISABLE_LOGIN_FORM=true`
- [ ] Set up proper role mappings
- [ ] Enable audit logging in Keycloak
- [ ] Configure session timeouts appropriately
- [ ] Restrict redirect URIs to known domains only
- [ ] Use Keycloak realm-level roles instead of client roles

### Emergency Access

**If OAuth breaks and you're locked out:**

1. **Use basic auth** (if not disabled):
   ```
   Username: admin
   Password: admin (or value from GF_SECURITY_ADMIN_PASSWORD)
   ```

2. **Reset via container**:
   ```bash
   docker exec -it $(docker ps -qf "name=monitoring_grafana") grafana-cli admin reset-admin-password newpassword
   ```

3. **Disable OAuth temporarily**:
   ```bash
   # Edit monitoring-stack.yml, comment out OAuth env vars
   # Redeploy stack
   docker stack deploy -c monitoring-stack.yml monitoring
   ```

---

## Role Mapping Examples

### Example 1: JMESPath Expression (Current Config)

```javascript
contains(roles[*], 'super-admin') && 'Admin' ||
contains(roles[*], 'tenant-admin') && 'Editor' ||
'Viewer'
```

**Logic:**
- If token has `super-admin` role → Grafana Admin
- Else if token has `tenant-admin` role → Grafana Editor
- Else → Grafana Viewer

### Example 2: Group-Based Mapping

```javascript
contains(groups[*], '/grafana-admins') && 'Admin' ||
contains(groups[*], '/grafana-editors') && 'Editor' ||
'Viewer'
```

**Logic:**
- User in `/grafana-admins` group → Grafana Admin
- User in `/grafana-editors` group → Grafana Editor
- All others → Grafana Viewer

---

## Files Created/Modified

| File | Description |
|------|-------------|
| `infrastructure/monitoring/grafana-oauth-client.json` | Keycloak client configuration (for API import) |
| `infrastructure/monitoring/monitoring-stack.yml` | Updated with OAuth environment variables |
| `docs/GRAFANA_KEYCLOAK_OAUTH_SETUP.md` | This guide |

---

## References

- [Grafana OAuth Documentation](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/generic-oauth/)
- [Keycloak OIDC Documentation](https://www.keycloak.org/docs/latest/server_admin/#_oidc)
- [Grafana Role Mapping](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/generic-oauth/#role-mapping)

---

## Next Steps

1. Create Grafana client in Keycloak (Step 1)
2. Get client secret and update monitoring-stack.yml (Step 2)
3. Configure role/group mappings in Keycloak (Step 3)
4. Redeploy monitoring stack (Step 4)
5. Test OAuth login (Step 5)
6. Disable basic auth once OAuth is confirmed working

---

**Migration Completed By:** Claude Code
**Configuration Method:** Keycloak OAuth2/OIDC
**Fallback Authentication:** Basic auth (admin/admin) - disable after OAuth verified

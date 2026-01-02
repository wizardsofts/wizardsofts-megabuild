# Grafana-Keycloak SSO Integration

**Status:** ✅ Active  
**Date:** 2025-12-30  
**Server:** 10.0.0.84

## Overview

Grafana has been integrated with Keycloak for Single Sign-On (SSO) authentication using OAuth 2.0 / OpenID Connect protocol.

## Configuration Details

### Keycloak Setup
- **URL:** http://10.0.0.84:8180
- **Realm:** master
- **Admin Credentials:** admin / W1z4rdS0fts!2025
- **Client ID:** grafana
- **Client Secret:** grafana-secret-1767088804
- **Protocol:** openid-connect

### Keycloak Client Configuration
```json
{
  "clientId": "grafana",
  "name": "Grafana",
  "enabled": true,
  "protocol": "openid-connect",
  "publicClient": false,
  "redirectUris": [
    "http://10.0.0.84:3002/login/generic_oauth",
    "http://10.0.0.84:3002/*"
  ],
  "webOrigins": ["http://10.0.0.84:3002"],
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": true
}
```

### Grafana OAuth Configuration
Located in: `infrastructure/auto-scaling/monitoring/grafana/grafana.ini`

```ini
[auth.generic_oauth]
enabled = true
name = Keycloak
allow_sign_up = true
client_id = grafana
client_secret = grafana-secret-1767088804
scopes = openid email profile
auth_url = http://10.0.0.84:8180/realms/master/protocol/openid-connect/auth
token_url = http://keycloak:8080/realms/master/protocol/openid-connect/token
api_url = http://keycloak:8080/realms/master/protocol/openid-connect/userinfo
role_attribute_path = contains(roles[*], 'admin') && 'Admin' || contains(roles[*], 'editor') && 'Editor' || 'Viewer'
```

## How It Works

### Authentication Flow
1. User visits Grafana (http://10.0.0.84:3002)
2. User clicks "Sign in with Keycloak"
3. Redirected to Keycloak login page
4. User enters Keycloak credentials
5. Keycloak validates and issues tokens
6. User redirected back to Grafana with auth code
7. Grafana exchanges code for access token
8. Grafana queries user info from Keycloak
9. User logged into Grafana with appropriate role

### Role Mapping
Grafana roles are determined by Keycloak user roles:
- Keycloak role `admin` → Grafana **Admin**
- Keycloak role `editor` → Grafana **Editor**
- Default → Grafana **Viewer**

## Network Configuration

Both Keycloak and Grafana are on the `auto-scaling_autoscaler` Docker network:
- Keycloak container name: `keycloak`
- Grafana container name: `grafana`
- Internal communication uses container names
- External access uses IP addresses

## Usage

### For End Users
1. Go to http://10.0.0.84:3002
2. Click **"Sign in with Keycloak"** button
3. Enter your Keycloak username and password
4. You'll be automatically logged into Grafana

### Creating Keycloak Users
1. Go to http://10.0.0.84:8180/admin
2. Login with admin credentials
3. Navigate to Users → Add user
4. Fill in user details (username, email, etc.)
5. Go to Credentials tab → Set password
6. Assign roles in Role Mapping tab

## Troubleshooting

### Issue: "Sign in with Keycloak" button not appearing

**Check:**
1. Verify Grafana configuration:
   ```bash
   docker exec grafana cat /etc/grafana/grafana.ini | grep -A 10 "auth.generic_oauth"
   ```

2. Restart Grafana:
   ```bash
   docker restart grafana
   ```

### Issue: Authentication fails with "Invalid redirect URI"

**Solution:**
Update redirect URIs in Keycloak:
1. Login to Keycloak admin console
2. Go to Clients → grafana
3. Add redirect URI: `http://10.0.0.84:3002/login/generic_oauth`
4. Save

### Issue: User logs in but has wrong permissions

**Solution:**
Check role mapping in Keycloak:
1. Go to Users → Select user
2. Go to Role Mapping tab
3. Assign appropriate role (admin/editor/viewer)
4. User needs to log out and log back in

### Issue: Token validation fails

**Check network connectivity:**
```bash
# From Grafana container
docker exec grafana wget -O- http://keycloak:8080/realms/master/.well-known/openid-configuration

# From host
curl http://10.0.0.84:8180/realms/master/.well-known/openid-configuration
```

## Security Considerations

1. **Client Secret**: The client secret is stored in grafana.ini. In production, use environment variables or secrets management.

2. **HTTPS**: Current setup uses HTTP. For production, enable HTTPS on both Keycloak and Grafana.

3. **Token Expiration**: Tokens expire based on Keycloak realm settings. Configure appropriately for your security requirements.

4. **Admin Password**: Change the default Keycloak admin password (`W1z4rdS0fts!2025`) in production.

## Updating Configuration

### To Change Client Secret

1. Generate new secret in Keycloak:
   ```bash
   # In Keycloak admin console
   Clients → grafana → Credentials → Regenerate Secret
   ```

2. Update Grafana configuration:
   ```bash
   # Edit grafana.ini
   client_secret = <new-secret>
   
   # Deploy and restart
   docker cp grafana.ini grafana:/etc/grafana/grafana.ini
   docker restart grafana
   ```

### To Add New OAuth Provider

Edit `grafana.ini` and add another `[auth.<provider>]` section. Multiple OAuth providers can coexist.

## Verification Commands

```bash
# Check if Keycloak is running
docker ps | grep keycloak

# Check Grafana OAuth config
docker exec grafana cat /etc/grafana/grafana.ini | grep -A 10 "generic_oauth"

# Test Keycloak endpoint
curl http://10.0.0.84:8180/realms/master/.well-known/openid-configuration

# Check Grafana logs for OAuth errors
docker logs grafana --tail 50 | grep -i "oauth\|keycloak"
```

## Related Documentation

- [GRAFANA_PROMETHEUS_TROUBLESHOOTING.md](GRAFANA_PROMETHEUS_TROUBLESHOOTING.md) - Grafana setup and troubleshooting
- [DEPLOYMENT_NOTE_DOCKER_SNAP.md](DEPLOYMENT_NOTE_DOCKER_SNAP.md) - Docker Snap workarounds
- Keycloak Documentation: https://www.keycloak.org/docs/latest/server_admin/

## Maintenance

### Backup Keycloak Configuration
```bash
# Backup PostgreSQL database
docker exec keycloak-postgres pg_dump -U keycloak keycloak > keycloak-backup.sql
```

### Restart Services
```bash
# Restart Keycloak
docker restart keycloak

# Restart Grafana
docker restart grafana

# Restart both
docker restart keycloak grafana
```

---

**Deployment Complete:** 2025-12-30  
**Tested and Verified:** ✅  
**Documentation Status:** Complete

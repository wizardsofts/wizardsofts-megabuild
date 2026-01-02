# Grafana Monitoring - Deployment Guide

This guide documents the correct deployment procedure for Grafana monitoring with Keycloak SSO integration, based on lessons learned from production deployment.

---

## Prerequisites

- Docker installed (prefer apt over Snap due to AppArmor restrictions)
- Access to microservices-overlay network
- Keycloak running and accessible
- Prometheus running and scraping metrics

---

## Quick Start

### 1. Prepare Configuration

```bash
cd /opt/wizardsofts-megabuild/infrastructure/auto-scaling

# Create config directory in home (Docker Snap requirement)
mkdir -p ~/grafana-config

# Copy configuration
cp monitoring/grafana/grafana.ini ~/grafana-config/
chmod 644 ~/grafana-config/grafana.ini
```

### 2. Deploy Grafana

```bash
# Start Grafana container
docker-compose up -d grafana

# Wait for container to be healthy
docker ps | grep grafana
```

### 3. Setup Provisioning

```bash
# Copy provisioning configs into container
docker cp monitoring/grafana/provisioning/. grafana:/etc/grafana/provisioning/

# Copy dashboards
docker exec grafana mkdir -p /var/lib/grafana/dashboards
docker cp monitoring/grafana/dashboards/. grafana:/var/lib/grafana/dashboards/

# Set permissions
docker exec -u 0 grafana chown -R 472:472 /etc/grafana/provisioning
docker exec -u 0 grafana chown -R 472:472 /var/lib/grafana/dashboards

# Restart to load provisioning
docker restart grafana
```

### 4. Connect Networks

```bash
# Connect Keycloak to shared network (if not already)
docker network connect microservices-overlay keycloak

# Grafana should already be on microservices-overlay via docker-compose
# Verify:
docker inspect grafana --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}'
```

### 5. Reset Admin Password

```bash
docker exec grafana grafana-cli admin reset-admin-password admin
```

### 6. Validate Deployment

```bash
bash monitoring/validate-grafana.sh
```

---

## Docker Compose Configuration

### Required Networks

```yaml
networks:
  - autoscaler              # Internal monitoring (Prometheus, Loki)
  - microservices-overlay   # External integrations (Keycloak, Traefik)
```

### Volume Strategy

**Use named volumes for data** (works with Docker Snap):
```yaml
volumes:
  - grafana-data:/var/lib/grafana
```

**Use home directory for config** (Docker Snap requirement):
```yaml
volumes:
  - ~/grafana-config/grafana.ini:/etc/grafana/grafana.ini:ro
```

**Do NOT mount from /opt** if using Docker Snap:
```yaml
# ❌ This will fail with AppArmor:
# - /opt/path/config.ini:/etc/grafana/grafana.ini

# ✅ Use this instead:
# - ~/grafana-config/grafana.ini:/etc/grafana/grafana.ini
```

---

## Grafana Configuration (grafana.ini)

### Critical Sections

#### Server
```ini
[server]
http_port = 3000
root_url = http://<SERVER_IP>:3002
```

#### Security
```ini
[security]
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
```

#### Users
```ini
[users]
allow_sign_up = false
auto_assign_org = true
auto_assign_org_role = Editor
```

#### Alerting (Grafana 12.3+)
```ini
# ❌ DO NOT USE - Removed in Grafana 12.3+:
# [alerting]
# enabled = true

# ✅ USE THIS INSTEAD:
[unified_alerting]
enabled = true
```

#### Keycloak OAuth
```ini
[auth.generic_oauth]
enabled = true
name = Keycloak
allow_sign_up = true
client_id = grafana
client_secret = <CLIENT_SECRET>
scopes = openid email profile
auth_url = http://<SERVER_IP>:8180/realms/master/protocol/openid-connect/auth
token_url = http://keycloak:8080/realms/master/protocol/openid-connect/token
api_url = http://keycloak:8080/realms/master/protocol/openid-connect/userinfo
role_attribute_path = contains(roles[*], 'admin') && 'Admin' || contains(roles[*], 'editor') && 'Editor' || 'Viewer'
```

**Important**:
- `auth_url` uses SERVER_IP (browser redirects)
- `token_url`/`api_url` use container name (server-to-server)

---

## Dashboard Provisioning

### Configuration File

`monitoring/grafana/provisioning/dashboards/dashboards.yaml`:

```yaml
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards  # ← Critical: Must match where dashboards are copied
```

### Dashboard Files

Place JSON files in: `monitoring/grafana/dashboards/`

**Each dashboard must have**:
```json
{
  "panels": [{
    "datasource": {
      "type": "prometheus",
      "uid": "prometheus"
    },
    "targets": [{
      "expr": "your_query",
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      }
    }]
  }]
}
```

---

## Keycloak Client Setup

### Create Client via API

```bash
# Get admin token
TOKEN=$(curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=<ADMIN_PASSWORD>" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Create Grafana client
curl -X POST http://localhost:8180/admin/realms/master/clients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "grafana",
    "name": "Grafana",
    "enabled": true,
    "protocol": "openid-connect",
    "publicClient": false,
    "secret": "<GENERATE_SECURE_SECRET>",
    "redirectUris": [
      "http://<SERVER_IP>:3002/login/generic_oauth",
      "http://<SERVER_IP>:3002/*"
    ],
    "webOrigins": ["*"],
    "standardFlowEnabled": true,
    "directAccessGrantsEnabled": false,
    "serviceAccountsEnabled": false,
    "attributes": {
      "post.logout.redirect.uris": "+"
    }
  }'
```

---

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker logs grafana --tail 50
```

**Common issues**:
1. Deprecated `[alerting]` config → Remove it
2. Permission denied on config → Move to `~/`
3. Invalid config value → Check grafana.ini syntax

### Dashboards Not Loading

**Verify provisioning**:
```bash
# Check config
docker exec grafana cat /etc/grafana/provisioning/dashboards/dashboards.yaml

# Check files exist
docker exec grafana ls -la /var/lib/grafana/dashboards/

# Check logs
docker logs grafana | grep -i dashboard

# Reload provisioning
curl -X POST -u admin:admin http://localhost:3002/api/admin/provisioning/dashboards/reload
```

### Cannot Reach Keycloak

**Check networks**:
```bash
# Verify both on microservices-overlay
docker inspect grafana --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}'
docker inspect keycloak --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}'

# Test connectivity
docker exec grafana ping -c 2 keycloak

# Connect if missing
docker network connect microservices-overlay keycloak
```

### Datasource Not Working

**Test Prometheus**:
```bash
# From host
curl 'http://localhost:9090/api/v1/query?query=up'

# From Grafana container
docker exec grafana wget -q -O- http://prometheus:9090/api/v1/query?query=up

# Via Grafana API
curl -u admin:admin 'http://localhost:3002/api/datasources/proxy/uid/prometheus/api/v1/query?query=up'
```

---

## Validation

### Automated Tests

Run the validation script:
```bash
bash monitoring/validate-grafana.sh
```

Expected output: All checks should pass (✅)

### Manual Verification

1. **Access UI**: http://<SERVER_IP>:3002
2. **Login**: admin / admin
3. **Check datasources**: Configuration → Data sources → Prometheus (default)
4. **View dashboard**: Dashboards → Executive Server Status
5. **Test SSO**: Logout → Sign in with Keycloak

---

## Maintenance

### Backup

```bash
# Backup Grafana database
docker exec grafana sqlite3 /var/lib/grafana/grafana.db .dump > grafana-backup.sql

# Backup dashboards
docker cp grafana:/var/lib/grafana/dashboards ./dashboard-backup/
```

### Update Grafana

```bash
# Pull new image
docker-compose pull grafana

# Recreate container
docker-compose up -d grafana

# Verify
bash monitoring/validate-grafana.sh
```

### Reload Provisioning

```bash
# Reload datasources
curl -X POST -u admin:admin http://localhost:3002/api/admin/provisioning/datasources/reload

# Reload dashboards
curl -X POST -u admin:admin http://localhost:3002/api/admin/provisioning/dashboards/reload
```

---

## Security Checklist

- [ ] Change default admin password
- [ ] Rotate OAuth client secret
- [ ] Configure HTTPS via Traefik
- [ ] Restrict firewall rules
- [ ] Enable Grafana audit logging
- [ ] Set up regular backups
- [ ] Review user permissions
- [ ] Update Grafana regularly

---

## References

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Provisioning Guide](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [OAuth Configuration](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/generic-oauth/)
- [Docker Snap Issues](https://snapcraft.io/docs/docker-snap)
- [Retrospective](../../GRAFANA_DEPLOYMENT_RETROSPECTIVE.md)

---

*Last Updated: 2025-12-30*
*Tested Grafana Version: 12.3.1*

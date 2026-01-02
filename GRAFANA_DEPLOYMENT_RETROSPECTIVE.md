# Grafana Deployment Retrospective

**Date**: 2025-12-30
**Issue**: Grafana monitoring not working - System Status panel errors, Keycloak SSO missing, login failures
**Outcome**: ✅ All issues resolved, system fully operational

---

## Problems Encountered and Solutions

### 1. System Status Panel - "An unexpected error happened"

**Root Cause**: Panel missing datasource configuration in dashboard JSON

**Investigation**:
- Panel had no `datasource` field
- Targets had no `datasource.uid` reference
- Grafana couldn't determine which datasource to query

**Solution**:
```json
{
  "datasource": {
    "type": "prometheus",
    "uid": "prometheus"
  },
  "targets": [{
    "expr": "up{job=\"node-exporter\"}",
    "datasource": {
      "type": "prometheus",
      "uid": "prometheus"
    }
  }]
}
```

**Learning**: Always specify datasource at both panel and target level in Grafana dashboards

---

### 2. Grafana Restart Loop - Deprecated Alerting Config

**Root Cause**: Grafana 12.3+ removed legacy alerting, but config still had `[alerting]` section

**Error Message**:
```
logger=settings level=error msg="Option '[alerting].enabled' cannot be true.
Legacy Alerting is removed..."
Error: ✗ invalid setting [alerting].enabled
```

**Solution**:
- Removed entire `[alerting]` section
- Kept `[unified_alerting]` section only
- Container started successfully

**Learning**:
- Grafana 12.3+ only supports unified alerting
- Legacy alerting has been completely removed
- Always check breaking changes in major version updates

---

### 3. Docker Snap AppArmor - Permission Denied on Mounts

**Root Cause**: Docker installed via Snap has AppArmor restrictions preventing mounts from `/opt`

**Error Messages**:
```
error while creating mount source path '/opt/wizardsofts-megabuild/...':
mkdir /opt/wizardsofts-megabuild: read-only file system

GF_PATHS_CONFIG='/etc/grafana/grafana.ini' is not readable.
permission denied
```

**Investigation**:
- Docker Snap has strict AppArmor confinement
- Cannot mount from `/opt`, `/root`, or other system directories
- Only allows mounts from user home directory (`~`)

**Solution**:
1. Move configs to `~/grafana-config/`
2. Change data directory to named volume `grafana-data:`
3. Update docker-compose.yml:
```yaml
volumes:
  - grafana-data:/var/lib/grafana
  - ~/grafana-config/grafana.ini:/etc/grafana/grafana.ini:ro
```

**Learning**:
- Docker Snap has different security model than Docker from apt
- Always use home directory (`~/`) for bind mounts with Snap
- Use named volumes for data persistence
- Check `/var/log/syslog` for AppArmor denials

---

### 4. Missing Keycloak SSO Integration

**Root Cause**: OAuth configuration not present in grafana.ini

**Solution**:
1. Created Keycloak client via API:
```bash
CLIENT_DATA='{
  "clientId": "grafana",
  "enabled": true,
  "protocol": "openid-connect",
  "publicClient": false,
  "secret": "grafana-secret-1767088804",
  "redirectUris": ["http://10.0.0.84:3002/login/generic_oauth"]
}'
```

2. Added OAuth config to grafana.ini:
```ini
[auth.generic_oauth]
enabled = true
name = Keycloak
client_id = grafana
client_secret = grafana-secret-1767088804
auth_url = http://10.0.0.84:8180/realms/master/protocol/openid-connect/auth
token_url = http://keycloak:8080/realms/master/protocol/openid-connect/token
api_url = http://keycloak:8080/realms/master/protocol/openid-connect/userinfo
```

**Learning**:
- External auth_url uses server IP (for browser redirect)
- Internal token_url/api_url use container name (for server-to-server)

---

### 5. Grafana Cannot Reach Keycloak - Network Isolation

**Root Cause**: Containers on different Docker networks

**Investigation**:
```
Grafana networks: auto-scaling_autoscaler
Keycloak networks: wizardsofts-megabuild_backend
Error: wget: bad address 'keycloak:8080'
```

**Solution**:
1. Added Grafana to `microservices-overlay` network:
```yaml
grafana:
  networks:
    - autoscaler
    - microservices-overlay
```

2. Connected Keycloak to same network:
```bash
docker network connect microservices-overlay keycloak
```

**Learning**:
- Container name DNS only works within same network
- Multi-service integrations need shared network
- Prometheus already had this configured correctly
- Runtime `docker network connect` can fix without restart

---

### 6. Dashboard Provisioning Not Loading

**Root Cause**: Provisioning config pointed to wrong path

**Investigation**:
```
Config: path: /etc/grafana/provisioning/dashboards
Actual location: /var/lib/grafana/dashboards
Result: 0 dashboards loaded
```

**Solution**:
Changed dashboards.yaml:
```yaml
options:
  path: /var/lib/grafana/dashboards  # Was: /etc/grafana/provisioning/dashboards
```

**Learning**:
- Dashboard provisioning requires correct path
- Files copied to container persist in named volumes
- API reload endpoint: `/api/admin/provisioning/dashboards/reload`

---

### 7. Admin Login Failing After Password Reset

**Root Cause**: Using wrong login endpoint and format

**Investigation**:
- `/login` endpoint expects form data, not JSON
- Basic auth works perfectly for API access
- Web form login uses different mechanism

**Solution**:
- Use HTTP Basic Auth for API: `curl -u admin:admin`
- Web UI login works through browser form
- Password reset via: `grafana-cli admin reset-admin-password`

**Learning**:
- Grafana has multiple auth methods
- Basic auth is most reliable for scripting
- Form-based login is for web UI only

---

## Architecture Decisions

### Volume Strategy
**Decision**: Use named volumes for data, bind mounts for config

**Rationale**:
- Named volumes work with Docker Snap
- Config files need to be version controlled
- Data should persist independently

**Implementation**:
```yaml
volumes:
  - grafana-data:/var/lib/grafana          # Named volume
  - ~/grafana-config/grafana.ini:/etc/grafana/grafana.ini:ro  # Bind mount
```

---

### Network Architecture
**Decision**: Connect Grafana to multiple networks

**Rationale**:
- `autoscaler`: Internal monitoring (Prometheus, Loki)
- `microservices-overlay`: External integrations (Keycloak, Traefik)

**Implementation**:
```yaml
networks:
  - autoscaler
  - microservices-overlay
```

---

### Provisioning Strategy
**Decision**: Copy provisioning files into container, not bind mount

**Rationale**:
- Docker Snap restrictions prevent mounting from `/opt`
- Copied files persist in named volumes
- Cleaner than complex mount paths

**Implementation**:
```bash
docker cp monitoring/grafana/provisioning/. grafana:/etc/grafana/provisioning/
docker cp monitoring/grafana/dashboards/. grafana:/var/lib/grafana/dashboards/
```

---

## Testing Strategy

Created comprehensive validation script covering:

1. **Container Health**: Docker ps status and healthcheck
2. **API Health**: `/api/health` endpoint
3. **Authentication**: Basic auth and session validation
4. **Datasources**: Count and configuration
5. **Dashboards**: Availability and loading
6. **Prometheus Connectivity**: Query execution
7. **Keycloak OAuth**: Configuration verification
8. **Network Connectivity**: Inter-container communication
9. **Web UI**: Login page and SSO button

**Script**: `/tmp/final-validation.sh`

**Usage**:
```bash
bash /tmp/final-validation.sh
```

---

## Key Learnings

### 1. Docker Snap Limitations
- Cannot mount from system directories
- Use `~/` for bind mounts
- Named volumes are preferred for data
- Check AppArmor logs for permission issues

### 2. Grafana 12.x Breaking Changes
- Legacy alerting completely removed
- Must use unified alerting only
- Check release notes for major versions

### 3. Container Networking
- DNS resolution requires shared network
- Multi-network containers are common
- Runtime network connection is non-destructive

### 4. OAuth Integration
- External URLs use server IP (browser)
- Internal URLs use container names (server-to-server)
- Redirect URIs must be exact matches

### 5. Provisioning Best Practices
- Always verify paths in provisioning config
- Use absolute paths consistently
- Test with reload API endpoint

---

## Troubleshooting Playbook

### When Grafana Won't Start

1. **Check logs**:
```bash
docker logs grafana --tail 50
```

2. **Look for config errors**:
- Deprecated settings
- Invalid values
- Missing required fields

3. **Verify mounts**:
```bash
docker inspect grafana --format='{{.Mounts}}'
```

4. **Check AppArmor** (if Snap):
```bash
sudo journalctl -xe | grep -i apparmor | grep grafana
```

---

### When Containers Can't Communicate

1. **Check networks**:
```bash
docker inspect <container> --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}'
```

2. **Test DNS resolution**:
```bash
docker exec grafana ping keycloak
```

3. **Connect to shared network**:
```bash
docker network connect microservices-overlay <container>
```

---

### When Dashboards Don't Load

1. **Check provisioning config**:
```bash
docker exec grafana cat /etc/grafana/provisioning/dashboards/dashboards.yaml
```

2. **Verify dashboard files exist**:
```bash
docker exec grafana ls -la /var/lib/grafana/dashboards/
```

3. **Check logs for errors**:
```bash
docker logs grafana | grep -i dashboard
```

4. **Reload provisioning**:
```bash
curl -X POST -u admin:admin http://localhost:3002/api/admin/provisioning/dashboards/reload
```

---

## Future Improvements

### 1. Automated Testing
- Create permanent validation script in repository
- Run on deployment pipeline
- Alert on failures

### 2. Backup Strategy
- Export dashboards regularly
- Backup grafana.db
- Version control provisioning configs

### 3. High Availability
- Multiple Grafana instances
- Shared database (PostgreSQL)
- Load balancer

### 4. Security Hardening
- Change default password
- Enable HTTPS
- Rotate OAuth secrets
- Configure RBAC

### 5. Monitoring the Monitor
- Alert on Grafana downtime
- Track query performance
- Monitor datasource health

---

## Deployment Checklist

For future Grafana deployments:

- [ ] Use Docker from apt, not Snap (or plan for AppArmor)
- [ ] Check Grafana version for breaking changes
- [ ] Configure multi-network if integrations needed
- [ ] Remove deprecated config sections
- [ ] Set correct provisioning paths
- [ ] Test OAuth endpoints reachability
- [ ] Verify dashboard datasource configuration
- [ ] Create validation script
- [ ] Document credentials securely
- [ ] Plan backup strategy

---

## Timeline

1. **System Status Panel Error** (30 min)
   - Diagnosed missing datasource
   - Fixed dashboard JSON
   - Deployed - issue persisted due to container crash

2. **Grafana Crash Loop** (45 min)
   - Found deprecated alerting config
   - Removed `[alerting]` section
   - Hit Docker Snap permission issues

3. **Docker Snap AppArmor** (60 min)
   - Multiple permission denied errors
   - Researched Snap limitations
   - Moved configs to home directory
   - Used named volumes

4. **Keycloak Integration** (40 min)
   - Set up OAuth client
   - Configured grafana.ini
   - Hit network connectivity issues

5. **Network Isolation** (30 min)
   - Diagnosed different networks
   - Connected to microservices-overlay
   - Verified connectivity

6. **Dashboard Provisioning** (20 min)
   - Found wrong path in config
   - Fixed dashboards.yaml
   - Reloaded successfully

7. **Final Validation** (30 min)
   - Created comprehensive test script
   - Validated all components
   - Documented findings

**Total Time**: ~4 hours
**Result**: Fully operational system

---

## References

- [Grafana Provisioning Docs](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Docker Snap AppArmor](https://snapcraft.io/docs/docker-snap)
- [Grafana OAuth Setup](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/generic-oauth/)
- [Keycloak Client Config](https://www.keycloak.org/docs/latest/server_admin/)

---

*Retrospective compiled: 2025-12-30*
*Engineer: Claude Sonnet 4.5*

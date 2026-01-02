# Fix Grafana Dashboards - Missing Dashboards Issue

## Problem
Dashboards disappeared after configuration changes. This was caused by:
1. Incorrect volume mount paths in docker-compose.yml
2. Missing provisioning configuration files
3. Conflicting grafana.ini settings

## Solution Applied

### Files Fixed/Created:

1. **✅ Fixed grafana.ini** - Removed conflicting default dashboard path
2. **✅ Fixed autoscaling-dashboard.json** - Added missing `overwrite: true` flag
3. **✅ Created provisioning/dashboards/dashboards.yaml** - Dashboard provisioning config
4. **✅ Created provisioning/preferences/preferences.yaml** - Sets executive dashboard as default
5. **✅ Updated docker-compose.yml** - Simplified volume mounts

### Directory Structure Now:

```
monitoring/grafana/
├── dashboards/
│   ├── .gitkeep
│   ├── autoscaling-dashboard.json     (uid: autoscaling-platform)
│   └── executive-dashboard.json       (uid: executive-overview) ⭐ DEFAULT
├── provisioning/
│   ├── dashboards/
│   │   └── dashboards.yaml           # Loads all JSON files
│   ├── datasources/
│   │   └── prometheus.yaml           # Prometheus connection
│   ├── alerting/
│   │   └── alerts.yaml               # 7 alert rules
│   └── preferences/
│       └── preferences.yaml          # Sets default dashboard
└── grafana.ini                       # Main config (cleaned up)
```

## How to Deploy

### Step 1: Deploy Files to Server

Your Grafana is likely running on a remote server. Deploy the fixed configuration:

```bash
# Option A: Deploy to specific server
SERVER="10.0.0.82"  # Or 10.0.0.80, 10.0.0.81, 10.0.0.83

cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/infrastructure/auto-scaling

# Sync all files
rsync -avz --delete monitoring/ $SERVER:~/auto-scaling/monitoring/
rsync -avz docker-compose.yml $SERVER:~/auto-scaling/

# SSH and restart
ssh $SERVER
cd ~/auto-scaling
docker-compose down grafana
docker-compose up -d grafana
docker logs -f grafana
```

### Step 2: Verify Dashboards Load

After Grafana restarts, check the logs:

```bash
docker logs grafana 2>&1 | grep -i "provision\|dashboard"
```

You should see:
```
✅ Provisioning dashboards
✅ Dashboard autoscaling-platform provisioned
✅ Dashboard executive-overview provisioned
```

### Step 3: Access Grafana

1. Open: http://YOUR_SERVER_IP:3002
2. Login: `admin` / (password from env)
3. You should see **Executive Server Status** as the home dashboard
4. Check left menu → Dashboards → should show both:
   - **Executive Server Status** ⭐
   - **Auto-Scaling Platform Dashboard**

## Troubleshooting

### Issue: Still No Dashboards

```bash
# 1. Check if files are mounted
docker exec grafana ls -la /etc/grafana/provisioning/dashboards/
docker exec grafana ls -la /var/lib/grafana/dashboards/

# 2. Check provisioning config
docker exec grafana cat /etc/grafana/provisioning/dashboards/dashboards.yaml

# 3. Check dashboard files exist
docker exec grafana ls -la /var/lib/grafana/dashboards/*.json

# 4. Restart with logs
docker-compose restart grafana && docker logs -f grafana
```

### Issue: Wrong Dashboard Shows as Default

```bash
# Check preferences
docker exec grafana cat /etc/grafana/provisioning/preferences/preferences.yaml

# Should show:
# homeDashboardUID: executive-overview
```

### Issue: Permission Errors

```bash
# Fix permissions on host
cd monitoring/grafana
chmod -R 755 provisioning/
chmod -R 644 provisioning/*/*.yaml
chmod 644 dashboards/*.json
chmod 644 grafana.ini

# Restart
docker-compose restart grafana
```

### Issue: Grafana Won't Start

```bash
# Check full logs
docker logs grafana

# Common issues:
# - grafana.ini syntax error
# - Missing GF_SECURITY_ADMIN_PASSWORD env var
# - Permission issues with grafana_data volume

# Solution: Remove grafana.ini temporarily
docker-compose down grafana
mv monitoring/grafana/grafana.ini monitoring/grafana/grafana.ini.bak
docker-compose up -d grafana
```

## Testing Locally (If Grafana Runs Locally)

If you want to test locally first:

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/infrastructure/auto-scaling

# Create .env file
echo "GF_SECURITY_ADMIN_PASSWORD=admin123" > .env

# Start Grafana
docker-compose up -d grafana

# Watch logs
docker logs -f grafana

# Access at http://localhost:3002
```

## What Changed in docker-compose.yml

**Before:**
```yaml
volumes:
  - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
  - ./monitoring/grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro
  - ./monitoring/grafana/provisioning/alerting:/etc/grafana/provisioning/alerting:ro
```

**After (Simplified):**
```yaml
volumes:
  - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
  - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
```

This way:
- Dashboard JSON files go to `/var/lib/grafana/dashboards/`
- Provisioning YAML files go to `/etc/grafana/provisioning/`
- Grafana auto-discovers and loads everything

## Verification Checklist

After deployment:

- [ ] Grafana container is running: `docker ps | grep grafana`
- [ ] No errors in logs: `docker logs grafana | grep -i error`
- [ ] Dashboards provisioned: `docker logs grafana | grep -i dashboard`
- [ ] Can access Grafana: http://YOUR_SERVER:3002
- [ ] Can login with admin credentials
- [ ] Executive dashboard shows as home
- [ ] Both dashboards visible in menu
- [ ] Alerts are configured (check Alerting menu)
- [ ] Prometheus datasource connected

## Next Steps

1. **Deploy to your server** using the commands above
2. **Set Grafana password** in environment variables
3. **Configure alert notifications** (email, Slack, etc.)
4. **Test alerts** by triggering thresholds

## Quick Deploy Command

```bash
SERVER="10.0.0.82"
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/infrastructure/auto-scaling && \
rsync -avz monitoring/ $SERVER:~/auto-scaling/monitoring/ && \
rsync -avz docker-compose.yml $SERVER:~/auto-scaling/ && \
ssh $SERVER "cd ~/auto-scaling && docker-compose restart grafana" && \
echo "✅ Deployed! Check: http://$SERVER:3002"
```

Replace `10.0.0.82` with your actual Grafana server IP.

# Ray Worker Cleanup System

**Status**: ✅ Deployed (2026-01-05)
**Servers**: 10.0.0.80, 10.0.0.81, 10.0.0.84 (Server 82 pending SSH access)

## Overview

Ray workers accumulate large temporary files in `/tmp` directories (35GB+ per container) due to:
- Code packaging and distribution (`/tmp/ray_tmp_*`)
- pip package installation (`/tmp/pip-*`)
- Training job checkpoints and artifacts
- **Ray 2.40.0 limitation**: No automatic cleanup after tasks complete

This automated cleanup system prevents disk space exhaustion while ensuring training jobs are never interrupted.

## Architecture

### Components

1. **Smart Cleanup Script** ([scripts/cleanup_ray_workers_smart.sh](../scripts/cleanup_ray_workers_smart.sh))
   - Intelligent activity detection (CPU-based)
   - Threshold-based cleanup (only if /tmp > 5GB)
   - Safe operation (never interrupts active workers)

2. **Hourly Cron Jobs**
   - Runs on Servers 80, 81, 84
   - Executes every hour at minute 0
   - Logs to `~/logs/ray_cleanup.log`

3. **Prometheus Alerts** ([infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml](../infrastructure/auto-scaling/monitoring/prometheus/infrastructure-alerts.yml))
   - `RayWorkerLargeTmpDirectory` (Warning: /tmp > 50%)
   - `RayWorkerCriticalTmpDirectory` (Critical: /tmp > 80%)
   - `RayWorkerDiskUsageHigh` (Warning: disk < 30%)
   - `RayWorkerDiskCritical` (Critical: disk < 15%)

4. **Deployment Automation** ([scripts/deploy_ray_cleanup.sh](../scripts/deploy_ray_cleanup.sh))
   - CI/CD-compatible deployment script
   - Multi-server orchestration
   - Verification checks

## How It Works

### Cleanup Logic

```bash
For each Ray worker container:
  1. Check /tmp directory size
  2. If /tmp > 5GB threshold:
     a. Check worker CPU usage
     b. If CPU < 5% (idle):
        - Delete /tmp/ray_tmp_*
        - Delete /tmp/pip-*
        - Delete /tmp/tmp*
     c. If CPU >= 5% (active):
        - Skip cleanup (worker is training)
  3. Log results

After all workers:
  4. Run docker system prune (cleanup stopped containers, unused images)
  5. Report disk usage
```

### Safety Features

- **Activity-Aware**: Only cleans idle workers (CPU < 5%)
- **Threshold-Based**: Only triggers if /tmp > 5GB
- **Non-Disruptive**: Active training jobs are never interrupted
- **Logged**: Full audit trail for debugging
- **Atomic**: Each worker cleaned independently

## Deployment

### Initial Setup (Already Done)

```bash
# Deploy to all servers
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
./scripts/deploy_ray_cleanup.sh
```

### Manual Deployment to Single Server

```bash
# Copy script
scp scripts/cleanup_ray_workers_smart.sh wizardsofts@10.0.0.80:~/

# SSH to server
ssh wizardsofts@10.0.0.80

# Make executable
chmod +x ~/cleanup_ray_workers_smart.sh

# Create log directory
mkdir -p ~/logs

# Add to crontab
(crontab -l 2>/dev/null | grep -v "cleanup_ray_workers"; \
 echo "# Ray worker /tmp cleanup - runs hourly"; \
 echo "0 * * * * /home/wizardsofts/cleanup_ray_workers_smart.sh \$(hostname -I | awk '{print \$1}') >> /home/wizardsofts/logs/ray_cleanup.log 2>&1") | crontab -
```

### CI/CD Integration

Add to GitLab CI pipeline:

```yaml
deploy_ray_cleanup:
  stage: deploy
  script:
    - cd /opt/wizardsofts-megabuild
    - ./scripts/deploy_ray_cleanup.sh
  only:
    - master
  when: manual
```

## Monitoring

### View Cleanup Logs

```bash
# Real-time log tail
ssh wizardsofts@10.0.0.80 tail -f ~/logs/ray_cleanup.log

# Last 100 lines
ssh wizardsofts@10.0.0.80 tail -100 ~/logs/ray_cleanup.log

# Search for errors
ssh wizardsofts@10.0.0.80 grep -i error ~/logs/ray_cleanup.log
```

### Check Cron Status

```bash
# View crontab
ssh wizardsofts@10.0.0.80 crontab -l

# Check last cron execution
ssh wizardsofts@10.0.0.80 'grep CRON /var/log/syslog | tail -10'
```

### Prometheus Alerts

Access Grafana dashboard: http://10.0.0.84:3002

Alerts available in `ray_cluster_monitoring` group:
- **RayWorkerLargeTmpDirectory**: Warning at 50% /tmp usage
- **RayWorkerCriticalTmpDirectory**: Critical at 80% /tmp usage
- **RayWorkerDiskUsageHigh**: Warning when disk < 30%
- **RayWorkerDiskCritical**: Critical when disk < 15%

## Manual Cleanup

If immediate cleanup is needed:

```bash
# Clean single server
ssh wizardsofts@10.0.0.80 ~/cleanup_ray_workers_smart.sh 10.0.0.80

# Clean all servers
for server in 10.0.0.80 10.0.0.81 10.0.0.84; do
  ssh wizardsofts@$server ~/cleanup_ray_workers_smart.sh $server
done
```

## Configuration

### Adjusting Cleanup Threshold

Edit `scripts/cleanup_ray_workers_smart.sh`:

```bash
# Current: 5000MB (5GB)
MIN_TMP_SIZE_MB=5000

# For more aggressive cleanup:
MIN_TMP_SIZE_MB=3000  # 3GB

# For less frequent cleanup:
MIN_TMP_SIZE_MB=10000  # 10GB
```

After changing, redeploy:

```bash
./scripts/deploy_ray_cleanup.sh
```

### Adjusting CPU Idle Threshold

Edit `scripts/cleanup_ray_workers_smart.sh`:

```bash
# Current: < 5% CPU = idle
if [ "$cpu_int" -lt 5 ]; then

# For more conservative (wait for lower CPU):
if [ "$cpu_int" -lt 2 ]; then

# For more aggressive (clean even at higher CPU):
if [ "$cpu_int" -lt 10 ]; then
```

### Changing Cleanup Frequency

```bash
# Edit crontab on server
ssh wizardsofts@10.0.0.80 crontab -e

# Current: Every hour at minute 0
0 * * * * /home/wizardsofts/cleanup_ray_workers_smart.sh ...

# Every 30 minutes:
*/30 * * * * /home/wizardsofts/cleanup_ray_workers_smart.sh ...

# Every 2 hours:
0 */2 * * * /home/wizardsofts/cleanup_ray_workers_smart.sh ...

# Daily at 2 AM:
0 2 * * * /home/wizardsofts/cleanup_ray_workers_smart.sh ...
```

## Troubleshooting

### Cleanup Not Running

```bash
# 1. Check if cron job exists
ssh wizardsofts@10.0.0.80 crontab -l | grep cleanup

# 2. Check if script exists and is executable
ssh wizardsofts@10.0.0.80 ls -lh ~/cleanup_ray_workers_smart.sh

# 3. Check cron logs
ssh wizardsofts@10.0.0.80 grep CRON /var/log/syslog | grep cleanup

# 4. Test manual execution
ssh wizardsofts@10.0.0.80 ~/cleanup_ray_workers_smart.sh 10.0.0.80
```

### /tmp Still Growing

```bash
# 1. Check if workers are idle
ssh wizardsofts@10.0.0.80 'docker stats --no-stream | grep ray-worker'

# 2. Check /tmp sizes
ssh wizardsofts@10.0.0.80 'for c in $(docker ps --filter name=ray-worker --format {{.Names}}); do echo "$c:"; docker exec $c du -sh /tmp; done'

# 3. Check cleanup threshold
# If /tmp < 5GB, cleanup won't trigger
# Lower MIN_TMP_SIZE_MB in script if needed

# 4. Force cleanup
ssh wizardsofts@10.0.0.80 ~/cleanup_ray_workers_smart.sh 10.0.0.80
```

### Prometheus Alerts Not Firing

```bash
# 1. Check if Prometheus is scraping metrics
# Visit: http://10.0.0.84:9090/targets

# 2. Verify alert rules loaded
# Visit: http://10.0.0.84:9090/alerts

# 3. Check metric exists
# Query: container_fs_usage_bytes{name=~"ray-worker.*"}

# 4. Reload Prometheus config
ssh wizardsofts@10.0.0.84 'docker exec prometheus kill -HUP 1'
```

## Performance Impact

- **CPU Overhead**: Minimal (<1% during cleanup)
- **Cleanup Duration**: 5-30 seconds per server
- **Training Impact**: None (active workers skipped)
- **Disk I/O**: Low (only deletes files, no reads)

## Historical Performance

### Cleanup Results (2026-01-05)

| Server | Before | After | Freed | Duration |
|--------|--------|-------|-------|----------|
| 10.0.0.80 | 100% (0GB free) | 33% (139GB free) | 141GB | 6 seconds |
| 10.0.0.84 | 50% (446GB free) | Healthy | 30.41GB | 8 seconds |

### Typical Cleanup

- **Idle worker /tmp**: 35GB → 70MB (99.8% reduction)
- **Active worker /tmp**: Skipped (no cleanup)
- **Docker system prune**: 0-5GB depending on stopped containers

## Ray Cleanup Limitations

**Ray 2.40.0 and 2.53.0 do NOT support automatic cleanup:**

- **No built-in cleanup configuration** ([Ray Issue #41202](https://github.com/ray-project/ray/issues/41202))
- **No `RAY_tmpdir_max_files` parameter** (does not exist)
- **Cleanup only on reboot** ([Ray Docs](https://docs.ray.io/en/latest/ray-core/configure.html))
- **Workaround required**: Manual cron-based cleanup (industry standard)

This is a known limitation affecting all Ray users, not specific to our deployment.

## Related Documentation

- [CLAUDE.md](../CLAUDE.md#automated-ray-worker-cleanup-deployed-2026-01-05) - Deployment summary
- [RAY_GCS_HEARTBEAT_FIX.md](../apps/gibd-quant-agent/docs/RAY_GCS_HEARTBEAT_FIX.md) - Ray cluster stability fixes
- [DISTRIBUTED_ML_NETWORKING.md](DISTRIBUTED_ML_NETWORKING.md) - Ray cluster architecture

## Support

For issues or questions:
1. Check logs: `ssh wizardsofts@10.0.0.80 tail -f ~/logs/ray_cleanup.log`
2. Review Prometheus alerts: http://10.0.0.84:3002
3. Consult this documentation
4. Contact DevOps team

---

**Last Updated**: 2026-01-05
**Maintained By**: WizardSofts DevOps Team

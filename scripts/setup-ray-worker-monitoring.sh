#!/bin/bash
# Setup Ray Worker Monitoring and Cleanup Cron Jobs
# Installs cron jobs for disk monitoring and periodic cleanup
# Usage: ./setup-ray-worker-monitoring.sh <server_ip>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <server_ip>"
    echo "Example: $0 10.0.0.80"
    exit 1
fi

SERVER=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==================================================================="
echo "Setting up Ray Worker Monitoring on $SERVER"
echo "==================================================================="

# Create monitoring script on remote server
echo "📝 Creating disk monitoring script on $SERVER..."
ssh wizardsofts@"$SERVER" 'cat > ~/monitor_disk_space.sh << '\''EOFSCRIPT'\''
#!/bin/bash
# Disk Space Monitoring for Ray Workers
# Alerts if disk usage > 80% or Ray worker /tmp > 10GB

DISK_THRESHOLD=80
TMP_THRESHOLD_GB=10
ALERT_LOG="/home/wizardsofts/disk_alerts.log"

# Check root filesystem usage
disk_usage=$(df -h / | tail -1 | awk '\''{print $5}'\'' | sed '\''s/%//'\'' || echo "0")

if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
    echo "[$(date)] ⚠️  ALERT: Disk usage at ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)" | tee -a "$ALERT_LOG"

    # Auto-cleanup if > 90%
    if [ "$disk_usage" -gt 90 ]; then
        echo "[$(date)] 🧹 Auto-cleanup triggered (disk > 90%)" | tee -a "$ALERT_LOG"
        docker system prune -f --volumes >> "$ALERT_LOG" 2>&1
    fi
fi

# Check Ray worker /tmp directories
for container in $(docker ps --filter name=ray-worker --format "{{.Names}}" 2>/dev/null); do
    tmp_size_kb=$(docker exec "$container" du -sk /tmp 2>/dev/null | cut -f1 || echo "0")
    tmp_size_gb=$(echo "scale=2; $tmp_size_kb / 1024 / 1024" | bc)

    # Check if tmp size exceeds threshold
    if (( $(echo "$tmp_size_gb > $TMP_THRESHOLD_GB" | bc -l) )); then
        echo "[$(date)] ⚠️  ALERT: $container /tmp at ${tmp_size_gb}GB (threshold: ${TMP_THRESHOLD_GB}GB)" | tee -a "$ALERT_LOG"

        # Auto-cleanup old tmp files
        echo "[$(date)] 🧹 Cleaning $container /tmp..." | tee -a "$ALERT_LOG"
        docker exec "$container" sh -c "find /tmp -type f -mtime +1 -delete 2>/dev/null || true" >> "$ALERT_LOG" 2>&1
    fi
done
EOFSCRIPT
'

# Make script executable
ssh wizardsofts@"$SERVER" 'chmod +x ~/monitor_disk_space.sh'

# Create cleanup script on remote server
echo "📝 Creating periodic cleanup script on $SERVER..."
ssh wizardsofts@"$SERVER" 'cat > ~/cleanup_docker.sh << '\''EOFSCRIPT'\''
#!/bin/bash
# Periodic Docker Cleanup for Ray Workers
# Runs weekly to prevent disk space issues

echo "[$(date)] Starting periodic Docker cleanup..." | tee -a /home/wizardsofts/cleanup.log

# Clean Ray worker /tmp directories
for container in $(docker ps --filter name=ray-worker --format "{{.Names}}" 2>/dev/null); do
    echo "  Cleaning $container..." | tee -a /home/wizardsofts/cleanup.log
    docker exec "$container" sh -c "rm -rf /tmp/ray_tmp_* /tmp/pip-* /tmp/tmp* 2>/dev/null || true" >> /home/wizardsofts/cleanup.log 2>&1
done

# Docker system prune
echo "  Running docker system prune..." | tee -a /home/wizardsofts/cleanup.log
docker system prune -f --volumes >> /home/wizardsofts/cleanup.log 2>&1

# Show disk space after cleanup
df -h / | tail -1 | tee -a /home/wizardsofts/cleanup.log

echo "[$(date)] Cleanup complete" | tee -a /home/wizardsofts/cleanup.log
EOFSCRIPT
'

# Make script executable
ssh wizardsofts@"$SERVER" 'chmod +x ~/cleanup_docker.sh'

# Setup cron jobs
echo "⏰ Setting up cron jobs on $SERVER..."
ssh wizardsofts@"$SERVER" '(crontab -l 2>/dev/null || true; cat << '\''EOFCRON'\''
# Ray Worker Disk Monitoring (every 15 minutes)
*/15 * * * * /home/wizardsofts/monitor_disk_space.sh

# Ray Worker Cleanup (every Sunday at 2 AM)
0 2 * * 0 /home/wizardsofts/cleanup_docker.sh
EOFCRON
) | crontab -'

# Test the monitoring script
echo "🧪 Testing monitoring script..."
ssh wizardsofts@"$SERVER" '~/monitor_disk_space.sh'

echo ""
echo "==================================================================="
echo "✅ Setup complete for $SERVER"
echo "==================================================================="
echo ""
echo "Installed cron jobs:"
echo "  - Disk monitoring: Every 15 minutes"
echo "  - Auto cleanup (>90% disk): Automatic"
echo "  - Weekly cleanup: Every Sunday at 2 AM"
echo ""
echo "Logs:"
echo "  - Alerts: /home/wizardsofts/disk_alerts.log"
echo "  - Cleanup: /home/wizardsofts/cleanup.log"
echo ""
echo "To view cron jobs: ssh wizardsofts@$SERVER crontab -l"
echo "To view alerts: ssh wizardsofts@$SERVER tail -f ~/disk_alerts.log"
echo "==================================================================="

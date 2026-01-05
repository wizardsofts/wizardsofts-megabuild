#!/bin/bash
# Ray Worker Cleanup Script
# Cleans Docker resources and Ray worker /tmp directories on distributed cluster
# Usage: ./cleanup_ray_workers.sh [server1] [server2] ...
#        ./cleanup_ray_workers.sh  (defaults to all Ray worker servers)

set -e

# Default Ray worker servers if none specified
if [ $# -eq 0 ]; then
    SERVERS=("10.0.0.80" "10.0.0.81" "10.0.0.82")
else
    SERVERS=("$@")
fi

echo "==================================================================="
echo "Ray Worker Cleanup Script"
echo "==================================================================="
echo "Servers: ${SERVERS[*]}"
echo "Started: $(date)"
echo ""

# Function to cleanup a single server
cleanup_server() {
    local server=$1

    echo "[$server] Starting cleanup..."

    # Check connectivity
    if ! ping -c 1 -W 2 "$server" > /dev/null 2>&1; then
        echo "  ⚠️  Server unreachable, skipping"
        return 1
    fi

    # Clean Ray worker /tmp directories
    echo "  🧹 Cleaning Ray worker /tmp directories..."
    ssh wizardsofts@"$server" '
        for container in $(docker ps --filter name=ray-worker --format "{{.Names}}"); do
            echo "    Cleaning $container..."
            docker exec "$container" sh -c "rm -rf /tmp/ray_tmp_* /tmp/pip-* /tmp/tmp* 2>/dev/null || true"

            # Show /tmp size after cleanup
            tmp_size=$(docker exec "$container" du -sh /tmp 2>/dev/null | cut -f1)
            echo "      /tmp size: $tmp_size"
        done
    ' 2>/dev/null

    # Docker system prune
    echo "  🧹 Running docker system prune..."
    ssh wizardsofts@"$server" 'docker system prune -f --volumes 2>&1' | grep -E "(Deleted|Total)" || echo "    Nothing to prune"

    # Check disk space
    echo "  💾 Disk usage after cleanup:"
    ssh wizardsofts@"$server" 'df -h / | tail -1' | while read -r line; do
        echo "    $line"
    done

    echo "  ✅ Cleanup complete for $server"
    echo ""
}

# Cleanup all servers
for server in "${SERVERS[@]}"; do
    cleanup_server "$server"
done

echo "==================================================================="
echo "Cleanup completed for all servers"
echo "Finished: $(date)"
echo "==================================================================="

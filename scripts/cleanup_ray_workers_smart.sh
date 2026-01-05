#!/bin/bash
# Smart Ray Worker Cleanup Script
# Checks if Ray workers are idle before cleaning /tmp directories
# Usage: ./cleanup_ray_workers_smart.sh [server1] [server2] ...
#        ./cleanup_ray_workers_smart.sh  (defaults to all Ray worker servers)

set -e

# Default Ray worker servers if none specified
if [ $# -eq 0 ]; then
    SERVERS=("10.0.0.80" "10.0.0.81" "10.0.0.82" "10.0.0.84")
else
    SERVERS=("$@")
fi

# Minimum /tmp size threshold (in MB) to trigger cleanup
MIN_TMP_SIZE_MB=5000

echo "==================================================================="
echo "Smart Ray Worker Cleanup Script"
echo "==================================================================="
echo "Servers: ${SERVERS[*]}"
echo "Started: $(date)"
echo "Min /tmp size for cleanup: ${MIN_TMP_SIZE_MB}MB"
echo ""

# Function to check if Ray worker is actively running tasks
check_ray_worker_active() {
    local server=$1
    local container=$2

    # Check if worker has active tasks by looking at CPU usage over last 30 seconds
    # If CPU usage < 5%, consider it idle
    local cpu_usage=$(ssh wizardsofts@"$server" "docker stats --no-stream --format '{{.CPUPerc}}' $container" 2>/dev/null | sed 's/%//')

    # If we can't get CPU stats, assume it's active (safer)
    if [ -z "$cpu_usage" ]; then
        echo "    ⚠️  Cannot get CPU stats, assuming active"
        return 0  # Active (don't cleanup)
    fi

    # Convert to integer for comparison (remove decimals)
    cpu_int=$(echo "$cpu_usage" | cut -d'.' -f1)

    if [ "$cpu_int" -lt 5 ]; then
        echo "    💤 Worker idle (CPU: ${cpu_usage}%)"
        return 1  # Idle (safe to cleanup)
    else
        echo "    🔥 Worker active (CPU: ${cpu_usage}%)"
        return 0  # Active (don't cleanup)
    fi
}

# Function to get /tmp size in MB
get_tmp_size_mb() {
    local server=$1
    local container=$2

    local tmp_size=$(ssh wizardsofts@"$server" "docker exec $container du -sm /tmp 2>/dev/null | cut -f1" 2>/dev/null)
    echo "${tmp_size:-0}"
}

# Function to cleanup a single server
cleanup_server() {
    local server=$1

    echo "[$server] Starting cleanup..."

    # Check connectivity
    if ! ping -c 1 -W 2 "$server" > /dev/null 2>&1; then
        echo "  ⚠️  Server unreachable, skipping"
        return 1
    fi

    # Get list of Ray worker containers
    local containers=$(ssh wizardsofts@"$server" "docker ps --filter name=ray-worker --format '{{.Names}}'" 2>/dev/null)

    if [ -z "$containers" ]; then
        echo "  ℹ️  No Ray worker containers found"
        # Still run docker system prune
        echo "  🧹 Running docker system prune..."
        ssh wizardsofts@"$server" 'docker system prune -f --volumes 2>&1' | grep -E "(Deleted|Total)" || echo "    Nothing to prune"
        return 0
    fi

    # Check each container
    local cleaned=0
    while IFS= read -r container; do
        echo "  Checking $container..."

        # Get /tmp size
        local tmp_size_mb=$(get_tmp_size_mb "$server" "$container")
        echo "    /tmp size: ${tmp_size_mb}MB"

        # Only cleanup if /tmp is large AND worker is idle
        if [ "$tmp_size_mb" -gt "$MIN_TMP_SIZE_MB" ]; then
            echo "    ⚠️  /tmp size exceeds threshold (${MIN_TMP_SIZE_MB}MB)"

            # Check if worker is active
            if check_ray_worker_active "$server" "$container"; then
                echo "    ⏭️  Skipping cleanup - worker is active"
                continue
            fi

            # Worker is idle and /tmp is large - safe to cleanup
            echo "    🧹 Cleaning /tmp (worker is idle)..."
            ssh wizardsofts@"$server" "docker exec $container sh -c 'rm -rf /tmp/ray_tmp_* /tmp/pip-* /tmp/tmp* 2>/dev/null || true'" 2>/dev/null

            # Show /tmp size after cleanup
            local new_size_mb=$(get_tmp_size_mb "$server" "$container")
            local saved_mb=$((tmp_size_mb - new_size_mb))
            echo "    ✅ Cleaned ${saved_mb}MB (${tmp_size_mb}MB → ${new_size_mb}MB)"
            cleaned=$((cleaned + 1))
        else
            echo "    ✅ /tmp size OK (under ${MIN_TMP_SIZE_MB}MB threshold)"
        fi
    done <<< "$containers"

    # Docker system prune (always run)
    echo "  🧹 Running docker system prune..."
    ssh wizardsofts@"$server" 'docker system prune -f --volumes 2>&1' | grep -E "(Deleted|Total)" || echo "    Nothing to prune"

    # Check disk space
    echo "  💾 Disk usage after cleanup:"
    ssh wizardsofts@"$server" 'df -h / | tail -1' | while read -r line; do
        echo "    $line"
    done

    if [ "$cleaned" -gt 0 ]; then
        echo "  ✅ Cleanup complete for $server ($cleaned workers cleaned)"
    else
        echo "  ✅ No cleanup needed for $server"
    fi
    echo ""
}

# Cleanup all servers
total_cleaned=0
for server in "${SERVERS[@]}"; do
    cleanup_server "$server"
done

echo "==================================================================="
echo "Smart cleanup completed for all servers"
echo "Finished: $(date)"
echo "==================================================================="

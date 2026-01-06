#!/bin/bash
# Autoscale Ollama based on Traefik request metrics from Prometheus
#
# Setup:
#   1. Copy to Server 84: scp scripts/autoscale_ollama.sh wizardsofts@10.0.0.84:~/scripts/
#   2. Make executable: chmod +x ~/scripts/autoscale_ollama.sh
#   3. Add to cron: */5 * * * * ~/scripts/autoscale_ollama.sh >> ~/logs/autoscale.log 2>&1
#
# Requirements:
#   - Prometheus running on localhost:9090
#   - Traefik exporting metrics to Prometheus
#   - jq installed (apt install jq)
#   - bc installed (apt install bc)

set -e

# Configuration
PROM_URL="http://localhost:9090"
MIN_REPLICAS=2
MAX_REPLICAS=6
SCALE_UP_THRESHOLD=10      # requests/sec - scale up if exceeded
SCALE_DOWN_THRESHOLD=2     # requests/sec - scale down if below
COOLDOWN_PERIOD=300        # 5 minutes between scaling actions

LOG_DIR="$HOME/logs"
LOG_FILE="${LOG_DIR}/autoscale.log"
STATE_FILE="${LOG_DIR}/autoscale_state"

# Create log directory if not exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if cooldown period has passed
check_cooldown() {
    if [ -f "$STATE_FILE" ]; then
        LAST_SCALE_TIME=$(cat "$STATE_FILE")
        CURRENT_TIME=$(date +%s)
        TIME_DIFF=$((CURRENT_TIME - LAST_SCALE_TIME))

        if [ "$TIME_DIFF" -lt "$COOLDOWN_PERIOD" ]; then
            log "Cooldown active: ${TIME_DIFF}s / ${COOLDOWN_PERIOD}s"
            return 1  # Cooldown active
        fi
    fi
    return 0  # Cooldown passed
}

# Record scaling action
record_scaling() {
    date +%s > "$STATE_FILE"
}

# Get current request rate from Prometheus
get_request_rate() {
    local query="rate(traefik_service_requests_total{service=\"ollama@docker\"}[5m])"
    local result=$(curl -s "${PROM_URL}/api/v1/query?query=${query}" 2>/dev/null)

    if [ $? -ne 0 ]; then
        log "ERROR: Failed to query Prometheus"
        echo "0"
        return 1
    fi

    # Extract value using jq (returns "0" if no data)
    local rate=$(echo "$result" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    echo "$rate"
}

# Get current number of replicas
get_current_replicas() {
    docker service inspect ollama --format='{{.Spec.Mode.Replicated.Replicas}}' 2>/dev/null || echo "0"
}

# Scale service
scale_service() {
    local new_replicas=$1
    log "Scaling to ${new_replicas} replicas..."
    docker service scale ollama=${new_replicas} >> "$LOG_FILE" 2>&1
    record_scaling
}

# Main logic
main() {
    log "=== Autoscale Check ==="

    # Get metrics
    REQUEST_RATE=$(get_request_rate)
    CURRENT_REPLICAS=$(get_current_replicas)

    if [ "$CURRENT_REPLICAS" -eq 0 ]; then
        log "ERROR: Ollama service not found"
        exit 1
    fi

    log "Request rate: ${REQUEST_RATE}/sec | Current replicas: ${CURRENT_REPLICAS}"

    # Check cooldown before scaling
    if ! check_cooldown; then
        log "Skipping scaling action (cooldown)"
        return 0
    fi

    # Scale up if high load
    if (( $(echo "$REQUEST_RATE > $SCALE_UP_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        if [ "$CURRENT_REPLICAS" -lt "$MAX_REPLICAS" ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS + 1))
            log "High load detected! Scaling UP: ${CURRENT_REPLICAS} → ${NEW_REPLICAS}"
            scale_service "$NEW_REPLICAS"
        else
            log "Already at MAX replicas (${MAX_REPLICAS})"
        fi
    # Scale down if low load
    elif (( $(echo "$REQUEST_RATE < $SCALE_DOWN_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        if [ "$CURRENT_REPLICAS" -gt "$MIN_REPLICAS" ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
            log "Low load detected! Scaling DOWN: ${CURRENT_REPLICAS} → ${NEW_REPLICAS}"
            scale_service "$NEW_REPLICAS"
        else
            log "Already at MIN replicas (${MIN_REPLICAS})"
        fi
    else
        log "Load within normal range (${SCALE_DOWN_THRESHOLD}-${SCALE_UP_THRESHOLD}/sec)"
    fi
}

# Run main logic
main

log "=== Check Complete ==="
echo ""  # Blank line for readability

#!/bin/bash
# Test autoscaling functionality with artificial load

set -e  # Exit on any error

echo "=================================="
echo "Testing Auto-Scaling Functionality"
echo "=================================="
echo

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check current service stats
check_stats() {
    log "Current service stats:"
    curl -s http://10.0.0.80:8000/services/ollama/stats | jq '{container_count, avg_cpu, containers: [.containers[] | {id: .id, status: .status, cpu_percent: .cpu_percent}]}' 2>/dev/null || echo "Could not retrieve stats"
    echo
}

# Check initial state
log "1. Checking initial state..."
check_stats

# Wait to ensure system is stable
log "Waiting 30 seconds to ensure system is stable..."
sleep 30

# Check state again
log "2. State after stabilization period..."
check_stats

# Start artificial load to trigger scale-up
log "3. Starting artificial load to trigger scale-up..."
log "This will simulate load against the Ollama service to increase CPU usage."

# We'll use curl in a loop to generate requests to the Ollama API
log "Generating load with concurrent requests..."
(
    for i in {1..50}; do
        curl -s -X POST http://10.0.0.80:11434/api/generate \
          -H "Content-Type: application/json" \
          -d '{"model":"llama2","prompt":"Why is the sky blue?","stream":false}' > /dev/null 2>&1 &
        
        # Add a small delay to space out requests
        sleep 0.1
    done
    
    # Wait for all background jobs to complete
    wait
) &

LOAD_PID=$!
log "Load generation started (PID: $LOAD_PID)"

# Monitor for scale-up events
log "4. Monitoring for scale-up events (next 2 minutes)..."
END_TIME=$(($(date +%s) + 120))

# Track initial container count
INITIAL_COUNT=$(curl -s http://10.0.0.80:8000/services/ollama/stats | jq -r '.container_count' 2>/dev/null || echo "unknown")
log "Initial container count: $INITIAL_COUNT"

while [ $(date +%s) -lt $END_TIME ]; do
    CURRENT_COUNT=$(curl -s http://10.0.0.80:8000/services/ollama/stats | jq -r '.container_count' 2>/dev/null || echo "unknown")
    
    if [ "$CURRENT_COUNT" != "unknown" ] && [ "$CURRENT_COUNT" -gt "$INITIAL_COUNT" ]; then
        log "✓ Scale-up detected! Container count increased from $INITIAL_COUNT to $CURRENT_COUNT"
        
        # Check detailed stats
        check_stats
        break
    fi
    
    sleep 10
done

# Stop the load generation
log "5. Stopping load generation..."
kill $LOAD_PID 2>/dev/null || true
wait $LOAD_PID 2>/dev/null || true

log "Load generation stopped"
echo

# Check state after load stops
log "6. Checking state after load stops..."
check_stats

# Wait for cooldown period and potential scale-down
log "7. Waiting for cooldown period (60 seconds) to see if scale-down occurs..."
sleep 60

log "8. Checking final state after cooldown..."
check_stats

# Get scaling events
log "9. Recent scaling events:"
curl -s http://10.0.0.80:8000/events | jq '.' 2>/dev/null || echo "Could not retrieve events"

echo
log "=================================="
log "Auto-Scaling Test Summary:"
log "✓ Artificial load was generated to trigger scaling"
log "✓ System response to load was monitored"
log "✓ Scale-up events were checked for"
log "✓ Scale-down events were checked for after load removal"
log ""
log "Important Notes:"
log "- Scaling only occurs during business hours (configurable)"
log "- There's a cooldown period to prevent rapid scaling"
log "- Minimum replicas are maintained even when not needed"
log "- Check Grafana dashboard for detailed metrics"
log "=================================="

# Provide guidance for interpreting results
log ""
log "How to interpret results:"
log "- If container count increased during load: Scale-up worked"
log "- If container count decreased after load removal: Scale-down worked"
log "- If no changes occurred: Check business hours setting or thresholds"
log "- If issues occurred: Check autoscaler logs with:"
log "  docker-compose logs -f autoscaler"
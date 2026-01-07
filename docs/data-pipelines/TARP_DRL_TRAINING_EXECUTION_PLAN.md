# TARP-DRL Training Execution Plan with Background Monitoring

**Date:** 2026-01-05
**Status:** Ready for Execution
**Ray Version:** 2.53.0 (Production)
**Training Image:** `gibd-quant-agent-tarp-drl-training:v4-final`
**Data Cache:** `/home/wizardsofts/ray-outputs/data_cache/dse_data_2015-01-01_2024-12-31.parquet` (12.56 MB, 828K rows)

---

## Table of Contents

1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Infrastructure Validation](#infrastructure-validation)
3. [Training Execution](#training-execution)
4. [Background Monitoring Strategy](#background-monitoring-strategy)
5. [Troubleshooting Procedures](#troubleshooting-procedures)
6. [Post-Training Validation](#post-training-validation)

---

## Pre-Flight Checklist

### 1. Ray Cluster Status

**Objective:** Verify all Ray nodes are healthy and connected.

```bash
# Check Ray head node (Server 84)
ssh wizardsofts@10.0.0.84 '
  docker ps --filter name=ray-head --format "{{.Names}}\t{{.Status}}"
  curl -s http://localhost:8265/api/cluster_status | python3 -m json.tool | head -30
'

# Expected output:
# ray-head    Up X hours (healthy)
# {
#   "result": {
#     "cluster_name": "tarp-drl-cluster",
#     "node_count": 4,  # 1 head + 3 workers (80, 81, 82)
#     "active_nodes": 4
#   }
# }
```

**Success Criteria:**
- ✅ Ray head container status: `Up X hours (healthy)`
- ✅ Active nodes: 4 (1 head + 3 workers)
- ✅ All nodes in "ALIVE" state

**If Failed:**
```bash
# Start Ray cluster
ssh wizardsofts@10.0.0.84 'cd ~/ray && docker-compose -f docker-compose.ray-head.yml up -d'
ssh wizardsofts@10.0.0.80 'cd ~/ray && docker-compose -f docker-compose.ray-workers-multi.yml up -d'
ssh wizardsofts@10.0.0.81 'cd ~/ray && docker-compose -f docker-compose.ray-worker.yml up -d'
ssh wizardsofts@10.0.0.82 'cd ~/ray && docker-compose -f docker-compose.ray-worker.yml up -d'

# Wait 30 seconds for cluster formation
sleep 30

# Verify again
ssh wizardsofts@10.0.0.84 'curl -s http://localhost:8265/api/cluster_status'
```

---

### 2. Data Cache Validation

**Objective:** Confirm parquet cache exists and is valid.

```bash
ssh wizardsofts@10.0.0.84 '
  ls -lh /home/wizardsofts/ray-outputs/data_cache/

  # Verify file integrity
  docker run --rm -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
    gibd-quant-agent-tarp-drl-training:v4-final \
    python -c "
import pandas as pd
df = pd.read_parquet(\"/home/ray/outputs/data_cache/dse_data_2015-01-01_2024-12-31.parquet\")
print(f\"Rows: {len(df)}, Columns: {len(df.columns)}\")
print(f\"Date range: {df[\"date\"].min()} to {df[\"date\"].max()}\")
print(f\"Tickers: {df[\"ticker\"].nunique()}\")
"
'
```

**Expected Output:**
```
-rw-r--r-- 1 root root 13M Jan  5 00:58 dse_data_2015-01-01_2024-12-31.parquet

Rows: 828305, Columns: 7
Date range: 2015-01-01 to 2024-12-30
Tickers: 456
```

**Success Criteria:**
- ✅ File exists: 12-13 MB size
- ✅ Rows: 828,305
- ✅ Tickers: 456
- ✅ Date range: 2015-01-01 to 2024-12-30

---

### 3. Disk Space Check

**Objective:** Ensure sufficient disk space on all servers.

```bash
# Check all servers
for server in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  echo "=== Server $server ==="
  ssh wizardsofts@$server 'df -h / | tail -1'
done
```

**Success Criteria:**
- ✅ Server 80: > 30 GB free (for Ray worker /tmp)
- ✅ Server 81: > 20 GB free
- ✅ Server 82: > 20 GB free
- ✅ Server 84: > 50 GB free (checkpoints + logs)

**If Low Disk Space:**
```bash
# Run automated cleanup
ssh wizardsofts@10.0.0.80 '~/cleanup_ray_workers_smart.sh 10.0.0.80'
ssh wizardsofts@10.0.0.81 '~/cleanup_ray_workers_smart.sh 10.0.0.81'
ssh wizardsofts@10.0.0.82 '~/cleanup_ray_workers_smart.sh 10.0.0.82'
ssh wizardsofts@10.0.0.84 'docker system prune -f --volumes'
```

---

### 4. Docker Image Verification

**Objective:** Confirm training image is available and has latest fixes.

```bash
ssh wizardsofts@10.0.0.84 '
  # Check image exists
  docker images | grep gibd-quant-agent-tarp-drl-training

  # Verify critical fixes are in image
  docker run --rm gibd-quant-agent-tarp-drl-training:v4-final sh -c "
    grep -q \"storage_path\" /app/src/portfolio/rl/train_ppo.py && echo \"✅ Ray Tune fix: storage_path\" || echo \"❌ Missing storage_path fix\"
    grep -q \"return checkpoint_dir\" /app/src/portfolio/rl/train_ppo.py && echo \"✅ Checkpoint fix: return checkpoint_dir\" || echo \"❌ Missing checkpoint fix\"
    test -f /app/src/portfolio/data/data_cache.py && echo \"✅ Data cache module exists\" || echo \"❌ Missing data cache\"
    test -f /app/src/utils/ray_resource_manager.py && echo \"✅ Resource manager exists\" || echo \"❌ Missing resource manager\"
  "
'
```

**Expected Output:**
```
gibd-quant-agent-tarp-drl-training   v4-final   579a5401e4e3   X hours ago   3.21GB
✅ Ray Tune fix: storage_path
✅ Checkpoint fix: return checkpoint_dir
✅ Data cache module exists
✅ Resource manager exists
```

---

## Infrastructure Validation

### Ray Cluster Health Check

**Objective:** Comprehensive cluster health validation.

```bash
ssh wizardsofts@10.0.0.84 '
  # Test distributed execution
  docker run --rm --network=host gibd-quant-agent-tarp-drl-training:v4-final \
    python -c "
import ray

# Connect to cluster
ray.init(\"ray://10.0.0.84:10001\", ignore_reinit_error=True)

# Get cluster info
print(f\"✅ Connected to Ray cluster\")
print(f\"Nodes: {len(ray.nodes())}\")
print(f\"CPUs: {ray.cluster_resources().get(\"CPU\", 0)}\")
print(f\"Memory: {ray.cluster_resources().get(\"memory\", 0) / 1e9:.2f} GB\")

# Test task execution
@ray.remote
def test_task(i):
    import time
    time.sleep(0.1)
    return i * i

# Run 100 tasks
results = ray.get([test_task.remote(i) for i in range(100)])
print(f\"✅ Distributed execution test PASSED: {len(results)} tasks completed\")

ray.shutdown()
"
'
```

**Success Criteria:**
- ✅ Connection successful
- ✅ Nodes: 4 (or more)
- ✅ CPUs: 20+ (depends on cluster config)
- ✅ All 100 tasks complete successfully

---

## Training Execution

### Configuration Review

**Training Parameters (2-Epoch Test):**
```yaml
# File: apps/gibd-quant-agent/config.yaml
output_dir: "outputs/tarp_drl_test"

data:
  start_date: "2015-01-01"
  end_date: "2024-12-31"
  train_end_date: "2021-12-31"
  val_end_date: "2022-12-31"

ppo:
  epochs: 2              # Quick test (150 for production)
  steps_per_epoch: 2048
  hidden_dim: 256
  lr_actor: 0.0003
  lr_critic: 0.001
  gamma: 0.99
  gae_lambda: 0.95
  clip_epsilon: 0.2
  entropy_coef: 0.01
  value_loss_coef: 0.5

use_ray: true
ray_address: "ray://10.0.0.84:10001"
num_cpus: 4
use_time_attention: true
validate_data: true
```

---

### Start Training (Background Process)

**Objective:** Start training with comprehensive logging and monitoring.

```bash
# SSH to Server 84
ssh wizardsofts@10.0.0.84

# Create training session
TRAINING_SESSION="tarp-drl-training-$(date +%Y%m%d-%H%M%S)"

# Start training in detached mode
docker run -d \
  --name "$TRAINING_SESSION" \
  --network=host \
  -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
  -e PYTHONUNBUFFERED=1 \
  gibd-quant-agent-tarp-drl-training:v4-final \
  2>&1 | tee /home/wizardsofts/training-logs/${TRAINING_SESSION}.log

# Get container ID
CONTAINER_ID=$(docker ps --filter name="$TRAINING_SESSION" --format "{{.ID}}")

echo "Training started: $TRAINING_SESSION"
echo "Container ID: $CONTAINER_ID"
echo "Log file: /home/wizardsofts/training-logs/${TRAINING_SESSION}.log"

# Return to local machine
exit
```

**Verification:**
```bash
ssh wizardsofts@10.0.0.84 "docker ps --filter name=tarp-drl-training"
```

**Expected Output:**
```
CONTAINER ID   IMAGE                                        STATUS         NAMES
abc123def456   gibd-quant-agent-tarp-drl-training:v4-final  Up 10 seconds  tarp-drl-training-20260105-170000
```

---

## Background Monitoring Strategy

### 1. Real-Time Log Monitoring (Terminal 1)

**Objective:** Stream training logs to track progress.

```bash
# Follow training logs
ssh wizardsofts@10.0.0.84 "docker logs -f tarp-drl-training-$(date +%Y%m%d)-* 2>&1"
```

**Key Log Patterns to Watch:**

| Pattern | Meaning | Action |
|---------|---------|--------|
| `✓ Loading data from parquet cache` | Data loaded from cache | ✅ Normal |
| `Loaded 828305 rows from cache` | Cache load successful | ✅ Normal |
| `Feature engineering complete: 39 features` | Features ready | ✅ Normal |
| `Connected to Ray cluster` | Ray connection OK | ✅ Normal |
| `Training iteration X` | PPO training progress | ✅ Normal |
| `Saved checkpoint` | Checkpoint saved | ✅ Normal |
| `ConnectionError: ray client connection timeout` | Ray cluster down | ❌ Error - Restart cluster |
| `DiskFull: No space left on device` | Disk full | ❌ Error - Run cleanup |
| `PermissionError: Cannot create directory` | Permission issue | ❌ Error - Check volume mounts |

---

### 2. Automated Monitoring Script (Terminal 2)

**Objective:** Continuous monitoring with alerts.

Create monitoring script:

```bash
cat > /tmp/monitor_training.sh <<'SCRIPT'
#!/bin/bash

# Configuration
CONTAINER_NAME="${1:-tarp-drl-training}"
CHECK_INTERVAL=60  # seconds
ALERT_DISK_THRESHOLD=10  # GB
ALERT_CPU_THRESHOLD=95   # percent

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  TARP-DRL Training Monitor"
echo "  Container: $CONTAINER_NAME"
echo "  Interval: ${CHECK_INTERVAL}s"
echo "=========================================="

while true; do
    clear
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Training Monitoring Dashboard"
    echo "=========================================="

    # 1. Container Status
    echo -e "\n${GREEN}[1] Container Status${NC}"
    CONTAINER_STATUS=$(docker ps --filter name="$CONTAINER_NAME" --format "{{.Status}}")
    if [ -n "$CONTAINER_STATUS" ]; then
        echo "  ✅ Running: $CONTAINER_STATUS"
    else
        echo -e "  ${RED}❌ Container not found or stopped${NC}"
        exit 1
    fi

    # 2. Latest Training Progress
    echo -e "\n${GREEN}[2] Training Progress${NC}"
    docker logs "$CONTAINER_NAME" 2>&1 | grep -E "Training iteration|Saved checkpoint|episode_reward" | tail -5

    # 3. Resource Usage
    echo -e "\n${GREEN}[3] Resource Usage${NC}"
    docker stats "$CONTAINER_NAME" --no-stream --format "  CPU: {{.CPUPerc}}\t Memory: {{.MemUsage}}"

    # 4. Disk Space
    echo -e "\n${GREEN}[4] Disk Space${NC}"
    for server in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
        DISK_FREE=$(ssh wizardsofts@$server 'df -h / | tail -1 | awk "{print \$4}"')
        DISK_USE=$(ssh wizardsofts@$server 'df -h / | tail -1 | awk "{print \$5}"')
        echo "  Server $server: $DISK_FREE free ($DISK_USE used)"
    done

    # 5. Ray Cluster Health
    echo -e "\n${GREEN}[5] Ray Cluster${NC}"
    RAY_STATUS=$(curl -s http://10.0.0.84:8265/api/cluster_status 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  Nodes: {data[\"result\"].get(\"node_count\", 0)}')
print(f'  CPUs: {data[\"result\"].get(\"resources\", {}).get(\"CPU\", 0)}')
" 2>/dev/null)
    if [ -n "$RAY_STATUS" ]; then
        echo "$RAY_STATUS"
    else
        echo -e "  ${YELLOW}⚠️  Ray dashboard not accessible${NC}"
    fi

    # 6. Recent Errors
    echo -e "\n${GREEN}[6] Recent Errors (last 5 min)${NC}"
    ERROR_COUNT=$(docker logs --since=5m "$CONTAINER_NAME" 2>&1 | grep -iE "error|exception|failed" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "  ${RED}⚠️  $ERROR_COUNT errors detected${NC}"
        docker logs --since=5m "$CONTAINER_NAME" 2>&1 | grep -iE "error|exception|failed" | tail -3
    else
        echo "  ✅ No errors in last 5 minutes"
    fi

    # 7. Checkpoint Status
    echo -e "\n${GREEN}[7] Checkpoints${NC}"
    CHECKPOINT_COUNT=$(ssh wizardsofts@10.0.0.84 'ls -1 /home/wizardsofts/ray-outputs/checkpoints/ 2>/dev/null | wc -l')
    echo "  Total checkpoints: $CHECKPOINT_COUNT"
    ssh wizardsofts@10.0.0.84 'ls -lht /home/wizardsofts/ray-outputs/checkpoints/ 2>/dev/null | head -4'

    echo ""
    echo "=========================================="
    echo "Next update in ${CHECK_INTERVAL}s (Ctrl+C to stop)"
    sleep $CHECK_INTERVAL
done
SCRIPT

chmod +x /tmp/monitor_training.sh
```

**Run Monitor:**
```bash
# Copy to Server 84
scp /tmp/monitor_training.sh wizardsofts@10.0.0.84:/home/wizardsofts/

# Run in background with nohup
ssh wizardsofts@10.0.0.84 "
  nohup /home/wizardsofts/monitor_training.sh tarp-drl-training-* \
    > /home/wizardsofts/training-monitor.log 2>&1 &
  echo \$! > /home/wizardsofts/monitor.pid
"

# View monitor output
ssh wizardsofts@10.0.0.84 "tail -f /home/wizardsofts/training-monitor.log"
```

---

### 3. Prometheus + Grafana Monitoring (Terminal 3)

**Objective:** Real-time metrics visualization.

**Grafana Dashboard Access:**
```bash
# SSH tunnel to Grafana
ssh -L 3002:localhost:3002 wizardsofts@10.0.0.84

# Open in browser
# http://localhost:3002
```

**Key Metrics to Monitor:**

1. **Ray Cluster Metrics:**
   - Active nodes count
   - CPU utilization per node
   - Memory usage per node
   - Object store usage
   - Task execution rate

2. **Training Metrics:**
   - Episode reward (increasing trend expected)
   - Actor loss
   - Critic loss
   - Training iteration count

3. **Resource Metrics:**
   - Disk usage % (should stay < 80%)
   - Ray worker /tmp directory size
   - Network I/O between nodes

**Grafana Dashboard:**
- **URL:** http://10.0.0.84:3002
- **Dashboard:** "Ray 2.53.0 Cluster Monitoring"
- **Credentials:** Check infrastructure/distributed-ml/monitoring/grafana/

---

### 4. Email/Slack Alerts (Optional)

**Objective:** Get notified on critical events.

**Prometheus Alertmanager Configuration:**

File: `infrastructure/distributed-ml/monitoring/alertmanager/config.yml`

```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'team@wizardsofts.com'
        from: 'alerts@wizardsofts.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@wizardsofts.com'
        auth_password: '${SMTP_PASSWORD}'

  - name: 'slack'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#ml-training-alerts'
        title: 'TARP-DRL Training Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

route:
  receiver: 'email'
  routes:
    - match:
        severity: critical
      receiver: 'slack'
```

---

## Troubleshooting Procedures

### Issue 1: Container Exits Immediately

**Symptoms:**
```bash
docker ps --filter name=tarp-drl-training
# No results
```

**Diagnosis:**
```bash
# Check container logs
docker logs $(docker ps -a --filter name=tarp-drl-training --format "{{.ID}}" | head -1)

# Check last exit code
docker inspect $(docker ps -a --filter name=tarp-drl-training --format "{{.ID}}" | head -1) \
  --format='{{.State.ExitCode}}'
```

**Common Causes & Fixes:**

1. **Ray Cluster Unreachable (Exit Code 1)**
   ```bash
   # Restart Ray cluster
   ssh wizardsofts@10.0.0.84 'cd ~/ray && docker-compose -f docker-compose.ray-head.yml restart'

   # Wait 30 seconds
   sleep 30

   # Retry training
   docker start $(docker ps -a --filter name=tarp-drl-training --format "{{.ID}}" | head -1)
   ```

2. **PostgreSQL Connection Failed (Exit Code 1)**
   ```bash
   # Check PostgreSQL status
   ssh wizardsofts@10.0.0.81 'docker ps --filter name=postgres'

   # Restart if needed
   ssh wizardsofts@10.0.0.81 'docker restart $(docker ps --filter name=postgres --format "{{.ID}}")'
   ```

3. **Data Cache Missing (Exit Code 2)**
   ```bash
   # Re-export cache
   ssh wizardsofts@10.0.0.84 "
   docker run --rm --network=host \
     -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
     gibd-quant-agent-tarp-drl-training:v4-final \
     python -c '
import sys
sys.path.insert(0, \"/app/src\")
from portfolio.data.data_cache import DataCache
cache = DataCache()
cache.export_to_cache(
    db_url=\"postgresql://ws_gibd:29Dec2#24@10.0.0.81:5432/ws_gibd_dse_daily_trades\",
    start_date=\"2015-01-01\",
    end_date=\"2024-12-31\"
)
'
   "
   ```

---

### Issue 2: Training Stuck (No Progress)

**Symptoms:**
- No new log entries for > 10 minutes
- Training iteration count not increasing

**Diagnosis:**
```bash
# Check if container is responsive
docker exec tarp-drl-training-* ps aux

# Check Ray task status
curl -s http://10.0.0.84:8265/api/tasks | python3 -m json.tool | grep state
```

**Fixes:**

1. **Ray Tasks Pending (Workers Overloaded)**
   ```bash
   # Scale up workers
   ssh wizardsofts@10.0.0.80 'cd ~/ray && docker-compose -f docker-compose.ray-workers-multi.yml up -d --scale ray-worker=6'
   ```

2. **Deadlock in Data Pipeline**
   ```bash
   # Get thread dump
   docker exec tarp-drl-training-* python -c "import sys, threading; print('\\n'.join([str(t) for t in threading.enumerate()]))"

   # Restart training from last checkpoint
   # (Checkpoints saved every 10 epochs)
   ```

---

### Issue 3: Disk Full During Training

**Symptoms:**
```
psycopg2.errors.DiskFull: could not write to file
```

**Immediate Fix:**
```bash
# Run emergency cleanup on all servers
for server in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
  echo "Cleaning $server..."
  ssh wizardsofts@$server '
    # Clean Ray workers
    for container in $(docker ps --filter name=ray-worker --format "{{.Names}}"); do
      docker exec "$container" sh -c "rm -rf /tmp/ray_tmp_* /tmp/pip-* /tmp/tmp* 2>/dev/null || true"
    done

    # Docker system prune
    docker system prune -f --volumes

    # Show freed space
    df -h / | tail -1
  '
done
```

**Long-Term Fix:**
- Training should use data cache (parquet), not PostgreSQL
- Verify `use_cache=True` in training config

---

## Post-Training Validation

### 1. Verify Training Completed

**Objective:** Confirm training finished all epochs.

```bash
ssh wizardsofts@10.0.0.84 '
  # Check final log entries
  docker logs tarp-drl-training-* 2>&1 | tail -50

  # Look for completion message
  docker logs tarp-drl-training-* 2>&1 | grep -i "training complete\|finished"
'
```

**Success Criteria:**
- ✅ Log shows: `Training complete` or `Finished X epochs`
- ✅ Container status: `Exited (0)` (clean exit)

---

### 2. Validate Checkpoints

**Objective:** Ensure checkpoints were saved correctly.

```bash
ssh wizardsofts@10.0.0.84 '
  # List checkpoints
  find /home/wizardsofts/ray-outputs/checkpoints/ -name "checkpoint.pt" -exec ls -lh {} \;

  # Count checkpoints (should be ~20 for 2-epoch test with checkpoint_freq=10)
  find /home/wizardsofts/ray-outputs/checkpoints/ -name "checkpoint.pt" | wc -l

  # Verify checkpoint integrity
  docker run --rm -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
    gibd-quant-agent-tarp-drl-training:v4-final \
    python -c "
import torch
import glob

checkpoints = glob.glob(\"/home/ray/outputs/checkpoints/**/checkpoint.pt\", recursive=True)
print(f\"Found {len(checkpoints)} checkpoints\")

for cp in checkpoints[-3:]:  # Check last 3
    try:
        data = torch.load(cp, map_location=\"cpu\")
        print(f\"✅ {cp.split(\"/\")[-2]}: {list(data.keys())}\")
    except Exception as e:
        print(f\"❌ {cp}: {e}\")
"
'
```

**Expected Output:**
```
Found 20 checkpoints
✅ checkpoint_000010: ['actor_state_dict', 'critic_state_dict', ...]
✅ checkpoint_000015: ['actor_state_dict', 'critic_state_dict', ...]
✅ checkpoint_000020: ['actor_state_dict', 'critic_state_dict', ...]
```

---

### 3. Extract Training Metrics

**Objective:** Get training performance summary.

```bash
ssh wizardsofts@10.0.0.84 '
  # Extract key metrics from logs
  docker logs tarp-drl-training-* 2>&1 | python3 -c "
import re, sys

logs = sys.stdin.read()

# Extract iterations
iterations = re.findall(r\"training_iteration\": (\d+)", logs)
print(f\"Training iterations: {len(iterations)}\")

# Extract rewards
rewards = re.findall(r\"episode_reward\": ([\d\.-]+)", logs)
if rewards:
    rewards = [float(r) for r in rewards]
    print(f\"Episode rewards: min={min(rewards):.2f}, max={max(rewards):.2f}, final={rewards[-1]:.2f}\")

# Extract timing
times = re.findall(r\"Completed in ([\d\.]+) seconds\", logs)
if times:
    print(f\"Total training time: {sum([float(t) for t in times]):.2f} seconds\")
"
'
```

---

### 4. Resource Usage Summary

**Objective:** Analyze resource consumption.

```bash
ssh wizardsofts@10.0.0.84 '
  # Disk space after training
  echo "=== Disk Space After Training ==="
  df -h / | tail -1

  # Checkpoint directory size
  echo -e "\n=== Checkpoint Directory Size ==="
  du -sh /home/wizardsofts/ray-outputs/checkpoints/

  # Ray worker /tmp sizes
  echo -e "\n=== Ray Worker /tmp Sizes ==="
  for server in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
    echo "Server $server:"
    ssh wizardsofts@$server "
      for container in \$(docker ps --filter name=ray-worker --format \"{{.Names}}\"); do
        size=\$(docker exec \"\$container\" du -sm /tmp 2>/dev/null | cut -f1)
        echo \"  \$container: \${size}MB\"
      done
    "
  done
'
```

---

## Next Steps

### For 2-Epoch Test Success:

1. **Review Results**
   - Analyze checkpoint files
   - Verify training metrics (episode_reward trend)
   - Check resource usage patterns

2. **Scale to 150 Epochs**
   - Update config.yaml: `epochs: 150`
   - Rebuild image with new config
   - Start full training run
   - Estimated time: ~12-18 hours (depends on cluster)

3. **Production Deployment**
   - Deploy best checkpoint to inference service
   - Monitor portfolio performance
   - Compare against baseline strategy

### For Training Failures:

1. **Capture State**
   - Save full container logs
   - Export Prometheus metrics
   - Document error messages

2. **Root Cause Analysis**
   - Review logs for error patterns
   - Check Ray dashboard for task failures
   - Analyze resource bottlenecks

3. **Iterate**
   - Apply fixes based on analysis
   - Re-run test
   - Update documentation with learnings

---

## Appendix: Quick Reference Commands

### Start Training
```bash
ssh wizardsofts@10.0.0.84 "
docker run -d --name tarp-drl-training-$(date +%Y%m%d-%H%M%S) \
  --network=host \
  -v /home/wizardsofts/ray-outputs:/home/ray/outputs \
  gibd-quant-agent-tarp-drl-training:v4-final
"
```

### Monitor Training
```bash
ssh wizardsofts@10.0.0.84 "docker logs -f tarp-drl-training-*"
```

### Stop Training
```bash
ssh wizardsofts@10.0.0.84 "docker stop tarp-drl-training-*"
```

### Clean Up
```bash
ssh wizardsofts@10.0.0.84 "
  docker rm tarp-drl-training-*
  rm -rf /home/wizardsofts/ray-outputs/checkpoints/*
"
```

### Ray Cluster Status
```bash
ssh wizardsofts@10.0.0.84 "curl -s http://localhost:8265/api/cluster_status | python3 -m json.tool"
```

---

## Contact & Support

- **Documentation:** `/docs/TARP_DRL_PRODUCTION_SOLUTION.md`
- **Ray Cluster:** [Ray Dashboard](http://10.0.0.84:8265)
- **Grafana:** [Metrics Dashboard](http://10.0.0.84:3002)
- **Logs:** `/home/wizardsofts/training-logs/`

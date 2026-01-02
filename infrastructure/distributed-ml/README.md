# WizardSofts Distributed ML Infrastructure

**Production-ready Ray cluster for distributed ML training, data processing, and parallel computing**

🚀 **Status:** ✅ Production (Phase 1 Complete)
🖥️ **Cluster:** 9 nodes | 25 CPUs | 44GB RAM
📊 **Dashboard:** http://10.0.0.84:8265

---

## Table of Contents

- [Quick Start](#quick-start)
- [When to Use Distributed Computing](#when-to-use-distributed-computing)
- [Architecture](#architecture)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Quick Start

### 1. Connect to Cluster

```python
import ray

# Connect to Ray cluster
ray.init(address="ray://10.0.0.84:10001")

print(f"Connected to cluster with {ray.available_resources()['CPU']} CPUs")
```

### 2. Run Distributed Task

```python
@ray.remote
def process_data(data_chunk):
    # Your processing logic
    return result

# Distribute work across cluster
futures = [process_data.remote(chunk) for chunk in data_chunks]
results = ray.get(futures)

ray.shutdown()
```

### 3. Run from Command Line

```bash
# Copy your script to Ray head
scp my_script.py wizardsofts@10.0.0.84:~/

# Execute on cluster
ssh wizardsofts@10.0.0.84 "docker cp ~/my_script.py ray-head:/tmp/ && docker exec ray-head python3 /tmp/my_script.py"
```

---

## When to Use Distributed Computing

### ✅ **Use Ray When:**

1. **Large Dataset Processing**
   - Dataset > 10GB
   - Millions of records to process
   - Parallel data transformations
   - ETL pipelines

2. **ML Model Training**
   - Hyperparameter tuning (100+ combinations)
   - Ensemble model training
   - Cross-validation across multiple folds
   - Large-scale feature engineering

3. **Compute-Intensive Tasks**
   - Monte Carlo simulations
   - Financial backtesting
   - Scientific computing
   - Batch predictions

4. **Time-Sensitive Operations**
   - Tasks that would take > 30 minutes sequentially
   - Need results in < 10% of sequential time
   - Real-time batch processing

### ❌ **Don't Use Ray When:**

- Dataset < 1GB (overhead not worth it)
- Task completes in < 5 minutes sequentially
- Simple CRUD operations
- Single-threaded I/O operations
- Tasks require persistent state

### 💡 **Rule of Thumb**

If your task would benefit from running on **4+ CPU cores in parallel**, use Ray.

**Speedup estimate:** Sequential time / (num_cpus * 0.8)
*0.8 accounts for ~20% overhead from distribution*

---

## Architecture

### Cluster Topology

```
┌─────────────────────────────────────────────────────────────┐
│ Server 84 (10.0.0.84) - Head Node + Workers                │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│ │ Ray Head     │  │ Ray Worker 1 │  │ Ray Worker 2 │  ...  │
│ │ Port: 6379   │  │ 3 CPUs, 8GB  │  │ 3 CPUs, 8GB  │       │
│ │ Dashboard:   │  └──────────────┘  └──────────────┘       │
│ │   8265       │                                            │
│ └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Server 80     │   │ Server 81     │   │ Server 82     │
│ 4 Workers     │   │ 2 Workers     │   │ 1 Worker      │
│ 8 CPUs, 24GB  │   │ 4 CPUs, 12GB  │   │ 2 CPUs, 6GB   │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Resource Distribution

| Server | Workers | CPUs | Memory | Purpose |
|--------|---------|------|--------|---------|
| 10.0.0.84 | 1 head + 3 workers | 11 | 26GB | Orchestration + Compute |
| 10.0.0.80 | 4 workers | 8 | 24GB | Primary compute |
| 10.0.0.81 | 2 workers | 4 | 12GB | Data-heavy tasks |
| 10.0.0.82 | 1 worker | 2 | 6GB | Lightweight tasks |
| **Total** | **11 containers** | **25** | **68GB** | - |

### Network Ports

- **6379** - Ray GCS (Global Control Service)
- **8265** - Ray Dashboard (monitoring)
- **10001** - Ray Client (Python API connection)
- **10002-10100** - Worker communication

---

## Usage Examples

See [examples/](examples/) directory for complete working examples.

### Example 1: Parallel Data Processing

```python
import ray
import pandas as pd

ray.init(address="ray://10.0.0.84:10001")

@ray.remote
def process_csv_chunk(file_path, start_row, num_rows):
    """Process a chunk of CSV file"""
    df = pd.read_csv(file_path, skiprows=start_row, nrows=num_rows)
    
    # Your processing logic
    df['new_column'] = df['value'] * 2
    df = df[df['amount'] > 100]
    
    return df

# Split large CSV into chunks
chunk_size = 100_000
total_rows = 10_000_000
chunks = range(0, total_rows, chunk_size)

# Process in parallel
futures = [
    process_csv_chunk.remote('data.csv', start, chunk_size) 
    for start in chunks
]

# Collect results
results = ray.get(futures)
final_df = pd.concat(results, ignore_index=True)

print(f"Processed {len(final_df)} rows across {len(chunks)} chunks")
ray.shutdown()
```

### Example 2: Hyperparameter Tuning

```python
import ray
from sklearn.ensemble import RandomForestClassifier

ray.init(address="ray://10.0.0.84:10001")

@ray.remote
def train_and_evaluate(params, X_train, y_train, X_test, y_test):
    """Train model with specific hyperparameters"""
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    return params, score

# Define hyperparameter grid
param_grid = [
    {'n_estimators': n, 'max_depth': d, 'min_samples_split': s}
    for n in [50, 100, 200]
    for d in [10, 20, 30]
    for s in [2, 5, 10]
]

# Distribute training across cluster (81 combinations)
futures = [
    train_and_evaluate.remote(params, X_train, y_train, X_test, y_test)
    for params in param_grid
]

# Get results
results = ray.get(futures)
best_params, best_score = max(results, key=lambda x: x[1])

print(f"Best params: {best_params}, Score: {best_score:.4f}")
ray.shutdown()
```

---

## API Reference

### Connection

```python
# Connect to cluster
ray.init(address="ray://10.0.0.84:10001")

# Check available resources
resources = ray.available_resources()
print(f"CPUs: {resources.get('CPU', 0)}")
print(f"Memory: {resources.get('memory', 0) / 1e9:.2f} GB")

# Get cluster info
nodes = ray.nodes()
print(f"Active nodes: {sum(1 for n in nodes if n['Alive'])}")

# Shutdown connection
ray.shutdown()
```

### Task Decoration

```python
# Basic task
@ray.remote
def my_task(x):
    return x * 2

# Task with resource requirements
@ray.remote(num_cpus=2, memory=1024*1024*1024)  # 1GB
def cpu_intensive_task(data):
    return process(data)

# Task with runtime environment
@ray.remote(runtime_env={"pip": ["scipy==1.11.0"]})
def scientific_task(data):
    from scipy import stats
    return stats.describe(data)
```

### Task Execution

```python
# Submit single task
future = my_task.remote(5)
result = ray.get(future)

# Submit multiple tasks
futures = [my_task.remote(i) for i in range(100)]
results = ray.get(futures)

# Submit with timeout
try:
    result = ray.get(future, timeout=30)  # 30 seconds
except ray.exceptions.GetTimeoutError:
    print("Task timed out")
```

---

## Deployment

### Deploy Additional Workers

```bash
# Deploy 4 workers on a new server
cd infrastructure/distributed-ml
./scripts/deploy-multi-workers.sh 10.0.0.85 4 2 6G 10.0.0.84:6379

# Arguments:
#   1. Server IP address
#   2. Number of workers
#   3. CPUs per worker  
#   4. Memory per worker (e.g., 6G, 8G)
#   5. Ray head address (optional, defaults to 10.0.0.84:6379)
```

### Check Cluster Status

```bash
# Via SSH
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Via Python
import ray
ray.init(address="ray://10.0.0.84:10001")
print(ray.nodes())
ray.shutdown()
```

---

## Monitoring

### Ray Dashboard

**URL:** http://10.0.0.84:8265

Features:
- Real-time cluster metrics
- Task execution timeline
- Resource utilization graphs
- Worker status
- Job history

### Command-Line Monitoring

```bash
# Cluster status
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Resource usage
ssh wizardsofts@10.0.0.84 "docker stats --no-stream"

# Worker logs
ssh wizardsofts@10.0.0.80 "docker logs ray-worker-1 --tail 100 -f"
```

---

## Troubleshooting

### Tasks Not Distributing

**Symptoms:** All tasks running on head node

**Solutions:**
1. Check workers are running: `ssh wizardsofts@10.0.0.80 "docker ps | grep ray-worker"`
2. Check worker logs: `ssh wizardsofts@10.0.0.80 "docker logs ray-worker-1 --tail 50"`
3. Verify firewall: `ssh wizardsofts@10.0.0.84 "sudo ufw status | grep 6379"`

### Out of Memory Errors

**Solutions:**
1. Reduce batch size
2. Specify memory requirements: `@ray.remote(memory=2*1024*1024*1024)`
3. Add more workers

### Slow Performance

**Diagnosis:**
```python
# Test overhead
import time
start = time.time()
futures = [benchmark_task.remote(1000) for _ in range(100)]
ray.get(futures)
elapsed = time.time() - start
print(f"Time per task: {elapsed/100:.4f}s")  # Should be < 0.1s
```

**Solutions:**
1. Increase task granularity (fewer, larger tasks)
2. Batch small tasks together
3. Check network latency: `ping 10.0.0.84`

---

## Best Practices

### 1. Task Granularity

**❌ Too Fine-Grained**
```python
futures = [process_row.remote(row) for row in df.iterrows()]  # 1 row per task
```

**✅ Optimal**
```python
chunk_size = 10_000
chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
futures = [process_chunk.remote(chunk) for chunk in chunks]  # 10k rows per task
```

**Rule:** Each task should run for **at least 1 second**.

### 2. Data Transfer

**❌ Passing Large Data as Arguments**
```python
large_df = pd.read_csv('huge.csv')  # 10GB
futures = [process.remote(large_df, i) for i in range(100)]  # Serializes 100 times!
```

**✅ Use Ray Object Store**
```python
large_df = pd.read_csv('huge.csv')
df_ref = ray.put(large_df)  # Upload once
futures = [process.remote(df_ref, i) for i in range(100)]  # Reference many times
```

### 3. Error Handling

```python
@ray.remote
def robust_task(data):
    try:
        return process(data)
    except Exception as e:
        return {"error": str(e), "data_id": data.id}

futures = [robust_task.remote(d) for d in data_list]
results = ray.get(futures)

# Retry failures
failures = [r for r in results if isinstance(r, dict) and 'error' in r]
```

### 4. Always Cleanup

```python
try:
    ray.init(address="ray://10.0.0.84:10001")
    # Your code here
finally:
    ray.shutdown()  # Release resources
```

---

## Performance Guidelines

### Expected Speedup

| Task Type | Sequential Time | Cluster Time (25 CPUs) | Speedup |
|-----------|----------------|------------------------|---------|
| Embarrassingly parallel | 100 min | 5-6 min | 17-20x |
| Data processing | 60 min | 4-5 min | 12-15x |
| Model training | 120 min | 8-10 min | 12-15x |
| I/O-bound tasks | 30 min | 15-20 min | 1.5-2x |

**Speedup formula:** `sequential_time / (num_cpus * efficiency)`
**Efficiency:** 0.7-0.8 for compute-bound, 0.2-0.3 for I/O-bound

---

## Migration Guide

### From Sequential to Distributed

**Before:**
```python
results = []
for item in large_dataset:
    result = process(item)
    results.append(result)
```

**After:**
```python
import ray
ray.init(address="ray://10.0.0.84:10001")

@ray.remote
def process_remote(item):
    return process(item)

futures = [process_remote.remote(item) for item in large_dataset]
results = ray.get(futures)
ray.shutdown()
```

---

## Additional Resources

- **Full Deployment Guide:** [docs/PHASE1_DEPLOYMENT_SUMMARY.md](../../docs/PHASE1_DEPLOYMENT_SUMMARY.md)
- **Implementation Plan:** [docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md](../../docs/DISTRIBUTED_ML_IMPLEMENTATION_PLAN.md)
- **Example Scripts:** [examples/](examples/)
- **Ray Documentation:** https://docs.ray.io/

---

## Quick Reference

```python
# Connection
ray.init(address="ray://10.0.0.84:10001")

# Submit tasks
futures = [task.remote(x) for x in data]
results = ray.get(futures)

# Check status
ray.available_resources()

# Cleanup
ray.shutdown()
```

**Dashboard:** http://10.0.0.84:8265

**Deploy Workers:** `./scripts/deploy-multi-workers.sh <ip> <num> <cpus> <mem>`

---

**Maintained by:** Claude Sonnet 4.5  
**Last Updated:** 2026-01-02  
**Phase:** 1 (Production)

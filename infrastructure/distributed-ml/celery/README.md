# Celery Task Queue - Background Job Orchestration

**Production-ready Celery setup for scheduling and orchestrating Ray distributed jobs**

🚀 **Status:** ✅ Phase 2 Ready
🖥️ **Components:** Redis Broker | 3 Worker Queues | Beat Scheduler | Flower Dashboard
📊 **Dashboard:** http://10.0.0.84:5555

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Task Types](#task-types)
- [Monitoring](#monitoring)
- [Deployment](#deployment)
- [Best Practices](#best-practices)

---

## Overview

### Why Celery + Ray?

**Ray alone provides:**
- ✅ Distributed computing across cluster
- ✅ Parallel task execution
- ✅ Resource scheduling

**Ray lacks:**
- ❌ No built-in task scheduler (cron-like)
- ❌ No task queuing and prioritization
- ❌ No retry logic and failure handling
- ❌ Limited support for long-running background tasks

**Celery provides:**
- ✅ **Celery Beat**: Cron-like scheduler for recurring tasks
- ✅ **Task Queues**: Priority-based task routing (ml, data, default)
- ✅ **Retry Logic**: Automatic retries with exponential backoff
- ✅ **Monitoring**: Flower dashboard for real-time monitoring
- ✅ **Integration**: Easy integration with web frameworks (Django, Flask, FastAPI)

### Combined Architecture

```
User/API Request → Celery Queue → Celery Worker → Ray Cluster
                                        ↓              ↓
                        Lightweight Task      Heavy Distributed Task
                              ↓                       ↓
                        Execute Locally      Distribute to 25 CPUs
```

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Server 84 - Celery Orchestration Layer                     │
│                                                              │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│ │ Redis Broker │  │ Celery Beat  │  │ Flower       │       │
│ │ Port: 6380   │  │ (Scheduler)  │  │ Port: 5555   │       │
│ └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ Celery Workers                                       │    │
│ │ - ML Queue (2 workers)      - concurrency: 2        │    │
│ │ - Data Queue (4 workers)    - concurrency: 4        │    │
│ │ - Default Queue (4 workers) - concurrency: 4        │    │
│ └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    Ray Cluster (25 CPUs)
                    For heavy distributed work
```

### Task Queues

| Queue | Purpose | Concurrency | Use Cases |
|-------|---------|-------------|-----------|
| **ml** | ML training & inference | 2 | Model training, hyperparameter search, batch predictions |
| **data** | Data processing | 4 | CSV processing, data aggregation, ETL |
| **default** | Lightweight tasks | 4 | Health checks, notifications, cleanup |

---

## Quick Start

### 1. Deploy Celery Infrastructure

```bash
cd infrastructure/distributed-ml
./scripts/deploy-celery.sh
```

This will:
- Deploy Redis broker on Server 84 (port 6380)
- Start 3 Celery worker queues (ml, data, default)
- Start Celery Beat scheduler
- Start Flower monitoring dashboard (port 5555)

### 2. Submit Your First Task

```python
from celery import Celery

# Connect to Celery
app = Celery(
    broker='redis://:PASSWORD@10.0.0.84:6380/0',
    backend='redis://:PASSWORD@10.0.0.84:6380/1'
)

# Submit a test task
result = app.send_task('tasks.simple_tasks.ping')
print(result.get(timeout=10))  # {'status': 'pong', 'worker': 'celery'}
```

### 3. Submit ML Training Task

```python
# Trigger distributed training on Ray cluster
result = app.send_task(
    'tasks.ml_tasks.distributed_training',
    kwargs={
        'model_config': {'n_estimators': 100, 'max_depth': 20, 'num_partitions': 4},
        'dataset_path': '/datasets/training_data'
    }
)

# Wait for result
training_result = result.get(timeout=600)  # 10 minutes
print(f"Training complete! Score: {training_result['avg_score']}")
```

---

## Usage Examples

### Example 1: Scheduled Daily Model Retraining

This task automatically runs every 24 hours via Celery Beat:

```python
# Already configured in tasks/celeryconfig.py
beat_schedule = {
    'daily-model-retraining': {
        'task': 'tasks.ml_tasks.retrain_models',
        'schedule': 3600 * 24,  # Daily
        'args': ()
    }
}
```

The task orchestrates multiple model retraining jobs:

```python
# From tasks/ml_tasks.py
@app.task
def retrain_models():
    models_to_retrain = [
        {'name': 'stock_predictor', 'dataset': '/datasets/stocks_latest.csv'},
        {'name': 'sentiment_analyzer', 'dataset': '/datasets/sentiment_latest.csv'}
    ]

    results = []
    for model_info in models_to_retrain:
        # Each triggers distributed training on Ray cluster
        result = distributed_training.delay(
            model_config={'n_estimators': 100, 'max_depth': 20},
            dataset_path=model_info['dataset']
        )
        results.append({'model': model_info['name'], 'task_id': result.id})

    return {'status': 'scheduled', 'models': results}
```

### Example 2: Hyperparameter Search

```python
from celery import Celery

app = Celery(broker='redis://:PASSWORD@10.0.0.84:6380/0')

# Define parameter grid
param_grid = [
    {'n_estimators': n, 'max_depth': d, 'min_samples_split': s}
    for n in [50, 100, 200]
    for d in [10, 20, 30]
    for s in [2, 5, 10]
]  # 81 combinations

# Submit to Celery (which orchestrates Ray)
result = app.send_task(
    'tasks.ml_tasks.hyperparameter_search',
    kwargs={
        'param_grid': param_grid,
        'dataset_path': '/datasets/training_data.csv'
    }
)

# Wait for best parameters
best_result = result.get(timeout=1800)  # 30 minutes
print(f"Best params: {best_result['best_params']}")
print(f"Best score: {best_result['best_score']:.4f}")
```

Behind the scenes, this distributes 81 training jobs across the Ray cluster (25 CPUs).

### Example 3: Hourly Data Processing

Configured to run every hour via Celery Beat:

```python
# From tasks/celeryconfig.py
beat_schedule = {
    'hourly-data-processing': {
        'task': 'tasks.data_tasks.process_new_data',
        'schedule': 3600,  # Every hour
        'args': ()
    }
}
```

The task processes all new CSV files in `/datasets/new/`:

```python
# From tasks/data_tasks.py
@app.task
def process_new_data():
    data_dir = '/datasets/new/'
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    results = []
    for file in files:
        # Each file processed in parallel on Ray cluster
        result = process_large_csv.delay(
            file_path=os.path.join(data_dir, file),
            output_path=f'/datasets/processed/{file}',
            transformations={'filter': {'amount': 100}, 'num_chunks': 5}
        )
        results.append({'file': file, 'task_id': result.id})

    return {'status': 'scheduled', 'files': results}
```

### Example 4: Batch Predictions

```python
# Submit batch prediction task
result = app.send_task(
    'tasks.ml_tasks.batch_predictions',
    kwargs={
        'model_path': '/models/trained_model.pkl',
        'data_batches': [
            '/datasets/batch_1.csv',
            '/datasets/batch_2.csv',
            '/datasets/batch_3.csv'
        ]
    }
)

# Get predictions
predictions = result.get(timeout=300)
print(f"Total predictions: {predictions['total_predictions']}")
```

### Example 5: Priority Tasks

Route urgent tasks to specific queues:

```python
# High-priority ML task
result = app.send_task(
    'tasks.ml_tasks.distributed_training',
    kwargs={'model_config': {...}, 'dataset_path': '...'},
    queue='ml',  # Route to ML queue
    priority=9   # Higher priority (0-9)
)

# Background data task
result = app.send_task(
    'tasks.data_tasks.process_large_csv',
    kwargs={...},
    queue='data',
    priority=5
)
```

---

## Task Types

### ML Tasks (Queue: `ml`)

**Located in:** `tasks/ml_tasks.py`

1. **`distributed_training`** - Train ML models across Ray cluster
   ```python
   app.send_task('tasks.ml_tasks.distributed_training', kwargs={
       'model_config': {'n_estimators': 100, 'max_depth': 20, 'num_partitions': 4},
       'dataset_path': '/datasets/training.csv'
   })
   ```

2. **`hyperparameter_search`** - Grid search with Ray parallelization
   ```python
   app.send_task('tasks.ml_tasks.hyperparameter_search', kwargs={
       'param_grid': [...],
       'dataset_path': '/datasets/training.csv'
   })
   ```

3. **`batch_predictions`** - Parallel inference on large datasets
   ```python
   app.send_task('tasks.ml_tasks.batch_predictions', kwargs={
       'model_path': '/models/model.pkl',
       'data_batches': ['/datasets/batch_1.csv', ...]
   })
   ```

4. **`retrain_models`** - Scheduled daily retraining (auto-triggered by Beat)

### Data Tasks (Queue: `data`)

**Located in:** `tasks/data_tasks.py`

1. **`process_large_csv`** - Process large CSV files in parallel chunks
   ```python
   app.send_task('tasks.data_tasks.process_large_csv', kwargs={
       'file_path': '/datasets/raw.csv',
       'output_path': '/datasets/processed.csv',
       'transformations': {'filter': {'amount': 100}, 'num_chunks': 10}
   })
   ```

2. **`aggregate_data`** - Aggregate from multiple data sources
   ```python
   app.send_task('tasks.data_tasks.aggregate_data', kwargs={
       'data_sources': ['/datasets/source1.csv', '/datasets/source2.csv'],
       'output_path': '/datasets/aggregated.csv'
   })
   ```

3. **`process_new_data`** - Scheduled hourly processing (auto-triggered by Beat)

### Simple Tasks (Queue: `default`)

**Located in:** `tasks/simple_tasks.py`

1. **`ping`** - Test task for connectivity
2. **`check_cluster_health`** - Monitor Ray cluster (auto-triggered every 5 min)
3. **`send_notification`** - Send alerts/notifications
4. **`cleanup_old_results`** - Clean up old data

---

## Monitoring

### Flower Dashboard

**URL:** http://10.0.0.84:5555
**Authentication:** Username/password from `.env.celery`

**Features:**
- Real-time task monitoring
- Worker status and resource usage
- Task history and success/failure rates
- Queue lengths and throughput
- Task details and tracebacks
- Worker control (restart, shutdown)

### Get Flower Credentials

```bash
ssh wizardsofts@10.0.0.84 "grep FLOWER /celery/.env.celery"
```

### Command-Line Monitoring

```bash
# Check all workers
ssh wizardsofts@10.0.0.84 "cd ~/celery && docker compose ps"

# View ML worker logs
ssh wizardsofts@10.0.0.84 "docker logs celery-worker-ml -f --tail 100"

# View Beat scheduler logs
ssh wizardsofts@10.0.0.84 "docker logs celery-beat -f --tail 100"

# Check Redis
ssh wizardsofts@10.0.0.84 "docker exec redis-celery redis-cli -a PASSWORD ping"
```

---

## Deployment

### Initial Deployment

```bash
cd infrastructure/distributed-ml
./scripts/deploy-celery.sh
```

### Update Tasks

After modifying task code:

```bash
# Copy updated tasks to Server 84
scp -r tasks/ wizardsofts@10.0.0.84:~/celery/

# Rebuild and restart workers
ssh wizardsofts@10.0.0.84 "cd ~/celery && docker compose build && docker compose restart"
```

### Scale Workers

Edit `docker-compose.celery.yml` to add more workers or change concurrency:

```yaml
celery-worker-ml:
  command: celery -A tasks worker --loglevel=info --queue=ml --concurrency=4  # Increased from 2
```

Then restart:

```bash
ssh wizardsofts@10.0.0.84 "cd ~/celery && docker compose up -d --force-recreate celery-worker-ml"
```

---

## Best Practices

### 1. Task Granularity

**❌ Too Many Small Tasks**
```python
# 1 million tiny tasks - excessive overhead
for i in range(1_000_000):
    app.send_task('process_item', args=[i])
```

**✅ Batch Tasks Appropriately**
```python
# 100 batches of 10k items each
batch_size = 10_000
for i in range(0, 1_000_000, batch_size):
    app.send_task('process_batch', args=[i, i+batch_size])
```

### 2. Use Appropriate Queue

```python
# ML training → ml queue
app.send_task('tasks.ml_tasks.distributed_training', kwargs={...}, queue='ml')

# Data processing → data queue
app.send_task('tasks.data_tasks.process_large_csv', kwargs={...}, queue='data')

# Health checks → default queue
app.send_task('tasks.simple_tasks.check_cluster_health', queue='default')
```

### 3. Set Timeouts

```python
# Set task timeout
result = app.send_task('long_running_task', kwargs={...})

try:
    output = result.get(timeout=600)  # 10 minutes
except TimeoutError:
    print("Task timed out")
```

### 4. Handle Failures Gracefully

Tasks automatically retry up to 3 times with exponential backoff (configured in task decorator):

```python
@app.task(bind=True, max_retries=3)
def distributed_training(self, ...):
    try:
        # Task logic
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### 5. Monitor Queue Lengths

Check Flower dashboard for queue buildup. If queues are consistently full:
- Add more workers
- Increase worker concurrency
- Optimize task execution time

---

## Configuration

### Environment Variables

**`.env.celery`**
```bash
REDIS_PASSWORD=<redis-password>
FLOWER_USER=admin
FLOWER_PASSWORD=<flower-password>
```

**`.env.redis`**
```bash
REDIS_PASSWORD=<same-as-celery>
```

### Celery Configuration

Edit `tasks/celeryconfig.py` to customize:
- Task routing
- Time limits
- Retry behavior
- Beat schedule
- Queue priorities

---

## Troubleshooting

### Workers Not Processing Tasks

**Check worker status:**
```bash
ssh wizardsofts@10.0.0.84 "docker ps | grep celery"
```

**Check worker logs:**
```bash
ssh wizardsofts@10.0.0.84 "docker logs celery-worker-ml --tail 100"
```

**Restart workers:**
```bash
ssh wizardsofts@10.0.0.84 "cd ~/celery && docker compose restart"
```

### Tasks Failing

**View task traceback in Flower:**
- Go to http://10.0.0.84:5555
- Click on failed task
- View detailed error traceback

**Check Ray cluster is accessible:**
```bash
curl http://10.0.0.84:8265/api/cluster_status
```

### Redis Connection Issues

**Test Redis:**
```bash
ssh wizardsofts@10.0.0.84 "docker exec redis-celery redis-cli -a PASSWORD ping"
```

**Check Redis logs:**
```bash
ssh wizardsofts@10.0.0.84 "docker logs redis-celery --tail 100"
```

---

## Additional Resources

- **Celery Documentation:** https://docs.celeryq.dev/
- **Flower Documentation:** https://flower.readthedocs.io/
- **Ray Integration:** [../README.md](../README.md)
- **Deployment Guide:** [../scripts/deploy-celery.sh](../scripts/deploy-celery.sh)

---

**Maintained by:** Claude Sonnet 4.5
**Last Updated:** 2026-01-02
**Phase:** 2 (Ready for Deployment)

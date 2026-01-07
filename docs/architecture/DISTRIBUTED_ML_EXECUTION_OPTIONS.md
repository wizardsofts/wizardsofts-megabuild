# Distributed Python/ML Execution Framework Analysis

**Date:** 2026-01-02
**Infrastructure:** 4 servers + additional laptops (on-premises, 10.0.0.0/24)

## Executive Summary

After analyzing current distributed computing frameworks, **three primary options** are recommended for your infrastructure:

1. **Ray** - Best for ML/AI workloads with GPU support
2. **Celery + Redis** - Best for task queuing and background jobs
3. **Dask** - Best for data processing and scaling existing Python code

For small-scale heterogeneous clusters like yours, **Ray** and **Celery** are the top choices depending on your workload type.

---

## Infrastructure Overview

| Server | IP | Hardware | Current Role |
|--------|-----|----------|--------------|
| Server 80 | 10.0.0.80 | Unknown | GIBD Services |
| Server 81 | 10.0.0.81 | Unknown | Database Server |
| Server 82 | 10.0.0.82 | Laptop (Ubuntu 24.04) | Monitoring (Prometheus/Grafana) |
| Server 84 | 10.0.0.84 | HP Server | Production (Appwrite, GitLab, microservices) |
| Hetzner | 178.63.44.221 | Cloud VPS | External services |
| Additional | TBD | Laptops | Worker nodes |

**Key Constraints:**
- Small cluster (4-10 nodes)
- Heterogeneous hardware (servers + laptops)
- On-premises network (10.0.0.0/24)
- Existing Docker + Prometheus + Grafana stack
- Security-conscious environment

---

## Option 1: Ray (Recommended for ML/AI Workloads)

### Overview
Ray is a unified framework for scaling AI and Python applications with a focus on distributed ML training, hyperparameter tuning, and model serving.

### Architecture
```
┌─────────────────────────────────────────────────┐
│ Server 84 (Head Node)                          │
│ - Ray Head (scheduler + object store)          │
│ - Ray Dashboard (port 8265)                     │
└─────────────────────────────────────────────────┘
         │
         ├────────────────────────────────────────┐
         │                                        │
┌────────▼────────┐  ┌──────────────┐  ┌─────────▼────────┐
│ Server 80       │  │ Server 82    │  │ Laptop Workers   │
│ Ray Worker      │  │ Ray Worker   │  │ Ray Workers      │
│ (CPU/GPU)       │  │ (CPU only)   │  │ (CPU only)       │
└─────────────────┘  └──────────────┘  └──────────────────┘
```

### Key Features
- **ML-Native**: Built-in support for PyTorch, TensorFlow, scikit-learn, XGBoost
- **Auto-scaling**: Dynamically add/remove workers based on workload
- **GPU Support**: Efficient GPU scheduling and memory management
- **Fault Tolerance**: Automatic task retry and recovery
- **Dashboard**: Web UI for monitoring (similar to your Grafana setup)

### Installation
```bash
# On all nodes
pip install "ray[default]"

# Start head node (Server 84)
ray start --head --port=6379 --dashboard-host=0.0.0.0 --dashboard-port=8265

# Start worker nodes (Server 80, 82, laptops)
ray start --address='10.0.0.84:6379'
```

### Docker Compose Example
```yaml
# docker-compose.ray.yml
version: '3.8'

services:
  ray-head:
    image: rayproject/ray:latest
    container_name: ray-head
    command: ray start --head --port=6379 --dashboard-host=0.0.0.0
    ports:
      - "6379:6379"      # Ray GCS
      - "8265:8265"      # Dashboard
      - "10001:10001"    # Ray Client
    volumes:
      - ./ray-storage:/tmp/ray
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    networks:
      - ray-network
    security_opt:
      - no-new-privileges:true

networks:
  ray-network:
    driver: bridge
```

### Use Cases
- **Distributed ML Training**: Train models across multiple GPUs/machines
- **Hyperparameter Tuning**: Parallel hyperparameter search (Ray Tune)
- **Data Processing**: Distributed data preprocessing (Ray Data)
- **Model Serving**: Deploy models with Ray Serve
- **Reinforcement Learning**: Distributed RL (Ray RLlib)

### Pros
✅ Python-native, minimal code changes
✅ Excellent ML/AI library integration
✅ Built-in monitoring dashboard
✅ Handles heterogeneous hardware well
✅ Good documentation and active community
✅ Works with your existing Prometheus (Ray metrics exporter available)

### Cons
❌ Higher memory overhead (~1GB per node)
❌ Overkill if you only need simple task queuing
❌ Steeper learning curve for non-ML workloads

### When to Choose Ray
- Primary workload is ML/AI (training, tuning, inference)
- Need GPU scheduling and management
- Want to scale existing ML code with minimal changes
- Have ≥2GB RAM per node available

### Monitoring Integration
```python
# Ray exposes Prometheus metrics
# Add to prometheus.yml on Server 84:
scrape_configs:
  - job_name: 'ray'
    static_configs:
      - targets: ['10.0.0.84:8265']
```

---

## Option 2: Celery + Redis (Recommended for Task Queuing)

### Overview
Celery is a distributed task queue focused on asynchronous job execution, ideal for background processing and scheduled tasks.

### Architecture
```
┌─────────────────────────────────────────────────┐
│ Server 84 (Broker + Beat)                      │
│ - Redis (message broker)                        │
│ - Celery Beat (scheduler)                       │
│ - Flower Dashboard (port 5555)                  │
└─────────────────────────────────────────────────┘
         │
         ├────────────────────────────────────────┐
         │                                        │
┌────────▼────────┐  ┌──────────────┐  ┌─────────▼────────┐
│ Server 80       │  │ Server 82    │  │ Laptop Workers   │
│ Celery Worker   │  │ Celery Worker│  │ Celery Workers   │
│ (4 processes)   │  │ (2 processes)│  │ (2 processes ea.)│
└─────────────────┘  └──────────────┘  └──────────────────┘
```

### Key Features
- **Simple & Proven**: Battle-tested in production for 15+ years
- **Task Scheduling**: Cron-like periodic tasks (Celery Beat)
- **Priority Queues**: Route tasks to specific workers
- **Result Backend**: Store task results in Redis/PostgreSQL
- **Monitoring**: Flower web dashboard

### Installation
```bash
# On all nodes
pip install celery[redis] flower

# Redis on Server 84 (via Docker)
docker run -d --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --requirepass YOUR_PASSWORD

# Start worker on each node
celery -A your_app worker --loglevel=info --concurrency=4

# Start Flower dashboard (Server 84)
celery -A your_app flower --port=5555
```

### Docker Compose Example
```yaml
# docker-compose.celery.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: celery-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    deploy:
      resources:
        limits:
          memory: 512M
    security_opt:
      - no-new-privileges:true
    networks:
      - celery-network

  celery-beat:
    image: your-app:latest
    container_name: celery-beat
    command: celery -A app beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - redis
    networks:
      - celery-network

  flower:
    image: your-app:latest
    container_name: celery-flower
    command: celery -A app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - redis
    networks:
      - celery-network

volumes:
  redis-data:

networks:
  celery-network:
    driver: bridge
```

### Use Cases
- **Background Jobs**: Email sending, report generation, data exports
- **Scheduled Tasks**: Daily data aggregation, periodic scraping
- **Async API Operations**: Long-running API requests
- **Data Pipeline**: ETL workflows with task dependencies
- **Webhooks**: Processing incoming webhook events

### Pros
✅ Extremely lightweight (~50MB RAM per worker)
✅ Simple to understand and debug
✅ Works well with FastAPI/Flask/Django
✅ Redis already familiar (you use it for caching)
✅ Excellent for heterogeneous hardware
✅ Can run on laptops without issues

### Cons
❌ Not optimized for ML training
❌ No built-in GPU support
❌ Task-level parallelism only (not data parallelism)
❌ Manual scaling (no auto-scaling)

### When to Choose Celery
- Primary workload is asynchronous tasks (not ML training)
- Need scheduled/periodic jobs
- Want minimal resource overhead
- Already using FastAPI/Flask/Django
- Need proven, stable solution

### Example Code
```python
# tasks.py
from celery import Celery

app = Celery('tasks', broker='redis://:password@10.0.0.84:6379/0')

@app.task
def train_model(dataset_path):
    """Train ML model asynchronously"""
    # Your training code here
    return {"status": "complete", "accuracy": 0.95}

@app.task
def process_data(file_path):
    """Process large dataset"""
    # Your processing code here
    return {"processed": True}

# Schedule periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'daily-retraining': {
        'task': 'tasks.train_model',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': ('/data/latest.csv',)
    }
}
```

---

## Option 3: Dask (Best for Data Processing)

### Overview
Dask is a Python library for parallel computing that scales NumPy, Pandas, and Scikit-learn to multi-core and distributed systems.

### Architecture
```
┌─────────────────────────────────────────────────┐
│ Server 84 (Scheduler)                          │
│ - Dask Scheduler                                │
│ - Dask Dashboard (port 8787)                    │
└─────────────────────────────────────────────────┘
         │
         ├────────────────────────────────────────┐
         │                                        │
┌────────▼────────┐  ┌──────────────┐  ┌─────────▼────────┐
│ Server 80       │  │ Server 82    │  │ Laptop Workers   │
│ Dask Worker     │  │ Dask Worker  │  │ Dask Workers     │
│ (8 threads)     │  │ (4 threads)  │  │ (4 threads ea.)  │
└─────────────────┘  └──────────────┘  └──────────────────┘
```

### Key Features
- **Familiar API**: Drop-in replacement for Pandas/NumPy
- **Lazy Evaluation**: Builds task graph before execution
- **Data Parallelism**: Automatically parallelize data operations
- **Out-of-Core**: Process datasets larger than RAM
- **Dashboard**: Real-time task graph visualization

### Installation
```bash
# On all nodes
pip install "dask[distributed]"

# Start scheduler (Server 84)
dask-scheduler --host 10.0.0.84 --port 8786 --dashboard-address :8787

# Start workers (Server 80, 82, laptops)
dask-worker 10.0.0.84:8786 --nthreads 4 --memory-limit 4GB
```

### Use Cases
- **Large Dataset Processing**: CSV, Parquet files larger than RAM
- **Parallel Pandas**: Scale Pandas operations across cluster
- **Feature Engineering**: Distributed feature computation
- **Time Series Analysis**: Process large time series data
- **Batch Predictions**: Parallelize model inference

### Pros
✅ Minimal code changes (familiar Pandas/NumPy API)
✅ Excellent for data-heavy workloads
✅ Built-in dashboard similar to Grafana
✅ Integrates with scikit-learn, XGBoost
✅ Good for laptops (intelligent memory management)

### Cons
❌ Not designed for deep learning
❌ Limited GPU support compared to Ray
❌ Overkill for simple task queuing
❌ Learning curve for task graph optimization

### When to Choose Dask
- Primary workload is data processing (ETL, aggregation)
- Working with large Pandas/NumPy datasets
- Need to scale existing data science code
- Want familiar API (minimal learning curve)

### Example Code
```python
import dask.dataframe as dd
from dask.distributed import Client

# Connect to cluster
client = Client('10.0.0.84:8786')

# Read large CSV across cluster
df = dd.read_csv('s3://bucket/*.csv')

# Familiar Pandas operations (executed in parallel)
result = df.groupby('category').agg({'value': 'mean'}).compute()

# Parallel machine learning
from dask_ml.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {'n_estimators': [100, 200, 300]}
search = GridSearchCV(RandomForestClassifier(), param_grid, cv=5)
search.fit(X, y)  # Distributed across cluster
```

---

## Option 4: Prefect (Workflow Orchestration)

### Overview
Modern workflow orchestration framework focused on data pipelines and ML workflows with Python-native approach.

### Key Features
- **Dynamic Workflows**: No rigid DAGs, pure Python
- **Built-in Retries**: Automatic failure handling
- **Parameter Scheduling**: Pass runtime parameters
- **Hybrid Execution**: Cloud + on-premises workers
- **Modern UI**: Clean web dashboard

### When to Choose Prefect
- Need sophisticated workflow orchestration
- Want modern alternative to Airflow
- Complex ML pipelines with dependencies
- Need hybrid cloud/on-prem execution

### Pros
✅ Most modern/developer-friendly
✅ Excellent for complex ML pipelines
✅ Good documentation and UX

### Cons
❌ Relatively new (less mature than Celery/Dask)
❌ Cloud-first design (self-hosted available but complex)
❌ Heavier than Celery for simple tasks

---

## Option 5: Apache Airflow (Not Recommended)

### Why Not Recommended
- **Too Heavy**: Requires PostgreSQL, Redis, multiple components
- **Complex Setup**: Overkill for small clusters
- **Resource Intensive**: ~2GB RAM minimum per component
- **Better Alternatives**: Prefect/Celery are simpler for your scale

Use Airflow only if you have strict enterprise requirements or existing Airflow expertise.

---

## Hybrid Approach (Recommended)

For maximum flexibility, consider combining frameworks:

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│ Server 84 (Orchestration Layer)                        │
│ - Celery Beat (scheduling)                              │
│ - Redis (message broker)                                │
│ - Ray Head (ML cluster)                                 │
│ - Prometheus + Grafana (monitoring)                     │
└─────────────────────────────────────────────────────────┘
         │
         ├──────────────────────────────────────────────┐
         │                                              │
┌────────▼────────┐  ┌──────────────┐  ┌───────────────▼──┐
│ Server 80       │  │ Server 82    │  │ Laptop Workers   │
│ - Celery Worker │  │ - Celery     │  │ - Celery Workers │
│ - Ray Worker    │  │ - Ray Worker │  │ - Ray Workers    │
└─────────────────┘  └──────────────┘  └──────────────────┘
```

### Workflow
1. **Celery** schedules ML training job at 2 AM daily
2. Celery task triggers **Ray** to distribute training across GPUs
3. **Prometheus** monitors both Celery and Ray metrics
4. **Grafana** shows unified dashboard

### Example
```python
# Celery task that uses Ray for ML training
from celery import Celery
import ray

app = Celery('ml_tasks', broker='redis://10.0.0.84:6379/0')

@app.task
def distributed_training(dataset_path):
    # Connect to Ray cluster
    ray.init(address='10.0.0.84:6379')

    # Use Ray for distributed training
    @ray.remote
    def train_model_partition(data_partition):
        # Training logic here
        return model

    # Distribute across cluster
    futures = [train_model_partition.remote(partition)
               for partition in load_partitions(dataset_path)]

    models = ray.get(futures)
    return aggregate_models(models)

# Schedule via Celery Beat
app.conf.beat_schedule = {
    'daily-training': {
        'task': 'ml_tasks.distributed_training',
        'schedule': crontab(hour=2, minute=0),
        'args': ('/data/latest.csv',)
    }
}
```

---

## Comparison Matrix

| Feature | Ray | Celery + Redis | Dask | Prefect |
|---------|-----|----------------|------|---------|
| **Primary Use Case** | ML/AI training | Task queuing | Data processing | Workflow orchestration |
| **Ease of Setup** | Medium | Easy | Easy | Medium |
| **Resource Usage** | High (1-2GB/node) | Low (50MB/node) | Medium (500MB/node) | Medium |
| **GPU Support** | Excellent | None | Limited | Via integrations |
| **Dashboard** | ✅ Built-in | ✅ Flower | ✅ Built-in | ✅ Built-in |
| **Fault Tolerance** | Automatic | Manual config | Automatic | Excellent |
| **Learning Curve** | Medium | Low | Low (if know Pandas) | Medium |
| **Laptop-Friendly** | ⚠️ OK | ✅ Excellent | ✅ Good | ✅ Good |
| **Prometheus Export** | ✅ Yes | ⚠️ Via custom | ✅ Yes | ✅ Yes |
| **Docker Support** | ✅ Official images | ✅ Easy | ✅ Good | ✅ Official images |
| **Maturity** | Mature (2017) | Very mature (2009) | Mature (2014) | New (2018) |
| **Community** | Large | Very large | Large | Growing |
| **Documentation** | Excellent | Excellent | Good | Excellent |

---

## Recommendations by Use Case

### Use Case 1: Distributed ML Model Training
**Recommended:** Ray

You need to train ML models across multiple servers/GPUs.

**Setup:**
1. Server 84: Ray head node
2. Servers 80, 82, laptops: Ray workers
3. Use Ray Tune for hyperparameter optimization
4. Export metrics to existing Prometheus

### Use Case 2: Daily Data Processing & ETL
**Recommended:** Celery + Redis

You need scheduled tasks like data scraping, report generation, model retraining.

**Setup:**
1. Server 84: Redis + Celery Beat
2. All nodes: Celery workers
3. Use Flower dashboard for monitoring
4. Integrate with existing services via API calls

### Use Case 3: Large Dataset Processing
**Recommended:** Dask

You work with massive CSV/Parquet files that don't fit in memory.

**Setup:**
1. Server 84: Dask scheduler
2. Server 81 (database server): Perfect for Dask workers (close to data)
3. Other servers: Additional workers
4. Use Dask DataFrame for Pandas-like operations

### Use Case 4: Complex ML Pipelines
**Recommended:** Hybrid (Celery + Ray)

You need both scheduling and distributed ML training.

**Setup:**
1. Server 84: Redis + Celery Beat + Ray head
2. All nodes: Celery workers + Ray workers
3. Celery triggers Ray jobs
4. Unified monitoring via Prometheus/Grafana

---

## Implementation Roadmap

### Phase 1: Proof of Concept (Week 1)
1. Choose framework based on primary use case
2. Set up head node on Server 84
3. Add Server 80 as first worker
4. Test with simple job
5. Verify monitoring integration

### Phase 2: Cluster Expansion (Week 2)
1. Add Server 82 (laptop) as worker
2. Configure resource limits for laptop
3. Add first additional laptop
4. Test heterogeneous workload distribution
5. Tune performance

### Phase 3: Production Hardening (Week 3-4)
1. Add security (TLS, authentication)
2. Configure fail2ban for new services
3. Set up backup/recovery procedures
4. Document operational procedures
5. Create alerting rules in Prometheus

### Phase 4: Laptop Fleet Integration (Week 5+)
1. Create automated worker deployment script
2. Add remaining laptops
3. Implement dynamic worker registration
4. Test fault tolerance (laptop sleep/wake)
5. Optimize scheduling for laptop availability

---

## Security Considerations

Based on your existing security practices (fail2ban, firewall rules):

### Network Security
```bash
# UFW rules for Ray (if chosen)
sudo ufw allow from 10.0.0.0/24 to any port 6379  # Ray GCS
sudo ufw allow from 10.0.0.0/24 to any port 8265  # Ray Dashboard

# UFW rules for Celery (if chosen)
sudo ufw allow from 10.0.0.0/24 to any port 6379  # Redis
sudo ufw allow from 10.0.0.0/24 to any port 5555  # Flower

# UFW rules for Dask (if chosen)
sudo ufw allow from 10.0.0.0/24 to any port 8786  # Dask scheduler
sudo ufw allow from 10.0.0.0/24 to any port 8787  # Dask dashboard
```

### Container Security
```yaml
# Apply to all distributed framework containers
services:
  worker:
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '4'
        reservations:
          memory: 2G
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed
```

### Authentication
- **Ray**: Use `--redis-password` for cluster authentication
- **Celery**: Use Redis `requirepass` directive
- **Dask**: Use `--tls-ca-file`, `--tls-cert`, `--tls-key` for TLS

### Monitoring Alerts
```yaml
# Add to prometheus.yml
groups:
  - name: distributed_computing
    rules:
      - alert: WorkerDown
        expr: up{job="ray"} == 0
        for: 5m
        annotations:
          summary: "Ray worker {{ $labels.instance }} is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        annotations:
          summary: "Worker {{ $labels.instance }} high memory usage"
```

---

## Cost Analysis (Resource Requirements)

### Ray Setup
- **Server 84 (head):** 4GB RAM, 2 CPU cores
- **Server 80 (worker):** 2-8GB RAM, 4+ CPU cores
- **Server 82 (worker):** 2GB RAM, 2 CPU cores
- **Laptops (workers):** 2GB RAM, 2 CPU cores each
- **Total:** ~12-20GB RAM across cluster

### Celery Setup
- **Server 84 (Redis + Beat):** 512MB RAM, 1 CPU core
- **Workers:** 50-100MB RAM per worker process
- **Total:** ~1-2GB RAM across cluster (extremely lightweight)

### Dask Setup
- **Server 84 (scheduler):** 1GB RAM, 1 CPU core
- **Workers:** 2-4GB RAM, 2-4 CPU cores
- **Total:** ~8-16GB RAM across cluster

---

## Next Steps

1. **Decide on primary use case:**
   - ML training → Ray
   - Task queuing → Celery
   - Data processing → Dask
   - Complex workflows → Hybrid

2. **Review this document with team**

3. **Create feature branch:**
   ```bash
   cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
   git worktree add ../wizardsofts-megabuild-worktrees/feature-distributed-ml -b feature/distributed-ml-setup
   ```

4. **Start with PoC on Server 84 + Server 80**

5. **Update this document with findings**

---

## References

- [Ray Documentation](https://docs.ray.io/)
- [Ray GitHub](https://github.com/ray-project/ray)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Celery GitHub](https://github.com/celery/celery)
- [Dask Documentation](https://distributed.dask.org/)
- [Dask GitHub](https://github.com/dask/distributed)
- [Prefect Documentation](https://docs.prefect.io/)
- [Top 5 Frameworks for Distributed Machine Learning](https://www.kdnuggets.com/top-5-frameworks-for-distributed-machine-learning)
- [Kubeflow](https://www.kubeflow.org/) (if you later move to Kubernetes)

---

**Document Status:** Draft for review
**Last Updated:** 2026-01-02
**Next Review:** After PoC completion

# Distributed ML/Data Processing - Implementation Plan

**Date:** 2026-01-02
**Project:** WizardSofts Megabuild - Distributed Computing Infrastructure
**Objective:** Implement distributed ML training and data processing across 4 servers + laptops

## Executive Summary

This plan implements a distributed computing infrastructure using **Ray** (Phase 1 MVP) for ML/data processing, with **Celery** integration (Phase 2) for background scheduling and orchestration.

**Timeline:** 6-8 weeks
**Servers:** 4 (10.0.0.80, 81, 82, 84) + additional laptops
**Technologies:** Ray, Celery, Redis, Docker, Prometheus

---

## Architecture Overview

### Final Architecture (After All Phases)

```
┌────────────────────────────────────────────────────────────┐
│ Server 84 (HP Production) - Orchestration Layer           │
│ ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌────────────┐ │
│ │ Ray Head   │ │ Redis      │ │ Celery   │ │ Prometheus │ │
│ │ (Scheduler)│ │ (Broker)   │ │ Beat     │ │ + Grafana  │ │
│ │ Port: 6379 │ │ Port: 6380 │ │          │ │ :9090/3002 │ │
│ └────────────┘ └────────────┘ └──────────┘ └────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Ray Dashboard (8265) | Flower Dashboard (5555)        │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼─────────┐
│ Server 80      │  │ Server 81      │  │ Server 82      │
│ GIBD Services  │  │ Database       │  │ Monitoring     │
├────────────────┤  ├────────────────┤  ├────────────────┤
│ Ray Worker     │  │ Ray Worker     │  │ Ray Worker     │
│ 4 CPUs, 8GB    │  │ 8 CPUs, 16GB   │  │ 2 CPUs, 4GB    │
│                │  │ (Data-heavy)   │  │ (Laptop)       │
│ Celery Worker  │  │ Celery Worker  │  │ Celery Worker  │
│ 2 processes    │  │ 4 processes    │  │ 1 process      │
└────────────────┘  └────────────────┘  └────────────────┘
                            │
        ┌───────────────────┴────────────────┐
        │                                    │
┌───────▼────────┐                  ┌────────▼────────┐
│ Laptop Worker 1│                  │ Laptop Worker N │
│ 2 CPUs, 4GB    │     ...          │ 2 CPUs, 4GB     │
│ Ray Worker     │                  │ Ray Worker      │
│ Celery Worker  │                  │ Celery Worker   │
└────────────────┘                  └─────────────────┘
```

### Data Flow

```
User/Scheduler → Celery Beat → Celery Task → Ray Submit
                                              ↓
                                        Ray Scheduler
                                              ↓
                           ┌──────────────────┼──────────────┐
                           ▼                  ▼              ▼
                    Worker 80           Worker 81      Worker 82
                           │                  │              │
                           └──────────────────┴──────────────┘
                                              ▼
                                        Results → S3/Storage
                                              ↓
                                    Metrics → Prometheus
```

---

## Phase 1: Ray MVP (Weeks 1-2)

**Goal:** Set up Ray cluster with Server 84 (head) + Server 80 (worker) and run first distributed ML job

### 1.1 Pre-Implementation Checklist

#### Hardware Audit
```bash
# Run on each server to document resources
ssh wizardsofts@10.0.0.80 "lscpu | grep 'CPU(s):' && free -h"
ssh wizardsofts@10.0.0.81 "lscpu | grep 'CPU(s):' && free -h"
ssh wizardsofts@10.0.0.82 "lscpu | grep 'CPU(s):' && free -h"
ssh wizardsofts@10.0.0.84 "lscpu | grep 'CPU(s):' && free -h"

# Check for GPUs
ssh wizardsofts@10.0.0.80 "nvidia-smi 2>/dev/null || echo 'No GPU'"
ssh wizardsofts@10.0.0.84 "nvidia-smi 2>/dev/null || echo 'No GPU'"
```

**Document findings:**
- [ ] CPU cores per server
- [ ] RAM per server
- [ ] GPU availability (NVIDIA, AMD, or none)
- [ ] Available disk space for datasets

#### Network Configuration
```bash
# Test connectivity between nodes
ssh wizardsofts@10.0.0.84 "ping -c 3 10.0.0.80"
ssh wizardsofts@10.0.0.84 "ping -c 3 10.0.0.81"
ssh wizardsofts@10.0.0.84 "ping -c 3 10.0.0.82"

# Test Docker networking
ssh wizardsofts@10.0.0.84 "docker network ls"
```

### 1.2 Create Project Structure

```bash
# Create feature branch using worktree
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git checkout master
git pull gitlab master

# Create worktree for distributed ML setup
mkdir -p ../wizardsofts-megabuild-worktrees
git worktree add ../wizardsofts-megabuild-worktrees/feature-distributed-ml -b feature/distributed-ml-infrastructure

cd ../wizardsofts-megabuild-worktrees/feature-distributed-ml

# Create infrastructure directory
mkdir -p infrastructure/distributed-ml/{ray,celery,monitoring,scripts,examples}
```

**Directory Structure:**
```
infrastructure/distributed-ml/
├── ray/
│   ├── docker-compose.ray-head.yml      # Head node (Server 84)
│   ├── docker-compose.ray-worker.yml    # Worker nodes
│   ├── Dockerfile.ray-worker            # Custom Ray worker image
│   ├── ray-config.yaml                  # Ray cluster config
│   └── .env.ray                         # Ray environment variables
├── celery/
│   ├── docker-compose.celery.yml        # Celery + Redis (Phase 2)
│   ├── tasks/                           # Celery task definitions
│   └── .env.celery                      # Celery environment variables
├── monitoring/
│   ├── prometheus-rules-ray.yml         # Ray alerting rules
│   ├── grafana-dashboard-ray.json       # Ray dashboard
│   └── prometheus-exporter-ray.yml      # Ray metrics exporter
├── scripts/
│   ├── setup-ray-head.sh                # Deploy head node
│   ├── setup-ray-worker.sh              # Deploy worker node
│   ├── test-ray-cluster.py              # Cluster validation
│   └── benchmark-cluster.py             # Performance testing
├── examples/
│   ├── 01-hello-ray.py                  # Basic Ray example
│   ├── 02-distributed-training.py       # ML training example
│   ├── 03-data-processing.py            # Data processing example
│   └── 04-hyperparameter-tuning.py      # Ray Tune example
└── README.md                            # Setup instructions
```

### 1.3 Install Ray on Server 84 (Head Node)

#### Step 1: Create Dockerfile
```dockerfile
# infrastructure/distributed-ml/ray/Dockerfile.ray-head
FROM rayproject/ray:2.40.0-py310

# Install additional ML libraries
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.3 \
    scikit-learn==1.4.0 \
    xgboost==2.0.3 \
    torch==2.1.2 \
    ray[tune,serve,data]==2.40.0 \
    prometheus-client==0.19.0

# Install monitoring tools
RUN pip install --no-cache-dir \
    ray[default,observability]==2.40.0

# Create app directory
WORKDIR /app

# Copy example scripts
COPY examples/ /app/examples/

# Expose ports
EXPOSE 6379 8265 10001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import ray; ray.init(address='auto', ignore_reinit_error=True); print('healthy')"

# Start Ray head node
CMD ["ray", "start", "--head", \
     "--port=6379", \
     "--dashboard-host=0.0.0.0", \
     "--dashboard-port=8265", \
     "--metrics-export-port=8080", \
     "--block"]
```

#### Step 2: Create Docker Compose Configuration
```yaml
# infrastructure/distributed-ml/ray/docker-compose.ray-head.yml
version: '3.8'

services:
  ray-head:
    build:
      context: .
      dockerfile: Dockerfile.ray-head
    container_name: ray-head
    hostname: ray-head
    ports:
      - "6379:6379"    # Ray GCS (Global Control Service)
      - "8265:8265"    # Ray Dashboard
      - "10001:10001"  # Ray Client
      - "8080:8080"    # Prometheus Metrics
    volumes:
      # Shared storage for datasets and models
      - ray-storage:/tmp/ray
      - ./examples:/app/examples:ro
      - /opt/ml-datasets:/datasets:ro  # Mount shared datasets
      - /opt/ml-models:/models         # Mount model output directory
    environment:
      - RAY_GRAFANA_HOST=http://10.0.0.84:3002
      - RAY_PROMETHEUS_HOST=http://10.0.0.84:9090
      - RAY_GRAFANA_IFRAME_HOST=http://10.0.0.84:3002
      - RAY_memory_monitor_refresh_ms=1000
      - RAY_object_spilling_config='{"type":"filesystem","params":{"directory_path":"/tmp/ray/spill"}}'
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - ray-network
    labels:
      - "com.wizardsofts.service=ray-head"
      - "com.wizardsofts.environment=production"

volumes:
  ray-storage:
    driver: local

networks:
  ray-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

#### Step 3: Create Environment Variables
```bash
# infrastructure/distributed-ml/ray/.env.ray
RAY_ADDRESS=10.0.0.84:6379
RAY_DASHBOARD_HOST=10.0.0.84
RAY_DASHBOARD_PORT=8265
RAY_REDIS_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD
RAY_object_store_memory=2000000000  # 2GB object store
RAY_NUM_CPUS=4
RAY_NUM_GPUS=0  # Update if you have GPUs
```

#### Step 4: Deploy Head Node
```bash
# infrastructure/distributed-ml/scripts/setup-ray-head.sh
#!/bin/bash
set -euo pipefail

echo "🚀 Deploying Ray Head Node on Server 84..."

# Navigate to Ray directory
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Create required directories
sudo mkdir -p /opt/ml-datasets /opt/ml-models
sudo chown -R $USER:$USER /opt/ml-datasets /opt/ml-models

# Generate secure Redis password if not exists
if ! grep -q "RAY_REDIS_PASSWORD" .env.ray || grep -q "CHANGE_THIS" .env.ray; then
    REDIS_PASS=$(openssl rand -hex 32)
    sed -i "s/CHANGE_THIS_TO_SECURE_PASSWORD/$REDIS_PASS/" .env.ray
    echo "✅ Generated secure Redis password"
fi

# Pull latest images
docker-compose -f docker-compose.ray-head.yml pull

# Start Ray head node
docker-compose -f docker-compose.ray-head.yml up -d

# Wait for Ray to be ready
echo "⏳ Waiting for Ray head node to start..."
sleep 30

# Verify Ray is running
docker exec ray-head ray status || {
    echo "❌ Ray head node failed to start"
    docker logs ray-head --tail 50
    exit 1
}

echo "✅ Ray head node deployed successfully!"
echo "📊 Dashboard: http://10.0.0.84:8265"
echo "🔗 Connect with: ray.init(address='ray://10.0.0.84:10001')"
```

**Make script executable:**
```bash
chmod +x infrastructure/distributed-ml/scripts/setup-ray-head.sh
```

### 1.4 Install Ray on Server 80 (First Worker)

#### Step 1: Create Worker Dockerfile
```dockerfile
# infrastructure/distributed-ml/ray/Dockerfile.ray-worker
FROM rayproject/ray:2.40.0-py310

# Install same ML libraries as head node
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.3 \
    scikit-learn==1.4.0 \
    xgboost==2.0.3 \
    torch==2.1.2 \
    ray[tune,serve,data]==2.40.0

WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import ray; print('healthy')"

# Start Ray worker
CMD ["ray", "start", \
     "--address=${RAY_HEAD_ADDRESS}", \
     "--num-cpus=${RAY_NUM_CPUS:-4}", \
     "--num-gpus=${RAY_NUM_GPUS:-0}", \
     "--object-store-memory=${RAY_OBJECT_STORE_MEMORY:-2000000000}", \
     "--block"]
```

#### Step 2: Create Worker Docker Compose
```yaml
# infrastructure/distributed-ml/ray/docker-compose.ray-worker.yml
version: '3.8'

services:
  ray-worker:
    build:
      context: .
      dockerfile: Dockerfile.ray-worker
    container_name: ray-worker-${WORKER_ID:-1}
    hostname: ray-worker-${WORKER_ID:-1}
    volumes:
      - /opt/ml-datasets:/datasets:ro
      - /opt/ml-models:/models
      - ray-worker-storage:/tmp/ray
    environment:
      - RAY_HEAD_ADDRESS=${RAY_HEAD_ADDRESS:-10.0.0.84:6379}
      - RAY_NUM_CPUS=${RAY_NUM_CPUS:-4}
      - RAY_NUM_GPUS=${RAY_NUM_GPUS:-0}
      - RAY_OBJECT_STORE_MEMORY=${RAY_OBJECT_STORE_MEMORY:-2000000000}
    deploy:
      resources:
        limits:
          cpus: '${RAY_NUM_CPUS:-4}'
          memory: ${RAY_MEMORY_LIMIT:-8G}
        reservations:
          cpus: '2'
          memory: 2G
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    network_mode: host  # Use host network for better Ray performance
    labels:
      - "com.wizardsofts.service=ray-worker"
      - "com.wizardsofts.worker-id=${WORKER_ID:-1}"

volumes:
  ray-worker-storage:
    driver: local
```

#### Step 3: Create Worker Deployment Script
```bash
# infrastructure/distributed-ml/scripts/setup-ray-worker.sh
#!/bin/bash
set -euo pipefail

# Usage: ./setup-ray-worker.sh <server-ip> <worker-id> <num-cpus> <memory-gb>
# Example: ./setup-ray-worker.sh 10.0.0.80 1 4 8

SERVER_IP=${1:-"10.0.0.80"}
WORKER_ID=${2:-"1"}
NUM_CPUS=${3:-"4"}
MEMORY_GB=${4:-"8"}

echo "🚀 Deploying Ray Worker on $SERVER_IP (ID: $WORKER_ID)..."

# Copy files to remote server
echo "📦 Copying deployment files..."
scp -r infrastructure/distributed-ml/ray wizardsofts@$SERVER_IP:/tmp/

# Execute deployment on remote server
ssh wizardsofts@$SERVER_IP << EOF
set -e

# Create required directories
sudo mkdir -p /opt/ml-datasets /opt/ml-models /opt/wizardsofts-megabuild/infrastructure/distributed-ml
sudo chown -R \$USER:\$USER /opt/ml-datasets /opt/ml-models /opt/wizardsofts-megabuild

# Move files to proper location
sudo mv /tmp/ray /opt/wizardsofts-megabuild/infrastructure/distributed-ml/
cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray

# Create .env file for this worker
cat > .env.ray-worker << EOL
RAY_HEAD_ADDRESS=10.0.0.84:6379
WORKER_ID=$WORKER_ID
RAY_NUM_CPUS=$NUM_CPUS
RAY_NUM_GPUS=0
RAY_OBJECT_STORE_MEMORY=2000000000
RAY_MEMORY_LIMIT=${MEMORY_GB}G
EOL

# Build and start worker
docker-compose -f docker-compose.ray-worker.yml --env-file .env.ray-worker up -d --build

echo "✅ Ray worker deployed on $SERVER_IP"
EOF

# Verify worker connected
echo "⏳ Verifying worker connection..."
sleep 10

ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status" | grep "worker" && \
    echo "✅ Worker $WORKER_ID connected successfully!" || \
    echo "⚠️  Worker may still be connecting, check: docker logs ray-worker-$WORKER_ID"
```

**Make script executable:**
```bash
chmod +x infrastructure/distributed-ml/scripts/setup-ray-worker.sh
```

### 1.5 Configure Firewall Rules

```bash
# infrastructure/distributed-ml/scripts/configure-firewall.sh
#!/bin/bash
set -euo pipefail

echo "🔒 Configuring firewall rules for Ray cluster..."

# Configure Server 84 (Head Node)
ssh wizardsofts@10.0.0.84 << 'EOF'
# Allow Ray GCS
sudo ufw allow from 10.0.0.0/24 to any port 6379 comment 'Ray GCS'

# Allow Ray Dashboard
sudo ufw allow from 10.0.0.0/24 to any port 8265 comment 'Ray Dashboard'

# Allow Ray Client
sudo ufw allow from 10.0.0.0/24 to any port 10001 comment 'Ray Client'

# Allow Ray Metrics
sudo ufw allow from 10.0.0.0/24 to any port 8080 comment 'Ray Metrics'

# Allow Ray worker ports (dynamic range)
sudo ufw allow from 10.0.0.0/24 to any port 10002:10999 comment 'Ray Workers'

sudo ufw reload
echo "✅ Server 84 firewall configured"
EOF

# Configure Worker Nodes (Server 80, 82)
for SERVER in 80 82; do
    ssh wizardsofts@10.0.0.$SERVER << 'EOF'
    # Allow outbound connections to Ray head
    # (UFW allows outbound by default, but document for reference)

    # Allow Ray worker ports
    sudo ufw allow from 10.0.0.0/24 to any port 10002:10999 comment 'Ray Workers'

    sudo ufw reload
    echo "✅ Server firewall configured"
EOF
done

echo "✅ All firewall rules configured"
```

### 1.6 Create Test Scripts

#### Basic Ray Test
```python
# infrastructure/distributed-ml/examples/01-hello-ray.py
"""
Basic Ray cluster test
Tests: Cluster connectivity, worker availability, basic task execution
"""
import ray
import time
import psutil

@ray.remote
def cpu_intensive_task(iterations: int):
    """Simulate CPU-intensive task"""
    result = 0
    for i in range(iterations):
        result += i ** 2
    return {
        "result": result,
        "node": ray.get_runtime_context().get_node_id(),
        "worker_id": ray.get_runtime_context().get_worker_id()
    }

def main():
    # Connect to Ray cluster
    print("🔗 Connecting to Ray cluster...")
    ray.init(address="ray://10.0.0.84:10001")

    print("\n📊 Cluster Information:")
    print(f"   Nodes: {len(ray.nodes())}")
    print(f"   Available CPUs: {ray.available_resources().get('CPU', 0)}")
    print(f"   Available Memory: {ray.available_resources().get('memory', 0) / 1e9:.2f} GB")

    print("\n🚀 Running distributed tasks...")

    # Submit 20 tasks across cluster
    futures = [cpu_intensive_task.remote(1_000_000) for _ in range(20)]

    start_time = time.time()
    results = ray.get(futures)
    elapsed = time.time() - start_time

    print(f"\n✅ Completed {len(results)} tasks in {elapsed:.2f}s")

    # Show task distribution
    node_distribution = {}
    for result in results:
        node = result['node']
        node_distribution[node] = node_distribution.get(node, 0) + 1

    print("\n📈 Task Distribution:")
    for node, count in node_distribution.items():
        print(f"   Node {node[:8]}: {count} tasks")

    ray.shutdown()

if __name__ == "__main__":
    main()
```

#### ML Training Test
```python
# infrastructure/distributed-ml/examples/02-distributed-training.py
"""
Distributed ML training test using Ray Train
Tests: Multi-node training, data distribution, model checkpointing
"""
import ray
from ray import train
from ray.train import ScalingConfig
from ray.train.sklearn import SklearnTrainer
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import numpy as np

def train_func(config):
    """Training function executed on each worker"""
    # Generate synthetic dataset
    X, y = make_classification(
        n_samples=10000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        random_state=42
    )

    # Train model
    model = RandomForestClassifier(
        n_estimators=config.get("n_estimators", 100),
        max_depth=config.get("max_depth", 10),
        random_state=42,
        n_jobs=-1  # Use all CPUs on worker
    )

    model.fit(X, y)
    accuracy = model.score(X, y)

    # Report metrics
    train.report({"accuracy": accuracy})

    return model

def main():
    print("🔗 Connecting to Ray cluster...")
    ray.init(address="ray://10.0.0.84:10001")

    print("\n🚀 Starting distributed training...")

    # Configure distributed training
    trainer = SklearnTrainer(
        train_loop_per_worker=train_func,
        train_loop_config={
            "n_estimators": 200,
            "max_depth": 15
        },
        scaling_config=ScalingConfig(
            num_workers=4,  # Distribute across 4 workers
            use_gpu=False
        )
    )

    # Run training
    result = trainer.fit()

    print("\n✅ Training complete!")
    print(f"   Best accuracy: {result.metrics['accuracy']:.4f}")
    print(f"   Checkpoint: {result.checkpoint}")

    ray.shutdown()

if __name__ == "__main__":
    main()
```

#### Data Processing Test
```python
# infrastructure/distributed-ml/examples/03-data-processing.py
"""
Distributed data processing test using Ray Data
Tests: Large dataset processing, parallel transformations, data persistence
"""
import ray
import numpy as np
import time

def process_batch(batch):
    """Simulate heavy data processing"""
    # Add computed features
    batch["feature_sum"] = batch["feature_1"] + batch["feature_2"]
    batch["feature_product"] = batch["feature_1"] * batch["feature_2"]
    batch["feature_normalized"] = (batch["feature_1"] - batch["feature_1"].mean()) / batch["feature_1"].std()
    return batch

def main():
    print("🔗 Connecting to Ray cluster...")
    ray.init(address="ray://10.0.0.84:10001")

    print("\n📊 Creating large synthetic dataset...")

    # Create dataset (10M rows)
    dataset = ray.data.range(10_000_000).map_batches(
        lambda batch: {
            "id": batch["id"],
            "feature_1": np.random.randn(len(batch["id"])),
            "feature_2": np.random.randn(len(batch["id"])),
            "label": np.random.randint(0, 2, len(batch["id"]))
        },
        batch_format="pandas"
    )

    print(f"   Dataset size: {dataset.count()} rows")

    print("\n🚀 Processing data across cluster...")
    start_time = time.time()

    # Process in parallel across all workers
    processed = dataset.map_batches(
        process_batch,
        batch_format="pandas",
        batch_size=10000
    )

    # Trigger execution and count
    row_count = processed.count()
    elapsed = time.time() - start_time

    print(f"\n✅ Processed {row_count:,} rows in {elapsed:.2f}s")
    print(f"   Throughput: {row_count / elapsed:,.0f} rows/sec")

    # Show sample
    print("\n📝 Sample output:")
    print(processed.take(5))

    # Save to storage (optional)
    # processed.write_parquet("/opt/ml-datasets/processed/")

    ray.shutdown()

if __name__ == "__main__":
    main()
```

### 1.7 Deployment Steps

#### Step 1: Deploy Head Node
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-distributed-ml

# Make scripts executable
chmod +x infrastructure/distributed-ml/scripts/*.sh

# Configure firewall first
./infrastructure/distributed-ml/scripts/configure-firewall.sh

# Deploy head node on Server 84
scp -r infrastructure/distributed-ml wizardsofts@10.0.0.84:/opt/wizardsofts-megabuild/infrastructure/
ssh wizardsofts@10.0.0.84 "cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/scripts && ./setup-ray-head.sh"
```

#### Step 2: Verify Head Node
```bash
# SSH into Server 84 and check
ssh wizardsofts@10.0.0.84

# Check Ray status
docker exec ray-head ray status

# Expected output:
# ======== Autoscaler status: 2024-01-02 12:00:00.000000 ========
# Node status
# ---------------------------------------------------------------
# Healthy:
#  1 ray.head.default
# Pending:
#  (no pending nodes)
# Recent failures:
#  (no failures)

# Check dashboard
curl http://localhost:8265

# View logs
docker logs ray-head --tail 50
```

#### Step 3: Deploy First Worker (Server 80)
```bash
# From your laptop
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-distributed-ml

# Deploy worker to Server 80
./infrastructure/distributed-ml/scripts/setup-ray-worker.sh 10.0.0.80 1 4 8
```

#### Step 4: Verify Cluster
```bash
# Check cluster status from head node
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Should show:
# Node status
# ---------------------------------------------------------------
# Healthy:
#  1 ray.head.default
#  1 ray-worker-1

# View Ray Dashboard
# Open browser: http://10.0.0.84:8265
```

#### Step 5: Run Tests
```bash
# Copy test scripts to Server 84
scp infrastructure/distributed-ml/examples/*.py wizardsofts@10.0.0.84:/tmp/

# Run basic test
ssh wizardsofts@10.0.0.84 "cd /tmp && python 01-hello-ray.py"

# Run ML training test
ssh wizardsofts@10.0.0.84 "cd /tmp && python 02-distributed-training.py"

# Run data processing test
ssh wizardsofts@10.0.0.84 "cd /tmp && python 03-data-processing.py"
```

### 1.8 Monitoring Integration

#### Add Ray Metrics to Prometheus
```yaml
# infrastructure/distributed-ml/monitoring/prometheus-config-ray.yml
# Add to /opt/wizardsofts-megabuild/prometheus/prometheus.yml on Server 84

scrape_configs:
  - job_name: 'ray-cluster'
    static_configs:
      - targets: ['10.0.0.84:8080']  # Ray head node metrics
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/metrics'
```

#### Create Ray Alert Rules
```yaml
# infrastructure/distributed-ml/monitoring/prometheus-rules-ray.yml
groups:
  - name: ray_cluster
    interval: 30s
    rules:
      - alert: RayHeadNodeDown
        expr: up{job="ray-cluster"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Ray head node is down"
          description: "Ray head node on Server 84 has been down for 5 minutes"

      - alert: RayWorkerDown
        expr: ray_cluster_active_nodes < 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Ray worker node missing"
          description: "Expected at least 2 nodes, only {{ $value }} active"

      - alert: RayHighMemoryUsage
        expr: ray_object_store_memory_usage / ray_object_store_memory_total > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Ray object store memory high"
          description: "Object store memory usage is {{ $value | humanizePercentage }}"

      - alert: RayTaskFailures
        expr: rate(ray_tasks_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Ray task failure rate"
          description: "Task failure rate: {{ $value | humanize }} failures/sec"
```

#### Deploy Monitoring
```bash
# Copy monitoring configs
scp infrastructure/distributed-ml/monitoring/prometheus-rules-ray.yml \
    wizardsofts@10.0.0.84:/opt/prometheus/rules/

# Update Prometheus configuration
ssh wizardsofts@10.0.0.84 << 'EOF'
# Append Ray scrape config to prometheus.yml
cat >> /opt/prometheus/prometheus.yml << EOL

  - job_name: 'ray-cluster'
    static_configs:
      - targets: ['10.0.0.84:8080']
    scrape_interval: 15s
EOL

# Add rule file reference
sed -i '/rule_files:/a \  - "rules/prometheus-rules-ray.yml"' /opt/prometheus/prometheus.yml

# Reload Prometheus
docker exec prometheus kill -HUP 1
EOF
```

### 1.9 Phase 1 Success Criteria

**✅ Phase 1 Complete When:**
- [ ] Ray head node running on Server 84
- [ ] Ray worker running on Server 80
- [ ] Cluster shows 2 healthy nodes in `ray status`
- [ ] Ray Dashboard accessible at http://10.0.0.84:8265
- [ ] All 3 test scripts execute successfully:
  - [ ] 01-hello-ray.py shows task distribution across nodes
  - [ ] 02-distributed-training.py completes training with >90% accuracy
  - [ ] 03-data-processing.py processes 10M rows in <60 seconds
- [ ] Prometheus scraping Ray metrics
- [ ] Grafana dashboard shows Ray cluster status

**Deliverables:**
- [ ] Git commit with all Phase 1 infrastructure code
- [ ] Documentation: `infrastructure/distributed-ml/README.md`
- [ ] Test results document
- [ ] Performance baseline (tasks/sec, throughput)

**Estimated Time:** 5-7 days

---

## Phase 2: Celery Integration (Weeks 3-4)

**Goal:** Add Celery for background task scheduling and orchestration of Ray jobs

### 2.1 Why Celery + Ray?

**Ray alone is not sufficient because:**
- ❌ Ray has no built-in scheduler for recurring jobs
- ❌ Ray workers are designed to be always-on (not ideal for laptops)
- ❌ No native support for task prioritization or queuing
- ❌ Limited support for long-running background tasks

**Celery complements Ray by providing:**
- ✅ Cron-like scheduling (Celery Beat)
- ✅ Task queuing and prioritization
- ✅ Retry logic and failure handling
- ✅ Lightweight workers (perfect for laptops)
- ✅ Integration with existing web frameworks

### 2.2 Architecture

```
User Request/Cron → Celery Beat → Celery Worker
                                        ↓
                                  Check if ML job
                                        ↓
                             Yes ← → No (simple task)
                              ↓            ↓
                        Ray Submit    Execute locally
                              ↓            ↓
                        Ray Cluster   Return result
                              ↓
                        Return result
```

### 2.3 Install Celery

#### Step 1: Create Celery Dockerfile
```dockerfile
# infrastructure/distributed-ml/celery/Dockerfile.celery
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    celery[redis]==5.3.6 \
    redis==5.0.1 \
    flower==2.0.1 \
    ray==2.40.0 \
    pandas==2.1.4 \
    prometheus-client==0.19.0

# Create app directory
WORKDIR /app

# Copy Celery tasks
COPY tasks/ /app/tasks/

# Create celery user
RUN useradd -m -u 1000 celery && \
    chown -R celery:celery /app

USER celery

# Default command (override in docker-compose)
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
```

#### Step 2: Create Celery Task Definitions
```python
# infrastructure/distributed-ml/celery/tasks/__init__.py
from celery import Celery
import os

# Initialize Celery app
app = Celery('ml_tasks')

# Load configuration
app.config_from_object('tasks.celeryconfig')

# Auto-discover tasks
app.autodiscover_tasks(['tasks'])
```

```python
# infrastructure/distributed-ml/celery/tasks/celeryconfig.py
import os

# Redis broker
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://:password@10.0.0.84:6380/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://:password@10.0.0.84:6380/1')

# Serialization
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task routing
task_routes = {
    'tasks.ml_tasks.*': {'queue': 'ml'},
    'tasks.data_tasks.*': {'queue': 'data'},
    'tasks.simple_tasks.*': {'queue': 'default'}
}

# Task time limits
task_soft_time_limit = 3600  # 1 hour
task_time_limit = 7200  # 2 hours

# Result expiration
result_expires = 86400  # 24 hours

# Beat schedule (recurring tasks)
beat_schedule = {
    'daily-model-retraining': {
        'task': 'tasks.ml_tasks.retrain_models',
        'schedule': 3600 * 24,  # Daily at midnight
        'args': ()
    },
    'hourly-data-processing': {
        'task': 'tasks.data_tasks.process_new_data',
        'schedule': 3600,  # Every hour
        'args': ()
    }
}
```

```python
# infrastructure/distributed-ml/celery/tasks/ml_tasks.py
from tasks import app
import ray
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3)
def distributed_training(self, model_config: dict, dataset_path: str):
    """
    Distributed ML training using Ray
    This task runs on Celery worker but submits work to Ray cluster
    """
    try:
        logger.info(f"Starting distributed training: {model_config}")

        # Connect to Ray cluster
        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        # Define Ray remote function
        @ray.remote
        def train_model_partition(config, data_path):
            # Import heavy ML libraries inside Ray task
            from sklearn.ensemble import RandomForestClassifier
            import pandas as pd

            # Load data
            df = pd.read_csv(data_path)
            X = df.drop('target', axis=1)
            y = df['target']

            # Train model
            model = RandomForestClassifier(**config)
            model.fit(X, y)

            return {
                'accuracy': model.score(X, y),
                'feature_importance': model.feature_importances_.tolist()
            }

        # Submit to Ray cluster
        future = train_model_partition.remote(model_config, dataset_path)
        result = ray.get(future)

        ray.shutdown()

        logger.info(f"Training complete. Accuracy: {result['accuracy']}")
        return result

    except Exception as exc:
        logger.error(f"Training failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task
def retrain_models():
    """
    Scheduled task: Retrain all models daily
    """
    logger.info("Starting daily model retraining...")

    models = [
        {'model': 'stock_predictor', 'dataset': '/datasets/stocks_daily.csv'},
        {'model': 'news_classifier', 'dataset': '/datasets/news_daily.csv'}
    ]

    for model in models:
        distributed_training.delay(
            model_config={'n_estimators': 200, 'max_depth': 15},
            dataset_path=model['dataset']
        )

    return f"Queued {len(models)} training jobs"
```

```python
# infrastructure/distributed-ml/celery/tasks/data_tasks.py
from tasks import app
import ray
import logging

logger = logging.getLogger(__name__)

@app.task
def process_large_dataset(input_path: str, output_path: str):
    """
    Process large dataset using Ray Data
    """
    try:
        logger.info(f"Processing dataset: {input_path}")

        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        # Use Ray Data for parallel processing
        dataset = ray.data.read_csv(input_path)

        # Apply transformations
        processed = dataset.map_batches(
            lambda batch: {
                **batch,
                'processed_at': pd.Timestamp.now()
            },
            batch_format="pandas"
        )

        # Save results
        processed.write_parquet(output_path)

        row_count = processed.count()
        ray.shutdown()

        logger.info(f"Processed {row_count} rows")
        return {'status': 'success', 'rows': row_count}

    except Exception as exc:
        logger.error(f"Processing failed: {exc}")
        raise

@app.task
def process_new_data():
    """
    Scheduled task: Process new data every hour
    """
    logger.info("Starting hourly data processing...")

    # Check for new files and process
    import glob
    new_files = glob.glob('/datasets/incoming/*.csv')

    for file in new_files:
        output = file.replace('/incoming/', '/processed/')
        process_large_dataset.delay(file, output)

    return f"Queued {len(new_files)} processing jobs"
```

```python
# infrastructure/distributed-ml/celery/tasks/simple_tasks.py
from tasks import app
import logging

logger = logging.getLogger(__name__)

@app.task
def send_notification(message: str):
    """
    Simple task: Send notification (no Ray needed)
    """
    logger.info(f"Notification: {message}")
    # Send email, Slack message, etc.
    return {'status': 'sent', 'message': message}

@app.task
def generate_report(report_type: str):
    """
    Simple task: Generate report
    """
    logger.info(f"Generating {report_type} report...")
    # Generate report logic
    return {'status': 'complete', 'report_type': report_type}
```

#### Step 3: Create Docker Compose Configuration
```yaml
# infrastructure/distributed-ml/celery/docker-compose.celery.yml
version: '3.8'

services:
  # Redis broker (separate from Ray Redis)
  celery-redis:
    image: redis:7-alpine
    container_name: celery-redis
    command: redis-server --requirepass ${REDIS_PASSWORD} --port 6380
    ports:
      - "6380:6380"  # Different port from Ray
    volumes:
      - celery-redis-data:/data
    deploy:
      resources:
        limits:
          memory: 512M
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - celery-network
    healthcheck:
      test: ["CMD", "redis-cli", "-p", "6380", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Celery Beat (scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: celery-beat
    command: celery -A tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@celery-redis:6380/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@celery-redis:6380/1
    depends_on:
      celery-redis:
        condition: service_healthy
    volumes:
      - ./tasks:/app/tasks:ro
      - celery-beat-schedule:/app
    restart: unless-stopped
    networks:
      - celery-network
      - ray-network  # Connect to Ray network

  # Celery Worker (default queue)
  celery-worker-default:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: celery-worker-default
    command: celery -A tasks worker -Q default --loglevel=info --concurrency=2
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@celery-redis:6380/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@celery-redis:6380/1
    depends_on:
      celery-redis:
        condition: service_healthy
    volumes:
      - ./tasks:/app/tasks:ro
      - /opt/ml-datasets:/datasets
      - /opt/ml-models:/models
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
    restart: unless-stopped
    networks:
      - celery-network
      - ray-network

  # Celery Worker (ML queue - connects to Ray)
  celery-worker-ml:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: celery-worker-ml
    command: celery -A tasks worker -Q ml --loglevel=info --concurrency=1
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@celery-redis:6380/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@celery-redis:6380/1
    depends_on:
      celery-redis:
        condition: service_healthy
    volumes:
      - ./tasks:/app/tasks:ro
      - /opt/ml-datasets:/datasets
      - /opt/ml-models:/models
    deploy:
      resources:
        limits:
          memory: 2G
    restart: unless-stopped
    networks:
      - celery-network
      - ray-network

  # Flower (Celery monitoring)
  flower:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: celery-flower
    command: celery -A tasks flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@celery-redis:6380/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@celery-redis:6380/1
      - FLOWER_BASIC_AUTH=${FLOWER_USER}:${FLOWER_PASSWORD}
    depends_on:
      celery-redis:
        condition: service_healthy
    volumes:
      - ./tasks:/app/tasks:ro
    restart: unless-stopped
    networks:
      - celery-network

volumes:
  celery-redis-data:
  celery-beat-schedule:

networks:
  celery-network:
    driver: bridge
  ray-network:
    external: true
    name: distributed-ml_ray-network
```

#### Step 4: Create Environment File
```bash
# infrastructure/distributed-ml/celery/.env.celery
REDIS_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
CELERY_BROKER_URL=redis://:CHANGE_THIS_SECURE_PASSWORD@celery-redis:6380/0
CELERY_RESULT_BACKEND=redis://:CHANGE_THIS_SECURE_PASSWORD@celery-redis:6380/1
FLOWER_USER=admin
FLOWER_PASSWORD=CHANGE_THIS_FLOWER_PASSWORD
```

#### Step 5: Deploy Celery
```bash
# infrastructure/distributed-ml/scripts/setup-celery.sh
#!/bin/bash
set -euo pipefail

echo "🚀 Deploying Celery on Server 84..."

cd /opt/wizardsofts-megabuild/infrastructure/distributed-ml/celery

# Generate secure passwords if not exists
if ! grep -q "REDIS_PASSWORD" .env.celery || grep -q "CHANGE_THIS" .env.celery; then
    REDIS_PASS=$(openssl rand -hex 32)
    FLOWER_PASS=$(openssl rand -hex 16)

    sed -i "s/CHANGE_THIS_SECURE_PASSWORD/$REDIS_PASS/g" .env.celery
    sed -i "s/CHANGE_THIS_FLOWER_PASSWORD/$FLOWER_PASS/g" .env.celery

    echo "✅ Generated secure passwords"
    echo "📝 Flower password: $FLOWER_PASS (save this!)"
fi

# Build and start services
docker-compose -f docker-compose.celery.yml --env-file .env.celery up -d --build

echo "⏳ Waiting for services to start..."
sleep 15

# Verify services
docker-compose -f docker-compose.celery.yml ps

echo "✅ Celery deployed successfully!"
echo "📊 Flower Dashboard: http://10.0.0.84:5555 (admin / [password in .env.celery])"
echo "🔗 Broker: redis://10.0.0.84:6380"
```

### 2.4 Test Celery + Ray Integration

```python
# infrastructure/distributed-ml/examples/04-celery-ray-integration.py
"""
Test Celery + Ray integration
Demonstrates: Task queuing, scheduled jobs, Ray cluster utilization
"""
from celery import Celery
import time

# Connect to Celery
app = Celery('test', broker='redis://:password@10.0.0.84:6380/0')

# Import tasks
from tasks.ml_tasks import distributed_training
from tasks.data_tasks import process_large_dataset
from tasks.simple_tasks import send_notification

def main():
    print("🔗 Testing Celery + Ray integration...")

    # Test 1: Simple task (no Ray)
    print("\n1️⃣ Testing simple task...")
    result = send_notification.delay("Test notification from Celery")
    print(f"   Task ID: {result.id}")
    print(f"   Result: {result.get(timeout=10)}")

    # Test 2: ML task (uses Ray)
    print("\n2️⃣ Testing ML training task...")
    result = distributed_training.delay(
        model_config={'n_estimators': 100, 'max_depth': 10},
        dataset_path='/datasets/test_data.csv'
    )
    print(f"   Task ID: {result.id}")
    print(f"   Status: {result.status}")
    print("   Waiting for result (this may take a while)...")
    print(f"   Result: {result.get(timeout=300)}")

    # Test 3: Data processing (uses Ray Data)
    print("\n3️⃣ Testing data processing task...")
    result = process_large_dataset.delay(
        input_path='/datasets/raw/data.csv',
        output_path='/datasets/processed/data.parquet'
    )
    print(f"   Task ID: {result.id}")
    print(f"   Result: {result.get(timeout=300)}")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()
```

### 2.5 Phase 2 Success Criteria

**✅ Phase 2 Complete When:**
- [ ] Celery + Redis running on Server 84
- [ ] Celery Beat scheduling tasks
- [ ] Flower dashboard accessible at http://10.0.0.84:5555
- [ ] Celery workers can submit jobs to Ray cluster
- [ ] Scheduled tasks executing on schedule
- [ ] All 4 test scripts execute successfully
- [ ] Task routing working (ml, data, default queues)

**Deliverables:**
- [ ] Git commit with Celery integration
- [ ] Updated documentation
- [ ] Example task definitions for common use cases

**Estimated Time:** 5-7 days

---

## Phase 3: Production Hardening (Week 5)

**Goal:** Secure, monitor, and harden the distributed infrastructure for production use

### 3.1 Security Hardening

#### Enable TLS for Ray
```bash
# Generate TLS certificates
ssh wizardsofts@10.0.0.84 << 'EOF'
mkdir -p /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs

# Generate CA
openssl genrsa -out /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/ca.key 4096
openssl req -new -x509 -days 3650 -key /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/ca.key \
    -out /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/ca.crt \
    -subj "/C=US/ST=State/L=City/O=WizardSofts/CN=Ray CA"

# Generate server certificate
openssl genrsa -out /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/server.key 4096
openssl req -new -key /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/server.key \
    -out /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/server.csr \
    -subj "/C=US/ST=State/L=City/O=WizardSofts/CN=10.0.0.84"

openssl x509 -req -days 3650 -in /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/server.csr \
    -CA /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/ca.crt \
    -CAkey /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/ca.key \
    -set_serial 01 \
    -out /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/server.crt

# Set permissions
chmod 600 /opt/wizardsofts-megabuild/infrastructure/distributed-ml/certs/*.key
EOF
```

#### Update Ray Configuration for TLS
```yaml
# Update docker-compose.ray-head.yml
services:
  ray-head:
    # ... existing config ...
    volumes:
      - ./certs:/certs:ro
    command:
      - ray
      - start
      - --head
      - --port=6379
      - --ray-client-server-port=10001
      - --dashboard-host=0.0.0.0
      - --dashboard-port=8265
      - --redis-password=${RAY_REDIS_PASSWORD}
      - --block
```

#### Add Authentication to Dashboards
```yaml
# Add Traefik middleware for authentication
# infrastructure/distributed-ml/traefik/dynamic/ray-auth.yml
http:
  middlewares:
    ray-auth:
      basicAuth:
        users:
          - "admin:$apr1$..."  # Use htpasswd to generate

  routers:
    ray-dashboard:
      rule: "Host(`ray.wizardsofts.local`)"
      service: ray-dashboard
      middlewares:
        - ray-auth
      entryPoints:
        - web

  services:
    ray-dashboard:
      loadBalancer:
        servers:
          - url: "http://10.0.0.84:8265"
```

### 3.2 Resource Limits and Auto-scaling

#### Configure Ray Autoscaler
```yaml
# infrastructure/distributed-ml/ray/ray-autoscaler.yaml
cluster_name: wizardsofts-ml-cluster

max_workers: 10  # Max 10 worker nodes

provider:
    type: local
    head_node: 10.0.0.84
    worker_nodes:
        - 10.0.0.80
        - 10.0.0.81
        - 10.0.0.82

available_node_types:
    ray.head.default:
        resources: {"CPU": 4, "memory": 8000000000}
        node_config: {}

    ray.worker.high-memory:
        resources: {"CPU": 8, "memory": 16000000000}
        node_config: {}
        max_workers: 1  # Server 81 only

    ray.worker.standard:
        resources: {"CPU": 4, "memory": 8000000000}
        node_config: {}
        max_workers: 3  # Servers 80, 82, and one laptop

    ray.worker.laptop:
        resources: {"CPU": 2, "memory": 4000000000}
        node_config: {}
        max_workers: 6  # Additional laptops

head_node_type: ray.head.default

upscaling_speed: 1.0
idle_timeout_minutes: 10  # Remove idle workers after 10 minutes
```

### 3.3 Backup and Recovery

#### Backup Script
```bash
# infrastructure/distributed-ml/scripts/backup-cluster-state.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/backups/distributed-ml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📦 Backing up distributed ML cluster state..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Ray configuration
tar -czf $BACKUP_DIR/ray-config-$TIMESTAMP.tar.gz \
    /opt/wizardsofts-megabuild/infrastructure/distributed-ml/ray/

# Backup Celery configuration and task definitions
tar -czf $BACKUP_DIR/celery-config-$TIMESTAMP.tar.gz \
    /opt/wizardsofts-megabuild/infrastructure/distributed-ml/celery/

# Backup Redis data (Celery broker/results)
docker exec celery-redis redis-cli -p 6380 -a $REDIS_PASSWORD --rdb /data/dump.rdb
docker cp celery-redis:/data/dump.rdb $BACKUP_DIR/celery-redis-$TIMESTAMP.rdb

# Backup trained models
tar -czf $BACKUP_DIR/models-$TIMESTAMP.tar.gz /opt/ml-models/

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete

echo "✅ Backup complete: $BACKUP_DIR"
```

#### Add to Cron
```bash
# Run daily at 3 AM
0 3 * * * /opt/wizardsofts-megabuild/infrastructure/distributed-ml/scripts/backup-cluster-state.sh >> /var/log/ml-backup.log 2>&1
```

### 3.4 Advanced Monitoring

#### Create Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Distributed ML Cluster",
    "panels": [
      {
        "title": "Ray Cluster Status",
        "targets": [
          {
            "expr": "ray_cluster_active_nodes",
            "legendFormat": "Active Nodes"
          }
        ]
      },
      {
        "title": "Task Throughput",
        "targets": [
          {
            "expr": "rate(ray_tasks_total[5m])",
            "legendFormat": "Tasks/sec"
          }
        ]
      },
      {
        "title": "Celery Queue Length",
        "targets": [
          {
            "expr": "celery_queue_length",
            "legendFormat": "{{ queue }}"
          }
        ]
      }
    ]
  }
}
```

### 3.5 Phase 3 Success Criteria

**✅ Phase 3 Complete When:**
- [ ] TLS enabled for Ray cluster
- [ ] Dashboard authentication configured
- [ ] Resource limits enforced on all containers
- [ ] Automated backups running daily
- [ ] Grafana dashboard showing cluster metrics
- [ ] Alert rules configured and tested
- [ ] Disaster recovery procedure documented

**Estimated Time:** 5 days

---

## Phase 4: Laptop Integration (Week 6)

**Goal:** Add laptops as worker nodes with dynamic availability handling

### 4.1 Laptop-Specific Considerations

**Challenges:**
- Laptops may sleep/suspend
- Limited battery life
- Variable network connectivity
- Limited cooling (thermal throttling)

**Solutions:**
- Configure laptops to ignore lid close (already done for Server 82)
- Use Celery workers instead of Ray workers (more fault-tolerant)
- Set conservative resource limits
- Implement heartbeat monitoring

### 4.2 Laptop Worker Setup Script

```bash
# infrastructure/distributed-ml/scripts/setup-laptop-worker.sh
#!/bin/bash
set -euo pipefail

# Usage: ./setup-laptop-worker.sh <laptop-ip> <worker-id>
# Example: ./setup-laptop-worker.sh 10.0.0.85 laptop-1

LAPTOP_IP=${1}
WORKER_ID=${2}

echo "🚀 Setting up laptop worker: $WORKER_ID at $LAPTOP_IP"

# SSH to laptop and configure
ssh wizardsofts@$LAPTOP_IP << EOF
set -e

# Configure laptop to stay awake when lid is closed
sudo sed -i 's/#HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sudo systemctl restart systemd-logind

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker \$USER
fi

# Create deployment directory
mkdir -p /opt/distributed-ml

# Copy deployment files
EOF

# Copy worker configuration
scp -r infrastructure/distributed-ml/celery wizardsofts@$LAPTOP_IP:/opt/distributed-ml/

# Deploy Celery worker only (not Ray, too heavy for laptops)
ssh wizardsofts@$LAPTOP_IP << 'EOF'
cd /opt/distributed-ml/celery

# Create laptop-specific docker-compose
cat > docker-compose.laptop-worker.yml << 'EOL'
version: '3.8'

services:
  celery-worker-laptop:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: celery-worker-${WORKER_ID}
    hostname: ${WORKER_ID}
    command: celery -A tasks worker -Q default,data --loglevel=info --concurrency=1
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@10.0.0.84:6380/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@10.0.0.84:6380/1
      - WORKER_ID=${WORKER_ID}
    volumes:
      - ./tasks:/app/tasks:ro
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
    restart: unless-stopped
    network_mode: host
EOL

# Start worker
docker-compose -f docker-compose.laptop-worker.yml up -d

echo "✅ Laptop worker $WORKER_ID deployed"
EOF

echo "✅ Laptop worker setup complete"
```

### 4.3 Laptop Fleet Management

```python
# infrastructure/distributed-ml/scripts/manage-laptop-fleet.py
"""
Laptop fleet management script
- Monitor laptop availability
- Auto-register/deregister laptops
- Balance workload based on availability
"""
import redis
import time
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LaptopFleetManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.laptop_heartbeats = {}

    def register_laptop(self, laptop_id: str, ip: str):
        """Register a laptop worker"""
        self.redis.hset('laptops', laptop_id, ip)
        logger.info(f"Registered laptop: {laptop_id} at {ip}")

    def update_heartbeat(self, laptop_id: str):
        """Update laptop heartbeat timestamp"""
        self.laptop_heartbeats[laptop_id] = time.time()
        self.redis.hset('laptop_heartbeats', laptop_id, time.time())

    def check_availability(self) -> Dict[str, bool]:
        """Check which laptops are available"""
        available = {}
        current_time = time.time()

        for laptop_id, last_heartbeat in self.laptop_heartbeats.items():
            # Consider laptop unavailable if no heartbeat for 2 minutes
            available[laptop_id] = (current_time - last_heartbeat) < 120

        return available

    def get_available_workers(self) -> List[str]:
        """Get list of currently available laptop workers"""
        availability = self.check_availability()
        return [lid for lid, available in availability.items() if available]

    def monitor_loop(self):
        """Continuous monitoring loop"""
        while True:
            available = self.get_available_workers()
            logger.info(f"Available laptops: {len(available)}/{len(self.laptop_heartbeats)}")

            # Publish availability to Redis for Celery to use
            self.redis.set('available_laptop_count', len(available))

            time.sleep(30)

if __name__ == "__main__":
    manager = LaptopFleetManager("redis://:password@10.0.0.84:6380/2")
    manager.monitor_loop()
```

### 4.4 Phase 4 Success Criteria

**✅ Phase 4 Complete When:**
- [ ] At least 2 laptops added as workers
- [ ] Laptops survive sleep/wake cycles
- [ ] Fleet manager monitoring laptop availability
- [ ] Tasks routing to available laptops
- [ ] Dashboard showing laptop status

**Estimated Time:** 3-5 days

---

## Phase 5: Optimization & Scaling (Week 7-8)

**Goal:** Optimize performance and add advanced features

### 5.1 Performance Optimization

#### Task Prioritization
```python
# Add to celeryconfig.py
task_default_priority = 5
task_inherit_parent_priority = True

# High priority for critical tasks
@app.task(priority=9)
def critical_ml_task():
    pass

# Low priority for batch jobs
@app.task(priority=1)
def batch_processing():
    pass
```

#### Ray Object Store Optimization
```python
# Use Ray's object store for large data
@ray.remote
def process_large_data(data_ref):
    # data_ref is a reference, not the actual data
    # Data is automatically transferred only once
    data = ray.get(data_ref)
    # Process...
    return result

# Store large dataset once in object store
data_ref = ray.put(large_dataset)

# Submit many tasks with reference
futures = [process_large_data.remote(data_ref) for _ in range(100)]
```

#### Celery Result Backend Optimization
```python
# Use MongoDB or PostgreSQL for better performance
result_backend = 'mongodb://10.0.0.81:27017/celery_results'
# or
result_backend = 'postgresql://user:pass@10.0.0.81/celery_results'
```

### 5.2 Advanced Features

#### GPU Support
```yaml
# docker-compose.ray-worker-gpu.yml
services:
  ray-worker-gpu:
    image: rayproject/ray:2.40.0-py310-cu118  # CUDA 11.8
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    environment:
      - RAY_NUM_GPUS=1
```

#### Ray Serve for Model Deployment
```python
# Deploy trained model as HTTP endpoint
import ray
from ray import serve

@serve.deployment
class ModelServing:
    def __init__(self, model_path):
        import pickle
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    async def __call__(self, request):
        data = await request.json()
        prediction = self.model.predict([data['features']])
        return {"prediction": prediction.tolist()}

# Deploy
serve.run(ModelServing.bind("/models/latest_model.pkl"))
```

### 5.3 Phase 5 Success Criteria

**✅ Phase 5 Complete When:**
- [ ] GPU support enabled (if GPUs available)
- [ ] Task prioritization working
- [ ] Object store optimization reducing network traffic
- [ ] Model serving endpoint deployed
- [ ] Performance benchmarks documented

**Estimated Time:** 5-7 days

---

## Maintenance & Operations

### Daily Operations

```bash
# Check cluster health
ssh wizardsofts@10.0.0.84 "docker exec ray-head ray status"

# Check Celery queue lengths
ssh wizardsofts@10.0.0.84 "docker exec celery-redis redis-cli -p 6380 -a \$REDIS_PASSWORD llen celery"

# View recent task failures
# Open Flower: http://10.0.0.84:5555

# Check Prometheus alerts
# Open Grafana: http://10.0.0.84:3002
```

### Weekly Maintenance

```bash
# Review resource usage
docker stats --no-stream

# Check for failed tasks
celery -A tasks inspect active

# Review logs
docker logs ray-head --tail 500 | grep ERROR
docker logs celery-worker-ml --tail 500 | grep ERROR

# Run backup
./infrastructure/distributed-ml/scripts/backup-cluster-state.sh
```

### Monthly Review

- [ ] Review task performance metrics
- [ ] Update Python dependencies
- [ ] Check for Ray/Celery security updates
- [ ] Review and archive old logs
- [ ] Performance tuning based on usage patterns

---

## Troubleshooting Guide

### Ray Issues

**Worker not connecting:**
```bash
# Check firewall
sudo ufw status

# Check Ray head logs
docker logs ray-head

# Verify network connectivity
ping 10.0.0.84

# Check Ray GCS
docker exec ray-head ray status
```

**High memory usage:**
```bash
# Check object store usage
docker exec ray-head ray memory --stats-only

# Clear object store
docker exec ray-head ray stop
docker exec ray-head ray start --head --object-store-memory=2000000000
```

### Celery Issues

**Tasks stuck in queue:**
```bash
# Check worker status
celery -A tasks inspect active

# Restart workers
docker-compose -f docker-compose.celery.yml restart celery-worker-ml

# Purge queue (careful!)
celery -A tasks purge
```

**Redis connection errors:**
```bash
# Check Redis
docker exec celery-redis redis-cli -p 6380 -a $REDIS_PASSWORD ping

# Check connection from worker
docker exec celery-worker-default celery -A tasks inspect ping
```

---

## Cost Analysis

### Resource Requirements Summary

| Component | Server | CPU | RAM | Storage |
|-----------|--------|-----|-----|---------|
| Ray Head | Server 84 | 4 cores | 8GB | 50GB |
| Ray Worker (high-mem) | Server 81 | 8 cores | 16GB | 100GB |
| Ray Worker (standard) | Server 80 | 4 cores | 8GB | 50GB |
| Ray Worker (laptop) | Server 82 | 2 cores | 4GB | 20GB |
| Celery + Redis | Server 84 | 2 cores | 2GB | 10GB |
| **Total** | - | **20 cores** | **38GB** | **230GB** |

### Network Bandwidth

- **Inter-node traffic:** ~100-500 MB/s during training
- **Object store transfers:** ~1-2 GB for large datasets
- **Recommendation:** 1 Gbps network minimum (you have this)

---

## Success Metrics

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Task throughput | >1000 tasks/hour | Celery Flower |
| Model training time | <30 min for RandomForest | Ray Dashboard |
| Data processing | >100K rows/sec | Ray Data metrics |
| Worker utilization | >70% during peak | Prometheus |
| Task failure rate | <1% | Celery metrics |

### Availability Targets

- Ray cluster uptime: >99%
- Celery worker availability: >95%
- Scheduled tasks: 100% execution rate

---

## Next Steps After Completion

1. **Integrate with existing apps:**
   - gibd-quant-web: Use for stock predictions
   - ws-news: Use for news classification
   - gibd-quant-agent: Distributed backtesting

2. **Add more sophisticated ML pipelines:**
   - Automated feature engineering
   - Model versioning and A/B testing
   - Continuous retraining

3. **Scale horizontally:**
   - Add more laptops as workers
   - Consider cloud burst for peak loads
   - Implement hybrid cloud/on-prem

4. **Advanced monitoring:**
   - ML model drift detection
   - Automatic anomaly detection
   - Predictive resource scaling

---

## Appendix

### Useful Commands

```bash
# Ray
ray start --head
ray start --address=10.0.0.84:6379
ray stop
ray status
ray memory
ray timeline

# Celery
celery -A tasks worker
celery -A tasks beat
celery -A tasks flower
celery -A tasks inspect active
celery -A tasks inspect stats
celery -A tasks purge

# Docker
docker-compose ps
docker-compose logs -f
docker-compose restart
docker stats
```

### References

- [Ray Documentation](https://docs.ray.io/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Ray Train Guide](https://docs.ray.io/en/latest/train/train.html)
- [Ray Data Guide](https://docs.ray.io/en/latest/data/data.html)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-02
**Status:** Ready for Phase 1 implementation
**Next Review:** After Phase 1 completion

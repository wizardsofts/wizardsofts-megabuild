# GIBD Quant Celery

Celery task queue for GIBD quantitative trading workflows.

## Purpose

Handles async task execution for data processing, model training, and scheduled jobs.

## Quick Start

```bash
# Build
docker build -t gibd-quant-celery .

# Run worker
docker run --rm gibd-quant-celery celery -A src.tasks worker --loglevel=info
```

## Structure

```
src/
├── __init__.py
└── tasks/           # Celery task definitions
```

## Related

- [gibd-quant-agent](../gibd-quant-agent/README.md) - Main trading agent
- [Celery Infrastructure](../../infrastructure/distributed-ml/celery/README.md) - Celery deployment

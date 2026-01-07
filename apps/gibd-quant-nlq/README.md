# GIBD Quant NLQ

Natural Language Query service for GIBD quantitative trading system.

## Purpose

Enables natural language queries against trading data, signals, and portfolio information.

## Quick Start

```bash
# Build
docker build -t gibd-quant-nlq .

# Run
docker run --rm -p 8000:8000 gibd-quant-nlq
```

## Structure

```
src/
├── __init__.py
└── nlq/             # NLQ processing logic
```

## Related

- [gibd-quant-agent](../gibd-quant-agent/README.md) - Main trading agent
- [gibd-vector-context](../gibd-vector-context/README.md) - Vector embeddings

# GIBD Quant Signal

Trading signal generation service for GIBD quantitative trading system.

## Purpose

Generates trading signals based on technical indicators, market data, and ML models.

## Quick Start

```bash
# Build
docker build -t gibd-quant-signal .

# Run
docker run --rm gibd-quant-signal
```

## Structure

```
src/
├── __init__.py
└── signals/         # Signal generation logic
```

## Related

- [gibd-quant-agent](../gibd-quant-agent/README.md) - Main trading agent
- [gibd-news](../gibd-news/README.md) - Market data source

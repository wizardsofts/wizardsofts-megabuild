# GIBD Quant Calibration

Model calibration service for GIBD quantitative trading system.

## Purpose

This service handles model parameter calibration and optimization for trading strategies.

## Quick Start

```bash
# Build
docker build -t gibd-quant-calibration .

# Run
docker run --rm gibd-quant-calibration
```

## Structure

```
src/
├── __init__.py
└── calibration/     # Calibration algorithms
```

## Related

- [gibd-quant-agent](../gibd-quant-agent/README.md) - Main trading agent
- [gibd-quant-signal](../gibd-quant-signal/README.md) - Signal generation

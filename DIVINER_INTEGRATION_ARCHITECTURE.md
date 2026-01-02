# Diviner Integration Architecture
## Embedding Diviner into GIBD Quant Agent

**Date:** 2025-12-30
**Decision:** Integrate Diviner code into project for full control
**Location:** `apps/gibd-quant-agent/src/forecasting/diviner/`

---

## Rationale: Why Integrate vs External Dependency?

### **Benefits of Integration**

1. **Full Ownership**
   - Modify without waiting for upstream
   - No dependency on external repo maintenance
   - Control version and features

2. **DSE-Specific Customization**
   - Add DSE market hours logic
   - Handle circuit breakers (±10% limits)
   - Optimize for thin trading patterns
   - Bengali calendar awareness (Eid, holidays)

3. **Tight System Integration**
   - Direct use of `SequenceCacheHelper`
   - Shared database connections
   - Unified logging and monitoring
   - Common config management

4. **Production Readiness**
   - Single deployment unit
   - No external dependencies
   - Easier CI/CD
   - Better testing integration

5. **Team Ownership**
   - Your team understands the code
   - Can debug and optimize
   - Knowledge stays in-house
   - Faster iteration cycles

---

## Proposed Directory Structure

```
apps/gibd-quant-agent/
├── src/
│   ├── indicators/              # Existing: Technical indicators
│   │   ├── calc.py
│   │   ├── sequence_cache.py   # NEW: Added for Diviner
│   │   └── store.py
│   │
│   ├── signals/                 # Existing: Rule-based signals
│   │   ├── signal_generator.py
│   │   └── confidence.py
│   │
│   ├── forecasting/             # NEW: Deep learning forecasts
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract forecaster interface
│   │   │
│   │   ├── diviner/            # Adapted Diviner implementation
│   │   │   ├── __init__.py
│   │   │   ├── model.py        # Core Diviner model
│   │   │   ├── attention.py    # Smoothing & Difference attention
│   │   │   ├── embedding.py    # Input embeddings
│   │   │   ├── encoder.py      # Encoder layers
│   │   │   ├── decoder.py      # Decoder layers
│   │   │   ├── trainer.py      # Training loop
│   │   │   ├── config.py       # Configuration models
│   │   │   └── utils.py        # Helper functions
│   │   │
│   │   └── ensemble/           # Future: Other models
│   │       ├── lstm.py
│   │       └── transformer.py
│   │
│   ├── hybrid/                  # NEW: Combine signals + forecasts
│   │   ├── __init__.py
│   │   ├── fusion.py           # Ensemble logic
│   │   └── confidence.py       # Combined confidence scoring
│   │
│   └── backtest/                # NEW: Backtesting framework
│       ├── __init__.py
│       ├── walk_forward.py     # Walk-forward validation
│       ├── metrics.py          # Performance metrics
│       └── visualizer.py       # Results visualization
│
├── tests/
│   ├── test_indicators.py      # Existing
│   ├── test_new_indicators.py  # Just added
│   ├── test_forecasting/       # NEW
│   │   ├── test_diviner_model.py
│   │   ├── test_diviner_attention.py
│   │   ├── test_trainer.py
│   │   └── fixtures/
│   │       └── sample_data.pkl
│   └── test_hybrid/            # NEW
│       └── test_fusion.py
│
├── scripts/
│   ├── train_diviner.py        # Training script
│   ├── backtest_diviner.py     # Backtesting script
│   └── evaluate_hybrid.py      # Ensemble evaluation
│
├── config/
│   ├── diviner_config.yaml     # Diviner hyperparameters
│   └── hybrid_config.yaml      # Ensemble weights
│
└── docs/
    ├── forecasting/            # NEW
    │   ├── diviner_architecture.md
    │   ├── training_guide.md
    │   └── deployment.md
    └── api/
        └── forecasting_api.md
```

---

## Implementation Plan

### **Phase 1: Extract & Adapt Diviner Core** (Week 1)

**Tasks:**
1. Study original Diviner repo structure
2. Extract core model components
3. Adapt to our coding standards
4. Remove dependencies on their data loaders

**Files to Create:**
```python
# src/forecasting/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import numpy as np

class BaseForecaster(ABC):
    """Abstract base class for all forecasting models"""

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the model"""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions"""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save model to disk"""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model from disk"""
        pass


# src/forecasting/diviner/model.py
import torch
import torch.nn as nn
from ..base import BaseForecaster

class DSEDiviner(BaseForecaster):
    """Diviner model adapted for DSE stocks

    Based on: https://github.com/CapricornGuang/Diviner-Nonstationary-time-series-forecasting

    Key Adaptations for DSE:
    - Custom temporal encoding for Bengali calendar
    - Circuit breaker awareness (±10% daily limits)
    - Thin trading day handling
    - DSE-specific normalization
    """

    def __init__(self, config: DivinerConfig):
        super().__init__()
        self.config = config

        # Core components (adapted from original)
        self.embedding = DataEmbedding(...)
        self.encoder = Encoder(...)
        self.decoder = Decoder(...)

        # DSE-specific additions
        self.dse_calendar = DSETradingCalendar()
        self.circuit_breaker_handler = CircuitBreakerHandler()

    def fit(self, X, y):
        """Training loop with DSE-specific handling"""
        # Use our SequenceCacheHelper data
        # Apply DSE-specific preprocessing
        # Train with custom loss for thin trading days
        pass

    def predict(self, X):
        """Prediction with DSE context awareness"""
        # Check for special market conditions
        # Adjust predictions for circuit breakers
        # Return calibrated forecasts
        pass
```

---

### **Phase 2: Integration with Existing Systems** (Week 2)

**Connect to Your Infrastructure:**

```python
# src/forecasting/diviner/data_loader.py
from src.indicators.sequence_cache import SequenceCacheHelper
from src.tools.database import DatabaseReaderTool

class DivinerDataLoader:
    """Load data for Diviner using existing infrastructure"""

    def __init__(self):
        self.db_tool = DatabaseReaderTool()
        self.cache = SequenceCacheHelper(self.db_tool)

    def prepare_training_data(
        self,
        stocks: List[str],
        end_date: date,
        window_size: int = 60,
        horizon: int = 5
    ):
        """Prepare Diviner-compatible data from indicators table"""

        sequences = {}
        for stock in stocks:
            # Use YOUR sequence caching
            window = self.cache.get_sequence_window(
                scrip=stock,
                end_date=end_date,
                window_size=window_size
            )

            if window is None:
                continue

            # Extract features YOU computed
            df = self.cache.to_dataframe(window)

            # Select Diviner features
            X = df[DIVINER_FEATURES].values

            # Create targets (5-day ahead)
            y = self._create_targets(df, horizon)

            sequences[stock] = {'X': X, 'y': y, 'dates': df['trading_date']}

        return sequences
```

---

### **Phase 3: Hybrid Ensemble System** (Week 3)

**Combine Rule-Based + Diviner:**

```python
# src/hybrid/fusion.py
from src.signals.signal_generator import SignalGenerator
from src.forecasting.diviner.model import DSEDiviner

class HybridSignalEngine:
    """Combine traditional signals with Diviner forecasts"""

    def __init__(self, diviner_weight: float = 0.6):
        self.signal_gen = SignalGenerator()  # Your existing
        self.diviner = DSEDiviner.load('checkpoints/diviner_best.pt')
        self.diviner_weight = diviner_weight

    def generate_hybrid_signal(
        self,
        stock: str,
        date: date
    ) -> Dict:
        """Generate combined signal"""

        # 1. Get traditional technical signal
        tech_signal = self.signal_gen.generate_signal(stock, 'daily')

        # 2. Get Diviner forecast
        window = self.cache.get_sequence_window(stock, date, 60)
        diviner_pred = self.diviner.predict(window.features)

        # 3. Ensemble logic
        if tech_signal['recommendation'] == 'BUY' and diviner_pred['direction'] == 'UP':
            # Strong agreement
            confidence = min(100,
                tech_signal['confidence'] * 0.4 +
                diviner_pred['confidence'] * 0.6 + 20
            )
            recommendation = 'STRONG_BUY'

        elif tech_signal['recommendation'] == 'BUY' or diviner_pred['direction'] == 'UP':
            # Partial agreement
            confidence = (
                tech_signal['confidence'] * 0.4 +
                diviner_pred['confidence'] * 0.6
            )
            recommendation = 'BUY'

        else:
            # Disagreement or both bearish
            confidence = min(
                tech_signal['confidence'] * 0.4 +
                diviner_pred['confidence'] * 0.6,
                60  # Cap confidence when signals disagree
            )
            recommendation = 'HOLD'

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'components': {
                'technical': tech_signal,
                'diviner': diviner_pred
            },
            'reason': self._generate_hybrid_reason(tech_signal, diviner_pred)
        }
```

---

### **Phase 4: API Integration** (Week 4)

**New Endpoints:**

```python
# src/api/forecasting_routes.py (if using FastAPI)

@router.post("/api/forecasting/diviner/predict")
async def diviner_forecast(request: ForecastRequest):
    """Get Diviner prediction for a stock

    Example:
        POST /api/forecasting/diviner/predict
        {
            "stock": "SQURPHARMA",
            "horizon": 5,
            "date": "2025-01-15"
        }

    Returns:
        {
            "stock": "SQURPHARMA",
            "forecast_date": "2025-01-20",
            "prediction": {
                "direction": "UP",
                "probability": 0.78,
                "return_estimate": 0.034
            },
            "confidence": 78,
            "model_version": "diviner_v1.0"
        }
    """
    diviner = DSEDiviner.load('checkpoints/diviner_best.pt')

    # Load data
    cache = SequenceCacheHelper(db_tool)
    window = cache.get_sequence_window(
        scrip=request.stock,
        end_date=request.date,
        window_size=60
    )

    # Predict
    prediction = diviner.predict(window.features)

    return {
        "stock": request.stock,
        "forecast_date": request.date + timedelta(days=request.horizon),
        "prediction": prediction,
        "confidence": prediction['confidence'],
        "model_version": diviner.version
    }


@router.post("/api/signals/hybrid")
async def hybrid_signal(request: SignalRequest):
    """Get hybrid signal (technical + Diviner)

    Combines:
    - Traditional technical analysis (SMA, RSI, MACD)
    - Diviner deep learning forecast

    Returns unified recommendation with enhanced confidence.
    """
    engine = HybridSignalEngine()
    signal = engine.generate_hybrid_signal(
        stock=request.stock,
        date=request.date
    )

    return signal
```

---

## Development Workflow

### **Step 1: Extract Diviner Components**

```bash
# Clone original repo for reference
cd ~/Workspace
git clone https://github.com/CapricornGuang/Diviner-Nonstationary-time-series-forecasting.git diviner-reference

# Create our implementation
cd wizardsofts-megabuild/apps/gibd-quant-agent
mkdir -p src/forecasting/diviner

# Copy and adapt (don't just copy-paste, understand and rewrite)
# Focus on:
# - models/Diviner.py -> src/forecasting/diviner/model.py
# - layers/SelfAttention_Family.py -> src/forecasting/diviner/attention.py
# - layers/Embed.py -> src/forecasting/diviner/embedding.py
```

### **Step 2: Adapt to Your Code Style**

```python
# Follow YOUR conventions
# - Type hints everywhere
# - Docstrings in YOUR format
# - Error handling YOUR way
# - Logging via YOUR logger
# - Config via YOUR config system

# Example adaptation:
# Original Diviner:
class Diviner(nn.Module):
    def __init__(self, configs):
        super(Diviner, self).__init__()
        # ...

# YOUR adapted version:
from typing import Optional
from dataclasses import dataclass
from src.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DivinerConfig:
    """Configuration for Diviner model"""
    sequence_length: int = 60
    hidden_dim: int = 128
    # ... with type hints and defaults

class DSEDiviner(BaseForecaster):
    """Diviner model adapted for DSE

    Based on original Diviner but customized for:
    - DSE market microstructure
    - Bengali calendar
    - Circuit breaker handling
    """

    def __init__(self, config: DivinerConfig):
        super().__init__()
        self.config = config
        logger.info(f"Initializing DSEDiviner with config: {config}")
        # ... YOUR code style
```

### **Step 3: Test Thoroughly**

```python
# tests/test_forecasting/test_diviner_model.py
import pytest
import torch
from src.forecasting.diviner.model import DSEDiviner
from src.forecasting.diviner.config import DivinerConfig

class TestDSEDiviner:
    """Test suite for DSE-adapted Diviner model"""

    @pytest.fixture
    def model(self):
        config = DivinerConfig(
            sequence_length=60,
            hidden_dim=64,
            num_features=15
        )
        return DSEDiviner(config)

    def test_forward_pass(self, model):
        """Test model forward pass"""
        batch_size = 32
        X = torch.randn(batch_size, 60, 15)

        output = model(X)

        assert output.shape == (batch_size, 3)  # 3 classes: UP/DOWN/NEUTRAL

    def test_save_load(self, model, tmp_path):
        """Test model serialization"""
        save_path = tmp_path / "model.pt"

        model.save(str(save_path))
        loaded_model = DSEDiviner.load(str(save_path))

        # Same predictions
        X = torch.randn(1, 60, 15)
        assert torch.allclose(model(X), loaded_model(X))

    def test_dse_circuit_breaker_handling(self, model):
        """Test DSE-specific circuit breaker logic"""
        # TODO: Test that predictions are adjusted when circuit breaker likely
        pass
```

---

## Comparison: Integrated vs External

| Aspect | External Dependency | Integrated (Recommended) |
|--------|---------------------|--------------------------|
| **Control** | Limited | Full |
| **Customization** | Fork required | Direct modification |
| **DSE Optimization** | Difficult | Easy |
| **Integration** | Loose coupling | Tight integration |
| **Maintenance** | Upstream dependency | Your responsibility |
| **Testing** | External tests | Your test suite |
| **Deployment** | Two codebases | Single codebase |
| **Team Knowledge** | Black box | Full understanding |
| **CI/CD** | Complex | Unified |
| **Production Support** | Harder | Easier |

---

## Migration from Original Diviner

### **What to Keep:**
- ✅ Core attention mechanisms (Smoothing, Difference)
- ✅ Encoder-decoder architecture
- ✅ Model structure and design philosophy

### **What to Adapt:**
- 🔄 Data loading (use YOUR SequenceCacheHelper)
- 🔄 Config management (use YOUR config system)
- 🔄 Logging (use YOUR logger)
- 🔄 Device management (optimize for M4 MPS)
- 🔄 Checkpointing (use YOUR checkpoint format)

### **What to Add:**
- ➕ DSE market calendar
- ➕ Circuit breaker handling
- ➕ Bengali calendar awareness
- ➕ Integration with existing signals
- ➕ API endpoints
- ➕ Production monitoring

---

## Timeline with Integration

### **Revised Week 1:**
- Day 1-2: Study original Diviner code
- Day 3-4: Extract and adapt model.py, attention.py
- Day 5-6: Create data_loader.py with YOUR infrastructure
- Day 7: Write initial tests

### **Week 2:** (Unchanged)
- Training and hyperparameter tuning

### **Week 3:** (Enhanced)
- Backtesting
- **NEW:** Hybrid signal integration

### **Week 4:** (Enhanced)
- Scaling
- **NEW:** API integration
- **NEW:** Production deployment prep

---

## Decision: Yes, Integrate!

**Verdict:** ✅ **Integrate Diviner code into your project**

**Immediate Action:**
1. Create `src/forecasting/diviner/` directory structure
2. Extract core Diviner components
3. Adapt to your code style and infrastructure
4. Write tests alongside

**Long-term Benefits:**
- Full ownership and control
- Better DSE optimization
- Easier maintenance
- Unified deployment
- Team knowledge retention

---

**Ready to start?** I can help create the initial `src/forecasting/diviner/model.py` based on the original Diviner repo!

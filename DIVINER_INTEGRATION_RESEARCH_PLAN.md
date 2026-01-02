# Diviner Integration Research & Planning Document
## Nonstationary Time Series Forecasting for Technical Analysis

**Date:** 2025-12-30
**Project:** GIBD Quant Agent & RL Trader Integration
**Status:** Research & Planning Phase

---

## Executive Summary

This document outlines a comprehensive research and implementation plan for integrating the **Diviner** deep learning model into our technical analysis system. Diviner is specifically designed for nonstationary time series forecasting, making it highly suitable for stock market prediction where data distributions change over time.

### Key Recommendations

1. **Start with Individual Stocks** - Begin with stock-level forecasting before expanding to sectors
2. **Multi-level Analysis** - Implement hierarchical forecasting (stock → sector → market)
3. **Hybrid Approach** - Combine Diviner predictions with existing technical indicators
4. **Walk-Forward Backtesting** - Use expanding window validation for realistic performance evaluation

---

## 1. Understanding Diviner

### 1.1 What is Diviner?

Diviner is a PyTorch-based deep learning model published in Nature's Communications Engineering journal, designed specifically for long-term time series forecasting in nonstationary environments.

**Source:** [GitHub - Diviner Nonstationary Time Series Forecasting](https://github.com/CapricornGuang/Diviner-Nonstationary-time-series-forecasting)

### 1.2 Core Architecture

#### Smoothing Filter Attention Mechanism
- Filters out random components layer-by-layer
- Adjusts feature scale to handle varying amplitudes
- Reduces noise in nonstationary data

#### Difference Attention Module
- Captures stable shifts at multiple scales
- Determines both long-range and short-range dependencies
- Models the underlying regularities in changing distributions

#### Encoder-Decoder Structure
- Configurable number of layers and attention heads
- Multi-scale feature extraction
- Flexible prediction horizons

### 1.3 Why Diviner for Stock Markets?

Stock market data exhibits key characteristics that Diviner is designed to handle:

**Nonstationarity**: Stock prices have changing means, variances, and distributions over time ([Time Series Forecasting for Stock Markets](https://collected.jcu.edu/cgi/viewcontent.cgi?article=1148&context=honorspapers))

**Multi-scale Patterns**: Markets have patterns at different scales (intraday, daily, weekly, monthly)

**High Noise**: Financial data is contaminated with random fluctuations that need filtering

**Regime Changes**: Markets shift between bull, bear, and sideways regimes

---

## 2. Individual Stock vs Sector vs Market Level Analysis

### 2.1 Research Findings

Recent research (2024-2025) provides evidence-based guidance on forecasting granularity:

#### Individual Stock Level

**Advantages:**
- Captures company-specific factors and events
- Direct actionable trading signals
- Detailed feature engineering possible

**Challenges:**
- Higher noise and volatility
- Data quality varies by stock
- Computationally expensive for large universes
- Risk of overfitting to idiosyncratic patterns

**Research Evidence:**
> "LSTM significantly outperformed buy-and-hold strategy for stocks in the Technology and Consumer Durables sectors, but offered very minor improvement for stocks in other sectors."

**Source:** [Stock Market Prediction Using ML and DL Techniques](https://www.mdpi.com/2673-9909/5/3/76)

#### Sector/ETF Level

**Advantages:**
- Lower noise through aggregation
- More stable patterns
- Reduces dimensionality (10-15 sectors vs 500+ stocks)
- Better generalization

**Challenges:**
- Less granular trading signals
- Misses individual stock alpha opportunities
- Sector rotation timing critical

**Research Evidence:**
> "Replacing individual stocks with their corresponding Exchange Traded Sector Funds (ETFs) and S&P 500 can be justified due to high degree of returns correlation and small Hamming distances of trading signals across stocks in the same sector."

**Source:** [Deep Learning for Stock Market Prediction](https://pmc.ncbi.nlm.nih.gov/articles/PMC7517440/)

#### Market Level (Index)

**Advantages:**
- Most stable and predictable
- Best for market regime detection
- Lower computational requirements
- Strong historical data availability

**Challenges:**
- Least specific for individual trading
- Misses relative performance opportunities
- Limited actionability for stock selection

### 2.2 Recommended Approach: Hierarchical Multi-Level

Implement a three-tier forecasting system:

```
Level 1: Market (DSE Index)
    ↓ (regime context)
Level 2: Sectors (10-12 major sectors)
    ↓ (sector rotation signals)
Level 3: Individual Stocks (top liquidity/quality)
    ↓ (final stock selection)
```

**Rationale:**
1. **Market level** provides regime context (bull/bear/sideways)
2. **Sector level** identifies rotating leadership
3. **Individual stock level** picks winners within strong sectors

**Implementation Priority:**
1. **Phase 1**: Individual stocks (50-100 most liquid) - immediate value
2. **Phase 2**: Sector aggregation and sector forecasting
3. **Phase 3**: Market-level integration and hierarchical ensemble

---

## 3. Data Preparation Strategy

### 3.1 Data Sources

#### Current System Analysis
Your existing system uses:
- Database: `ws_dse_daily_prices` table
- Fields: `txn_scrip`, `txn_date`, `txn_open`, `txn_high`, `txn_low`, `txn_close`, `txn_volume`
- Timeframes: Daily and weekly
- Current lookback: 200 days for technical indicators

#### Diviner Requirements
- Minimum sequence length: Configurable (typically 36-96 time steps)
- Prediction horizon: Configurable (1-30 steps ahead)
- Feature dimensions: Multi-variate time series support

### 3.2 Feature Engineering

#### Primary Features (OHLCV)
```python
{
    "price_features": [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ],
    "derived_price_features": [
        "log_return",           # log(close_t / close_t-1)
        "high_low_range",       # (high - low) / close
        "close_open_diff",      # (close - open) / open
        "volume_change"         # volume_t / volume_t-1
    ]
}
```

#### Technical Indicators (from existing system)
```python
{
    "trend_indicators": [
        "sma_50",              # 50-day simple moving average
        "sma_200",             # 200-day simple moving average
        "ema_12",              # 12-day exponential moving average
        "ema_26",              # 26-day exponential moving average
        "price_sma50_ratio",   # close / sma_50
        "price_sma200_ratio"   # close / sma_200
    ],
    "momentum_indicators": [
        "rsi_14",              # 14-day RSI
        "macd",                # MACD line
        "macd_signal",         # MACD signal line
        "macd_histogram"       # MACD - Signal
    ],
    "volume_indicators": [
        "volume_sma_20",       # 20-day volume average
        "volume_ratio",        # volume / volume_sma_20
        "obv"                  # On-balance volume
    ],
    "volatility_indicators": [
        "atr_14",              # 14-day Average True Range
        "bollinger_upper",     # Upper Bollinger Band
        "bollinger_lower",     # Lower Bollinger Band
        "bollinger_width"      # (upper - lower) / middle
    ]
}
```

#### External/Contextual Features (Optional Phase 2)
```python
{
    "market_context": [
        "market_return",       # DSE index return
        "market_volume",       # Total market volume
        "market_volatility"    # Market-level volatility
    ],
    "sector_features": [
        "sector_return",       # Sector index return
        "sector_relative_strength"  # Sector vs market performance
    ],
    "temporal_features": [
        "day_of_week",         # Monday=1, ..., Friday=5
        "week_of_month",       # 1-4
        "month_of_year",       # 1-12
        "is_month_end",        # Boolean
        "is_quarter_end"       # Boolean
    ]
}
```

### 3.3 Data Preprocessing Pipeline

```python
preprocessing_steps = {
    "1_data_cleaning": {
        "handle_missing": "forward_fill with limit=5, then drop",
        "handle_outliers": "winsorize at 1st/99th percentile",
        "handle_zero_volume": "flag and potentially exclude",
        "corporate_actions": "adjust for splits/dividends if data available"
    },

    "2_feature_calculation": {
        "technical_indicators": "use existing IndicatorCalculator",
        "derived_features": "calculate log returns, ratios",
        "temporal_encoding": "cyclical encoding for day/month"
    },

    "3_normalization": {
        "price_features": "log transformation + standardization",
        "volume_features": "log transformation + standardization",
        "indicators": "min-max normalization to [0, 1]",
        "returns": "standardization (z-score)",

        "important": "Fit scaler on training data only, transform test separately"
    },

    "4_sequence_construction": {
        "lookback_window": 60,  # days of history
        "prediction_horizon": 5,  # days ahead to predict
        "stride": 1,  # sliding window step

        "output_format": {
            "X": "(num_samples, lookback_window, num_features)",
            "y": "(num_samples, prediction_horizon, num_targets)"
        }
    },

    "5_train_test_split": {
        "method": "temporal_split",
        "train_ratio": 0.7,
        "validation_ratio": 0.15,
        "test_ratio": 0.15,

        "critical": "NO random shuffling - preserve time order"
    }
}
```

### 3.4 Target Variable Design

#### Option A: Direct Price Prediction
```python
target = {
    "type": "price_level",
    "variable": "close_price",
    "horizon": [1, 5, 10],  # 1-day, 1-week, 2-week ahead
    "transformation": "log_price",
    "post_processing": "exp() to get actual price"
}
```

#### Option B: Return Prediction (Recommended)
```python
target = {
    "type": "returns",
    "variable": "log_return",
    "calculation": "log(close_t+h / close_t)",
    "horizon": [1, 5, 10],
    "interpretation": "easier for model, stationary-like",
    "post_processing": "convert to price via cumulative returns"
}
```

#### Option C: Direction Classification (Conservative)
```python
target = {
    "type": "direction",
    "classes": ["DOWN", "NEUTRAL", "UP"],
    "thresholds": [-0.02, 0.02],  # ±2% boundaries
    "horizon": [1, 5],
    "advantage": "easier to learn, actionable signals",
    "loss_function": "cross_entropy"
}
```

**Recommendation**: Start with **Option C (Direction)** for interpretability, then add **Option B (Returns)** for finer predictions.

### 3.5 Data Quality Filters

```python
stock_selection_criteria = {
    "minimum_history": "252 trading days (1 year)",
    "minimum_liquidity": "average daily volume > threshold",
    "minimum_price": "close > 10 BDT (avoid penny stocks)",
    "data_completeness": "< 5% missing days in lookback period",
    "listing_status": "actively traded (not suspended)"
}
```

---

## 4. Model Architecture & Configuration

### 4.1 Diviner Model Variants

Based on the repository, Diviner supports multiple configurations:

```python
model_configs = {
    "diviner_full": {
        "use_conv_generator": True,
        "use_smoothing_attention": True,
        "use_difference_attention": True,
        "description": "Full model with all components"
    },

    "diviner_lite": {
        "use_conv_generator": False,
        "use_smoothing_attention": True,
        "use_difference_attention": True,
        "description": "Lighter version, faster training"
    },

    "ablation_variants": {
        "no_smooth": "Test without smoothing attention",
        "no_diff": "Test without difference attention",
        "baseline": "Simple encoder-decoder baseline"
    }
}
```

### 4.2 Hyperparameter Ranges

```python
hyperparameters = {
    "sequence_length": [30, 60, 90],      # Input window
    "prediction_horizon": [1, 5, 10],      # Forecast horizon
    "hidden_dim": [64, 128, 256],          # Model capacity
    "num_encoder_layers": [2, 3, 4],       # Depth
    "num_decoder_layers": [2, 3],          # Depth
    "num_attention_heads": [4, 8],         # Attention heads
    "dropout": [0.1, 0.2, 0.3],           # Regularization
    "learning_rate": [1e-4, 5e-4, 1e-3],  # Optimization
    "batch_size": [32, 64, 128]            # Training batch
}
```

### 4.3 Training Configuration

```python
training_config = {
    "optimizer": "AdamW",
    "learning_rate": 1e-3,
    "lr_scheduler": {
        "type": "ReduceLROnPlateau",
        "patience": 10,
        "factor": 0.5
    },

    "loss_function": {
        "regression": "MSE or MAE",
        "classification": "CrossEntropy",
        "custom": "Combined loss (direction + magnitude)"
    },

    "regularization": {
        "dropout": 0.2,
        "weight_decay": 1e-5,
        "gradient_clipping": 1.0
    },

    "early_stopping": {
        "patience": 20,
        "monitor": "validation_loss",
        "min_delta": 1e-4
    },

    "checkpointing": {
        "save_best": True,
        "save_last": True,
        "monitor": "validation_sharpe_ratio"
    }
}
```

---

## 5. Backtesting Strategy

### 5.1 Why Traditional CV Fails for Time Series

> "Traditional cross-validation techniques cannot be used with time series data. When you randomly shuffle your data before splitting it into folds, you're accidentally allowing your model to peek into the future."

**Source:** [Time Series Cross-Validation Best Practices](https://medium.com/@pacosun/respect-the-order-cross-validation-in-time-series-7d12beab79a1)

### 5.2 Walk-Forward Validation Approach

**Recommended Method**: Expanding Window with Purging

```python
walk_forward_config = {
    "window_type": "expanding",
    "initial_train_size": 504,     # 2 years of daily data
    "validation_size": 63,          # ~3 months
    "test_size": 63,                # ~3 months
    "purge_gap": 5,                 # 5 days between train/val
    "step_size": 21,                # Re-train monthly (21 trading days)

    "workflow": [
        "Train on expanding window (t0 to t_train)",
        "Purge 5 days gap",
        "Validate on (t_train+gap to t_val)",
        "Test on (t_val to t_test)",
        "Step forward by step_size",
        "Repeat until end of data"
    ]
}
```

**Source:** [Walk-Forward Validation Guide](https://medium.com/@ahmedfahad04/understanding-walk-forward-validation-in-time-series-analysis-a-practical-guide-ea3814015abf)

### 5.3 Backtesting Pipeline

```python
backtesting_workflow = {
    "step_1_data_split": {
        "full_dataset": "2020-01-01 to 2025-12-30",
        "training_period": "2020-01-01 to 2023-12-31",
        "validation_period": "2024-01-01 to 2024-06-30",
        "test_period": "2024-07-01 to 2025-12-30"
    },

    "step_2_walk_forward_loop": """
        for fold in walk_forward_splits:
            # Fit preprocessing on train fold only
            scaler.fit(train_fold)
            X_train = scaler.transform(train_fold)
            X_val = scaler.transform(val_fold)

            # Train or update model
            if refit_strategy == "full_retrain":
                model = Diviner(config)
                model.fit(X_train, y_train, validation_data=(X_val, y_val))
            elif refit_strategy == "incremental":
                model.partial_fit(X_train, y_train)

            # Generate predictions
            predictions = model.predict(X_val)

            # Store results with timestamp
            results.append({
                'fold': fold_id,
                'predictions': predictions,
                'actuals': y_val,
                'timestamp': val_fold.index
            })
    """,

    "step_3_evaluation": {
        "statistical_metrics": [
            "MAE (Mean Absolute Error)",
            "RMSE (Root Mean Squared Error)",
            "MAPE (Mean Absolute Percentage Error)",
            "Direction Accuracy (% correct up/down)"
        ],

        "financial_metrics": [
            "Sharpe Ratio",
            "Maximum Drawdown",
            "Win Rate",
            "Profit Factor",
            "Calmar Ratio"
        ],

        "backtesting_specific": [
            "Out-of-sample R²",
            "Information Ratio",
            "Hit Ratio by horizon (1d, 5d, 10d)"
        ]
    },

    "step_4_trading_simulation": """
        # Convert predictions to trading signals
        signals = generate_signals(predictions, thresholds)

        # Simulate trading with transaction costs
        portfolio = backtest_portfolio(
            signals=signals,
            prices=actual_prices,
            initial_capital=100000,
            transaction_cost=0.002,  # 0.2% per trade
            slippage=0.0005
        )

        # Calculate performance metrics
        metrics = calculate_metrics(portfolio)
    """
}
```

### 5.4 Refit Strategy

**Options:**

1. **No Refit** (Fast): Train once, use throughout
   - Pros: Fast, simulates deployment
   - Cons: Model becomes stale

2. **Periodic Refit** (Recommended): Retrain monthly/quarterly
   - Pros: Balance between freshness and computational cost
   - Cons: Some computational overhead

3. **Rolling Refit**: Retrain at every step
   - Pros: Always fresh model
   - Cons: Computationally expensive, not realistic

**Recommendation**: **Periodic Refit** every 21 trading days (monthly)

**Source:** [How to Backtest ML Models for Time Series](https://machinelearningmastery.com/backtest-machine-learning-models-time-series-forecasting/)

### 5.5 Critical Considerations

```python
backtesting_best_practices = {
    "data_leakage_prevention": [
        "Never use future data in features",
        "Fit scalers only on training data",
        "No look-ahead bias in indicators",
        "Respect trading calendar (no weekends)"
    ],

    "realistic_constraints": [
        "Include transaction costs (0.15-0.25% DSE)",
        "Model slippage (0.05-0.1%)",
        "Consider liquidity limits",
        "Account for failed orders",
        "Respect position size limits"
    ],

    "statistical_validity": [
        "Minimum 50+ trades for significance",
        "Bootstrap confidence intervals",
        "Multiple random seeds for robustness",
        "Test on multiple time periods (bull/bear/sideways)"
    ]
}
```

---

## 6. Integration with Existing System

### 6.1 Current System Architecture

**Existing Components:**
- **SignalGenerator**: Rule-based technical analysis (SMA, RSI, MACD, Volume)
- **BatchSignalRunner**: Process 500+ stocks
- **ConfidenceCalculator**: 0-100 confidence scores
- **ReasonGenerator**: Natural language explanations
- **RL Trader**: PPO-based reinforcement learning agent

### 6.2 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  (ws_dse_daily_prices + External Data + News)               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              Feature Engineering Layer                       │
│  • OHLCV Processing                                         │
│  • Technical Indicators (existing IndicatorCalculator)      │
│  • Diviner-specific features                                │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
┌──────────────┐  ┌──────────────────────┐
│ Rule-Based   │  │  Diviner Forecaster  │
│ Signals      │  │  (Deep Learning)     │
│ (Existing)   │  │                      │
└──────┬───────┘  └──────┬───────────────┘
       │                 │
       │                 ↓
       │          ┌────────────────┐
       │          │  Prediction    │
       │          │  Ensemble      │
       │          │  & Fusion      │
       │          └────────┬───────┘
       │                   │
       └───────┬───────────┘
               ↓
    ┌──────────────────────┐
    │  Signal Aggregator   │
    │  • Confidence Blend  │
    │  • Reason Generation │
    └──────────┬───────────┘
               │
               ↓
    ┌──────────────────────┐
    │  Decision Layer      │
    │  • Portfolio Opt     │
    │  • Risk Management   │
    │  • RL Agent (PPO)    │
    └──────────┬───────────┘
               │
               ↓
    ┌──────────────────────┐
    │  Execution Layer     │
    │  • Order Generation  │
    │  • Paper/Live Trade  │
    └──────────────────────┘
```

### 6.3 Hybrid Signal Generation

**Ensemble Strategy:**

```python
hybrid_signal_config = {
    "method": "weighted_ensemble",

    "components": {
        "rule_based": {
            "weight": 0.4,
            "source": "existing SignalGenerator",
            "strengths": ["interpretable", "fast", "proven"],
            "weaknesses": ["limited_patterns", "no_learning"]
        },

        "diviner_forecast": {
            "weight": 0.6,
            "source": "Diviner model predictions",
            "strengths": ["learns_patterns", "nonstationary", "multi_horizon"],
            "weaknesses": ["black_box", "needs_data", "computational"]
        }
    },

    "fusion_rules": {
        "high_agreement": {
            "condition": "both_bullish or both_bearish",
            "action": "boost confidence by 20%",
            "confidence_floor": 70
        },

        "disagreement": {
            "condition": "opposite signals",
            "action": "reduce confidence by 30%",
            "override": "set to HOLD if conf < 40"
        },

        "diviner_strong": {
            "condition": "diviner_conf > 85 and rule_conf < 60",
            "action": "follow diviner with 70% weight"
        }
    },

    "confidence_calculation": """
        base_confidence = (
            rule_based_conf * 0.4 +
            diviner_conf * 0.6
        )

        # Adjust for agreement
        if signals_agree:
            final_confidence = min(100, base_confidence * 1.2)
        else:
            final_confidence = base_confidence * 0.7

        # Floor and ceiling
        final_confidence = max(20, min(95, final_confidence))
    """
}
```

### 6.4 Reason Generation Enhancement

```python
enhanced_reasoning = {
    "template": """
    Technical Analysis:
    {rule_based_reason}

    AI Forecast:
    • Predicted {horizon}-day return: {predicted_return}
    • Direction confidence: {direction_conf}%
    • Key pattern: {learned_pattern_description}

    Combined Signal: {final_signal}
    Confidence: {final_confidence}%
    Reason: {synthesis_of_both}
    """,

    "example_output": """
    Technical Analysis:
    Bullish - Price above both 50-day and 200-day MA in golden cross
    formation. RSI at 62 shows momentum without overbought. MACD
    positive with increasing histogram.

    AI Forecast:
    • Predicted 5-day return: +3.2%
    • Direction confidence: 78%
    • Key pattern: Strong uptrend with stable volatility, similar to
      previous breakout in Nov 2024

    Combined Signal: STRONG BUY
    Confidence: 82%
    Reason: Both traditional technical indicators and AI forecast align
    on bullish outlook. Multiple timeframes confirm upward momentum.
    Entry timing favorable based on volume analysis.
    """
}
```

### 6.5 API Endpoints

**New Endpoints to Add:**

```python
api_endpoints = {
    "POST /api/diviner/forecast": {
        "description": "Get Diviner forecast for a stock",
        "params": {
            "ticker": "string",
            "horizon": "int (1, 5, 10 days)",
            "include_confidence": "bool"
        },
        "response": {
            "ticker": "SQURPHARMA",
            "forecast": {
                "1d": {"return": 0.012, "direction": "UP", "prob": 0.78},
                "5d": {"return": 0.034, "direction": "UP", "prob": 0.72},
                "10d": {"return": 0.051, "direction": "UP", "prob": 0.65}
            },
            "confidence": 78,
            "model_version": "diviner_v1.2",
            "timestamp": "2025-12-30T10:00:00Z"
        }
    },

    "POST /api/signals/hybrid": {
        "description": "Get hybrid signal (rule-based + Diviner)",
        "params": {
            "ticker": "string",
            "ensemble_method": "weighted | voting | stacking"
        },
        "response": {
            "ticker": "SQURPHARMA",
            "signal": "BUY",
            "confidence": 82,
            "components": {
                "technical": {"signal": "BUY", "conf": 75},
                "diviner": {"signal": "BUY", "conf": 85}
            },
            "reasoning": "Combined technical and AI analysis...",
            "timestamp": "2025-12-30T10:00:00Z"
        }
    },

    "GET /api/diviner/performance": {
        "description": "Get backtesting performance metrics",
        "response": {
            "model_version": "diviner_v1.2",
            "backtest_period": "2024-01-01 to 2025-12-30",
            "metrics": {
                "direction_accuracy": 0.67,
                "sharpe_ratio": 1.45,
                "max_drawdown": -0.18,
                "win_rate": 0.58
            }
        }
    }
}
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Setup infrastructure and baseline

```markdown
Tasks:
1. [ ] Setup development environment
   - Clone Diviner repository
   - Install PyTorch, dependencies
   - Setup separate conda/venv

2. [ ] Data pipeline development
   - Extract OHLCV from ws_dse_daily_prices
   - Implement feature engineering pipeline
   - Create train/val/test splits

3. [ ] Baseline model training
   - Train Diviner on 5-10 liquid stocks
   - Single prediction horizon (5-day)
   - Basic hyperparameters

4. [ ] Initial validation
   - Simple backtest (expanding window)
   - Calculate direction accuracy
   - Document baseline performance

Deliverables:
- Working Diviner training pipeline
- Baseline model checkpoints
- Initial performance report
```

### Phase 2: Experimentation (Weeks 3-4)
**Goal**: Optimize model and features

```markdown
Tasks:
1. [ ] Feature engineering experiments
   - Test different feature combinations
   - Add external features (market, sector)
   - Test temporal encodings

2. [ ] Hyperparameter tuning
   - Grid search on key parameters
   - Test sequence lengths (30, 60, 90)
   - Test model architectures (lite vs full)

3. [ ] Multi-horizon forecasting
   - Train for 1d, 5d, 10d horizons
   - Compare single vs multi-output models
   - Evaluate horizon-specific performance

4. [ ] Backtesting refinement
   - Implement walk-forward validation
   - Add transaction costs
   - Test different refit strategies

Deliverables:
- Optimized model configuration
- Feature importance analysis
- Comprehensive backtest results
```

### Phase 3: Scaling (Weeks 5-6)
**Goal**: Extend to more stocks and sectors

```markdown
Tasks:
1. [ ] Universe expansion
   - Train models for 50-100 stocks
   - Implement batch training pipeline
   - Manage model registry/versioning

2. [ ] Sector-level forecasting
   - Aggregate stocks into sectors
   - Train sector-level models
   - Compare sector vs stock performance

3. [ ] Transfer learning
   - Test pre-training on market data
   - Fine-tune for individual stocks
   - Evaluate performance gains

4. [ ] Infrastructure optimization
   - Parallel training for multiple stocks
   - Model compression/quantization
   - Inference optimization

Deliverables:
- Multi-stock model registry
- Sector forecasting models
- Scalability performance report
```

### Phase 4: Integration (Weeks 7-8)
**Goal**: Integrate with existing system

```markdown
Tasks:
1. [ ] Hybrid signal generator
   - Implement ensemble logic
   - Integrate with SignalGenerator
   - Enhanced confidence scoring

2. [ ] API development
   - /api/diviner/forecast endpoint
   - /api/signals/hybrid endpoint
   - /api/diviner/performance endpoint

3. [ ] Reasoning enhancement
   - Combine rule-based + AI reasons
   - Pattern explanation generation
   - Confidence interpretation

4. [ ] RL trader integration
   - Add Diviner predictions as features
   - Test performance in paper trading
   - Compare with baseline RL agent

Deliverables:
- Hybrid signal API
- Integration documentation
- A/B testing setup
```

### Phase 5: Production (Weeks 9-10)
**Goal**: Deploy and monitor

```markdown
Tasks:
1. [ ] Model deployment
   - Setup model serving (TorchServe or FastAPI)
   - Implement model versioning
   - Setup monitoring and logging

2. [ ] Automated retraining
   - Schedule periodic retraining
   - Validation checks before deployment
   - Automated backtesting reports

3. [ ] Performance monitoring
   - Real-time prediction logging
   - Daily performance metrics
   - Alert system for degradation

4. [ ] Documentation & handoff
   - User guide for hybrid signals
   - Model cards for each stock
   - Operational runbook

Deliverables:
- Production deployment
- Monitoring dashboard
- Complete documentation
```

---

## 8. Success Metrics

### 8.1 Model Performance Metrics

```python
success_criteria = {
    "forecasting_accuracy": {
        "direction_accuracy_1d": "> 55%",  # Beat random (50%)
        "direction_accuracy_5d": "> 58%",
        "direction_accuracy_10d": "> 60%",

        "mae_returns": "< 0.03 (3% average error)",
        "rmse_returns": "< 0.05"
    },

    "trading_performance": {
        "sharpe_ratio": "> 1.0",
        "max_drawdown": "< 25%",
        "win_rate": "> 52%",
        "profit_factor": "> 1.3",

        "benchmark": "beat buy-and-hold by 5%+ annually"
    },

    "system_performance": {
        "inference_latency": "< 100ms per stock",
        "training_time": "< 2 hours per stock",
        "model_size": "< 50MB per checkpoint"
    }
}
```

### 8.2 Comparison Benchmarks

```python
benchmarks = {
    "baseline_1": {
        "name": "Buy and Hold",
        "description": "Simply hold DSE index or stock"
    },

    "baseline_2": {
        "name": "Existing Rule-Based System",
        "description": "Current SignalGenerator performance"
    },

    "baseline_3": {
        "name": "Simple LSTM",
        "description": "Vanilla LSTM without Diviner's innovations"
    },

    "target": {
        "name": "Diviner Hybrid System",
        "requirement": "Outperform all baselines on risk-adjusted returns"
    }
}
```

---

## 9. Risk Mitigation

### 9.1 Technical Risks

```python
technical_risks = {
    "overfitting": {
        "risk": "Model learns noise instead of signal",
        "mitigation": [
            "Use walk-forward validation",
            "Regular dropout and regularization",
            "Early stopping on validation set",
            "Test on multiple time periods"
        ]
    },

    "data_quality": {
        "risk": "Poor data leads to poor predictions",
        "mitigation": [
            "Implement strict data quality checks",
            "Handle missing data appropriately",
            "Validate against known events",
            "Manual spot checks on random samples"
        ]
    },

    "concept_drift": {
        "risk": "Market regime changes invalidate model",
        "mitigation": [
            "Periodic model retraining",
            "Monitor prediction performance",
            "Detect distribution shifts",
            "Ensemble of models from different periods"
        ]
    },

    "computational_cost": {
        "risk": "Training/inference too slow/expensive",
        "mitigation": [
            "Start with lite model variant",
            "Use model compression",
            "Batch inference efficiently",
            "Consider using GPU acceleration"
        ]
    }
}
```

### 9.2 Business Risks

```python
business_risks = {
    "user_trust": {
        "risk": "Users don't trust 'black box' AI",
        "mitigation": [
            "Provide clear explanations",
            "Show backtesting results transparently",
            "Allow users to weight rule-based vs AI",
            "Start with low-stakes recommendations"
        ]
    },

    "false_confidence": {
        "risk": "Over-reliance on model predictions",
        "mitigation": [
            "Clear confidence intervals",
            "Warning when data is out-of-distribution",
            "Ensemble with rule-based for safety",
            "Conservative position sizing recommendations"
        ]
    },

    "regulatory": {
        "risk": "AI recommendations may need disclosures",
        "mitigation": [
            "Label AI predictions clearly",
            "Include standard disclaimers",
            "Keep audit trail of predictions",
            "Consult with compliance if needed"
        ]
    }
}
```

---

## 10. Resource Requirements

### 10.1 Computational Resources

```python
compute_requirements = {
    "development": {
        "hardware": "GPU (NVIDIA RTX 3060 or better) with 12GB+ VRAM",
        "cloud_option": "AWS p3.2xlarge or GCP n1-standard-4 with V100",
        "storage": "500GB SSD for data + models",
        "ram": "32GB recommended"
    },

    "production": {
        "inference": "CPU sufficient, GPU optional for speed",
        "serving": "4-8 CPU cores, 16GB RAM",
        "storage": "100GB for model registry + logs",
        "backup": "Daily snapshots of models + data"
    }
}
```

### 10.2 Personnel & Skills

```python
team_requirements = {
    "ml_engineer": {
        "skills": ["PyTorch", "Time Series", "Model Deployment"],
        "effort": "60% FTE for 10 weeks"
    },

    "data_engineer": {
        "skills": ["ETL", "SQL", "Data Quality"],
        "effort": "30% FTE for 6 weeks"
    },

    "backend_developer": {
        "skills": ["FastAPI", "Integration", "Testing"],
        "effort": "40% FTE for 4 weeks"
    },

    "domain_expert": {
        "skills": ["Finance", "Technical Analysis", "Validation"],
        "effort": "20% FTE throughout project"
    }
}
```

### 10.3 Software & Libraries

```python
dependencies = {
    "core": [
        "pytorch >= 1.12.0",
        "numpy >= 1.21.0",
        "pandas >= 1.3.0",
        "scikit-learn >= 1.0.0"
    ],

    "technical_analysis": [
        "ta-lib",  # Already in use
        "pandas_ta"  # Alternative/supplement
    ],

    "serving": [
        "fastapi",
        "uvicorn",
        "pydantic"
    ],

    "monitoring": [
        "mlflow",  # Experiment tracking
        "wandb",  # Alternative
        "tensorboard"  # Visualization
    ],

    "backtesting": [
        "backtrader",  # Optional
        "vectorbt",  # Fast backtesting
        "custom implementation"  # Recommended
    ]
}
```

---

## 11. Research Questions & Future Directions

### 11.1 Open Research Questions

```markdown
1. **Optimal Prediction Horizon**
   - Is 5-day the sweet spot, or should we focus on 1-day or 10-day?
   - How does accuracy degrade with longer horizons?

2. **Feature Selection**
   - Which technical indicators are most predictive for Diviner?
   - Do external features (news, sentiment) improve performance?

3. **Ensemble Architecture**
   - What's the optimal weight between rule-based and Diviner?
   - Should weights be dynamic based on market regime?

4. **Transfer Learning**
   - Can we pre-train on developed markets (US) and fine-tune on DSE?
   - How much does transfer learning help with limited DSE data?

5. **Market Regime Detection**
   - Can Diviner detect regime changes (bull/bear/sideways)?
   - Should we have separate models per regime?

6. **Multi-Task Learning**
   - Can we jointly predict price, volume, and volatility?
   - Does multi-task learning improve individual predictions?
```

### 11.2 Future Enhancements

```markdown
1. **Attention Visualization**
   - Visualize which features Diviner attends to
   - Interpretability for user trust

2. **Uncertainty Quantification**
   - Provide prediction intervals, not just point estimates
   - Use dropout at inference for uncertainty estimation

3. **Reinforcement Learning Integration**
   - Use Diviner forecasts as state features for RL agent
   - Train RL agent to decide when to trust Diviner vs rules

4. **News & Sentiment**
   - Incorporate news sentiment scores
   - Event-driven prediction adjustments

5. **Intraday Forecasting**
   - Extend to intraday (hourly/minute) predictions
   - High-frequency trading applications

6. **Portfolio Optimization**
   - Use forecasts for multi-stock portfolio construction
   - Mean-variance optimization with Diviner returns
```

---

## 12. Key Research Sources

### Academic Papers & Technical Documentation

1. [GitHub - Diviner Nonstationary Time Series Forecasting](https://github.com/CapricornGuang/Diviner-Nonstationary-time-series-forecasting)

2. [Stock Market Prediction Using Machine Learning and Deep Learning Techniques](https://www.mdpi.com/2673-9909/5/3/76)

3. [Deep Learning for Stock Market Prediction - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7517440/)

4. [Understanding Walk Forward Validation in Time Series Analysis](https://medium.com/@ahmedfahad04/understanding-walk-forward-validation-in-time-series-analysis-a-practical-guide-ea3814015abf)

5. [Time Series Cross-Validation Best Practices](https://medium.com/@pacosun/respect-the-order-cross-validation-in-time-series-7d12beab79a1)

6. [How To Backtest Machine Learning Models for Time Series Forecasting](https://machinelearningmastery.com/backtest-machine-learning-models-time-series-forecasting/)

7. [Putting Your Forecasting Model to the Test: A Guide to Backtesting](https://towardsdatascience.com/putting-your-forecasting-model-to-the-test-a-guide-to-backtesting-24567d377fb5/)

8. [Time Series Forecasting for Stock Market Prices](https://collected.jcu.edu/cgi/viewcontent.cgi?article=1148&context=honorspapers)

---

## 13. Conclusion & Recommendations

### Summary of Recommendations

1. **Start with Individual Stocks (Phase 1)**
   - Focus on 50-100 most liquid DSE stocks
   - Immediate business value for stock selection
   - Build expertise before scaling

2. **Multi-Horizon Forecasting**
   - Primary: 5-day (1 week) forecasts
   - Secondary: 1-day and 10-day
   - Cater to different trading styles

3. **Hybrid Approach**
   - Combine Diviner (60%) + Rule-Based (40%)
   - Leverage strengths of both
   - Gradual transition as confidence grows

4. **Rigorous Backtesting**
   - Walk-forward validation with expanding window
   - Monthly retraining schedule
   - Include realistic transaction costs

5. **Phased Rollout**
   - 10 weeks to production
   - Start with paper trading
   - A/B test before full deployment

### Expected Outcomes

**Conservative Estimate:**
- Direction accuracy: 55-60% (1-day), 58-65% (5-day)
- Sharpe ratio: 1.0-1.5
- Outperformance vs buy-and-hold: 5-10% annually

**Optimistic Estimate:**
- Direction accuracy: 60-68% (1-day), 65-72% (5-day)
- Sharpe ratio: 1.5-2.0
- Outperformance vs buy-and-hold: 10-20% annually

### Go/No-Go Decision Criteria

**Proceed to Phase 2 if Phase 1 Achieves:**
- Direction accuracy > 55% on 5-day forecasts
- Sharpe ratio > 0.8 in backtest
- Inference latency < 200ms

**Proceed to Production if Phase 4 Achieves:**
- Hybrid system outperforms rule-based by 3%+ in paper trading
- No major data quality or infrastructure issues
- Positive feedback from pilot users

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Next Review:** After Phase 1 completion

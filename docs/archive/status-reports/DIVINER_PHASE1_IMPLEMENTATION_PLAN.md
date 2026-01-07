# Diviner Phase 1 Implementation Plan
## 5-Day Stock Price Forecasting with Nonstationary Time Series

**Date:** 2025-12-30
**Hardware:** MacBook Pro M4 Max (32GB RAM)
**Objective:** Train baseline Diviner model on high-volume DSE stocks
**Forecast Horizon:** 5 days
**Timeline:** 4 weeks

---

## Executive Summary

Build and validate a Diviner-based forecasting system for DSE stocks, focusing on 5-day ahead predictions for high-volume, high-volatility securities. Leverage the new indicators from `feature/diviner-indicators` branch and the M4 Max's Neural Engine for accelerated training.

**Success Criteria:**
- ✅ Direction accuracy >55% on 5-day forecasts
- ✅ Sharpe ratio >0.8 in backtesting
- ✅ Training time <2 hours per stock
- ✅ Baseline performance documented for future improvements

---

## Hardware Assessment: MacBook Pro M4 Max

### **Excellent Choice for ML!** 🚀

Your M4 Max is actually **better** than a consumer GPU for this task:

**Advantages:**
- ✅ **128GB unified memory bandwidth** (vs ~448GB/s on RTX 3060)
- ✅ **Metal Performance Shaders (MPS)** - PyTorch native support
- ✅ **40-core GPU** with 32GB shared memory (no transfers!)
- ✅ **Low power, silent operation** (no thermal throttling)

**Performance Estimate:**
- Training Diviner on 60-day windows: **~15-30 min per stock**
- Batch inference (100 stocks): **~5-10 seconds**
- Much faster than CPU, competitive with mid-range GPUs

**Setup Note:**
- Use PyTorch with MPS backend (`device='mps'`)
- Batch size: 64-128 (plenty of memory)
- FP16 training: Supported for 2x speedup

---

## Target Stocks: High Volume & Volatility

Based on DSE characteristics, here are the recommended stocks:

### **Tier 1: Primary Focus (Top 5)**
High liquidity + volatility, best for initial training

1. **SQURPHARMA** - Pharmaceuticals, consistent volume
2. **BATBC** - Tobacco, high trading activity
3. **BRACBANK** - Banking, volatile
4. **HEIDELBCEM** - Cement, industrial sector
5. **BEXIMCO** - Conglomerate, high volatility

### **Tier 2: Secondary Testing (5 more)**
For validation and diversity

6. **RENATA** - Pharmaceuticals
7. **MARICO** - Consumer goods
8. **WALTONHIL** - Electronics/manufacturing
9. **CITYBANK** - Banking
10. **GPH** - Pharma, high volume

### **Selection Criteria:**
- Average daily volume >5M shares
- Price volatility (30-day std) >3%
- Trading days >90% of calendar days
- Market cap >5B BDT

**Recommendation:** Start with **Tier 1 (5 stocks)** for Week 1-2, expand to Tier 2 in Week 3.

---

## Week-by-Week Implementation Plan

### **Week 1: Environment Setup & Data Preparation**

#### **Day 1-2: Development Environment**

**Tasks:**
1. Clone Diviner repository
2. Setup PyTorch with MPS support
3. Install dependencies
4. Verify GPU acceleration

**Commands:**
```bash
# Navigate to projects directory
cd ~/Workspace

# Clone Diviner
git clone https://github.com/CapricornGuang/Diviner-Nonstationary-time-series-forecasting.git
cd Diviner-Nonstationary-time-series-forecasting

# Create virtual environment
python3 -m venv venv-diviner
source venv-diviner/bin/activate

# Install PyTorch with MPS support
pip install torch torchvision torchaudio

# Install other dependencies
pip install numpy pandas scikit-learn matplotlib tqdm

# Verify MPS
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

**Expected Output:** `MPS available: True`

---

#### **Day 3-4: Data Pipeline**

**Objective:** Extract indicator sequences for Tier 1 stocks

**Implementation:**
```python
# File: scripts/prepare_diviner_data.py
from datetime import date, timedelta
from src.indicators.sequence_cache import SequenceCacheHelper
from src.tools.database import DatabaseReaderTool
import pandas as pd
import numpy as np
import pickle

# Initialize
db_tool = DatabaseReaderTool()
cache_helper = SequenceCacheHelper(db_tool)

# Target stocks
TIER1_STOCKS = ['SQURPHARMA', 'BATBC', 'BRACBANK', 'HEIDELBCEM', 'BEXIMCO']

# Parameters
WINDOW_SIZE = 60  # 60 days of history
HORIZON = 5       # 5-day forecast
END_DATE = date(2025, 1, 15)  # Adjust to latest available

# Fetch sequences
data = {}
for stock in TIER1_STOCKS:
    print(f"Fetching {stock}...")
    window = cache_helper.get_sequence_window(
        scrip=stock,
        end_date=END_DATE,
        window_size=WINDOW_SIZE
    )

    if window is None:
        print(f"  ⚠️  Insufficient data for {stock}")
        continue

    # Convert to DataFrame
    df = cache_helper.to_dataframe(window)

    # Validate
    validation = cache_helper.validate_completeness(window)
    if not validation['is_complete']:
        print(f"  ⚠️  Incomplete data: {validation['missing_features']}")

    data[stock] = df
    print(f"  ✅ {len(df)} days retrieved")

# Save to disk
with open('data/tier1_sequences.pkl', 'wb') as f:
    pickle.dump(data, f)

print(f"\n✅ Saved {len(data)} stocks to data/tier1_sequences.pkl")
```

**Run:**
```bash
cd ~/Workspace/wizardsofts-megabuild/apps/gibd-quant-agent
python scripts/prepare_diviner_data.py
```

---

#### **Day 5-7: Feature Engineering & Normalization**

**Objective:** Prepare features in Diviner-compatible format

**Key Decisions:**
1. **Feature Selection:** Which indicators to use
2. **Normalization:** How to scale for neural networks
3. **Target Variable:** Direction classification or returns

**Feature Set (Recommended 15 features):**
```python
DIVINER_FEATURES = [
    # Price-based
    'log_return',           # NEW: Stationary returns
    'close_open_diff',      # NEW: Intraday sentiment
    'high_low_range',       # NEW: Intraday volatility

    # Trend
    'SMA_20', 'SMA_50',     # Moving averages
    'EMA_20', 'EMA_50',     # Exponential MAs

    # Momentum
    'RSI_14',               # Oversold/overbought
    'MACD_line_12_26_9',    # Trend strength
    'MACD_hist_12_26_9',    # Momentum

    # Volume
    'volume_ratio_20',      # NEW: Volume anomaly detection
    'OBV',                  # Cumulative volume

    # Volatility
    'ATR_14',               # Average true range
    'BOLLINGER_bandwidth_20_2',  # Volatility bands

    # Temporal
    'day_of_week',          # NEW: Weekday patterns
    'is_month_end'          # NEW: Month-end effects
]
```

**Normalization Strategy:**
```python
# File: scripts/normalize_features.py
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import numpy as np

def prepare_diviner_input(df, features, horizon=5):
    """Prepare data for Diviner training

    Args:
        df: DataFrame with indicators
        features: List of feature names to use
        horizon: Forecast horizon (days)

    Returns:
        X: (samples, sequence_length, num_features)
        y: (samples, horizon) - target returns or direction
    """
    # Extract feature values
    X_raw = df[features].values

    # Separate normalization for different feature types
    price_features = ['log_return', 'close_open_diff', 'high_low_range']
    bounded_features = ['RSI_14', 'volume_ratio_20']  # Already 0-100 or ratios
    temporal_features = ['day_of_week', 'is_month_end']

    X_normalized = X_raw.copy()

    # Standardize price-derived features (z-score)
    price_idx = [features.index(f) for f in price_features if f in features]
    if price_idx:
        scaler_price = StandardScaler()
        X_normalized[:, price_idx] = scaler_price.fit_transform(X_raw[:, price_idx])

    # Min-max normalize bounded features
    bounded_idx = [features.index(f) for f in bounded_features if f in features]
    if bounded_idx:
        scaler_bounded = MinMaxScaler()
        X_normalized[:, bounded_idx] = scaler_bounded.fit_transform(X_raw[:, bounded_idx])

    # Temporal features: one-hot or cyclical encoding
    # For simplicity, normalize day_of_week to [0, 1]
    dow_idx = features.index('day_of_week') if 'day_of_week' in features else None
    if dow_idx is not None:
        X_normalized[:, dow_idx] = (X_raw[:, dow_idx] - 1) / 4.0  # 1-5 -> 0-1

    # Create targets: 5-day ahead returns
    close_prices = df['close'].values  # Assume close exists
    y_returns = []
    for i in range(len(df) - horizon):
        future_return = np.log(close_prices[i + horizon] / close_prices[i])
        y_returns.append(future_return)

    y_returns = np.array(y_returns)

    # Align X with y (drop last 'horizon' samples from X)
    X_normalized = X_normalized[:-horizon]

    # Convert to direction classification (UP/DOWN/NEUTRAL)
    threshold = 0.02  # ±2%
    y_direction = np.zeros_like(y_returns, dtype=int)
    y_direction[y_returns > threshold] = 2   # UP
    y_direction[y_returns < -threshold] = 0  # DOWN
    y_direction[(y_returns >= -threshold) & (y_returns <= threshold)] = 1  # NEUTRAL

    return X_normalized, y_returns, y_direction, (scaler_price, scaler_bounded)


# Example usage
df = pd.read_pickle('data/tier1_sequences.pkl')['SQURPHARMA']
X, y_returns, y_direction, scalers = prepare_diviner_input(df, DIVINER_FEATURES, horizon=5)

print(f"X shape: {X.shape}")  # (samples, features)
print(f"y_returns shape: {y_returns.shape}")
print(f"y_direction distribution: UP={np.sum(y_direction==2)}, NEUTRAL={np.sum(y_direction==1)}, DOWN={np.sum(y_direction==0)}")
```

---

### **Week 2: Model Training & Hyperparameter Tuning**

#### **Day 8-10: Baseline Diviner Training**

**Objective:** Train first Diviner model on SQURPHARMA

**Configuration:**
```python
# config/diviner_config.py
DIVINER_CONFIG = {
    # Data
    'sequence_length': 60,      # 60-day lookback
    'prediction_horizon': 5,    # 5-day forecast
    'num_features': 15,         # Feature count

    # Model architecture
    'model_type': 'diviner_lite',  # Start with lite version
    'hidden_dim': 128,          # Model capacity
    'num_encoder_layers': 3,    # Depth
    'num_decoder_layers': 2,
    'num_attention_heads': 4,   # Multi-head attention
    'dropout': 0.2,             # Regularization

    # Training
    'batch_size': 64,           # M4 Max can handle this
    'learning_rate': 0.001,
    'num_epochs': 100,
    'early_stopping_patience': 15,
    'device': 'mps',            # Use M4 GPU

    # Optimization
    'optimizer': 'AdamW',
    'lr_scheduler': 'ReduceLROnPlateau',
    'scheduler_patience': 10,
    'scheduler_factor': 0.5,

    # Loss
    'task': 'classification',   # UP/DOWN/NEUTRAL
    'num_classes': 3,
    'class_weights': [1.0, 0.5, 1.0]  # Downweight NEUTRAL
}
```

**Training Script:**
```python
# scripts/train_diviner.py
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from datetime import date
import numpy as np

# Diviner imports (from cloned repo)
from models.Diviner import Diviner  # Adjust path as needed

class StockForecastDataset(Dataset):
    """Dataset for time series forecasting"""

    def __init__(self, X, y, sequence_length=60):
        self.X = X
        self.y = y
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.X) - self.sequence_length

    def __getitem__(self, idx):
        # Get sequence window
        x_seq = self.X[idx:idx + self.sequence_length]
        y_target = self.y[idx + self.sequence_length]

        return (
            torch.FloatTensor(x_seq),
            torch.LongTensor([y_target])
        )


def train_diviner(stock_name, X, y_direction, config):
    """Train Diviner model for a single stock"""

    print(f"\n{'='*60}")
    print(f"Training Diviner for {stock_name}")
    print(f"{'='*60}\n")

    # Train/val/test split (70/15/15)
    n = len(X)
    train_size = int(0.7 * n)
    val_size = int(0.15 * n)

    X_train = X[:train_size]
    y_train = y_direction[:train_size]

    X_val = X[train_size:train_size + val_size]
    y_val = y_direction[train_size:train_size + val_size]

    X_test = X[train_size + val_size:]
    y_test = y_direction[train_size + val_size:]

    # Create datasets
    train_dataset = StockForecastDataset(X_train, y_train, config['sequence_length'])
    val_dataset = StockForecastDataset(X_val, y_val, config['sequence_length'])

    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'], shuffle=False)

    # Initialize model
    device = torch.device(config['device'])
    model = Diviner(
        enc_in=config['num_features'],
        dec_in=config['num_features'],
        c_out=config['num_classes'],
        seq_len=config['sequence_length'],
        pred_len=1,  # Predicting single future point
        d_model=config['hidden_dim'],
        n_heads=config['num_attention_heads'],
        e_layers=config['num_encoder_layers'],
        d_layers=config['num_decoder_layers'],
        dropout=config['dropout']
    ).to(device)

    # Loss and optimizer
    class_weights = torch.FloatTensor(config['class_weights']).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config['learning_rate'])
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        patience=config['scheduler_patience'],
        factor=config['scheduler_factor']
    )

    # Training loop
    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(config['num_epochs']):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_X, batch_y in train_loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device).squeeze()

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            train_correct += (predicted == batch_y).sum().item()
            train_total += batch_y.size(0)

        train_acc = 100 * train_correct / train_total

        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X = batch_X.to(device)
                batch_y = batch_y.to(device).squeeze()

                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)

                val_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                val_correct += (predicted == batch_y).sum().item()
                val_total += batch_y.size(0)

        val_acc = 100 * val_correct / val_total

        # Learning rate scheduling
        scheduler.step(val_loss)

        # Print progress
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{config['num_epochs']}")
            print(f"  Train Loss: {train_loss/len(train_loader):.4f}, Acc: {train_acc:.2f}%")
            print(f"  Val Loss: {val_loss/len(val_loader):.4f}, Acc: {val_acc:.2f}%")

        # Early stopping
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), f'checkpoints/{stock_name}_best.pt')
        else:
            patience_counter += 1
            if patience_counter >= config['early_stopping_patience']:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    print(f"\n✅ Best validation accuracy: {best_val_acc:.2f}%")

    return model, best_val_acc


# Run for SQURPHARMA
if __name__ == '__main__':
    # Load prepared data
    X, y_returns, y_direction, scalers = ...  # From previous step

    # Train
    model, val_acc = train_diviner('SQURPHARMA', X, y_direction, DIVINER_CONFIG)
```

**Expected Training Time:** ~20-30 minutes on M4 Max

---

#### **Day 11-14: Hyperparameter Optimization**

**Objective:** Find best configuration through experimentation

**Grid Search (Top 3 Parameters):**
```python
HYPERPARAM_GRID = {
    'sequence_length': [30, 60, 90],
    'hidden_dim': [64, 128, 256],
    'num_encoder_layers': [2, 3, 4]
}

# Run 3x3x3 = 27 experiments
# Use validation accuracy to select best
```

**Recommendation:** Start with defaults, tune only if val_acc <50%

---

### **Week 3: Backtesting & Evaluation**

#### **Day 15-17: Walk-Forward Backtesting**

**Objective:** Realistic performance evaluation

**Implementation:**
```python
# scripts/backtest_diviner.py
from datetime import date, timedelta
import pandas as pd
import numpy as np

def walk_forward_backtest(
    stock_name,
    model,
    X_full,
    y_full,
    dates,
    initial_train_size=504,  # 2 years
    val_size=63,             # 3 months
    test_size=63,            # 3 months
    step_size=21,            # Monthly retraining
    device='mps'
):
    """
    Walk-forward validation with expanding window

    Returns:
        results: DataFrame with predictions, actuals, timestamps
    """
    results = []

    n = len(X_full)
    train_end = initial_train_size

    while train_end + val_size + test_size <= n:
        print(f"\nFold: Train[0:{train_end}], Val[{train_end}:{train_end+val_size}], Test[{train_end+val_size}:{train_end+val_size+test_size}]")

        # Split data
        X_train = X_full[:train_end]
        y_train = y_full[:train_end]

        X_val = X_full[train_end:train_end + val_size]
        y_val = y_full[train_end:train_end + val_size]

        X_test = X_full[train_end + val_size:train_end + val_size + test_size]
        y_test = y_full[train_end + val_size:train_end + val_size + test_size]
        test_dates = dates[train_end + val_size:train_end + val_size + test_size]

        # Retrain model (or use pretrained for speed)
        # For now, assume model is pretrained

        # Predict on test set
        model.eval()
        with torch.no_grad():
            # Create sequences
            test_dataset = StockForecastDataset(X_test, y_test, sequence_length=60)
            test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

            predictions = []
            actuals = []

            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(torch.device(device))
                outputs = model(batch_X)
                _, predicted = torch.max(outputs, 1)

                predictions.extend(predicted.cpu().numpy())
                actuals.extend(batch_y.cpu().numpy().flatten())

        # Store results
        for i, (pred, actual, dt) in enumerate(zip(predictions, actuals, test_dates)):
            results.append({
                'date': dt,
                'prediction': pred,
                'actual': actual,
                'fold': len(results) // len(predictions)
            })

        # Step forward
        train_end += step_size

    return pd.DataFrame(results)


# Run backtest
backtest_results = walk_forward_backtest('SQURPHARMA', model, X, y_direction, dates)

# Calculate metrics
correct = (backtest_results['prediction'] == backtest_results['actual']).sum()
total = len(backtest_results)
direction_accuracy = 100 * correct / total

print(f"\n📊 Backtest Results:")
print(f"Direction Accuracy: {direction_accuracy:.2f}%")
print(f"Total Predictions: {total}")
```

---

#### **Day 18-21: Performance Metrics & Visualization**

**Metrics to Calculate:**

1. **Direction Accuracy**: % of correct up/down predictions
2. **Precision/Recall**: For UP and DOWN classes
3. **Confusion Matrix**: See which directions are hardest
4. **Sharpe Ratio**: Risk-adjusted returns from trading signals
5. **Maximum Drawdown**: Worst peak-to-trough loss
6. **Win Rate**: % of profitable trades

**Visualization Script:**
```python
# scripts/visualize_results.py
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

def plot_backtest_results(results_df, stock_name):
    """Create comprehensive visualization of backtest results"""

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 1. Confusion Matrix
    cm = confusion_matrix(results_df['actual'], results_df['prediction'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0],
                xticklabels=['DOWN', 'NEUTRAL', 'UP'],
                yticklabels=['DOWN', 'NEUTRAL', 'UP'])
    axes[0, 0].set_title(f'{stock_name} - Confusion Matrix')
    axes[0, 0].set_ylabel('Actual')
    axes[0, 0].set_xlabel('Predicted')

    # 2. Accuracy over time
    results_df['correct'] = (results_df['prediction'] == results_df['actual']).astype(int)
    rolling_acc = results_df['correct'].rolling(window=20).mean() * 100
    axes[0, 1].plot(results_df['date'], rolling_acc)
    axes[0, 1].axhline(y=50, color='r', linestyle='--', label='Random (50%)')
    axes[0, 1].set_title('Rolling 20-Day Accuracy')
    axes[0, 1].set_ylabel('Accuracy (%)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Class distribution
    pred_dist = results_df['prediction'].value_counts()
    actual_dist = results_df['actual'].value_counts()
    x = np.arange(3)
    width = 0.35
    axes[1, 0].bar(x - width/2, actual_dist.values, width, label='Actual')
    axes[1, 0].bar(x + width/2, pred_dist.values, width, label='Predicted')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(['DOWN', 'NEUTRAL', 'UP'])
    axes[1, 0].set_title('Class Distribution')
    axes[1, 0].legend()

    # 4. Classification Report
    report = classification_report(results_df['actual'], results_df['prediction'],
                                    target_names=['DOWN', 'NEUTRAL', 'UP'],
                                    output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    axes[1, 1].axis('off')
    table = axes[1, 1].table(cellText=report_df.values,
                             colLabels=report_df.columns,
                             rowLabels=report_df.index,
                             cellLoc='center',
                             loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    axes[1, 1].set_title('Classification Report')

    plt.tight_layout()
    plt.savefig(f'results/{stock_name}_backtest.png', dpi=300)
    plt.show()

    return report


# Run visualization
report = plot_backtest_results(backtest_results, 'SQURPHARMA')
print(report)
```

---

### **Week 4: Scaling & Documentation**

#### **Day 22-24: Train on All Tier 1 Stocks**

**Objective:** Extend to all 5 stocks, compare performance

**Batch Training:**
```bash
for stock in SQURPHARMA BATBC BRACBANK HEIDELBCEM BEXIMCO; do
    python scripts/train_diviner.py --stock $stock --config config/diviner_config.py
    python scripts/backtest_diviner.py --stock $stock --checkpoint checkpoints/${stock}_best.pt
    python scripts/visualize_results.py --stock $stock
done
```

**Expected Output:**
- 5 trained models (checkpoints/*.pt)
- 5 backtest result files (results/*_backtest.csv)
- 5 visualization PDFs (results/*_backtest.png)

---

#### **Day 25-26: Feature Importance Analysis**

**Objective:** Understand which indicators matter most

**Method:** Attention weight analysis from Diviner

```python
# scripts/analyze_feature_importance.py
import torch
import numpy as np

def extract_attention_weights(model, X_sample, device='mps'):
    """Extract attention weights from trained Diviner model"""
    model.eval()

    # Forward pass with attention output
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X_sample).unsqueeze(0).to(device)

        # Assuming Diviner exposes attention weights
        # (Check actual implementation)
        outputs, attention_weights = model(X_tensor, return_attention=True)

    # Average attention across heads and layers
    avg_attention = attention_weights.mean(dim=(0, 1)).cpu().numpy()

    return avg_attention


def rank_features_by_importance(model, X_val, feature_names, device='mps'):
    """Rank features by average attention weight"""

    # Sample multiple sequences
    sample_size = min(100, len(X_val))
    importances = []

    for i in np.random.choice(len(X_val), sample_size, replace=False):
        att_weights = extract_attention_weights(model, X_val[i], device)
        importances.append(att_weights)

    # Average across samples
    avg_importance = np.mean(importances, axis=0)

    # Create ranking
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': avg_importance
    }).sort_values('importance', ascending=False)

    return feature_importance


# Analyze
importance = rank_features_by_importance(model, X_val, DIVINER_FEATURES)
print(importance)

# Visualize
plt.figure(figsize=(10, 6))
plt.barh(importance['feature'], importance['importance'])
plt.xlabel('Average Attention Weight')
plt.title('Feature Importance (Diviner Attention Analysis)')
plt.tight_layout()
plt.savefig('results/feature_importance.png', dpi=300)
```

**Key Question:** Are new indicators (log_return, volume_ratio, temporal) getting high attention?

---

#### **Day 27-28: Documentation & Report**

**Final Deliverables:**

1. **Performance Report** (`DIVINER_PHASE1_RESULTS.md`)
   - Summary table of all 5 stocks
   - Direction accuracy, Sharpe ratio, max drawdown
   - Comparison to buy-and-hold baseline

2. **Model Cards** (`models/STOCK_model_card.md`)
   - Training data size and date range
   - Hyperparameters used
   - Performance metrics
   - Known limitations

3. **Deployment Guide** (`DIVINER_DEPLOYMENT.md`)
   - How to load models for inference
   - API integration points
   - Monitoring recommendations

---

## Success Criteria Checklist

After Week 4, evaluate against these criteria:

### **Minimum Viable Performance**
- [ ] Direction accuracy >55% on at least 3/5 stocks
- [ ] Sharpe ratio >0.8 on at least 2/5 stocks
- [ ] No catastrophic failures (accuracy <45%)
- [ ] Training completes in <2 hours per stock

### **Technical Validation**
- [ ] Walk-forward backtest implemented correctly
- [ ] No data leakage (future info not in training)
- [ ] Models saved and can be loaded for inference
- [ ] Feature normalization is reversible

### **Documentation**
- [ ] Results documented with charts
- [ ] Feature importance analyzed
- [ ] Known issues and limitations listed
- [ ] Next steps identified

---

## Risk Mitigation

### **Risk 1: Poor Initial Performance (<50% accuracy)**

**Likely Causes:**
- Insufficient data (need more history)
- Feature scaling issues
- Model architecture mismatch
- Class imbalance (too few UP/DOWN samples)

**Mitigation:**
1. Try different threshold for UP/DOWN (±1% instead of ±2%)
2. Use focal loss instead of cross-entropy
3. Add more historical data if available
4. Simplify model (fewer layers)

---

### **Risk 2: Overfitting (Train 90%, Val 50%)**

**Likely Causes:**
- Model too complex for data size
- No regularization
- Data leakage

**Mitigation:**
1. Increase dropout to 0.3-0.4
2. Add L2 regularization (weight_decay)
3. Reduce model capacity (hidden_dim 64 instead of 128)
4. Use more data augmentation

---

### **Risk 3: Training Too Slow (>4 hours per stock)**

**Likely Causes:**
- MPS not enabled
- Batch size too small
- Too many epochs

**Mitigation:**
1. Verify `device='mps'` in config
2. Increase batch size to 128
3. Reduce num_epochs to 50
4. Use early stopping aggressively

---

## Next Steps After Phase 1

Based on Phase 1 results, choose next phase:

### **If Performance is Good (>60% accuracy):**
→ **Phase 2: Hybrid Integration**
- Combine Diviner forecasts with rule-based signals
- Build ensemble (60% Diviner + 40% technical)
- Deploy to paper trading

### **If Performance is Moderate (55-60% accuracy):**
→ **Phase 2: Feature Engineering**
- Add market/sector context features
- Experiment with different feature sets
- Try transfer learning from US markets

### **If Performance is Poor (<55% accuracy):**
→ **Phase 2: Model Alternatives**
- Try simpler models (LSTM, GRU)
- Benchmark against naive baselines
- Re-evaluate if deep learning is right approach

---

## Quick Start Checklist

To get started immediately:

```bash
# 1. Clone Diviner
cd ~/Workspace
git clone https://github.com/CapricornGuang/Diviner-Nonstationary-time-series-forecasting.git

# 2. Setup environment
cd Diviner-Nonstationary-time-series-forecasting
python3 -m venv venv-diviner
source venv-diviner/bin/activate
pip install torch torchvision torchaudio numpy pandas scikit-learn matplotlib tqdm

# 3. Verify MPS
python -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"

# 4. Prepare data
cd ~/Workspace/wizardsofts-megabuild/apps/gibd-quant-agent
git checkout feature/diviner-indicators
python scripts/prepare_diviner_data.py  # Create this from template above

# 5. Train first model
python scripts/train_diviner.py --stock SQURPHARMA
```

**Expected Time to First Model:** ~1 day setup + ~30 min training = **Day 1 completion possible!**

---

**Questions or Issues?** Document in `DIVINER_PHASE1_ISSUES.md` for tracking.

**Good luck! 🚀**

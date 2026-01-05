#!/usr/bin/env python3
"""
Example: Installing task-specific dependencies at runtime

This demonstrates Ray's runtime_env feature which allows workers
to install dependencies on-demand rather than pre-baking them into Docker images.
"""

import ray

# Connect to Ray cluster
ray.init(address="ray://10.0.0.84:10001")

@ray.remote(runtime_env={"pip": ["scikit-learn==1.4.0", "xgboost==2.0.3"]})
def train_ml_model(data_size: int):
    """
    This function will automatically install scikit-learn and xgboost
    on the worker before execution. Dependencies are cached per worker.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    import xgboost as xgb

    # Generate synthetic data
    X, y = make_classification(n_samples=data_size, n_features=20, random_state=42)

    # Train RandomForest
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)
    rf_score = rf.score(X, y)

    # Train XGBoost
    xgb_model = xgb.XGBClassifier(n_estimators=10, random_state=42)
    xgb_model.fit(X, y)
    xgb_score = xgb_model.score(X, y)

    return {
        "data_size": data_size,
        "random_forest_accuracy": rf_score,
        "xgboost_accuracy": xgb_score,
        "node": ray.get_runtime_context().get_node_id()[:8]
    }


@ray.remote(runtime_env={"pip": ["torch==2.1.2"]})
def train_pytorch_model(epochs: int):
    """
    This function will install PyTorch only on workers that run it.
    Other workers don't need to download the 670MB PyTorch package.
    """
    import torch
    import torch.nn as nn

    # Simple neural network
    model = nn.Sequential(
        nn.Linear(10, 50),
        nn.ReLU(),
        nn.Linear(50, 1)
    )

    # Dummy training
    optimizer = torch.optim.Adam(model.parameters())
    for _ in range(epochs):
        x = torch.randn(32, 10)
        y = torch.randn(32, 1)
        loss = nn.MSELoss()(model(x), y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return {
        "epochs": epochs,
        "final_loss": loss.item(),
        "node": ray.get_runtime_context().get_node_id()[:8]
    }


if __name__ == "__main__":
    print("🚀 Running tasks with runtime dependency installation...\n")

    # Run ML tasks - dependencies installed only where needed
    print("📊 Training ML models (scikit-learn, XGBoost)...")
    ml_futures = [train_ml_model.remote(1000) for _ in range(3)]
    ml_results = ray.get(ml_futures)

    for result in ml_results:
        print(f"  Node {result['node']}: RF={result['random_forest_accuracy']:.3f}, "
              f"XGB={result['xgboost_accuracy']:.3f}")

    # Run PyTorch tasks - PyTorch installed only where needed
    print("\n🔥 Training PyTorch models...")
    torch_futures = [train_pytorch_model.remote(10) for _ in range(2)]
    torch_results = ray.get(torch_futures)

    for result in torch_results:
        print(f"  Node {result['node']}: {result['epochs']} epochs, "
              f"loss={result['final_loss']:.4f}")

    print("\n✅ Runtime dependency installation complete!")
    print("\n💡 Benefits:")
    print("  - Workers start in <1 minute (not 10+ minutes)")
    print("  - Each task installs only what it needs")
    print("  - Dependencies cached per worker")
    print("  - Docker images stay lightweight (~200MB vs 2GB)")

    ray.shutdown()

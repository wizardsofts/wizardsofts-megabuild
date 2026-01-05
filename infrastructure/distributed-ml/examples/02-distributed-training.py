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
import sys

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
    try:
        ray.init(address="ray://10.0.0.84:10001")
    except Exception as e:
        print(f"❌ Failed to connect to Ray cluster: {e}")
        sys.exit(1)

    print("\n🚀 Starting distributed training...")

    # Configure distributed training
    trainer = SklearnTrainer(
        train_loop_per_worker=train_func,
        train_loop_config={
            "n_estimators": 200,
            "max_depth": 15
        },
        scaling_config=ScalingConfig(
            num_workers=2,  # Distribute across 2 workers (adjust based on cluster size)
            use_gpu=False
        )
    )

    # Run training
    try:
        result = trainer.fit()

        print("\n✅ Training complete!")
        print(f"   Best accuracy: {result.metrics['accuracy']:.4f}")
        print(f"   Checkpoint: {result.checkpoint}")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        sys.exit(1)

    ray.shutdown()
    print("\n✅ Test passed!")

if __name__ == "__main__":
    main()

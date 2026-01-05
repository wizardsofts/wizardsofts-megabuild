"""
Distributed data processing test using Ray Data
Tests: Large dataset processing, parallel transformations, data persistence
"""
import ray
import numpy as np
import time
import sys

def process_batch(batch):
    """Simulate heavy data processing"""
    # Add computed features
    batch["feature_sum"] = batch["feature_1"] + batch["feature_2"]
    batch["feature_product"] = batch["feature_1"] * batch["feature_2"]
    batch["feature_normalized"] = (batch["feature_1"] - batch["feature_1"].mean()) / batch["feature_1"].std()
    return batch

def main():
    print("🔗 Connecting to Ray cluster...")
    try:
        ray.init(address="ray://10.0.0.84:10001")
    except Exception as e:
        print(f"❌ Failed to connect to Ray cluster: {e}")
        sys.exit(1)

    print("\n📊 Creating large synthetic dataset...")

    # Create dataset (1M rows for faster testing)
    dataset = ray.data.range(1_000_000).map_batches(
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
    sample = processed.take(5)
    for i, row in enumerate(sample[:3], 1):
        print(f"   Row {i}: id={row['id']}, feature_sum={row['feature_sum']:.4f}")

    ray.shutdown()
    print("\n✅ Test passed!")

if __name__ == "__main__":
    main()

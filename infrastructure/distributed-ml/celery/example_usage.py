"""
Example usage of Celery + Ray distributed tasks

This script demonstrates how to submit tasks to the Celery queue
which then orchestrates work on the Ray cluster.
"""
from celery import Celery
import time
import os

# Get credentials from environment or use defaults
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'your-redis-password')
SERVER_IP = '10.0.0.84'

# Initialize Celery app
app = Celery(
    'example',
    broker=f'redis://:{REDIS_PASSWORD}@{SERVER_IP}:6380/0',
    backend=f'redis://:{REDIS_PASSWORD}@{SERVER_IP}:6380/1'
)

def example_1_simple_ping():
    """Example 1: Simple ping test"""
    print("\n=== Example 1: Simple Ping Test ===")

    result = app.send_task('tasks.simple_tasks.ping')

    print(f"Task ID: {result.id}")
    print(f"Task State: {result.state}")

    # Wait for result
    output = result.get(timeout=10)
    print(f"Result: {output}")


def example_2_distributed_training():
    """Example 2: Distributed ML training on Ray cluster"""
    print("\n=== Example 2: Distributed Training ===")

    # Configure model and dataset
    model_config = {
        'n_estimators': 100,
        'max_depth': 20,
        'num_partitions': 4  # Split across 4 Ray workers
    }

    result = app.send_task(
        'tasks.ml_tasks.distributed_training',
        kwargs={
            'model_config': model_config,
            'dataset_path': '/datasets/training_data'
        },
        queue='ml'  # Route to ML queue
    )

    print(f"Task ID: {result.id}")
    print(f"Waiting for training to complete...")

    # Wait for result (may take several minutes)
    try:
        output = result.get(timeout=600)  # 10 minutes
        print(f"\n✅ Training Complete!")
        print(f"  - Average Score: {output['avg_score']:.4f}")
        print(f"  - Total Samples: {output['total_samples']}")
        print(f"  - Partitions: {output['num_partitions']}")
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")


def example_3_hyperparameter_search():
    """Example 3: Hyperparameter search with Ray parallelization"""
    print("\n=== Example 3: Hyperparameter Search ===")

    # Define parameter grid
    param_grid = [
        {'n_estimators': n, 'max_depth': d}
        for n in [50, 100, 200]
        for d in [10, 20, 30]
    ]  # 9 combinations

    print(f"Testing {len(param_grid)} parameter combinations...")

    result = app.send_task(
        'tasks.ml_tasks.hyperparameter_search',
        kwargs={
            'param_grid': param_grid,
            'dataset_path': '/datasets/validation_data.csv'
        },
        queue='ml'
    )

    print(f"Task ID: {result.id}")

    # Wait for results
    try:
        output = result.get(timeout=900)  # 15 minutes
        print(f"\n✅ Search Complete!")
        print(f"  - Best Parameters: {output['best_params']}")
        print(f"  - Best Score: {output['best_score']:.4f}")
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")


def example_4_data_processing():
    """Example 4: Process large CSV file"""
    print("\n=== Example 4: Large CSV Processing ===")

    result = app.send_task(
        'tasks.data_tasks.process_large_csv',
        kwargs={
            'file_path': '/datasets/large_file.csv',
            'output_path': '/datasets/processed_file.csv',
            'transformations': {
                'filter': {'amount': 100},  # Filter rows where amount > 100
                'num_chunks': 10  # Split into 10 chunks for parallel processing
            }
        },
        queue='data'
    )

    print(f"Task ID: {result.id}")

    try:
        output = result.get(timeout=300)  # 5 minutes
        print(f"\n✅ Processing Complete!")
        print(f"  - Total Rows: {output['total_rows_processed']}")
        print(f"  - Chunks: {output['num_chunks']}")
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")


def example_5_batch_predictions():
    """Example 5: Batch predictions using trained model"""
    print("\n=== Example 5: Batch Predictions ===")

    result = app.send_task(
        'tasks.ml_tasks.batch_predictions',
        kwargs={
            'model_path': '/models/trained_model.pkl',
            'data_batches': [
                '/datasets/batch_1.csv',
                '/datasets/batch_2.csv',
                '/datasets/batch_3.csv'
            ]
        },
        queue='ml'
    )

    print(f"Task ID: {result.id}")

    try:
        output = result.get(timeout=300)
        print(f"\n✅ Predictions Complete!")
        print(f"  - Total Predictions: {output['total_predictions']}")
        print(f"  - Sample Predictions: {output['predictions'][:5]}")
    except Exception as e:
        print(f"❌ Predictions failed: {str(e)}")


def example_6_check_cluster():
    """Example 6: Check Ray cluster health"""
    print("\n=== Example 6: Cluster Health Check ===")

    result = app.send_task('tasks.simple_tasks.check_cluster_health')

    try:
        output = result.get(timeout=30)
        print(f"\n✅ Cluster Status: {output['status']}")
        if 'cluster_data' in output:
            print(f"  - Data: {output['cluster_data']}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")


def example_7_async_multiple():
    """Example 7: Submit multiple tasks asynchronously"""
    print("\n=== Example 7: Multiple Async Tasks ===")

    # Submit 5 tasks without waiting
    tasks = []
    for i in range(5):
        result = app.send_task(
            'tasks.simple_tasks.ping',
            queue='default'
        )
        tasks.append(result)
        print(f"Submitted task {i+1}: {result.id}")

    # Wait for all to complete
    print("\nWaiting for all tasks to complete...")
    for i, task in enumerate(tasks):
        output = task.get(timeout=30)
        print(f"Task {i+1} result: {output}")


if __name__ == '__main__':
    print("=" * 60)
    print("Celery + Ray Integration Examples")
    print("=" * 60)

    # Run examples
    example_1_simple_ping()

    # Uncomment to run other examples:
    # example_2_distributed_training()
    # example_3_hyperparameter_search()
    # example_4_data_processing()
    # example_5_batch_predictions()
    # example_6_check_cluster()
    # example_7_async_multiple()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)

"""
ML tasks that orchestrate Ray cluster jobs
These tasks run on Celery workers but submit work to the Ray cluster
"""
from tasks import app
import ray
import logging
from typing import Dict, List, Any
import time

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3)
def distributed_training(self, model_config: Dict[str, Any], dataset_path: str):
    """
    Distributed ML training using Ray cluster

    Args:
        model_config: Model hyperparameters and configuration
        dataset_path: Path to training dataset

    Returns:
        Dict with training results and metrics
    """
    try:
        logger.info(f"Starting distributed training with config: {model_config}")

        # Connect to Ray cluster
        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        # Define remote training function
        @ray.remote
        def train_model_partition(config, data_partition):
            """Train model on a data partition"""
            from sklearn.ensemble import RandomForestClassifier
            import pandas as pd

            # Load data partition
            df = pd.read_csv(data_partition)
            X = df.drop('target', axis=1)
            y = df['target']

            # Train model
            model = RandomForestClassifier(**config)
            model.fit(X, y)

            # Return metrics
            score = model.score(X, y)
            return {
                'score': score,
                'n_samples': len(df),
                'config': config
            }

        # Submit training tasks to Ray cluster
        num_partitions = model_config.get('num_partitions', 4)
        partitions = [f"{dataset_path}_part_{i}.csv" for i in range(num_partitions)]

        futures = [
            train_model_partition.remote(model_config, partition)
            for partition in partitions
        ]

        # Wait for results
        results = ray.get(futures)

        # Aggregate results
        avg_score = sum(r['score'] for r in results) / len(results)
        total_samples = sum(r['n_samples'] for r in results)

        logger.info(f"Training complete. Avg score: {avg_score:.4f}, Total samples: {total_samples}")

        # Cleanup
        ray.shutdown()

        return {
            'status': 'success',
            'avg_score': avg_score,
            'total_samples': total_samples,
            'num_partitions': num_partitions,
            'results': results
        }

    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@app.task(bind=True, max_retries=3)
def hyperparameter_search(self, param_grid: List[Dict], dataset_path: str):
    """
    Distributed hyperparameter search using Ray cluster

    Args:
        param_grid: List of parameter combinations to try
        dataset_path: Path to training/validation dataset

    Returns:
        Dict with best parameters and scores
    """
    try:
        logger.info(f"Starting hyperparameter search with {len(param_grid)} combinations")

        # Connect to Ray cluster
        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        @ray.remote
        def train_and_evaluate(params, data_path):
            """Train with specific params and return score"""
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            import pandas as pd

            # Load data
            df = pd.read_csv(data_path)
            X = df.drop('target', axis=1)
            y = df['target']

            # Split
            X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train
            model = RandomForestClassifier(**params)
            model.fit(X_train, y_train)

            # Evaluate
            score = model.score(X_val, y_val)

            return {'params': params, 'score': score}

        # Distribute across Ray cluster
        futures = [train_and_evaluate.remote(params, dataset_path) for params in param_grid]

        # Get results
        results = ray.get(futures)

        # Find best
        best = max(results, key=lambda x: x['score'])

        logger.info(f"Hyperparameter search complete. Best score: {best['score']:.4f}")

        # Cleanup
        ray.shutdown()

        return {
            'status': 'success',
            'best_params': best['params'],
            'best_score': best['score'],
            'all_results': results
        }

    except Exception as e:
        logger.error(f"Hyperparameter search failed: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@app.task
def retrain_models():
    """
    Scheduled task: Retrain all models daily
    This is triggered by Celery Beat scheduler
    """
    logger.info("Starting scheduled model retraining")

    # Example: Trigger retraining for multiple models
    models_to_retrain = [
        {'name': 'stock_predictor', 'dataset': '/datasets/stocks_latest.csv'},
        {'name': 'sentiment_analyzer', 'dataset': '/datasets/sentiment_latest.csv'}
    ]

    results = []
    for model_info in models_to_retrain:
        # Trigger distributed training
        result = distributed_training.delay(
            model_config={'n_estimators': 100, 'max_depth': 20},
            dataset_path=model_info['dataset']
        )
        results.append({
            'model': model_info['name'],
            'task_id': result.id
        })

    logger.info(f"Triggered retraining for {len(models_to_retrain)} models")
    return {'status': 'scheduled', 'models': results}


@app.task(bind=True)
def batch_predictions(self, model_path: str, data_batches: List[str]):
    """
    Distributed batch predictions using Ray cluster

    Args:
        model_path: Path to trained model
        data_batches: List of paths to data batches

    Returns:
        Aggregated predictions
    """
    try:
        logger.info(f"Starting batch predictions on {len(data_batches)} batches")

        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        @ray.remote
        def predict_batch(model_file, batch_file):
            """Load model and predict on batch"""
            import pickle
            import pandas as pd

            # Load model
            with open(model_file, 'rb') as f:
                model = pickle.load(f)

            # Load data
            df = pd.read_csv(batch_file)

            # Predict
            predictions = model.predict(df)

            return predictions.tolist()

        # Distribute predictions
        futures = [predict_batch.remote(model_path, batch) for batch in data_batches]

        # Collect results
        all_predictions = []
        for predictions in ray.get(futures):
            all_predictions.extend(predictions)

        logger.info(f"Batch predictions complete. Total predictions: {len(all_predictions)}")

        ray.shutdown()

        return {
            'status': 'success',
            'total_predictions': len(all_predictions),
            'predictions': all_predictions[:100]  # Return first 100 as sample
        }

    except Exception as e:
        logger.error(f"Batch predictions failed: {str(e)}")
        raise

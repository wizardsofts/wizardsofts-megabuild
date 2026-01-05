"""
Data processing tasks using Ray cluster
"""
from tasks import app
import ray
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3)
def process_large_csv(self, file_path: str, output_path: str, transformations: Dict[str, Any]):
    """
    Process large CSV file in parallel using Ray cluster

    Args:
        file_path: Input CSV file path
        output_path: Output processed file path
        transformations: Dict of transformations to apply

    Returns:
        Processing results and statistics
    """
    try:
        logger.info(f"Processing CSV: {file_path}")

        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        @ray.remote
        def process_chunk(chunk_start, chunk_size, file, transforms):
            """Process a chunk of CSV file"""
            import pandas as pd

            # Read chunk
            df = pd.read_csv(file, skiprows=chunk_start, nrows=chunk_size)

            # Apply transformations
            if 'filter' in transforms:
                for col, condition in transforms['filter'].items():
                    df = df[df[col] > condition]

            if 'new_columns' in transforms:
                for col_name, formula in transforms['new_columns'].items():
                    # Simple formula evaluation
                    df[col_name] = eval(formula, {'df': df})

            return len(df), df.head().to_dict()

        # Split into chunks (100k rows per chunk)
        chunk_size = 100_000
        num_chunks = transformations.get('num_chunks', 10)

        # Process chunks in parallel
        futures = [
            process_chunk.remote(i * chunk_size, chunk_size, file_path, transformations)
            for i in range(num_chunks)
        ]

        # Get results
        results = ray.get(futures)
        total_rows = sum(count for count, _ in results)

        logger.info(f"CSV processing complete. Processed {total_rows} rows")

        ray.shutdown()

        return {
            'status': 'success',
            'input_file': file_path,
            'output_file': output_path,
            'total_rows_processed': total_rows,
            'num_chunks': num_chunks
        }

    except Exception as e:
        logger.error(f"CSV processing failed: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@app.task
def process_new_data():
    """
    Scheduled task: Process new data every hour
    Triggered by Celery Beat
    """
    logger.info("Starting hourly data processing")

    # Example: Process any new data files
    import os
    data_dir = os.getenv('NEW_DATA_DIR', '/datasets/new/')

    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

        results = []
        for file in files:
            file_path = os.path.join(data_dir, file)
            output_path = os.path.join('/datasets/processed/', file)

            # Trigger processing
            result = process_large_csv.delay(
                file_path=file_path,
                output_path=output_path,
                transformations={'filter': {'amount': 100}, 'num_chunks': 5}
            )

            results.append({
                'file': file,
                'task_id': result.id
            })

        logger.info(f"Triggered processing for {len(files)} files")
        return {'status': 'scheduled', 'files': results}
    else:
        logger.info("No new data to process")
        return {'status': 'no_data'}


@app.task(bind=True)
def aggregate_data(self, data_sources: List[str], output_path: str):
    """
    Aggregate data from multiple sources using Ray

    Args:
        data_sources: List of data source paths
        output_path: Output aggregated file path

    Returns:
        Aggregation results
    """
    try:
        logger.info(f"Aggregating {len(data_sources)} data sources")

        ray.init(address="ray://10.0.0.84:10001", ignore_reinit_error=True)

        @ray.remote
        def load_and_summarize(source):
            """Load data source and compute summary statistics"""
            import pandas as pd

            df = pd.read_csv(source)
            return {
                'source': source,
                'rows': len(df),
                'columns': list(df.columns),
                'summary': df.describe().to_dict()
            }

        # Load and summarize in parallel
        futures = [load_and_summarize.remote(source) for source in data_sources]
        summaries = ray.get(futures)

        total_rows = sum(s['rows'] for s in summaries)

        logger.info(f"Data aggregation complete. Total rows: {total_rows}")

        ray.shutdown()

        return {
            'status': 'success',
            'total_rows': total_rows,
            'num_sources': len(data_sources),
            'summaries': summaries
        }

    except Exception as e:
        logger.error(f"Data aggregation failed: {str(e)}")
        raise

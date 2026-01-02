import logging
import time

from utils import read_config
import os
import pandas as pd
import requests
from datetime import datetime


def save_to_db(file):
    """Save CSV data to the database."""
    try:
        if file.endswith('.csv'):
            df = pd.read_csv(f'{folder_name}/{file}', parse_dates=['Date'])
            payload = []
            for _, row in df.iterrows():
                payload.append({
                    "date": row["Date"].strftime('%Y-%m-%d'),
                    "scrip": row["Scrip"],
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })

            # print(json.dumps(payload, indent=4))
            response = requests.post('http://10.0.0.80:8080/GIBD-TRADES/api/v1/dse-daily-prices', json=payload)
            response.raise_for_status()
            # print(response.json())
        else:
            logging.info(f'Invalid file {file}')
    except Exception as e:
        logging.error(f'Error for {file} - {str(e)}')
        raise



config, base_url, output_dir, log_dir = read_config('DEFAULT')
log_file_name = f"{log_dir}/load_dse_daily_stock_data_{datetime.now().strftime('%Y-%m-%d')}.log"
log_file = os.path.join(log_dir, log_file_name)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")
folder_name = f'{output_dir}/amrastock'
csv_files = [f for f in os.listdir(folder_name) if f.endswith('.csv')]

for file in csv_files:
    # check if file name exists in the log_file and skip
    if file in open(log_file_name).read():
        logging.info('File already exists in the database')
        continue

    try:
        save_to_db(file)
        logging.info(f'File {file} saved to the database')
        time.sleep(1)
    except Exception as e:
        logging.error(f'Error for {file} - {str(e)}')


logging.info('All files saved to the database')

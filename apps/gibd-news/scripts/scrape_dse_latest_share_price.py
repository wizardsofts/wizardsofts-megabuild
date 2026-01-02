import os
import csv
import time
import pytz
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from utils import read_config, webdriver_session
import warnings

warnings.filterwarnings("ignore")

# Setup configuration and logging
config, base_url, output_dir, log_dir = read_config('LATEST_SHARE_PRICE_SCROLL')


def save_data(data):
    formatted_data = [
        {
            "timestamp": datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').isoformat(),
            "tradingCode": row[2],
            "ltp": float(row[3].replace(",", "")) if row[3] != '--' else None,
            "high": float(row[4].replace(",", "")) if row[4] != '--' else None,
            "low": float(row[5].replace(",", "")) if row[5] != '--' else None,
            "closep": float(row[6].replace(",", "")) if row[6] != '--' else None,
            "ycp": float(row[7].replace(",", "")) if row[7] != '--' else None,
            "priceChange": float(row[8].replace(",", "")) if row[8] != '--' else None,
            "trade": int(row[9].replace(",", "")) if row[9] != '--' else None,
            "valueMn": float(row[10].replace(",", "")) if row[10] != '--' else None,
            "volume": int(row[11].replace(",", "")) if row[11] != '--' else None
        }
        for row in data
    ]
    response = requests.post(config.get('LATEST_SHARE_PRICE_SCROLL', 'latest_trades_url'), json=formatted_data)
    response.raise_for_status()


def log_error(error: Exception, context: str = "") -> None:
    """Safely log errors with timestamp."""
    try:
        error_time = datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%Y-%m-%d_%H%M%S")
        log_file_path = f"{log_dir}/error_log_{error_time}.log"
        with open(log_file_path, "a") as log_file:
            log_file.write(f"{datetime.now(pytz.timezone('Asia/Dhaka'))}: {context} - {error}\n")
    except Exception as log_error:
        print(f"Failed to write error log: {log_error}. Original error: {error}")


def run_scraper():
    """Main scraper function with proper resource management."""
    # URL of the DSE table
    url = config.get('LATEST_SHARE_PRICE_SCROLL', 'base_url')

    # Column headers for the CSV, adding "Timestamp" as the first column
    headers = ["Timestamp", "#", "TRADING CODE", "LTP", "HIGH", "LOW", "CLOSEP", "YCP", "CHANGE", "TRADE", "VALUE (mn)", "VOLUME"]

    # Use context manager for safe WebDriver lifecycle
    with webdriver_session() as driver:
        # Generate today's date in "YYYY-MM-DD" format
        today_date = datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%Y-%m-%d")

        # Create a daily CSV file name
        os.makedirs(f"{output_dir}/dse_stock_price", exist_ok=True)
        csv_file = f"{output_dir}/dse_stock_price/dse_stock_data_{today_date}.csv"
        step_start = time.time()
        # Open the URL
        driver.get(url)
        step_end = time.time()
        print(f"Step 'Open URL' took {step_end - step_start:.2f} seconds")

        step_start = time.time()
        # Wait for the table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "#RightBody > div.row > div.col-md-9.col-sm-9.col-xs-9.full-width-mobile > div.floatThead-wrapper > div.table-responsive.inner-scroll > table"))
        )
        step_end = time.time()
        print(f"Step 'Wait for table to load' took {step_end - step_start:.2f} seconds")

        step_start = time.time()
        # Locate the table element
        table = driver.find_element(By.CSS_SELECTOR,
                                    "#RightBody > div.row > div.col-md-9.col-sm-9.col-xs-9.full-width-mobile > div.floatThead-wrapper > div.table-responsive.inner-scroll > table")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        step_end = time.time()
        print(f"Step 'Locate table element' took {step_end - step_start:.2f} seconds")

        step_start = time.time()
        # Prepare data for CSV with timestamp
        data = []
        current_time = datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%Y-%m-%d %H:%M:%S")  # Add current timestamp
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) == len(headers) - 1:  # Ensure row has expected number of columns
                row_data = [current_time] + [col.text.strip() for col in cols]  # Add timestamp as the first value
                data.append(row_data)
        step_end = time.time()
        print(f"Step 'Prepare data for CSV' took {step_end - step_start:.2f} seconds")

        step_start = time.time()
        # Write to CSV
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(headers)  # Write headers if file is new
            for row_data in data:
                writer.writerow(row_data)  # Append each row of data
        step_end = time.time()
        print(f"Step 'Write to CSV' took {step_end - step_start:.2f} seconds")

        # Insert data into the database
        save_data(data)
        print(f"Data successfully written to {csv_file} and inserted into the database at {current_time}")


if __name__ == "__main__":
    try:
        run_scraper()
    except Exception as e:
        print(f"Error encountered: {e}")
        log_error(e, "scrape_dse_latest_share_price")
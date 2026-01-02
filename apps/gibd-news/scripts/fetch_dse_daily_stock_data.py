import logging
import os
import time
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils import read_config
from config_loader import get_email_config

def download_csv(output_dir, start_date, end_date):
    """Download CSV files from the specified URL for the given date range."""
    url = 'https://www.amarstock.com/data/download/CSV'
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    }
    os.makedirs(f"{output_dir}/dse_stock_price", exist_ok=True)
    new_files = []
    for date in pd.date_range(start=start_date, end=end_date):
        if date.weekday() in [4, 5]:
            continue
        data = {'QuotesType': '1', 'date': date.strftime('%Y-%m-%d')}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            file_path = f'{output_dir}/dse_stock_price/data_{data["date"]}.csv'
            with open(file_path, 'wb') as f:
                f.write(response.content)
            new_files.append(file_path)
            logging.info(f'File downloaded for {data["date"]}')
        else:
            logging.info(f'Failed to download file for {data["date"]}')
        time.sleep(10)
    return new_files

def save_data(file, post_url):
    """Save CSV data to the database."""
    try:
        if file.endswith('.csv'):
            df = pd.read_csv(file, parse_dates=['Date'])
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

            # Print the JSON payload
            response = requests.post(post_url, json=payload)
            response.raise_for_status()
            logging.info(f'File {file} saved to the database {response.status_code}')
        else:
            logging.info(f'Invalid file {file}')
    except Exception as e:
        logging.error(f'Error for {file} - {str(e)}')
        notify_admin(f'Error for {file} - {str(e)}')
        raise

def notify_admin(message):
    """Notify admin in case of an error."""
    send_email(message, 'Error')

def send_email(message, status):
    """Send an email notification using centralized config."""
    try:
        email_config = get_email_config()
        sender_email = email_config.get('sender_email')
        password = email_config.get('sender_password')
        receiver_email = email_config.get('admin_email')

        if not sender_email or not password:
            raise ValueError("Email configuration incomplete. Set GIBD_EMAIL_SENDER and GIBD_EMAIL_PASSWORD.")
        if not receiver_email:
            raise ValueError("Admin email not configured. Set GIBD_EMAIL_ADMIN or GIBD_EMAIL_RECIPIENTS.")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f'Stock Data Download {status}'

        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        logging.error(f'Failed to send email: {str(e)}')

def run_task():
    """Main function to run the task."""
    try:

        config, base_url, output_dir, log_dir = read_config('DEFAULT')
        logging.basicConfig(filename=f'{log_dir}/dse_stock_data.log', level=logging.INFO)
        data = requests.get(config.get('DEFAULT', 'latest_price_date'))
        max_date = data.json()['data'] if data.status_code == 200 else None
        if max_date is None:
            max_date = '2024-11-07'
        start_date = pd.to_datetime(max_date) + pd.DateOffset(days=1)
        end_date = pd.to_datetime('today')
        post_url = config.get('DEFAULT', 'dse_daily_prices')
        new_files = download_csv(output_dir, start_date, end_date)
        for file in new_files:
            save_data(file, post_url)

        message = f'Task completed successfully. Downloaded files for dates: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'
        notify_admin(message)
    except Exception as e:
        logging.info(f'Task failed: {str(e)}')
        error_message = f'Task failed: {str(e)}'
        notify_admin(error_message)

if __name__ == "__main__":
    run_task()
    logging.info('Done')
import logging
import requests
from utils import read_config
from datetime import datetime
import os

def send_news(news_details):
    """
    Sends a news entry to the API.
    """
    # Get the API URL from the configuration
    config, _, _, log_dir = read_config()
    log_file = os.path.join(log_dir, f"send_news_{datetime.now().strftime('%Y-%m-%d')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")
    api_url = config.get("DEFAULT", "api_url_news_post")

    try:
        # Log the news details being sent
        logging.info(f"Sending news details: {news_details}")

        # Make POST request to the API
        response = requests.post(api_url, json=news_details)
        response.raise_for_status()
        logging.info(f"News sent successfully: {news_details['url']}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        logging.error(f"Error sending news: {e}")

# Example usage
if __name__ == "__main__":
    # Example news article data
    news_example = {
        "url": "https://test3",
        "title": "Dhaka stocks decline in early trade",
        "subtitle": "DSEX loses 16.74 points as of 11:28 am",
        "date": "2025-01-02T11:54:00",
        "content": "Stocks start today's trading on a declining note, snapping four consecutive days of gains. The DSEX, the premier index of the Dhaka Stock Exchange, lost 16.74 points or 0.32 percent to 5,201.41 as of 11:28 am. Some 84 issues advanced, 194 declined, and 88 remained unchanged. Total turnover stood at Tk 106.90 crore. Rupali Bank and Western Marine Shipyard led the gains, rising over 9 percent each, while shares of Usmania Glass Sheet Factory dropped 7 percent. CSE All Share Price Index was up 0.01 percent, gaining 2.02 points to 14,514.08.",
        "tags": "test_post",
        "sentimentScore": 0.13333334
    }
    send_news(news_example)
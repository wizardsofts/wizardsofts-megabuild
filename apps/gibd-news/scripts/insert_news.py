
# Load embedding model
# model = SentenceTransformer('all-MiniLM-L6-v2')

import logging
from utils import read_config
from datetime import datetime
import os

# Load configuration
config, base_url, output_dir, log_dir, connection = read_config("FINANCIALEXPRESS", include_db_connection=True, db_section="POSTGRES_WS_GIBD_NEWS")
log_file = os.path.join(log_dir, f"insert_news {datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")
def insert_news(news_details):
    """
    Inserts or updates a news entry in the database.
    """
    query = """
    INSERT INTO news (url, title, subtitle, date, content, tags, embedding, sentiment_score, scraped_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (url)
    DO UPDATE SET
        title = EXCLUDED.title,
        subtitle = EXCLUDED.subtitle,
        date = EXCLUDED.date,
        content = EXCLUDED.content,
        tags = EXCLUDED.tags,
        embedding = EXCLUDED.embedding,
        sentiment_score = EXCLUDED.sentiment_score,
        scraped_at = NOW();
    """
    values = (
        news_details["url"],
        news_details["title"],
        news_details["subtitle"],
        news_details["date"],
        news_details["content"],
        news_details["tags"],
        news_details.get("embedding"),
        news_details.get("sentiment_score"),
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
            connection.commit()
            logging.info(f"News inserted/updated successfully: {news_details['url']}")
    except Exception as e:
        logging.error(f"Error inserting/updating news: {e}")
        connection.rollback()
    finally:
        logging.info(f"insert_news completed for URL {news_details['url']}")



def is_url_processed(url):
    """
    Checks if a URL is already processed.
    """
    query = "SELECT EXISTS(SELECT 1 FROM news WHERE url = %s)"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (url,))
            return cursor.fetchone()[0]
    except Exception as e:
        logging.error(f"Error checking URL {url}: {e}")
        return False
    finally:
        logging.info(f"is_url_processed completed for URL {url}")
# Example usage
if __name__ == "__main__":
    # Example news article data
    news_example = {
        "url": "https://www.thedailystar.net/business/news/sample-article",
        "title": "Dhaka stocks decline in early trade",
        "subtitle": "DSEX loses 16.74 points as of 11:28 am",
        "date": "2025-01-02T11:54:00",
        "content": "Stocks start today's trading on a declining note, snapping four consecutive days of gains.",
        "tags": ["DSE", "DSEX", "CASPI", "stock"]
    }
    insert_news(news_example)



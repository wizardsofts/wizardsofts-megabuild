import time
import argparse

from utils import read_config, convert_to_datetime
import logging
import os
from datetime import datetime, timedelta
import requests
from fetch_news_details import fetch_and_save_financialexpress_news_details


def parse_args():
    """Parse command line arguments for backfill configuration."""
    parser = argparse.ArgumentParser(description='Fetch Financial Express news URLs')
    parser.add_argument('--backfill-days', type=int, default=0,
                        help='Number of days to backfill (0 = normal mode, stops at latest stored news)')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Override max pages to fetch per category')
    return parser.parse_args()


def fetch_urls_for_category(category_path, latest_at=None, max_pages=50, backfill_until=None):
    """
    Fetch URLs for a given category until duplicates are encountered or max_pages is reached.

    Args:
        category_path: The category to fetch
        latest_at: Stop when reaching news older than this (normal mode)
        max_pages: Maximum pages to fetch
        backfill_until: If set, fetch until this date (backfill mode, overrides latest_at)
    """
    # In backfill mode, use backfill_until as the stop date instead of latest_at
    stop_date = backfill_until if backfill_until else latest_at
    mode = "BACKFILL" if backfill_until else "NORMAL"

    logging.info(f"Starting URL fetch for category: {category_path} (mode: {mode}, stop_date: {stop_date})")
    output_file = os.path.join(output_dir, f"financialexpress_urls.txt")
    fetched_urls = []

    # Fetch already processed URLs
    base_url_full = f"{base_url}{config.get('FINANCIALEXPRESS', 'url_path')}"
    url_path_details = config.get("FINANCIALEXPRESS", "url_path_details")
    for page in range(1, max_pages + 1):
        time.sleep(10)
        api_url = f"{base_url_full}?page={page}&slug={category_path}"
        logging.info(f"Fetching page {page} for category {category_path}: {api_url}")

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            # Process each news item
            for item in data.get("items", []):
                url = f"{base_url}{url_path_details}{item.get('slug').replace(f'/{category_path}', '')}"
                item_datetime = convert_to_datetime(item.get('datetime'))
                if stop_date and item_datetime <= stop_date:
                    logging.info(f"Reached stop date ({stop_date}). Stopping for category {category_path}.")
                    # Write fetched URLs before returning
                    save_fetched_urls(output_file, fetched_urls)
                    return fetched_urls  # Stop processing further
                # Save the new URL
                fetch_and_save_financialexpress_news_details(url, category_path)
                fetched_urls.append(url)

        except Exception as e:
            logging.error(f"Error fetching page {page} for category {category_path}: {e}")
            break  # Stop fetching this category on error
        finally:
            # Write fetched URLs to the output file
            save_fetched_urls(output_file, fetched_urls)
            fetched_urls = []  # Reset fetched URLs for the next page
            logging.info(f"Finished fetching URLs for category {category_path}. Total fetched: {len(fetched_urls)}")
    return fetched_urls

def save_fetched_urls(output_file, urls):
    """
    Save the fetched URLs to the output file.
    """
    if urls:
        with open(output_file, "a", encoding="utf-8") as file:
            for url in urls:
                file.write(url + "\n")

if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_args()

        # Setup configuration and logging
        config, base_url, output_dir, log_dir = read_config('FINANCIALEXPRESS')
        data = requests.get(config.get('DEFAULT', 'api_url_news_latest_by_tags')).json()['data']
        latest_by_tags = {item[0]: item[2] for item in data}
        log_file = os.path.join(log_dir, f"fetch_urls_financialexpress_{datetime.now().strftime('%Y-%m-%d')}.log")
        logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")

        # Calculate backfill date if specified
        backfill_until = None
        if args.backfill_days > 0:
            backfill_until = datetime.now() - timedelta(days=args.backfill_days)
            logging.info(f"BACKFILL MODE: Fetching news back to {backfill_until}")
            print(f"BACKFILL MODE: Fetching news back to {backfill_until}")

        # Determine max pages (use args override or config default)
        max_pages = args.max_pages if args.max_pages else config.getint("FINANCIALEXPRESS", "batch_size")
        # In backfill mode, use higher max_pages if not explicitly set
        if args.backfill_days > 0 and not args.max_pages:
            max_pages = max(500, max_pages)  # At least 500 pages for backfill
            logging.info(f"BACKFILL MODE: Using max_pages={max_pages}")

        for category_path in config.get("FINANCIALEXPRESS", "categories").split(","):
            latest = latest_by_tags.get(f"/{category_path.strip()}", None)
            if latest:
                print(latest)
                latest = convert_to_datetime(latest)
            fetch_urls_for_category(
                category_path.strip(),
                latest_at=latest,
                max_pages=max_pages,
                backfill_until=backfill_until
            )
    except Exception as e:
        logging.error(f"Error in URL fetching: {e}")
    finally:
        logging.shutdown()
        print("URL fetching completed.")

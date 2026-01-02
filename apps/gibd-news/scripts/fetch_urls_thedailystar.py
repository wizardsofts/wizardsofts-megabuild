import os
import argparse
from selenium.webdriver.common.by import By
import logging
import time

from fetch_news_details import fetch_and_save_thedailystar_news_details
from utils import read_config, get_webdriver
from datetime import datetime, timedelta
import requests


def parse_args():
    """Parse command line arguments for backfill configuration."""
    parser = argparse.ArgumentParser(description='Fetch The Daily Star news URLs')
    parser.add_argument('--backfill-days', type=int, default=0,
                        help='Number of days to backfill (0 = normal mode, stops at latest stored news)')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Override max pages to fetch per category')
    return parser.parse_args()

def fetch_urls_for_category(url_path, latest_url=None, max_pages=50, backfill_until=None):
    """
    Scrape links for a specific URL path and save them to a file.
    
    Args:
        url_path: The URL path to scrape
        latest_url: Stop when reaching this URL (normal mode)
        max_pages: Maximum pages to fetch
        backfill_until: If set, fetch until this date (backfill mode, ignores latest_url)
    """
    mode = "BACKFILL" if backfill_until else "NORMAL"
    logging.info(f"Starting URL fetch for category: {url_path} (mode: {mode}, backfill_until: {backfill_until})")
    full_url = f"{base_url}{url_path}"
    logging.info(f"Accessing URL: {full_url}")
    scraped_links = set()
    try:
        driver = get_webdriver()
        driver.get(full_url)
        time.sleep(2)  # Allow the page to load
        count = 0
        while True:
            # Scrape all <a> tags with href starting with "/business/news/"
            links = driver.find_elements(By.XPATH, f'//a[starts-with(@href, "/business/news/")]')
            for link in links:
                href = link.get_attribute("href")
                if href.startswith("/"):
                    href = base_url + href  # Ensure full URL
                
                # In normal mode, stop at latest_url; in backfill mode, ignore latest_url
                if not backfill_until and href == latest_url:
                    logging.info(f"Reached latest URL: {href}")
                    raise StopIteration
                
                if href in scraped_links:
                    continue  # Skip already processed links
                    
                scraped_links.add(href)
                news_data = fetch_and_save_thedailystar_news_details(href, url_path)
                
                # In backfill mode, check if article is older than backfill_until
                if backfill_until and news_data and news_data.get('date'):
                    try:
                        article_date = datetime.fromisoformat(news_data['date'].replace('Z', '+00:00'))
                        # Make backfill_until timezone-aware if article_date is
                        if article_date.tzinfo is not None:
                            from datetime import timezone
                            backfill_check = backfill_until.replace(tzinfo=timezone.utc)
                        else:
                            backfill_check = backfill_until
                        
                        if article_date < backfill_check:
                            logging.info(f"Reached backfill limit: article date {article_date} < {backfill_check}")
                            raise StopIteration
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Could not parse article date for backfill check: {e}")
                
                time.sleep(2)

            # Find and click the "More" button
            try:
                logging.info("Searching for 'More' button...")
                time.sleep(5)  # Wait for the button to appear
                load_more_button = driver.find_element(By.XPATH,  '//*[@id="inner-wrap"]/div[2]/main/div/div[2]/div/div[3]/div/div/div[1]/div/div[2]/ul/li/a')
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                load_more_button.click()
                logging.info("Clicked 'More' button.")
                time.sleep(10)  # Wait for new content to load
                count += 1
                if count >= max_pages:
                    break  # Stop after max_iterations iterations
            except Exception as e:
                logging.error(f"'Load More' button error occurred: {str(e)}")
                break
            finally:
                save_urls(scraped_links)
            break
        logging.info(f"Finished scraping for {url_path}. Total links scraped: {len(scraped_links)}")
    except StopIteration:
        logging.info("Reached latest URL. Stopping scraping.")
    except Exception as e:
        logging.error(f"Error scraping URL {full_url}: {e}")
    finally:
        save_urls(scraped_links)

def save_urls(scraped_links) :
    logging.info(f"Saving {len(scraped_links)} scraped URLs to file...")
    output_file = os.path.join(output_dir, f"thedailystar_urls.txt")
    with open(output_file, "a", encoding="utf-8") as file:
        for url in sorted(scraped_links):
            file.write(url + "\n")

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    config, base_url, output_dir, log_dir = read_config('THEDAILYSTAR')
    try:
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"fetch_urls_the_daily_star_{datetime.now().strftime('%Y-%m-%d')}.log")
        logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")
        
        # Calculate backfill date if specified
        backfill_until = None
        if args.backfill_days > 0:
            backfill_until = datetime.now() - timedelta(days=args.backfill_days)
            logging.info(f"BACKFILL MODE: Fetching news back to {backfill_until}")
            print(f"BACKFILL MODE: Fetching news back to {backfill_until}")

        # Determine max pages (use args override or config default)
        max_pages = args.max_pages if args.max_pages else config.getint("THEDAILYSTAR", "max_iterations", fallback=500)
        # In backfill mode, use higher max_pages if not explicitly set
        if args.backfill_days > 0 and not args.max_pages:
            max_pages = max(500, max_pages)  # At least 500 pages for backfill
            logging.info(f"BACKFILL MODE: Using max_pages={max_pages}")

        # Try to get latest URLs by tag
        latest_by_tags = {}
        try:
            data = requests.get(config.get('DEFAULT', 'api_url_news_latest_by_tags'), timeout=10).json()['data']
            latest_by_tags = {item[0]: item[1] for item in data}
        except Exception as e:
            logging.warning(f"Could not fetch latest URLs from API: {str(e)}")
        
        for url_path in config.get("THEDAILYSTAR", "url_paths").split(","):
            latest_url = latest_by_tags.get(url_path, None)
            fetch_urls_for_category(
                url_path, 
                latest_url, 
                max_pages,
                backfill_until=backfill_until
            )
            time.sleep(2)
    except Exception as e:
        logging.error(f"Error calling scraper_news_details: {str(e)}")
    finally:
        logging.shutdown()
        print("Daily Star URL fetching completed.")

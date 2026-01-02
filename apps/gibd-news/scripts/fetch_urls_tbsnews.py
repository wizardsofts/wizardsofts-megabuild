import os
import time
import logging
import argparse
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import requests
from fetch_news_details import fetch_and_save_tbsnews_details, ARTICLE_TIMEOUT
from utils import read_config, get_webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


def parse_args():
    """Parse command line arguments for backfill configuration."""
    parser = argparse.ArgumentParser(description='Fetch TBS News URLs')
    parser.add_argument('--backfill-days', type=int, default=0,
                        help='Number of days to backfill (0 = normal mode, stops at latest stored news)')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Override max pages/scrolls to fetch per category')
    parser.add_argument('--max-articles', type=int, default=None,
                        help='Override max articles to process per category')
    return parser.parse_args()

def load_scraped_urls(file_path):
    """Loads previously scraped URLs from a file into a set."""
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        logging.error(f"Error loading scraped URLs from {file_path}: {e}")
        return set()

def fetch_urls_for_category(base_url, output_dir, category_path, latest_url=None, max_pages=2, 
                            backfill_until=None, max_articles_override=None):
    """
    Scrape news links for a specific TBS category and save them to a file.
    
    Args:
        base_url: The base URL for TBS News
        output_dir: Directory to save URLs
        category_path: The category to fetch
        latest_url: Stop when reaching this URL (normal mode)
        max_pages: Maximum scrolls/pages to fetch
        backfill_until: If set, fetch until this date (backfill mode, ignores latest_url)
        max_articles_override: Override max articles to process
    """
    mode = "BACKFILL" if backfill_until else "NORMAL"
    logging.info(f"Starting URL fetch for category: {category_path} (mode: {mode}, backfill_until: {backfill_until})")
    full_url = f"{base_url}{category_path}"
    logging.info(f"Accessing URL: {full_url}")
    urls_file_path = os.path.join(output_dir, "tbsnews_urls.txt")
    previously_scraped_urls = load_scraped_urls(urls_file_path)
    logging.info(f"Loaded {len(previously_scraped_urls)} previously scraped URLs to skip.")
    scraped_links = set()
    driver = None

    # Maximum number of articles to process in one run
    # In backfill mode, allow more articles; otherwise use conservative limit
    if max_articles_override:
        max_articles_to_process = max_articles_override
    elif backfill_until:
        max_articles_to_process = 500  # Backfill mode: process more articles
    else:
        max_articles_to_process = 10  # Normal mode: conservative limit
    
    articles_processed = 0
    reached_backfill_limit = False

    try:
        driver = get_webdriver()
        driver.set_page_load_timeout(ARTICLE_TIMEOUT)
        driver.get(full_url)
        time.sleep(5)  # Allow the page to load fully

        scroll_count = 0
        last_link_count = 0
        consecutive_no_new_links = 0

        # Continue scrolling until we reach max_pages or no new links are loaded after multiple attempts
        while scroll_count < max_pages and articles_processed < max_articles_to_process:
            # Target the specific view-content row class
            try:
                view_content = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "view-content.row"))
                )

                # Find all article links within the view-content
                links = view_content.find_elements(By.TAG_NAME, "a")

                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if not href:
                            continue

                        # In normal mode, stop at latest_url; in backfill mode, ignore latest_url
                        if not backfill_until and latest_url and href == latest_url:
                            logging.info(f"Reached latest URL: {href}")
                            raise StopIteration

                        # Skip non-article links like category links
                        if href.endswith('/economy') or href.endswith('/news') or href == base_url or href.endswith('/analysis'):
                            continue

                        if href in previously_scraped_urls:
                            continue

                        if href and href not in scraped_links:
                            scraped_links.add(href)
                            logging.info(f"Found article URL: {href}")

                            # Process article with appropriate error handling
                            try:
                                news_data = fetch_and_save_tbsnews_details(href, category_path)
                                articles_processed += 1
                                
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
                                            reached_backfill_limit = True
                                            raise StopIteration
                                    except (ValueError, TypeError) as e:
                                        logging.warning(f"Could not parse article date for backfill check: {e}")

                                # Add a delay between article processing to avoid overwhelming resources
                                time.sleep(3)

                                # If we've processed enough articles, break out
                                if articles_processed >= max_articles_to_process:
                                    break
                            except WebDriverException as e:
                                logging.error(f"WebDriver error processing article {href}: {str(e)}")
                                # Save our progress so far even if one article fails
                                if scraped_links:
                                    save_urls(scraped_links, output_dir)
                                # Don't allow the driver to continue in this state
                                if driver:
                                    try:
                                        driver.quit()
                                    except Exception:
                                        pass
                                # Get a fresh driver
                                driver = get_webdriver()
                                driver.set_page_load_timeout(ARTICLE_TIMEOUT)
                                driver.get(full_url)
                                time.sleep(5)
                            except Exception as e:
                                logging.error(f"Error processing article {href}: {str(e)}")
                    except WebDriverException:
                        # If we encounter a WebDriver exception while getting href, skip this link
                        continue

                # Check if we found any new links
                if len(scraped_links) > last_link_count:
                    last_link_count = len(scraped_links)
                    consecutive_no_new_links = 0
                else:
                    consecutive_no_new_links += 1

                # If we haven't found any new links after 3 scrolls, stop
                if consecutive_no_new_links >= 3:
                    logging.info("No new links found after multiple scrolls. Stopping.")
                    break

            except TimeoutException:
                logging.warning("Timed out waiting for view-content row to load")
            except NoSuchElementException:
                logging.warning("Could not find view-content row element")
            except WebDriverException as e:
                logging.error(f"WebDriver exception: {str(e)}")
                # Try to get a fresh driver if the current one is in a bad state
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                driver = get_webdriver()
                driver.set_page_load_timeout(ARTICLE_TIMEOUT)
                driver.get(full_url)
                time.sleep(5)

            # Scroll to bottom to load more content via AJAX
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logging.info("Scrolled to bottom to trigger content loading")
            except WebDriverException as e:
                logging.error(f"Error scrolling: {str(e)}")
                break

            # Wait for AJAX content to load
            time.sleep(3)

            scroll_count += 1
            logging.info(f"Scroll count: {scroll_count}, Links found: {len(scraped_links)}")

        logging.info(f"Finished scraping for {category_path}. Total links scraped: {len(scraped_links)}")
    except StopIteration:
        logging.info("Reached latest URL. Stopping scraping.")
    except WebDriverException as e:
        logging.error(f"WebDriver error while scraping URL {full_url}: {e}")
    except Exception as e:
        logging.error(f"Error scraping URL {full_url}: {e}")
    finally:
        if scraped_links:
            save_urls(scraped_links, output_dir)
        if driver:
            try:
                driver.quit()
            except WebDriverException as e:
                logging.warning(f"Error quitting WebDriver: {str(e)}")

def save_urls(scraped_links, output_dir):
    if not scraped_links:
        return

    logging.info(f"Saving {len(scraped_links)} scraped URLs to file...")
    output_file = os.path.join(output_dir, f"tbsnews_urls.txt")
    try:
        with open(output_file, "a", encoding="utf-8") as file:
            for url in sorted(scraped_links):
                file.write(url + "\n")
    except Exception as e:
        logging.error(f"Error saving URLs to file: {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    config, base_url, output_dir, log_dir = read_config('TBSNEWS')
    try:
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"fetch_urls_tbsnews_{datetime.now().strftime('%Y-%m-%d')}.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            filemode='a'  # Append to existing log file if it exists
        )

        # Calculate backfill date if specified
        backfill_until = None
        if args.backfill_days > 0:
            backfill_until = datetime.now() - timedelta(days=args.backfill_days)
            logging.info(f"BACKFILL MODE: Fetching news back to {backfill_until}")
            print(f"BACKFILL MODE: Fetching news back to {backfill_until}")

        # Determine max pages (use args override or config default)
        max_pages = args.max_pages if args.max_pages else config.getint("TBSNEWS", "max_iterations", fallback=3)
        # In backfill mode, use higher max_pages if not explicitly set
        if args.backfill_days > 0 and not args.max_pages:
            max_pages = max(50, max_pages)  # At least 50 pages for backfill
            logging.info(f"BACKFILL MODE: Using max_pages={max_pages}")

        # Try to get the latest URLs by tag, but don't fail if the API is unavailable
        latest_by_tags = {}
        try:
            data = requests.get(config.get('DEFAULT', 'api_url_news_latest_by_tags'), timeout=10).json()['data']
            latest_by_tags = {item[0]: item[1] for item in data}
        except Exception as e:
            logging.warning(f"Could not fetch latest URLs from API: {str(e)}")

        for category_path in config.get("TBSNEWS", "categories").split(","):
            latest_url = latest_by_tags.get(category_path.strip(), None)
            fetch_urls_for_category(
                base_url,
                output_dir,
                category_path.strip(),
                latest_url,
                max_pages,
                backfill_until=backfill_until,
                max_articles_override=args.max_articles
            )
            # Add delay between categories to avoid overwhelming the server
            time.sleep(5)
    except Exception as e:
        logging.error(f"Error in main execution: {str(e)}")
    finally:
        logging.shutdown()
        print("TBS News URL fetching completed.")

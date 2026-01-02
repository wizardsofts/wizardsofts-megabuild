import logging
import time
import requests
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
from send_news import send_news
from utils import read_config, convert_to_isoformat, webdriver_session
from utils import convert_to_datetime
from storage import NewsStorage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set a more reasonable timeout for article fetching
ARTICLE_TIMEOUT = 30  # Reduced from 60 seconds to 30 seconds
PAGE_LOAD_WAIT = 15   # Explicit wait for key elements

def fetch_and_save_financialexpress_news_details(url, category):
    try:
        news_details = fetch_financialexpress_news_details(url)
        cleaned_content = clean_html(news_details.get("content", ""))
        news_data = {
            "url": url,
            "title": news_details.get("title"),
            "subtitle": news_details.get("excerpt"),
            "date": convert_to_isoformat(convert_to_datetime(news_details.get("publishedAt"))),
            "content": cleaned_content,
            "tags": category,
        }
        send_news(news_data)
        save_news_details(news_data)
    except Exception as e:
        logging.error(f"Error fetching and saving news details for URL {url}: {e}")
    finally:
        logging.info(f"Completed for URL: {url}")

def fetch_and_save_thedailystar_news_details(url, category):
    """Fetch and save Daily Star news details. Returns news_data for backfill date checking."""
    try:
        news_data = fetch_thedailystar_news_details(url, category)
        if news_data:
            send_news(news_data)
            save_news_details(news_data)
        return news_data  # Return news_data for backfill date checking
    except Exception as e:
        logging.error(f"Error fetching and saving news details for URL {url}: {e}")
        return None

def fetch_thedailystar_news_details(url, category):
    """Fetch news details from The Daily Star using context manager."""
    try:
        with webdriver_session() as driver:
            driver.set_page_load_timeout(ARTICLE_TIMEOUT)
            driver.get(url)
            time.sleep(5)
            title = safe_find_element(driver, By.XPATH, '//h1[@class="fw-700 e-mb-16 article-title"]')
            subtitle = safe_find_element(driver, By.XPATH, '//div[@class="bg-cyan br-4 e-p-12 e-mb-16 text-16"]')
            date = safe_find_element(driver, By.XPATH, '//div[@class="date text-14 lh-20 color-iron"]')
            if date:
                date = datetime.strptime(date.split("\n")[0].strip(), '%a %b %d, %Y %I:%M %p')
            content_elements = safe_find_elements(driver, By.XPATH, '//div[@class="pb-20 clearfix"]//p')
            content = " ".join([p.text.strip() for p in content_elements]) if content_elements else None
            logging.info(f"Successfully scraped Daily Star article: {url}")
            return {
                "url": url,
                "title": title,
                "subtitle": subtitle,
                "date": convert_to_isoformat(date),
                "content": content,
                "tags": category
            }
    except Exception as e:
        logging.error(f"Error scraping URL {url}: {str(e)}")
        return None

def fetch_financialexpress_news_details(url):
    try:
        response = requests.get(url, timeout=ARTICLE_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching details for URL {url}: {e}")
        return None

def clean_html(content):
    return BeautifulSoup(content, "html.parser").get_text()

def save_news_details(news_data):
    """
    Save news details using O(1) JSONL append.

    Uses the new NewsStorage module for efficient storage instead of
    the O(n) read-modify-write JSON approach.
    """
    if not news_data:
        return
    try:
        _, _, output_dir, _ = read_config('FINANCIALEXPRESS')
        storage = NewsStorage(output_dir)
        storage.append_news(news_data)
    except Exception as e:
        logging.error(f"Error saving news details for URL {news_data.get('url', 'unknown')}: {e}")
    finally:
        time.sleep(2)  # Brief pause between saves

def safe_find_element(driver, by, value):
    try:
        return driver.find_element(by, value).text.strip()
    except Exception:
        return None

def safe_find_elements(driver, by, value):
    try:
        return driver.find_elements(by, value)
    except Exception:
        return []

def fetch_and_save_tbsnews_details(url, category):
    """
    Fetch and save TBS News article details with retry logic.

    Uses webdriver_session context manager for proper resource cleanup.
    """
    max_retries = 3

    for retry_count in range(max_retries):
        try:
            with webdriver_session(optimize_for_article=True) as driver:
                driver.set_page_load_timeout(ARTICLE_TIMEOUT)
                driver.set_script_timeout(15)

                # Try to load the page with minimal resources first
                try:
                    driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": True})
                    driver.get(url)
                    logging.info(f"Initial page load without JavaScript for {url}")
                    driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": False})
                except Exception as e:
                    logging.warning(f"Error during optimized page load, falling back to standard: {e}")
                    driver.get(url)

                # Use explicit wait for title instead of arbitrary sleep
                try:
                    WebDriverWait(driver, PAGE_LOAD_WAIT).until(
                        EC.presence_of_element_located((By.XPATH, '//h1[contains(@class, "hide-for-small-only") and @itemprop="headline"]'))
                    )
                    logging.info(f"Title element found for {url}")
                except TimeoutException:
                    logging.warning(f"Timeout waiting for title element on {url}, will try to extract content anyway")

                # Extract title - try multiple selectors
                title = None
                for selector in ['//h1[contains(@class, "hide-for-small-only") and @itemprop="headline"]',
                                 '//h1[contains(@class, "node-title")]', '//h1[contains(@class, "title")]']:
                    title = safe_find_element(driver, By.XPATH, selector)
                    if title:
                        break

                if not title:
                    logging.warning(f"Could not find title on {url}, using page title")
                    title = driver.title

                # Extract date using multiple possible selectors
                publication_date = None
                for selector in [".author-section .date", ".date-display-single", ".submitted .date"]:
                    try:
                        date_element = driver.find_element(By.CSS_SELECTOR, selector)
                        date_str = date_element.text.strip()
                        if date_str:
                            for fmt in ["%d %B, %Y, %I:%M %p", "%d %B %Y", "%Y-%m-%d"]:
                                try:
                                    date_obj = datetime.strptime(date_str, fmt)
                                    publication_date = convert_to_isoformat(date_obj)
                                    break
                                except ValueError:
                                    continue
                            if publication_date:
                                break
                    except NoSuchElementException:
                        continue

                # Extract subtitle
                subtitle = None
                for selector in [".intro", ".field-name-field-summary", ".lead-text"]:
                    try:
                        subtitle = safe_find_element(driver, By.CSS_SELECTOR, selector)
                        if subtitle:
                            break
                    except Exception:
                        continue

                # Extract content paragraphs
                content = None
                for selector in ["//p[contains(@class, 'rtejustify')]",
                                 "//div[contains(@class, 'node-body')]//p",
                                 "//div[contains(@class, 'field-name-body')]//p"]:
                    content_elements = safe_find_elements(driver, By.XPATH, selector)
                    if content_elements:
                        content = " ".join([p.text.strip() for p in content_elements if p.text.strip()])
                        break

                # Fallback to BeautifulSoup if Selenium fails
                if not content:
                    logging.warning(f"Could not extract content with Selenium, trying BeautifulSoup for {url}")
                    try:
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        article_body = soup.select_one('div.node-body') or \
                                      soup.select_one('div.field-name-field-body') or \
                                      soup.select_one('article')
                        if article_body:
                            paragraphs = article_body.find_all('p')
                            content = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
                    except Exception as bs_error:
                        logging.error(f"BeautifulSoup extraction failed for {url}: {bs_error}")

                # Get author
                author = None
                for selector in [".author", ".byline", ".field-name-field-author"]:
                    author = safe_find_element(driver, By.CLASS_NAME, selector)
                    if author:
                        break

                # Check if we have minimum required data
                if title and content:
                    news_data = {
                        "url": url,
                        "title": title,
                        "subtitle": subtitle,
                        "date": publication_date,
                        "content": content,
                        "author": author,
                        "tags": category,
                    }

                    logging.info(f"Successfully scraped article: {title}")
                    send_news(news_data)
                    save_news_details(news_data)
                    logging.info(f"Completed for TBS URL: {url}")
                    return news_data  # Return news_data for backfill date checking

                # Missing required fields
                missing = [f for f, v in [("title", title), ("content", content)] if not v]
                raise ValueError(f"Could not extract required fields: {', '.join(missing)}")

        except Exception as e:
            logging.error(f"Error fetching TBS news for URL {url} (attempt {retry_count + 1}/{max_retries}): {e}")
            if retry_count < max_retries - 1:
                logging.info(f"Retrying article fetch (attempt {retry_count + 2}/{max_retries})")
                time.sleep(2)
            else:
                logging.error(f"Failed to fetch article after {max_retries} attempts")

    logging.info(f"Completed for TBS URL: {url}")

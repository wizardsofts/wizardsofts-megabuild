import logging
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')

from scripts.utils import read_config
import json

def scrape_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    news_data = []
    table = soup.find('table', class_='table-news')
    if table:
        rows = table.find_all('tr')
        for i in range(0, len(rows), 6):  # Each news item spans 6 rows
            try:
                news_item = {}
                news_item['title'] = rows[i + 1].find('td').text.strip()
                news_item['subtitle'] = rows[i].find('td').text.strip()
                news_item['date'] = datetime.strptime(rows[i + 3].find('td').text.strip(),
                                                               '%Y-%m-%d').isoformat()
                news_item['url'] = url + '&rand=' + str(i)
                news_item['content'] = rows[i + 2].find('td').text.strip()
                news_item['tags'] = 'dsebd_news_archive'
                news_data.append(news_item)
            except Exception as e:
                logging.error(f"Error while scraping news for {today}: {e}")

    return news_data

try:
    config, base_url, output_dir, log_dir = read_config('DSEBD_NEWS_ARCHIEVE')
    logging.basicConfig(filename=f'{log_dir}/scrape_dsebd_news_archieve.log', level=logging.INFO)
    news_url = config.get('DSEBD_NEWS_ARCHIEVE', 'news_url')
    startDate = datetime.strptime(os.getenv('START_DATE', datetime.today().strftime('%Y-%m-%d')), '%Y-%m-%d')
    endDate = datetime.strptime(os.getenv('END_DATE', datetime.today().strftime('%Y-%m-%d')), '%Y-%m-%d')
    current_date = startDate

    while current_date <= endDate:
        today = current_date.strftime('%Y-%m-%d')
        try:
            print(f"Processing date: {today}")
            logging.info(f"Processing date: {today}")
            url = base_url + f'?startDate={today}&endDate={today}&criteria=4&archive=news'
            scrip_news = scrape_news(url)
            logging.info(f"Scraped {len(scrip_news)} news items for {today}.")
            os.makedirs(output_dir, exist_ok=True)
            with open(f'{output_dir}/dsebd_news_archive_{today}.json', 'w') as f:
                f.write(json.dumps(scrip_news, indent=4))
            response = requests.post(news_url, json=scrip_news)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Error processing date {today}: {e}")
        finally:
            current_date += timedelta(days=1)

except Exception as e:
    logging.error(f"Error encountered: {e}")
    sys.exit(1)

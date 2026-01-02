import os
import json
import logging
import time
import glob
import sys
from send_news import send_news

def process_files(file_list):
    for file_name in file_list:
        if not os.path.exists(file_name):
            logging.error(f"File not found: {file_name}")
            continue

        with open(file_name, "r") as file:
            try:
                news_list = json.load(file)
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON from file: {file_name}")
                continue

            # Extract the last two parts of the file name for tags
            base_name = os.path.basename(file_name)
            parts = base_name.split('_')[-3:]
            tags = '/'.join(parts).replace('.json', '')

            for news_item in news_list:
                try:
                    if 'scraped_news_details_' in file_name:
                        news_item['tags'] = '/' + tags

                    convert_date_format(news_item)
                    send_news(news_item)

                except Exception as e:
                    logging.error(f"Error sending news item: {e}")
                finally:
                    time.sleep(1)


from datetime import datetime


def convert_date_format(news_item):
    old_format = "%a %b %d, %Y %I:%M %p"
    new_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    try:
        old_date = datetime.strptime(news_item['date'], old_format)
        news_item['date'] = old_date.strftime(new_format)
    except ValueError as e:
        print(f"Error converting date: {e}")


if __name__ == "__main__":
    try:
        input_file = sys.argv[1]
        # Use glob to find all matching files
        file_pattern = f"../data/{input_file}*.json"
        print(f"File pattern: {file_pattern}")
        file_names = glob.glob(file_pattern)
        process_files(file_names)
    except Exception as e:
        print(f"Error processing files: {e}")
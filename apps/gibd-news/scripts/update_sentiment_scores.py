import requests
import logging
from utils import read_config
import json
import time
from typing import Dict, List, Optional

# Configure logging
# add logg file location

# Ollama configuration
OLLAMA_MODEL = "llama3:8b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Page size (adjust as needed)
PAGE_SIZE = 20  # You can adjust this based on your API's capabilities

def get_financial_sentiment_with_ollama(text: str, model: str = OLLAMA_MODEL) -> Dict:
    """
    Use Ollama to analyze financial sentiment with custom prompt
    """
    prompt = f"""
    Analyze the sentiment of the following financial news text in the context of Bangladesh's stock market and economy:
    Text: "{text}"
    
    Respond with a JSON object containing:
    - "sentiment": Classification as "POSITIVE", "NEGATIVE", or "NEUTRAL"
    - "score": A confidence score between -1 and 1 (negative values indicate negative sentiment)
    - "confidence": A confidence level between 0 and 1
    - "key_factors": List of key factors that influenced the sentiment classification
    - "entities": List of important entities like company names, people, financial instruments mentioned
    - "topic": Main topic or theme of the news
    Consider the financial context, implications for stock markets, and economic impact.
    Format your response as a JSON object only, with no additional text.
    """
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1  # Lower temperature for more consistent results
                }
            },
            timeout=30  # 30 second timeout
        )
        
        if response.status_code != 200:
            logging.error(f"Ollama API error: {response.status_code} - {response.text}")
            return {
                "sentiment": "NEUTRAL",
                "score": 0.0,
                "confidence": 0.0,
                "key_factors": ["Ollama API error"],
                "entities": [],
                "topic": "error"
            }
        
        result = response.json()
        
        # Extract JSON from response
        import re
        # Look for JSON pattern in response
        json_match = re.search(r'\{.*\}', result['response'], re.DOTALL)
        if json_match:
            json_str = json_match.group()
            parsed_result = json.loads(json_str)
            
            # Ensure all expected keys exist
            default_keys = ['sentiment', 'score', 'confidence', 'key_factors', 'entities', 'topic']
            for key in default_keys:
                if key not in parsed_result:
                    if key == 'score':
                        parsed_result[key] = 0.0
                    elif key == 'confidence':
                        parsed_result[key] = 0.5
                    elif key == 'key_factors':
                        parsed_result[key] = ["No key factors identified"]
                    elif key == 'entities':
                        parsed_result[key] = []
                    elif key == 'topic':
                        parsed_result[key] = "general"
                    else:
                        parsed_result[key] = "NEUTRAL" if key == 'sentiment' else "unknown"
            
            return parsed_result
        else:
            # Fallback if JSON parsing fails
            return {
                "sentiment": "NEUTRAL",
                "score": 0.0,
                "confidence": 0.5,
                "key_factors": ["Could not parse Ollama response"],
                "entities": [],
                "topic": "general"
            }
    except Exception as e:
        logging.error(f"Error calling Ollama for sentiment: {e}")
        return {
            "sentiment": "NEUTRAL", 
            "score": 0.0,
            "confidence": 0.0,
            "key_factors": ["Error processing sentiment"],
            "entities": [],
            "topic": "error"
        }

def update_sentiment_scores(config):
    try:
        # API endpoints (REPLACE THESE WITH YOUR ACTUAL ENDPOINTS)
        PAGINATED_API_URL = config.get('UPDATE_SENTIMENT_SCORE', 'PAGINATED_API_URL')
        UPDATE_API_URL = config.get('UPDATE_SENTIMENT_SCORE', 'UPDATE_API_URL')
        
        page = 0  # Initialize page counter
        while True:
            # Fetch data from paginated API
            url = PAGINATED_API_URL.format(page=page, size=PAGE_SIZE)
            response = requests.get(url)

            if response.status_code != 200:
                logging.error(f"Error fetching data from API: {response.status_code} - {response.text}")
                break

            try:
                data = response.json()['data']
            except (ValueError, KeyError) as e:
                logging.error(f"Failed to parse JSON from response: {response.text}")
                break

            if not data.get("content") or len(data.get("content")) == 0:  # Check for empty content or null
                logging.info("No more data to process.")
                break

            updates = {}
            for item in data["content"]:
                try:
                    if 'dsebd_news_archive' == item.get("tags"):
                        continue
                    title = item.get("title", "")
                    content = item.get("content", "")
                    news_id = item.get("id")

                    text_to_analyze = f"{title}\n{content}"  # Combine text

                    # Use Ollama for sentiment analysis and entity/topic extraction
                    analysis_result = get_financial_sentiment_with_ollama(text_to_analyze)
                    
                    sentiment_score = analysis_result.get("score", 0.0)
                    confidence = analysis_result.get("confidence", 0.5)
                    entities = analysis_result.get("entities", [])
                    topic = analysis_result.get("topic", "general")
                    key_factors = analysis_result.get("key_factors", [])

                    updates[news_id] = {
                        "sentimentScore": sentiment_score,
                        "sentimentConfidence": confidence,
                        "entities": entities,
                        "topic": topic,
                        "keyFactors": key_factors
                    }

                    # Add a small delay to avoid overwhelming Ollama
                    time.sleep(0.1)

                except Exception as e:
                    logging.error(f"Error processing news ID: {news_id}. Error: {e}")

            if updates:  # Check if there are updates to send.
                # Update sentiment scores and extracted data via API
                update_response = requests.put(UPDATE_API_URL, json=updates) # Send the updates

                if update_response.status_code != 200:
                    logging.error(f"Error updating sentiment scores: {update_response.status_code} - {update_response.text}")
                    # Handle the error appropriately (e.g., retry, stop)
                else:
                    logging.info(f"Successfully updated {len(updates)} news items.")
            
            page += 1  # Move to next page
            
            # Optional: Add a small delay between pages to avoid overwhelming the API
            time.sleep(0.5)

    except Exception as e:
        logging.exception("An unexpected error occurred:")

if __name__ == "__main__":
    try:
        config, _, _, log_dir = read_config('UPDATE_SENTIMENT_SCORE')
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            filename=f'{log_dir}/update_sentiment_scores.log')
        update_sentiment_scores(config)
    except Exception as e:
        logging.exception("An unexpected error occurred:")
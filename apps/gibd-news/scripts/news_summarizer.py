import logging
import sys
import os
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from deepseek_llm import DeepSeekLLM
import tldextract

# Import centralized configuration
from config_loader import (
    get_api_keys,
    get_email_config,
    get_llm_provider,
    get_api_base_urls,
    validate_startup,
    ConfigurationError
)

# Build configuration from environment variables
_api_keys = get_api_keys()
_email_config = get_email_config()

MODEL_CONFIG = {
    "provider": get_llm_provider(),
    "model_name": os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/foundation_models/microsoft-Phi-4-mini-instruct")),
    # For OpenAI (from environment):
    "openai_api_key": _api_keys.get('openai'),
    "openai_model": os.getenv('GIBD_OPENAI_MODEL', 'gpt-3.5-turbo'),
    # For DeepSeek (from environment):
    "deepseek_api_url": _api_keys.get('deepseek_url'),
    "deepseek_api_key": _api_keys.get('deepseek'),
    # Email config (from environment):
    "sender_email": _email_config.get('sender_email'),
    "sender_password": _email_config.get('sender_password'),
    "receiver_email": _email_config.get('admin_email'),
    "recipient_emails": _email_config.get('recipient_emails', []),
}

from datetime import datetime, timedelta

# Calculate the timestamp for 24 hours ago in ISO format (assuming UTC)
start_date = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
_api_base_urls = get_api_base_urls()
API_URL = f"{_api_base_urls['news_service']}/api/news/search?size=100&sort=date,desc&startDate={start_date}"

def get_llm_instance(config):
    provider = config.get("provider", "huggingface").lower()
    if provider == "openai":
        return OpenAILLM(config)
    elif provider == "deepseek":
        return DeepSeekLLM(config)
    else:
        raise ValueError(f"Unknown provider: {provider}")

def fetch_news():
    news_items = []
    page = 0
    while True:
        paged_url = f"{API_URL}&page={page}"
        response = requests.get(paged_url)
        try:
            resp_json = response.json()
        except Exception as e:
            print(f"Failed to parse JSON from API response: {e}")
            print(f"Raw response: {response.text}")
            break
        data = resp_json.get('data', {})
        content = data.get('content', [])
        news_items.extend(content)
        if data.get('last', True):
            break
        page += 1
    return news_items

# Prompt formatter
def build_prompt(news):
    content = f"On {news['date']}, title: {news['title']}, content: {news['content']}"
    prompt = (
        f"{content}\n\n"
            "Please analyze the above news and respond in the following JSON format:\n"
            "{\n"
            '  "summary": "A concise, easy-to-understand version of the news that preserves all key facts, context, and critical insights. Focus on retaining maximum informational value without unnecessary detail.",\n'
            '  "entities": ["Top 5 entities mentioned — including companies, people (with designation), events, or financial terms."],\n'
            '  "action_items": ["Top 3 clear, specific actions that a business analyst, AI agent, or investor should take based on the news."]\n'
            "}"

    )
    return prompt

provider = MODEL_CONFIG.get("provider", "deepseek").lower()
llm_instance = get_llm_instance(MODEL_CONFIG)

def generate_with_timeout(prompt, timeout=60):
    """Run model inference with a timeout"""
    result = [None]
    error = [None]

    def run_model():
        try:
            result[0] = llm_instance.generate(prompt)
        except Exception as e:
            error[0] = str(e)

    # Run in a separate thread with timeout
    with ThreadPoolExecutor() as executor:
        future = executor.submit(run_model)
        try:
            future.result(timeout=timeout)
            if error[0]:
                return {"error": error[0]}
            return result[0]
        except TimeoutError:
            return {"error": f"Model inference timed out after {timeout} seconds"}

def extract_json_from_output(output):
    """
    Extract and clean JSON from model output, handling markdown and partial outputs.
    If output is already a dict, return as is.
    """
    if isinstance(output, dict):
        return output

    import re
    import json

    # Remove markdown code block if present
    output = output.strip()
    if output.startswith("```json"):
        output = output[7:]
    if output.startswith("```"):
        output = output[3:]
    if output.endswith("```"):
        output = output[:-3]
    output = output.strip()

    # Try to find the first valid JSON object in the string
    # This will handle cases where the output is truncated or has extra text
    json_start = output.find('{')
    json_end = output.rfind('}')
    if json_start != -1 and json_end != -1 and json_end > json_start:
        candidate = output[json_start:json_end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # fallback: try to fix common JSON issues with demjson3 if available
    try:
        import demjson3
        return demjson3.decode(output)
    except Exception:
        pass

    # fallback: return raw output
    return {"raw_output": output}

def analyze_news_item(news):
    """Analyze a single news item with timeout handling"""
    print(f"Analyzing: {news['title'][:50]}...")

    # Build prompt and generate with timeout
    prompt = build_prompt(news)
    start_time = time.time()
    output = generate_with_timeout(prompt)
    elapsed = time.time() - start_time

    # Check for timeout or error
    if isinstance(output, dict) and "error" in output:
        print(f"⚠️ Error: {output['error']}")
        return output

    print(f"Generation completed in {elapsed:.2f} seconds")
    # print(f"Raw LLM output: {output}")

    # Always clean output if it's a string (e.g., markdown-wrapped JSON)
    if isinstance(output, str):
        output = extract_json_from_output(output)

    # If output is already in the correct format, return as is
    if isinstance(output, dict) and ("summary" in output or "raw_output" in output):
        # Fallback: if all fields are None, try to use raw_output
        if (
            (output.get("summary") is None or output.get("summary") == "") and
            (output.get("entities") is None or output.get("entities") == "") and
            (output.get("action_items") is None or output.get("action_items") == "") and
            output.get("raw_output")
        ):
            print("All fields missing, using raw_output for PDF.")
            return {
                "summary": output.get("raw_output"),
                "entities": None,
                "action_items": None,
                "raw_output": output.get("raw_output")
            }
        return output

    # Use improved extraction
    try:
        return extract_json_from_output(output)
    except Exception as e:
        print(f"⚠️ Failed to parse JSON: {e}")
        return {"raw_output": output}


def analyze_news_item_wrapper(args):
    """
    Wrapper for parallel processing - unpacks args and handles exceptions.
    Returns tuple of (index, news_item, analysis_result).
    """
    idx, news = args
    try:
        analysis = analyze_news_item(news)
        return (idx, news, analysis)
    except Exception as e:
        print(f"⚠️ Error analyzing news item {idx}: {e}")
        return (idx, news, {"error": str(e)})


def analyze_news_parallel(news_list, max_workers=3):
    """
    Analyze multiple news items in parallel.

    Args:
        news_list: List of news items to analyze
        max_workers: Maximum number of concurrent workers (default: 3)
                     Keep this low to respect API rate limits

    Returns:
        List of result dictionaries with title, date, url, summary, entities, action_items
    """
    from concurrent.futures import as_completed

    results = [None] * len(news_list)
    indexed_news = list(enumerate(news_list))

    print(f"\nProcessing {len(news_list)} news items with {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(analyze_news_item_wrapper, item): item[0]
            for item in indexed_news
        }

        # Process as they complete
        completed = 0
        for future in as_completed(future_to_idx):
            completed += 1
            try:
                idx, news, analysis = future.result()
                results[idx] = {
                    "title": news["title"],
                    "date": news["date"],
                    "url": news.get("url"),
                    "summary": analysis.get('summary'),
                    "entities": analysis.get('entities'),
                    "action_items": analysis.get('action_items'),
                }
                print(f"[{completed}/{len(news_list)}] Completed: {news['title'][:40]}...")
            except Exception as e:
                idx = future_to_idx[future]
                print(f"⚠️ Task {idx} failed with exception: {e}")
                results[idx] = {
                    "title": news_list[idx]["title"],
                    "date": news_list[idx]["date"],
                    "url": news_list[idx].get("url"),
                    "summary": None,
                    "entities": None,
                    "action_items": None,
                    "error": str(e)
                }

    return results

def generate_overall_summary(summaries):
    """
    Generate an overall summary from a list of summaries using the selected LLM.
    """
    if not summaries:
        return "No summaries available to generate an overall summary."
    joined_summaries = "\n".join(f"- {s}" for s in summaries)
    prompt = (
        "Given the following news summaries, provide an overall summary capturing the main themes, trends, and key points. "
        "Be concise and insightful.\n\n"
        f"{joined_summaries}\n\nOverall summary:"
    )
    return llm_instance.generate(prompt, max_new_tokens=256)

def extract_summary_from_analysis(analysis):
    summary = None
    if isinstance(analysis, dict):
        summary = analysis.get("summary")
        if not summary and "raw_output" in analysis:
            try:
                raw = analysis["raw_output"]
                if isinstance(raw, str):
                    extracted = extract_json_from_output(raw)
                    summary = extracted.get("summary")
            except Exception:
                pass
    return summary

def generate_and_save_overall_summary_from_file(results_file):
    with open(results_file, "r") as f:
        data = json.load(f)
    # Support both old and new format
    if isinstance(data, dict) and "news_analyses" in data:
        analyses = data["news_analyses"]
    elif isinstance(data, list):
        analyses = data
    else:
        print("Invalid results file format.")
        return

    summaries = []
    for item in analyses:
        analysis = item.get("analysis", {})
        summary = extract_summary_from_analysis(analysis)
        if summary:
            summaries.append(summary)
    overall_summary = generate_overall_summary(summaries)
    print("\nOverall Summary:\n", overall_summary)

    # Save back with overall_summary
    if isinstance(data, dict):
        data["overall_summary"] = overall_summary
    else:
        data = {
            "overall_summary": overall_summary,
            "news_analyses": analyses
        }
    with open(results_file, "w") as f:
        json.dump(data, indent=2, fp=f)
    print(f"Updated file with overall summary: {results_file}")

# PDF and Email utilities
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from urllib.parse import urlparse

def sanitize_pdf_text(text):
    if not isinstance(text, str):
        text = str(text)
    # Replace en dash, em dash, and other common unicode dashes with ASCII dash
    return (
        text.replace('\u2013', '-')
            .replace('\u2014', '-')
            .replace('–', '-')
            .replace('—', '-')
            .encode('latin-1', errors='replace').decode('latin-1')
    )


def extract_source_from_url(url):
    if not url:
        return "N/A"
    try:
        ext = tldextract.extract(url)
        # ext.subdomain, ext.domain, ext.suffix
        if ext.domain:
            return f"{ext.domain}"
    except Exception:
        pass
    logging.info(f"⚠️ Failed to extract source from URL: {url}")
    return "N/A"

def generate_pdf_report(results, overall_summary, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 12, txt="News Summarization Report", ln=True, align='C')
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 14)
    for idx, item in enumerate(results, 1):
        title = item.get('title', f'News {idx}')
        date = item.get('date', f'{idx}')
        url = item.get('url', None)
        summary = item.get("summary")
        entities = item.get("entities")
        action_items = item.get("action_items")
        # Title as heading
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 10, txt=sanitize_pdf_text(title), ln=True)
        # Source after title
        source = extract_source_from_url(url)
        pdf.set_font("Arial", 'I', 11)
        pdf.cell(0, 8, txt=f"Source: {sanitize_pdf_text(source)}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=sanitize_pdf_text(date), ln=True)
        # URL
        # if url:
        #     pdf.set_font("Arial", 'I', 11)
        #     pdf.set_text_color(0, 0, 255)
        #     pdf.cell(0, 8, txt=sanitize_pdf_text(url), ln=True, link=url)
        #     pdf.set_text_color(0, 0, 0)
        # Summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, txt="Summary:", ln=True)
        pdf.set_font("Arial", size=12)
        if summary:
            pdf.multi_cell(0, 8, txt=sanitize_pdf_text(summary))
        else:
            pdf.cell(0, 8, txt="N/A", ln=True)
        # Entities
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, txt="Entities:", ln=True)
        pdf.set_font("Arial", size=12)
        if isinstance(entities, (list, tuple)) and len(entities) > 0:
            for ent in entities:
                pdf.cell(8)
                pdf.multi_cell(0, 8, txt=f"- {sanitize_pdf_text(ent)}")
        elif isinstance(entities, dict) and entities:
            for k, v in entities.items():
                pdf.cell(8)
                pdf.set_font("Arial", 'I', 12)
                # Print category name, no line break
                pdf.cell(0, 8, txt=f"{sanitize_pdf_text(k.capitalize())}: ", ln=False)
                pdf.set_font("Arial", size=12)
                if isinstance(v, (list, tuple)) and v:
                    joined = ", ".join(sanitize_pdf_text(ent) for ent in v)
                    pdf.multi_cell(0, 8, txt=joined)
                elif v:
                    pdf.multi_cell(0, 8, txt=sanitize_pdf_text(v))
        elif entities:
            pdf.multi_cell(0, 8, txt=sanitize_pdf_text(str(entities)))
        else:
            pdf.cell(0, 8, txt="N/A", ln=True)
        # Action Items
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, txt="Action Items:", ln=True)
        pdf.set_font("Arial", size=12)
        if isinstance(action_items, (list, tuple)) and len(action_items) > 0:
            for act in action_items:
                pdf.cell(8)
                pdf.multi_cell(0, 8, txt=f"- {sanitize_pdf_text(act)}")
        elif action_items:
            pdf.multi_cell(0, 8, txt=sanitize_pdf_text(str(action_items)))
        else:
            pdf.cell(0, 8, txt="N/A", ln=True)
        pdf.ln(6)
    pdf.output(pdf_path)

def send_email_with_pdf(subject, body, pdf_path, config):
    sender = config["sender_email"]
    password = config["sender_password"]
    recipients = config["recipient_emails"]
    if not sender or not password:
        print("ERROR: Sender email or password is not set. Please set GIBD_EMAIL_SENDER and GIBD_EMAIL_PASSWORD.")
        return
    if not recipients:
        print("ERROR: No recipients configured. Please set GIBD_EMAIL_RECIPIENTS.")
        return
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    for recipient in recipients:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(pdf_path)}')
        msg.attach(part)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())

if __name__ == "__main__":
    # Validate configuration at startup
    try:
        validate_startup(script_name='news_summarizer')
    except ConfigurationError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="News summarizer with LLM analysis")
    parser.add_argument("--summarize-file", type=str, help="Generate overall summary from an existing results file")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing (default: sequential)")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel workers (default: 3)")
    args = parser.parse_args()

    if args.summarize_file:
        generate_and_save_overall_summary_from_file(args.summarize_file)
    else:
        results = []
        try:
            print("Fetching news...")
            news_list = fetch_news()
            if not news_list:
                print("No news items found.")
                sys.exit(0)

            print(f"Found {len(news_list)} news items to process")

            if args.parallel:
                # Use parallel processing for faster analysis
                start_time = time.time()
                results = analyze_news_parallel(news_list, max_workers=args.workers)
                elapsed = time.time() - start_time
                print(f"\nParallel processing completed in {elapsed:.2f} seconds")
            else:
                # Sequential processing (original behavior)
                for i, news in enumerate(news_list):
                    print(f"\nItem {i+1}/{len(news_list)}: {news['title']}")
                    analysis = analyze_news_item(news)
                    print(f"Analysis completed: {len(str(analysis))} chars")
                    results.append({
                        "title": news["title"],
                        "date": news["date"],
                        "url": news.get("url"),
                        "summary": analysis.get('summary'),
                        "entities": analysis.get('entities'),
                        "action_items": analysis.get('action_items'),
                    })

            # Generate overall summary from all summaries (currently disabled)
            overall_summary = None

            # Save results
            timestamp = time.strftime("%Y-%m-%d_%H-%M")
            output_data = {
                "news_analyses": results
            }
            json_path = f"news_analysis_results_{provider}_{timestamp}.json"
            with open(json_path, "w") as f:
                json.dump(output_data, indent=2, fp=f)
            print(f"\nAnalysis complete. Results saved to {json_path}")

            # Generate PDF and send email
            pdf_path = f"news_summary_report_{provider}_{timestamp}.pdf"
            generate_pdf_report(results, overall_summary, pdf_path)
            print(f"PDF report generated: {pdf_path}")
            subject = f"News Summary Report ({timestamp})"
            body = "Please find attached the latest news summary report."
            send_email_with_pdf(subject, body, pdf_path, MODEL_CONFIG)
            print(f"Email sent to: {MODEL_CONFIG['recipient_emails']}")

        except KeyboardInterrupt:
            print("\nProcess interrupted. Saving partial results...")
            with open("news_analysis_partial_results.json", "w") as f:
                json.dump(results, indent=2, fp=f)
            print("Partial results saved.")

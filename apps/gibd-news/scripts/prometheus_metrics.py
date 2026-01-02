#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for GIBD-News Scrapers

Exposes metrics at /metrics endpoint for Prometheus scraping.
Monitors:
- Scraper execution status
- Article counts per source
- Last successful run timestamps
- Error counts
"""

import os
import json
import glob
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics port
METRICS_PORT = int(os.environ.get('METRICS_PORT', 9090))

# Data directories
config = ConfigLoader()
DATA_DIR = Path(config.get('DEFAULT', 'output_dir', fallback='/app/data'))
LOGS_DIR = Path(config.get('DEFAULT', 'log_dir', fallback='/app/logs'))


def get_article_counts():
    """Count articles per source from today's JSONL file."""
    counts = {
        'financialexpress': 0,
        'tbsnews': 0,
        'thedailystar': 0,
        'total': 0
    }

    today = datetime.now().strftime('%Y-%m-%d')
    jsonl_file = DATA_DIR / f'news_details_{today}.jsonl'

    if jsonl_file.exists():
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            article = json.loads(line)
                            url = article.get('url', '')
                            counts['total'] += 1

                            if 'financialexpress' in url:
                                counts['financialexpress'] += 1
                            elif 'tbsnews' in url:
                                counts['tbsnews'] += 1
                            elif 'thedailystar' in url or 'dailystar' in url:
                                counts['thedailystar'] += 1
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error reading JSONL file: {e}")

    return counts


def get_url_counts():
    """Count URLs collected per source."""
    counts = {}
    url_files = {
        'financialexpress': DATA_DIR / 'financialexpress_urls.txt',
        'tbsnews': DATA_DIR / 'tbsnews_urls.txt',
        'thedailystar': DATA_DIR / 'thedailystar_urls.txt'
    }

    for source, filepath in url_files.items():
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    counts[source] = sum(1 for line in f if line.strip())
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
                counts[source] = 0
        else:
            counts[source] = 0

    return counts


def get_last_run_times():
    """Get last modification times of log files."""
    last_runs = {}
    log_patterns = {
        'financialexpress': 'fetch_urls_financialexpress_*.log',
        'tbsnews': 'fetch_urls_tbsnews_*.log',
        'thedailystar': 'fetch_urls_the_daily_star_*.log'
    }

    for source, pattern in log_patterns.items():
        log_files = sorted(LOGS_DIR.glob(pattern), reverse=True)
        if log_files:
            mtime = log_files[0].stat().st_mtime
            last_runs[source] = int(mtime)
        else:
            last_runs[source] = 0

    return last_runs


def get_error_counts():
    """Count errors from today's logs."""
    errors = {
        'financialexpress': 0,
        'tbsnews': 0,
        'thedailystar': 0
    }

    today = datetime.now().strftime('%Y-%m-%d')
    log_files = {
        'financialexpress': LOGS_DIR / f'fetch_urls_financialexpress_{today}.log',
        'tbsnews': LOGS_DIR / f'fetch_urls_tbsnews_{today}.log',
        'thedailystar': LOGS_DIR / f'fetch_urls_the_daily_star_{today}.log'
    }

    for source, filepath in log_files.items():
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    errors[source] = content.lower().count('error')
            except Exception as e:
                logger.error(f"Error reading log {filepath}: {e}")

    return errors


def check_scraper_health():
    """Check if scrapers have run recently (within last 3 hours)."""
    health = {}
    last_runs = get_last_run_times()
    threshold = time.time() - (3 * 3600)  # 3 hours ago

    for source, last_run in last_runs.items():
        health[source] = 1 if last_run > threshold else 0

    return health


def generate_metrics():
    """Generate Prometheus-format metrics."""
    metrics = []

    # Article counts
    article_counts = get_article_counts()
    metrics.append('# HELP gibd_articles_today_total Total articles fetched today')
    metrics.append('# TYPE gibd_articles_today_total gauge')
    for source, count in article_counts.items():
        if source != 'total':
            metrics.append(f'gibd_articles_today_total{{source="{source}"}} {count}')
    metrics.append(f'gibd_articles_today_total{{source="all"}} {article_counts["total"]}')

    # URL counts
    url_counts = get_url_counts()
    metrics.append('# HELP gibd_urls_collected_total Total URLs collected per source')
    metrics.append('# TYPE gibd_urls_collected_total gauge')
    for source, count in url_counts.items():
        metrics.append(f'gibd_urls_collected_total{{source="{source}"}} {count}')

    # Last run timestamps
    last_runs = get_last_run_times()
    metrics.append('# HELP gibd_scraper_last_run_timestamp Unix timestamp of last scraper run')
    metrics.append('# TYPE gibd_scraper_last_run_timestamp gauge')
    for source, timestamp in last_runs.items():
        metrics.append(f'gibd_scraper_last_run_timestamp{{source="{source}"}} {timestamp}')

    # Error counts
    error_counts = get_error_counts()
    metrics.append('# HELP gibd_scraper_errors_today_total Errors in today logs')
    metrics.append('# TYPE gibd_scraper_errors_today_total gauge')
    for source, count in error_counts.items():
        metrics.append(f'gibd_scraper_errors_today_total{{source="{source}"}} {count}')

    # Scraper health (1 = healthy, 0 = not run recently)
    health = check_scraper_health()
    metrics.append('# HELP gibd_scraper_healthy Scraper health status (1=healthy, 0=stale)')
    metrics.append('# TYPE gibd_scraper_healthy gauge')
    for source, status in health.items():
        metrics.append(f'gibd_scraper_healthy{{source="{source}"}} {status}')

    # Add timestamp
    metrics.append('# HELP gibd_metrics_last_update_timestamp Last metrics update timestamp')
    metrics.append('# TYPE gibd_metrics_last_update_timestamp gauge')
    metrics.append(f'gibd_metrics_last_update_timestamp {int(time.time())}')

    return '\n'.join(metrics) + '\n'


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint."""

    def do_GET(self):
        if self.path == '/metrics':
            try:
                metrics = generate_metrics()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(metrics.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error generating metrics: {e}")
                self.send_response(500)
                self.end_headers()
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def main():
    """Start the metrics server."""
    server = HTTPServer(('0.0.0.0', METRICS_PORT), MetricsHandler)
    logger.info(f"Starting GIBD-News Prometheus metrics exporter on port {METRICS_PORT}")
    logger.info(f"Metrics endpoint: http://0.0.0.0:{METRICS_PORT}/metrics")
    logger.info(f"Health endpoint: http://0.0.0.0:{METRICS_PORT}/health")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down metrics server")
        server.shutdown()


if __name__ == '__main__':
    main()

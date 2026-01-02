"""
Thread-safe JSONL storage module with O(1) appends.

Provides efficient storage for news articles with backward compatibility
for existing JSON files.
"""
import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional


class NewsStorage:
    """
    Thread-safe JSONL storage with O(1) appends.

    JSONL (JSON Lines) format stores one JSON object per line, allowing O(1) append
    operations instead of the O(n) read-modify-write required by JSON arrays.

    Migration Strategy:
    - New data is written to JSONL files
    - Legacy JSON files are read (read-only) for backward compatibility
    - No manual migration required - both formats coexist

    Example:
        storage = NewsStorage("/path/to/output")
        storage.append_news({"title": "News", "url": "http://example.com"})
        all_news = storage.read_all()  # Reads both JSONL and legacy JSON
    """

    _lock = threading.Lock()

    def __init__(self, output_dir: str):
        """
        Initialize the storage.

        Args:
            output_dir: Directory to store news files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _get_date(self, date: Optional[str] = None) -> str:
        """Get date string for file naming."""
        return date or datetime.now().strftime("%Y-%m-%d")

    def _get_jsonl_path(self, date: Optional[str] = None) -> str:
        """Get path for JSONL file."""
        return os.path.join(self.output_dir, f"news_details_{self._get_date(date)}.jsonl")

    def _get_json_path(self, date: Optional[str] = None) -> str:
        """Get path for legacy JSON file."""
        return os.path.join(self.output_dir, f"news_details_{self._get_date(date)}.json")

    def append_news(self, news_data: Dict[str, Any], date: Optional[str] = None) -> None:
        """
        Append a news item to storage with O(1) complexity.

        Args:
            news_data: Dictionary containing news article data
            date: Optional date string (YYYY-MM-DD). Defaults to today.
        """
        if not news_data:
            return

        path = self._get_jsonl_path(date)
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(news_data, ensure_ascii=False, default=str) + "\n")

    def append_batch(self, news_items: List[Dict[str, Any]], date: Optional[str] = None) -> int:
        """
        Append multiple news items efficiently.

        Args:
            news_items: List of news article dictionaries
            date: Optional date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Number of items written
        """
        if not news_items:
            return 0

        path = self._get_jsonl_path(date)
        count = 0
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                for item in news_items:
                    if item:
                        f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
                        count += 1
        return count

    def read_all(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Read all news items for a given date.

        Reads from both JSONL (new format) and JSON (legacy format) files
        to ensure backward compatibility.

        Args:
            date: Optional date string (YYYY-MM-DD). Defaults to today.

        Returns:
            List of news article dictionaries
        """
        items = []

        # Read JSONL (new format)
        jsonl_path = self._get_jsonl_path(date)
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            items.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            # Log but continue - don't fail on single bad line
                            print(f"Warning: Skipping invalid JSON at line {line_num} in {jsonl_path}: {e}")

        # Also read legacy JSON for backward compatibility
        json_path = self._get_json_path(date)
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    legacy = json.load(f)
                    if isinstance(legacy, list):
                        items.extend(legacy)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not read legacy JSON file {json_path}: {e}")

        return items

    def exists(self, url: str, date: Optional[str] = None) -> bool:
        """
        Check if a news item with the given URL already exists.

        Args:
            url: The URL to check for
            date: Optional date string (YYYY-MM-DD). Defaults to today.

        Returns:
            True if URL already exists in storage
        """
        items = self.read_all(date)
        return any(item.get("url") == url for item in items)

    def count(self, date: Optional[str] = None) -> int:
        """
        Get count of news items for a given date.

        Args:
            date: Optional date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Number of news items
        """
        return len(self.read_all(date))

    def get_urls(self, date: Optional[str] = None) -> set:
        """
        Get set of all URLs in storage for deduplication.

        Args:
            date: Optional date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Set of URLs
        """
        items = self.read_all(date)
        return {item.get("url") for item in items if item.get("url")}

    def read_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Read all news items within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD), inclusive
            end_date: End date (YYYY-MM-DD), inclusive

        Returns:
            List of news article dictionaries
        """
        from datetime import datetime, timedelta

        items = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            items.extend(self.read_all(date_str))
            current += timedelta(days=1)

        return items

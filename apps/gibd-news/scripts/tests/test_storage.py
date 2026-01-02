"""
Unit tests for storage.py
"""
import json
import os
import tempfile
import threading
import unittest
from datetime import datetime


class TestNewsStorage(unittest.TestCase):
    """Tests for NewsStorage class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creates_output_directory(self):
        from storage import NewsStorage
        subdir = os.path.join(self.temp_dir, 'subdir')
        storage = NewsStorage(subdir)
        self.assertTrue(os.path.exists(subdir))

    def test_append_creates_jsonl_file(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)
        storage.append_news({"title": "Test", "url": "http://test.com"})

        files = os.listdir(self.temp_dir)
        jsonl_files = [f for f in files if f.endswith('.jsonl')]
        self.assertEqual(len(jsonl_files), 1)

    def test_append_writes_valid_json_line(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)
        news = {"title": "Test Article", "url": "http://test.com"}
        storage.append_news(news)

        jsonl_path = storage._get_jsonl_path()
        with open(jsonl_path) as f:
            line = f.readline()
            loaded = json.loads(line)

        self.assertEqual(loaded['title'], 'Test Article')
        self.assertEqual(loaded['url'], 'http://test.com')

    def test_append_multiple_items(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        for i in range(5):
            storage.append_news({"id": i})

        items = storage.read_all()
        self.assertEqual(len(items), 5)
        self.assertEqual([item['id'] for item in items], [0, 1, 2, 3, 4])

    def test_append_batch(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)
        news_items = [{"id": i} for i in range(10)]

        count = storage.append_batch(news_items)

        self.assertEqual(count, 10)
        self.assertEqual(len(storage.read_all()), 10)

    def test_append_batch_skips_empty_items(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)
        news_items = [{"id": 1}, None, {"id": 2}, {}, {"id": 3}]

        count = storage.append_batch(news_items)

        # Empty dict is falsy, so it's skipped. Only 3 items written
        self.assertEqual(count, 3)

    def test_read_all_returns_empty_list_for_nonexistent_file(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        items = storage.read_all(date="2099-01-01")

        self.assertEqual(items, [])

    def test_read_all_includes_legacy_json(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        # Create legacy JSON file
        today = datetime.now().strftime("%Y-%m-%d")
        legacy_path = os.path.join(self.temp_dir, f"news_details_{today}.json")
        with open(legacy_path, 'w') as f:
            json.dump([{"id": "legacy1"}, {"id": "legacy2"}], f)

        # Append new item via JSONL
        storage.append_news({"id": "new1"})

        # Read should include both
        items = storage.read_all()
        ids = [item['id'] for item in items]

        self.assertIn("legacy1", ids)
        self.assertIn("legacy2", ids)
        self.assertIn("new1", ids)

    def test_exists_returns_true_for_existing_url(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)
        storage.append_news({"url": "http://exists.com"})

        self.assertTrue(storage.exists("http://exists.com"))

    def test_exists_returns_false_for_nonexistent_url(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)
        storage.append_news({"url": "http://exists.com"})

        self.assertFalse(storage.exists("http://notfound.com"))

    def test_count_returns_correct_count(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        self.assertEqual(storage.count(), 0)

        for i in range(7):
            storage.append_news({"id": i})

        self.assertEqual(storage.count(), 7)

    def test_get_urls_returns_set_of_urls(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        storage.append_news({"url": "http://a.com"})
        storage.append_news({"url": "http://b.com"})
        storage.append_news({"url": "http://a.com"})  # duplicate

        urls = storage.get_urls()

        self.assertEqual(urls, {"http://a.com", "http://b.com"})

    def test_append_is_thread_safe(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        def append_items(start, count):
            for i in range(start, start + count):
                storage.append_news({"id": i})

        threads = [
            threading.Thread(target=append_items, args=(i * 100, 100))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        items = storage.read_all()
        self.assertEqual(len(items), 500)

    def test_handles_unicode_content(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        news = {
            "title": "Test with emoji and unicode",
            "content": "Test content"
        }
        storage.append_news(news)

        items = storage.read_all()
        self.assertEqual(items[0]['title'], news['title'])

    def test_handles_datetime_serialization(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        news = {
            "title": "Test",
            "date": datetime(2024, 1, 15, 10, 30, 0)
        }
        storage.append_news(news)

        # Should not raise, datetime should be serialized
        items = storage.read_all()
        self.assertEqual(len(items), 1)

    def test_read_date_range(self):
        from storage import NewsStorage
        storage = NewsStorage(self.temp_dir)

        # Create files for different dates
        for date in ["2024-01-01", "2024-01-02", "2024-01-03"]:
            storage.append_news({"date": date}, date=date)

        items = storage.read_date_range("2024-01-01", "2024-01-02")

        self.assertEqual(len(items), 2)
        dates = [item['date'] for item in items]
        self.assertIn("2024-01-01", dates)
        self.assertIn("2024-01-02", dates)
        self.assertNotIn("2024-01-03", dates)


class TestNewsStoragePerformance(unittest.TestCase):
    """Performance tests for NewsStorage."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_append_is_o1_not_on(self):
        """Verify append is O(1), not O(n) like read-modify-write."""
        from storage import NewsStorage
        import time

        storage = NewsStorage(self.temp_dir)

        # Append many items and measure time
        start = time.time()
        for i in range(1000):
            storage.append_news({"id": i})
        elapsed = time.time() - start

        # Should complete in under 2 seconds (O(1) per append)
        # O(n) would be much slower as file grows
        self.assertLess(elapsed, 2.0, "Append should be O(1), not O(n)")


if __name__ == '__main__':
    unittest.main()

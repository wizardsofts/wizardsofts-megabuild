import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
from datetime import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch_news_details import (
    fetch_and_save_financialexpress_news_details, fetch_financialexpress_news_details,
    fetch_and_save_thedailystar_news_details, fetch_thedailystar_news_details,
    fetch_and_save_tbsnews_details, save_news_details, clean_html,
    safe_find_element, safe_find_elements, ARTICLE_TIMEOUT, PAGE_LOAD_WAIT
)


class TestFetchNewsDetails(unittest.TestCase):

    @patch('fetch_news_details.fetch_financialexpress_news_details')
    @patch('fetch_news_details.clean_html')
    @patch('fetch_news_details.send_news')
    @patch('fetch_news_details.save_news_details')
    @patch('fetch_news_details.convert_to_datetime')
    @patch('fetch_news_details.convert_to_isoformat')
    def test_fetch_and_save_financialexpress_news_details_success(
            self, mock_convert_iso, mock_convert_datetime, mock_save_news,
            mock_send_news, mock_clean_html, mock_fetch_details):
        """Test successful fetch and save of Financial Express news details."""
        # Setup mocks
        mock_fetch_details.return_value = {
            "title": "Test Article",
            "excerpt": "Test Subtitle",
            "content": "<p>Test content</p>",
            "publishedAt": "2025-08-28T10:00:00Z"
        }
        mock_clean_html.return_value = "Test content"
        mock_convert_datetime.return_value = datetime(2025, 8, 28, 10, 0, 0)
        mock_convert_iso.return_value = "2025-08-28T10:00:00"

        # Call the function
        fetch_and_save_financialexpress_news_details("https://example.com/article", "economy")

        # Verify behavior
        mock_fetch_details.assert_called_once_with("https://example.com/article")
        mock_clean_html.assert_called_once_with("<p>Test content</p>")
        mock_send_news.assert_called_once()
        mock_save_news.assert_called_once()

    @patch('fetch_news_details.fetch_financialexpress_news_details', side_effect=Exception("API error"))
    @patch('logging.error')
    def test_fetch_and_save_financialexpress_news_details_error(self, mock_logging, mock_fetch_details):
        """Test error handling in fetch and save of Financial Express news details."""
        # Call the function
        fetch_and_save_financialexpress_news_details("https://example.com/article", "economy")

        # Verify error was logged
        mock_logging.assert_called_once()
        self.assertIn("Error fetching and saving news details", mock_logging.call_args[0][0])

    @patch('fetch_news_details.requests.get')
    def test_fetch_financialexpress_news_details_success(self, mock_get):
        """Test successful API fetch for Financial Express."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Test Article"}
        mock_get.return_value = mock_response

        # Call the function
        result = fetch_financialexpress_news_details("https://example.com/article")

        # Verify behavior
        mock_get.assert_called_once_with("https://example.com/article", timeout=ARTICLE_TIMEOUT)
        self.assertEqual(result, {"title": "Test Article"})

    @patch('fetch_news_details.requests.get', side_effect=Exception("API error"))
    @patch('logging.error')
    def test_fetch_financialexpress_news_details_error(self, mock_logging, mock_get):
        """Test error handling in Financial Express API fetch."""
        # Call the function
        result = fetch_financialexpress_news_details("https://example.com/article")

        # Verify behavior
        mock_logging.assert_called_once()
        self.assertIn("Error fetching details", mock_logging.call_args[0][0])
        self.assertIsNone(result)

    def test_clean_html(self):
        """Test HTML cleaning function."""
        html = "<html><body><p>Test paragraph</p><div>Test div</div></body></html>"
        result = clean_html(html)
        self.assertEqual(result, "Test paragraphTest div")

    @patch('fetch_news_details.fetch_thedailystar_news_details')
    @patch('fetch_news_details.send_news')
    @patch('fetch_news_details.save_news_details')
    def test_fetch_and_save_thedailystar_news_details_success(
            self, mock_save_news, mock_send_news, mock_fetch_details):
        """Test successful fetch and save of Daily Star news details."""
        # Setup mock
        mock_fetch_details.return_value = {"title": "Test Article", "content": "Test content"}

        # Call the function
        fetch_and_save_thedailystar_news_details("https://example.com/article", "economy")

        # Verify behavior
        mock_fetch_details.assert_called_once_with("https://example.com/article", "economy")
        mock_send_news.assert_called_once_with({"title": "Test Article", "content": "Test content"})
        mock_save_news.assert_called_once_with({"title": "Test Article", "content": "Test content"})

    @patch('fetch_news_details.fetch_thedailystar_news_details', side_effect=Exception("Scraping error"))
    @patch('logging.error')
    def test_fetch_and_save_thedailystar_news_details_error(self, mock_logging, mock_fetch_details):
        """Test error handling in fetch and save of Daily Star news details."""
        # Call the function
        fetch_and_save_thedailystar_news_details("https://example.com/article", "economy")

        # Verify error was logged
        mock_logging.assert_called_once()
        self.assertIn("Error fetching and saving news details", mock_logging.call_args[0][0])

    @patch('fetch_news_details.get_webdriver')
    def test_fetch_thedailystar_news_details_success(self, mock_get_driver):
        """Test successful scraping of Daily Star article."""
        # Setup mock driver and elements
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock element finding
        def mock_find_element(by, selector):
            mock_element = MagicMock()
            if selector == '//h1[@class="fw-700 e-mb-16 article-title"]':
                mock_element.text = "Test Title"
            elif selector == '//div[@class="bg-cyan br-4 e-p-12 e-mb-16 text-16"]':
                mock_element.text = "Test Subtitle"
            elif selector == '//div[@class="date text-14 lh-20 color-iron"]':
                mock_element.text = "Tue Aug 28, 2025 10:00 AM"
            return mock_element

        mock_driver.find_element.side_effect = mock_find_element

        # Mock finding paragraph elements
        mock_p1 = MagicMock()
        mock_p1.text = "Paragraph 1"
        mock_p2 = MagicMock()
        mock_p2.text = "Paragraph 2"
        mock_driver.find_elements.return_value = [mock_p1, mock_p2]

        # Call the function
        with patch('fetch_news_details.safe_find_element', side_effect=lambda d, by, val: mock_find_element(by, val).text.strip()):
            with patch('fetch_news_details.safe_find_elements', return_value=[mock_p1, mock_p2]):
                result = fetch_thedailystar_news_details("https://example.com/article", "economy")

        # Verify result
        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["subtitle"], "Test Subtitle")
        self.assertEqual(result["content"], "Paragraph 1 Paragraph 2")
        self.assertEqual(result["tags"], "economy")

    @patch('fetch_news_details.get_webdriver')
    @patch('logging.error')
    def test_fetch_thedailystar_news_details_error(self, mock_logging, mock_get_driver):
        """Test error handling in Daily Star article scraping."""
        # Setup mock driver to raise exception
        mock_driver = MagicMock()
        mock_driver.get.side_effect = WebDriverException("Browser error")
        mock_get_driver.return_value = mock_driver

        # Call the function
        result = fetch_thedailystar_news_details("https://example.com/article", "economy")

        # Verify behavior
        mock_logging.assert_called_once()
        self.assertIn("Error scraping URL", mock_logging.call_args[0][0])
        self.assertIsNone(result)

    @patch('fetch_news_details.read_config')
    @patch('fetch_news_details.json.load')
    @patch('fetch_news_details.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_save_news_details_new_file(self, mock_exists, mock_file, mock_dump, mock_load, mock_read_config):
        """Test saving news details to a new file."""
        # Setup mocks
        mock_read_config.return_value = (None, None, "/path/to/output", None)
        mock_exists.return_value = False
        mock_load.return_value = []

        news_data = {"url": "https://example.com/article", "title": "Test Article"}

        # Call the function
        save_news_details(news_data)

        # Verify behavior
        mock_exists.assert_called_once()
        self.assertEqual(mock_file.call_count, 2)  # Once for creating, once for appending
        # Updated assertion to include indent parameter
        mock_dump.assert_any_call([], mock_file())
        mock_dump.assert_any_call([news_data], mock_file(), indent=4)

    @patch('fetch_news_details.read_config')
    @patch('fetch_news_details.json.load')
    @patch('fetch_news_details.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_save_news_details_existing_file(self, mock_exists, mock_file, mock_dump, mock_load, mock_read_config):
        """Test saving news details to an existing file."""
        # Setup mocks
        mock_read_config.return_value = (None, None, "/path/to/output", None)
        mock_exists.return_value = True
        mock_load.return_value = [{"url": "https://example.com/article1", "title": "Article 1"}]

        news_data = {"url": "https://example.com/article2", "title": "Article 2"}

        # Call the function
        save_news_details(news_data)

        # Verify behavior
        mock_exists.assert_called_once()
        self.assertEqual(mock_file.call_count, 1)  # Only for appending
        expected_data = [{"url": "https://example.com/article1", "title": "Article 1"}, news_data]
        # Updated assertion to include indent parameter
        mock_dump.assert_called_with(expected_data, mock_file(), indent=4)

    @patch('fetch_news_details.read_config')
    @patch('fetch_news_details.json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    @patch('logging.error')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_save_news_details_json_error(self, mock_exists, mock_file, mock_logging, mock_load, mock_read_config):
        """Test handling JSON errors when saving news details."""
        # Setup mocks
        mock_read_config.return_value = (None, None, "/path/to/output", None)
        mock_exists.return_value = True

        news_data = {"url": "https://example.com/article", "title": "Test Article"}

        # Call the function
        save_news_details(news_data)

        # Verify error was logged
        mock_logging.assert_called_once()
        self.assertIn("Error appending to JSON file", mock_logging.call_args[0][0])

    def test_safe_find_element_success(self):
        """Test safe element finding when successful."""
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.text = "Test Element"
        mock_driver.find_element.return_value = mock_element

        result = safe_find_element(mock_driver, "xpath", "//div")
        self.assertEqual(result, "Test Element")

    def test_safe_find_element_exception(self):
        """Test safe element finding when exception occurs."""
        mock_driver = MagicMock()
        mock_driver.find_element.side_effect = Exception("Element not found")

        result = safe_find_element(mock_driver, "xpath", "//div")
        self.assertIsNone(result)

    def test_safe_find_elements_success(self):
        """Test safe elements finding when successful."""
        mock_driver = MagicMock()
        mock_element1 = MagicMock()
        mock_element2 = MagicMock()
        mock_driver.find_elements.return_value = [mock_element1, mock_element2]

        result = safe_find_elements(mock_driver, "xpath", "//div")
        self.assertEqual(result, [mock_element1, mock_element2])

    def test_safe_find_elements_exception(self):
        """Test safe elements finding when exception occurs."""
        mock_driver = MagicMock()
        mock_driver.find_elements.side_effect = Exception("Elements not found")

        result = safe_find_elements(mock_driver, "xpath", "//div")
        self.assertEqual(result, [])

    @patch('fetch_news_details.get_webdriver')
    @patch('fetch_news_details.WebDriverWait')
    @patch('fetch_news_details.send_news')
    @patch('fetch_news_details.save_news_details')
    @patch('time.sleep')
    def test_fetch_and_save_tbsnews_details_success(self, mock_sleep, mock_save_news, mock_send_news,
                                                   mock_wait, mock_get_driver):
        """Test successful TBS news scraping with all elements found."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock the WebDriverWait
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance

        # Setup title element
        mock_title_element = MagicMock()
        mock_title_element.text = "Test Title"
        mock_wait_instance.until.return_value = mock_title_element

        # Mock successful element finds
        def mock_find_element(by, selector):
            mock_element = MagicMock()
            if selector == ".author-section .date":
                mock_element.text = "28 August, 2025, 10:00 AM"
            elif selector == ".intro":
                mock_element.text = "Test Subtitle"
            elif selector == ".author":
                mock_element.text = "Test Author"
            return mock_element

        mock_driver.find_element.side_effect = mock_find_element

        # Mock finding content paragraphs
        mock_p1 = MagicMock()
        mock_p1.text = "Paragraph 1"
        mock_p2 = MagicMock()
        mock_p2.text = "Paragraph 2"
        mock_driver.find_elements.return_value = [mock_p1, mock_p2]

        # Call function with mocked safe_find methods
        with patch('fetch_news_details.safe_find_element', side_effect=lambda d, by, val: {
                '//h1[contains(@class, "hide-for-small-only") and @itemprop="headline"]': "Test Title",
                '.intro': "Test Subtitle",
                '.author': "Test Author"
            }.get(val)):
            with patch('fetch_news_details.safe_find_elements',
                       return_value=[mock_p1, mock_p2]):
                fetch_and_save_tbsnews_details("https://example.com/article", "economy")

        # Verify behavior
        mock_get_driver.assert_called_once_with(optimize_for_article=True)
        mock_send_news.assert_called_once()
        mock_save_news.assert_called_once()

    @patch('fetch_news_details.get_webdriver')
    @patch('fetch_news_details.WebDriverWait')
    @patch('logging.warning')
    @patch('time.sleep')
    def test_fetch_and_save_tbsnews_details_timeout(self, mock_sleep, mock_logging, mock_wait, mock_get_driver):
        """Test TBS news scraping when title element times out."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock the WebDriverWait to timeout
        mock_wait_instance = MagicMock()
        mock_wait_instance.until.side_effect = TimeoutException("Timed out waiting for title")
        mock_wait.return_value = mock_wait_instance

        # Set up BeautifulSoup fallback to work
        with patch('fetch_news_details.safe_find_element', side_effect=lambda d, by, val: {
                '//h1[contains(@class, "title")]': "Test Title from Fallback"
            }.get(val, None)):
            with patch('fetch_news_details.safe_find_elements', return_value=[]):
                with patch('fetch_news_details.BeautifulSoup') as mock_bs:
                    # Setup BeautifulSoup to find content
                    mock_soup = MagicMock()
                    mock_bs.return_value = mock_soup

                    mock_article = MagicMock()
                    mock_soup.select_one.return_value = mock_article

                    mock_p1 = MagicMock()
                    mock_p1.text = "BS Paragraph 1"
                    mock_p2 = MagicMock()
                    mock_p2.text = "BS Paragraph 2"
                    mock_article.find_all.return_value = [mock_p1, mock_p2]

                    fetch_and_save_tbsnews_details("https://example.com/article", "economy")

        # Verify timeout was logged
        mock_logging.assert_called()
        any_timeout_log = any("Timeout waiting for title element" in call[0][0]
                            for call in mock_logging.call_args_list)
        self.assertTrue(any_timeout_log)

    @patch('fetch_news_details.get_webdriver')
    @patch('fetch_news_details.WebDriverWait')
    @patch('logging.error')
    @patch('time.sleep')
    def test_fetch_and_save_tbsnews_details_missing_fields(self, mock_sleep, mock_logging, mock_wait, mock_get_driver):
        """Test TBS news scraping when required fields are missing."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock successful WebDriverWait
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance

        # Mock finding no content
        with patch('fetch_news_details.safe_find_element', return_value=None):
            with patch('fetch_news_details.safe_find_elements', return_value=[]):
                with patch('fetch_news_details.BeautifulSoup') as mock_bs:
                    # Setup BeautifulSoup to find no content
                    mock_soup = MagicMock()
                    mock_bs.return_value = mock_soup
                    mock_soup.select_one.return_value = None

                    fetch_and_save_tbsnews_details("https://example.com/article", "economy")

        # Verify error was logged about missing required fields
        mock_logging.assert_called()
        any_missing_fields_log = any("Failed to extract required fields" in call[0][0]
                                   for call in mock_logging.call_args_list)
        self.assertTrue(any_missing_fields_log)

    @patch('fetch_news_details.get_webdriver')
    @patch('fetch_news_details.WebDriverWait')
    @patch('logging.error')
    @patch('logging.info')  # Added this to catch the retry message
    @patch('time.sleep')
    def test_fetch_and_save_tbsnews_details_retry_success(self, mock_sleep, mock_logging_info, mock_logging_error, mock_wait, mock_get_driver):
        """Test TBS news scraping with failure and then success on retry."""
        # Setup two drivers: first fails, second succeeds
        mock_failed_driver = MagicMock()
        mock_success_driver = MagicMock()

        # First call returns failing driver, second returns success driver
        mock_get_driver.side_effect = [
            mock_failed_driver,  # First attempt fails
            mock_success_driver  # Second attempt succeeds
        ]

        # First driver fails with WebDriverException
        mock_failed_driver.get.side_effect = WebDriverException("Connection lost")

        # Second driver succeeds
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance

        # Mock successful title element
        mock_title_element = MagicMock()
        mock_title_element.text = "Test Title"
        mock_wait_instance.until.return_value = mock_title_element

        # Mock successful content find on second attempt
        with patch('fetch_news_details.safe_find_element', side_effect=lambda d, by, val:
                  "Test Title" if "title" in val else None):
            with patch('fetch_news_details.safe_find_elements', side_effect=lambda d, by, val:
                      [] if d == mock_failed_driver else [MagicMock(text="Test Content")]):
                with patch('fetch_news_details.send_news'):
                    with patch('fetch_news_details.save_news_details'):
                        fetch_and_save_tbsnews_details("https://example.com/article", "economy")

        # Verify retry was logged in info log
        any_retry_log = any("Retrying article fetch" in call[0][0]
                          for call in mock_logging_info.call_args_list)
        self.assertTrue(any_retry_log)

        # Verify both drivers were created and quit
        self.assertEqual(mock_get_driver.call_count, 2)
        mock_failed_driver.quit.assert_called_once()
        mock_success_driver.quit.assert_called_once()


if __name__ == '__main__':
    unittest.main()

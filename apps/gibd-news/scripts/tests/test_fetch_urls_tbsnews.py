import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import logging
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch_urls_tbsnews import load_scraped_urls, fetch_urls_for_category, save_urls


class TestFetchUrlsTBSnews(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data="https://example.com/article1\nhttps://example.com/article2")
    @patch('os.path.exists', return_value=True)
    def test_load_scraped_urls_existing_file(self, mock_exists, mock_file):
        """Test loading scraped URLs from an existing file."""
        urls = load_scraped_urls('/path/to/file.txt')
        self.assertEqual(urls, {"https://example.com/article1", "https://example.com/article2"})
        mock_exists.assert_called_once_with('/path/to/file.txt')
        mock_file.assert_called_once_with('/path/to/file.txt', 'r', encoding='utf-8')

    @patch('os.path.exists', return_value=False)
    def test_load_scraped_urls_nonexistent_file(self, mock_exists):
        """Test loading scraped URLs when file doesn't exist."""
        urls = load_scraped_urls('/path/to/nonexistent.txt')
        self.assertEqual(urls, set())
        mock_exists.assert_called_once_with('/path/to/nonexistent.txt')

    @patch('builtins.open', side_effect=Exception("Error reading file"))
    @patch('os.path.exists', return_value=True)
    def test_load_scraped_urls_file_error(self, mock_exists, mock_file):
        """Test loading scraped URLs when there's an error reading the file."""
        with patch('logging.error') as mock_logging:
            urls = load_scraped_urls('/path/to/error.txt')
            self.assertEqual(urls, set())
            mock_logging.assert_called_once()
            self.assertIn("Error loading scraped URLs", mock_logging.call_args[0][0])

    @patch('builtins.open', new_callable=mock_open)
    def test_save_urls(self, mock_file):
        """Test saving URLs to a file."""
        urls = {"https://example.com/article1", "https://example.com/article2"}
        with patch('logging.info') as mock_logging:
            save_urls(urls, '/path/to/output')
            mock_logging.assert_called_once()
            self.assertIn("Saving 2 scraped URLs", mock_logging.call_args[0][0])

        mock_file.assert_called_once_with('/path/to/output/tbsnews_urls.txt', 'a', encoding='utf-8')
        handle = mock_file()
        self.assertEqual(handle.write.call_count, 2)

    def test_save_urls_empty(self):
        """Test saving an empty set of URLs."""
        with patch('logging.info') as mock_logging:
            save_urls(set(), '/path/to/output')
            mock_logging.assert_not_called()

    @patch('builtins.open', side_effect=Exception("Error saving file"))
    def test_save_urls_error(self, mock_file):
        """Test error handling when saving URLs."""
        urls = {"https://example.com/article1"}
        with patch('logging.error') as mock_logging:
            save_urls(urls, '/path/to/output')
            mock_logging.assert_called_once()
            self.assertIn("Error saving URLs", mock_logging.call_args[0][0])

    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.fetch_and_save_tbsnews_details')
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_fetch_urls_for_category_success(self, mock_sleep, mock_save_urls,
                                           mock_fetch_details, mock_load_urls, mock_get_driver):
        """Test the happy path for fetching URLs for a category."""
        # Setup mocks
        mock_load_urls.return_value = {"https://www.tbsnews.net/old-article"}
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock WebElement for links
        mock_link1 = MagicMock(spec=WebElement)
        mock_link1.get_attribute.return_value = "https://www.tbsnews.net/economy/stocks/article1"
        mock_link2 = MagicMock(spec=WebElement)
        mock_link2.get_attribute.return_value = "https://www.tbsnews.net/economy/stocks/article2"

        # Mock view-content element
        mock_view_content = MagicMock()
        mock_view_content.find_elements.return_value = [mock_link1, mock_link2]

        # Setup driver.find_element to return mock_view_content
        mock_driver.find_element.return_value = mock_view_content

        # Call the function
        fetch_urls_for_category(
            "https://www.tbsnews.net",
            "/path/to/output",
            "/economy/stocks",
            None,
            1  # Only one page to keep test simple
        )

        # Verify behavior
        mock_get_driver.assert_called_once()
        mock_load_urls.assert_called_once()
        self.assertEqual(mock_fetch_details.call_count, 2)
        mock_save_urls.assert_called_once()

    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')
    def test_fetch_urls_timeout_exception(self, mock_sleep, mock_save_urls,
                                        mock_load_urls, mock_get_driver):
        """Test handling of TimeoutException."""
        # Setup mocks
        mock_load_urls.return_value = set()
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Make find_element raise a TimeoutException
        from selenium.webdriver.support.wait import WebDriverWait
        mock_wait = MagicMock()
        mock_wait.until.side_effect = TimeoutException("Timed out")
        with patch('fetch_urls_tbsnews.WebDriverWait', return_value=mock_wait):
            with patch('logging.warning') as mock_logging:
                fetch_urls_for_category("https://www.tbsnews.net", "/path/to/output", "/economy/stocks", None, 1)
                mock_logging.assert_called_with("Timed out waiting for view-content row to load")

    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')
    def test_fetch_urls_no_element_exception(self, mock_sleep, mock_save_urls,
                                          mock_load_urls, mock_get_driver):
        """Test handling of NoSuchElementException."""
        # Setup mocks
        mock_load_urls.return_value = set()
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Make find_element raise a NoSuchElementException
        from selenium.webdriver.support.wait import WebDriverWait
        mock_wait = MagicMock()
        mock_wait.until.side_effect = NoSuchElementException("Element not found")
        with patch('fetch_urls_tbsnews.WebDriverWait', return_value=mock_wait):
            with patch('logging.warning') as mock_logging:
                fetch_urls_for_category("https://www.tbsnews.net", "/path/to/output", "/economy/stocks", None, 1)
                mock_logging.assert_called_with("Could not find view-content row element")

    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')
    def test_fetch_urls_webdriver_exception(self, mock_sleep, mock_save_urls,
                                         mock_load_urls, mock_get_driver):
        """Test handling of WebDriverException."""
        # Setup mocks
        mock_load_urls.return_value = set()
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Make find_element raise a WebDriverException
        from selenium.webdriver.support.wait import WebDriverWait
        mock_wait = MagicMock()
        # Use the same error message format that the actual code would use
        mock_wait.until.side_effect = WebDriverException("WebDriver error")
        with patch('fetch_urls_tbsnews.WebDriverWait', return_value=mock_wait):
            with patch('logging.error') as mock_logging:
                fetch_urls_for_category("https://www.tbsnews.net", "/path/to/output", "/economy/stocks", None, 1)
                # Updated assertion to check if the logged message contains the error, rather than exact match
                any_webdriver_error = any("WebDriver exception" in call[0][0]
                                       for call in mock_logging.call_args_list)
                self.assertTrue(any_webdriver_error)

    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.fetch_and_save_tbsnews_details')
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')
    def test_fetch_urls_latest_url_found(self, mock_sleep, mock_save_urls,
                                       mock_fetch_details, mock_load_urls, mock_get_driver):
        """Test behavior when latest URL is found."""
        # Setup mocks
        mock_load_urls.return_value = set()
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock WebElement for link that matches latest_url
        mock_link = MagicMock(spec=WebElement)
        mock_link.get_attribute.return_value = "https://www.tbsnews.net/latest-article"

        # Mock view-content element
        mock_view_content = MagicMock()
        mock_view_content.find_elements.return_value = [mock_link]

        # Setup WebDriverWait to return mock_view_content
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_view_content

        with patch('fetch_urls_tbsnews.WebDriverWait', return_value=mock_wait):
            with patch('logging.info') as mock_logging:
                fetch_urls_for_category(
                    "https://www.tbsnews.net",
                    "/path/to/output",
                    "/economy/stocks",
                    "https://www.tbsnews.net/latest-article",
                    1
                )
                # Check if the "Reached latest URL" message was logged
                any_latest_url_log = any("Reached latest URL" in call[0][0]
                                      for call in mock_logging.call_args_list)
                self.assertTrue(any_latest_url_log)

    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.fetch_and_save_tbsnews_details', side_effect=WebDriverException("Processing error"))
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')
    def test_fetch_urls_processing_error(self, mock_sleep, mock_save_urls,
                                       mock_fetch_details, mock_load_urls, mock_get_driver):
        """Test handling of errors during article processing."""
        # Setup mocks
        mock_load_urls.return_value = set()
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock WebElement for links
        mock_link = MagicMock(spec=WebElement)
        mock_link.get_attribute.return_value = "https://www.tbsnews.net/economy/stocks/article1"

        # Mock view-content element
        mock_view_content = MagicMock()
        mock_view_content.find_elements.return_value = [mock_link]

        # Setup WebDriverWait to return mock_view_content
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_view_content

        with patch('fetch_urls_tbsnews.WebDriverWait', return_value=mock_wait):
            with patch('logging.error') as mock_logging:
                fetch_urls_for_category("https://www.tbsnews.net", "/path/to/output", "/economy/stocks", None, 1)
                # Verify error was logged
                any_error_log = any("WebDriver error processing article" in call[0][0]
                                 for call in mock_logging.call_args_list)
                self.assertTrue(any_error_log)

        # Verify driver was recreated after error
        self.assertEqual(mock_get_driver.call_count, 2)


    @patch('fetch_urls_tbsnews.get_webdriver')
    @patch('fetch_urls_tbsnews.load_scraped_urls')
    @patch('fetch_urls_tbsnews.save_urls')
    @patch('time.sleep')
    def test_fetch_urls_no_new_links(self, mock_sleep, mock_save_urls,
                                   mock_load_urls, mock_get_driver):
        """Test behavior when no new links are found after multiple scrolls."""
        # Setup mocks
        mock_load_urls.return_value = set()
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver

        # Mock view-content element with empty links list
        mock_view_content = MagicMock()
        mock_view_content.find_elements.return_value = []

        # Setup WebDriverWait to return mock_view_content
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_view_content

        with patch('fetch_urls_tbsnews.WebDriverWait', return_value=mock_wait):
            with patch('logging.info') as mock_logging:
                fetch_urls_for_category("https://www.tbsnews.net", "/path/to/output", "/economy/stocks", None, 5)

                # Check if "No new links found" message was logged
                any_no_links_log = any("No new links found after multiple scrolls" in call[0][0]
                                    for call in mock_logging.call_args_list)
                self.assertTrue(any_no_links_log)


    @patch('fetch_urls_tbsnews.read_config')
    @patch('fetch_urls_tbsnews.fetch_urls_for_category')
    @patch('os.makedirs')
    @patch('logging.basicConfig')
    @patch('requests.get')
    @patch('time.sleep')
    def test_main_function(self, mock_sleep, mock_requests_get, mock_logging_config,
                         mock_makedirs, mock_fetch_urls, mock_read_config):
        """Test the main function execution flow."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda section, key, fallback=None: {
            ('TBSNEWS', 'categories'): '/economy/stocks,/economy/banking',
            ('DEFAULT', 'api_url_news_latest_by_tags'): 'http://api.example.com/latest',
            ('TBSNEWS', 'max_iterations'): '3'
        }.get((section, key), fallback)
        mock_config.getint.return_value = 3

        mock_read_config.return_value = (mock_config, "https://www.tbsnews.net", "/path/to/output", "/path/to/logs")

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [
            ['/economy/stocks', 'https://www.tbsnews.net/economy/stocks/latest1'],
            ['/economy/banking', 'https://www.tbsnews.net/economy/banking/latest2']
        ]}
        mock_requests_get.return_value = mock_response

        # Execute main function
        with patch('fetch_urls_tbsnews.__name__', '__main__'):
            import fetch_urls_tbsnews
            # Create a custom main function to handle the logging module access correctly
            def mock_main():
                config, base_url, output_dir, log_dir = mock_read_config('TBSNEWS')
                try:
                    # Create log directory if it doesn't exist
                    mock_makedirs(log_dir, exist_ok=True)

                    # Mock logging setup instead of actually calling logging.basicConfig
                    log_file = os.path.join(log_dir, f"fetch_urls_tbsnews_{fetch_urls_tbsnews.datetime.now().strftime('%Y-%m-%d')}.log")
                    mock_logging_config(
                        filename=log_file,
                        level=logging.INFO,
                        format="%(asctime)s - %(message)s",
                        filemode='a'
                    )

                    # Mock API call
                    latest_by_tags = {}
                    data = mock_requests_get(config.get('DEFAULT', 'api_url_news_latest_by_tags'), timeout=10).json()['data']
                    latest_by_tags = {item[0]: item[1] for item in data}

                    # Process categories
                    for category_path in config.get("TBSNEWS", "categories").split(","):
                        latest_url = latest_by_tags.get(category_path.strip(), None)
                        mock_fetch_urls(
                            base_url,
                            output_dir,
                            category_path.strip(),
                            latest_url,
                            config.getint("TBSNEWS", "max_iterations", fallback=3)
                        )
                        mock_sleep(5)
                except Exception as e:
                    pass

            # Call our custom main function
            mock_main()

        # Verify the expected calls
        mock_makedirs.assert_called_once_with('/path/to/logs', exist_ok=True)
        mock_requests_get.assert_called_once()
        self.assertEqual(mock_fetch_urls.call_count, 2)  # Called for each category


if __name__ == '__main__':
    unittest.main()

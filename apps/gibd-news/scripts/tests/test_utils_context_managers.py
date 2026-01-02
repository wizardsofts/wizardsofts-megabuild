"""
Unit tests for context managers in utils.py
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock


class TestWebDriverSession(unittest.TestCase):
    """Tests for webdriver_session context manager."""

    @patch('utils.get_webdriver')
    def test_yields_driver(self, mock_get_webdriver):
        from utils import webdriver_session

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with webdriver_session() as driver:
            self.assertEqual(driver, mock_driver)

    @patch('utils.get_webdriver')
    def test_closes_driver_on_exit(self, mock_get_webdriver):
        from utils import webdriver_session

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with webdriver_session():
            pass

        mock_driver.quit.assert_called_once()

    @patch('utils.get_webdriver')
    def test_closes_driver_on_exception(self, mock_get_webdriver):
        from utils import webdriver_session

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with self.assertRaises(ValueError):
            with webdriver_session():
                raise ValueError("test error")

        mock_driver.quit.assert_called_once()

    @patch('utils.get_webdriver')
    def test_passes_optimize_flag(self, mock_get_webdriver):
        from utils import webdriver_session

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with webdriver_session(optimize_for_article=True):
            pass

        mock_get_webdriver.assert_called_with(optimize_for_article=True)

    @patch('utils.get_webdriver')
    def test_handles_quit_exception(self, mock_get_webdriver):
        from utils import webdriver_session
        from selenium.common.exceptions import WebDriverException

        mock_driver = MagicMock()
        mock_driver.quit.side_effect = WebDriverException("quit failed")
        mock_get_webdriver.return_value = mock_driver

        # Should not raise, just log warning
        with webdriver_session():
            pass

    @patch('utils.get_webdriver')
    def test_adds_to_active_drivers(self, mock_get_webdriver):
        from utils import webdriver_session, _active_drivers

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with webdriver_session() as driver:
            # During context, driver should be tracked
            self.assertIn(driver, _active_drivers)


class TestWebDriverSessionPool(unittest.TestCase):
    """Tests for WebDriverSessionPool class."""

    @patch('utils.get_webdriver')
    def test_creates_driver_on_first_use(self, mock_get_webdriver):
        from utils import WebDriverSessionPool

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with WebDriverSessionPool() as pool:
            with pool.get_driver() as driver:
                self.assertEqual(driver, mock_driver)

        mock_get_webdriver.assert_called_once()

    @patch('utils.get_webdriver')
    def test_reuses_driver_for_multiple_requests(self, mock_get_webdriver):
        from utils import WebDriverSessionPool

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with WebDriverSessionPool() as pool:
            with pool.get_driver() as d1:
                pass
            with pool.get_driver() as d2:
                pass
            with pool.get_driver() as d3:
                pass

        # Should only create one driver
        mock_get_webdriver.assert_called_once()

    @patch('utils.get_webdriver')
    def test_recycles_driver_after_max_articles(self, mock_get_webdriver):
        from utils import WebDriverSessionPool

        mock_driver1 = MagicMock()
        mock_driver2 = MagicMock()
        mock_get_webdriver.side_effect = [mock_driver1, mock_driver2]

        with WebDriverSessionPool(max_articles_per_driver=3) as pool:
            for _ in range(5):
                with pool.get_driver():
                    pass

        # Should create 2 drivers (3 uses + 2 uses)
        self.assertEqual(mock_get_webdriver.call_count, 2)
        mock_driver1.quit.assert_called_once()

    @patch('utils.get_webdriver')
    def test_recycles_on_optimize_flag_change(self, mock_get_webdriver):
        from utils import WebDriverSessionPool

        mock_driver1 = MagicMock()
        mock_driver2 = MagicMock()
        mock_get_webdriver.side_effect = [mock_driver1, mock_driver2]

        with WebDriverSessionPool() as pool:
            with pool.get_driver(optimize=False):
                pass
            with pool.get_driver(optimize=True):  # Different flag
                pass

        # Should create 2 drivers
        self.assertEqual(mock_get_webdriver.call_count, 2)

    @patch('utils.get_webdriver')
    def test_closes_driver_on_pool_exit(self, mock_get_webdriver):
        from utils import WebDriverSessionPool

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        with WebDriverSessionPool() as pool:
            with pool.get_driver():
                pass

        mock_driver.quit.assert_called_once()

    @patch('utils.get_webdriver')
    def test_handles_driver_crash(self, mock_get_webdriver):
        from utils import WebDriverSessionPool
        from selenium.common.exceptions import WebDriverException

        mock_driver1 = MagicMock()
        mock_driver2 = MagicMock()
        mock_get_webdriver.side_effect = [mock_driver1, mock_driver2]

        with WebDriverSessionPool() as pool:
            # First use works
            with pool.get_driver():
                pass

            # Second use crashes
            with self.assertRaises(WebDriverException):
                with pool.get_driver():
                    raise WebDriverException("driver crashed")

            # Third use should get a new driver
            with pool.get_driver() as d:
                self.assertEqual(d, mock_driver2)


class TestDatabaseConnection(unittest.TestCase):
    """Tests for DatabaseConnection context manager."""

    @patch('psycopg2.connect')
    def test_connects_to_database(self, mock_connect):
        from utils import DatabaseConnection
        from configparser import ConfigParser

        config = ConfigParser()
        config['TEST_DB'] = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with DatabaseConnection(config, 'TEST_DB') as conn:
            self.assertEqual(conn, mock_conn)

        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass'
        )

    @patch('psycopg2.connect')
    def test_commits_on_success(self, mock_connect):
        from utils import DatabaseConnection
        from configparser import ConfigParser

        config = ConfigParser()
        config['TEST_DB'] = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with DatabaseConnection(config, 'TEST_DB'):
            pass

        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    @patch('psycopg2.connect')
    def test_rollbacks_on_exception(self, mock_connect):
        from utils import DatabaseConnection
        from configparser import ConfigParser

        config = ConfigParser()
        config['TEST_DB'] = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with self.assertRaises(ValueError):
            with DatabaseConnection(config, 'TEST_DB'):
                raise ValueError("test error")

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    @patch('psycopg2.connect')
    def test_closes_connection_on_exit(self, mock_connect):
        from utils import DatabaseConnection
        from configparser import ConfigParser

        config = ConfigParser()
        config['TEST_DB'] = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with DatabaseConnection(config, 'TEST_DB'):
            pass

        mock_conn.close.assert_called_once()

    @patch('psycopg2.connect')
    def test_closes_connection_on_exception(self, mock_connect):
        from utils import DatabaseConnection
        from configparser import ConfigParser

        config = ConfigParser()
        config['TEST_DB'] = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with self.assertRaises(ValueError):
            with DatabaseConnection(config, 'TEST_DB'):
                raise ValueError("test error")

        mock_conn.close.assert_called_once()


class TestCleanupAllDrivers(unittest.TestCase):
    """Tests for emergency cleanup function."""

    @patch('utils.get_webdriver')
    def test_cleanup_quits_active_drivers(self, mock_get_webdriver):
        from utils import _cleanup_all_drivers, _active_drivers, webdriver_session

        mock_driver = MagicMock()
        mock_get_webdriver.return_value = mock_driver

        # Simulate a driver that wasn't properly closed
        _active_drivers.add(mock_driver)

        _cleanup_all_drivers()

        mock_driver.quit.assert_called()


if __name__ == '__main__':
    unittest.main()

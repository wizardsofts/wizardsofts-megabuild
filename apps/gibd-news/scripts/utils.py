import os
import atexit
import weakref
from configparser import ConfigParser
from contextlib import contextmanager
from typing import Optional, Generator

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
import logging
from datetime import datetime

# Global registry for WebDriver cleanup on unexpected exit
_active_drivers: weakref.WeakSet = weakref.WeakSet()


def _cleanup_all_drivers():
    """Emergency cleanup on process exit."""
    for driver in list(_active_drivers):
        try:
            driver.quit()
        except Exception:
            pass


atexit.register(_cleanup_all_drivers)

def read_config(domain='THEDAILYSTAR'):
    """
    Reads the configuration file and returns a ConfigParser object along with base_url, output_dir, and log_dir.
    Returns:
        tuple: ConfigParser object, base_url, output_dir, log_dir
    """
    # Get the active profile from environment variable
    active_profile = os.getenv('ACTIVE_PROFILE', 'hp')

    config_file = os.path.join(os.path.dirname(__file__), f"../config/application-{active_profile}.properties")
    config = ConfigParser()
    config.read(config_file)

    base_url = config.get(domain, "base_url")
    output_dir = config.get("DEFAULT", "output_file_path")  # Directory to save output files
    log_dir = config.get("DEFAULT", "log_file_path")  # Log directory from config

    # Ensure directories exist
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    return config, base_url, output_dir, log_dir


def get_webdriver(optimize_for_article=False):
    """
    Configures and returns a Chrome WebDriver instance with the desired options.
    Uses webdriver-manager to automatically download the compatible ChromeDriver.

    Args:
        optimize_for_article (bool): If True, applies additional optimizations for article scraping
                                    to avoid timeouts and improve performance
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument('--headless')  # Runs Chrome in headless mode
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--disable-dev-shm-usage')  # Overcomes limited resource problems
    options.add_argument('--disable-gpu')  # Disables GPU hardware acceleration

    if optimize_for_article:
        # More aggressive optimizations for article scraping
        options.add_argument('--window-size=1366,768')  # Smaller window size to save memory
        options.add_argument('--disable-images')  # Don't load images
        options.add_argument('--disable-javascript')  # Disable JavaScript initially
        options.add_argument('--disable-animations')  # Disable animations
        options.add_argument('--blink-settings=imagesEnabled=false')  # Disable image loading
        options.add_argument('--disk-cache-size=1')  # Minimize disk cache
        options.add_argument('--media-cache-size=1')  # Minimize media cache
        options.add_argument('--disable-application-cache')  # Disable application cache
        options.add_argument('--disable-extensions')  # Disable extensions
        options.add_argument('--disable-notifications')  # Disable notifications
        options.add_argument('--disable-background-networking')  # Disable background network activity
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values': {
                'images': 2,  # 2 = block images
                'plugins': 2,  # 2 = block plugins
                'popups': 2,  # 2 = block popups
                'geolocation': 2,  # 2 = block geolocation
                'notifications': 2,  # 2 = block notifications
                'auto_select_certificate': 2,  # 2 = block auto select certificate
                'fullscreen': 2,  # 2 = block fullscreen
                'mouselock': 2,  # 2 = block mouselock
                'mixed_script': 2,  # 2 = block mixed script
                'media_stream': 2,  # 2 = block media stream
                'media_stream_mic': 2,  # 2 = block media stream mic
                'media_stream_camera': 2,  # 2 = block media stream camera
                'protocol_handlers': 2,  # 2 = block protocol handlers
                'ppapi_broker': 2,  # 2 = block ppapi broker
                'automatic_downloads': 2,  # 2 = block automatic downloads
                'midi_sysex': 2,  # 2 = block midi sysex
                'push_messaging': 2,  # 2 = block push messaging
                'ssl_cert_decisions': 2,  # 2 = block ssl cert decisions
                'metro_switch_to_desktop': 2,  # 2 = block metro switch to desktop
                'protected_media_identifier': 2,  # 2 = block protected media identifier
                'app_banner': 2,  # 2 = block app banner
                'site_engagement': 2,  # 2 = block site engagement
                'durable_storage': 2  # 2 = block durable storage
            },
            'profile.managed_default_content_settings': {
                'images': 2
            }
        })
    else:
        # Standard options for normal browsing/scraping
        options.add_argument('--window-size=1920,1080')  # Sets default window size
        options.add_argument('--start-maximized')  # Start maximized
        options.add_argument('--disable-extensions')  # Disables extensions
        options.add_argument('--disable-infobars')  # Disables info bars
        options.add_argument('--disable-browser-side-navigation')  # Prevents browser-side navigation
        options.add_argument('--disable-features=VizDisplayCompositor')  # Disables VizDisplayCompositor

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Set reasonable page load timeout
    driver.set_page_load_timeout(30)  # 30 seconds timeout

    return driver


@contextmanager
def webdriver_session(optimize_for_article: bool = False) -> Generator[WebDriver, None, None]:
    """
    Context manager for safe WebDriver lifecycle management.

    Ensures WebDriver is properly closed even if an exception occurs.

    Args:
        optimize_for_article: If True, applies performance optimizations for article scraping

    Yields:
        WebDriver instance

    Example:
        with webdriver_session(optimize_for_article=True) as driver:
            driver.get(url)
            # ... scraping logic
        # driver is automatically closed here
    """
    driver = None
    try:
        driver = get_webdriver(optimize_for_article=optimize_for_article)
        _active_drivers.add(driver)
        yield driver
    finally:
        if driver:
            try:
                _active_drivers.discard(driver)
                driver.quit()
            except WebDriverException as e:
                logging.warning(f"Error closing WebDriver: {e}")
            except Exception:
                pass


class WebDriverSessionPool:
    """
    Reusable WebDriver pool for batch operations.

    Maintains a single WebDriver instance across multiple article fetches,
    recycling it after a configurable number of uses to prevent memory leaks.

    Example:
        with WebDriverSessionPool(max_articles_per_driver=50) as pool:
            for url in urls:
                with pool.get_driver(optimize=True) as driver:
                    driver.get(url)
                    # ... scraping logic
    """

    def __init__(self, max_articles_per_driver: int = 50):
        """
        Initialize the WebDriver pool.

        Args:
            max_articles_per_driver: Number of articles to process before recycling the driver
        """
        self.max_articles = max_articles_per_driver
        self._driver: Optional[WebDriver] = None
        self._usage_count: int = 0
        self._optimize: bool = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    @contextmanager
    def get_driver(self, optimize: bool = False) -> Generator[WebDriver, None, None]:
        """
        Get a WebDriver instance, reusing existing one if possible.

        Args:
            optimize: If True, use article-optimized settings

        Yields:
            WebDriver instance
        """
        # Recycle driver if settings changed or usage limit reached
        if self._driver is not None:
            if optimize != self._optimize or self._usage_count >= self.max_articles:
                self._close_driver()

        # Create new driver if needed
        if self._driver is None:
            self._driver = get_webdriver(optimize_for_article=optimize)
            _active_drivers.add(self._driver)
            self._optimize = optimize
            self._usage_count = 0

        try:
            self._usage_count += 1
            yield self._driver
        except WebDriverException as e:
            # If driver crashed, close and allow recreation on next call
            logging.warning(f"WebDriver error during operation: {e}")
            self._close_driver()
            raise

    def _close_driver(self) -> None:
        """Close the current driver instance."""
        if self._driver:
            try:
                _active_drivers.discard(self._driver)
                self._driver.quit()
            except WebDriverException as e:
                logging.warning(f"Error closing pooled WebDriver: {e}")
            except Exception:
                pass
            finally:
                self._driver = None
                self._usage_count = 0

    def close(self) -> None:
        """Close all resources."""
        self._close_driver()


def setup_logging(log_dir, log_file_name):
    """
    Sets up logging with the specified log directory and log file name.
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, log_file_name)
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")
    return log_file

def convert_to_datetime(datetime_str):
    return datetime.fromisoformat(datetime_str.replace('Z', ''))

def convert_to_isoformat(datetime):
    return datetime.isoformat()


class DatabaseConnection:
    """
    Context manager for PostgreSQL database connections.

    Ensures connections are properly closed and handles transaction management.

    Example:
        config, _, _, _ = read_config()
        with DatabaseConnection(config, 'POSTGRES_WS_GIBD_NEWS') as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM news LIMIT 10")
                results = cursor.fetchall()
        # connection is automatically closed here
    """

    def __init__(self, config: ConfigParser, db_section: str):
        """
        Initialize database connection manager.

        Args:
            config: ConfigParser instance with database configuration
            db_section: Section name in config file containing DB credentials
        """
        self.config = config
        self.db_section = db_section
        self._conn = None

    def __enter__(self):
        try:
            import psycopg2
            self._conn = psycopg2.connect(
                host=self.config.get(self.db_section, 'host'),
                port=self.config.getint(self.db_section, 'port'),
                database=self.config.get(self.db_section, 'database'),
                user=self.config.get(self.db_section, 'user'),
                password=self.config.get(self.db_section, 'password')
            )
            return self._conn
        except ImportError:
            raise ImportError("psycopg2 is required for database connections. Install with: pip install psycopg2-binary")
        except Exception as e:
            logging.error(f"Failed to connect to database [{self.db_section}]: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            try:
                if exc_type:
                    self._conn.rollback()
                    logging.warning(f"Transaction rolled back due to: {exc_val}")
                else:
                    self._conn.commit()
            except Exception as e:
                logging.error(f"Error during transaction cleanup: {e}")
            finally:
                try:
                    self._conn.close()
                except Exception:
                    pass
        return False  # Don't suppress exceptions
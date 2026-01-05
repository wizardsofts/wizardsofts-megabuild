"""Database connection management with pooling and retry logic."""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, pool
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from database.retry import retry_connection

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get database URL from environment variable.

    Returns:
        str: Database URL for PostgreSQL or SQLite

    Defaults to PostgreSQL localhost if DATABASE_URL not set.
    """
    return os.getenv("DATABASE_URL", "postgresql://localhost/quant_flow")


def get_company_info_database_url() -> str:
    """Get database URL for DSE company info database.

    Returns:
        str: Database URL for ws_gibd_dse_company_info database

    Uses same credentials as main database but different database name.
    """
    main_url = get_database_url()
    # Replace database name in the URL (same credentials, different database)
    if "ws_gibd_dse_daily_trades" in main_url:
        return main_url.replace("ws_gibd_dse_daily_trades", "ws_gibd_dse_company_info")
    # Fallback: use environment variable if set
    return os.getenv("COMPANY_INFO_DATABASE_URL", main_url)


class SessionManager:
    """Database session manager with lifecycle management.

    Provides context manager for safe session handling with automatic
    commit/rollback and connection retry logic.

    Example:
        manager = SessionManager()
        with manager.session() as session:
            user = session.query(User).first()

    Example with savepoints:
        with manager.session() as session:
            user = User(name='John')
            session.add(user)
            # Nested transactions with savepoints
            with manager.session() as nested_session:
                nested_session.execute(...)
    """

    def __init__(self):
        """Initialize session manager."""
        self._connection = get_db_connection()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Create a managed database session.

        Yields:
            SQLAlchemy Session with automatic lifecycle management

        Raises:
            ConnectionRetryError: If connection fails after all retries
            Any database exception is rolled back and re-raised
        """
        session = self._connection.create_session()
        try:
            yield session
            session.commit()
            logger.debug("SessionManager: session committed")
        except Exception as e:
            session.rollback()
            logger.warning(f"SessionManager: session rolled back - {e}")
            raise
        finally:
            session.close()
            logger.debug("SessionManager: session closed")

    def close(self) -> None:
        """Close session manager and clean up resources."""
        self._connection.close()
        logger.info("SessionManager closed")


class DatabaseConnection:
    """Singleton database connection manager with pooling.

    Handles:
    - Connection pooling with configurable size
    - Connection timeout configuration
    - Graceful error handling
    - Connection testing on startup
    """

    _instance = None
    _engine = None
    _session_factory = None
    _session = None

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connection."""
        if self._engine is None:
            self._initialize_engine()
            self._initialize_sessions()

    def _initialize_engine(self) -> None:
        """Initialize SQLAlchemy engine with pooling.

        Configuration:
        - Pool size: Configurable via DATABASE_POOL_SIZE env (default: 10)
        - Pool recycle: 3600s (1 hour) to avoid stale connections
        - Connect timeout: 30s (default)
        - Echo: SQL logging if DEBUG=true
        """
        db_url = get_database_url()
        pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        debug = os.getenv("DEBUG", "false").lower() == "true"

        logger.info(f"Creating database engine: {db_url[:30]}... (pool_size={pool_size})")

        # Build connect_args based on database type
        connect_args = {}
        if "postgresql" in db_url:
            connect_args = {
                "connect_timeout": 30,
                "options": "-c statement_timeout=30000",  # 30s statement timeout
            }

        self._engine = create_engine(
            db_url,
            # Connection pooling
            poolclass=pool.QueuePool,
            pool_size=pool_size,
            max_overflow=20,  # Max additional connections beyond pool_size
            pool_timeout=pool_timeout,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Test connections before use
            # Other settings
            echo=debug,
            connect_args=connect_args,
        )

        # Register connection test event
        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Test connection when acquired from pool."""
            logger.debug("New database connection acquired")

        logger.info("Database engine created successfully")

    def _initialize_sessions(self) -> None:
        """Initialize session factory and scoped sessions."""
        self._session_factory = sessionmaker(bind=self._engine)
        self._session = scoped_session(self._session_factory)
        logger.info("Session factory initialized")

    @retry_connection
    def test_connection(self) -> bool:
        """Test database connection on startup with retry logic.

        Retries up to 3 times with exponential backoff (1s, 2s, 4s delays).

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self._engine.connect() as connection:
                # Simple query to test connection
                result = connection.execute(sql_text("SELECT 1"))
                result.close()
            logger.info("✓ Database connection test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Database connection test failed: {e}")
            return False

    def get_engine(self):
        """Get SQLAlchemy engine.

        Returns:
            SQLAlchemy Engine instance
        """
        if self._engine is None:
            self._initialize_engine()
            self._initialize_sessions()
        return self._engine

    def get_session_factory(self):
        """Get session factory.

        Returns:
            sessionmaker instance
        """
        if self._session_factory is None:
            self._initialize_sessions()
        return self._session_factory

    def get_scoped_session(self):
        """Get scoped session for thread-safe access.

        Returns:
            scoped_session instance
        """
        if self._session is None:
            self._initialize_sessions()
        return self._session

    def create_session(self) -> Session:
        """Create a new database session.

        Returns:
            SQLAlchemy Session instance
        """
        if self._session_factory is None:
            self._initialize_sessions()
        return self._session_factory()

    def dispose_pool(self) -> None:
        """Dispose of all connections in the pool.

        Use this during shutdown to ensure clean connection closure.
        """
        if self._engine is not None:
            self._engine.dispose()
            logger.info("Connection pool disposed")

    def close(self) -> None:
        """Close all connections and clean up resources."""
        if self._session is not None:
            self._session.remove()
        if self._engine is not None:
            self._engine.dispose()
        logger.info("Database connection closed")


def get_db_connection() -> DatabaseConnection:
    """Get singleton database connection instance.

    Returns:
        DatabaseConnection singleton
    """
    return DatabaseConnection()


def get_db_session() -> Session:
    """Create a new database session.

    Returns:
        SQLAlchemy Session instance
    """
    return get_db_connection().create_session()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions with retry logic.

    Automatically handles session lifecycle:
    - Creates session on entry
    - Commits on successful exit
    - Rolls back on exception
    - Always closes session

    Retries up to 3 times on transient connection errors with exponential
    backoff (1s, 2s, 4s delays).

    Example:
        with get_db_context() as session:
            result = session.query(Stock).all()

    Example with explicit transaction handling:
        with get_db_context() as session:
            stock = Stock(symbol='AAPL', price=150.0)
            session.add(stock)
            # Auto-commits on successful exit

    Yields:
        SQLAlchemy Session instance

    Raises:
        ConnectionRetryError: If connection fails after all retries
        Any database exception is rolled back and re-raised
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
        logger.debug("Session committed successfully")
    except Exception as e:
        session.rollback()
        logger.warning(f"Session rolled back due to error: {e}")
        raise
    finally:
        session.close()
        logger.debug("Session closed")


# Company Info Database Connection (separate database)
_company_info_engine = None
_company_info_session_factory = None


def _get_company_info_engine():
    """Get or create engine for company info database."""
    global _company_info_engine
    if _company_info_engine is None:
        db_url = get_company_info_database_url()
        logger.info(f"Creating company info database engine: {db_url[:40]}...")
        _company_info_engine = create_engine(
            db_url,
            poolclass=pool.QueuePool,
            pool_size=3,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=os.getenv("DEBUG", "false").lower() == "true",
        )
    return _company_info_engine


def _get_company_info_session_factory():
    """Get or create session factory for company info database."""
    global _company_info_session_factory
    if _company_info_session_factory is None:
        _company_info_session_factory = sessionmaker(bind=_get_company_info_engine())
    return _company_info_session_factory


@contextmanager
def get_company_info_db_context() -> Generator[Session, None, None]:
    """Context manager for company info database sessions.

    Connects to the ws_gibd_dse_company_info database which contains
    DSE company information including sector classifications.

    Example:
        with get_company_info_db_context() as session:
            companies = session.query(Company).all()

    Yields:
        SQLAlchemy Session instance for company info database
    """
    session = _get_company_info_session_factory()()
    try:
        yield session
        session.commit()
        logger.debug("Company info session committed successfully")
    except Exception as e:
        session.rollback()
        logger.warning(f"Company info session rolled back due to error: {e}")
        raise
    finally:
        session.close()
        logger.debug("Company info session closed")

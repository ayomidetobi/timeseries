"""Class to wrap database connection and create sessions.

This includes a function `get_session()` to be used as a FastAPI dependency
to get a database session in endpoints.
"""
import asyncio
import contextlib
from typing import AsyncGenerator

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
import sqlalchemy.ext.asyncio as sa_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.config


class DatabaseConnectionManager:
    """Database connection manager."""

    def __init__(self, settings: app.core.config.Settings) -> None:
        self.database_url = settings.database_url
        self.engine = None
        self.sessionmaker = None
        self._pool_size = settings.sqlalchemy_pool_size
        self._max_overflow = settings.sqlalchemy_max_overflow
        self._pool_timeout = settings.sqlalchemy_pool_timeout
        self._echo = settings.debug

    def init(self):
        """Initialize the database engine and session maker.
        
        TimescaleModel will handle hypertable creation when tables are created via migrations.
        """
        self.engine = sa_asyncio.create_async_engine(
            self.database_url,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_timeout=self._pool_timeout,
            echo=self._echo,
            future=True,
        )
        self.sessionmaker = sa_asyncio.async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @contextlib.asynccontextmanager
    async def make_session(
            self) -> AsyncGenerator[sa_asyncio.AsyncSession, None]:
        """Create a database session as a context manager."""
        if self.sessionmaker is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self.sessionmaker() as session:
            yield session


# This is initialized when the module is imported. Since it is accessed
# via the below function (`get_session()`), a different database connection
# can be used in tests by overriding that dependency in endpoints.
# The creation of the `engine` is delayed until `init()` is called, to
# make it possible to import this module without having to connect to the database.
# This is useful for unit tests.
_db_connection_manager: DatabaseConnectionManager = DatabaseConnectionManager(
    app.core.config.settings)


def init():
    """Function to init the global connection manager instance."""
    _db_connection_manager.init()


async def get_session() -> AsyncGenerator[sa_asyncio.AsyncSession, None]:
    """Function that can be used as a FastAPI dependency to get a db session."""
    async with _db_connection_manager.make_session() as db_session:
        yield db_session


@contextlib.asynccontextmanager
async def get_session_context(
) -> AsyncGenerator[sa_asyncio.AsyncSession, None]:
    """Equal to `get_session()`, but using a context manager.

    While `get_session()` is a dependency that can be used in FastAPI
    endpoints, this can be used in functions that are not FastAPI endpoints
    with:
        async with db_connection.get_session_context() as db_session:
            ...

    """
    try:
        async with _db_connection_manager.make_session() as db_session:
            yield db_session
    except sa_exc.SQLAlchemyError as error:
        error.add_note(pool_status())
        raise


def pool_status() -> str:
    """Get the status of the database connection pool."""
    if _db_connection_manager.engine is None:
        return "Pool Status: Database not initialized"
    
    try:
        # Access the underlying sync engine pool for status
        sync_engine = _db_connection_manager.engine.sync_engine
        if not (hasattr(sync_engine, 'pool') and sync_engine.pool):
            return "Pool Status: Pool not available"
        
        pool = sync_engine.pool
        status = pool.status()
        return f"Pool Status: {status}"
    except Exception as error:  # noqa: BLE001
        return f"Pool Status: Error - {error}"


def check_if_db_is_initialized() -> bool:
    """Check if the database is initialized."""
    return _db_connection_manager.engine is not None


async def db_health_check(timeout: float = 5.0) -> None:
    """Check if the database is up.

    Args:
        timeout: Maximum time to wait for the health check query, in seconds.

    Raises:
        RuntimeError: If the database is not initialized.
        asyncio.TimeoutError: If the health check times out.
    """
    if _db_connection_manager.engine is None:
        raise RuntimeError("Database not initialized.")

    async with sa_asyncio.AsyncSession(
            _db_connection_manager.engine) as session:
        await asyncio.wait_for(session.execute(sa.text("SELECT 1")),
                               timeout=timeout)

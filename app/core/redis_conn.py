"""Redis connection pool management."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis

import app.core.config


class redisConnectionManager:
    """Redis connection manager."""

    def __init__(self, settings: app.core.config.settings) -> None:
        self.hostname = settings.redis_host
        self.port = settings.redis_port
        self.db = settings.redis_db
        self.password = settings.redis_password
        self.encoding = settings.redis_encoding
        self.decode_responses = settings.redis_decode_responses
        self.connection_pool = None

    def init(self) -> None:
        """Initialize connection pool.

        The connection pool is a module-level variable, that is used to create
        Redis connections. This function should be called on application startup.
        """
        self.connection_pool = redis.ConnectionPool(
            host=self.hostname,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=self.decode_responses,
            encoding=self.encoding,
        )

    def close(self) -> None:
        """Close the connection pool."""
        if self.connection_pool:
            # Connection pool will be closed automatically when all connections are closed
            self.connection_pool = None

    def is_initialized(self) -> bool:
        """Check if the connection pool is initialized."""
        return self.connection_pool is not None


# This is initialized when the module is imported. Since it is accessed
# via the below functions, a different Redis connection can be used in tests
# by overriding those dependencies in endpoints.
# The creation of the `connection_pool` is delayed until `init()` is called, to
# make it possible to import this module without having to connect to Redis.
# This is useful for unit tests.
_redis_connection_manager: redisConnectionManager = redisConnectionManager(
    app.core.config.settings
)


def init() -> None:
    """Function to init the global connection manager instance."""
    _redis_connection_manager.init()


def close() -> None:
    """Function to close the global connection manager instance."""
    _redis_connection_manager.close()


def is_initialized() -> bool:
    """Check if Redis connection pool is initialized."""
    return _redis_connection_manager.is_initialized()


async def get_redis_conn() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency to get an asynchronous Redis connection.

    This function is used as a FastAPI dependency in endpoints and other
    dependencies that need to access Redis.

    Yields:
        Asynchronous Redis connection.

    Raises:
        RuntimeError: If Redis connection pool is not initialized.
    """
    if not _redis_connection_manager.is_initialized():
        raise RuntimeError("Redis connection pool not initialized. Call init() first.")

    async with redis.Redis(
        connection_pool=_redis_connection_manager.connection_pool,
        auto_close_connection_pool=False,
    ) as conn:
        yield conn


@asynccontextmanager
async def get_redis_conn_context() -> AsyncGenerator[redis.Redis, None]:
    """Equal to `get_redis_conn()`, but using a context manager.

    While `get_redis_conn()` is a dependency that can be used in FastAPI
    endpoints, this can be used in functions that are not FastAPI endpoints
    with:
        async with redis_conn.get_redis_conn_context() as redis_conn:
            ...

    Raises:
        RuntimeError: If Redis connection pool is not initialized.
    """
    if not _redis_connection_manager.is_initialized():
        raise RuntimeError("Redis connection pool not initialized. Call init() first.")

    async with redis.Redis(
        connection_pool=_redis_connection_manager.connection_pool,
        auto_close_connection_pool=False,
    ) as conn:
        yield conn


async def redis_health_check(timeout: float = 5.0) -> None:
    """Ping Redis to check if it is up.

    Args:
        timeout: Maximum time to wait for the health check ping, in seconds.

    Raises:
        RuntimeError: If the Redis connection pool is not initialized.
        asyncio.TimeoutError: If the health check times out.
    """
    if not _redis_connection_manager.is_initialized():
        raise RuntimeError("Redis connection pool not initialized.")

    async with redis.Redis(
        connection_pool=_redis_connection_manager.connection_pool,
        auto_close_connection_pool=False,
    ) as redis_conn:
        await asyncio.wait_for(redis_conn.ping(), timeout=timeout)

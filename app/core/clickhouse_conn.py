"""ClickHouse connection management with SQLAlchemy engine support."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine
import clickhouse_connect
from clickhouse_sqlalchemy import get_declarative_base

import app.core.config


class clickHouseConnectionManager:
    """ClickHouse connection manager supporting both raw client and SQLAlchemy engine."""

    def __init__(self, settings: app.core.config.settings) -> None:
        self.host = settings.clickhouse_host
        self.port = settings.clickhouse_port
        self.username = settings.clickhouse_username
        self.password = settings.clickhouse_password
        self.database = settings.clickhouse_database
        self.secure = settings.clickhouse_secure
        self.verify = settings.clickhouse_verify

        self.client: Optional[clickhouse_connect.driver.Client] = None
        self.sqlalchemy_engine: Optional["Engine"] = None

    def init(self) -> None:
        """Initialize the ClickHouse client and SQLAlchemy engine."""
        try:
            # Raw ClickHouse client
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
                secure=self.secure,
                verify=self.verify,
            )

            # SQLAlchemy engine for declarative tables
            uri = f"clickhousedb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            self.sqlalchemy_engine = create_engine(uri)

        except Exception as error:
            raise RuntimeError(
                f"Failed to initialize ClickHouse connection: {error}"
            ) from error

    def close(self) -> None:
        """Close the ClickHouse client connection."""
        if self.client:
            try:
                self.client.close()
            except Exception:  # noqa
                pass
            finally:
                self.client = None
        self.sqlalchemy_engine = None

    def is_initialized(self) -> bool:
        """Check if ClickHouse client and engine are initialized."""
        return self.client is not None and self.sqlalchemy_engine is not None

    def get_sqlalchemy_engine(self):
        """Return SQLAlchemy engine, guaranteed initialized."""
        if not self.is_initialized():
            raise RuntimeError("ClickHouse client not initialized. Call init() first.")
        return self.sqlalchemy_engine


# Global manager instance
_clickhouse_connection_manager = clickHouseConnectionManager(app.core.config.settings)


def init() -> None:
    """Initialize the global ClickHouse manager."""
    _clickhouse_connection_manager.init()


def close() -> None:
    """Close the global ClickHouse manager."""
    _clickhouse_connection_manager.close()


def is_initialized() -> bool:
    """Check if the ClickHouse manager is initialized."""
    return _clickhouse_connection_manager.is_initialized()


async def get_clickhouse_client() -> (
    AsyncGenerator[clickhouse_connect.driver.Client, None]
):
    """FastAPI dependency to get ClickHouse client."""
    if not _clickhouse_connection_manager.is_initialized():
        raise RuntimeError("ClickHouse client not initialized. Call init() first.")
    if _clickhouse_connection_manager.client is None:
        raise RuntimeError("ClickHouse client is None despite being initialized.")
    yield _clickhouse_connection_manager.client


@asynccontextmanager
async def get_clickhouse_client_context() -> (
    AsyncGenerator[clickhouse_connect.driver.Client, None]
):
    """Context manager version of ClickHouse client dependency."""
    if not _clickhouse_connection_manager.is_initialized():
        raise RuntimeError("ClickHouse client not initialized. Call init() first.")
    if _clickhouse_connection_manager.client is None:
        raise RuntimeError("ClickHouse client is None despite being initialized.")
    yield _clickhouse_connection_manager.client


async def clickhouse_health_check(timeout: float = 5.0) -> None:
    """Check if ClickHouse is up by executing a simple query."""
    if not _clickhouse_connection_manager.is_initialized():
        raise RuntimeError("ClickHouse client not initialized.")

    client = _clickhouse_connection_manager.client

    def _sync_health_check():
        try:
            result = client.command("SELECT 1")
            if result is None:
                raise RuntimeError("ClickHouse health check returned None")
        except Exception as error:
            raise RuntimeError(f"ClickHouse health check failed: {error}") from error

    loop = asyncio.get_event_loop()
    await asyncio.wait_for(
        loop.run_in_executor(None, _sync_health_check), timeout=timeout
    )


Base = get_declarative_base()

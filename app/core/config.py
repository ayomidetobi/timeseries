from decouple import config
from typing import Optional


def cast_bool(value: str) -> bool:
    """Custom boolean cast that handles invalid values."""
    if isinstance(value, bool):
        return value
    value_lower = str(value).lower().strip()
    if value_lower in ("true", "1", "yes", "on"):
        return True
    if value_lower in ("false", "0", "no", "off", "warn", ""):
        return False
    return False


class Settings:
    """Application settings using python-decouple."""

    # Application
    app_name: str = config("APP_NAME", default="Financial Data API")
    debug: bool = config("DEBUG", default=False, cast=cast_bool)
    log_level: str = config("LOG_LEVEL", default="INFO")

    # Database - Railway PostgreSQL (defaults can be overridden via .env)
    database_url: str = config("DATABASE_URL")
    sync_database_url: str = config("SYNC_DATABASE_URL")

    # Database pool settings
    sqlalchemy_pool_size: int = config("SQLALCHEMY_POOL_SIZE", default=5, cast=int)
    sqlalchemy_max_overflow: int = config(
        "SQLALCHEMY_MAX_OVERFLOW", default=10, cast=int
    )
    sqlalchemy_pool_timeout: int = config(
        "SQLALCHEMY_POOL_TIMEOUT", default=30, cast=int
    )

    # Redis settings (optional)
    redis_host: str = config("REDIS_HOST", default="localhost")
    redis_port: int = config("REDIS_PORT", default=6379, cast=int)
    redis_db: int = config("REDIS_DB", default=0, cast=int)
    redis_password: Optional[str] = config("REDIS_PASSWORD", default=None)
    redis_encoding: str = config("REDIS_ENCODING", default="UTF-8")
    redis_decode_responses: bool = config(
        "REDIS_DECODE_RESPONSES", default=True, cast=bool
    )

    # ClickHouse settings (optional)
    clickhouse_host: str = config("CLICKHOUSE_HOST", default="localhost")
    clickhouse_port: int = config("CLICKHOUSE_PORT", default=8123, cast=int)
    clickhouse_username: str = config("CLICKHOUSE_USERNAME", default="default")
    clickhouse_password: Optional[str] = config("CLICKHOUSE_PASSWORD", default=None)
    clickhouse_database: str = config("CLICKHOUSE_DATABASE", default="default")
    clickhouse_secure: bool = config("CLICKHOUSE_SECURE", default=False, cast=cast_bool)
    clickhouse_verify: bool = config("CLICKHOUSE_VERIFY", default=True, cast=cast_bool)


settings = Settings()

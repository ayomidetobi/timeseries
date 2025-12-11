from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger  # Import configured logger (configures loguru globally)
from app.core.database import init as init_db
from app.core.redis_conn import init as init_redis, close as close_redis
from app.core.clickhouse_conn import init as init_clickhouse, close as close_clickhouse, Base
from app.core.clickhouse_conn import _clickhouse_connection_manager
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app startup and shutdown."""
    # Startup
    logger.info("Initializing application...")
    init_db()
    logger.success("Database initialized")

    # Initialize Redis if configured (optional)
    try:
        init_redis()
        logger.success("Redis connection initialized")
    except Exception as e:
        # Redis is optional, so we continue if it fails to initialize
        logger.warning(f"Redis initialization failed (optional): {e}")
    
    # Initialize ClickHouse if configured (optional)
    try:
        init_clickhouse()  # Initialize ClickHouse client & engine
        # Create tables declaratively
        if _clickhouse_connection_manager.is_initialized():
            engine = _clickhouse_connection_manager.get_sqlalchemy_engine()
            Base.metadata.create_all(engine, checkfirst=True)
            logger.success("ClickHouse connection initialized")
    except Exception as e:
        # ClickHouse is optional, so we continue if it fails to initialize
        logger.warning(f"ClickHouse initialization failed (optional): {e}")

    logger.info("Application startup complete")
    yield 
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")
    try:
        close_clickhouse()
        logger.info("ClickHouse connection closed")
    except Exception as e:
        logger.warning(f"Error closing ClickHouse connection: {e}")
    # Database connections will be closed automatically when the engine is disposed
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")



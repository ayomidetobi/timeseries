from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init as init_db, db_health_check
from app.core.redis_conn import init as init_redis, close as close_redis, redis_health_check
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app startup and shutdown."""
    # Startup
    init_db()

    # Initialize Redis if configured (optional)
    try:
        init_redis()
    except Exception:
        # Redis is optional, so we continue if it fails to initialize
        pass
    
    yield
    
    # Shutdown
    try:
        close_redis()
    except Exception:
        pass
    # Database connections will be closed automatically when the engine is disposed


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Financial Data API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that verifies database and Redis connectivity."""
    health_status = {
        "status": "healthy",
        "database": "connected",
        "redis": "unknown"
    }
    
    # Check database
    try:
        await db_health_check(timeout=5.0)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
    
    # Check Redis (optional)
    try:
        await redis_health_check(timeout=2.0)
        health_status["redis"] = "connected"
    except RuntimeError:
        # Redis not initialized, which is fine
        health_status["redis"] = "not_configured"
    except Exception:
        # Redis is configured but not responding
        health_status["redis"] = "disconnected"
        # Don't fail the health check for Redis issues
    
    return health_status



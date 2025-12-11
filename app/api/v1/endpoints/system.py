"""System endpoints (root, health check)."""

from fastapi import APIRouter, HTTPException

from app.core.database import db_health_check
from app.core.redis_conn import redis_health_check
from app.core.clickhouse_conn import clickhouse_health_check
from app.schemas.system import rootResponse, healthStatusResponse, healthErrorResponse

router = APIRouter()


@router.get("/", response_model=rootResponse)
async def root():
    """Root endpoint."""
    return rootResponse(message="Financial Data API", version="1.0.0", docs="/docs")


@router.get("/health", response_model=healthStatusResponse)
async def health_check():
    """Health check endpoint that verifies database, Redis, and ClickHouse connectivity."""
    health_status = {
        "status": "healthy",
        "database": "connected",
        "redis": "unknown",
        "clickhouse": "unknown",
    }

    # Check database
    try:
        await db_health_check(timeout=5.0)
    except Exception as e:
        error_detail = healthErrorResponse(
            status="unhealthy", database="disconnected", error=str(e)
        )
        raise HTTPException(status_code=503, detail=error_detail.model_dump())

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

    # Check ClickHouse (optional)
    try:
        await clickhouse_health_check(timeout=2.0)
        health_status["clickhouse"] = "connected"
    except RuntimeError:
        # ClickHouse not initialized, which is fine
        health_status["clickhouse"] = "not_configured"
    except Exception:
        # ClickHouse is configured but not responding
        health_status["clickhouse"] = "disconnected"
        # Don't fail the health check for ClickHouse issues

    return healthStatusResponse(**health_status)

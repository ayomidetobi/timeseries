"""System response schemas."""

from sqlmodel import SQLModel, Field


class rootResponse(SQLModel):
    """Response schema for the root endpoint."""

    message: str = Field(description="API welcome message")
    version: str = Field(description="API version")
    docs: str = Field(description="Path to API documentation")


class healthStatusResponse(SQLModel):
    """Response schema for the health check endpoint."""

    status: str = Field(description="Overall health status: 'healthy' or 'unhealthy'")
    database: str = Field(
        description="Database connection status: 'connected', 'disconnected', or 'unknown'"
    )
    redis: str = Field(
        description="Redis connection status: 'connected', 'disconnected', 'not_configured', or 'unknown'"
    )
    clickhouse: str = Field(
        description="ClickHouse connection status: 'connected', 'disconnected', 'not_configured', or 'unknown'"
    )


class healthErrorResponse(SQLModel):
    """Response schema for health check error (HTTPException detail)."""

    status: str = Field(description="Health status: 'unhealthy'")
    database: str = Field(description="Database connection status: 'disconnected'")
    error: str = Field(description="Error message describing the failure")

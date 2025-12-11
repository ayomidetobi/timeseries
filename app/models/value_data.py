"""ClickHouse ValueData model and response schemas."""

from datetime import date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import Column
from sqlalchemy.sql import text, func
from sqlmodel import SQLModel, Field

from app.core.clickhouse_conn import Base
from clickhouse_sqlalchemy import types, engines  # type: ignore


class valueData(Base):
    """ValueData table in ClickHouse for time-series observations."""

    __tablename__: str = "value_data"

    series_id: Column = Column(
        types.UInt32, primary_key=True
    )  # FK to metaSeries.series_id
    timestamp: Column = Column(
        types.DateTime64(6), primary_key=True
    )  # high precision timestamp
    value: Column = Column(types.Float64, nullable=False)

    # Audit fields (versioning and derived flags moved to MetaSeries)
    created_at: Column = Column(types.DateTime64(3), server_default=func.now())
    updated_at: Column = Column(types.DateTime64(3), server_default=func.now())

    __table_args__ = (
        engines.MergeTree(
            partition_by=text("toYYYYMM(timestamp)"),
            order_by=("series_id", "timestamp"),
            primary_key=("series_id", "timestamp"),
        ),
    )


class valueDataResponse(SQLModel):
    """Response schema for ValueData - only includes timestamp and value."""

    timestamp: date
    value: Decimal


class valueDataWithMetadataResponse(SQLModel):
    """Response schema for ValueData with full metadata (without timestamp)."""

    # Series identifier
    series_id: int

    # Series metadata
    series_name: str
    ticker: Optional[str] = None
    is_active: bool
    is_derived: bool

    # Fields moved from ValueData to MetaSeries
    is_latest: bool
    version_number: int
    derived_flag: Optional[str] = None
    dependency_calculation_id: Optional[int] = None
    field_name: Optional[str] = None

    # Lookup table metadata (names)
    asset_class_name: Optional[str] = None
    sub_asset_class_name: Optional[str] = None
    product_type_name: Optional[str] = None
    data_type_name: Optional[str] = None
    structure_type_name: Optional[str] = None
    market_segment_name: Optional[str] = None
    field_type_name: Optional[str] = None
    ticker_source_name: Optional[str] = None


class valueDataCombinedResponse(SQLModel):
    """Response schema combining metadata and value data as separate fields."""

    model_config = {"populate_by_name": True}

    meta_series_data: valueDataWithMetadataResponse = Field(
        alias="metadata", description="Series metadata and lookup table information"
    )
    value_data: List[valueDataResponse] = Field(
        description="Array of all value data for this metadata"
    )

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import Field, Relationship, Column, Numeric
from sqlalchemy import Index
from sqlmodel import SQLModel
from timescaledb import TimescaleModel

if TYPE_CHECKING:
    from app.models.meta_series import MetaSeries
    from app.models.dependency import CalculationLog


class ValueData(TimescaleModel, table=True):
    """Unified value data table for both raw and derived time series observations."""
    
    __tablename__ = "value_data"
    __table_args__ = (
        # Composite indexes for common filter combinations
        Index("ix_value_data_series_is_latest", "series_id", "is_latest"),
        Index("ix_value_data_series_date", "series_id", "timestamp"),
    )
    __time_column__ = "timestamp"  # Specify the time column
    __chunk_time_interval__ = "INTERVAL 7 days"  # Chunk interval for partitioning
    __enable_compression__ = True  # Enable compression for older data
    __compress_orderby__ = "timestamp DESC"  # Compression ordering
    __compress_segmentby__ = "series_id"  # Segment by series_id for better compression
    __if_not_exists__ = True  # Create hypertable if not exists
    
    # Override TimescaleModel's default id and time fields
    # id is nullable and not part of primary key (we use composite key: series_id + timestamp)
    # time is nullable and not used (we use timestamp as the time column via __time_column__)
    id: Optional[int] = Field(default=None, sa_column_kwargs={"primary_key": False, "autoincrement": True})
    time: Optional[datetime] = Field(default=None, sa_column_kwargs={"primary_key": False, "nullable": True})
    
    # Primary key (composite: series_id + timestamp)
    # timestamp acts as the time column for TimescaleDB (via __time_column__ = "timestamp")
    series_id: int = Field(foreign_key="meta_series.series_id", primary_key=True)
    timestamp: date = Field(primary_key=True, index=True)
    
    # Value field (used for both raw and derived values)
    value: Decimal = Field(sa_column=Column(Numeric(20, 8)))
    
    # Fields specific to derived values (only populated when series is_derived=True)
    dependency_calculation_id: Optional[int] = Field(default=None, foreign_key="calculation_log.calculation_id", index=True)
    derived_flag: Optional[str] = Field(default=None, max_length=50, description="Flag indicating derived data characteristics")
    
    # Value-specific versioning and audit fields
    version_number: int = Field(default=1)
    is_latest: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    series: "MetaSeries" = Relationship(back_populates="value_data")
    calculation: Optional["CalculationLog"] = Relationship(back_populates="derived_values")



class ValueDataResponse(SQLModel):
    """Response schema for ValueData - only includes timestamp and value."""
    
    timestamp: date
    value: Decimal


class ValueDataWithMetadataResponse(SQLModel):
    """Response schema for ValueData with full metadata (without timestamp)."""
    
    # Series identifier
    series_id: int
    
    # Series metadata
    series_name: str
    ticker: Optional[str] = None
    is_active: bool
    is_derived: bool
    
    # Lookup table metadata (names)
    asset_class_name: Optional[str] = None
    sub_asset_class_name: Optional[str] = None
    product_type_name: Optional[str] = None
    data_type_name: Optional[str] = None
    structure_type_name: Optional[str] = None
    market_segment_name: Optional[str] = None
    field_type_name: Optional[str] = None


class ValueDataCombinedResponse(SQLModel):
    """Response schema combining metadata and value data as separate fields."""
    
    model_config = {"populate_by_name": True}
    
    meta_series_data: ValueDataWithMetadataResponse = Field(
        alias="metadata", description="Series metadata and lookup table information"
    )
    value_data: List[ValueDataResponse] = Field(description="Array of all value data for this metadata")
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column, Numeric
from sqlalchemy import Index, Enum as SQLEnum

if TYPE_CHECKING:
    from app.models.lookup_tables import (
        AssetClassLookup,
        ProductTypeLookup,
        SubAssetClassLookup,
        DataTypeLookup,
        StructureTypeLookup,
        MarketSegmentLookup,
        FieldTypeLookup,
    )
    from app.models.value_data import ValueData
    from app.models.dependency import SeriesDependencyGraph, CalculationLog


class DataSource(str, Enum):
    """Enum for data source types."""
    RAW = "RAW"
    DERIVED = "DERIVED"


class FieldType(str, Enum):
    """Enum for field types (FLDS)."""
    PX_LAST = "PX_LAST"
    OPEN_INT = "OPEN_INT"
    PX_OPEN = "PX_OPEN"
    PX_HIGH = "PX_HIGH"
    PX_LOW = "PX_LOW"
    PX_VOLUME = "PX_VOLUME"


class MetaSeries(SQLModel, table=True):
    """Meta series table for financial data series metadata."""
    
    __tablename__ = "meta_series"
    __table_args__ = (
        # Composite indexes for common filter combinations
        Index("ix_meta_series_is_active_asset_class", "is_active", "asset_class_id"),
        Index("ix_meta_series_is_active_product_type", "is_active", "product_type_id"),
        Index("ix_meta_series_asset_class_product_type", "asset_class_id", "product_type_id"),
        Index("ix_meta_series_is_derived", "is_derived"),
        Index("ix_meta_series_source", "source"),
    )
    
    series_id: Optional[int] = Field(default=None, primary_key=True)
    series_name: str = Field(index=True, max_length=255)
    asset_class_id: Optional[int] = Field(default=None, foreign_key="asset_class_lookup.asset_class_id", index=True)
    sub_asset_class_id: Optional[int] = Field(default=None, foreign_key="sub_asset_class_lookup.sub_asset_class_id", index=True)
    product_type_id: Optional[int] = Field(default=None, foreign_key="product_type_lookup.product_type_id", index=True)
    data_type_id: Optional[int] = Field(default=None, foreign_key="data_type_lookup.data_type_id", index=True)
    structure_type_id: Optional[int] = Field(default=None, foreign_key="structure_type_lookup.structure_type_id", index=True)
    market_segment_id: Optional[int] = Field(default=None, foreign_key="market_segment_lookup.market_segment_id", index=True)
    ticker: Optional[str] = Field(default=None, max_length=100, index=True)
    flds_id: Optional[int] = Field(default=None, foreign_key="field_type_lookup.field_type_id", index=True, description="Field type (FLDS) - e.g., PX_LAST, OPEN_INT")
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    version_number: int = Field(default=1)
    is_active: bool = Field(default=True, index=True)
    
    # Series metadata fields (moved from ValueData)
    is_derived: bool = Field(default=False, index=True, description="True if series contains derived/calculated values")
    calculation_method: Optional[str] = Field(default=None, max_length=100, description="Method used to calculate derived values")
    data_quality_score: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(3, 2)), description="Overall data quality score for the series")
    source: Optional[DataSource] = Field(
        default=None,
        sa_column=Column(SQLEnum(DataSource, name="data_source", create_constraint=True ,native_enum=True)),
        description="Data source: raw or derived"
    )
    confidence_level: Optional[str] = Field(default=None, max_length=20, description="Confidence level for the series data")
    effective_date: Optional[datetime] = Field(default=None, description="Date when the series becomes effective")
    as_of_date: Optional[datetime] = Field(default=None, description="Date as of which the series metadata is current")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    asset_class: Optional["AssetClassLookup"] = Relationship(back_populates="meta_series")
    sub_asset_class: Optional["SubAssetClassLookup"] = Relationship(back_populates="meta_series")
    product_type: Optional["ProductTypeLookup"] = Relationship(back_populates="meta_series")
    data_type: Optional["DataTypeLookup"] = Relationship(back_populates="meta_series")
    structure_type: Optional["StructureTypeLookup"] = Relationship(back_populates="meta_series")
    market_segment: Optional["MarketSegmentLookup"] = Relationship(back_populates="meta_series")
    field_type: Optional["FieldTypeLookup"] = Relationship(back_populates="meta_series")
    value_data: list["ValueData"] = Relationship(back_populates="series")
    parent_dependencies: list["SeriesDependencyGraph"] = Relationship(
        back_populates="parent_series",
        sa_relationship_kwargs={"foreign_keys": "SeriesDependencyGraph.parent_series_id"}
    )
    child_dependencies: list["SeriesDependencyGraph"] = Relationship(
        back_populates="child_series",
        sa_relationship_kwargs={"foreign_keys": "SeriesDependencyGraph.child_series_id"}
    )
    calculations: list["CalculationLog"] = Relationship(back_populates="derived_series")


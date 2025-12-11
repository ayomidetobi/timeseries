from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column, Numeric
from sqlalchemy import Index, Enum as SQLEnum

if TYPE_CHECKING:
    from app.models.lookup_tables import (
        assetClassLookup,
        productTypeLookup,
        subAssetClassLookup,
        dataTypeLookup,
        structureTypeLookup,
        marketSegmentLookup,
        fieldTypeLookup,
    )
    from app.models.dependency import seriesDependencyGraph, calculationLog


class dataSource(str, Enum):
    """Enum for data source types."""
    RAW = "RAW"
    DERIVED = "DERIVED"


class fieldType(str, Enum):
    """Enum for field types (FLDS)."""
    PX_LAST = "PX_LAST"
    OPEN_INT = "OPEN_INT"
    PX_OPEN = "PX_OPEN"
    PX_HIGH = "PX_HIGH"
    PX_LOW = "PX_LOW"
    PX_VOLUME = "PX_VOLUME"


class metaSeries(SQLModel, table=True):
    """Meta series table for financial data series metadata."""
    
    __tablename__ = "meta_series"
    __table_args__ = (
        # Composite indexes for common filter combinations
        Index("ix_meta_series_is_active_asset_class", "is_active", "asset_class_id"),
        Index("ix_meta_series_is_active_product_type", "is_active", "product_type_id"),
        Index("ix_meta_series_asset_class_product_type", "asset_class_id", "product_type_id"),
        Index("ix_meta_series_is_derived", "is_derived"),
        Index("ix_meta_series_source", "source"),
        Index("ix_meta_series_is_latest", "is_latest"),
        Index("ix_meta_series_dependency_calc", "dependency_calculation_id"),
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
    version_number: int = Field(default=1, description="Version number for the series")
    is_active: bool = Field(default=True, index=True)
    is_latest: bool = Field(default=True, index=True, description="True if this is the latest version of the series")
    
    # Series metadata fields (moved from ValueData)
    is_derived: bool = Field(default=False, index=True, description="True if series contains derived/calculated values")
    derived_flag: Optional[str] = Field(default=None, max_length=50, description="Flag indicating derived data characteristics")
    dependency_calculation_id: Optional[int] = Field(default=None, foreign_key="calculation_log.calculation_id", index=True, description="FK to calculation log for derived series")
    field_name: Optional[str] = Field(default=None, max_length=255, description="Field name (alternative to flds_id, stored directly as string)")
    calculation_method: Optional[str] = Field(default=None, max_length=100, description="Method used to calculate derived values")
    data_quality_score: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(3, 2)), description="Overall data quality score for the series")
    source: Optional[dataSource] = Field(
        default=None,
        sa_column=Column(SQLEnum(dataSource, name="data_source", create_constraint=True ,native_enum=True)),
        description="Data source: raw or derived"
    )
    confidence_level: Optional[str] = Field(default=None, max_length=20, description="Confidence level for the series data")
    effective_date: Optional[datetime] = Field(default=None, description="Date when the series becomes effective")
    as_of_date: Optional[datetime] = Field(default=None, description="Date as of which the series metadata is current")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    asset_class: Optional["assetClassLookup"] = Relationship(back_populates="meta_series")
    sub_asset_class: Optional["subAssetClassLookup"] = Relationship(back_populates="meta_series")
    product_type: Optional["productTypeLookup"] = Relationship(back_populates="meta_series")
    data_type: Optional["dataTypeLookup"] = Relationship(back_populates="meta_series")
    structure_type: Optional["structureTypeLookup"] = Relationship(back_populates="meta_series")
    market_segment: Optional["marketSegmentLookup"] = Relationship(back_populates="meta_series")
    field_type: Optional["fieldTypeLookup"] = Relationship(back_populates="meta_series")
    # Note: value_data relationship removed - valueData is now in ClickHouse and cannot have SQLAlchemy relationships
    # Use the CRUD layer to query value_data from ClickHouse instead
    parent_dependencies: list["seriesDependencyGraph"] = Relationship(
        back_populates="parent_series",
        sa_relationship_kwargs={"foreign_keys": "seriesDependencyGraph.parent_series_id"}
    )
    child_dependencies: list["seriesDependencyGraph"] = Relationship(
        back_populates="child_series",
        sa_relationship_kwargs={"foreign_keys": "seriesDependencyGraph.child_series_id"}
    )
    calculations: list["calculationLog"] = Relationship(
        back_populates="derived_series",
        sa_relationship_kwargs={"foreign_keys": "calculationLog.derived_series_id"}
    )


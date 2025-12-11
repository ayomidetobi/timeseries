from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship, Column, Numeric
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import Integer, Index

if TYPE_CHECKING:
    from app.models.meta_series import metaSeries


class seriesDependencyGraph(SQLModel, table=True):
    """Series dependency graph table for tracking dependencies between series."""
    
    __tablename__ = "series_dependency_graph"
    __table_args__ = (
        # Composite indexes for common filter combinations
        Index("ix_dependency_parent_is_active", "parent_series_id", "is_active"),
        Index("ix_dependency_child_is_active", "child_series_id", "is_active"),
    )
    
    dependency_id: Optional[int] = Field(default=None, primary_key=True)
    parent_series_id: int = Field(foreign_key="meta_series.series_id", index=True)
    child_series_id: int = Field(foreign_key="meta_series.series_id", index=True)
    dependency_type: Optional[str] = Field(default=None, max_length=50, index=True)
    weight: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(3, 2)))
    formula: Optional[str] = None
    is_active: bool = Field(default=True, index=True)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    parent_series: "metaSeries" = Relationship(
        back_populates="parent_dependencies",
        sa_relationship_kwargs={"foreign_keys": "seriesDependencyGraph.parent_series_id"}
    )
    child_series: "metaSeries" = Relationship(
        back_populates="child_dependencies",
        sa_relationship_kwargs={"foreign_keys": "seriesDependencyGraph.child_series_id"}
    )


class calculationLog(SQLModel, table=True):
    """Calculation log table for tracking derived value calculations."""
    
    __tablename__ = "calculation_log"
    __table_args__ = (
        # Composite indexes for common filter combinations
        Index("ix_calculation_series_status", "derived_series_id", "calculation_status"),
        Index("ix_calculation_status_method", "calculation_status", "calculation_method"),
        Index("ix_calculation_series_method", "derived_series_id", "calculation_method"),
    )
    
    calculation_id: Optional[int] = Field(default=None, primary_key=True)
    derived_series_id: int = Field(foreign_key="meta_series.series_id", index=True)
    calculation_method: Optional[str] = Field(default=None, max_length=100, index=True)
    input_series_ids: Optional[list[int]] = Field(default=None, sa_column=Column(ARRAY(Integer)))
    calculation_parameters: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    calculation_status: Optional[str] = Field(default=None, max_length=50, index=True)
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    calculated_at: Optional[datetime] = Field(default=None, index=True)
    last_calculated: Optional[datetime] = None
    calculated_by: Optional[str] = Field(default=None, max_length=100)
    calculation_policy: Optional[str] = Field(default=None, max_length=50)
    
    # Relationships
    derived_series: "metaSeries" = Relationship(
        back_populates="calculations",
        sa_relationship_kwargs={"foreign_keys": "calculationLog.derived_series_id"}
    )
    # Note: derived_values relationship removed - ValueData is now in ClickHouse and cannot have SQLAlchemy relationships
    # Use the CRUD layer to query value_data from ClickHouse instead


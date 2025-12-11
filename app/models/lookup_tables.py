from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

if TYPE_CHECKING:
    from app.models.meta_series import metaSeries


class assetClassLookup(SQLModel, table=True):
    """Asset class lookup table."""
    
    __tablename__ = "asset_class_lookup"
    __table_args__ = (
        Index("ix_asset_class_lookup_name", "asset_class_name"),
    )
    
    asset_class_id: Optional[int] = Field(default=None, primary_key=True)
    asset_class_name: str = Field(index=True, max_length=255, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    meta_series: list["metaSeries"] = Relationship(back_populates="asset_class")
    sub_asset_classes: list["subAssetClassLookup"] = Relationship(back_populates="asset_class")


class productTypeLookup(SQLModel, table=True):
    """Product type lookup table."""
    
    __tablename__ = "product_type_lookup"
    __table_args__ = (
        Index("ix_product_type_lookup_name", "product_type_name"),

    )
    
    product_type_id: Optional[int] = Field(default=None, primary_key=True)
    product_type_name: str = Field(index=True, max_length=255, unique=True)
    description: Optional[str] = None
    is_derived: bool = Field(default=False, description="Whether this product type represents derived data")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    meta_series: list["metaSeries"] = Relationship(back_populates="product_type")


class subAssetClassLookup(SQLModel, table=True):
    """Sub-asset class lookup table."""
    
    __tablename__ = "sub_asset_class_lookup"
    __table_args__ = (
        Index("ix_sub_asset_class_lookup_name", "sub_asset_class_name"),
        Index("ix_sub_asset_class_lookup_asset_class", "asset_class_id"),
        Index("ix_sub_asset_class_lookup_asset_class_name", "asset_class_id", "sub_asset_class_name"),
    )
    
    sub_asset_class_id: Optional[int] = Field(default=None, primary_key=True)
    sub_asset_class_name: str = Field(index=True, max_length=255)
    asset_class_id: Optional[int] = Field(default=None, foreign_key="asset_class_lookup.asset_class_id", index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    asset_class: Optional["assetClassLookup"] = Relationship(back_populates="sub_asset_classes")
    meta_series: list["metaSeries"] = Relationship(back_populates="sub_asset_class")


class dataTypeLookup(SQLModel, table=True):
    """Data type lookup table."""
    
    __tablename__ = "data_type_lookup"
    __table_args__ = (
        Index("ix_data_type_lookup_name", "data_type_name"),
    )
    
    data_type_id: Optional[int] = Field(default=None, primary_key=True)
    data_type_name: str = Field(index=True, max_length=255, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    meta_series: list["metaSeries"] = Relationship(back_populates="data_type")


class structureTypeLookup(SQLModel, table=True):
    """Structure type lookup table."""
    
    __tablename__ = "structure_type_lookup"
    __table_args__ = (
        Index("ix_structure_type_lookup_name", "structure_type_name"),
    )
    
    structure_type_id: Optional[int] = Field(default=None, primary_key=True)
    structure_type_name: str = Field(index=True, max_length=255, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    meta_series: list["metaSeries"] = Relationship(back_populates="structure_type")


class marketSegmentLookup(SQLModel, table=True):
    """Market segment lookup table."""
    
    __tablename__ = "market_segment_lookup"
    __table_args__ = (
        Index("ix_market_segment_lookup_name", "market_segment_name"),
    )
    
    market_segment_id: Optional[int] = Field(default=None, primary_key=True)
    market_segment_name: str = Field(index=True, max_length=255, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    meta_series: list["metaSeries"] = Relationship(back_populates="market_segment")


class fieldTypeLookup(SQLModel, table=True):
    """Field type lookup table (FLDS)."""
    
    __tablename__ = "field_type_lookup"
    __table_args__ = (
        Index("ix_field_type_lookup_name", "field_type_name"),
    )
    
    field_type_id: Optional[int] = Field(default=None, primary_key=True)
    field_type_name: str = Field(index=True, max_length=255, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    meta_series: list["metaSeries"] = Relationship(back_populates="field_type")


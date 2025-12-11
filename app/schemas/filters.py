"""Filter schemas for API endpoints using fastapi-filter."""
from typing import Optional
from datetime import date, datetime
from fastapi_filter.contrib.sqlalchemy import Filter

from app.models.meta_series import metaSeries
from app.models.value_data import valueData
from app.models.dependency import seriesDependencyGraph, calculationLog
from app.models.lookup_tables import assetClassLookup, productTypeLookup


class metaSeriesFilter(Filter):
    """Filter schema for MetaSeries queries."""
    
    is_active: Optional[bool] = None
    is_derived: Optional[bool] = None
    asset_class_id: Optional[int] = None
    asset_class_id__in: Optional[list[int]] = None
    product_type_id: Optional[int] = None
    product_type_id__in: Optional[list[int]] = None
    sub_asset_class_id: Optional[int] = None
    sub_asset_class_id__in: Optional[list[int]] = None
    data_type_id: Optional[int] = None
    data_type_id__in: Optional[list[int]] = None
    structure_type_id: Optional[int] = None
    structure_type_id__in: Optional[list[int]] = None
    market_segment_id: Optional[int] = None
    market_segment_id__in: Optional[list[int]] = None
    ticker__ilike: Optional[str] = None
    series_name__ilike: Optional[str] = None
    series_name__in: Optional[list[str]] = None
    
    order_by: Optional[list[str]] = None
    
    class Constants:
        model = metaSeries
        ordering_field_name = "order_by"


class valueDataFilter(Filter):
    """Filter schema for ValueData queries with support for filtering by MetaSeries and lookup tables."""
    
    # Direct ValueData filters
    series_id: Optional[int] = None
    series_id__in: Optional[list[int]] = None
    timestamp__gte: Optional[date] = None
    timestamp__lte: Optional[date] = None
    timestamp__ago: Optional[str] = None  # Humanized time string (e.g., "1y", "2y", "20m", "6mo") - interpreted as "X ago from now"
    is_latest: Optional[bool] = None
    value__gte: Optional[float] = None
    value__lte: Optional[float] = None
    
    # MetaSeries filters (via join)
    series_name__ilike: Optional[str] = None
    series_name__in: Optional[list[str]] = None
    ticker__ilike: Optional[str] = None
    is_active: Optional[bool] = None
    is_derived: Optional[bool] = None
    
    # Lookup table filters (via MetaSeries join) - using names as primary keys for filtering
    asset_class_name: Optional[str] = None
    asset_class_name__in: Optional[list[str]] = None
    sub_asset_class_name: Optional[str] = None
    sub_asset_class_name__in: Optional[list[str]] = None
    product_type_name: Optional[str] = None
    product_type_name__in: Optional[list[str]] = None
    data_type_name: Optional[str] = None
    data_type_name__in: Optional[list[str]] = None
    structure_type_name: Optional[str] = None
    structure_type_name__in: Optional[list[str]] = None
    market_segment_name: Optional[str] = None
    market_segment_name__in: Optional[list[str]] = None
    field_type_name: Optional[str] = None
    field_type_name__in: Optional[list[str]] = None
    
    order_by: Optional[list[str]] = None
    
    class Constants:
        model = valueData
        ordering_field_name = "order_by"


class dependencyFilter(Filter):
    """Filter schema for SeriesDependencyGraph queries."""
    
    parent_series_id: Optional[int] = None
    parent_series_id__in: Optional[list[int]] = None
    child_series_id: Optional[int] = None
    child_series_id__in: Optional[list[int]] = None
    is_active: Optional[bool] = True
    dependency_type: Optional[str] = None
    dependency_type__in: Optional[list[str]] = None
    
    order_by: Optional[list[str]] = None
    
    class Constants:
        model = seriesDependencyGraph
        ordering_field_name = "order_by"


class calculationFilter(Filter):
    """Filter schema for CalculationLog queries."""
    
    derived_series_id: Optional[int] = None
    derived_series_id__in: Optional[list[int]] = None
    calculation_status: Optional[str] = None
    calculation_status__in: Optional[list[str]] = None
    calculation_method: Optional[str] = None
    calculation_method__in: Optional[list[str]] = None
    calculated_at__gte: Optional[datetime] = None
    calculated_at__lte: Optional[datetime] = None
    
    order_by: Optional[list[str]] = None
    
    class Constants:
        model = calculationLog
        ordering_field_name = "order_by"


class assetClassFilter(Filter):
    """Filter schema for AssetClassLookup queries."""
    
    asset_class_id: Optional[int] = None
    asset_class_id__in: Optional[list[int]] = None
    asset_class_name__ilike: Optional[str] = None
    
    order_by: Optional[list[str]] = None
    
    class Constants:
        model = assetClassLookup
        ordering_field_name = "order_by"


class productTypeFilter(Filter):
    """Filter schema for ProductTypeLookup queries."""
    
    product_type_id: Optional[int] = None
    product_type_id__in: Optional[list[int]] = None
    product_type_name__ilike: Optional[str] = None
    is_derived: Optional[bool] = None
    
    order_by: Optional[list[str]] = None
    
    class Constants:
        model = productTypeLookup
        ordering_field_name = "order_by"

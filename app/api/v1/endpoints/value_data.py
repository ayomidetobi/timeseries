"""Value data endpoints."""
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.clickhouse_conn import _clickhouse_connection_manager
from app.models.value_data import valueDataResponse, valueDataWithMetadataResponse, valueDataCombinedResponse, valueData
from app.models.meta_series import metaSeries
from app.schemas.filters import valueDataFilter
from app.crud.value_data import get_crud_value_data

router = APIRouter()


@router.get("/", response_model=List[valueDataCombinedResponse])
async def get_value_data(
    filters: valueDataFilter = FilterDepends(valueDataFilter),
    session: AsyncSession = Depends(get_session),
):
    """
    Get value data with comprehensive filtering options and full metadata.
    
    Returns value data grouped by metadata:
    - metadata: Contains series information and all lookup table names (without timestamp)
    - value_data: Array of all value data records (timestamp and value) for this metadata
    
    The response groups all value data records by their metadata (series_id), so each metadata entry
    contains an array of all its value data records.
    
    Filters available:
    - Direct valueData: series_id, timestamp__gte, timestamp__lte, timestamp__ago, is_latest, value__gte, value__lte
    - timestamp__ago: Humanized time string (e.g., "1y", "2y", "20m", "6mo", "1w") - filters data from X time ago to now
    - metaSeries: series_name__ilike, ticker__ilike, is_active, is_derived
    - Lookup tables (by name): asset_class_name, sub_asset_class_name, product_type_name, data_type_name,
      structure_type_name, market_segment_name, field_type_name
    - All lookup table filters support __in for multiple values (e.g., asset_class_name__in)
    - Use order_by parameter for sorting (e.g., order_by=["-timestamp", "series_id"])
    
    Examples:
    - ?timestamp__ago=1y (data from 1 year ago to now)
    - ?timestamp__ago=6mo (data from 6 months ago to now)
    - ?timestamp__ago=20m (data from 20 minutes ago to now)
    - ?asset_class_name=Commodity (filter by asset class name)
    - ?product_type_name__in=Spot,Forward (filter by multiple product type names)
    
    Response structure:
    [
      {
        "metadata": {
          "series_id": 1,
          "series_name": "Gold Spot Price",
          "ticker": "XAU Curncy",
          "asset_class_name": "Commodity",
          ...
        },
        "value_data": [
          {"timestamp": "2025-01-01", "value": "100.5"},
          {"timestamp": "2025-01-02", "value": "101.2"},
          ...
        ]
      },
      ...
    ]
    """
    # Validate series_name filters - at least one is required and must have a valid value
    has_ilike = filters.series_name__ilike is not None
    has_in = filters.series_name__in is not None
    
    # Check if at least one filter is provided
    if not (has_ilike or has_in):
        raise HTTPException(
            status_code=400,
            detail="At least one of series_name__ilike or series_name__in is required. Series names are required."
        )
    
    # Check if at least one has a valid value
    ilike_valid = has_ilike and filters.series_name__ilike and filters.series_name__ilike.strip()
    in_valid = has_in and filters.series_name__in and any(name and name.strip() for name in filters.series_name__in)
    
    if not (ilike_valid or in_valid):
        raise HTTPException(
            status_code=400,
            detail="At least one of series_name__ilike or series_name__in must have a valid value. Series names are required."
        )
    
    # Get ClickHouse client and CRUD instance
    if not _clickhouse_connection_manager.is_initialized() or _clickhouse_connection_manager.client is None:
        raise HTTPException(status_code=503, detail="ClickHouse not available")
    
    clickhouse_client = _clickhouse_connection_manager.client
    crud_ch = get_crud_value_data(clickhouse_client)
    value_data_list = await crud_ch.get_multi_with_filters(db=session, filter_obj=filters)
    
    # Get metadata for all series_ids found
    series_ids = list(set(getattr(vd, 'series_id', None) for vd in value_data_list if getattr(vd, 'series_id', None) is not None))  # type: ignore
    if not series_ids:
        return []
    
    # Query PostgreSQL for metadata
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    
    if not series_ids:
        return []
    
    metadata_query = select(metaSeries).where(metaSeries.series_id.in_(series_ids)).options(
        joinedload(metaSeries.asset_class),
        joinedload(metaSeries.sub_asset_class),
        joinedload(metaSeries.product_type),
        joinedload(metaSeries.data_type),
        joinedload(metaSeries.structure_type),
        joinedload(metaSeries.market_segment),
        joinedload(metaSeries.field_type),
    )
    metadata_result = await session.execute(metadata_query)
    metadata_dict = {series.series_id: series for series in metadata_result.scalars().unique().all()}
    
    # Group value data by metadata (series_id)
    # Use a dictionary to group by series_id
    grouped_data: dict[int, dict] = {}
    
    for vd in value_data_list:
        # Get series metadata from PostgreSQL query result
        # Access series_id attribute from valueData (works at runtime)
        series_id = getattr(vd, 'series_id', None)  # type: ignore
        if series_id is None:
            continue
        series = metadata_dict.get(series_id)  # type: ignore
        
        # If this is the first time we see this series_id, create the metadata entry
        if series_id not in grouped_data:
            grouped_data[series_id] = {
                'metadata': valueDataWithMetadataResponse(
                    series_id=series_id,  # type: ignore
                    series_name=series.series_name if series else "",
                    ticker=series.ticker if series else None,
                    is_active=series.is_active if series else False,
                    is_derived=series.is_derived if series else False,
                    # Fields moved from valueData to metaSeries
                    is_latest=getattr(series, 'is_latest', True) if series else True,  # type: ignore
                    version_number=getattr(series, 'version_number', 1) if series else 1,  # type: ignore
                    derived_flag=getattr(series, 'derived_flag', None) if series else None,  # type: ignore
                    dependency_calculation_id=getattr(series, 'dependency_calculation_id', None) if series else None,  # type: ignore
                    field_name=getattr(series, 'field_name', None) if series else None,  # type: ignore
                    asset_class_name=series.asset_class.asset_class_name if series and series.asset_class else None,
                    sub_asset_class_name=series.sub_asset_class.sub_asset_class_name if series and series.sub_asset_class else None,
                    product_type_name=series.product_type.product_type_name if series and series.product_type else None,
                    data_type_name=series.data_type.data_type_name if series and series.data_type else None,
                    structure_type_name=series.structure_type.structure_type_name if series and series.structure_type else None,
                    market_segment_name=series.market_segment.market_segment_name if series and series.market_segment else None,
                    field_type_name=series.field_type.field_type_name if series and series.field_type else None,
                ),
                'value_data_list': []
            }
        
        # Add this value_data record to the list for this series
        grouped_data[series_id]['value_data_list'].append(
            valueDataResponse(
                timestamp=getattr(vd, 'timestamp', None),  # type: ignore
                value=getattr(vd, 'value', None),  # type: ignore
            )
        )
    
    # Convert grouped data to response format
    result = []
    for series_id, data in grouped_data.items():
        result.append(valueDataCombinedResponse(
            meta_series_data=data['metadata'],
            value_data=data['value_data_list'],
        ))
    
    return result


@router.get("/{series_id}/{timestamp}", response_model=valueDataResponse)
async def get_value_data_by_date(
    series_id: int,
    timestamp: date,
    session: AsyncSession = Depends(get_session),
):
    """Get value data for a specific series and timestamp."""
    if not _clickhouse_connection_manager.is_initialized() or _clickhouse_connection_manager.client is None:
        raise HTTPException(status_code=503, detail="ClickHouse not available")
    
    clickhouse_client = _clickhouse_connection_manager.client
    crud_ch = get_crud_value_data(clickhouse_client)
    value = await crud_ch.get_by_id(
        series_id=series_id,
        timestamp=timestamp,
    )
    if not value:
        raise HTTPException(status_code=404, detail="Value data not found")
    return valueDataResponse(timestamp=value.timestamp, value=value.value)


@router.post("/", response_model=valueDataResponse, status_code=201)
async def create_value_data(
    value_data: valueDataResponse,
    session: AsyncSession = Depends(get_session),
):
    """Create new value data."""
    if not _clickhouse_connection_manager.is_initialized() or _clickhouse_connection_manager.client is None:
        raise HTTPException(status_code=503, detail="ClickHouse not available")
    
    clickhouse_client = _clickhouse_connection_manager.client
    crud_ch = get_crud_value_data(clickhouse_client)
    
    # Convert valueDataResponse to valueData model for insertion
    # Note: This is a simplified version - you may need to provide additional fields
    value_data_obj = valueData(
        series_id=0,  # This should come from the request or be derived
        timestamp=value_data.timestamp,
        field_name="",  # This should come from the request
        value=value_data.value,
    )
    return await crud_ch.create_with_validation(db=session, obj_in=value_data_obj)


@router.put("/{series_id}/{timestamp}", response_model=valueDataResponse)
async def update_value_data(
    series_id: int,
    timestamp: date,
    value_data_update: valueDataResponse,
    session: AsyncSession = Depends(get_session),
):
    """Update value data."""
    if not _clickhouse_connection_manager.is_initialized() or _clickhouse_connection_manager.client is None:
        raise HTTPException(status_code=503, detail="ClickHouse not available")
    
    clickhouse_client = _clickhouse_connection_manager.client
    crud_ch = get_crud_value_data(clickhouse_client)
    value_data = await crud_ch.get_by_id(
        series_id=series_id,
        timestamp=timestamp,
    )
    if not value_data:
        raise HTTPException(status_code=404, detail="Value data not found")
    
    # Exclude primary keys from update
    update_dict = value_data_update.model_dump(
        exclude_unset=True,
        exclude={"series_id", "timestamp"},
    )
    return await crud_ch.update(
        series_id=series_id,
        timestamp=timestamp,
        obj_in=update_dict,
    )


@router.get("/derived/", response_model=List[valueDataResponse])
async def get_derived_value_data(
    filters: valueDataFilter = FilterDepends(valueDataFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get derived value data for a specific series (filters by is_derived=True)."""
    if not _clickhouse_connection_manager.is_initialized() or _clickhouse_connection_manager.client is None:
        raise HTTPException(status_code=503, detail="ClickHouse not available")
    
    clickhouse_client = _clickhouse_connection_manager.client
    crud_ch = get_crud_value_data(clickhouse_client)
    value_data_list = await crud_ch.get_derived(db=session, filter_obj=filters)
    return [valueDataResponse(timestamp=vd.timestamp, value=vd.value) for vd in value_data_list]

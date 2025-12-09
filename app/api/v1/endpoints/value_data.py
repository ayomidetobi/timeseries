"""Value data endpoints."""
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.value_data import ValueData, ValueDataResponse, ValueDataWithMetadataResponse, ValueDataCombinedResponse
from app.schemas.filters import ValueDataFilter
from app.crud.value_data import crud_value_data

router = APIRouter()


@router.get("/", response_model=List[ValueDataCombinedResponse])
async def get_value_data(
    filters: ValueDataFilter = FilterDepends(ValueDataFilter),
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
    - Direct ValueData: series_id, timestamp__gte, timestamp__lte, timestamp__ago, is_latest, value__gte, value__lte
    - timestamp__ago: Humanized time string (e.g., "1y", "2y", "20m", "6mo", "1w") - filters data from X time ago to now
    - MetaSeries: series_name__ilike, ticker__ilike, is_active, is_derived
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
    value_data_list = await crud_value_data.get_multi_with_filters(db=session, filter_obj=filters)
    
    # Group value data by metadata (series_id)
    # Use a dictionary to group by series_id
    grouped_data: dict[int, dict] = {}
    
    for vd in value_data_list:
        # Access the series relationship (should be loaded via eager loading)
        series = vd.series if hasattr(vd, 'series') and vd.series else None
        
        series_id = vd.series_id
        
        # If this is the first time we see this series_id, create the metadata entry
        if series_id not in grouped_data:
            grouped_data[series_id] = {
                'metadata': ValueDataWithMetadataResponse(
                    series_id=series_id,
                    series_name=series.series_name if series else "",
                    ticker=series.ticker if series else None,
                    is_active=series.is_active if series else False,
                    is_derived=series.is_derived if series else False,
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
            ValueDataResponse(
                timestamp=vd.timestamp,
                value=vd.value,
            )
        )
    
    # Convert grouped data to response format
    result = []
    for series_id, data in grouped_data.items():
        result.append(ValueDataCombinedResponse(
            meta_series_data=data['metadata'],
            value_data=data['value_data_list'],
        ))
    
    return result


@router.get("/{series_id}/{timestamp}", response_model=ValueDataResponse)
async def get_value_data_by_date(
    series_id: int,
    timestamp: date,
    session: AsyncSession = Depends(get_session),
):
    """Get value data for a specific series and timestamp."""
    value = await crud_value_data.get_by_id(
        db=session,
        series_id=series_id,
        timestamp=timestamp,
    )
    if not value:
        raise HTTPException(status_code=404, detail="Value data not found")
    return ValueDataResponse(timestamp=value.timestamp, value=value.value)


@router.post("/", response_model=ValueData, status_code=201)
async def create_value_data(
    value_data: ValueData,
    session: AsyncSession = Depends(get_session),
):
    """Create new value data."""
    try:
        return await crud_value_data.create_with_validation(db=session, obj_in=value_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{series_id}/{timestamp}", response_model=ValueData)
async def update_value_data(
    series_id: int,
    timestamp: date,
    value_data_update: ValueData,
    session: AsyncSession = Depends(get_session),
):
    """Update value data."""
    value_data = await crud_value_data.get_by_id(
        db=session,
        series_id=series_id,
        timestamp=timestamp,
    )
    if not value_data:
        raise HTTPException(status_code=404, detail="Value data not found")
    
    # Exclude primary keys from update
    update_dict = value_data_update.dict(
        exclude_unset=True,
        exclude={"series_id", "timestamp"},
    )
    return await crud_value_data.update(db=session, db_obj=value_data, obj_in=update_dict)


@router.get("/derived/", response_model=List[ValueDataResponse])
async def get_derived_value_data(
    filters: ValueDataFilter = FilterDepends(ValueDataFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get derived value data for a specific series (filters by is_derived=True)."""
    value_data_list = await crud_value_data.get_derived(db=session, filter_obj=filters)
    return [ValueDataResponse(timestamp=vd.timestamp, value=vd.value) for vd in value_data_list]

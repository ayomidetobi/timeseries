"""Meta series endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.meta_series import MetaSeries
from app.schemas.filters import MetaSeriesFilter
from app.crud.meta_series import crud_meta_series

router = APIRouter()


@router.get("/", response_model=List[MetaSeries])
async def get_meta_series(
    filters: MetaSeriesFilter = FilterDepends(MetaSeriesFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get list of meta series with optional filters."""
    return await crud_meta_series.get_multi_with_filters(db=session, filter_obj=filters)


@router.get("/{series_id}", response_model=MetaSeries)
async def get_meta_series_by_id(
    series_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific meta series by ID."""
    series = await crud_meta_series.get_by_id(db=session, series_id=series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Meta series not found")
    return series


@router.post("/", response_model=MetaSeries, status_code=201)
async def create_meta_series(
    series: MetaSeries,
    session: AsyncSession = Depends(get_session),
):
    """Create a new meta series."""
    return await crud_meta_series.create(db=session, obj_in=series)


@router.put("/{series_id}", response_model=MetaSeries)
async def update_meta_series(
    series_id: int,
    series_update: MetaSeries,
    session: AsyncSession = Depends(get_session),
):
    """Update an existing meta series."""
    series = await crud_meta_series.get_by_id(db=session, series_id=series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Meta series not found")
    return await crud_meta_series.update(db=session, db_obj=series, obj_in=series_update)


@router.delete("/{series_id}", status_code=204)
async def delete_meta_series(
    series_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a meta series (soft delete by setting is_active=False)."""
    series = await crud_meta_series.soft_delete(db=session, series_id=series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Meta series not found")
    return None

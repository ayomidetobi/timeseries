"""Dependencies endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.dependency import SeriesDependencyGraph, CalculationLog
from app.schemas.filters import DependencyFilter, CalculationFilter
from app.crud.dependencies import crud_dependency, crud_calculation

router = APIRouter()


@router.get("/dependencies/", response_model=List[SeriesDependencyGraph])
async def get_dependencies(
    filters: DependencyFilter = FilterDepends(DependencyFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get list of series dependencies."""
    return await crud_dependency.get_multi_with_filters(db=session, filter_obj=filters)


@router.post("/dependencies/", response_model=SeriesDependencyGraph, status_code=201)
async def create_dependency(
    dependency: SeriesDependencyGraph,
    session: AsyncSession = Depends(get_session),
):
    """Create a new series dependency."""
    return await crud_dependency.create(db=session, obj_in=dependency)


@router.get("/calculations/", response_model=List[CalculationLog])
async def get_calculations(
    filters: CalculationFilter = FilterDepends(CalculationFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get list of calculation logs."""
    return await crud_calculation.get_multi_with_filters(db=session, filter_obj=filters)


@router.get("/calculations/{calculation_id}", response_model=CalculationLog)
async def get_calculation_by_id(
    calculation_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific calculation log by ID."""
    calculation = await crud_calculation.get_by_id(
        db=session,
        calculation_id=calculation_id,
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation log not found")
    return calculation


@router.post("/calculations/", response_model=CalculationLog, status_code=201)
async def create_calculation(
    calculation: CalculationLog,
    session: AsyncSession = Depends(get_session),
):
    """Create a new calculation log."""
    return await crud_calculation.create(db=session, obj_in=calculation)


"""CRUD operations for dependencies."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.dependency import SeriesDependencyGraph, CalculationLog
from app.schemas.filters import DependencyFilter, CalculationFilter


class CRUDDependency(CRUDBase[SeriesDependencyGraph]):
    """CRUD operations for SeriesDependencyGraph."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        dependency_id: int,
    ) -> Optional[SeriesDependencyGraph]:
        """Get a dependency by dependency_id."""
        query = select(SeriesDependencyGraph).where(
            SeriesDependencyGraph.dependency_id == dependency_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: DependencyFilter,
    ) -> list[SeriesDependencyGraph]:
        """Get multiple dependencies with filters."""
        query = select(SeriesDependencyGraph)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


class CRUDCalculation(CRUDBase[CalculationLog]):
    """CRUD operations for CalculationLog."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        calculation_id: int,
    ) -> Optional[CalculationLog]:
        """Get a calculation log by calculation_id."""
        query = select(CalculationLog).where(
            CalculationLog.calculation_id == calculation_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: CalculationFilter,
    ) -> list[CalculationLog]:
        """Get multiple calculation logs with filters."""
        query = select(CalculationLog)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Create instances
crud_dependency = CRUDDependency(SeriesDependencyGraph)
crud_calculation = CRUDCalculation(CalculationLog)

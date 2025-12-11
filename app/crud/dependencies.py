"""CRUD operations for dependencies."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import crudBase
from app.models.dependency import seriesDependencyGraph, calculationLog
from app.schemas.filters import dependencyFilter, calculationFilter


class crudDependency(crudBase[seriesDependencyGraph]):
    """CRUD operations for SeriesDependencyGraph."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        dependency_id: int,
    ) -> Optional[seriesDependencyGraph]:
        """Get a dependency by dependency_id."""
        query = select(seriesDependencyGraph).where(
            seriesDependencyGraph.dependency_id == dependency_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: dependencyFilter,
    ) -> list[seriesDependencyGraph]:
        """Get multiple dependencies with filters."""
        query = select(seriesDependencyGraph)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


class crudCalculation(crudBase[calculationLog]):
    """CRUD operations for CalculationLog."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        calculation_id: int,
    ) -> Optional[calculationLog]:
        """Get a calculation log by calculation_id."""
        query = select(calculationLog).where(
            calculationLog.calculation_id == calculation_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: calculationFilter,
    ) -> list[calculationLog]:
        """Get multiple calculation logs with filters."""
        query = select(calculationLog)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Create instances
crud_dependency = crudDependency(seriesDependencyGraph)
crud_calculation = crudCalculation(calculationLog)

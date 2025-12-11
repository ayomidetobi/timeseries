"""CRUD operations for MetaSeries."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import crudBase
from app.models.meta_series import metaSeries
from app.schemas.filters import metaSeriesFilter


class crudMetaSeries(crudBase[metaSeries]):
    """CRUD operations for MetaSeries."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        series_id: int,
    ) -> Optional[metaSeries]:
        """Get a meta series by series_id."""
        query = select(metaSeries).where(metaSeries.series_id == series_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: metaSeriesFilter,
    ) -> list[metaSeries]:
        """Get multiple meta series with filters."""
        query = select(metaSeries)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def soft_delete(
        self,
        db: AsyncSession,
        *,
        series_id: int,
    ) -> Optional[metaSeries]:
        """Soft delete a meta series by setting is_active=False."""
        series = await self.get_by_id(db, series_id=series_id)
        if series:
            series.is_active = False
            db.add(series)
            await db.commit()
            await db.refresh(series)
        return series


# Create instance
crud_meta_series = crudMetaSeries(metaSeries)

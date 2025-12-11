"""CRUD operations for lookup tables."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import crudBase
from app.models.lookup_tables import assetClassLookup, productTypeLookup
from app.schemas.filters import assetClassFilter, productTypeFilter


class crudAssetClass(crudBase[assetClassLookup]):
    """CRUD operations for AssetClassLookup."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        asset_class_id: int,
    ) -> Optional[assetClassLookup]:
        """Get an asset class by asset_class_id."""
        query = select(assetClassLookup).where(
            assetClassLookup.asset_class_id == asset_class_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: assetClassFilter,
    ) -> list[assetClassLookup]:
        """Get multiple asset classes with filters."""
        query = select(assetClassLookup)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


class crudProductType(crudBase[productTypeLookup]):
    """CRUD operations for ProductTypeLookup."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        product_type_id: int,
    ) -> Optional[productTypeLookup]:
        """Get a product type by product_type_id."""
        query = select(productTypeLookup).where(
            productTypeLookup.product_type_id == product_type_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: productTypeFilter,
    ) -> list[productTypeLookup]:
        """Get multiple product types with filters."""
        query = select(productTypeLookup)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Create instances
crud_asset_class = crudAssetClass(assetClassLookup)
crud_product_type = crudProductType(productTypeLookup)

"""CRUD operations for lookup tables."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.lookup_tables import AssetClassLookup, ProductTypeLookup
from app.schemas.filters import AssetClassFilter, ProductTypeFilter


class CRUDAssetClass(CRUDBase[AssetClassLookup]):
    """CRUD operations for AssetClassLookup."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        asset_class_id: int,
    ) -> Optional[AssetClassLookup]:
        """Get an asset class by asset_class_id."""
        query = select(AssetClassLookup).where(
            AssetClassLookup.asset_class_id == asset_class_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: AssetClassFilter,
    ) -> list[AssetClassLookup]:
        """Get multiple asset classes with filters."""
        query = select(AssetClassLookup)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


class CRUDProductType(CRUDBase[ProductTypeLookup]):
    """CRUD operations for ProductTypeLookup."""

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        product_type_id: int,
    ) -> Optional[ProductTypeLookup]:
        """Get a product type by product_type_id."""
        query = select(ProductTypeLookup).where(
            ProductTypeLookup.product_type_id == product_type_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filter_obj: ProductTypeFilter,
    ) -> list[ProductTypeLookup]:
        """Get multiple product types with filters."""
        query = select(ProductTypeLookup)
        
        # Apply fastapi-filter filters
        query = filter_obj.filter(query)
        query = filter_obj.sort(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Create instances
crud_asset_class = CRUDAssetClass(AssetClassLookup)
crud_product_type = CRUDProductType(ProductTypeLookup)

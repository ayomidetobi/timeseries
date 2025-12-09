"""Lookup tables endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.lookup_tables import AssetClassLookup, ProductTypeLookup
from app.schemas.filters import AssetClassFilter, ProductTypeFilter
from app.crud.lookup_tables import crud_asset_class, crud_product_type

router = APIRouter()


@router.get("/asset-classes/", response_model=List[AssetClassLookup])
async def get_asset_classes(
    filters: AssetClassFilter = FilterDepends(AssetClassFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get list of asset classes."""
    return await crud_asset_class.get_multi_with_filters(db=session, filter_obj=filters)


@router.get("/asset-classes/{asset_class_id}", response_model=AssetClassLookup)
async def get_asset_class_by_id(
    asset_class_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific asset class by ID."""
    asset_class = await crud_asset_class.get_by_id(
        db=session,
        asset_class_id=asset_class_id,
    )
    if not asset_class:
        raise HTTPException(status_code=404, detail="Asset class not found")
    return asset_class


@router.post("/asset-classes/", response_model=AssetClassLookup, status_code=201)
async def create_asset_class(
    asset_class: AssetClassLookup,
    session: AsyncSession = Depends(get_session),
):
    """Create a new asset class."""
    return await crud_asset_class.create(db=session, obj_in=asset_class)


@router.get("/product-types/", response_model=List[ProductTypeLookup])
async def get_product_types(
    filters: ProductTypeFilter = FilterDepends(ProductTypeFilter),
    session: AsyncSession = Depends(get_session),
):
    """Get list of product types."""
    return await crud_product_type.get_multi_with_filters(db=session, filter_obj=filters)


@router.get("/product-types/{product_type_id}", response_model=ProductTypeLookup)
async def get_product_type_by_id(
    product_type_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific product type by ID."""
    product_type = await crud_product_type.get_by_id(
        db=session,
        product_type_id=product_type_id,
    )
    if not product_type:
        raise HTTPException(status_code=404, detail="Product type not found")
    return product_type


@router.post("/product-types/", response_model=ProductTypeLookup, status_code=201)
async def create_product_type(
    product_type: ProductTypeLookup,
    session: AsyncSession = Depends(get_session),
):
    """Create a new product type."""
    return await crud_product_type.create(db=session, obj_in=product_type)


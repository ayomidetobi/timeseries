"""CRUD operations for the application."""
from app.crud.base import crudBase
from app.crud.meta_series import crud_meta_series
from app.crud.dependencies import crud_dependency, crud_calculation
from app.crud.lookup_tables import crud_asset_class, crud_product_type

__all__ = [
    "crudBase",
    "crud_meta_series",
    "crud_dependency",
    "crud_calculation",
    "crud_asset_class",
    "crud_product_type",
]


"""CRUD operations for the application."""
from app.crud.base import CRUDBase
from app.crud.meta_series import crud_meta_series
from app.crud.value_data import crud_value_data
from app.crud.dependencies import crud_dependency, crud_calculation
from app.crud.lookup_tables import crud_asset_class, crud_product_type

__all__ = [
    "CRUDBase",
    "crud_meta_series",
    "crud_value_data",
    "crud_dependency",
    "crud_calculation",
    "crud_asset_class",
    "crud_product_type",
]


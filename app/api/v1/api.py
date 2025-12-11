from fastapi import APIRouter
from app.api.v1.endpoints import (
    meta_series,
    value_data,
    lookup_tables,
    dependencies,
    system,
)

api_router = APIRouter()

api_router.include_router(system.router, tags=["system"])
api_router.include_router(
    meta_series.router, prefix="/meta-series", tags=["meta-series"]
)
api_router.include_router(value_data.router, prefix="/value-data", tags=["value-data"])
api_router.include_router(lookup_tables.router, prefix="/lookup", tags=["lookup"])
api_router.include_router(
    dependencies.router, prefix="/dependencies", tags=["dependencies"]
)

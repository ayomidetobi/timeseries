"""Filter utilities for querying."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class FilterBase(BaseModel):
    """Base filter class with common pagination and ordering."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of records to return"
    )
    order_by: Optional[str] = Field(default=None, description="Field to order by")
    order: Optional[str] = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"
    )

    class Config:
        populate_by_name = True


def apply_filter(
    query: Any,
    model: Any,
    filter_obj: FilterBase,
    additional_filters: Optional[dict[str, Any]] = None,
) -> Any:
    """Apply filters to a SQLAlchemy query.

    Args:
        query: SQLAlchemy select query
        model: SQLModel class
        filter_obj: Filter object with filter criteria
        additional_filters: Additional filter conditions as dict

    Returns:
        Filtered and ordered query
    """
    # Apply additional filters
    if additional_filters:
        for field, value in additional_filters.items():
            if value is not None and hasattr(model, field):
                column = getattr(model, field)
                if isinstance(value, (list, tuple)):
                    query = query.where(column.in_(value))
                else:
                    query = query.where(column == value)

    # Apply ordering
    if filter_obj.order_by and hasattr(model, filter_obj.order_by):
        column = getattr(model, filter_obj.order_by)
        if filter_obj.order == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # Apply pagination
    query = query.offset(filter_obj.skip).limit(filter_obj.limit)

    return query

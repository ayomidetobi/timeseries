"""Base CRUD operations."""

from typing import Any, Generic, Optional, TypeVar, Type
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class crudBase(Generic[ModelType]):
    """Base class for CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**
        * `model`: A SQLModel class
        """
        self.model = model

    async def get(
        self, db: AsyncSession, id: Any, id_field: str = "id"
    ) -> Optional[ModelType]:
        """Get a single record by ID."""
        if not hasattr(self.model, id_field):
            raise ValueError(
                f"Model {self.model.__name__} does not have field {id_field}"
            )
        query = select(self.model).where(getattr(self.model, id_field) == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Get multiple records with pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ModelType | dict[str, Any],
    ) -> ModelType:
        """Create a new record."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: ModelType | dict[str, Any],
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # Update updated_at timestamp if field exists
        if hasattr(db_obj, "updated_at"):
            db_obj.updated_at = datetime.utcnow()

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self, db: AsyncSession, *, id: Any, id_field: str = "id"
    ) -> Optional[ModelType]:
        """Delete a record by ID."""
        obj = await self.get(db, id, id_field=id_field)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

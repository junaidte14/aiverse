"""
Base repository with common CRUD operations

All repositories should inherit from this base class
"""

from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common database operations

    Provides CRUD operations for any SQLAlchemy model
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository

        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record

        Args:
            **kwargs: Model attributes

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get record by ID

        Args:
            id: Record ID

        Returns:
            Model instance if found, None otherwise
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """
        Get all records with optional filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Field filters

        Returns:
            List of model instances
        """
        query = select(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update record by ID

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance if found, None otherwise
        """
        # Remove None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            return await self.get_by_id(id)

        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**update_data)
        )
        await self.session.flush()

        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        """
        Delete record by ID

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def count(self, **filters) -> int:
        """
        Count records with optional filtering

        Args:
            **filters: Field filters

        Returns:
            Number of records
        """
        from sqlalchemy import func

        query = select(func.count(self.model.id))

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """
        Check if record exists

        Args:
            **filters: Field filters

        Returns:
            True if exists, False otherwise
        """
        count = await self.count(**filters)
        return count > 0

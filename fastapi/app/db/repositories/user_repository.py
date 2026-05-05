"""
User repository

Data access layer for User model
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.db.models.user import User, UserRole


class UserRepository(BaseRepository[User]):
    """
    User repository

    Handles all database operations for users
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            username: Username to search for

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: Email to search for

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_role(
        self, role: UserRole, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """
        Get users by role

        Args:
            role: User role to filter by
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of users with specified role
        """
        result = await self.session.execute(
            select(User).where(User.role == role).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get active users

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of active users
        """
        result = await self.session.execute(
            select(User).where(User.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: int) -> Optional[User]:
        """
        Update user's last login timestamp

        Args:
            user_id: User ID

        Returns:
            Updated user
        """
        from datetime import datetime

        return await self.update(user_id, last_login=datetime.utcnow())

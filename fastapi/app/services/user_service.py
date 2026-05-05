"""
User service - Business logic for user operations

Updated with new security module
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.user_repository import UserRepository
from app.db.models.user import User, UserRole
from app.models.user import UserCreate, UserUpdate
from app.core.exceptions import UserNotFoundException, UserAlreadyExistsException
from app.core.security import hash_password, verify_password


class UserService:
    """
    User service class

    Handles all user-related business logic with database operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session

        Args:
            db: Database session
        """
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            UserAlreadyExistsException: If username or email already exists
        """
        if await self.repository.get_by_username(user_data.username):
            raise UserAlreadyExistsException("username", user_data.username)
        if await self.repository.get_by_email(user_data.email):
            raise UserAlreadyExistsException("email", user_data.email)

        hashed_password = hash_password(user_data.password)

        # Convert model to dict, excluding fields the DB doesn't have/want
        create_dict = user_data.model_dump(
            exclude={"password", "confirm_password", "allowed_email_domains"}
        )

        # Add the computed/system fields
        create_dict.update(
            {
                "hashed_password": hashed_password,
                "is_active": True,
                "is_verified": False,
            }
        )

        user = await self.repository.create(**create_dict)

        return user

    async def get_all_users(
        self, skip: int = 0, limit: int = 10, role: Optional[UserRole] = None
    ) -> list[User]:
        """Get all users with optional filtering"""
        if role:
            return await self.repository.get_by_role(role, skip, limit)
        return await self.repository.get_all(skip, limit)

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.repository.get_by_username(username)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.repository.get_by_email(email)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """Update user information"""
        user = await self.get_user_by_id(user_id)

        update_data = user_update.model_dump(exclude_unset=True)

        # Check for username conflict
        if "username" in update_data:
            existing = await self.repository.get_by_username(update_data["username"])
            if existing and existing.id != user_id:
                raise UserAlreadyExistsException("username", update_data["username"])

        # Check for email conflict
        if "email" in update_data:
            existing = await self.repository.get_by_email(update_data["email"])
            if existing and existing.id != user_id:
                raise UserAlreadyExistsException("email", update_data["email"])

        updated_user = await self.repository.update(user_id, **update_data)
        if not updated_user:
            raise UserNotFoundException(user_id)

        return updated_user

    async def delete_user(self, user_id: int) -> None:
        """Delete a user"""
        deleted = await self.repository.delete(user_id)
        if not deleted:
            raise UserNotFoundException(user_id)

    async def get_user_count(self) -> int:
        """Get total number of users"""
        return await self.repository.count()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        # Try username first
        user = await self.repository.get_by_username(username)

        # If not found, try email
        if not user:
            user = await self.repository.get_by_email(username)

        if not user:
            return None

        # Verify password using new security module
        if not verify_password(password, user.hashed_password):
            return None

        # Update last login
        await self.repository.update_last_login(user.id)

        return user

    async def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            UserNotFoundException: If user not found
            ValueError: If current password is incorrect
        """
        user = await self.get_user_by_id(user_id)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update password
        await self.repository.update(user_id, hashed_password=hashed_password)

        return True

    async def reset_password(self, email: str, new_password: str) -> bool:
        """
        Reset user password (for password reset flow)

        Args:
            email: User email
            new_password: New password

        Returns:
            True if password reset successfully

        Raises:
            UserNotFoundException: If user not found
        """
        user = await self.repository.get_by_email(email)
        if not user:
            raise UserNotFoundException(email)

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update password
        await self.repository.update(user.id, hashed_password=hashed_password)

        return True

    async def verify_email(self, email: str) -> bool:
        """
        Mark user email as verified

        Args:
            email: User email

        Returns:
            True if email verified successfully

        Raises:
            UserNotFoundException: If user not found
        """
        user = await self.repository.get_by_email(email)
        if not user:
            raise UserNotFoundException(email)

        await self.repository.update(user.id, is_verified=True)

        return True

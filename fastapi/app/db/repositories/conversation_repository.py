"""
Conversation repository

Data access layer for Conversation model
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.db.models.conversation import Conversation


class ConversationRepository(BaseRepository[Conversation]):
    """
    Conversation repository

    Handles all database operations for conversations
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Conversation]:
        """
        Get conversations by user ID

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of user's conversations
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_messages(self, conversation_id: int) -> Optional[Conversation]:
        """
        Get conversation with all messages loaded

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation with messages if found, None otherwise
        """
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_user_conversation_count(self, user_id: int) -> int:
        """
        Get number of conversations for a user

        Args:
            user_id: User ID

        Returns:
            Number of conversations
        """
        return await self.count(user_id=user_id)

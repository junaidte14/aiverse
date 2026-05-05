"""
Message repository

Data access layer for Message model
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.db.models.message import Message, MessageRole


class MessageRepository(BaseRepository[Message]):
    """
    Message repository

    Handles all database operations for messages
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def get_by_conversation(
        self, conversation_id: int, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        """
        Get messages for a conversation

        Args:
            conversation_id: Conversation ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of messages ordered by creation time
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """
        Get the last message in a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            Last message if found, None otherwise
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_role(self, conversation_id: int, role: MessageRole) -> int:
        """
        Count messages by role in a conversation

        Args:
            conversation_id: Conversation ID
            role: Message role

        Returns:
            Number of messages with specified role
        """
        return await self.count(conversation_id=conversation_id, role=role)

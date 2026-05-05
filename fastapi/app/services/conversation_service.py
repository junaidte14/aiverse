"""
Conversation service

Business logic for conversation operations
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageRole


class ConversationService:
    """
    Conversation service

    Handles conversation and message business logic
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session

        Args:
            db: Database session
        """
        self.session = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    async def create_conversation(
        self, user_id: int, title: str, model_name: str
    ) -> Conversation:
        """
        Create a new conversation

        Args:
            user_id: User ID
            title: Conversation title
            model_name: AI model name

        Returns:
            Created conversation
        """
        conversation = await self.conversation_repo.create(
            user_id=user_id, title=title, model_name=model_name
        )
        return conversation

    async def get_conversation(
        self, conversation_id: int, user_id: int
    ) -> Optional[Conversation]:
        """Fetch a conversation with messages only if the user_id matches"""
        # Use the repository's 'get_with_messages' to avoid lazy-loading issues
        conversation = await self.conversation_repo.get_with_messages(conversation_id)

        if conversation and conversation.user_id == user_id:
            return conversation
        return None

    async def get_user_conversations(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        metadata: dict = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ) -> Message:
        """
        Add message to conversation

        Args:
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            metadata_json=metadata,
            prompt_tokens: Prompt tokens used
            completion_tokens: Completion tokens used
            total_tokens: Total tokens used

        Returns:
            Created message
        """
        message = await self.message_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_json=metadata,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        return message

    async def get_conversation_messages(
        self, conversation_id: int, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        """
        Get messages for a conversation

        Args:
            conversation_id: Conversation ID
            skip: Number to skip
            limit: Maximum number

        Returns:
            List of messages
        """
        return await self.message_repo.get_by_conversation(conversation_id, skip, limit)

    async def update_conversation(
        self, conversation_id: int, user_id: int, title: str
    ) -> Optional[Conversation]:
        """Update title if owned by user"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        update_data = {"title": title}
        return await self.conversation_repo.update(conversation_id, **update_data)

    async def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Verify ownership before deletion"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        return await self.conversation_repo.delete(conversation_id)

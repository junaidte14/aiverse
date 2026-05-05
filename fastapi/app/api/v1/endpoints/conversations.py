"""
Conversation management endpoints

Handles conversation CRUD operations
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from pydantic import BaseModel

from app.services.conversation_service import ConversationService
from app.db.session import get_db
from app.db.models.message import MessageRole
from app.core.auth_dependencies import get_current_active_user
from app.db.models.user import User
from datetime import datetime

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# ============================================
# PYDANTIC MODELS
# ============================================


class ConversationCreate(BaseModel):
    """Request model for creating conversation"""

    user_id: int
    title: str = "New Conversation"
    model_name: str = "llama2"


class MessageCreate(BaseModel):
    """Request model for creating message"""

    role: MessageRole
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class MessageResponse(BaseModel):
    """Response model for message"""

    id: int
    conversation_id: int
    role: str
    content: str
    metadata_json: Optional[dict] = None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Response model for conversation"""

    id: int
    user_id: int
    title: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(ConversationResponse):
    """Response model for conversation with messages"""

    messages: list[MessageResponse] = []


# ============================================
# DEPENDENCIES
# ============================================


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Get conversation service with database session"""
    return ConversationService(db)


# ============================================
# ENDPOINTS
# ============================================
@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
):
    """List all conversations for the authenticated user"""
    return await service.get_user_conversations(current_user.id, skip, limit)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get a specific conversation only if it belongs to the user"""
    conv = await service.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Delete conversation if owned by current user"""
    success = await service.delete_conversation(conversation_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Conversation not found or unauthorized"
        )


# Add this new endpoint after the delete endpoint


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    title: str,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update conversation title if owned by current user"""
    updated_conv = await service.update_conversation(
        conversation_id, current_user.id, title
    )
    if not updated_conv:
        raise HTTPException(
            status_code=404, detail="Conversation not found or unauthorized"
        )
    return updated_conv


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new conversation",
)
async def create_conversation(
    conversation_data: ConversationCreate,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    """
    Create a new conversation

    - **user_id**: User ID who owns the conversation
    - **title**: Conversation title
    - **model_name**: AI model to use
    """
    conversation = await service.create_conversation(
        user_id=conversation_data.user_id,
        title=conversation_data.title,
        model_name=conversation_data.model_name,
    )
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/user/{user_id}",
    response_model=list[ConversationResponse],
    summary="Get user conversations",
)
async def get_user_conversations(
    user_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    skip: int = 0,
    limit: int = 20,
):
    """
    Get all conversations for a user

    - **user_id**: User ID
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records
    """
    conversations = await service.get_user_conversations(user_id, skip, limit)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message to conversation",
)
async def add_message(
    conversation_id: int,
    message_data: MessageCreate,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    """
    Add a message to a conversation

    - **role**: Message role (user, assistant, system)
    - **content**: Message content
    - **tokens**: Optional token counts
    """
    message = await service.add_message(
        conversation_id=conversation_id,
        role=message_data.role,
        content=message_data.content,
        prompt_tokens=message_data.prompt_tokens,
        completion_tokens=message_data.completion_tokens,
        total_tokens=message_data.total_tokens,
    )
    return MessageResponse.model_validate(message)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="Get conversation messages",
)
async def get_messages(
    conversation_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Get messages for a conversation

    Returns messages in chronological order
    """
    messages = await service.get_conversation_messages(conversation_id, skip, limit)
    return [MessageResponse.model_validate(m) for m in messages]

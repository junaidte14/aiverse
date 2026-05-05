"""
Multi-Provider AI Endpoints

Unified interface for all AI providers
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.auth_dependencies import get_current_active_user
from app.db.models.user import User
from app.services.ai.unified_service import UnifiedAIService
from app.services.ai.base_provider import ChatMessage, ModelInfo
from app.services.ai.provider_manager import ProviderManager
from app.services.conversation_service import ConversationService
from app.utils.logger import logger
import json

router = APIRouter(prefix="/ai/multi", tags=["Multi-Provider AI"])


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request"""

    provider: str = Field(
        ..., description="AI provider (ollama, groq, openai, anthropic, together)"
    )
    model: str = Field(..., description="Model identifier")
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    conversation_id: int | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(
        1000, ge=1, le=4000, description="Maximum tokens to generate"
    )
    stream: bool = Field(False, description="Stream response")


class ChatResponseModel(BaseModel):
    """Chat response"""

    content: str
    model: str
    provider: str
    tokens_used: int
    cost: float


class ProviderInfo(BaseModel):
    """Provider information"""

    name: str
    display_name: str
    requires_api_key: bool
    has_api_key: bool
    models_count: int


class UsageStats(BaseModel):
    """User usage statistics"""

    total_tokens: int
    total_cost: float
    monthly_cost: float
    monthly_limit: float
    remaining_budget: float


# Endpoints


@router.post("/chat", response_model=ChatResponseModel)
async def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Send chat request to specified AI provider

    Supports all registered providers:
    - **ollama**: Local models (free)
    - **groq**: Ultra-fast inference

    Returns response with content, tokens, and cost tracking.
    """
    if request.stream:
        raise HTTPException(
            status_code=400, detail="Use /chat/stream endpoint for streaming responses"
        )

    service = UnifiedAIService(db, current_user)

    try:
        if not request.conversation_id:
            conv = await ConversationService(db).create_conversation(
                user_id=current_user.id,
                title=request.messages[-1].content[:50],
                model_name=request.model,
            )
            conversation_id = conv.id
        else:
            conversation_id = request.conversation_id

        await ConversationService(db).add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.messages[-1].content,
        )

        response = await service.chat(
            provider=request.provider,
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        await ConversationService(db).add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.content,
        )

        return ChatResponseModel(
            content=response.content,
            model=response.model,
            provider=response.provider,
            tokens_used=response.tokens_used,
            cost=response.cost,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", extra={"user_id": current_user.id})
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # logger.info(f"DEBUG: Starting stream for user {current_user.id}")
    service = UnifiedAIService(db, current_user)
    conv_service = ConversationService(db)

    # 1. Conversation Setup
    if not request.conversation_id:
        # logger.info("DEBUG: No conversation_id provided. Creating new conversation...")
        conv = await conv_service.create_conversation(
            user_id=current_user.id,
            title=request.messages[-1].content[:50],
            model_name=request.model,
        )
        conversation_id = conv.id
        # logger.info(f"DEBUG: Created new conversation ID: {conversation_id}")
    else:
        conversation_id = request.conversation_id
        # logger.info(f"DEBUG: Using existing conversation ID: {conversation_id}")

    # 2. Add User Message
    try:
        await conv_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.messages[-1].content,
        )
        await db.commit()
        # logger.info("DEBUG: User message saved and committed successfully.")
    except Exception as e:
        logger.error(f"DEBUG ERROR: Failed to save user message: {str(e)}")

    async def generate():
        full_response = ""
        try:
            # Send conversation metadata to frontend
            yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"

            # logger.info(f"DEBUG: Beginning AI stream from provider: {request.provider}")

            async for chunk in service.stream_chat(
                provider=request.provider,
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

            # logger.info( f"DEBUG: Stream finished. Received {len(full_response)} characters.")

            # 3. SAVE ASSISTANT RESPONSE
            if full_response:
                # logger.info("DEBUG: Attempting to save assistant message to DB...")
                # Re-verify session state here
                await conv_service.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                )
                await db.commit()
                # logger.info( "DEBUG: Assistant message saved and committed successfully.")
            else:
                logger.warning("DEBUG: Assistant response was empty. Nothing to save.")

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"DEBUG ERROR in generate(): {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            logger.info("DEBUG: Generator closed.")

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    List all available AI providers

    Shows which providers are configured and ready to use.
    """
    service = UnifiedAIService(db, current_user)
    provider_names = ProviderManager.list_providers()

    providers = []

    for name in provider_names:
        # Check if user has API key
        has_key = False
        requires_key = name != "ollama"

        try:
            await service.get_provider(name)
            has_key = True
        except:
            has_key = False

        # Get model count
        model_count = 0
        if has_key or not requires_key:
            try:
                models = await service.list_models(name)
                model_count = len(models)
            except:
                model_count = 0

        providers.append(
            ProviderInfo(
                name=name,
                display_name=name.capitalize(),
                requires_api_key=requires_key,
                has_api_key=has_key,
                models_count=model_count,
            )
        )

    return providers


@router.get("/models/{provider}", response_model=List[ModelInfo])
async def list_models(
    provider: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    List available models for specified provider

    Returns model information including:
    - Model ID and name
    - Context length
    - Cost per 1K tokens
    - Streaming support
    """
    service = UnifiedAIService(db, current_user)

    try:
        models = await service.list_models(provider)
        return models
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to list models: {str(e)}")


@router.get("/models/{provider}/{model_id}", response_model=ModelInfo)
async def get_model_info(
    provider: str,
    model_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get detailed information about specific model
    """
    service = UnifiedAIService(db, current_user)

    try:
        model_info = await service.get_model_info(provider, model_id)
        return model_info
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}")


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Get user's AI usage statistics

    Returns:
    - Total tokens used
    - Total cost (all time)
    - Monthly cost
    - Monthly limit
    - Remaining budget
    """
    from app.core.config import settings

    remaining = settings.MAX_MONTHLY_COST - current_user.monthly_cost

    return UsageStats(
        total_tokens=current_user.total_tokens_used,
        total_cost=current_user.total_cost,
        monthly_cost=current_user.monthly_cost,
        monthly_limit=settings.MAX_MONTHLY_COST,
        remaining_budget=max(0, remaining),
    )

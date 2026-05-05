"""
Unified AI Service

Single interface for all AI providers
"""

from typing import List, AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.ai.base_provider import (
    BaseAIProvider,
    ChatMessage,
    ChatResponse,
    ModelInfo,
)
from app.services.ai.provider_manager import ProviderManager
from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository
from app.utils.encryption import api_key_encryption
from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.logger import logger
from datetime import datetime, timedelta


class UnifiedAIService:
    """
    Unified service for all AI providers

    Handles provider selection, API key management, cost tracking
    """

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.user_repo = UserRepository(db)

    async def get_provider(self, provider_name: str) -> BaseAIProvider:
        """
        Get AI provider instance with user's API key

        Args:
            provider_name: Provider name (groq, ollama)

        Returns:
            Provider instance

        Raises:
            AppException: If API key missing or invalid
        """
        # Ollama doesn't need API key
        if provider_name == "ollama":
            return ProviderManager.get_provider("ollama")

        # Get user's encrypted API key
        api_key = await self._get_user_api_key(provider_name)

        if not api_key:
            raise AppException(
                status_code=400,
                detail=f"No API key configured for {provider_name}. Please add your API key in settings.",
            )

        # Get provider with decrypted key
        return ProviderManager.get_provider(provider_name, api_key=api_key)

    async def chat(
        self,
        provider: str,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ChatResponse:
        """
        Send chat request to specified provider

        Args:
            provider: Provider name
            model: Model identifier
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            ChatResponse with content and metadata
        """
        # Check monthly cost limit
        await self._check_cost_limit()

        # Get provider
        ai_provider = await self.get_provider(provider)

        # Make request
        response = await ai_provider.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Track usage
        await self._track_usage(response.tokens_used, response.cost)

        logger.info(
            f"Chat completed: {provider}/{model}",
            extra={
                "user_id": self.user.id,
                "provider": provider,
                "model": model,
                "tokens": response.tokens_used,
                "cost": response.cost,
            },
        )

        return response

    async def stream_chat(
        self,
        provider: str,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from specified provider

        Args:
            provider: Provider name
            model: Model identifier
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Chunks of response text
        """
        # Check monthly cost limit
        await self._check_cost_limit()

        # Get provider
        ai_provider = await self.get_provider(provider)

        # Stream response
        async for chunk in ai_provider.stream_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

        # Note: Token tracking for streaming is approximate
        # Would need to count tokens from response
        estimated_tokens = max_tokens // 2  # Rough estimate
        estimated_cost = 0.0  # Calculate based on provider

        await self._track_usage(estimated_tokens, estimated_cost)

    async def list_models(self, provider: str) -> List[ModelInfo]:
        """
        List available models for provider

        Args:
            provider: Provider name

        Returns:
            List of ModelInfo objects
        """
        ai_provider = await self.get_provider(provider)
        return await ai_provider.list_models()

    async def get_model_info(self, provider: str, model_id: str) -> ModelInfo:
        """
        Get information about specific model

        Args:
            provider: Provider name
            model_id: Model identifier

        Returns:
            ModelInfo object
        """
        ai_provider = await self.get_provider(provider)
        return await ai_provider.get_model_info(model_id)

    async def _get_user_api_key(self, provider: str) -> Optional[str]:
        """Get and decrypt user's API key for provider"""

        # Map provider to user field
        key_field_map = {
            "groq": self.user.groq_api_key,
            "openai": self.user.openai_api_key,
            "anthropic": self.user.anthropic_api_key,
            "together": self.user.together_api_key,
        }

        encrypted_key = key_field_map.get(provider)

        if not encrypted_key:
            # Check for system-level API keys
            system_key_map = {"groq": settings.GROQ_API_KEY}
            return system_key_map.get(provider)

        # Decrypt user's key
        return api_key_encryption.decrypt(encrypted_key)

    async def _track_usage(self, tokens: int, cost: float):
        """Track token usage and cost for user"""

        if not settings.ENABLE_COST_TRACKING:
            return

        # Update user totals
        result = await self.db.execute(select(User).where(User.id == self.user.id))
        self.user = result.scalar_one()
        self.user.total_tokens_used += tokens
        self.user.total_cost += cost
        self.user.monthly_cost += cost

        # Reset monthly cost if needed
        now = datetime.utcnow()
        if now - self.user.last_cost_reset > timedelta(days=30):
            self.user.monthly_cost = cost
            self.user.last_cost_reset = now

        await self.db.commit()
        await self.db.refresh(self.user)

    async def _check_cost_limit(self):
        """Check if user has exceeded monthly cost limit"""

        if not settings.ENABLE_COST_TRACKING:
            return

        # Reset monthly cost if needed
        now = datetime.utcnow()
        if now - self.user.last_cost_reset > timedelta(days=30):
            self.user.monthly_cost = 0.0
            self.user.last_cost_reset = now
            await self.db.commit()

        # Check limit
        if self.user.monthly_cost >= settings.MAX_MONTHLY_COST:
            raise AppException(
                status_code=429,
                detail=f"Monthly cost limit of ${settings.MAX_MONTHLY_COST} exceeded. "
                f"Current usage: ${self.user.monthly_cost:.2f}",
            )

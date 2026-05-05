"""
Abstract base class for AI providers

All AI providers must implement this interface
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Standard chat message format"""

    role: str  # "user", "assistant", "system"
    content: str


class ChatResponse(BaseModel):
    """Standard chat response format"""

    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cost: float = 0.0


class ModelInfo(BaseModel):
    """Model information"""

    id: str
    name: str
    provider: str
    context_length: int
    cost_per_1k_tokens: float = 0.0
    supports_streaming: bool = True


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers

    All AI providers (Groq, OpenAI, Claude, etc.) must inherit this
    """

    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key
        self.provider_name = "base"

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ChatResponse:
        """
        Send a chat request and get response

        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            ChatResponse object
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response

        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Chunks of response text
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """
        List available models

        Returns:
            List of ModelInfo objects
        """
        pass

    @abstractmethod
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """
        Get information about a specific model

        Args:
            model_id: Model identifier

        Returns:
            ModelInfo object
        """
        pass

    def calculate_cost(self, tokens: int, cost_per_1k: float) -> float:
        """
        Calculate cost for token usage

        Args:
            tokens: Number of tokens used
            cost_per_1k: Cost per 1000 tokens

        Returns:
            Total cost in dollars
        """
        return (tokens / 1000) * cost_per_1k

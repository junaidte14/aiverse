"""
Ollama AI Provider

Local LLM provider using Ollama
"""

from typing import List, AsyncGenerator
import httpx
from app.services.ai.base_provider import (
    BaseAIProvider,
    ChatMessage,
    ChatResponse,
    ModelInfo,
)
from app.core.config import settings
from app.utils.logger import logger


class OllamaProvider(BaseAIProvider):
    """
    Ollama provider for local LLMs

    Supports models like LLaMA 2, Mistral, etc.
    """

    def __init__(self, api_key: str = None, base_url: str = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.provider_name = "ollama"
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = httpx.AsyncClient(timeout=300.0)

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ChatResponse:
        """Send chat request to Ollama"""

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        # Make request
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": ollama_messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )

        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data.get("message", {}).get("content", ""),
            model=model,
            provider=self.provider_name,
            tokens_used=data.get("eval_count", 0),
            cost=0.0,  # Local is free!
        )

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Ollama"""

        ollama_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": ollama_messages,
                "stream": True,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line:
                    import json

                    data = json.loads(line)

                    if "message" in data:
                        content = data["message"].get("content", "")
                        if content:
                            yield content

    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models"""

        response = await self.client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        data = response.json()

        models = []
        for model in data.get("models", []):
            models.append(
                ModelInfo(
                    id=model["name"],
                    name=model["name"],
                    provider=self.provider_name,
                    context_length=4096,  # Default, can be configured
                    cost_per_1k_tokens=0.0,
                    supports_streaming=True,
                )
            )

        return models

    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get info about specific Ollama model"""

        response = await self.client.post(
            f"{self.base_url}/api/show", json={"name": model_id}
        )
        response.raise_for_status()
        data = response.json()

        return ModelInfo(
            id=model_id,
            name=model_id,
            provider=self.provider_name,
            context_length=data.get("context_length", 4096),
            cost_per_1k_tokens=0.0,
            supports_streaming=True,
        )

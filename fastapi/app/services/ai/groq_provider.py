"""
Groq AI Provider

Ultra-fast inference with Groq API
"""

from typing import List, AsyncGenerator
import httpx
import json
from app.services.ai.base_provider import (
    BaseAIProvider,
    ChatMessage,
    ChatResponse,
    ModelInfo,
)
from app.utils.logger import logger


class GroqProvider(BaseAIProvider):
    """
    Groq provider for fast inference

    Supports models: llama-3.3-70b, mixtral-8x7b, gemma-7b
    """

    # Groq pricing (as of 2024)
    PRICING = {
        "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
        "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079},
        "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
        "mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
        "gemma-7b-it": {"input": 0.00007, "output": 0.00007},
    }

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.provider_name = "groq"
        self.base_url = "https://api.groq.com/openai/v1"

        if not api_key:
            raise ValueError("Groq API key is required")

        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ChatResponse:
        """Send chat request to Groq"""

        # Convert messages to OpenAI format
        groq_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        # Make request
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": model,
                "messages": groq_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            },
        )

        response.raise_for_status()
        data = response.json()

        # Extract response
        choice = data["choices"][0]
        content = choice["message"]["content"]

        # Calculate tokens and cost
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        input_cost = self.calculate_cost(
            usage.get("prompt_tokens", 0), pricing["input"]
        )
        output_cost = self.calculate_cost(
            usage.get("completion_tokens", 0), pricing["output"]
        )
        total_cost = input_cost + output_cost

        return ChatResponse(
            content=content,
            model=model,
            provider=self.provider_name,
            tokens_used=total_tokens,
            cost=total_cost,
        )

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Groq"""

        groq_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json={
                "model": model,
                "messages": groq_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs,
            },
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix

                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"]

                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> List[ModelInfo]:
        """List available Groq models"""

        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        data = response.json()

        models = []
        for model in data.get("data", []):
            model_id = model["id"]
            pricing = self.PRICING.get(model_id, {"input": 0, "output": 0})

            models.append(
                ModelInfo(
                    id=model_id,
                    name=model.get("name", model_id),
                    provider=self.provider_name,
                    context_length=model.get("context_window", 32768),
                    cost_per_1k_tokens=pricing["input"],  # Use input pricing
                    supports_streaming=True,
                )
            )

        return models

    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get info about specific Groq model"""

        response = await self.client.get(f"{self.base_url}/models/{model_id}")
        response.raise_for_status()
        data = response.json()

        pricing = self.PRICING.get(model_id, {"input": 0, "output": 0})

        return ModelInfo(
            id=model_id,
            name=data.get("name", model_id),
            provider=self.provider_name,
            context_length=data.get("context_window", 32768),
            cost_per_1k_tokens=pricing["input"],
            supports_streaming=True,
        )

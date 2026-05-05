"""
AI Services Package

Register all AI providers
"""

from app.services.ai.provider_manager import ProviderManager
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.groq_provider import GroqProvider

# Register all providers
ProviderManager.register_provider("ollama", OllamaProvider)
ProviderManager.register_provider("groq", GroqProvider)


__all__ = [
    "ProviderManager",
    "OllamaProvider",
    "GroqProvider",
]

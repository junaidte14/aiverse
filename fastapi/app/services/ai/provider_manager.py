"""
AI Provider Manager

Factory pattern for managing multiple AI providers
"""

from typing import Dict, Type, Optional
from app.services.ai.base_provider import BaseAIProvider
from app.core.exceptions import AppException
from app.utils.logger import logger


class ProviderManager:
    """
    Manages multiple AI providers

    Singleton pattern to ensure one instance across app
    """

    _instance = None
    _providers: Dict[str, Type[BaseAIProvider]] = {}
    _initialized_providers: Dict[str, BaseAIProvider] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseAIProvider]):
        """
        Register a new AI provider

        Args:
            name: Provider name (e.g., "groq", "ollama")
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        # logger.info(f"Registered AI provider: {name}")

    @classmethod
    def get_provider(cls, name: str, api_key: str = None, **kwargs) -> BaseAIProvider:
        """
        Get or create provider instance

        Args:
            name: Provider name
            api_key: API key for provider
            **kwargs: Additional provider configuration

        Returns:
            Provider instance

        Raises:
            AppException: If provider not found
        """
        # Check if provider is registered
        if name not in cls._providers:
            raise AppException(
                status_code=400,
                detail=f"AI provider '{name}' not found. Available: {list(cls._providers.keys())}",
            )

        # Create cache key
        cache_key = f"{name}:{api_key or 'default'}"

        # Return cached instance if exists
        if cache_key in cls._initialized_providers:
            return cls._initialized_providers[cache_key]

        # Create new instance
        provider_class = cls._providers[name]
        provider = provider_class(api_key=api_key, **kwargs)

        # Cache instance
        cls._initialized_providers[cache_key] = provider

        logger.info(f"Initialized AI provider: {name}")
        return provider

    @classmethod
    def list_providers(cls) -> list:
        """
        List all registered providers

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

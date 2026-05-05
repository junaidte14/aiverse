"""
Core configuration module
Manages all application settings using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings

    These values are loaded from environment variables or .env file
    Pydantic validates the types automatically
    """

    # Application
    APP_NAME: str = "AIVerse Backend"
    APP_VERSION: str = "0.5.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # API
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "localhost"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Database Configuration
    DATABASE_URL: str = None
    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    @property
    def async_database_url(self) -> str:
        """Get async database URL"""
        return self.DATABASE_URL

    @property
    def sync_database_url(self) -> str:
        """Get sync database URL (for Alembic migrations)"""
        return self.DATABASE_URL.replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )

    # AI Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_AI_MODEL: str = "llama2"

    # Multi-Provider AI Configuration
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None

    # Default AI provider
    DEFAULT_AI_PROVIDER: str = "groq"

    # Provider-specific settings
    AI_PROVIDER_TIMEOUT: int = 120  # seconds
    AI_MAX_RETRIES: int = 3

    # Cost tracking
    ENABLE_COST_TRACKING: bool = True
    MAX_MONTHLY_COST: float = 10.0  # USD

    # JWT Authentication Settings
    SECRET_KEY: str = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Reset Settings
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # Email Settings (for future use)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@aiverse.com"
    EMAILS_FROM_NAME: str = "AIVerse"

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Create settings instance (cached)

    @lru_cache ensures we only create one Settings instance
    and reuse it throughout the application

    Returns:
        Settings: Application settings
    """
    return Settings()


# Convenience: Get settings instance
settings = get_settings()

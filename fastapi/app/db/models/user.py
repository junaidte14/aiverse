"""
User database model

SQLAlchemy ORM model for users
"""

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Integer,
    Float,
    JSON,
    Enum as SQLEnum,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
import enum

from app.db.base import Base
from app.db.models.conversation import Conversation
from app.db.models.rag_source import RAGSource


class UserRole(str, enum.Enum):
    """User role enumeration"""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(Base):
    """
    User model

    Represents a user in the system
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User Information
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Role and Status
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.USER, nullable=False
    )

    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=[], nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # AI Provider API Keys (encrypted)
    groq_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    openai_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    anthropic_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    together_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # AI Usage tracking
    total_tokens_used: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )

    total_cost: Mapped[float] = mapped_column(Float, server_default="0", nullable=False)

    monthly_cost: Mapped[float] = mapped_column(
        Float, server_default="0", nullable=False
    )

    last_cost_reset: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("now()"), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )

    rag_sources = relationship(
        "RAGSource", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

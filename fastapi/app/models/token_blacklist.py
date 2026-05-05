"""
Token blacklist model

For advanced security: blacklist revoked tokens
"""

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.db.base import Base


class TokenBlacklist(Base):
    """
    Token blacklist model

    Stores revoked tokens to prevent their use after logout
    """

    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Token identifier (jti claim from JWT)
    jti: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # Token type (access or refresh)
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # User ID who owned the token
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # When token was blacklisted
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(datetime.timezone.utc), nullable=False
    )

    # Token expiration (for cleanup)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<TokenBlacklist(jti='{self.jti}', type='{self.token_type}')>"

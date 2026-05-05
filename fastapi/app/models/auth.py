"""
Authentication models

Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Token(BaseModel):
    """
    Token response model

    Returned after successful authentication
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    }


class TokenPayload(BaseModel):
    """
    Token payload model

    Represents decoded JWT token data
    """

    sub: str | None = None  # Subject (user ID or email)
    exp: int | None = None  # Expiration time
    iat: int | None = None  # Issued at
    type: str | None = None  # Token type


class LoginRequest(BaseModel):
    """
    Login request model
    """

    username: str = Field(..., min_length=3, description="Username or email")
    password: str = Field(..., min_length=8, description="Password")

    model_config = {
        "json_schema_extra": {
            "example": {"username": "john_doe", "password": "SecurePass123"}
        }
    }


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request model
    """

    refresh_token: str = Field(..., description="Refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    }


class PasswordResetRequest(BaseModel):
    """
    Password reset request model
    """

    email: EmailStr = Field(..., description="User email")

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com"}}}


class PasswordResetConfirm(BaseModel):
    """
    Password reset confirmation model
    """

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass123",
            }
        }
    }


class EmailVerificationRequest(BaseModel):
    """
    Email verification request model
    """

    token: str = Field(..., description="Verification token")

    model_config = {
        "json_schema_extra": {
            "example": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    }


class ChangePasswordRequest(BaseModel):
    """
    Change password request model
    """

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPass123",
                "new_password": "NewSecurePass123",
            }
        }
    }

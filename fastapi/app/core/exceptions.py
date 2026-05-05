"""
Custom exceptions for the application

These provide more specific error handling than generic HTTPException
"""

from fastapi import HTTPException, status
from typing import Any, Optional, Dict


class AppException(HTTPException):
    """
    Base application exception

    All custom exceptions should inherit from this
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class UserNotFoundException(AppException):
    """User not found exception"""

    def __init__(self, user_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
            error_code="USER_NOT_FOUND",
        )


class UserAlreadyExistsException(AppException):
    """User already exists exception"""

    def __init__(self, field: str, value: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with {field} '{value}' already exists",
            error_code="USER_ALREADY_EXISTS",
        )


class InvalidCredentialsException(AppException):
    """Invalid credentials exception"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            error_code="INVALID_CREDENTIALS",
        )


class PermissionDeniedException(AppException):
    """Permission denied exception"""

    def __init__(self, action: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to {action}",
            error_code="PERMISSION_DENIED",
        )


class ValidationException(AppException):
    """Custom validation exception"""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )


class DatabaseException(AppException):
    """Database operation exception"""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
        )

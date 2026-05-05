"""
Error response models

Standardized error responses for the API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ValidationError(BaseModel):
    """Single validation error"""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Type of validation error")


class ErrorResponse(BaseModel):
    """
    Standard error response format

    Used for all API errors
    """

    success: bool = Field(default=False, description="Always false for errors")
    error_code: Optional[str] = Field(
        None, description="Application-specific error code"
    )
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )
    path: Optional[str] = Field(None, description="Request path that caused the error")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error_code": "USER_NOT_FOUND",
                "message": "User with ID '123' not found",
                "timestamp": "2024-01-15T10:30:00",
                "path": "/api/v1/users/123",
            }
        }
    }


class ValidationErrorResponse(BaseModel):
    """
    Validation error response

    Used when Pydantic validation fails
    """

    success: bool = Field(default=False)
    error_code: str = Field(default="VALIDATION_ERROR")
    message: str = Field(default="Validation error")
    errors: List[ValidationError] = Field(..., description="List of validation errors")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Validation error",
                "errors": [
                    {
                        "field": "email",
                        "message": "value is not a valid email address",
                        "error_type": "value_error.email",
                    },
                    {
                        "field": "password",
                        "message": "Password must contain at least one uppercase letter",
                        "error_type": "value_error",
                    },
                ],
                "timestamp": "2024-01-15T10:30:00",
            }
        }
    }

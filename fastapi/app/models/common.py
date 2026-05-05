"""
Common Pydantic models used across the application
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class HealthCheck(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment (dev/prod)")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.3.0",
                "environment": "development",
                "timestamp": "2024-01-15T10:30:00",
            }
        }


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")

    class Config:
        json_schema_extra = {
            "example": {"message": "Operation completed successfully", "success": True}
        }


class ErrorResponse(BaseModel):
    """Error response model"""

    detail: str = Field(..., description="Error details")
    error_code: Optional[str] = Field(None, description="Error code")

    class Config:
        json_schema_extra = {
            "example": {"detail": "Resource not found", "error_code": "NOT_FOUND"}
        }

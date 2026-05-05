"""
Advanced user endpoints with comprehensive validation
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.user import UserCreate, UserResponse
from app.models.user import UserRole, UserUpdate, User
from app.models.common import MessageResponse
from app.services.user_service import UserService
from app.db.session import get_db
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency to get user service instance"""
    return UserService(db)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user with advanced validation",
    description="""
    Create a new user with comprehensive validation:
    
    **Username Rules:**
    - 3-50 characters
    - Only letters, numbers, underscores, hyphens
    - Cannot start/end with special characters
    - No consecutive special characters
    - Automatically converted to lowercase
    
    **Password Rules:**
    - Minimum 8 characters
    - Must contain uppercase letter
    - Must contain lowercase letter
    - Must contain number
    - Cannot be common password
    
    **Email Rules:**
    - Valid email format
    - Must be from allowed domain
    
    **Age Rules:**
    - Must be 13 or older
    - If date_of_birth provided, must be consistent
    
    **Other Validations:**
    - Full name: no numbers, proper capitalization
    - Website: valid URL format
    - Tags: 2-30 chars, lowercase, no duplicates
    """,
)
async def create_user(
    user_data: UserCreate, service: UserService = Depends(get_user_service)
):
    """
    Create a user with advanced validation

    This endpoint demonstrates comprehensive Pydantic validation
    """
    # Convert UserCreateAdvanced to regular UserCreate
    from app.models.user import UserCreate

    user_create = UserCreate(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
    )

    # Create the user
    created_user = await service.create_user(user_create)

    return MessageResponse(
        message=f"User '{created_user.username}' created successfully", success=True
    )


@router.post(
    "/validate",
    summary="Validate user data without creating",
    description="Test user data against all validation rules without actually creating the user",
)
async def validate_user_data(user_data: UserCreate):
    """
    Validate user data without creating

    Useful for client-side validation feedback
    """
    return MessageResponse(message="User data is valid", success=True)


@router.get(
    "/validation-rules",
    summary="Get validation rules",
    description="Returns all validation rules for user creation",
)
async def get_validation_rules():
    """
    Get validation rules documentation

    Helps frontend developers understand what validations are in place
    """
    return {
        "username": {
            "min_length": 3,
            "max_length": 50,
            "pattern": "^[a-zA-Z0-9_-]+$",
            "rules": [
                "Only letters, numbers, underscores, and hyphens",
                "Cannot start/end with special characters",
                "No consecutive special characters",
                "Automatically converted to lowercase",
            ],
        },
        "password": {
            "min_length": 8,
            "max_length": 128,
            "rules": [
                "At least one uppercase letter",
                "At least one lowercase letter",
                "At least one number",
                "Cannot be common password (password, 12345678, etc.)",
            ],
        },
        "email": {
            "format": "Valid email address",
            "allowed_domains": ["gmail.com", "yahoo.com", "outlook.com", "example.com"],
        },
        "age": {"minimum": 13, "maximum": 120},
        "full_name": {
            "min_length": 2,
            "max_length": 100,
            "rules": ["Cannot contain numbers", "Automatically capitalized"],
        },
        "website": {
            "format": "Valid URL",
            "rules": ["Automatically adds https:// if missing"],
        },
        "tags": {
            "min_length": 2,
            "max_length": 30,
            "max_count": 10,
            "pattern": "^[a-z0-9-_]+$",
            "rules": [
                "Lowercase only",
                "Letters, numbers, hyphens, underscores",
                "Duplicates automatically removed",
            ],
        },
    }

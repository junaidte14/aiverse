"""
User models with comprehensive validation

This module demonstrates various Pydantic validation techniques
"""

from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    model_validator,
    ConfigDict,
)
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum
import re


class UserRole(str, Enum):
    """User role enumeration"""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    MODERATOR = "moderator"


class PasswordStrength(str, Enum):
    """Password strength levels"""

    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class UserCreate(BaseModel):
    """
    User creation model with custom validation
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (letters, numbers, underscore, hyphen only)",
    )

    email: EmailStr = Field(..., description="Valid email address")

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must include uppercase, lowercase, and number)",
    )

    confirm_password: str = Field(
        ..., description="Password confirmation (must match password)"
    )

    full_name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Full name"
    )

    age: Optional[int] = Field(
        None, ge=13, le=120, description="Age (must be 13 or older)"
    )

    date_of_birth: Optional[date] = Field(None, description="Date of birth")

    phone_number: Optional[str] = Field(
        None, description="Phone number (international format preferred)"
    )

    website: Optional[str] = Field(None, description="Personal website URL")

    bio: Optional[str] = Field(None, max_length=500, description="Short bio")

    role: UserRole = Field(default=UserRole.USER, description="User role")

    allowed_email_domains: List[str] = Field(
        default=["gmail.com", "yahoo.com", "outlook.com", "example.com"],
        description="Allowed email domains for registration",
    )

    tags: List[str] = Field(default=[], max_length=10, description="User tags (max 10)")

    # ========================================
    # FIELD VALIDATORS
    # ========================================

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Validate username format

        Rules:
        - Only alphanumeric, underscore, and hyphen
        - Cannot start or end with underscore/hyphen
        - No consecutive underscores or hyphens
        """
        # Check allowed characters
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

        # Cannot start/end with special chars
        if v[0] in "_-" or v[-1] in "_-":
            raise ValueError("Username cannot start or end with underscore or hyphen")

        # No consecutive special chars
        if "__" in v or "--" in v or "_-" in v or "-_" in v:
            raise ValueError("Username cannot contain consecutive special characters")

        # Convert to lowercase for consistency
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - Optionally one special character for strong passwords
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        # Check for common weak passwords
        weak_passwords = ["password", "12345678", "qwerty", "abc123"]
        if v.lower() in weak_passwords:
            raise ValueError(
                "Password is too common. Please choose a stronger password."
            )

        return v

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: EmailStr, info) -> EmailStr:
        """
        Validate email domain against allowed list

        Note: info.data contains other field values that have been validated so far
        """
        # Extract domain from email
        domain = v.split("@")[1].lower()

        # Get allowed domains from model data (if available)
        # During validation, other fields might not be set yet
        # So we use a default list
        default_allowed = ["gmail.com", "yahoo.com", "outlook.com", "example.com"]

        if domain not in default_allowed:
            raise ValueError(
                f'Email domain "{domain}" is not allowed. '
                f'Allowed domains: {", ".join(default_allowed)}'
            )

        return v.lower()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean full name
        """
        if v is None:
            return v

        # Remove extra whitespace
        v = " ".join(v.split())

        # Check for numbers (names shouldn't have numbers)
        if re.search(r"\d", v):
            raise ValueError("Full name cannot contain numbers")

        # Capitalize each word
        return v.title()

    @field_validator("website")
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate website URL format
        """
        if v is None:
            return v

        # Add https:// if no protocol specified
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"

        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError("Invalid website URL format")

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """
        Validate and clean tags
        """
        if not v:
            return v

        # Remove duplicates and empty strings
        tags = [tag.strip().lower() for tag in v if tag.strip()]
        tags = list(set(tags))  # Remove duplicates

        # Validate each tag
        for tag in tags:
            if len(tag) < 2:
                raise ValueError("Each tag must be at least 2 characters long")
            if len(tag) > 30:
                raise ValueError("Each tag must be at most 30 characters long")
            if not re.match(r"^[a-z0-9-_]+$", tag):
                raise ValueError(
                    "Tags can only contain lowercase letters, numbers, hyphens, and underscores"
                )

        return tags

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[date]) -> Optional[date]:
        """
        Validate date of birth
        """
        if v is None:
            return v

        # Check if date is in the future
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")

        # Check minimum age (13 years)
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))

        if age < 13:
            raise ValueError("You must be at least 13 years old to register")

        if age > 120:
            raise ValueError("Invalid date of birth")

        return v

    # ========================================
    # MODEL VALIDATORS (validate multiple fields)
    # ========================================

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "UserCreate":
        """
        Validate that password and confirm_password match

        This runs AFTER all field validators
        """
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self

    @model_validator(mode="after")
    def validate_age_and_dob_consistency(self) -> "UserCreate":
        """
        If both age and date_of_birth are provided, ensure they're consistent
        """
        if self.age is not None and self.date_of_birth is not None:
            # Calculate age from date of birth
            today = date.today()
            calculated_age = today.year - self.date_of_birth.year
            calculated_age -= (today.month, today.day) < (
                self.date_of_birth.month,
                self.date_of_birth.day,
            )

            # Allow 1 year difference (birthday might not have occurred yet)
            if abs(calculated_age - self.age) > 1:
                raise ValueError(
                    f"Age ({self.age}) does not match date of birth "
                    f"(calculated age: {calculated_age})"
                )

        return self

    # ========================================
    # CONFIGURATION
    # ========================================

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Automatically strip whitespace from strings
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "full_name": "John Doe",
                "age": 27,
                "date_of_birth": "1999-01-15",
                "phone_number": "+1-555-123-4567",
                "website": "https://johndoe.com",
                "bio": "Software developer passionate about AI",
                "role": "user",
                "tags": ["developer", "python", "ai"],
            }
        },
    )


class UserUpdate(BaseModel):
    """Model for updating a user (all fields optional)"""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    phone_number: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

    model_config = ConfigDict(str_strip_whitespace=True)


class User(BaseModel):
    """Complete user model (internal bridge to DB)"""

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    tags: List[str] = []
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """
    User response model
    """

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    age: Optional[int]
    date_of_birth: Optional[date]
    phone_number: Optional[str]
    website: Optional[str]
    bio: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    tags: List[str]

    # Computed fields (derived from other fields)
    @property
    def display_name(self) -> str:
        """Return full name if available, otherwise username"""
        return self.full_name if self.full_name else self.username

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "age": 27,
                "date_of_birth": "1999-01-15",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "tags": ["developer", "python"],
            }
        },
    )

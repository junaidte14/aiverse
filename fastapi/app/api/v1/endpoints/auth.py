"""
Authentication endpoints

Handles login, registration, token refresh, and password management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import timedelta
from datetime import datetime

from app.db.session import get_db
from app.models.auth import (
    Token,
    LoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    ChangePasswordRequest,
)
from app.models.user import UserCreate, UserResponse
from app.models.common import MessageResponse
from app.services.user_service import UserService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    create_password_reset_token,
    create_email_verification_token,
)
from app.core.auth_dependencies import get_current_user, get_current_active_user
from app.core.config import settings
from app.db.models.user import User
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service with database session"""
    return UserService(db)


# ============================================
# REGISTRATION
# ============================================


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def register(
    user_data: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Register a new user

    Creates a new user account with the provided information.
    Email verification is required before full access.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Strong password (min 8 characters)
    - **full_name**: Optional full name
    - **role**: User role (defaults to 'user')
    """
    user = await service.create_user(user_data)

    logger.info(
        "User registered",
        extra={"user_id": user.id, "username": user.username, "email": user.email},
    )

    return UserResponse.model_validate(user)


# ============================================
# LOGIN
# ============================================


@router.post("/login", response_model=Token, summary="Login user")
async def login(
    credentials: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Login with username/email and password

    Returns access and refresh tokens for authentication.

    **Request Body:**
    - **username**: Username or email
    - **password**: User password

    **Response:**
    - **access_token**: JWT access token (expires in 30 minutes)
    - **refresh_token**: JWT refresh token (expires in 7 days)
    - **token_type**: Bearer
    - **expires_in**: Token expiration in seconds
    """
    # Authenticate user
    user = await service.authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    user.last_login = datetime.utcnow()

    logger.info("User logged in", extra={"user_id": user.id, "username": user.username})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login/form", response_model=Token, summary="Login user (OAuth2 form)")
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    OAuth2 compatible login endpoint

    This endpoint follows OAuth2 password flow specification.
    Used by Swagger UI and OAuth2 clients.

    **Form Data:**
    - **username**: Username or email
    - **password**: User password
    """
    # Authenticate user
    user = await service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(
        "User logged in (OAuth2)", extra={"user_id": user.id, "username": user.username}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ============================================
# TOKEN REFRESH
# ============================================


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Refresh access token using refresh token

    When the access token expires, use the refresh token
    to obtain a new access token without re-authenticating.

    **Request Body:**
    - **refresh_token**: Valid refresh token

    **Response:**
    - New access and refresh tokens
    """
    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user exists and is active
    try:
        user = await service.get_user_by_id(int(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    # Create new tokens (token rotation)
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info("Token refreshed", extra={"user_id": user.id})

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ============================================
# USER INFO
# ============================================


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current authenticated user information

    Returns the profile of the currently authenticated user.
    Requires valid access token.
    """
    return UserResponse.model_validate(current_user)


# ============================================
# PASSWORD MANAGEMENT
# ============================================


@router.post(
    "/password/change", response_model=MessageResponse, summary="Change password"
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Change user password

    Allows authenticated users to change their password.
    Requires current password for verification.

    **Request Body:**
    - **current_password**: Current password
    - **new_password**: New password (min 8 characters)
    """
    try:
        await service.change_password(
            current_user.id, password_data.current_password, password_data.new_password
        )

        logger.info("Password changed", extra={"user_id": current_user.id})

        return MessageResponse(message="Password changed successfully", success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/password/reset/request",
    response_model=MessageResponse,
    summary="Request password reset",
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Request password reset email

    Sends a password reset token to the user's email.
    Token expires in 1 hour.

    **Request Body:**
    - **email**: User email address

    **Note:** Always returns success to prevent email enumeration
    """
    # Get user by email
    user = await service.get_user_by_email(reset_request.email)

    if user:
        # Create password reset token
        reset_token = create_password_reset_token(user.email)

        # TODO: Send email with reset token
        # For now, we'll log it (in production, send email)
        logger.info(
            "Password reset requested",
            extra={
                "user_id": user.id,
                "email": user.email,
                "reset_token": reset_token,  # Remove in production!
            },
        )

        # In development, return token in response
        # In production, only send via email
        if settings.ENVIRONMENT == "development":
            return MessageResponse(
                message=f"Password reset token (DEV ONLY): {reset_token}", success=True
            )

    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If the email exists, a password reset link has been sent", success=True
    )


@router.post(
    "/password/reset/confirm",
    response_model=MessageResponse,
    summary="Confirm password reset",
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Reset password with token

    Uses the password reset token to set a new password.

    **Request Body:**
    - **token**: Password reset token (from email)
    - **new_password**: New password (min 8 characters)
    """
    # Decode token
    payload = decode_token(reset_data.token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    # Verify token type
    if not verify_token_type(payload, "password_reset"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type"
        )

    # Get email from token
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload"
        )

    # Reset password
    try:
        await service.reset_password(email, reset_data.new_password)

        logger.info("Password reset completed", extra={"email": email})

        return MessageResponse(message="Password reset successful", success=True)
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset failed"
        )


# ============================================
# EMAIL VERIFICATION
# ============================================


@router.post(
    "/email/verification/request",
    response_model=MessageResponse,
    summary="Request email verification",
)
async def request_email_verification(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Request email verification

    Sends a verification email to the user's email address.
    Token expires in 24 hours.

    **Note:** User must be authenticated
    """
    if current_user.is_verified:
        return MessageResponse(message="Email already verified", success=True)

    # Create verification token
    verification_token = create_email_verification_token(current_user.email)

    # TODO: Send email with verification token
    # For now, we'll log it (in production, send email)
    logger.info(
        "Email verification requested",
        extra={
            "user_id": current_user.id,
            "email": current_user.email,
            "verification_token": verification_token,  # Remove in production!
        },
    )

    # In development, return token in response
    if settings.ENVIRONMENT == "development":
        return MessageResponse(
            message=f"Verification token (DEV ONLY): {verification_token}", success=True
        )

    return MessageResponse(message="Verification email sent", success=True)


@router.post(
    "/email/verification/confirm",
    response_model=MessageResponse,
    summary="Confirm email verification",
)
async def confirm_email_verification(
    verification_data: EmailVerificationRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Verify email with token

    Uses the email verification token to mark email as verified.

    **Request Body:**
    - **token**: Email verification token (from email)
    """
    # Decode token
    payload = decode_token(verification_data.token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    # Verify token type
    if not verify_token_type(payload, "email_verification"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type"
        )

    # Get email from token
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload"
        )

    # Verify email
    try:
        await service.verify_email(email)

        logger.info("Email verified", extra={"email": email})

        return MessageResponse(message="Email verified successfully", success=True)
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email verification failed"
        )


# ============================================
# LOGOUT
# ============================================


@router.post("/logout", response_model=MessageResponse, summary="Logout user")
async def logout(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Logout current user

    Since JWT tokens are stateless, logout is handled client-side
    by removing tokens from storage.

    For enhanced security, implement token blacklisting.

    **Note:** Client should delete stored tokens after this call
    """
    logger.info("User logged out", extra={"user_id": current_user.id})

    return MessageResponse(
        message="Logged out successfully. Please delete tokens from client storage.",
        success=True,
    )

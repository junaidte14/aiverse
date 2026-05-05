"""
FastAPI AI Backend - Main Application

Updated with JWT authentication
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.exceptions import AppException
from app.core.error_handlers import (
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.performance_middleware import PerformanceMiddleware
from app.utils.logger import logger
from app.db.session import close_db
from app.db.utils import check_database_connection, get_database_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(
        "Application startup",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )

    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")

    # Check database connection
    db_connected = await check_database_connection()
    if db_connected:
        print("✅ Database connection successful")
        db_info = await get_database_info()
        print(f"📊 PostgreSQL version: {db_info.get('version', 'unknown')}")
    else:
        print("❌ Database connection failed!")

    print(f"🔐 JWT Authentication enabled")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔑 Use /api/v1/auth/login to authenticate")

    yield

    # Shutdown
    logger.info("Application shutdown", extra={"app_name": settings.APP_NAME})
    print(f"👋 Shutting down {settings.APP_NAME}")
    await close_db()


def create_application() -> FastAPI:
    """Application factory pattern"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        A production-ready FastAPI backend for AI applications.
        
        ## Features
        * **JWT Authentication** with access and refresh tokens
        * **Role-Based Access Control** (RBAC)
        * **Password Management** (change, reset, verification)
        * **Email Verification** workflow
        * **OAuth2 Password Flow** for Swagger UI
        * **Database Integration** with PostgreSQL
        * **Async Operations** for high performance
        * **Repository Pattern** for clean data access
        * **Advanced Validation** with Pydantic
        * **Comprehensive Error Handling**
        * **Structured Logging**
        
        ## Authentication
        
        1. **Register**: POST /api/v1/auth/register
        2. **Login**: POST /api/v1/auth/login
        3. **Use Token**: Add `Authorization: Bearer <token>` header
        4. **Refresh**: POST /api/v1/auth/refresh when token expires
        
        ## Security
        
        * Passwords hashed with bcrypt
        * JWT tokens with expiration
        * Refresh token rotation
        * Role-based permissions
        * Password reset via email tokens
        * Email verification
        """,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(PerformanceMiddleware, slow_request_threshold=1.0)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()

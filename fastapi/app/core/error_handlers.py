"""
Global exception handlers

Centralized error handling for the entire application
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from datetime import datetime
from typing import Union

from app.core.exceptions import AppException
from app.models.error import (
    ErrorResponse,
    ValidationErrorResponse,
    ValidationError as ValidationErrorModel,
)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler for custom application exceptions

    Returns standardized error response
    """
    error_response = ErrorResponse(
        error_code=exc.error_code, message=exc.detail, path=str(request.url.path)
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response.model_dump()),
    )


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handler for Pydantic validation errors

    Transforms Pydantic errors into our standard format
    """
    errors = []

    for error in exc.errors():
        # Extract field name (might be nested)
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")

        errors.append(
            ValidationErrorModel(
                field=field, message=error["msg"], error_type=error["type"]
            )
        )

    error_response = ValidationErrorResponse(
        errors=errors, message=f"Validation failed for {len(errors)} field(s)"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response.model_dump()),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for any unhandled exceptions

    Last resort error handler
    """
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details=str(exc) if request.app.debug else None,  # Only show in debug mode
        path=str(request.url.path),
    )

    # Log the error (we'll implement proper logging later)
    print(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(error_response.model_dump()),
    )

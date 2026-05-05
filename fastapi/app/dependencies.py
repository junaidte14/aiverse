"""
Application dependencies

Reusable dependencies for FastAPI endpoints
"""

from fastapi import Header, HTTPException, status, Query, Request
from typing import Optional, Annotated
from datetime import datetime
import time
import uuid

from app.core.config import settings


# ============================================
# SIMPLE DEPENDENCIES
# ============================================


async def get_current_timestamp() -> datetime:
    """
    Get current timestamp

    Returns:
        Current datetime
    """
    return datetime.now()


async def verify_token(x_token: Annotated[Optional[str], Header()] = None) -> str:
    """
    Verify API token from header

    Args:
        x_token: Token from X-Token header

    Returns:
        Token if valid

    Raises:
        HTTPException: If token is invalid or missing
    """
    if x_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Token header missing"
        )

    # TODO: Replace with database lookup or JWT verification
    valid_tokens = ["secret-token-123", "admin-token-456"]

    if x_token not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return x_token


async def verify_api_key(api_key: Annotated[Optional[str], Query()] = None) -> str:
    """
    Verify API key from query parameter

    Args:
        api_key: API key from query parameter

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )

    # TODO: Replace with database lookup
    valid_keys = ["key-12345", "key-67890"]

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return api_key


# ============================================
# DEPENDENCY CLASSES
# ============================================


class CommonQueryParams:
    """
    Common query parameters for list endpoints

    Provides standard pagination and sorting parameters
    """

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(10, ge=1, le=100, description="Max records to return"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query(
            "asc", pattern="^(asc|desc)$", description="Sort order"
        ),
    ):
        self.skip = skip
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order


class RateLimiter:
    """
    Rate limiter dependency

    Limits requests per time window based on client IP
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    async def __call__(self, request: Request) -> bool:
        """
        Check rate limit for client

        Args:
            request: FastAPI request object

        Returns:
            True if request is allowed

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Use client IP as identifier
        client_id = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old requests outside window
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time
                for req_time in self.requests[client_id]
                if current_time - req_time < self.window_seconds
            ]
        else:
            self.requests[client_id] = []

        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds.",
            )

        # Add current request
        self.requests[client_id].append(current_time)

        return True


# ============================================
# REQUEST CONTEXT
# ============================================


class RequestContext:
    """
    Request context with aggregated request information

    Combines multiple request attributes into a single object
    """

    def __init__(
        self,
        request: Request,
        request_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.request = request
        self.request_id = request_id or str(uuid.uuid4())
        self.user_agent = user_agent or "unknown"
        self.timestamp = timestamp or datetime.now()
        self.client_ip = request.client.host if request.client else "unknown"
        self.method = request.method
        self.url = str(request.url)


async def get_request_context(
    request: Request,
    request_id: Annotated[Optional[str], Header(alias="X-Request-ID")] = None,
    user_agent: Annotated[Optional[str], Header(alias="User-Agent")] = None,
) -> RequestContext:
    """
    Build request context from multiple dependencies

    Args:
        request: FastAPI request object
        request_id: Optional request ID from header
        user_agent: Optional user agent from header

    Returns:
        RequestContext object with aggregated information
    """
    return RequestContext(
        request=request,
        request_id=request_id,
        user_agent=user_agent,
        timestamp=datetime.now(),
    )


# ============================================
# RESOURCE DEPENDENCIES WITH CLEANUP
# ============================================


async def get_db_session():
    """
    Database session dependency (example)

    Demonstrates generator pattern for resources needing cleanup

    Yields:
        Database session object
    """
    # Setup: Create session
    db = {"connected": True, "session_id": f"session-{uuid.uuid4().hex[:8]}"}

    try:
        yield db
    finally:
        # Cleanup: Close session
        db["connected"] = False


# ============================================
# CACHED DEPENDENCIES
# ============================================


from functools import lru_cache


@lru_cache()
def get_expensive_resource():
    """
    Expensive resource that should be cached

    The @lru_cache decorator ensures this is only computed once
    and the result is reused for subsequent calls

    Returns:
        Cached resource data
    """
    return {"data": "expensive computation result", "computed_at": datetime.now()}


def get_settings():
    """
    Get application settings

    Returns:
        Settings instance
    """
    from app.core.config import get_settings

    return get_settings()

"""
Performance monitoring middleware

Tracks slow requests and performance metrics
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import logger
from app.utils.metrics import http_requests_total, http_request_duration_seconds


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Monitor request performance

    Logs warnings for slow requests
    """

    def __init__(self, app, slow_request_threshold: float = 1.0):
        """
        Initialize performance middleware

        Args:
            app: ASGI application
            slow_request_threshold: Threshold in seconds for slow request warning
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next):
        """Monitor request performance"""
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method, endpoint=request.url.path
        ).observe(duration)

        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                "Slow request detected",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "duration_seconds": round(duration, 2),
                    "threshold_seconds": self.slow_request_threshold,
                },
            )

        return response

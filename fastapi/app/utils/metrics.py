"""
Prometheus metrics for monitoring

Track application performance and health
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# Request metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

# Database metrics
db_connections_active = Gauge("db_connections_active", "Active database connections")

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds", "Database query duration", ["query_type"]
)

# Authentication metrics
auth_attempts_total = Counter(
    "auth_attempts_total", "Total authentication attempts", ["status"]
)

# Business metrics
active_users = Gauge("active_users", "Number of active users")

conversations_total = Counter("conversations_total", "Total conversations created")


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

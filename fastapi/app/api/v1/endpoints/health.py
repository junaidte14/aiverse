"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from app.models.common import HealthCheck
from app.core.config import Settings, get_settings
from app.db.utils import check_database_connection
from app.utils.metrics import active_users, db_connections_active
import datetime
from app.utils.metrics import metrics_endpoint

router = APIRouter(tags=["Health"])


# Add before routers
@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()


@router.get("/health/detailed")
async def detailed_health_check(settings: Settings = Depends(get_settings)):
    """
    Detailed health check with component status

    Returns health status of all system components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "components": {},
    }

    # Check database
    try:
        db_healthy = await check_database_connection()
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_ms": 0,  # Add actual timing
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Redis (if implemented)
    # health_status["components"]["redis"] = {...}

    # System metrics
    import psutil

    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }

    return health_status


@router.get("/health", response_model=HealthCheck)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint

    Returns current system status and version information
    """
    return HealthCheck(
        status="healthy", version=settings.APP_VERSION, environment=settings.ENVIRONMENT
    )


@router.get("/health/database")
async def database_health():
    """DB health check endpoint"""
    from app.db.utils import check_database_connection, get_database_info

    is_connected = await check_database_connection()
    info = await get_database_info()

    return {"status": "healthy" if is_connected else "unhealthy", "database": info}


@router.get("/health/ollama")
async def debug_ollama():
    """Ollama health check endpoint"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:11434/api/tags")
            return {"status_code": r.status_code, "json": r.json()}
    except Exception as e:
        return {"error": str(e)}


@router.get("/")
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics",
    }

"""
API v1 router aggregator

Combines all v1 endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    users,
    auth,
    health,
    conversations,
    ai_multi,
    admin,
    rag,
)

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(conversations.router)
api_router.include_router(ai_multi.router)
api_router.include_router(admin.router)
api_router.include_router(rag.router)

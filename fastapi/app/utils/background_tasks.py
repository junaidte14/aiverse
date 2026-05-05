"""
Background task utilities

Functions that run asynchronously after response is sent
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

from app.utils.logger import logger


async def send_welcome_email(email: str, username: str):
    """
    Send welcome email (simulated)

    In production, this would integrate with email service
    """
    logger.info("Sending welcome email", extra={"email": email, "username": username})

    # Simulate email sending delay
    await asyncio.sleep(2)

    logger.info("Welcome email sent", extra={"email": email, "username": username})


async def process_user_analytics(user_id: int, event: str, metadata: Dict[str, Any]):
    """
    Process user analytics event

    This runs in background without blocking the response
    """
    logger.info(
        "Processing analytics event",
        extra={"user_id": user_id, "event": event, "metadata": metadata},
    )

    # Simulate analytics processing
    await asyncio.sleep(1)

    logger.info("Analytics event processed", extra={"user_id": user_id, "event": event})


async def cleanup_old_data(days: int = 30):
    """
    Cleanup old data (example background task)
    """
    logger.info(f"Starting data cleanup (older than {days} days)")

    # Simulate cleanup process
    await asyncio.sleep(3)

    logger.info("Data cleanup completed")


def log_user_activity(user_id: int, action: str, details: Dict[str, Any] = None):
    """
    Log user activity (synchronous background task)

    This can be a non-async function too
    """
    logger.info(
        "User activity logged",
        extra={
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        },
    )

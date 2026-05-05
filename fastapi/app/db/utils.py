"""
Database utilities

Helper functions for database operations
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.db.session import async_session_maker, engine
from app.db.base import Base
from app.core.config import settings


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session

    Usage:
        async with get_db_context() as db:
            user = await db.execute(select(User))
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """
    Initialize database

    Creates all tables if they don't exist
    WARNING: Only use in development. Use Alembic migrations in production.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized")


async def drop_database() -> None:
    """
    Drop all database tables

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("🗑️  Database dropped")


async def reset_database() -> None:
    """
    Reset database (drop and recreate)

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    await drop_database()
    await init_database()
    print("🔄 Database reset complete")


async def check_database_connection() -> bool:
    """
    Check if database connection is working
    """
    try:
        async with engine.connect() as conn:
            # Wrap the string in text()
            await conn.execute(text("SELECT 1"))
            # Also, since it's an async connection, you should commit or just use
            # .execute() which is enough for a health check.
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get database information

    Returns:
        Dictionary with database info
    """
    from sqlalchemy import text

    info = {
        "url": settings.DATABASE_URL.replace(settings.SECRET_KEY, "***"),
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
    }

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            info["version"] = version
            info["connected"] = True
    except Exception as e:
        info["connected"] = False
        info["error"] = str(e)

    return info

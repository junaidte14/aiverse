"""
Database seeding

Populate database with initial/test data
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.db.models.user import User, UserRole
from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageRole
from app.utils.logger import logger

from app.core.security import hash_password, verify_password


async def seed_users(session: AsyncSession) -> list[User]:
    """
    Seed users

    Creates demo users for development/testing
    """
    users = [
        User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        ),
        User(
            username="john_doe",
            email="john@example.com",
            hashed_password=hash_password("password123"),
            full_name="John Doe",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        ),
        User(
            username="jane_smith",
            email="jane@example.com",
            hashed_password=hash_password("password123"),
            full_name="Jane Smith",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        ),
    ]

    session.add_all(users)
    await session.flush()

    logger.info(f"Seeded {len(users)} users")
    return users


async def seed_conversations(
    session: AsyncSession, users: list[User]
) -> list[Conversation]:
    """
    Seed conversations

    Creates demo conversations for users
    """
    conversations = [
        Conversation(
            user_id=users[1].id,  # john_doe
            title="Getting Started with FastAPI",
            model_name="llama2",
        ),
        Conversation(
            user_id=users[1].id,  # john_doe
            title="Python Best Practices",
            model_name="llama2",
        ),
        Conversation(
            user_id=users[2].id,  # jane_smith
            title="Database Design Questions",
            model_name="mistral",
        ),
    ]

    session.add_all(conversations)
    await session.flush()

    logger.info(f"Seeded {len(conversations)} conversations")
    return conversations


async def seed_messages(
    session: AsyncSession, conversations: list[Conversation]
) -> list[Message]:
    """
    Seed messages

    Creates demo messages for conversations
    """
    messages = [
        # Conversation 1 messages
        Message(
            conversation_id=conversations[0].id,
            role=MessageRole.USER,
            content="What is FastAPI and why should I use it?",
        ),
        Message(
            conversation_id=conversations[0].id,
            role=MessageRole.ASSISTANT,
            content="FastAPI is a modern, fast web framework for building APIs with Python. It's built on Starlette and Pydantic, offering automatic API documentation, data validation, and async support out of the box.",
        ),
        Message(
            conversation_id=conversations[0].id,
            role=MessageRole.USER,
            content="How do I create my first endpoint?",
        ),
        Message(
            conversation_id=conversations[0].id,
            role=MessageRole.ASSISTANT,
            content="Here's a simple example:\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\nasync def root():\n    return {'message': 'Hello World'}\n```",
        ),
        # Conversation 2 messages
        Message(
            conversation_id=conversations[1].id,
            role=MessageRole.USER,
            content="What are some Python best practices?",
        ),
        Message(
            conversation_id=conversations[1].id,
            role=MessageRole.ASSISTANT,
            content="Key Python best practices include: use type hints, follow PEP 8, write docstrings, use virtual environments, handle exceptions properly, and write tests.",
        ),
        # Conversation 3 messages
        Message(
            conversation_id=conversations[2].id,
            role=MessageRole.USER,
            content="Should I use ORM or raw SQL?",
        ),
        Message(
            conversation_id=conversations[2].id,
            role=MessageRole.ASSISTANT,
            content="Both have their place. ORMs like SQLAlchemy provide abstraction, type safety, and easier migrations. Raw SQL offers more control and can be more performant for complex queries. For most applications, start with an ORM.",
        ),
    ]

    session.add_all(messages)
    await session.flush()

    logger.info(f"Seeded {len(messages)} messages")
    return messages


async def seed_database() -> None:
    """
    Seed database with all demo data

    Creates users, conversations, and messages
    """
    async with async_session_maker() as session:
        try:
            # Seed in order (users first, then conversations, then messages)
            users = await seed_users(session)
            conversations = await seed_conversations(session, users)
            messages = await seed_messages(session, conversations)

            await session.commit()

            logger.info("✅ Database seeding complete")
            print("✅ Database seeded successfully!")
            print(f"   - {len(users)} users")
            print(f"   - {len(conversations)} conversations")
            print(f"   - {len(messages)} messages")

        except Exception as e:
            await session.rollback()
            logger.error(f"Database seeding failed: {e}")
            print(f"❌ Seeding failed: {e}")
            raise


if __name__ == "__main__":
    """Run seeding directly"""
    import asyncio

    asyncio.run(seed_database())

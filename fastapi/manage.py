"""
Database management script

Provides CLI commands for database operations
"""

import asyncio
import sys
from app.db.utils import (
    init_database,
    drop_database,
    reset_database,
    check_database_connection,
    get_database_info,
)
from app.db.seed import seed_database


async def main():
    """Main CLI handler"""
    if len(sys.argv) < 2:
        print("""
Usage: python manage.py <command>

Commands:
  init       - Initialize database (create tables)
  drop       - Drop all tables (WARNING: deletes all data)
  reset      - Drop and recreate all tables (WARNING: deletes all data)
  seed       - Seed database with demo data
  check      - Check database connection
  info       - Show database information
        """)
        return

    command = sys.argv[1]

    if command == "init":
        await init_database()

    elif command == "drop":
        confirm = input("⚠️  This will delete ALL data. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            await drop_database()
        else:
            print("Operation cancelled")

    elif command == "reset":
        confirm = input(
            "⚠️  This will delete ALL data and recreate tables. Continue? (yes/no): "
        )
        if confirm.lower() == "yes":
            await reset_database()
        else:
            print("Operation cancelled")

    elif command == "seed":
        await seed_database()

    elif command == "check":
        connected = await check_database_connection()
        if connected:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")

    elif command == "info":
        info = await get_database_info()
        print("\n📊 Database Information:")
        for key, value in info.items():
            print(f"   {key}: {value}")

    else:
        print(f"Unknown command: {command}")
        print("Run 'python manage.py' for help")


if __name__ == "__main__":
    asyncio.run(main())

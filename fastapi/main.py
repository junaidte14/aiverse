"""
Application entry point

Run with: uvicorn main:app --reload
"""

from app.main import app

# This file exists so we can run: uvicorn main:app
# which is simpler than: uvicorn app.main:app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )

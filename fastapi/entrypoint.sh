#!/bin/bash
set -e

echo "📦 Running migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI (Lean Mode)..."
# Using uvicorn directly with a single worker to save ~150MB of RAM
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --log-level info
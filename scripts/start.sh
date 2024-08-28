#!/bin/sh

echo "Starting migrations..."
alembic upgrade head
echo "Finished migration"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
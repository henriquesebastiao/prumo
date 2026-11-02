#!/bin/sh
# Applies pending migrations, then runs the given command (Uvicorn by default).
set -eu
cd /app
alembic upgrade head
exec "$@"

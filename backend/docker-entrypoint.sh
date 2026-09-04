#!/usr/bin/env bash
# docker-entrypoint.sh — runs DB migrations and optional seed, then hands off to uvicorn
set -e

cd /app

if [ "$1" = "migrate" ]; then
    echo "[entrypoint] Running alembic migrations..."
    alembic upgrade head
    echo "[entrypoint] Migrations complete."
    exec alembic upgrade head
elif [ "$1" = "shell" ]; then
    echo "[entrypoint] Starting interactive shell."
    exec /bin/bash
fi

# Default: migrate -> start server
echo "[entrypoint] Running database migrations..."
alembic upgrade head 2>&1 || {
    echo "[entrypoint] WARNING: migrations failed, continuing anyway."
}

echo "[entrypoint] Starting BedaanWaves backend on port ${API_PORT:-3000}..."

if [ "$1" = "start" ] || [ "$1" = "uvicorn" ] || [ -z "$1" ]; then
    shift
    exec uvicorn app.main:app \
        --host "${API_HOST:-0.0.0.0}" \
        --port "${API_PORT:-3000}" \
        --workers "${UVICORN_WORKERS:-4}" \
        "$@"
fi

exec "$@"

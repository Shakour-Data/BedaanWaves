# Backend Dockerfile — BedaanWaves FastAPI service
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system deps needed by psycopg2 / asyncpg and alembic
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source, database migration tooling, ML models, and scripts
COPY app/ ./app/
COPY database/ ./database/
COPY alembic.ini ./
COPY scripts/ ./scripts/
COPY models/ ./models/
COPY requirements.lock ./

# Non-root user for runtime
RUN useradd --uid 1000 --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 3000

# Entrypoint runs migrations then starts the server
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]

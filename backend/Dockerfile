# syntax=docker/dockerfile:1.7

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code and config
COPY pyproject.toml uv.lock alembic.ini ./
COPY src/ ./src/
COPY alembic/ ./alembic/

# Ensure venv is used
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

# Default command to run the application
CMD ["uvicorn", "talkingcode.app:app", "--host", "0.0.0.0", "--port", "8000"]

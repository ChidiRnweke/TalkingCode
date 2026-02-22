FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "talkingcode.app:app", "--host", "0.0.0.0", "--port", "8000"]

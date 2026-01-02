FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system

# Copy application code
COPY src/ ./src/

# Run Celery worker
CMD ["celery", "-A", "src.celery_app", "worker", "--loglevel=info"]

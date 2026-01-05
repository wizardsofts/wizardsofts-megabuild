FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt ./

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/health')"

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "5001"]

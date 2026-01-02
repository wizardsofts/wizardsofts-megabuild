# GIBD-News Docker Image
# Multi-stage build for optimized image size

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for Chrome, PostgreSQL, and MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libpq-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome (updated for modern Debian/Ubuntu)
RUN wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && mkdir -p /etc/apt/keyrings \
    && gpg --dearmor < /tmp/google-chrome-key.pub > /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/google-chrome-key.pub

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Set default environment variables
ENV ACTIVE_PROFILE=docker

# Health check - verify config can be loaded
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from scripts.config_loader import get_api_keys; print('Config OK')" || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "scripts.news_summarizer"]


# ============================================
# Test Stage - for running tests in CI/CD
# ============================================
FROM base as test

# Install test dependencies
RUN pip install pytest pytest-cov

# Run tests
CMD ["pytest", "scripts/tests/", "-v", "--cov=scripts", "--cov-report=term-missing"]


# ============================================
# Production Stage - minimal image
# ============================================
FROM base as production

# Remove test files and unnecessary items
RUN rm -rf scripts/tests/ \
    && rm -rf .git \
    && rm -rf __pycache__ \
    && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Create non-root user for security
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# Default to news summarizer
CMD ["python", "-m", "scripts.news_summarizer"]

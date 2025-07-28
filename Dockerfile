# Multi-stage build for AI Agent Platform Backend
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base AS production

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser

# Create necessary directories
RUN mkdir -p /app/data \
    /app/agent_documents \
    /app/agent_vectors \
    /app/vanna_cache \
    /app/logs \
    /app/src \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Set proper permissions
RUN chmod +x /app/main.py

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app \
    PORT=3006 \
    ENVIRONMENT=production

# Expose port
EXPOSE 3006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3006/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3006", "--workers", "2"]

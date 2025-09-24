# Multi-stage build for TelegramNewsFeedBot
# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies with trusted hosts
RUN pip install --user --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/botuser/.local/bin:$PATH"

# Create non-root user
RUN groupadd --gid 1000 botuser && \
    useradd --uid 1000 --gid botuser --shell /bin/bash --create-home botuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/botuser/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=botuser:botuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/media_cache /app/data && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Create volume mount points
VOLUME ["/app/data", "/app/logs", "/app/media_cache"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import sys; from config import config; config.validate(); sys.exit(0)" || exit 1

# Expose port (if webhook mode is used)
EXPOSE 8443

# Default command
CMD ["python", "main.py"]
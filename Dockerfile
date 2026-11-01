# ==============================================================================
# Multi-Stage Production Dockerfile — Empório AI
# Designed for high security, minimal image size, and fast container startups.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Dependencies (Builder)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Prevent Python from writing .pyc and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal build tools required for native C extension compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Upgrade build tools
RUN pip install --upgrade pip setuptools wheel

# Copy dependency definition and install packages
COPY pyproject.toml .
RUN pip install .


# ------------------------------------------------------------------------------
# Stage 2: Runtime Environment (Runner)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

# OCI Metadata Annotations
LABEL org.opencontainers.image.title="Empório AI" \
      org.opencontainers.image.description="Intelligent Customer Service Agent for Empório da Música" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Artefact AI Engineer Candidate" \
      org.opencontainers.image.licenses="Proprietary"

# Runtime Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root dedicated user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy virtualenv from builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

WORKDIR /app

# Copy application source code and datasets
COPY --chown=appuser:appgroup . /app

# Ensure entrypoint script is executable
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-privileged user for enhanced container security
USER appuser

# Expose Streamlit application port
EXPOSE 8501

# Container Healthcheck targeting Streamlit core endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch self-bootstrapping entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["streamlit", "run", "app/main.py"]

# Multi-stage hardened production Dockerfile for Footfall MCP Server (Section 12.2, 13.3)
# - Non-root execution (UID 10001)
# - Minimal base image
# - Healthcheck on /health/live
# - Read-only filesystem compatible

# Stage 1: Build virtual environment with uv
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first for optimal Docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install package
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Stage 2: Hardened runtime
FROM python:3.12-slim AS runner

# Security: Create unprivileged user with explicit UID/GID
RUN groupadd -g 10001 footfall && \
    useradd -u 10001 -g footfall -s /usr/sbin/nologin -M -d /app footfall

WORKDIR /app

# Copy isolated virtual environment and application assets
COPY --from=builder --chown=footfall:footfall /app/.venv /app/.venv
COPY --chown=footfall:footfall src/ /app/src/
COPY --chown=footfall:footfall registry/ /app/registry/
COPY --chown=footfall:footfall exports/ /app/exports/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Drop all privileges
USER 10001:10001

EXPOSE 8000

# Container healthcheck: verify liveness probe every 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1

ENTRYPOINT ["python", "-m", "footfall.cli", "serve", "--host", "0.0.0.0", "--port", "8000", "--exports-dir", "exports/v1"]

# -----------------------------------------------------------------------------
# Stage 1 – Builder
# -----------------------------------------------------------------------------
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only what is needed to install the package
COPY pyproject.toml README.md ./
COPY src ./src

# Create a virtual environment and install the project + dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .


# -----------------------------------------------------------------------------
# Stage 2 – Runtime
# -----------------------------------------------------------------------------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create a non-root user
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY --chown=appuser:appgroup src ./src

# Switch to non-root user
USER appuser

EXPOSE 8000

# For development you can override this with --reload in docker-compose
CMD ["uvicorn", "chinese_learning.app:app", "--host", "0.0.0.0", "--port", "8000"]
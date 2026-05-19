FROM python:3.11-slim

# Keep Python logs immediate and avoid writing .pyc files into mounted source.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages:
# - curl: useful for container debugging and optional health checks
# - build-essential: needed by some ML/scientific Python wheels when no wheel is available
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies before copying source so Docker can reuse this layer
# when only application code changes.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application after dependencies for better layer caching.
COPY . .

# Run as a non-root user for safer container execution.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Suggested .dockerignore entries:
# .git
# __pycache__/
# *.pyc
# .env
# .venv/
# venv/
# .DS_Store
# dist/
# build/
CMD ["uvicorn", "backend.api.ml_app:app", "--host", "0.0.0.0", "--port", "8000"]

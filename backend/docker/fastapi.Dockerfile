FROM python:3.11-slim-bookworm AS base

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=600 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install minimal system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip and install all requirements in consolidated layers
COPY backend/fastapi_app/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --timeout=1800 \
    "sentence-transformers>=2.2.0" \
    "numpy>=1.24.0" && \
    pip install --timeout=600 -r /tmp/requirements.txt

# Copy application code
COPY backend/fastapi_app/ .

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

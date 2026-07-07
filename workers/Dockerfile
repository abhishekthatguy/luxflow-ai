FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# PaddleOCR runtime libraries (Phase 1 scanned PDF OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml apps/api/README.md ./apps/api/
COPY apps/api/src ./apps/api/src

WORKDIR /app/apps/api
RUN pip install --no-cache-dir -e ".[dev,ocr]"

WORKDIR /app
ENV PYTHONPATH=/app/apps/api/src

CMD ["celery", "-A", "lexflow_api.celery_app:celery_app", "worker", "--loglevel=INFO", "-Q", "platform.default"]

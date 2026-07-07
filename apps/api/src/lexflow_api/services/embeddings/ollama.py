"""Ollama embedding API (Phase 1 pgvector indexing)."""

from __future__ import annotations

import logging

import httpx

from lexflow_api.config import settings

logger = logging.getLogger(__name__)


def embed_texts(texts: list[str]) -> list[list[float] | None]:
    """Return embedding vectors; None entries when Ollama is unavailable."""
    if not settings.embedding_enabled or not texts:
        return [None] * len(texts)

    url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
    model = settings.ollama_embedding_model
    vectors: list[list[float] | None] = []

    try:
        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            for text in texts:
                response = client.post(url, json={"model": model, "prompt": text})
                if response.status_code != 200:
                    logger.warning("Ollama embedding failed: HTTP %s", response.status_code)
                    vectors.append(None)
                    continue
                embedding = response.json().get("embedding")
                if not isinstance(embedding, list):
                    vectors.append(None)
                    continue
                vectors.append([float(v) for v in embedding])
    except httpx.HTTPError:
        logger.exception("Ollama embeddings unavailable — chunks stored without vectors")
        return [None] * len(texts)

    return vectors

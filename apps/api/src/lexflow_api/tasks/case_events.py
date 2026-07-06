"""Celery task stub for processing case outbox events."""

from __future__ import annotations

import logging
from typing import Any

from lexflow_api.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="lexflow_api.tasks.case_events.process_outbox_batch")  # type: ignore[untyped-decorator]
def process_outbox_batch(limit: int = 100) -> dict[str, Any]:
    """Stub: mark outbox events for async publishing (RabbitMQ / n8n)."""
    logger.info("process_outbox_batch stub invoked", extra={"limit": limit})
    return {"processed": 0, "status": "stub"}

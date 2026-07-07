"""Workflow deduplication — prevent duplicate auto/manual executions."""

from __future__ import annotations

from uuid import UUID


def workflow_event_key(*, slug: str, aggregate_id: UUID | str) -> str:
    """Deterministic key for event-driven triggers (one run per aggregate)."""
    return f"event:{slug}:{aggregate_id}"


def workflow_manual_key(*, slug: str, case_id: UUID | None, idempotency_key: str) -> str:
    """Client-supplied idempotency for manual triggers."""
    scope = str(case_id) if case_id else "firm"
    return f"manual:{slug}:{scope}:{idempotency_key}"


def document_upload_key(document_id: UUID | str) -> str:
    return workflow_event_key(slug="document-upload-v1", aggregate_id=document_id)


def client_created_key(client_id: UUID | str) -> str:
    return workflow_event_key(slug="client-created-v1", aggregate_id=client_id)


def case_intake_key(case_id: UUID | str) -> str:
    return workflow_event_key(slug="case-intake-v1", aggregate_id=case_id)

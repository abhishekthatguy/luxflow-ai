#!/usr/bin/env python3
"""Clear stale failed workflow runs and stuck async jobs after n8n/import fixes."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import delete, select, update

from lexflow_api.db.session import async_session_factory
from lexflow_api.models.shared import AsyncJob
from lexflow_api.models.workflows import WorkflowDefinition, WorkflowExecution

STALE_WORKFLOW_AFTER = timedelta(hours=1)
STALE_JOB_AFTER = timedelta(minutes=30)


async def cleanup() -> None:
    workflow_cutoff = datetime.now(UTC) - STALE_WORKFLOW_AFTER
    job_cutoff = datetime.now(UTC) - STALE_JOB_AFTER
    async with async_session_factory() as session:
        legacy_ids = (
            await session.execute(
                select(WorkflowDefinition.id).where(
                    WorkflowDefinition.slug == "document-upload-notify-v1"
                )
            )
        ).scalars().all()

        removed_404 = (
            await session.execute(
                delete(WorkflowExecution).where(
                    WorkflowExecution.status == "failed",
                    WorkflowExecution.error_message.ilike("%404%"),
                )
            )
        ).rowcount

        removed_legacy = 0
        if legacy_ids:
            removed_legacy = (
                await session.execute(
                    delete(WorkflowExecution).where(
                        WorkflowExecution.workflow_definition_id.in_(legacy_ids)
                    )
                )
            ).rowcount

        cancelled_queued = (
            await session.execute(
                update(WorkflowExecution)
                .where(
                    WorkflowExecution.status == "queued",
                    WorkflowExecution.created_at < workflow_cutoff,
                )
                .values(
                    status="cancelled",
                    error_message="Cancelled — stale queued run after infrastructure fix",
                    completed_at=datetime.now(UTC),
                )
            )
        ).rowcount

        cleared_jobs = (
            await session.execute(
                update(AsyncJob)
                .where(
                    AsyncJob.status.in_(("queued", "running")),
                    AsyncJob.created_at < job_cutoff,
                )
                .values(
                    status="failed",
                    error={"message": "Stale job cleared after worker/n8n fix"},
                    completed_at=datetime.now(UTC),
                )
            )
        ).rowcount

        await session.commit()
        print(
            f"OK  cleanup: removed_404={removed_404}, removed_legacy={removed_legacy}, "
            f"cancelled_queued={cancelled_queued}, cleared_jobs={cleared_jobs}"
        )


def main() -> None:
    asyncio.run(cleanup())


if __name__ == "__main__":
    main()

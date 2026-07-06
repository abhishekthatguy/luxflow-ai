"""Seed Sprint 4 prompt templates and workflow definitions (idempotent)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.db.session import async_session_factory
from lexflow_api.models.ai import PromptTemplate
from lexflow_api.models.identity import Firm
from lexflow_api.models.workflows import TriggerType, WorkflowDefinition

DOCUMENT_SUMMARY_TEMPLATE = """You are a legal research assistant.

Summarize the following case materials for attorney review.

Case: {{ case_title }}

Materials:
{{ context }}

Provide a concise summary with key facts, issues, and recommended next steps.
"""

async def seed_sprint4() -> None:
    async with async_session_factory() as session:
        firm = (
            await session.execute(select(Firm).where(Firm.slug == "lexflow-dev"))
        ).scalar_one_or_none()
        if firm is None:
            print("Run seed_dev.py first (firm lexflow-dev missing).")
            return

        existing_template = (
            await session.execute(
                select(PromptTemplate).where(PromptTemplate.slug == "document-summary-v1")
            )
        ).scalar_one_or_none()
        if existing_template is None:
            session.add(
                PromptTemplate(
                    name="Document Summary v1",
                    slug="document-summary-v1",
                    version=1,
                    template=DOCUMENT_SUMMARY_TEMPLATE,
                    llm_config={
                        "provider": "stub",
                        "model": "stub-gpt-4o",
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    },
                    requires_approval=True,
                    description="Default document/case summary template for Sprint 4",
                )
            )
            print("OK  Seeded prompt template document-summary-v1")

        existing_wf = (
            await session.execute(
                select(WorkflowDefinition).where(
                    WorkflowDefinition.slug == "document-upload-notify-v1"
                )
            )
        ).scalar_one_or_none()
        if existing_wf is None:
            session.add(
                WorkflowDefinition(
                    firm_id=None,
                    name="Document Upload Notify",
                    slug="document-upload-notify-v1",
                    description="Notify case team when a document is uploaded",
                    n8n_workflow_id="document-upload-notify-v1",
                    trigger_type=TriggerType.EVENT.value,
                    is_active=True,
                )
            )
            print("OK  Seeded workflow definition document-upload-notify-v1")

        await session.commit()
        print("✅ Sprint 4 seed complete")


def main() -> None:
    asyncio.run(seed_sprint4())


if __name__ == "__main__":
    main()

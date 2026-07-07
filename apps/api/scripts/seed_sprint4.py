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
from lexflow_api.models.workflows import WorkflowDefinition

DOCUMENT_SUMMARY_TEMPLATE = """You are a legal assistant preparing an attorney-review draft.

Summarize ONLY from the case materials below. Use exact names, dates, locations, and amounts from the documents — do not invent facts or reuse generic examples.

Case: {{ case_title }}

Materials:
{{ context }}

Write a markdown summary with these sections (omit a section only if the documents contain no relevant information):

### Incident Overview
### People Involved
### Injuries & Medical
### Insurance & Claim
### Potential Liability
### Recommended Next Actions

End with: _Attorney review required before sharing with the team or client._
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
                        "provider": "ollama",
                        "model": "qwen2.5:latest",
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    },
                    requires_approval=True,
                    description="Default document/case summary template for Sprint 4",
                )
            )
            print("OK  Seeded prompt template document-summary-v1")
        else:
            existing_template.template = DOCUMENT_SUMMARY_TEMPLATE
            existing_template.llm_config = {
                "provider": "ollama",
                "model": "qwen2.5:latest",
                "temperature": 0.3,
                "max_tokens": 4096,
            }
            existing_template.version = max(existing_template.version, 2)
            print("OK  Updated prompt template document-summary-v1 (ollama + structured prompt)")

        existing_wf = (
            await session.execute(
                select(WorkflowDefinition).where(
                    WorkflowDefinition.slug == "document-upload-v1"
                )
            )
        ).scalar_one_or_none()
        if existing_wf is None:
            print("Run make seed-workflows for full enterprise catalog.")

        await session.commit()
        print("✅ Sprint 4 seed complete")


def main() -> None:
    asyncio.run(seed_sprint4())


if __name__ == "__main__":
    main()

"""Seed enterprise workflow definitions from n8n/workflows/catalog.json (idempotent)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.db.session import async_session_factory
from lexflow_api.models.workflows import TriggerType, WorkflowDefinition

CATALOG_PATH = Path(__file__).resolve().parent / "data" / "workflow_catalog.json"

TRIGGER_MAP = {
    "webhook": TriggerType.EVENT.value,
    "schedule": TriggerType.SCHEDULE.value,
    "manual": TriggerType.MANUAL.value,
}


def _load_catalog() -> list[dict[str, object]]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Run: python3 scripts/n8n/build_workflows.py ({CATALOG_PATH})")
    return json.loads(CATALOG_PATH.read_text())


async def seed_workflows() -> None:
    catalog = _load_catalog()
    async with async_session_factory() as session:
        for item in catalog:
            slug = str(item["slug"])
            meta = dict(item["meta"])  # type: ignore[arg-type]
            meta["tags"] = item.get("tags", meta.get("tags", []))
            meta["group"] = item.get("group", meta.get("group", ""))
            trigger = TRIGGER_MAP.get(str(item["trigger"]), TriggerType.EVENT.value)

            existing = (
                await session.execute(
                    select(WorkflowDefinition).where(WorkflowDefinition.slug == slug)
                )
            ).scalar_one_or_none()

            if existing is None:
                session.add(
                    WorkflowDefinition(
                        firm_id=None,
                        name=str(item.get("display_name", item["name"])),
                        slug=slug,
                        description=str(meta.get("purpose", "")),
                        n8n_workflow_id=slug,
                        trigger_type=trigger,
                        is_active=True,
                        config_schema=meta,
                        version=int(meta.get("version", 1)),
                    )
                )
                print(f"OK  Seeded workflow {slug}")
            else:
                existing.name = str(item.get("display_name", item["name"]))
                existing.description = str(meta.get("purpose", ""))
                existing.n8n_workflow_id = slug
                existing.trigger_type = trigger
                existing.is_active = True
                existing.config_schema = meta
                existing.version = int(meta.get("version", 1))
                print(f"OK  Updated workflow {slug}")

        legacy = (
            await session.execute(
                select(WorkflowDefinition).where(
                    WorkflowDefinition.slug == "document-upload-notify-v1"
                )
            )
        ).scalar_one_or_none()
        if legacy is not None:
            legacy.is_active = False
            print("OK  Deactivated legacy document-upload-notify-v1")

        await session.commit()
        print(f"✅ Workflow catalog seed complete ({len(catalog)} definitions)")


def main() -> None:
    asyncio.run(seed_workflows())


if __name__ == "__main__":
    main()

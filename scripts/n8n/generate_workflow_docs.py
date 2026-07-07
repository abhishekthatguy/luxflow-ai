#!/usr/bin/env python3
"""Generate workflow documentation from n8n/workflows/catalog.json."""

from __future__ import annotations

import json
from pathlib import Path

from workflow_groups import GROUPS

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "n8n" / "workflows" / "catalog.json"
DOCS_OUT = ROOT / "docs" / "06-workflows"
N8N_README = ROOT / "n8n" / "workflows" / "README.md"


def _load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text())


def _steps_md(steps: list) -> str:
    if not steps:
        return "_No steps (manual trigger only)._"
    lines = []
    for i, step in enumerate(steps, 1):
        if isinstance(step, list) and len(step) >= 2:
            lines.append(f"{i}. **{step[1]}** (`{step[0]}`)")
        else:
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


def generate_workflow_index(catalog: list[dict]) -> str:
    """Quick-reference table: serial, folder, slug, one-liner."""
    lines = [
        "# Workflow Index — Quick Reference",
        "",
        "Canonical naming: **`WF-NN · Short Title`** (e.g. `WF-02 · Document Upload Pipeline`).",
        "Webhook slugs (`document-upload-v1`) are stable API identifiers — do not change.",
        "",
        "| # | n8n name | Folder | Slug | Trigger | One-liner |",
        "|---|----------|--------|------|---------|-----------|",
    ]
    for item in sorted(catalog, key=lambda x: x.get("serial", 0)):
        g = GROUPS.get(item.get("group", ""), {})
        folder = g.get("folder", item.get("group", ""))
        trigger = item.get("trigger", "")
        summary = item.get("summary") or item.get("meta", {}).get("summary", "")
        display = item.get("display_name", item["name"])
        serial = item.get("serial", "—")
        lines.append(
            f"| {serial} | {display} | `{folder}/` | `{item['slug']}` | {trigger} | {summary} |"
        )
    lines += [
        "",
        "## Folder groups",
        "",
        "| Folder | Serials | Role |",
        "|--------|---------|------|",
    ]
    for gid, g in GROUPS.items():
        lines.append(
            f"| `{g['folder']}/` | {g.get('serial_range', '—')} | {g['description'].split('.')[0]}. |"
        )
    lines += [
        "",
        "## n8n UI tips",
        "",
        "- **Sort by name** — workflows appear in execution order (WF-01 … WF-10).",
        "- **Filter by tag** — use `business`, `notifications`, `reports`, `infra`, or `test`.",
        "- **Repo folders** mirror groups under `n8n/workflows/{folder}/`.",
        "",
        "Regenerate: `make n8n-build` · Apply to n8n: `make n8n-import` · DB seed: `make seed-workflows`",
        "",
    ]
    return "\n".join(lines)


def _workflow_detail(item: dict) -> str:
    meta = item.get("meta", {})
    slug = item["slug"]
    group = item.get("group", meta.get("group", ""))
    trigger = item.get("trigger", "")
    display = item.get("display_name", item["name"])
    serial = item.get("serial", meta.get("serial", ""))
    summary = item.get("summary") or meta.get("summary", "")
    lines = [
        f"### `{slug}` — {display}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| **Serial** | WF-{serial:02d} |" if serial else f"| **Serial** | — |",
        f"| **Group** | `{group}` |",
        f"| **Owner** | {meta.get('owner', '—')} |",
        f"| **Version** | v{meta.get('version', 1)} |",
        f"| **Trigger type** | `{trigger}` |",
        f"| **Retries** | {meta.get('retries', 3)} |",
        f"| **Repo path** | `n8n/workflows/{item['file']}` |",
        "",
        "#### Summary",
        "",
        summary or meta.get("purpose", "—"),
        "",
        "#### Purpose",
        "",
        meta.get("purpose", item.get("name", "")),
        "",
    ]

    if meta.get("domain_event"):
        lines += ["#### Domain event", "", f"`{meta['domain_event']}`", ""]
    if meta.get("fastapi_trigger"):
        lines += ["#### FastAPI trigger", "", meta["fastapi_trigger"], ""]
    if trigger == "webhook":
        lines += [
            "#### Webhook",
            "",
            f"- **Local:** `POST http://localhost:5679/webhook/{slug}`",
            f"- **Docker internal:** `POST http://n8n:5678/webhook/{slug}`",
            "",
        ]
    if trigger == "schedule" and item.get("cron"):
        lines += ["#### Schedule", "", f"Cron: `{item['cron']}`", ""]
    if trigger == "manual":
        lines += [
            "#### Trigger",
            "",
            "Manual — run from n8n UI or CI (`verify-n8n-callback`). Never activate for live webhooks.",
            "",
        ]

    if item.get("callback"):
        lines += [
            "#### Callback",
            "",
            "`POST http://api:8000/internal/n8n/callback` — HMAC-signed completion payload.",
            "",
        ]
    if item.get("admin_notify_steps"):
        lines += [
            "#### Admin notifications",
            "",
            "These steps call `POST http://api:8000/internal/notifications/admin`:",
            "",
        ]
        for step in item["admin_notify_steps"]:
            lines.append(f"- {step}")
        lines.append("")

    lines += [
        "#### Input payload",
        "",
        "```json",
        json.dumps(meta.get("input", {}), indent=2),
        "```",
        "",
        "#### Output payload",
        "",
        "```json",
        json.dumps(meta.get("output", {}), indent=2),
        "```",
        "",
        "#### Steps",
        "",
        _steps_md(item.get("steps", [])),
        "",
        "#### Failure handling",
        "",
        meta.get("failure", "—"),
        "",
        "#### Tags",
        "",
        ", ".join(f"`{t}`" for t in item.get("tags", [])),
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def generate_groups_doc(catalog: list[dict]) -> str:
    by_group: dict[str, list[dict]] = {g: [] for g in GROUPS}
    for item in catalog:
        g = item.get("group", item.get("meta", {}).get("group", "business"))
        by_group.setdefault(g, []).append(item)

    lines = [
        "# Workflow Groups",
        "",
        "**LexFlow AI** — n8n workflow organization by function",
        "",
        "Workflows are grouped into five folders under `n8n/workflows/`. Each group has a distinct "
        "operational role, activation policy, and owner.",
        "",
        "---",
        "",
        "## Group index",
        "",
        "| Group | Folder | Workflows | Activation |",
        "|-------|--------|-----------|------------|",
    ]
    for gid, g in GROUPS.items():
        count = len(by_group.get(gid, []))
        lines.append(f"| **{g['label']}** | `{g['folder']}/` | {count} | {g['activate']} |")

    lines += ["", "---", ""]

    for gid, g in GROUPS.items():
        items = by_group.get(gid, [])
        lines += [
            f"## {g['label']} (`{g['folder']}/`)",
            "",
            g["description"],
            "",
            f"**Activation:** {g['activate']}",
            "",
        ]
        if not items:
            lines += ["_No workflows in this group._", ""]
            continue
        lines += ["| Workflow | Slug | Trigger |", "|----------|------|---------|"]
        for item in items:
            trig = item.get("trigger", "")
            if trig == "schedule":
                trig = f"schedule `{item.get('cron', '')}`"
            lines.append(f"| {item['name']} | `{item['slug']}` | {trig} |")
        lines += ["", "### What each workflow does", ""]
        for item in items:
            meta = item.get("meta", {})
            lines.append(f"- **`{item['slug']}`** — {meta.get('purpose', item['name'])}")
        lines += ["", "---", ""]

    lines += [
        "## Related docs",
        "",
        "- [Workflow technical reference](./workflow-technical-reference.md) — webhooks, payloads, callbacks",
        "- [n8n/workflows/README.md](../../n8n/workflows/README.md) — repo folder guide",
        "- [Workflow catalog UI](http://localhost:3000/workflows) — live status in LexFlow",
        "",
    ]
    return "\n".join(lines)


def generate_technical_reference(catalog: list[dict]) -> str:
    lines = [
        "# Workflow Technical Reference",
        "",
        "**LexFlow AI** — auto-generated from `n8n/workflows/catalog.json`",
        "",
        "> Regenerate: `python3 scripts/n8n/build_workflows.py`",
        "",
        "## Architecture",
        "",
        "```",
        "Domain Event → FastAPI (auth, audit) → workflow_executions row → Celery",
        "    → POST n8n webhook (HMAC) → n8n steps → POST /internal/n8n/callback",
        "```",
        "",
        "Scheduled workflows run inside n8n on cron — no FastAPI trigger required.",
        "",
        "## Environment URLs",
        "",
        "| Context | n8n base | API internal |",
        "|---------|----------|--------------|",
        "| Local Docker | `http://n8n:5678` | `http://api:8000` |",
        "| Local host (editor) | `http://localhost:5679` | `http://localhost:8000` |",
        "",
        "## Authentication",
        "",
        "| Direction | Mechanism |",
        "|-----------|-----------|",
        "| FastAPI → n8n webhook | `X-LexFlow-Signature` HMAC-SHA256 (`N8N_WEBHOOK_SECRET`) |",
        "| n8n → FastAPI callback | Same HMAC on callback body |",
        "| n8n → admin notify | Internal network only (no auth in local dev) |",
        "",
        "## Workflow definitions (PostgreSQL)",
        "",
        "Table: `workflows.workflow_definitions`. Seed: `make seed-workflows`.",
        "",
        "---",
        "",
    ]

    by_group: dict[str, list[dict]] = {}
    for item in catalog:
        g = item.get("group", "business")
        by_group.setdefault(g, []).append(item)

    for gid in GROUPS:
        items = by_group.get(gid, [])
        if not items:
            continue
        lines += [f"## {GROUPS[gid]['label']}", ""]
        for item in items:
            lines.append(_workflow_detail(item))

    return "\n".join(lines)


def generate_n8n_readme(catalog: list[dict]) -> str:
    by_group: dict[str, list[dict]] = {}
    for item in catalog:
        g = item.get("group", "business")
        by_group.setdefault(g, []).append(item)

    lines = [
        "# n8n Workflow Repository",
        "",
        "Auto-generated index. Source of truth: `scripts/n8n/build_workflows.py` → `catalog.json`.",
        "",
        "## Folder groups",
        "",
    ]
    for gid, g in GROUPS.items():
        lines += [
            f"### `{g['folder']}/` — {g['label']}",
            "",
            g["description"],
            "",
        ]
        for item in by_group.get(gid, []):
            active = "manual" if item.get("trigger") == "manual" else "webhook/schedule"
            display = item.get("display_name", item["name"])
            summary = item.get("summary", "")
            lines.append(f"- **{display}** — `{item['slug']}.json` ({active})")
            if summary:
                lines.append(f"  - {summary}")
        lines += [""]

    lines += [
        "## Commands",
        "",
        "```bash",
        "python3 scripts/n8n/build_workflows.py  # JSON + docs",
        "make n8n-import                         # purge + import to n8n",
        "make seed-workflows                     # PostgreSQL definitions",
        "```",
        "",
        "See [workflow-index.md](./workflow-index.md) for the one-line reference table.",
        "",
        "See [docs/06-workflows/workflow-groups.md](../../docs/06-workflows/workflow-groups.md).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    catalog = _load_catalog()
    (DOCS_OUT / "workflow-index.md").write_text(generate_workflow_index(catalog) + "\n")
    (DOCS_OUT / "workflow-groups.md").write_text(generate_groups_doc(catalog) + "\n")
    (DOCS_OUT / "workflow-technical-reference.md").write_text(generate_technical_reference(catalog) + "\n")
    N8N_README.write_text(generate_n8n_readme(catalog) + "\n")
    print(f"OK  docs/06-workflows/workflow-index.md")
    print(f"OK  docs/06-workflows/workflow-technical-reference.md")
    print(f"OK  n8n/workflows/README.md")


if __name__ == "__main__":
    main()

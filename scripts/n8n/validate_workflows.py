#!/usr/bin/env python3
"""Validate LexFlow n8n workflow JSON — structure, uniqueness, catalog parity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / "n8n" / "workflows"
CATALOG = WORKFLOWS / "catalog.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    wf = _load_json(path)
    nodes = wf.get("nodes", [])
    names = [n.get("name") for n in nodes]
    ids = [n.get("id") for n in nodes]

    if not nodes:
        errors.append(f"{path.name}: no nodes")
    if len(names) != len(set(names)):
        dupes = {n for n in names if names.count(n) > 1}
        errors.append(f"{path.name}: duplicate node names: {sorted(dupes)}")
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        errors.append(f"{path.name}: duplicate node ids: {sorted(dupes)}")

    connections = wf.get("connections", {})
    for src, outs in connections.items():
        if src not in names:
            errors.append(f"{path.name}: connection source missing node '{src}'")
        for branch in outs.get("main", []):
            for link in branch:
                target = link.get("node")
                if target and target not in names:
                    errors.append(f"{path.name}: connection target missing node '{target}'")

    webhooks = [n for n in nodes if n.get("type", "").endswith("webhook")]
    for wh in webhooks:
        wh_path = wh.get("parameters", {}).get("path")
        wh_id = wh.get("webhookId")
        if wh_path and wh_id and wh_path != wh_id:
            errors.append(f"{path.name}: webhook path/id mismatch {wh_path} vs {wh_id}")

    stub_only = all(n.get("type", "").endswith("code") for n in nodes if n.get("name") not in {
        "Normalize Context", "Validate Signature", "Merge Session Context",
        "Merge Execution Context", "Prepare Callback", "Resolve Webhook URL",
        "Load Session Token", "Store Session Token", "Merge Heartbeat Result",
    })
    has_http = any(n.get("type", "").endswith("httpRequest") for n in nodes)
    if stub_only and not has_http and "smoke" not in path.name and "session" not in path.name:
        errors.append(f"{path.name}: appears stub-only (no HTTP nodes)")

    return errors


def main() -> int:
    if not CATALOG.exists():
        print("FAIL: catalog.json missing — run build_workflows.py")
        return 1

    catalog = _load_json(CATALOG)
    catalog_files = {item["file"] for item in catalog}
    all_errors: list[str] = []
    checked = 0

    for item in catalog:
        rel = item["file"]
        path = WORKFLOWS / rel
        if not path.exists():
            all_errors.append(f"missing catalog file: {rel}")
            continue
        all_errors.extend(validate_workflow(path))
        checked += 1

    orphans = []
    for path in sorted(WORKFLOWS.rglob("*.json")):
        if path.name in {"catalog.json", "groups.json"}:
            continue
        rel = str(path.relative_to(WORKFLOWS))
        if rel not in catalog_files:
            orphans.append(rel)

    if orphans:
        all_errors.append(f"orphan workflow JSON not in catalog: {orphans}")

    slugs = [item["slug"] for item in catalog if item.get("slug")]
    if len(slugs) != len(set(slugs)):
        all_errors.append("duplicate slugs in catalog")

    if all_errors:
        print("FAIL workflow validation:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"OK  validated {checked} catalog workflows, 0 orphans, 0 errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())

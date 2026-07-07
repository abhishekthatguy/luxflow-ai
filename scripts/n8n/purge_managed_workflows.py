#!/usr/bin/env python3
"""Purge LexFlow-managed workflows from n8n SQLite (host-side, n8n stopped)."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "n8n" / "workflows" / "catalog.json"
LEGACY = {"document-upload-notify-v1", "Demo: My first AI Agent in n8n", "WF-Notification-Teams"}


def _volume_name() -> str:
    result = subprocess.run(
        ["docker", "volume", "ls", "--format", "{{.Name}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    for name in result.stdout.splitlines():
        if name.endswith("_n8n_data"):
            return name
    raise SystemExit("FAIL: n8n_data volume not found — run make dev first")


def _managed_names() -> set[str]:
    names = set(LEGACY)
    if CATALOG.exists():
        for item in json.loads(CATALOG.read_text()):
            if item.get("display_name"):
                names.add(str(item["display_name"]))
            if item.get("name"):
                names.add(str(item["name"]))
    return names


def purge(db_path: Path, managed: set[str]) -> int:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, name FROM workflow_entity").fetchall()
    to_delete = [(wid, name) for wid, name in rows if name in managed]
    if not to_delete:
        conn.close()
        return 0

    ids = [wid for wid, _ in to_delete]
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM workflows_tags WHERE workflowId IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM webhook_entity WHERE workflowId IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM shared_workflow WHERE workflowId IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM workflow_entity WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()

    for _, name in to_delete:
        print(f"    - {name}")
    return len(to_delete)


def main() -> None:
    managed = _managed_names()
    volume = _volume_name()
    tmp = Path("/tmp/lexflow-n8n-purge.sqlite")

    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{volume}:/data:ro",
            "alpine",
            "cat",
            "/data/database.sqlite",
        ],
        stdout=tmp.open("wb"),
        check=True,
    )

    if not tmp.exists() or tmp.stat().st_size == 0:
        print("==> n8n purge: empty database — skip")
        return

    removed = purge(tmp, managed)
    if removed == 0:
        print("==> n8n purge: no managed workflows to remove")
        tmp.unlink(missing_ok=True)
        return

    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "-v",
            f"{volume}:/data",
            "alpine",
            "sh",
            "-c",
            "cat > /data/database.sqlite",
        ],
        stdin=tmp.open("rb"),
        check=True,
    )
    tmp.unlink(missing_ok=True)
    print(f"==> n8n purge: removed {removed} managed workflow(s)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)

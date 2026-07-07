#!/usr/bin/env python3
"""Import n8n workflow JSON files from repo into local n8n instance."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib import error, request

DEFAULT_BASE = os.environ.get("N8N_BASE_URL", "http://localhost:5679")
DEFAULT_KEY = os.environ.get("N8N_API_KEY", "")


def _api(method: str, url: str, body: dict | None = None, api_key: str = "") -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("X-N8N-API-KEY", api_key)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {url} failed ({exc.code}): {detail}") from exc


def import_workflow(path: Path, base: str, api_key: str, activate: bool) -> str:
    payload = json.loads(path.read_text())
    name = payload.get("name", path.stem)
    existing = _api("GET", f"{base}/api/v1/workflows?limit=250", api_key=api_key)
    workflows = existing.get("data", existing if isinstance(existing, list) else [])
    match = next((w for w in workflows if w.get("name") == name), None)

    body = {
        "name": name,
        "nodes": payload.get("nodes", []),
        "connections": payload.get("connections", {}),
        "settings": payload.get("settings", {}),
        "staticData": payload.get("staticData"),
    }
    if match:
        wf_id = match["id"]
        _api("PUT", f"{base}/api/v1/workflows/{wf_id}", body, api_key)
        action = "updated"
    else:
        created = _api("POST", f"{base}/api/v1/workflows", body, api_key)
        wf_id = created["id"]
        action = "created"

    if activate:
        _api("POST", f"{base}/api/v1/workflows/{wf_id}/activate", {}, api_key)
        action += "+activated"

    return f"{action} {name} ({wf_id})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Import LexFlow n8n workflows")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--api-key", default=DEFAULT_KEY)
    parser.add_argument("--activate", action="store_true", help="Activate workflows after import")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["n8n/workflows"],
        help="Workflow JSON files or directories",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("WARN: N8N_API_KEY not set — import may fail on secured instances", file=sys.stderr)

    root = Path(__file__).resolve().parents[2]
    files: list[Path] = []
    for p in args.paths:
        path = (root / p).resolve() if not Path(p).is_absolute() else Path(p)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        elif path.is_file():
            files.append(path)

    if not files:
        print("No workflow JSON files found.")
        sys.exit(1)

    for wf in files:
        print(import_workflow(wf, args.base_url.rstrip("/"), args.api_key, args.activate))


if __name__ == "__main__":
    main()

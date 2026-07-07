#!/usr/bin/env python3
"""Smoke-test all catalog webhooks against local n8n (requires stack + WF-11 session)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "n8n" / "workflows" / "catalog.json"
N8N_BASE = os.environ.get("N8N_PUBLIC_URL", "http://localhost:5679").rstrip("/")
SECRET = os.environ.get("N8N_WEBHOOK_SECRET", "dev-n8n-webhook-secret")


def _sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def _post(path: str, payload: dict) -> tuple[int, str]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{N8N_BASE}/webhook/{path}",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-LexFlow-Signature": _sign(body),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(500).decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(500).decode()


def _init_session() -> None:
    req = urllib.request.Request(
        f"{N8N_BASE}/webhook/workflow-session-init-v1",
        data=b"{}",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15):
        pass


def _wait_n8n() -> None:
    import time
    import urllib.error

    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{N8N_BASE}/healthz", timeout=3) as resp:
                if resp.status == 200:
                    time.sleep(5)
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionResetError):
            time.sleep(2)
    raise RuntimeError(f"n8n not ready at {N8N_BASE}")


def main() -> int:
    catalog = json.loads(CATALOG.read_text())
    webhooks = [item for item in catalog if item.get("trigger") == "webhook" and not item.get("custom")]

    print(f"==> Waiting for n8n at {N8N_BASE}")
    _wait_n8n()
    print(f"==> Initializing session via {N8N_BASE}")
    try:
        _init_session()
    except Exception as exc:
        print(f"WARN: session init failed: {exc}")

    failed = 0
    exec_id = str(uuid4())
    case_id = str(uuid4())
    doc_id = str(uuid4())

    for item in webhooks:
        slug = item["slug"]
        payload = {
            "executionId": exec_id,
            "caseId": case_id,
            "documentId": doc_id,
            "payload": {"documentId": doc_id},
        }
        status, detail = _post(slug, payload)
        ok = status == 200
        mark = "OK " if ok else "FAIL"
        print(f"{mark}  {slug} → HTTP {status}")
        if not ok:
            failed += 1
            print(f"      {detail[:200]}")

    # notification-teams / notification-slack do not require session/signature contract
    for slug, body_obj in (
        ("notification-teams-v1", {"correlationId": "smoke", "card": {"type": "message"}}),
        (
            "notification-slack-v1",
            {
                "correlationId": "smoke",
                "message": {"text": "LexFlow n8n smoke test"},
                "slackBotToken": None,
                "slackChannelId": None,
                "slackWebhookUrl": None,
            },
        ),
    ):
        if not next((i for i in catalog if i.get("slug") == slug), None):
            continue
        body = json.dumps(body_obj).encode()
        req = urllib.request.Request(
            f"{N8N_BASE}/webhook/{slug}",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                detail = resp.read(200).decode()
                ok = resp.status == 200
                mark = "OK " if ok else "FAIL"
                print(f"{mark}  {slug} → HTTP {resp.status} {detail[:80]}")
                if not ok:
                    failed += 1
        except urllib.error.HTTPError as exc:
            print(f"FAIL {slug} → HTTP {exc.code} {exc.read(200).decode()}")
            failed += 1

    scheduled = [i["slug"] for i in catalog if i.get("trigger") == "schedule"]
    print(f"==> Scheduled workflows ({len(scheduled)}): manual/cron only — {', '.join(scheduled)}")

    notification_webhooks = sum(
        1 for i in catalog if i.get("slug") in ("notification-teams-v1", "notification-slack-v1")
    )
    if failed:
        print(f"FAIL {failed} webhook(s)")
        return 1
    print(f"OK  all {len(webhooks) + notification_webhooks} webhook smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

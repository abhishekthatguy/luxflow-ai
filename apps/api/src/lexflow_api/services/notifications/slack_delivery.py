"""Legacy direct Slack delivery — production uses n8n notification-slack-v1."""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

import httpx

from lexflow_api.config import settings

logger = logging.getLogger(__name__)


def send_slack_message_sync(payload: dict[str, object]) -> dict[str, Any]:
    """Post to Slack team channel. Returns status dict for delivery logging."""
    started = time.perf_counter()
    webhook = settings.slack_webhook_url.strip()
    bot_token = settings.slack_bot_token.strip()
    channel_id = settings.slack_team_channel_id.strip()

    if webhook:
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(webhook, json=payload)
                latency_ms = int((time.perf_counter() - started) * 1000)
                if response.status_code >= 400:
                    return {
                        "status": "failed",
                        "provider": "slack_webhook",
                        "latency_ms": latency_ms,
                        "error": response.text[:300],
                    }
                return {
                    "status": "sent",
                    "provider": "slack_webhook",
                    "latency_ms": latency_ms,
                    "channel": channel_id or "webhook",
                }
        except Exception as exc:
            return {
                "status": "failed",
                "provider": "slack_webhook",
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "error": str(exc)[:300],
            }

    if bot_token and channel_id:
        try:
            body = {**payload, "channel": channel_id}
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {bot_token}"},
                    json=body,
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                data = response.json()
                if not data.get("ok"):
                    return {
                        "status": "failed",
                        "provider": "slack_bot",
                        "latency_ms": latency_ms,
                        "error": str(data.get("error", "unknown"))[:300],
                    }
                return {
                    "status": "sent",
                    "provider": "slack_bot",
                    "latency_ms": latency_ms,
                    "channel": channel_id,
                }
        except Exception as exc:
            return {
                "status": "failed",
                "provider": "slack_bot",
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "error": str(exc)[:300],
            }

    return {
        "status": "stub",
        "provider": "slack",
        "latency_ms": 0,
        "error": "SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN+SLACK_TEAM_CHANNEL_ID not configured",
    }

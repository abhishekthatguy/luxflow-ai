"""Redis-backed n8n orchestrator session — initialize once, heartbeat refreshes."""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta

from lexflow_api.config import settings
from lexflow_api.infrastructure.cache import get_cache_client

SESSION_KEY = "lexflow:n8n:orchestrator:session"
SESSION_TTL_SECONDS = 600  # 10 minutes; heartbeat every 5 min refreshes


class WorkflowSessionService:
    def __init__(self) -> None:
        self._cache = get_cache_client(settings.redis_url)

    def initialize(self) -> dict[str, object]:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        expires = now + timedelta(seconds=SESSION_TTL_SECONDS)
        payload = {
            "sessionToken": token,
            "createdAt": now.isoformat(),
            "expiresAt": expires.isoformat(),
            "sessionValid": True,
        }
        self._cache.set(SESSION_KEY, json.dumps(payload), ttl=SESSION_TTL_SECONDS)
        return payload

    def heartbeat(self, session_token: str | None) -> dict[str, object]:
        raw = self._cache.get(SESSION_KEY)
        if not raw:
            return {
                "sessionValid": False,
                "requiresInitialize": True,
                "message": "No active orchestrator session — run WF-11 Initialize.",
            }
        data = json.loads(raw)
        stored = str(data.get("sessionToken", ""))
        if session_token and stored and session_token != stored:
            return {
                "sessionValid": False,
                "requiresInitialize": True,
                "message": "Session token mismatch — re-initialize required.",
            }
        self._cache.set(SESSION_KEY, raw, ttl=SESSION_TTL_SECONDS)
        expires = datetime.now(UTC) + timedelta(seconds=SESSION_TTL_SECONDS)
        return {
            "sessionValid": True,
            "requiresInitialize": False,
            "sessionToken": stored,
            "expiresAt": expires.isoformat(),
            "refreshedAt": datetime.now(UTC).isoformat(),
        }

    def verify(self, session_token: str | None) -> dict[str, object]:
        raw = self._cache.get(SESSION_KEY)
        if not raw:
            return {
                "sessionValid": False,
                "authorized": False,
                "message": "Orchestrator session expired. Run WF-11 or wait for WF-12 heartbeat.",
            }
        data = json.loads(raw)
        stored = str(data.get("sessionToken", ""))
        if session_token and stored and session_token != stored:
            return {
                "sessionValid": False,
                "authorized": False,
                "message": "Invalid session token.",
            }
        return {
            "sessionValid": True,
            "authorized": True,
            "expiresAt": data.get("expiresAt"),
        }

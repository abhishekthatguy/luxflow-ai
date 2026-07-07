"""Shared HMAC verification for n8n ↔ FastAPI internal calls."""

from __future__ import annotations

import hashlib
import hmac

from lexflow_api.config import settings


def sign_payload(raw: bytes) -> str:
    return hmac.new(
        settings.n8n_webhook_secret.encode(),
        raw,
        hashlib.sha256,
    ).hexdigest()


def verify_internal_signature(signature: str | None, raw: bytes = b"") -> bool:
    if not signature:
        return False
    expected = sign_payload(raw)
    return hmac.compare_digest(signature, expected)


def verify_internal_token(token: str | None) -> bool:
    """Fallback for GET probes when n8n sends shared secret as token header."""
    if not token:
        return False
    return hmac.compare_digest(token, settings.n8n_webhook_secret)


def verify_n8n_request(
    *,
    signature: str | None,
    token: str | None = None,
    raw: bytes = b"",
) -> bool:
    if verify_internal_signature(signature, raw):
        return True
    return verify_internal_token(token)

"""Virus scan hook — ClamAV integration deferred to production (Sprint 5)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class VirusScanResult:
    def __init__(self, *, clean: bool, engine: str = "stub", detail: str | None = None) -> None:
        self.clean = clean
        self.engine = engine
        self.detail = detail


def scan_object_stub(*, s3_key: str, mime_type: str) -> VirusScanResult:
    """Local dev stub — always clean. Replace with ClamAV HTTP/gRPC in production."""
    logger.info("virus_scan_stub", extra={"s3Key": s3_key, "mimeType": mime_type, "engine": "stub"})
    return VirusScanResult(clean=True, engine="stub", detail="ClamAV not configured — skipped")

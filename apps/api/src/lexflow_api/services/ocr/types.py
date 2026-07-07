"""OCR result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResult:
    text: str
    method: str
    page_count: int = 0

"""OCR provider factory — Phase 1 local vs Phase 2 Azure Document Intelligence."""

from __future__ import annotations

from lexflow_api.config import settings
from lexflow_api.services.ocr.azure_di import AzureDocumentIntelligenceOcr
from lexflow_api.services.ocr.local import extract_local
from lexflow_api.services.ocr.types import OcrResult


def extract_text(content: bytes, mime_type: str) -> OcrResult:
    provider = settings.ocr_provider.strip().lower()
    if provider == "azure_di":
        return AzureDocumentIntelligenceOcr().extract(content, mime_type)
    return extract_local(content, mime_type)

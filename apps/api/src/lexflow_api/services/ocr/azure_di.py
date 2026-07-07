"""Phase 2 — Azure AI Document Intelligence OCR adapter."""

from __future__ import annotations

from lexflow_api.config import settings
from lexflow_api.services.ocr.types import OcrResult


class AzureDocumentIntelligenceOcr:
    """Azure DI integration (Phase 2). Wire when AZURE_DI_* credentials are configured."""

    def extract(self, content: bytes, mime_type: str) -> OcrResult:
        if not settings.azure_di_endpoint or not settings.azure_di_api_key:
            raise RuntimeError(
                "Azure Document Intelligence is not configured. "
                "Set AZURE_DI_ENDPOINT and AZURE_DI_API_KEY, or use OCR_PROVIDER=local for Phase 1."
            )
        raise NotImplementedError(
            "Azure Document Intelligence adapter is planned for Phase 2 production. "
            "Use OCR_PROVIDER=local (PyMuPDF + PaddleOCR) for development."
        )

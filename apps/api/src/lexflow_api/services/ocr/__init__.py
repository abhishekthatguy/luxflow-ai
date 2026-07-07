"""Document OCR — Phase 1 local (PyMuPDF + PaddleOCR) or Phase 2 Azure DI."""

from lexflow_api.services.ocr.factory import extract_text
from lexflow_api.services.ocr.types import OcrResult

__all__ = ["OcrResult", "extract_text"]

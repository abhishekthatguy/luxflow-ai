"""Phase 1 local OCR — PyMuPDF (native text) + PaddleOCR (scanned fallback)."""

from __future__ import annotations

import io
import logging

from lexflow_api.config import settings
from lexflow_api.services.ocr.types import OcrResult

logger = logging.getLogger(__name__)

_MIN_NATIVE_CHARS = 32


def _extract_pdf_pymupdf(content: bytes) -> tuple[str, int]:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=content, filetype="pdf")
    parts: list[str] = []
    try:
        for page in doc:
            parts.append(page.get_text("text") or "")
        return "\n".join(parts).strip(), doc.page_count
    finally:
        doc.close()


def _paddle_ocr_available() -> bool:
    if not settings.ocr_enable_paddle:
        return False
    try:
        import paddleocr  # noqa: F401

        return True
    except ImportError:
        return False


def _extract_pdf_paddle(content: bytes) -> str:
    import fitz
    import numpy as np
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    doc = fitz.open(stream=content, filetype="pdf")
    lines: list[str] = []
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                img = img[:, :, :3]
            result = ocr.ocr(img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) > 1:
                        lines.append(str(line[1][0]))
    finally:
        doc.close()
    return "\n".join(lines).strip()


def _extract_image_paddle(content: bytes) -> str:
    import numpy as np
    from paddleocr import PaddleOCR
    from PIL import Image

    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    image = Image.open(io.BytesIO(content)).convert("RGB")
    img = np.array(image)
    result = ocr.ocr(img, cls=True)
    lines: list[str] = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) > 1:
                lines.append(str(line[1][0]))
    return "\n".join(lines).strip()


def extract_local(content: bytes, mime_type: str) -> OcrResult:
    """Extract text using PyMuPDF first, PaddleOCR for scans/images."""
    if len(content) >= 2 and content[:2] == b"PK":
        mime_type = "application/zip"

    if mime_type == "application/pdf":
        try:
            text, pages = _extract_pdf_pymupdf(content)
            if len(text) >= _MIN_NATIVE_CHARS:
                return OcrResult(text=text, method="pymupdf", page_count=pages)
            if _paddle_ocr_available():
                paddle_text = _extract_pdf_paddle(content)
                if paddle_text:
                    return OcrResult(text=paddle_text, method="paddleocr_pdf", page_count=pages)
            return OcrResult(text=text, method="pymupdf_partial", page_count=pages)
        except Exception:
            logger.exception("PyMuPDF extraction failed")
            if _paddle_ocr_available():
                try:
                    paddle_text = _extract_pdf_paddle(content)
                    if paddle_text:
                        return OcrResult(text=paddle_text, method="paddleocr_pdf")
                except Exception:
                    logger.exception("PaddleOCR PDF fallback failed")

    if mime_type.startswith("image/") and _paddle_ocr_available():
        try:
            text = _extract_image_paddle(content)
            if text:
                return OcrResult(text=text, method="paddleocr_image")
        except Exception:
            logger.exception("PaddleOCR image extraction failed")

    if mime_type.startswith("text/"):
        return OcrResult(
            text=content.decode("utf-8", errors="replace"),
            method="text_decode",
        )

    if mime_type in ("application/zip", "application/x-zip-compressed"):
        import zipfile

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                parts: list[str] = []
                for name in archive.namelist():
                    if name.endswith("/"):
                        continue
                    if name.lower().endswith((".txt", ".md")):
                        parts.append(archive.read(name).decode("utf-8", errors="replace"))
                    else:
                        parts.append(f"[archive file: {name}]")
                text = "\n".join(parts).strip() or f"[zip archive: {len(archive.namelist())} files]"
                return OcrResult(text=text, method="zip_manifest", page_count=len(archive.namelist()))
        except Exception:
            logger.exception("Zip extraction failed")

    return OcrResult(text="", method="unsupported")

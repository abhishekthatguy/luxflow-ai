"""Tests for Phase 1 local OCR pipeline."""

from lexflow_api.services.document_chunking import chunk_text
from lexflow_api.services.ocr.local import extract_local


def test_chunk_text_splits_long_content() -> None:
    text = "word " * 200
    chunks = chunk_text(text.strip(), chunk_size=100, overlap=10)
    assert len(chunks) >= 2
    assert all(len(c) <= 100 for c in chunks)


def test_extract_local_plain_text() -> None:
    result = extract_local(b"Hello from police report.", "text/plain")
    assert result.text == "Hello from police report."
    assert result.method == "text_decode"


def test_extract_local_pdf_with_pymupdf() -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Motor vehicle accident report sample text.")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = extract_local(pdf_bytes, "application/pdf")
    assert "Motor vehicle" in result.text
    assert result.method in ("pymupdf", "pymupdf_partial")

"""Tests for document chunking."""

from lexflow_api.services.document_chunking import chunk_text


def test_single_short_chunk() -> None:
    assert chunk_text("Hello world") == ["Hello world"]

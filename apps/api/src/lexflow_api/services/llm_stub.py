"""Backward-compatible stub helpers (Sprint 4). Prefer lexflow_api.services.llm."""

from lexflow_api.services.llm.stub import StubLLMProvider
from lexflow_api.services.llm.types import LLMResult

_stub = StubLLMProvider()


def generate_stub_summary(*, case_title: str, context: str, summary_type: str) -> LLMResult:
    return _stub.complete(
        prompt=context,
        llm_config={
            "model": "stub-gpt-4o",
            "case_title": case_title,
            "summary_type": summary_type,
        },
    )


def redact_pii(text: str) -> str:
    """Minimal PII redaction for prompt_history storage."""
    return text.replace("@example.com", "@[REDACTED_EMAIL]")

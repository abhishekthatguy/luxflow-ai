"""Stub LLM provider for local dev (Sprint 4)."""

from dataclasses import dataclass


@dataclass
class LLMResult:
    content: str
    input_tokens: int
    output_tokens: int
    model: str


def generate_stub_summary(*, case_title: str, context: str, summary_type: str) -> LLMResult:
    preview = context[:500].strip() if context else "(no document text available)"
    content = (
        f"**AI Draft Summary** ({summary_type})\n\n"
        f"Case: {case_title}\n\n"
        f"This is a development stub summary. In production, Azure OpenAI generates this content.\n\n"
        f"Context excerpt:\n{preview}\n\n"
        f"_Attorney review required before sharing with the team._"
    )
    return LLMResult(
        content=content,
        input_tokens=max(len(context) // 4, 50),
        output_tokens=max(len(content) // 4, 100),
        model="stub-gpt-4o",
    )


def redact_pii(text: str) -> str:
    """Minimal PII redaction for prompt_history storage."""
    return text.replace("@example.com", "@[REDACTED_EMAIL]")

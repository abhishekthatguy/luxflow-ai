"""Deterministic stub LLM for local development and CI."""

from typing import Any

from lexflow_api.services.llm.types import LLMResult


class StubLLMProvider:
    provider_name = "stub"

    def complete(self, *, prompt: str, llm_config: dict[str, Any]) -> LLMResult:
        model = str(llm_config.get("model", "stub-gpt-4o"))
        summary_type = str(llm_config.get("summary_type", "general"))
        case_title = str(llm_config.get("case_title", "Untitled case"))
        context = prompt
        preview = context[:500].strip() if context else "(no document text available)"
        content = (
            f"**AI Draft Summary** ({summary_type})\n\n"
            f"Case: {case_title}\n\n"
            f"This is a development stub summary. In production, Azure OpenAI generates "
            f"this content.\n\n"
            f"Context excerpt:\n{preview}\n\n"
            f"_Attorney review required before sharing with the team._"
        )
        return LLMResult(
            content=content,
            input_tokens=max(len(prompt) // 4, 50),
            output_tokens=max(len(content) // 4, 100),
            model=model,
            provider=self.provider_name,
        )

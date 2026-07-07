"""Shared types for LLM providers."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResult:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class LLMProvider(Protocol):
    """Protocol for completion providers (stub, Azure OpenAI, etc.)."""

    def complete(self, *, prompt: str, llm_config: dict[str, Any]) -> LLMResult:
        """Run a completion for the given rendered prompt."""
        ...


class LLMConfigurationError(RuntimeError):
    """Raised when provider credentials or config are missing in this environment."""

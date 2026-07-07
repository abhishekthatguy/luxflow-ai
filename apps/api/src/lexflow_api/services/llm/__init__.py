"""LLM provider adapters and factory."""

from lexflow_api.services.llm.factory import (
    complete_prompt,
    complete_with_fallback,
    get_llm_provider,
    persist_provider_name,
    resolve_provider_name,
)
from lexflow_api.services.llm.ollama import OllamaProvider
from lexflow_api.services.llm.types import LLMConfigurationError, LLMProvider, LLMResult

__all__ = [
    "LLMConfigurationError",
    "LLMProvider",
    "LLMResult",
    "complete_prompt",
    "complete_with_fallback",
    "get_llm_provider",
    "OllamaProvider",
    "persist_provider_name",
    "resolve_provider_name",
]

"""Tests for Ollama LLM provider."""

from __future__ import annotations

import pytest

from lexflow_api.config import Settings
from lexflow_api.services.llm.factory import get_llm_provider, persist_provider_name
from lexflow_api.services.llm.ollama import OllamaProvider
from lexflow_api.services.llm.types import LLMConfigurationError


def test_persist_provider_name_includes_ollama() -> None:
    assert persist_provider_name("ollama") == "ollama"


def test_get_ollama_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    import lexflow_api.services.llm.factory as factory_module

    factory_module._cached_provider.cache_clear()
    provider = get_llm_provider("ollama")
    assert isinstance(provider, OllamaProvider)


def test_ollama_complete_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "message": {"content": "## Summary\nIncident on March 15."},
                "eval_count": 120,
                "prompt_eval_count": 80,
            }

    class FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, url: str, json: dict[str, object]) -> FakeResponse:
            assert "/api/chat" in url
            return FakeResponse()

    monkeypatch.setattr("lexflow_api.services.llm.ollama.httpx.Client", FakeClient)
    provider = OllamaProvider(Settings(ollama_base_url="http://ollama:11434"))
    result = provider.complete(prompt="Summarize case.", llm_config={"model": "qwen2.5:latest"})
    assert "March 15" in result.content
    assert result.provider == "ollama"


def test_ollama_unreachable_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    class FailingClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> FailingClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, url: str, json: dict[str, object]) -> None:
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("lexflow_api.services.llm.ollama.httpx.Client", FailingClient)
    provider = OllamaProvider(Settings(ollama_base_url="http://invalid:11434"))
    with pytest.raises(LLMConfigurationError, match="Ollama unreachable"):
        provider.complete(prompt="test", llm_config={})

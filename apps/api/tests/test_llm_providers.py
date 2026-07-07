"""Unit tests for LLM provider factory and adapters."""

from __future__ import annotations

import pytest

from lexflow_api.services.llm.factory import (
    _provider_chain,
    complete_prompt,
    complete_with_fallback,
    persist_provider_name,
    resolve_provider_name,
)
from lexflow_api.services.llm.stub import StubLLMProvider
from lexflow_api.services.llm.types import LLMConfigurationError


def test_resolve_provider_name_from_template() -> None:
    assert resolve_provider_name({"provider": "azure_openai"}) == "azure_openai"


def test_stub_provider_returns_content() -> None:
    provider = StubLLMProvider()
    result = provider.complete(
        prompt="Sample legal context for testing.",
        llm_config={"model": "stub-gpt-4o", "case_title": "Test v. Demo", "summary_type": "brief"},
    )
    assert "Test v. Demo" in result.content
    assert result.provider == "stub"
    assert result.input_tokens > 0
    assert result.output_tokens > 0


def test_complete_prompt_uses_stub_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    from lexflow_api.config import Settings

    import lexflow_api.services.llm.factory as factory_module

    factory_module.settings = Settings()
    factory_module._cached_provider.cache_clear()

    result = complete_prompt(
        prompt="Contract dispute over payment terms.",
        llm_config={"provider": "stub", "model": "stub-gpt-4o"},
    )
    assert result.provider == "stub"
    assert "stub" in result.model or result.model == "stub-gpt-4o"


def test_persist_provider_name_maps_stub_to_db_enum() -> None:
    assert persist_provider_name("stub") == "azure_openai"
    assert persist_provider_name("azure_openai") == "azure_openai"
    assert persist_provider_name("openai") == "openai"
    assert persist_provider_name("ollama") == "ollama"


def test_production_blocks_stub_without_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.setenv("LLM_ALLOW_STUB", "false")
    from lexflow_api.config import Settings

    import lexflow_api.services.llm.factory as factory_module

    factory_module.settings = Settings()
    factory_module._cached_provider.cache_clear()

    with pytest.raises(LLMConfigurationError, match="Production requires"):
        complete_prompt(prompt="test", llm_config={"provider": "stub"})


def test_production_azure_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LLM_PROVIDER", "azure_openai")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    from lexflow_api.config import Settings

    import lexflow_api.services.llm.factory as factory_module

    factory_module.settings = Settings()
    factory_module._cached_provider.cache_clear()

    with pytest.raises(LLMConfigurationError, match="AZURE_OPENAI"):
        complete_prompt(prompt="test", llm_config={"provider": "azure_openai"})


def test_provider_chain_local_prefers_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.setenv("LLM_ALLOW_STUB", "true")
    from lexflow_api.config import Settings

    import lexflow_api.services.llm.factory as factory_module

    factory_module.settings = Settings()
    assert _provider_chain({"provider": "stub"}) == ["ollama", "stub"]
    assert _provider_chain({"provider": "ollama"}) == ["ollama", "stub"]


def test_complete_with_fallback_uses_stub_when_ollama_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_ALLOW_STUB", "true")
    from lexflow_api.config import Settings

    import lexflow_api.services.llm.factory as factory_module

    factory_module.settings = Settings()
    factory_module._cached_provider.cache_clear()
    real_complete = factory_module.complete_prompt

    def selective_fail(*, prompt: str, llm_config: dict) -> object:
        if llm_config.get("provider") == "ollama":
            raise LLMConfigurationError("Ollama unreachable")
        return real_complete(prompt=prompt, llm_config=llm_config)

    monkeypatch.setattr(factory_module, "complete_prompt", selective_fail)

    result = complete_with_fallback(
        prompt="Abhishek S motor claim in Bengaluru",
        llm_config={
            "provider": "ollama",
            "model": "qwen2.5:latest",
            "case_title": "Abhishek Case",
        },
        case_title="Abhishek Case",
        context="Police report for Abhishek S in Koramangala",
    )
    assert result.provider == "stub"

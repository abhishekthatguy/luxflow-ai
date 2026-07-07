"""LLM provider factory — resolves template config + environment settings."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from lexflow_api.config import settings
from lexflow_api.services.llm.azure_openai import AzureOpenAIProvider
from lexflow_api.services.llm.stub import StubLLMProvider
from lexflow_api.services.llm.types import LLMConfigurationError, LLMProvider, LLMResult

logger = logging.getLogger(__name__)

_PRODUCTION_BLOCKED = {"stub", ""}
_DB_PROVIDERS = frozenset({"openai", "azure_openai", "anthropic", "ollama"})


def resolve_provider_name(llm_config: dict[str, Any]) -> str:
    """Provider from template config, falling back to LLM_PROVIDER env."""
    raw = llm_config.get("provider") or settings.llm_provider
    return str(raw).strip().lower()


def persist_provider_name(provider_name: str) -> str:
    """Map runtime provider id to a value allowed by ai.llm_provider enum."""
    normalized = provider_name.strip().lower()
    if normalized in _DB_PROVIDERS:
        return normalized
    if normalized in ("stub", ""):
        return "azure_openai"
    raise LLMConfigurationError(f"Cannot persist unknown LLM provider: {provider_name}")


def _assert_production_provider(provider_name: str) -> None:
    if settings.environment != "production":
        return
    if provider_name in _PRODUCTION_BLOCKED and not settings.llm_allow_stub:
        raise LLMConfigurationError(
            "Production requires a real LLM provider. Set LLM_PROVIDER=azure_openai, "
            "configure AZURE_OPENAI_* secrets, and update prompt template llm_config — "
            "or set LLM_ALLOW_STUB=true only for emergency rollback."
        )


@lru_cache(maxsize=4)
def _cached_provider(provider_name: str) -> LLMProvider:
    if provider_name in ("stub", ""):
        return StubLLMProvider()
    if provider_name == "azure_openai":
        return AzureOpenAIProvider(settings)
    if provider_name == "ollama":
        from lexflow_api.services.llm.ollama import OllamaProvider

        return OllamaProvider(settings)
    raise LLMConfigurationError(f"Unsupported LLM provider: {provider_name}")


def get_llm_provider(provider_name: str) -> LLMProvider:
    _assert_production_provider(provider_name)
    return _cached_provider(provider_name)


def complete_prompt(*, prompt: str, llm_config: dict[str, Any]) -> LLMResult:
    """Run completion using provider from template config."""
    provider_name = resolve_provider_name(llm_config)
    _assert_production_provider(provider_name)

    if settings.environment == "production" and provider_name == "stub":
        logger.warning("LLM_ALLOW_STUB=true — stub provider active in production")

    provider = get_llm_provider(provider_name)
    return provider.complete(prompt=prompt, llm_config=llm_config)


def _provider_chain(llm_config: dict[str, Any]) -> list[str]:
    """Local: Ollama → configured provider → stub. Production: configured provider only."""
    primary = resolve_provider_name(llm_config)
    if settings.environment == "production":
        chain: list[str] = []
        if primary not in ("stub", ""):
            chain.append(primary)
        elif settings.llm_allow_stub:
            chain.append("stub")
        return chain

    chain: list[str] = ["ollama"]
    if primary not in ("ollama", "stub", ""):
        chain.append(primary)
    if settings.llm_allow_stub:
        chain.append("stub")
    return chain


def complete_with_fallback(
    *,
    prompt: str,
    llm_config: dict[str, Any],
    case_title: str = "",
    context: str = "",
) -> LLMResult:
    """Try Ollama first (local), then configured provider, then stub; template last."""
    errors: list[str] = []
    chain = _provider_chain(llm_config)

    for index, provider_name in enumerate(chain):
        try:
            config = {**llm_config, "provider": provider_name}
            if provider_name == "ollama":
                config.setdefault("model", settings.ollama_chat_model)
            result = complete_prompt(prompt=prompt, llm_config=config)
            if index > 0:
                logger.warning(
                    "LLM fallback: used %s after %s failed",
                    provider_name,
                    chain[0],
                )
            else:
                logger.info("LLM completion via %s model=%s", provider_name, result.model)
            return result
        except Exception as exc:
            logger.warning("LLM provider %s failed: %s", provider_name, exc)
            errors.append(f"{provider_name}: {exc}")

    if settings.llm_allow_stub and context and case_title:
        from lexflow_api.services.llm.insurance_mva import (
            build_insurance_mva_summary,
            is_insurance_mva_context,
        )

        if is_insurance_mva_context(case_title=case_title, context=context):
            logger.warning(
                "LLM chain exhausted (%s); using insurance_mva template as last resort",
                "; ".join(errors),
            )
            return build_insurance_mva_summary(case_title=case_title, context=context)

    raise LLMConfigurationError(
        "All LLM providers failed: " + ("; ".join(errors) if errors else "no providers configured")
    )

"""Ollama chat completions adapter (Phase 1 local LLM)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from lexflow_api.config import Settings
from lexflow_api.services.llm.types import LLMConfigurationError, LLMResult

logger = logging.getLogger(__name__)


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._default_model = settings.ollama_chat_model

    def complete(self, *, prompt: str, llm_config: dict[str, Any]) -> LLMResult:
        model = str(llm_config.get("model") or self._default_model)
        temperature = float(llm_config.get("temperature", 0.3))
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            with httpx.Client(timeout=httpx.Timeout(300.0)) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as exc:
            raise LLMConfigurationError(
                f"Ollama unreachable at {self._base_url}. "
                "Start with: docker compose up -d ollama && docker compose exec ollama ollama pull qwen2.5:latest"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMConfigurationError(f"Ollama request failed: {exc}") from exc

        message = data.get("message") or {}
        content = str(message.get("content", ""))
        if not content:
            raise LLMConfigurationError(f"Ollama returned empty content for model {model}")

        eval_count = int(data.get("eval_count", len(content) // 4))
        prompt_eval = int(data.get("prompt_eval_count", len(prompt) // 4))
        return LLMResult(
            content=content,
            input_tokens=prompt_eval,
            output_tokens=eval_count,
            model=model,
            provider=self.provider_name,
        )

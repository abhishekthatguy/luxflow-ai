"""Azure OpenAI chat completions adapter (production primary)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from lexflow_api.config import Settings
from lexflow_api.services.llm.types import LLMConfigurationError, LLMResult

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class AzureOpenAIProvider:
    provider_name = "azure_openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise LLMConfigurationError(
                "Azure OpenAI requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
            )

    def complete(self, *, prompt: str, llm_config: dict[str, Any]) -> LLMResult:
        deployment = str(
            llm_config.get("deployment")
            or self._settings.azure_openai_deployment
        )
        model = str(llm_config.get("model", deployment))
        temperature = float(llm_config.get("temperature", 0.3))
        max_tokens = int(llm_config.get("max_tokens", 4096))
        endpoint = self._settings.azure_openai_endpoint.rstrip("/")
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"
        params = {"api-version": self._settings.azure_openai_api_version}
        headers = {
            "api-key": self._settings.azure_openai_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
                    response = client.post(url, params=params, headers=headers, json=payload)
                if response.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    logger.warning(
                        "Azure OpenAI retryable status %s (attempt %s/%s)",
                        response.status_code,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return LLMResult(
                    content=str(choice),
                    input_tokens=int(usage.get("prompt_tokens", len(prompt) // 4)),
                    output_tokens=int(usage.get("completion_tokens", len(choice) // 4)),
                    model=model,
                    provider=self.provider_name,
                )
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    time.sleep(2**attempt)
                    continue
                raise
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2**attempt)
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Azure OpenAI completion failed without response")

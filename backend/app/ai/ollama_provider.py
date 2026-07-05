"""
Ollama AI Provider — Development Implementation.

Connects to a locally running Ollama instance (default: http://localhost:11434).
Uses the /api/chat endpoint for all interactions to support proper role-based
messaging with gemma4 models.

Retry logic is implemented via tenacity with exponential backoff to handle
transient Ollama connection issues during heavy inference.
"""
import json
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.base_provider import AIMessage, AIProviderError, AIResponse, BaseAIProvider
from app.config import get_settings

settings = get_settings()


class OllamaProvider(BaseAIProvider):
    """
    Concrete AI provider implementation for local Ollama inference.

    Targets the Ollama /api/chat endpoint which supports:
      - System prompts via the 'system' role
      - Multi-turn conversation history
      - Structured JSON output via format="json"
      - Non-streaming response mode (stream=False)

    All requests use a shared httpx.AsyncClient for connection pooling.
    """

    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model
        self._timeout = settings.ollama_timeout_seconds
        self._max_tokens = settings.ollama_max_tokens
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return a reusable async HTTP client for Ollama."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> AIResponse:
        """Generate a single-turn completion via Ollama /api/generate."""
        messages = [AIMessage(role="user", content=prompt)]
        return await self.chat(messages, temperature, max_tokens, json_mode)

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, ValueError)),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[AIMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> AIResponse:
        """
        Submit a multi-turn chat request to Ollama /api/chat.

        Converts AIMessage objects to Ollama's message format and returns
        a normalized AIResponse regardless of provider-specific response shape.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or self._max_tokens,
                "num_ctx": self._max_tokens,
            },
        }

        # We rely on prompt engineering ("Output ONLY valid JSON") instead of 
        # Ollama's format="json" because the grammar engine can cause silent 
        # empty-string failures on resource-constrained local environments.
        # if json_mode:
        #     payload["format"] = "json"

        try:
            client = self._get_client()
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            content = data["message"]["content"]
            if not content or not content.strip():
                raise ValueError("Ollama returned an empty response content")

            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            logger.debug(
                f"Ollama response: {len(content)} chars, "
                f"{prompt_tokens}+{completion_tokens} tokens"
            )

            return AIResponse(
                content=content,
                model=data.get("model", self._model),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                raw_response=data,
            )

        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                message=f"Ollama HTTP error: {exc.response.text}",
                provider=self.provider_name,
                status_code=exc.response.status_code,
            ) from exc
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise AIProviderError(
                message=f"Ollama connection failed: {exc}",
                provider=self.provider_name,
            ) from exc
        except (KeyError, json.JSONDecodeError) as exc:
            raise AIProviderError(
                message=f"Malformed Ollama response: {exc}",
                provider=self.provider_name,
            ) from exc

    async def health_check(self) -> bool:
        """
        Verify Ollama is running and the configured model is available.

        Checks /api/tags to confirm the model exists locally.
        """
        try:
            client = self._get_client()
            response = await client.get("/api/tags", timeout=10.0)
            response.raise_for_status()
            models_data = response.json()
            available_models = [m["name"] for m in models_data.get("models", [])]

            is_available = any(
                self._model in model_name or model_name.startswith(self._model.split(":")[0])
                for model_name in available_models
            )

            if not is_available:
                logger.warning(
                    f"Model '{self._model}' not found in Ollama. "
                    f"Available: {available_models}. "
                    f"Run: ollama pull {self._model}"
                )

            return is_available

        except Exception as exc:
            logger.warning(f"Ollama health check failed: {exc}")
            return False

    @property
    def provider_name(self) -> str:
        return "Ollama"

    @property
    def model_name(self) -> str:
        return self._model

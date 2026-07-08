"""
Gemma API Provider — Production Implementation.

Connects to the Google AI (Gemma 4) REST API via the
generativelanguage.googleapis.com endpoint. This provider is
production-ready and activates the moment GEMMA_API_KEY is set
in the environment.

Model used: gemma-2-27b-it (closest production API equivalent to the
local gemma-4-31B-it model; update GEMMA_API_MODEL in .env as needed).
"""
import json
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.base_provider import AIMessage, AIProviderError, AIResponse, BaseAIProvider
from app.config import get_settings

settings = get_settings()


def is_retryable_exception(exc: Exception) -> bool:
    """Return True if the exception is transient and should trigger a retry."""
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        # Retry on Server Errors (5xx status codes)
        return exc.response.status_code >= 500
    return False


class GemmaAPIProvider(BaseAIProvider):
    """
    Concrete AI provider for the Google Generative Language API.

    Uses the generateContent endpoint with the Google AI format,
    which is compatible with Gemma 2 and Gemma 4 series models served
    via Google AI Studio and Vertex AI.

    Authentication: API key via X-goog-api-key header.
    """

    def __init__(self) -> None:
        self._api_key = settings.gemma_api_key
        self._base_url = settings.gemma_api_base_url
        self._model = settings.gemma_api_model
        self._timeout = settings.gemma_api_timeout_seconds

    def _get_client(self) -> httpx.AsyncClient:
        """Return a configured async HTTP client for the Gemma API."""
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
        )

    def _build_contents(self, messages: list[AIMessage]) -> list[dict[str, Any]]:
        """
        Convert AIMessage list to Google Generative Language API content format.

        The Google API uses a 'contents' array with 'parts'. System messages
        are prepended to the first user message since the API handles system
        instructions differently.
        """
        contents = []
        system_content: str | None = None

        for message in messages:
            if message.role == "system":
                system_content = message.content
            elif message.role == "user":
                text = message.content
                if system_content:
                    text = f"{system_content}\n\n{text}"
                    system_content = None
                contents.append({
                    "role": "user",
                    "parts": [{"text": text}]
                })
            elif message.role == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": message.content}]
                })

        return contents

    @retry(
        retry=retry_if_exception(is_retryable_exception),
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
        """Generate a single-turn completion via the Gemma API."""
        messages = [AIMessage(role="user", content=prompt)]
        return await self.chat(messages, temperature, max_tokens, json_mode)

    @retry(
        retry=retry_if_exception(is_retryable_exception),
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
        """Submit a chat request to the Google Generative Language API."""
        if not self._api_key:
            raise AIProviderError(
                message="GEMMA_API_KEY is not set. Add it to your .env file.",
                provider=self.provider_name,
            )

        contents = self._build_contents(messages)

        generation_config: dict[str, Any] = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        endpoint = f"/models/{self._model}:generateContent"

        try:
            async with self._get_client() as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise AIProviderError(
                    message="Gemma API returned no candidates in response.",
                    provider=self.provider_name,
                )

            parts = candidates[0]["content"]["parts"]
            # Separate internal thinking/Chain-of-Thought from the actual final response
            thoughts = [part["text"] for part in parts if part.get("thought")]
            text_parts = [part["text"] for part in parts if not part.get("thought")]

            if thoughts:
                logger.debug(f"Gemma API Internal Thought Process:\n{''.join(thoughts)}")

            content = "".join(text_parts)
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("candidatesTokenCount", 0)

            logger.debug(
                f"Gemma API response: {len(content)} chars, "
                f"{prompt_tokens}+{completion_tokens} tokens"
            )

            return AIResponse(
                content=content,
                model=self._model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                raw_response=data,
            )

        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                message=f"Gemma API HTTP error {exc.response.status_code}: {exc.response.text}",
                provider=self.provider_name,
                status_code=exc.response.status_code,
            ) from exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise AIProviderError(
                message=f"Malformed Gemma API response: {exc}",
                provider=self.provider_name,
            ) from exc

    async def health_check(self) -> bool:
        """
        Verify the Gemma API is reachable and the API key is valid.

        Sends a minimal test request to verify connectivity.
        """
        if not self._api_key:
            logger.warning("Gemma API health check: no API key configured.")
            return False

        try:
            test_messages = [AIMessage(role="user", content="Hi")]
            response = await self.chat(test_messages, temperature=0.0, max_tokens=5)
            return bool(response.content)
        except AIProviderError as exc:
            logger.warning(f"Gemma API health check failed: {exc.message}")
            return False
        except Exception as exc:
            logger.warning(f"Gemma API health check unexpected error: {exc}")
            return False

    @property
    def provider_name(self) -> str:
        return "Gemma API"

    @property
    def model_name(self) -> str:
        return self._model

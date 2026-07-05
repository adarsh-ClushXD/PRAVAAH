"""
AI Provider Factory — Dependency Injection Entry Point.

This module implements the Strategy Pattern factory for AI providers.
The active provider is determined exclusively by the AI_PROVIDER environment
variable. Business logic NEVER imports providers directly — it always calls
get_ai_provider() which returns the correct BaseAIProvider implementation.

Switching from development (Ollama) to production (Gemma API) requires
only a single environment variable change:
    AI_PROVIDER=ollama   → Development
    AI_PROVIDER=gemma_api → Production
"""
from functools import lru_cache

from loguru import logger

from app.ai.base_provider import BaseAIProvider
from app.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_ai_provider() -> BaseAIProvider:
    """
    Factory function that returns the singleton AI provider instance.

    The provider is selected based on the AI_PROVIDER environment variable.
    The lru_cache ensures the provider is instantiated exactly once per
    process lifecycle, preventing redundant client initialization.

    Returns:
        A concrete BaseAIProvider implementation ready for use.

    Raises:
        ValueError: If an unknown AI_PROVIDER value is configured.
    """
    provider_key = settings.ai_provider.lower()

    if provider_key == "ollama":
        from app.ai.ollama_provider import OllamaProvider
        provider = OllamaProvider()
        logger.info(
            f"AI Provider: Ollama | Model: {provider.model_name} | "
            f"Endpoint: {settings.ollama_base_url}"
        )
        return provider

    elif provider_key == "gemma_api":
        from app.ai.gemma_api_provider import GemmaAPIProvider
        provider = GemmaAPIProvider()
        logger.info(
            f"AI Provider: Gemma API | Model: {provider.model_name}"
        )
        return provider

    else:
        raise ValueError(
            f"Unknown AI_PROVIDER: '{provider_key}'. "
            "Valid options are: 'ollama', 'gemma_api'"
        )

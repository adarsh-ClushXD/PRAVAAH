"""
AI Provider Factory — Dependency Injection Entry Point.

Returns the GemmaAPIProvider as the sole AI provider for the application.
All business logic calls get_ai_provider() to obtain the provider instance.
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

    Returns the GemmaAPIProvider backed by the Google Generative Language API.
    The lru_cache ensures the provider is instantiated exactly once per
    process lifecycle, preventing redundant client initialization.

    Returns:
        A GemmaAPIProvider instance ready for use.
    """
    from app.ai.gemma_api_provider import GemmaAPIProvider
    provider = GemmaAPIProvider()
    logger.info(
        f"AI Provider: Gemma API | Model: {provider.model_name}"
    )
    return provider

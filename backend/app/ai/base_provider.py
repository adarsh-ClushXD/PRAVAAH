"""
Abstract AI Provider contract.

All AI provider implementations MUST inherit from BaseAIProvider and
implement every abstract method. This contract ensures that switching
providers (via environment variable) requires zero changes to business logic.

Design Pattern: Strategy + Abstract Base Class
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIMessage:
    """
    Represents a single message in an AI conversation turn.

    Attributes:
        role: The speaker role. Must be 'system', 'user', or 'assistant'.
        content: The text content of the message.
    """
    role: str
    content: str

    def __post_init__(self) -> None:
        valid_roles = {"system", "user", "assistant"}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of {valid_roles}")


@dataclass
class AIResponse:
    """
    Standardized response from any AI provider.

    Attributes:
        content: The generated text response.
        model: The model identifier that produced this response.
        prompt_tokens: Number of tokens in the input prompt.
        completion_tokens: Number of tokens in the generated output.
        total_tokens: Total tokens consumed (prompt + completion).
        raw_response: The unmodified response dict from the provider.
    """
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    raw_response: dict[str, Any]


class BaseAIProvider(ABC):
    """
    Abstract base class defining the AI provider contract.

    Every concrete provider must implement:
      - generate(): Single-turn text generation.
      - chat(): Multi-turn conversational generation.
      - health_check(): Provider connectivity verification.

    Providers must NOT be instantiated directly — use provider_factory.py.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> AIResponse:
        """
        Generate a single-turn text completion.

        Args:
            prompt: The input prompt text.
            temperature: Sampling temperature. Lower = more deterministic.
                         For structured JSON output, use 0.0–0.15.
            max_tokens: Maximum tokens to generate. None = provider default.
            json_mode: When True, instructs the provider to return valid JSON.
                       Business logic MUST still validate the JSON structure.

        Returns:
            AIResponse with the generated text and token usage metadata.

        Raises:
            AIProviderError: When the provider call fails after retries.
        """
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[AIMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> AIResponse:
        """
        Generate a multi-turn chat completion.

        Args:
            messages: Ordered list of AIMessage objects (system, user, assistant).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            json_mode: When True, enforces JSON output format.

        Returns:
            AIResponse with the assistant's reply and token usage metadata.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify that the AI provider is reachable and the model is available.

        Returns:
            True if the provider is healthy and ready to serve requests.
            False if the provider is unreachable or the model is unavailable.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of the provider (e.g., 'Ollama', 'Gemma API')."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The specific model identifier being used."""
        ...


class AIProviderError(Exception):
    """
    Raised when an AI provider call fails.

    Attributes:
        provider: The name of the provider that failed.
        status_code: HTTP status code if available.
        message: Human-readable error description.
    """
    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.message = message

    def __repr__(self) -> str:
        return (
            f"AIProviderError(provider={self.provider!r}, "
            f"status_code={self.status_code}, message={self.message!r})"
        )

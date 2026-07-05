"""
Abstract data fetcher base class.

All data fetchers (weather, river, historical) must inherit from
BaseFetcher. This enforces a uniform interface for the CacheManager
and makes fetchers independently testable.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseFetcher(ABC):
    """
    Abstract base for all data source fetchers.

    Each concrete fetcher is responsible for:
      1. Fetching raw data from its source.
      2. Normalizing it into a consistent Python dict/list structure.
      3. Raising descriptive exceptions on failure.
    """

    @abstractmethod
    async def fetch(self, *args: Any, **kwargs: Any) -> dict[str, Any] | list[Any]:
        """
        Fetch and normalize data from the source.

        Returns:
            Normalized data as a dict or list.

        Raises:
            DataFetchError: When the source is unreachable or returns invalid data.
        """
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the data source."""
        ...

    @property
    @abstractmethod
    def cache_key_prefix(self) -> str:
        """Unique prefix used to namespace cache keys for this fetcher."""
        ...


class DataFetchError(Exception):
    """
    Raised when a data fetcher fails to retrieve or parse data.

    Attributes:
        source: The data source that failed.
        message: Human-readable error description.
    """
    def __init__(self, message: str, source: str = "unknown") -> None:
        super().__init__(message)
        self.source = source
        self.message = message

    def __repr__(self) -> str:
        return f"DataFetchError(source={self.source!r}, message={self.message!r})"

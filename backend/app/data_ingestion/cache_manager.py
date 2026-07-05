"""
SQLite TTL-based cache manager for data fetcher results.

Caches fetcher outputs in the SQLite database using a dedicated
cache_entries table. Each entry stores:
  - A cache key (namespace + identifier)
  - The serialized JSON payload
  - The timestamp when it was stored
  - The TTL in seconds

Cache reads automatically expire stale entries. Cache writes update
existing entries (upsert). This design is resilient across process
restarts — the database persists between server reloads.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal


class CacheManager:
    """
    TTL-based cache manager backed by SQLite.

    Usage:
        cache = CacheManager()
        data = await cache.get("weather", "murshidabad")
        if data is None:
            data = await fetcher.fetch(district)
            await cache.set("weather", "murshidabad", data, ttl_seconds=3600)
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS cache_entries (
        cache_key TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        stored_at TEXT NOT NULL,
        ttl_seconds INTEGER NOT NULL
    )
    """

    async def initialize(self) -> None:
        """Create the cache_entries table if it does not exist."""
        async with AsyncSessionLocal() as session:
            await session.execute(text(self.CREATE_TABLE_SQL))
            await session.commit()
        logger.debug("Cache table initialized.")

    def _build_key(self, namespace: str, identifier: str) -> str:
        """Build a namespaced cache key string."""
        return f"{namespace}::{identifier}"

    async def get(
        self, namespace: str, identifier: str
    ) -> dict[str, Any] | list[Any] | None:
        """
        Retrieve a cached value if it exists and has not expired.

        Args:
            namespace: Data source namespace (e.g., 'weather', 'river').
            identifier: Unique identifier within the namespace (e.g., district_id).

        Returns:
            The deserialized cached data, or None if not found or expired.
        """
        cache_key = self._build_key(namespace, identifier)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT payload, stored_at, ttl_seconds "
                    "FROM cache_entries WHERE cache_key = :key"
                ),
                {"key": cache_key},
            )
            row = result.fetchone()

        if row is None:
            logger.debug(f"Cache MISS: {cache_key}")
            return None

        payload_str, stored_at_str, ttl_seconds = row
        stored_at = datetime.fromisoformat(stored_at_str)
        expires_at = stored_at + timedelta(seconds=ttl_seconds)
        now = datetime.now(timezone.utc)

        if now > expires_at:
            logger.debug(f"Cache EXPIRED: {cache_key} (expired {now - expires_at} ago)")
            return None

        logger.debug(f"Cache HIT: {cache_key} (expires in {expires_at - now})")
        return json.loads(payload_str)

    async def set(
        self,
        namespace: str,
        identifier: str,
        data: dict[str, Any] | list[Any],
        ttl_seconds: int,
    ) -> None:
        """
        Store a value in the cache with the specified TTL.

        Uses UPSERT semantics — overwrites any existing entry for the same key.

        Args:
            namespace: Data source namespace.
            identifier: Unique identifier within the namespace.
            data: The data to cache (must be JSON-serializable).
            ttl_seconds: Time-to-live in seconds.
        """
        cache_key = self._build_key(namespace, identifier)
        stored_at = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(data, ensure_ascii=False, default=str)

        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO cache_entries (cache_key, payload, stored_at, ttl_seconds)
                    VALUES (:key, :payload, :stored_at, :ttl)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        payload = excluded.payload,
                        stored_at = excluded.stored_at,
                        ttl_seconds = excluded.ttl_seconds
                    """
                ),
                {
                    "key": cache_key,
                    "payload": payload_str,
                    "stored_at": stored_at,
                    "ttl": ttl_seconds,
                },
            )
            await session.commit()

        logger.debug(f"Cache SET: {cache_key} (TTL: {ttl_seconds}s)")

    async def invalidate(self, namespace: str, identifier: str) -> None:
        """Explicitly remove a cache entry."""
        cache_key = self._build_key(namespace, identifier)
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("DELETE FROM cache_entries WHERE cache_key = :key"),
                {"key": cache_key},
            )
            await session.commit()
        logger.debug(f"Cache INVALIDATED: {cache_key}")

    async def clear_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            The number of entries removed.
        """
        now = datetime.now(timezone.utc).isoformat()
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    DELETE FROM cache_entries
                    WHERE datetime(stored_at, '+' || ttl_seconds || ' seconds') < :now
                    """
                ),
                {"now": now},
            )
            await session.commit()
            deleted = result.rowcount

        if deleted > 0:
            logger.info(f"Cache cleanup: removed {deleted} expired entries.")
        return deleted

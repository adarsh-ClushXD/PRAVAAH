"""
Application configuration module.

Uses Pydantic Settings for type-safe, environment-variable-driven configuration.
All configuration is loaded once at application startup via the `get_settings`
cached factory function.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration class for PRAVAAH.

    All values are read from environment variables or the .env file.
    Types are enforced and validated at startup — misconfigured environments
    fail loudly rather than silently.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = Field(default="PRAVAAH", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    # ── AI Provider (Google Gemma API) ───────────────────────────────────────
    gemma_api_key: str = Field(default="")
    gemma_api_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta"
    )
    gemma_api_model: str = Field(default="gemma-4-31b-it")
    gemma_api_timeout_seconds: int = Field(default=120)

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./pravaah.db",
        description="SQLAlchemy async database URL",
    )

    # ── Cache TTL (seconds) ───────────────────────────────────────────────────
    weather_cache_ttl_seconds: int = Field(default=3600)
    river_cache_ttl_seconds: int = Field(default=1800)
    historical_cache_ttl_seconds: int = Field(default=86400)

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # ── Data File Paths ───────────────────────────────────────────────────────
    geojson_path: str = Field(default="data/geojson/west_bengal_districts.geojson")
    historical_data_path: str = Field(
        default="data/historical/wb_flood_history.json"
    )
    river_stations_path: str = Field(
        default="data/static/river_gauge_stations.json"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list) -> list[str]:
        """Parse comma-separated CORS origins from env string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value

    @property
    def is_production(self) -> bool:
        """Returns True when running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Returns True when running in development environment."""
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Using lru_cache ensures the .env file is read exactly once per process
    lifecycle, making configuration access O(1) after the first call.
    """
    return Settings()

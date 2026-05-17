"""Application configuration loaded from environment variables.

Settings are validated at startup by Pydantic. Missing required
variables cause a clear error before the app accepts requests.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Values are loaded from environment variables, with `.env` as a
    fallback for local development. Production environments inject
    variables directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./cash_tracker.db"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so that ``Settings()`` is instantiated only once per process.
    Tests that need different settings can clear the cache with
    ``get_settings.cache_clear()``.
    """
    return Settings()

"""Application settings, read from environment variables (or a local .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No default on purpose: the app should fail at startup, loudly, if it is
    # not told which database to use, instead of silently using a wrong one.
    database_url: str
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Return the settings, parsed once and cached for the life of the process."""
    return Settings()

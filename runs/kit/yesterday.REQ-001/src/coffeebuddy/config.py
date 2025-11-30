from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central runtime configuration sourced from the environment."""

    slack_signing_secret: str = Field(..., min_length=16)
    database_url: str
    kafka_bootstrap_servers: str = Field(..., description="Comma-separated broker list")
    run_events_topic: str = "coffeebuddy.run.events"
    app_name: str = "CoffeeBuddy"
    slack_timestamp_tolerance_seconds: int = 300

    class Config:
        env_file = ".env"
        env_prefix = "COFFEEBUDDY_"


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
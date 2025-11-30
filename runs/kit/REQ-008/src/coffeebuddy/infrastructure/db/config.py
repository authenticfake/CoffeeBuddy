from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class DatabaseConfig:
    """
    Declarative database configuration.

    The defaults align with the pilot footprint and can be overridden
    via environment variables without modifying code.
    """

    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 5
    pool_timeout: int = 30

    @classmethod
    def from_env(cls, *, env_prefix: str = "COFFEEBUDDY_DB_") -> "DatabaseConfig":
        """
        Build a DatabaseConfig from standardised environment variables.

        Expected environment variables (prefix + name):
            - URL (required)
            - ECHO
            - POOL_SIZE
            - MAX_OVERFLOW
            - POOL_TIMEOUT
        """
        url = getenv(f"{env_prefix}URL")
        if not url:
            raise ValueError(f"{env_prefix}URL must be set")
        echo = getenv(f"{env_prefix}ECHO", "false").lower() == "true"
        pool_size = int(getenv(f"{env_prefix}POOL_SIZE", "5"))
        max_overflow = int(getenv(f"{env_prefix}MAX_OVERFLOW", "5"))
        pool_timeout = int(getenv(f"{env_prefix}POOL_TIMEOUT", "30"))
        return cls(
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
        )
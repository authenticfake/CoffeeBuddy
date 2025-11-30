from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import BaseSettings, Field, AnyHttpUrl, validator


class Settings(BaseSettings):
    """
    Runtime configuration for the CoffeeBuddy service.

    All values are driven via environment variables to keep deployment
    flexible across Kubernetes environments.

    This settings model is intentionally minimal for REQ-010 and is
    expected to be extended in later REQs (DB, Kafka, etc.).
    """

    app_name: str = Field("coffeebuddy", env="COFFEEBUDDY_APP_NAME")
    environment: Literal["dev", "test", "prod"] = Field(
        "dev", env="COFFEEBUDDY_ENVIRONMENT"
    )
    # HTTP bind address information (used in manifests / runner scripts).
    http_host: str = Field("0.0.0.0", env="COFFEEBUDDY_HTTP_HOST")
    http_port: int = Field(8080, env="COFFEEBUDDY_HTTP_PORT")

    # Vault integration
    vault_addr: Optional[AnyHttpUrl] = Field(
        default=None, env="VAULT_ADDR", description="Base URL for Vault HTTP API."
    )
    vault_token: Optional[str] = Field(
        default=None,
        env="VAULT_TOKEN",
        description="Token for Vault, injected via Kubernetes secret.",
    )

    # Ory integration (e.g., for OIDC-related checks if needed)
    ory_base_url: Optional[AnyHttpUrl] = Field(
        default=None,
        env="ORY_BASE_URL",
        description="Base URL for Ory services (e.g., Keto/Hydra).",
    )

    metrics_path: str = Field(
        "/metrics",
        env="COFFEEBUDDY_METRICS_PATH",
        description="Path at which Prometheus metrics are exposed.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("http_port")
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("http_port must be between 1 and 65535")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached accessor for Settings used by the application factory.

    Using lru_cache ensures deterministic behavior for a given process
    and avoids repeatedly parsing environment variables.
    """
    return Settings()
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class ConfigError(RuntimeError):
    """Raised when runtime configuration is invalid or incomplete."""


def _read_env(
    key: str,
    *,
    env: Mapping[str, str],
    default: str | None = None,
    required: bool = False,
) -> str:
    if key in env:
        return env[key]
    if default is not None and not required:
        return default
    if required:
        raise ConfigError(f"Missing required environment variable: {key}")
    return ""


def _read_int(
    key: str,
    *,
    env: Mapping[str, str],
    default: int | None = None,
    required: bool = False,
) -> int:
    raw = _read_env(key, env=env, default=None if required else (str(default) if default is not None else None), required=required)
    if raw == "":
        raise ConfigError(f"Expected integer for {key}")
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"Invalid integer for {key}: {raw}") from exc


def _read_bool(
    key: str,
    *,
    env: Mapping[str, str],
    default: bool = False,
) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str) -> list[str]:
    tokens = [token.strip() for token in value.split(",")]
    return [token for token in tokens if token]


@dataclass(frozen=True)
class SlackConfig:
    signing_secret: str
    bot_token: str
    app_id: str | None


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    pool_min_size: int
    pool_max_size: int


@dataclass(frozen=True)
class KafkaConfig:
    brokers: Sequence[str]
    security_protocol: str
    sasl_username: str | None
    sasl_password: str | None


@dataclass(frozen=True)
class VaultConfig:
    address: str
    role: str
    token_path: Path
    secret_paths: Sequence[str]


@dataclass(frozen=True)
class OryConfig:
    issuer_url: str
    audience: str
    client_id: str


@dataclass(frozen=True)
class MetricsConfig:
    path: str
    multiprocess_dir: Path | None
    enable_default_process_metrics: bool


@dataclass(frozen=True)
class ServiceConfig:
    service_name: str
    environment: str
    version: str
    host: str
    port: int
    slack: SlackConfig
    database: DatabaseConfig
    kafka: KafkaConfig
    vault: VaultConfig
    ory: OryConfig
    metrics: MetricsConfig
    debug_enabled: bool


def load_service_config(env: Mapping[str, str] | None = None) -> ServiceConfig:
    env = env or os.environ

    slack = SlackConfig(
        signing_secret=_read_env("SLACK_SIGNING_SECRET", env=env, required=True),
        bot_token=_read_env("SLACK_BOT_TOKEN", env=env, required=True),
        app_id=_read_env("SLACK_APP_ID", env=env, default=None, required=False) or None,
    )

    database = DatabaseConfig(
        url=_read_env("DATABASE_URL", env=env, required=True),
        pool_min_size=_read_int("DATABASE_POOL_MIN", env=env, default=1),
        pool_max_size=_read_int("DATABASE_POOL_MAX", env=env, default=10),
    )

    kafka = KafkaConfig(
        brokers=_split_csv(_read_env("KAFKA_BROKERS", env=env, required=True)),
        security_protocol=_read_env("KAFKA_SECURITY_PROTOCOL", env=env, default="PLAINTEXT"),
        sasl_username=_read_env("KAFKA_SASL_USERNAME", env=env, default=None),
        sasl_password=_read_env("KAFKA_SASL_PASSWORD", env=env, default=None),
    )

    vault_token_path = Path(_read_env("VAULT_TOKEN_PATH", env=env, default="/var/run/secrets/vault/token"))
    vault = VaultConfig(
        address=_read_env("VAULT_ADDR", env=env, required=True),
        role=_read_env("VAULT_ROLE", env=env, required=True),
        token_path=vault_token_path,
        secret_paths=_split_csv(
            _read_env(
                "VAULT_SECRET_PATHS",
                env=env,
                default="secret/data/coffeebuddy/slack,secret/data/coffeebuddy/database",
            )
        ),
    )

    ory = OryConfig(
        issuer_url=_read_env("ORY_ISSUER_URL", env=env, required=True),
        audience=_read_env("ORY_AUDIENCE", env=env, required=True),
        client_id=_read_env("ORY_CLIENT_ID", env=env, required=True),
    )

    prometheus_dir = _read_env("PROMETHEUS_MULTIPROC_DIR", env=env, default=None)
    metrics = MetricsConfig(
        path=_read_env("METRICS_PATH", env=env, default="/metrics"),
        multiprocess_dir=Path(prometheus_dir) if prometheus_dir else None,
        enable_default_process_metrics=_read_bool("METRICS_ENABLE_PROCESS", env=env, default=True),
    )

    return ServiceConfig(
        service_name=_read_env("SERVICE_NAME", env=env, default="coffeebuddy-service"),
        environment=_read_env("SERVICE_ENV", env=env, default="dev"),
        version=_read_env("SERVICE_VERSION", env=env, default="0.1.0"),
        host=_read_env("SERVICE_HOST", env=env, default="0.0.0.0"),
        port=_read_int("SERVICE_PORT", env=env, default=8080),
        slack=slack,
        database=database,
        kafka=kafka,
        vault=vault,
        ory=ory,
        metrics=metrics,
        debug_enabled=_read_bool("SERVICE_DEBUG", env=env, default=False),
    )


__all__ = [
    "ConfigError",
    "SlackConfig",
    "DatabaseConfig",
    "KafkaConfig",
    "VaultConfig",
    "OryConfig",
    "MetricsConfig",
    "ServiceConfig",
    "load_service_config",
]
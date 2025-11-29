from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

import hvac
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DbCredentials:
    username: str
    password: str
    host: str
    port: int
    database: str
    sslmode: str = "prefer"

    def to_sqlalchemy_url(self) -> str:
        user = quote_plus(self.username)
        pwd = quote_plus(self.password)
        return (
            f"postgresql+psycopg://{user}:{pwd}@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )


@dataclass
class DatabaseConfig:
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 5
    pool_timeout: int = 30

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        echo = os.getenv("SQL_ECHO", "false").lower() == "true"
        pool_size = int(os.getenv("SQL_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("SQL_MAX_OVERFLOW", "5"))
        pool_timeout = int(os.getenv("SQL_POOL_TIMEOUT", "30"))

        vault_secret_path = os.getenv("VAULT_DB_SECRET_PATH")
        if vault_secret_path:
            provider = VaultDbCredentialsProvider(
                secret_path=vault_secret_path,
                url=os.getenv("VAULT_ADDR"),
                token=os.getenv("VAULT_TOKEN"),
                mount_point=os.getenv("VAULT_KV_MOUNT", "secret"),
            )
            credentials = provider.fetch_with_backoff()
            url = credentials.to_sqlalchemy_url()
        else:
            url = os.environ["DATABASE_URL"]

        return cls(
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
        )


class VaultDbCredentialsProvider:
    """Fetches dynamic database credentials from Vault."""

    def __init__(
        self,
        secret_path: str,
        url: Optional[str],
        token: Optional[str],
        mount_point: str = "secret",
        max_attempts: int = 3,
        backoff_seconds: float = 1.5,
    ) -> None:
        self.secret_path = secret_path
        self.mount_point = mount_point
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.client = hvac.Client(url=url, token=token)

    def fetch_with_backoff(self) -> DbCredentials:
        attempt = 0
        last_error: Exception | None = None
        while attempt < self.max_attempts:
            try:
                return self._fetch()
            except Exception as exc:  # pragma: no cover - defensive logging
                last_error = exc
                attempt += 1
                LOGGER.warning(
                    "Vault credential fetch failed (attempt %s/%s): %s",
                    attempt,
                    self.max_attempts,
                    exc,
                )
                time.sleep(self.backoff_seconds * attempt)
        raise RuntimeError("Unable to fetch DB credentials from Vault") from last_error

    def _fetch(self) -> DbCredentials:
        response = self.client.secrets.kv.v2.read_secret_version(
            path=self.secret_path,
            mount_point=self.mount_point,
        )
        data = response["data"]["data"]
        return DbCredentials(
            username=data["username"],
            password=data["password"],
            host=data["host"],
            port=int(data.get("port", 5432)),
            database=data["database"],
            sslmode=data.get("sslmode", "prefer"),
        )


def create_session_factory(config: Optional[DatabaseConfig] = None) -> sessionmaker:
    cfg = config or DatabaseConfig.from_env()
    engine = _create_engine(cfg)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _create_engine(cfg: DatabaseConfig) -> Engine:
    return create_engine(
        cfg.url,
        echo=cfg.echo,
        pool_size=cfg.pool_size,
        max_overflow=cfg.max_overflow,
        pool_timeout=cfg.pool_timeout,
        pool_pre_ping=True,
        future=True,
    )
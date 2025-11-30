from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class KafkaConfig:
    """
    Runtime configuration for Kafka clients.

    Values are read from environment variables to align with platform
    secrets management (Vault → env injection).
    """

    bootstrap_servers: Tuple[str, ...]
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None
    client_id: str = "coffeebuddy-service"
    acks: str | int = "all"
    compression_type: str | None = "lz4"
    linger_ms: int = 5
    enable_idempotence: bool = True
    request_timeout_ms: int = 40000
    metadata_max_age_ms: int = 60000
    topic_prefix: str = "coffeebuddy"

    @classmethod
    def from_env(cls, prefix: str = "KAFKA_") -> "KafkaConfig":
        brokers_raw = os.getenv(f"{prefix}BOOTSTRAP_SERVERS")
        if not brokers_raw:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS must be set")
        servers = tuple(
            host.strip() for host in brokers_raw.split(",") if host.strip()
        )
        if not servers:
            raise ValueError("At least one Kafka bootstrap server must be provided")

        return cls(
            bootstrap_servers=servers,
            security_protocol=os.getenv(f"{prefix}SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv(f"{prefix}SASL_MECHANISM"),
            sasl_username=os.getenv(f"{prefix}SASL_USERNAME"),
            sasl_password=os.getenv(f"{prefix}SASL_PASSWORD"),
            client_id=os.getenv(f"{prefix}CLIENT_ID", "coffeebuddy-service"),
            acks=os.getenv(f"{prefix}ACKS", "all"),
            compression_type=os.getenv(f"{prefix}COMPRESSION", "lz4"),
            linger_ms=int(os.getenv(f"{prefix}LINGER_MS", "5")),
            enable_idempotence=(
                os.getenv(f"{prefix}ENABLE_IDEMPOTENCE", "true").lower() == "true"
            ),
            request_timeout_ms=int(os.getenv(f"{prefix}REQUEST_TIMEOUT_MS", "40000")),
            metadata_max_age_ms=int(os.getenv(f"{prefix}METADATA_MAX_AGE_MS", "60000")),
            topic_prefix=os.getenv(f"{prefix}TOPIC_PREFIX", "coffeebuddy"),
        )

    def producer_kwargs(self) -> Dict[str, Any]:
        """
        Render keyword arguments for AIOKafkaProducer.
        """
        kwargs: Dict[str, Any] = {
            "bootstrap_servers": ",".join(self.bootstrap_servers),
            "client_id": self.client_id,
            "acks": self.acks,
            "compression_type": self.compression_type,
            "linger_ms": self.linger_ms,
            "enable_idempotence": self.enable_idempotence,
            "request_timeout_ms": self.request_timeout_ms,
            "metadata_max_age_ms": self.metadata_max_age_ms,
            "security_protocol": self.security_protocol,
        }
        if self.sasl_mechanism:
            kwargs["sasl_mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            kwargs["sasl_plain_username"] = self.sasl_username
        if self.sasl_password:
            kwargs["sasl_plain_password"] = self.sasl_password
        return kwargs

    def consumer_kwargs(self) -> Dict[str, Any]:
        """
        Render keyword arguments for AIOKafkaConsumer.
        """
        kwargs = {
            "bootstrap_servers": ",".join(self.bootstrap_servers),
            "client_id": self.client_id,
            "request_timeout_ms": self.request_timeout_ms,
            "metadata_max_age_ms": self.metadata_max_age_ms,
            "security_protocol": self.security_protocol,
        }
        if self.sasl_mechanism:
            kwargs["sasl_mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            kwargs["sasl_plain_username"] = self.sasl_username
        if self.sasl_password:
            kwargs["sasl_plain_password"] = self.sasl_password
        return kwargs

    def qualified_topic(self, slug: str) -> str:
        """
        Apply the configured prefix to a logical topic slug.
        """
        prefix = self.topic_prefix.strip()
        return f"{prefix}.{slug}" if prefix else slug


@dataclass(frozen=True)
class ConsumerSettings:
    """
    Behavioral settings for Kafka consumers.
    """

    group_id: str
    topics: Tuple[str, ...]
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    session_timeout_ms: int = 10000
    max_poll_interval_ms: int = 300000
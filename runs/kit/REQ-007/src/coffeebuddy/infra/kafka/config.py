from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class KafkaSettings:
    """Runtime configuration for connecting to the on-prem Kafka cluster."""

    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None
    client_id: str = "coffeebuddy"
    request_timeout_ms: int = 12000

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "KafkaSettings":
        source = env or os.environ
        bootstrap = source.get("KAFKA_BOOTSTRAP_SERVERS")
        if not bootstrap:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS is required")
        return cls(
            bootstrap_servers=bootstrap,
            security_protocol=source.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=source.get("KAFKA_SASL_MECHANISM"),
            sasl_username=source.get("KAFKA_SASL_USERNAME"),
            sasl_password=source.get("KAFKA_SASL_PASSWORD"),
            client_id=source.get("KAFKA_CLIENT_ID", "coffeebuddy"),
            request_timeout_ms=int(source.get("KAFKA_REQUEST_TIMEOUT_MS", "12000")),
        )
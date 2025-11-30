from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Sequence

KafkaHeaders = Mapping[str, str | bytes]
KafkaValue = Any


def _to_bytes(value: Any) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (bytearray, memoryview)):
        return bytes(value)
    raise TypeError(f"Value '{value}' of type '{type(value)}' cannot be coerced to bytes")


def default_serializer(payload: KafkaValue) -> bytes:
    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def normalize_headers(headers: KafkaHeaders | None) -> Sequence[tuple[str, bytes]]:
    normalized = []
    if headers:
        for key, value in headers.items():
            normalized.append((key, _to_bytes(value) or b""))
    return tuple(normalized)


@dataclass(frozen=True)
class KafkaRecord:
    """
    Envelope describing a message ready for Kafka.

    Domain layers construct KafkaRecord instances with already-redacted
    payloads; infrastructure handles serialization and delivery.
    """

    topic: str
    value: KafkaValue
    key: Any | None = None
    headers: KafkaHeaders | None = None
    timestamp_ms: int | None = None

    def as_kwargs(self, serializer=default_serializer) -> MutableMapping[str, Any]:
        value_bytes = serializer(self.value)
        key_bytes = _to_bytes(self.key) if self.key is not None else None
        return {
            "topic": self.topic,
            "value": value_bytes,
            "key": key_bytes,
            "headers": normalize_headers(self.headers),
            "timestamp_ms": self.timestamp_ms,
        }
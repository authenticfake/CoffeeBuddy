from __future__ import annotations

import json
from typing import Any

from kafka import KafkaProducer

from coffeebuddy.events.run import RunCreatedEvent, RunEventPublisher


class KafkaRunEventPublisher(RunEventPublisher):
    """Kafka-backed event publisher for run lifecycle notifications."""

    def __init__(self, *, bootstrap_servers: str, topic: str) -> None:
        self._topic = topic
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=self._serialize,
            linger_ms=10,
            retries=5,
        )

    def publish_run_created(self, event: RunCreatedEvent) -> None:
        payload = event.to_payload()
        future = self._producer.send(
            self._topic,
            key=payload["run_id"].encode(),
            value=payload,
        )
        future.get(timeout=10)

    @staticmethod
    def _serialize(value: dict[str, Any]) -> bytes:
        return json.dumps(value, separators=(",", ":")).encode("utf-8")
import asyncio
from typing import Any

import pytest

from coffeebuddy.infra.kafka.config import KafkaSettings
from coffeebuddy.infra.kafka.models import KafkaEvent
from coffeebuddy.infra.kafka.producer import KafkaEventProducer
from coffeebuddy.infra.kafka.topics import RUN_EVENTS_TOPIC


class StubProducer:
    def __init__(self) -> None:
        self.started = False
        self.sent_payloads: list[dict[str, Any]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def send_and_wait(self, topic: str, value: bytes, **kwargs: Any) -> None:
        if not self.started:
            raise RuntimeError("Producer not started")
        self.sent_payloads.append({"topic": topic, "value": value, **kwargs})


@pytest.mark.asyncio
async def test_producer_emits_bytes_and_tracks_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = StubProducer()
    settings = KafkaSettings(bootstrap_servers="localhost:9092")
    producer = KafkaEventProducer(settings, producer_factory=lambda *args, **kwargs: stub)
    await producer.start()

    event = KafkaEvent(event_type="run_created", correlation_id="corr-123", payload={"run_id": "abc"})
    await producer.send(RUN_EVENTS_TOPIC, event, key="abc")

    assert stub.sent_payloads[0]["topic"] == RUN_EVENTS_TOPIC.name
    assert stub.sent_payloads[0]["key"] == b"abc"

    await producer.stop()


@pytest.mark.asyncio
async def test_producer_requires_start_call() -> None:
    settings = KafkaSettings(bootstrap_servers="localhost:9092")
    producer = KafkaEventProducer(settings, producer_factory=lambda *args, **kwargs: StubProducer())
    event = KafkaEvent(event_type="run_created", correlation_id="corr", payload={})
    with pytest.raises(RuntimeError):
        await producer.send(RUN_EVENTS_TOPIC, event)
import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import pytest

from coffeebuddy.infra.kafka.config import KafkaSettings
from coffeebuddy.infra.kafka.consumer import KafkaEventConsumer
from coffeebuddy.infra.kafka.models import KafkaEvent
from coffeebuddy.infra.kafka.topics import REMINDER_EVENTS_TOPIC


@dataclass
class StubMessage:
    value: bytes
    offset: int = 0


class StubConsumer:
    def __init__(self, payloads: list[bytes]) -> None:
        self._payloads = payloads
        self.started = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._payloads:
            raise StopAsyncIteration
        value = self._payloads.pop(0)
        return StubMessage(value=value)


@pytest.mark.asyncio
async def test_consumer_dispatches_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    processed: list[str] = []

    async def handler(event: KafkaEvent) -> None:
        processed.append(event.event_type)

    settings = KafkaSettings(bootstrap_servers="localhost:9092")
    payload = KafkaEvent(
        event_type="reminder_due",
        correlation_id="cid",
        payload={"reminder_id": "r1", "reminder_type": "runner", "run_id": "run", "channel_id": "chan", "runner_user_id": "user", "scheduled_for": "2024-01-01T00:00:00+00:00", "reminder_offset_minutes": 5},
    ).as_bytes()

    consumer = KafkaEventConsumer(
        settings,
        REMINDER_EVENTS_TOPIC,
        group_id="test",
        handler=handler,
        consumer_factory=lambda *args, **kwargs: StubConsumer([payload]),
    )

    await consumer.start()
    await asyncio.sleep(0)  # allow loop iteration
    await consumer.stop()

    assert processed == ["reminder_due"]
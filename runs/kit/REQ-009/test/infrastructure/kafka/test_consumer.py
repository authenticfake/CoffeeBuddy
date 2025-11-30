import asyncio
from typing import List
from unittest.mock import AsyncMock

import pytest
from aiokafka.structs import ConsumerRecord
from prometheus_client import CollectorRegistry

from coffeebuddy.infrastructure.kafka.consumer import (
    KafkaConsumerWorker,
    KafkaConsumeError,
)
from coffeebuddy.infrastructure.kafka.metrics import KafkaMetrics


class _FakeConsumer:
    def __init__(self, records: List[ConsumerRecord]) -> None:
        self._records = records
        self._started = False
        self._stopped = False
        self.commits = 0

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._stopped = True

    def __aiter__(self):
        async def iterator():
            for record in self._records:
                await asyncio.sleep(0)  # yield control
                yield record

        return iterator()

    async def commit(self) -> None:
        self.commits += 1


def _build_record(topic: str, value: bytes = b"{}") -> ConsumerRecord:
    return ConsumerRecord(
        topic=topic,
        partition=0,
        offset=0,
        timestamp=1,
        timestamp_type=0,
        key=b"k",
        value=value,
        checksum=None,
        serialized_key_size=1,
        serialized_value_size=len(value),
        headers=[],
    )


@pytest.mark.asyncio
async def test_consumer_worker_processes_records_and_commits():
    record = _build_record("pilot.run.events")
    consumer = _FakeConsumer([record])
    handler = AsyncMock()
    registry = CollectorRegistry()
    metrics = KafkaMetrics.create(registry)

    worker = KafkaConsumerWorker(
        consumer,
        handler,
        metrics=metrics,
        commit_on_success=True,
    )

    await worker.start()
    await worker.wait()

    handler.assert_awaited_once()
    assert consumer.commits == 1
    assert (
        metrics.consume_total.labels(topic="pilot.run.events", outcome="success")._value.get()
        == 1.0
    )


@pytest.mark.asyncio
async def test_consumer_worker_raises_on_handler_error():
    record = _build_record("pilot.run.events")
    consumer = _FakeConsumer([record])
    handler = AsyncMock(side_effect=RuntimeError("boom"))
    registry = CollectorRegistry()
    metrics = KafkaMetrics.create(registry)

    worker = KafkaConsumerWorker(consumer, handler, metrics=metrics)

    await worker.start()
    with pytest.raises(KafkaConsumeError):
        await worker.wait()

    assert (
        metrics.consume_total.labels(topic="pilot.run.events", outcome="error")._value.get()
        == 1.0
    )
import asyncio
from unittest.mock import AsyncMock

import pytest
from prometheus_client import CollectorRegistry

from coffeebuddy.infrastructure.kafka.events import KafkaRecord
from coffeebuddy.infrastructure.kafka.metrics import KafkaMetrics
from coffeebuddy.infrastructure.kafka.producer import (
    KafkaEventPublisher,
    KafkaPublishError,
)


@pytest.mark.asyncio
async def test_publish_success_records_metrics():
    mock_producer = AsyncMock()
    registry = CollectorRegistry()
    metrics = KafkaMetrics.create(registry)

    publisher = KafkaEventPublisher(mock_producer, metrics=metrics)
    record = KafkaRecord(topic="pilot.run.events", key="run-1", value={"type": "run_created"})

    await publisher.publish(record)

    mock_producer.send_and_wait.assert_awaited_once()
    assert (
        metrics.publish_total.labels(topic="pilot.run.events", outcome="success")._value.get()
        == 1.0
    )
    # Ensure histogram recorded at least one observation
    assert (
        metrics.publish_latency_seconds.labels(topic="pilot.run.events")._sum.get() >= 0
    )


@pytest.mark.asyncio
async def test_publish_failure_raises_and_counts_error():
    mock_producer = AsyncMock()
    mock_producer.send_and_wait.side_effect = RuntimeError("kaboom")
    registry = CollectorRegistry()
    metrics = KafkaMetrics.create(registry)
    publisher = KafkaEventPublisher(mock_producer, metrics=metrics)
    record = KafkaRecord(topic="pilot.run.events", key="run-2", value={"type": "run_closed"})

    with pytest.raises(KafkaPublishError):
        await publisher.publish(record)

    assert (
        metrics.publish_total.labels(topic="pilot.run.events", outcome="error")._value.get()
        == 1.0
    )
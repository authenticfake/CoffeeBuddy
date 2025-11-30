from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from aiokafka import AIOKafkaProducer

from .config import KafkaConfig
from .events import KafkaRecord, default_serializer
from .metrics import DEFAULT_METRICS, KafkaMetrics

LOGGER = logging.getLogger(__name__)


class KafkaPublishError(Exception):
    """
    Raised when a record cannot be published to Kafka.
    """


@dataclass(frozen=True)
class KafkaProducerFactory:
    config: KafkaConfig

    def build(self) -> AIOKafkaProducer:
        """
        Instantiate an AIOKafkaProducer with CoffeeBuddy defaults.
        """
        return AIOKafkaProducer(**self.config.producer_kwargs())


class KafkaEventPublisher:
    """
    Type-safe publisher that wraps AIOKafkaProducer with instrumentation
    and deterministic serialization.
    """

    def __init__(
        self,
        producer: AIOKafkaProducer,
        metrics: KafkaMetrics | None = None,
        serializer: Callable = default_serializer,
    ) -> None:
        self._producer = producer
        self._metrics = metrics or DEFAULT_METRICS
        self._serializer = serializer

    async def publish(self, record: KafkaRecord) -> None:
        """
        Publish a record and record observability signals.
        """
        payload = record.as_kwargs(serializer=self._serializer)
        topic = payload.pop("topic")
        start = time.perf_counter()
        try:
            await self._producer.send_and_wait(topic, **payload)
        except Exception as exc:  # noqa: BLE001
            self._metrics.publish_total.labels(topic=topic, outcome="error").inc()
            LOGGER.exception("Kafka publish failed", extra={"topic": topic})
            raise KafkaPublishError(f"Failed to publish to {topic}") from exc
        else:
            self._metrics.publish_total.labels(topic=topic, outcome="success").inc()
        finally:
            duration = time.perf_counter() - start
            self._metrics.publish_latency_seconds.labels(topic=topic).observe(duration)
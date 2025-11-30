from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Protocol

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import ConsumerRecord

from .config import ConsumerSettings, KafkaConfig
from .metrics import DEFAULT_METRICS, KafkaMetrics

LOGGER = logging.getLogger(__name__)


class KafkaConsumeError(Exception):
    """
    Raised when a Kafka handler fails to process a message.
    """

    def __init__(self, topic: str, partition: int, offset: int, cause: Exception) -> None:
        super().__init__(
            f"Failed to process Kafka message topic={topic} partition={partition} offset={offset}"
        )
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.__cause__ = cause


class KafkaMessageHandler(Protocol):
    async def __call__(self, record: ConsumerRecord) -> None:
        ...


@dataclass(frozen=True)
class KafkaConsumerFactory:
    config: KafkaConfig
    settings: ConsumerSettings

    def build(self) -> AIOKafkaConsumer:
        kwargs = self.config.consumer_kwargs()
        kwargs.update(
            {
                "group_id": self.settings.group_id,
                "auto_offset_reset": self.settings.auto_offset_reset,
                "enable_auto_commit": self.settings.enable_auto_commit,
                "session_timeout_ms": self.settings.session_timeout_ms,
                "max_poll_interval_ms": self.settings.max_poll_interval_ms,
            }
        )
        return AIOKafkaConsumer(*self.settings.topics, **kwargs)


class KafkaConsumerWorker:
    """
    Async task that drives an AIOKafkaConsumer with robust instrumentation.
    """

    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        handler: KafkaMessageHandler,
        *,
        metrics: KafkaMetrics | None = None,
        commit_on_success: bool = False,
    ) -> None:
        self._consumer = consumer
        self._handler = handler
        self._metrics = metrics or DEFAULT_METRICS
        self._commit_on_success = commit_on_success
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        if self._task:
            raise RuntimeError("Consumer already started")
        await self._consumer.start()
        self._stopped.clear()
        self._task = asyncio.create_task(self._run(), name="KafkaConsumerWorker")

    async def stop(self) -> None:
        if not self._task:
            await self._consumer.stop()
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def wait(self) -> None:
        if self._task:
            await self._task

    async def _run(self) -> None:
        try:
            async for message in self._consumer:
                await self._handle_message(message)
        except asyncio.CancelledError:
            raise
        finally:
            await self._consumer.stop()
            self._stopped.set()

    async def _handle_message(self, record: ConsumerRecord) -> None:
        topic = record.topic
        start = time.perf_counter()
        try:
            await self._handler(record)
        except Exception as exc:  # noqa: BLE001
            self._metrics.consume_total.labels(topic=topic, outcome="error").inc()
            LOGGER.exception(
                "Kafka handler failed",
                extra={"topic": topic, "partition": record.partition, "offset": record.offset},
            )
            raise KafkaConsumeError(topic, record.partition, record.offset, exc) from exc
        else:
            self._metrics.consume_total.labels(topic=topic, outcome="success").inc()
            if self._commit_on_success:
                await self._consumer.commit()
        finally:
            latency = time.perf_counter() - start
            self._metrics.consume_latency_seconds.labels(topic=topic).observe(latency)
            if record.timestamp != -1:
                lag = max(0.0, time.time() - record.timestamp / 1000)
                self._metrics.consume_lag_seconds.labels(topic=topic).observe(lag)


import contextlib  # placed at end to avoid circular import order complaints.
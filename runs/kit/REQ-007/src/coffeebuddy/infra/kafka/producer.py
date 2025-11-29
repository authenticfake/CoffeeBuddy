from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from aiokafka import AIOKafkaProducer

from .config import KafkaSettings
from .metrics import KAFKA_PRODUCE_TOTAL
from .models import KafkaEvent
from .topics import TopicConfig

logger = logging.getLogger(__name__)

ProducerFactory = Callable[[KafkaSettings, asyncio.AbstractEventLoop | None], AIOKafkaProducer]


class KafkaEventProducer:
    """Typed producer that enforces correlation IDs and metrics for all sends."""

    def __init__(
        self,
        settings: KafkaSettings,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        producer_factory: ProducerFactory | None = None,
    ) -> None:
        self._settings = settings
        self._loop = loop
        self._producer_factory = producer_factory or self._default_factory
        self._producer: AIOKafkaProducer | None = None

    def _default_factory(
        self,
        settings: KafkaSettings,
        loop: asyncio.AbstractEventLoop | None,
    ) -> AIOKafkaProducer:
        return AIOKafkaProducer(
            bootstrap_servers=settings.bootstrap_servers,
            security_protocol=settings.security_protocol,
            sasl_mechanism=settings.sasl_mechanism,
            sasl_plain_username=settings.sasl_username,
            sasl_plain_password=settings.sasl_password,
            client_id=settings.client_id,
            request_timeout_ms=settings.request_timeout_ms,
            loop=loop,
        )

    async def start(self) -> None:
        if self._producer is not None:
            return
        self._producer = self._producer_factory(self._settings, self._loop)
        await self._producer.start()
        logger.info("Kafka producer started", extra={"client_id": self._settings.client_id})

    async def stop(self) -> None:
        if self._producer is None:
            return
        await self._producer.stop()
        self._producer = None
        logger.info("Kafka producer stopped", extra={"client_id": self._settings.client_id})

    async def send(
        self,
        topic: TopicConfig,
        event: KafkaEvent,
        *,
        key: str | None = None,
        headers: list[tuple[str, bytes]] | None = None,
    ) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaEventProducer.start() must be called before send().")
        payload_bytes = event.as_bytes()
        key_bytes = key.encode("utf-8") if key else None
        try:
            await self._producer.send_and_wait(
                topic.name,
                payload_bytes,
                key=key_bytes,
                headers=headers,
            )
            KAFKA_PRODUCE_TOTAL.labels(topic=topic.name, status="success").inc()
            logger.debug(
                "Kafka message produced",
                extra={"topic": topic.name, "event_type": event.event_type},
            )
        except Exception:
            KAFKA_PRODUCE_TOTAL.labels(topic=topic.name, status="error").inc()
            logger.exception(
                "Failed to produce Kafka message",
                extra={"topic": topic.name, "event_type": event.event_type},
            )
            raise
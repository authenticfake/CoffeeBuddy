from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

from .config import KafkaSettings
from .metrics import KAFKA_CONSUME_TOTAL
from .models import KafkaEvent
from .topics import TopicConfig

logger = logging.getLogger(__name__)

Handler = Callable[[KafkaEvent], Awaitable[None]]
ConsumerFactory = Callable[[KafkaSettings, TopicConfig, str, asyncio.AbstractEventLoop | None], AIOKafkaConsumer]


class KafkaEventConsumer:
    """Shared consumer harness with graceful shutdown and metrics hooks."""

    def __init__(
        self,
        settings: KafkaSettings,
        topic: TopicConfig,
        group_id: str,
        handler: Handler,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        consumer_factory: ConsumerFactory | None = None,
    ) -> None:
        self._settings = settings
        self._topic = topic
        self._group_id = group_id
        self._handler = handler
        self._loop = loop
        self._consumer_factory = consumer_factory or self._default_factory
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def _default_factory(
        self,
        settings: KafkaSettings,
        topic: TopicConfig,
        group_id: str,
        loop: asyncio.AbstractEventLoop | None,
    ) -> AIOKafkaConsumer:
        return AIOKafkaConsumer(
            topic.name,
            bootstrap_servers=settings.bootstrap_servers,
            security_protocol=settings.security_protocol,
            sasl_mechanism=settings.sasl_mechanism,
            sasl_plain_username=settings.sasl_username,
            sasl_plain_password=settings.sasl_password,
            group_id=group_id,
            client_id=f"{settings.client_id}.{group_id}",
            enable_auto_commit=True,
            auto_offset_reset="earliest",
            request_timeout_ms=settings.request_timeout_ms,
            loop=loop,
        )

    async def start(self) -> None:
        if self._consumer is not None:
            return
        self._stop_event.clear()
        self._consumer = self._consumer_factory(self._settings, self._topic, self._group_id, self._loop)
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            "Kafka consumer started",
            extra={"topic": self._topic.name, "group_id": self._group_id},
        )

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
        logger.info(
            "Kafka consumer stopped",
            extra={"topic": self._topic.name, "group_id": self._group_id},
        )

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        try:
            async for message in self._consumer:
                if self._stop_event.is_set():
                    break
                try:
                    event = KafkaEvent.model_validate_json(message.value)
                    await self._handler(event)
                    KAFKA_CONSUME_TOTAL.labels(topic=self._topic.name, status="success").inc()
                except Exception:
                    KAFKA_CONSUME_TOTAL.labels(topic=self._topic.name, status="error").inc()
                    logger.exception(
                        "Kafka handler failed",
                        extra={
                            "topic": self._topic.name,
                            "group_id": self._group_id,
                            "message_offset": getattr(message, "offset", None),
                        },
                    )
        except asyncio.CancelledError:
            logger.debug("Kafka consume loop cancelled", extra={"topic": self._topic.name})
            raise
        except Exception:
            KAFKA_CONSUME_TOTAL.labels(topic=self._topic.name, status="error").inc()
            logger.exception(
                "Kafka consume loop error",
                extra={"topic": self._topic.name, "group_id": self._group_id},
            )
            raise


import contextlib  # placed at end to avoid circular import issues
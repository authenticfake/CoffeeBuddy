"""
Kafka infrastructure primitives for CoffeeBuddy.

REQ-009 introduces the canonical Kafka wiring: topic definitions,
configuration helpers, producer/consumer factories, and instrumentation.
"""

from .config import KafkaConfig, ConsumerSettings
from .consumer import KafkaConsumerFactory, KafkaConsumerWorker, KafkaConsumeError
from .events import KafkaRecord
from .metrics import KafkaMetrics, DEFAULT_METRICS
from .producer import KafkaEventPublisher, KafkaProducerFactory, KafkaPublishError
from .topics import (
    TopicDefinition,
    TopicRegistry,
    RUN_EVENTS_TOPIC,
    REMINDER_EVENTS_TOPIC,
)

__all__ = [
    "KafkaConfig",
    "ConsumerSettings",
    "KafkaProducerFactory",
    "KafkaEventPublisher",
    "KafkaPublishError",
    "KafkaConsumerFactory",
    "KafkaConsumerWorker",
    "KafkaConsumeError",
    "KafkaRecord",
    "KafkaMetrics",
    "DEFAULT_METRICS",
    "TopicDefinition",
    "TopicRegistry",
    "RUN_EVENTS_TOPIC",
    "REMINDER_EVENTS_TOPIC",
]
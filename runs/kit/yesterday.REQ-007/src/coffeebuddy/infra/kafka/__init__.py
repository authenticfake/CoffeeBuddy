"""Kafka infrastructure utilities for CoffeeBuddy.

This package exposes the topic catalog, event models, producer/consumer abstractions,
and reminder worker harness used across application slices. App code should import
symbols from here instead of instantiating Kafka clients directly to ensure
consistent configuration, metrics, and observability.
"""

from .config import KafkaSettings
from .models import KafkaEvent, ReminderPayload, ReminderType
from .producer import KafkaEventProducer
from .consumer import KafkaEventConsumer
from .reminder_worker import ReminderWorker, ReminderSender
from .topics import (
    TOPIC_REGISTRY,
    ACL_REQUIREMENTS,
    RUN_EVENTS_TOPIC,
    REMINDER_EVENTS_TOPIC,
    TopicACLRequirement,
    TopicConfig,
)

__all__ = [
    "KafkaSettings",
    "KafkaEvent",
    "ReminderPayload",
    "ReminderType",
    "KafkaEventProducer",
    "KafkaEventConsumer",
    "ReminderWorker",
    "ReminderSender",
    "TOPIC_REGISTRY",
    "ACL_REQUIREMENTS",
    "RUN_EVENTS_TOPIC",
    "REMINDER_EVENTS_TOPIC",
    "TopicACLRequirement",
    "TopicConfig",
]
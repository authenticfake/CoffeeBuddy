from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class TopicDefinition:
    """
    Declarative definition of a Kafka topic required by CoffeeBuddy.
    """

    slug: str
    partitions: int
    replication_factor: int
    retention_ms: int
    cleanup_policy: str = "delete"
    description: str = ""

    def full_name(self, prefix: str) -> str:
        prefix = prefix.strip()
        return f"{prefix}.{self.slug}" if prefix else self.slug


RUN_EVENTS_TOPIC = TopicDefinition(
    slug="run.events",
    partitions=3,
    replication_factor=3,
    retention_ms=7 * 24 * 60 * 60 * 1000,
    cleanup_policy="delete",
    description="Lifecycle events for runs (created, closed, failed).",
)

REMINDER_EVENTS_TOPIC = TopicDefinition(
    slug="reminder.events",
    partitions=3,
    replication_factor=3,
    retention_ms=24 * 60 * 60 * 1000,
    cleanup_policy="delete",
    description="Scheduled reminder jobs (due events, sent notifications).",
)


class TopicRegistry:
    """
    Computes fully-qualified topic names and exposes topic metadata.

    Platform teams can render infrastructure (e.g., Terraform) by reading
    this registry, ensuring a single source of truth.
    """

    def __init__(self, prefix: str) -> None:
        self._prefix = prefix
        self._definitions: Dict[str, TopicDefinition] = {
            RUN_EVENTS_TOPIC.slug: RUN_EVENTS_TOPIC,
            REMINDER_EVENTS_TOPIC.slug: REMINDER_EVENTS_TOPIC,
        }

    @property
    def prefix(self) -> str:
        return self._prefix

    def list(self) -> Iterable[Tuple[str, TopicDefinition]]:
        for slug, definition in self._definitions.items():
            yield definition.full_name(self._prefix), definition

    def resolve(self, slug: str) -> str:
        if slug not in self._definitions:
            raise KeyError(f"Unknown topic slug '{slug}'")
        return self._definitions[slug].full_name(self._prefix)

    def definition(self, slug: str) -> TopicDefinition:
        try:
            return self._definitions[slug]
        except KeyError as exc:
            raise KeyError(f"Unknown topic slug '{slug}'") from exc
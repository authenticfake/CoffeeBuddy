from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(slots=True, frozen=True)
class TopicConfig:
    """Declarative topic definition rendered for platform provisioning."""

    name: str
    partitions: int
    replication_factor: int
    retention_ms: int
    cleanup_policy: str
    description: str
    configs: Mapping[str, str] = field(default_factory=dict)

    def render_admin_request(self) -> dict:
        return {
            "topic": self.name,
            "num_partitions": self.partitions,
            "replication_factor": self.replication_factor,
            "configs": {
                "retention.ms": str(self.retention_ms),
                "cleanup.policy": self.cleanup_policy,
                **self.configs,
            },
        }


@dataclass(slots=True, frozen=True)
class TopicACLRequirement:
    """Captures ACL handoff notes for platform teams."""

    principal: str
    operation: str
    resource: str
    description: str


RUN_EVENTS_TOPIC = TopicConfig(
    name="coffeebuddy.run.events",
    partitions=3,
    replication_factor=3,
    retention_ms=7 * 24 * 60 * 60 * 1000,  # 7 days
    cleanup_policy="delete",
    description="Lifecycle events for coffee runs (created, updated, closed).",
    configs={"min.insync.replicas": "2"},
)

REMINDER_EVENTS_TOPIC = TopicConfig(
    name="coffeebuddy.reminder.events",
    partitions=3,
    replication_factor=3,
    retention_ms=24 * 60 * 60 * 1000,  # 24 hours
    cleanup_policy="delete",
    description="Reminder scheduling payloads (runner reminders, last call alerts).",
    configs={"min.insync.replicas": "2"},
)

TOPIC_REGISTRY: tuple[TopicConfig, ...] = (RUN_EVENTS_TOPIC, REMINDER_EVENTS_TOPIC)

ACL_REQUIREMENTS: tuple[TopicACLRequirement, ...] = (
    TopicACLRequirement(
        principal="User:svc_coffeebuddy_app",
        operation="Describe,Read,Write",
        resource=f"Topic:{RUN_EVENTS_TOPIC.name}",
        description="API service produces run lifecycle events.",
    ),
    TopicACLRequirement(
        principal="User:svc_coffeebuddy_reminder_worker",
        operation="Describe,Read,Write",
        resource=f"Topic:{REMINDER_EVENTS_TOPIC.name}",
        description="Reminder worker consumes reminder events and emits outcomes.",
    ),
)

__all__ = [
    "TopicConfig",
    "TopicACLRequirement",
    "RUN_EVENTS_TOPIC",
    "REMINDER_EVENTS_TOPIC",
    "TOPIC_REGISTRY",
    "ACL_REQUIREMENTS",
]
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Protocol
from uuid import uuid4

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload, ReminderType
from coffeebuddy.infra.kafka.topics import REMINDER_EVENTS_TOPIC

LOGGER = logging.getLogger(__name__)


class EventPublisher(Protocol):
    """Minimal abstraction over Kafka event publishing."""

    def publish(self, *, topic: str, event: KafkaEvent) -> None: ...


@dataclass(frozen=True)
class ChannelReminderConfig:
    """Snapshot of channel reminder settings captured at scheduling time."""

    channel_id: str
    reminders_enabled: bool
    reminder_offset_minutes: int
    last_call_enabled: bool
    last_call_lead_minutes: int | None = None


class ReminderScheduler:
    """Creates reminder payloads and enqueues them on Kafka."""

    def __init__(
        self,
        publisher: EventPublisher,
        *,
        reminder_event_type: str = "reminder_scheduled",
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._publisher = publisher
        self._event_type = reminder_event_type
        self._id_factory = id_factory or (lambda: uuid4().hex)

    def schedule_for_run(
        self,
        *,
        run_id: str,
        pickup_time: datetime | None,
        runner_user_id: str | None,
        channel: ChannelReminderConfig,
        correlation_id: str,
    ) -> List[ReminderPayload]:
        """Enqueue runner and optional last-call reminders if permitted."""
        if pickup_time is None:
            LOGGER.debug("Run %s has no pickup time; skipping reminders.", run_id)
            return []

        aware_pickup = self._as_aware(pickup_time)
        scheduled_payloads: List[ReminderPayload] = []

        if channel.reminders_enabled and runner_user_id:
            payload = self._build_payload(
                run_id=run_id,
                channel=channel,
                runner_user_id=runner_user_id,
                scheduled_for=aware_pickup - timedelta(minutes=channel.reminder_offset_minutes),
                reminder_type="runner",
                correlation_id=correlation_id,
            )
            self._publish(payload)
            scheduled_payloads.append(payload)
        elif channel.reminders_enabled and not runner_user_id:
            LOGGER.info(
                "Run %s has pickup time but no runner yet; runner reminder not scheduled.",
                run_id,
            )
        else:
            LOGGER.info(
                "Reminders disabled for channel %s; runner reminder suppressed.", channel.channel_id
            )

        if (
            channel.reminders_enabled
            and channel.last_call_enabled
            and channel.last_call_lead_minutes
            and channel.last_call_lead_minutes > 0
        ):
            payload = self._build_payload(
                run_id=run_id,
                channel=channel,
                runner_user_id=None,
                scheduled_for=aware_pickup - timedelta(minutes=channel.last_call_lead_minutes),
                reminder_type="last_call",
                correlation_id=correlation_id,
            )
            self._publish(payload)
            scheduled_payloads.append(payload)
        elif channel.last_call_enabled and not channel.reminders_enabled:
            LOGGER.info(
                "Last-call enabled but reminders disabled globally for channel %s.",
                channel.channel_id,
            )

        return scheduled_payloads

    def _build_payload(
        self,
        *,
        run_id: str,
        channel: ChannelReminderConfig,
        runner_user_id: str | None,
        scheduled_for: datetime,
        reminder_type: ReminderType,
        correlation_id: str,
    ) -> ReminderPayload:
        payload = ReminderPayload(
            reminder_id=self._id_factory(),
            run_id=str(run_id),
            channel_id=str(channel.channel_id),
            runner_user_id=str(runner_user_id) if runner_user_id else None,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            reminder_offset_minutes=channel.reminder_offset_minutes,
            channel_reminders_enabled=channel.reminders_enabled,
            last_call_enabled=channel.last_call_enabled,
            correlation_id=correlation_id,
        )
        LOGGER.debug(
            "Built reminder payload %s for run %s (type=%s).",
            payload.reminder_id,
            run_id,
            reminder_type,
        )
        return payload

    def _publish(self, payload: ReminderPayload) -> None:
        event = KafkaEvent(
            event_type=self._event_type,
            correlation_id=payload.correlation_id,
            payload=payload.model_dump(),
        )
        LOGGER.info(
            "Publishing reminder %s for channel %s to topic %s.",
            payload.reminder_id,
            payload.channel_id,
            REMINDER_EVENTS_TOPIC.name,
        )
        self._publisher.publish(topic=REMINDER_EVENTS_TOPIC.name, event=event)

    @staticmethod
    def _as_aware(timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)
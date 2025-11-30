from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Protocol
from uuid import uuid4

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload, ReminderType
from coffeebuddy.infra.kafka.topics import REMINDER_EVENTS_TOPIC

LOGGER = logging.getLogger(__name__)
MIN_DELAY_SECONDS = 5


class EventPublisher(Protocol):
    """Minimal abstraction over the Kafka producer."""

    def publish(self, *, topic: str, event: KafkaEvent) -> None: ...


@dataclass(frozen=True)
class ChannelReminderConfig:
    """Snapshot of per-channel reminder switches captured during scheduling."""

    channel_id: str
    reminders_enabled: bool
    reminder_offset_minutes: int
    last_call_enabled: bool
    last_call_lead_minutes: int | None = None


@dataclass(frozen=True)
class RunReminderContext:
    """Inputs required to schedule reminder payloads."""

    run_id: str
    channel_id: str
    runner_user_id: str | None
    pickup_time: datetime | None
    correlation_id: str


class ReminderScheduler:
    """Creates reminder payloads and enqueues them on Kafka."""

    def __init__(
        self,
        publisher: EventPublisher,
        *,
        reminder_event_type: str = "reminder_scheduled",
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._publisher = publisher
        self._event_type = reminder_event_type
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def schedule_for_run(
        self,
        *,
        context: RunReminderContext,
        config: ChannelReminderConfig,
    ) -> List[KafkaEvent]:
        if context.pickup_time is None:
            LOGGER.info("Skipping reminder scheduling because pickup time not provided", extra={"run_id": context.run_id})
            return []
        if not config.reminders_enabled:
            LOGGER.info(
                "Skipping reminder scheduling because channel disabled reminders",
                extra={"channel_id": config.channel_id, "run_id": context.run_id},
            )
            return []

        pickup_time = self._ensure_timezone(context.pickup_time)
        events: List[KafkaEvent] = []

        runner_event = self._maybe_build_runner_event(context=context, config=config, pickup_time=pickup_time)
        if runner_event:
            self._publisher.publish(topic=REMINDER_EVENTS_TOPIC.name, event=runner_event)
            events.append(runner_event)

        last_call_event = self._maybe_build_last_call_event(context=context, config=config, pickup_time=pickup_time)
        if last_call_event:
            self._publisher.publish(topic=REMINDER_EVENTS_TOPIC.name, event=last_call_event)
            events.append(last_call_event)

        return events

    def _maybe_build_runner_event(
        self,
        *,
        context: RunReminderContext,
        config: ChannelReminderConfig,
        pickup_time: datetime,
    ) -> KafkaEvent | None:
        if context.runner_user_id is None:
            LOGGER.warning(
                "Runner not assigned; runner reminder skipped",
                extra={"run_id": context.run_id},
            )
            return None
        scheduled_for = pickup_time - timedelta(minutes=config.reminder_offset_minutes)
        scheduled_for = self._ensure_future(scheduled_for)
        payload = self._build_payload(
            context=context,
            reminder_type="runner",
            scheduled_for=scheduled_for,
            config=config,
        )
        LOGGER.info(
            "Queued runner reminder",
            extra={
                "run_id": context.run_id,
                "reminder_id": payload.reminder_id,
                "scheduled_for": scheduled_for.isoformat(),
            },
        )
        return self._wrap_event(payload)

    def _maybe_build_last_call_event(
        self,
        *,
        context: RunReminderContext,
        config: ChannelReminderConfig,
        pickup_time: datetime,
    ) -> KafkaEvent | None:
        if not config.last_call_enabled or config.last_call_lead_minutes is None:
            return None
        scheduled_for = pickup_time - timedelta(minutes=config.last_call_lead_minutes)
        scheduled_for = self._ensure_future(scheduled_for)
        payload = self._build_payload(
            context=context,
            reminder_type="last_call",
            scheduled_for=scheduled_for,
            config=config,
        )
        LOGGER.info(
            "Queued last call reminder",
            extra={
                "run_id": context.run_id,
                "reminder_id": payload.reminder_id,
                "scheduled_for": scheduled_for.isoformat(),
            },
        )
        return self._wrap_event(payload)

    def _build_payload(
        self,
        *,
        context: RunReminderContext,
        reminder_type: ReminderType,
        scheduled_for: datetime,
        config: ChannelReminderConfig,
    ) -> ReminderPayload:
        return ReminderPayload(
            reminder_id=str(uuid4()),
            run_id=context.run_id,
            channel_id=context.channel_id,
            runner_user_id=context.runner_user_id,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            reminder_offset_minutes=config.reminder_offset_minutes,
            channel_reminders_enabled=config.reminders_enabled,
            last_call_enabled=config.last_call_enabled,
            correlation_id=context.correlation_id,
        )

    def _wrap_event(self, payload: ReminderPayload) -> KafkaEvent:
        return KafkaEvent(
            event_type=self._event_type,
            correlation_id=payload.correlation_id,
            payload=payload.model_dump(mode="json"),
        )

    def _ensure_future(self, scheduled_for: datetime) -> datetime:
        now = self._clock()
        min_allowed = now + timedelta(seconds=MIN_DELAY_SECONDS)
        if scheduled_for < min_allowed:
            return min_allowed
        return scheduled_for

    @staticmethod
    def _ensure_timezone(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


__all__ = [
    "ReminderScheduler",
    "ChannelReminderConfig",
    "RunReminderContext",
    "EventPublisher",
]
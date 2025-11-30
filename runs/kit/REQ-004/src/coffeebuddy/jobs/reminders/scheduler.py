from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Protocol
from uuid import uuid4

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.infra.kafka.topics import REMINDER_EVENTS_TOPIC

LOGGER = logging.getLogger(__name__)

Clock = Callable[[], datetime]


class EventPublisher(Protocol):
    """Abstraction used to publish Kafka events."""

    def publish(self, *, topic: str, event: KafkaEvent) -> None: ...


@dataclass(frozen=True)
class ChannelReminderConfig:
    """Snapshot of reminder-related channel configuration."""

    channel_id: str
    reminders_enabled: bool
    reminder_offset_minutes: int
    last_call_enabled: bool
    last_call_lead_minutes: int | None = None


@dataclass(frozen=True)
class RunReminderContext:
    """Run-specific context captured when scheduling reminders."""

    run_id: str
    channel_id: str
    runner_user_id: str | None
    correlation_id: str


@dataclass(frozen=True)
class ScheduleResult:
    """Return value describing which reminders were queued."""

    runner_reminder_id: str | None = None
    last_call_reminder_id: str | None = None

    @property
    def reminder_ids(self) -> tuple[str, ...]:
        return tuple(
            reminder_id
            for reminder_id in (self.runner_reminder_id, self.last_call_reminder_id)
            if reminder_id is not None
        )


class ReminderScheduler:
    """Produces reminder payloads and pushes them to Kafka."""

    def __init__(
        self,
        publisher: EventPublisher,
        *,
        reminder_event_type: str = "reminder_scheduled",
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._publisher = publisher
        self._event_type = reminder_event_type
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._id_factory = id_factory or (lambda: str(uuid4()))

    def schedule(
        self,
        *,
        context: RunReminderContext,
        config: ChannelReminderConfig,
        pickup_time: datetime | None,
    ) -> ScheduleResult:
        if pickup_time is None:
            LOGGER.debug(
                "Reminder scheduling skipped: pickup time missing",
                extra={"run_id": context.run_id},
            )
            return ScheduleResult()
        if not config.reminders_enabled:
            LOGGER.info(
                "Reminder scheduling skipped: reminders disabled",
                extra={"run_id": context.run_id, "channel_id": config.channel_id},
            )
            return ScheduleResult()

        pickup_time = self._ensure_timezone(pickup_time)
        events = list(
            filter(
                None,
                (
                    self._maybe_build_runner_event(
                        context=context, config=config, pickup_time=pickup_time
                    ),
                    self._maybe_build_last_call_event(
                        context=context, config=config, pickup_time=pickup_time
                    ),
                ),
            )
        )

        for event in events:
            self._publisher.publish(topic=REMINDER_EVENTS_TOPIC.name, event=event)
            LOGGER.debug(
                "Reminder event published",
                extra={
                    "run_id": context.run_id,
                    "reminder_id": event.payload["reminder_id"],
                    "reminder_type": event.payload["reminder_type"],
                },
            )

        return ScheduleResult(
            runner_reminder_id=_get_payload_value(events, "runner"),
            last_call_reminder_id=_get_payload_value(events, "last_call"),
        )

    def _maybe_build_runner_event(
        self,
        *,
        context: RunReminderContext,
        config: ChannelReminderConfig,
        pickup_time: datetime,
    ) -> KafkaEvent | None:
        if context.runner_user_id is None:
            LOGGER.warning(
                "Runner reminder skipped because runner is missing",
                extra={"run_id": context.run_id},
            )
            return None
        scheduled_for = self._ensure_future(
            pickup_time - timedelta(minutes=config.reminder_offset_minutes)
        )
        payload = self._build_payload(
            context=context,
            reminder_type="runner",
            scheduled_for=scheduled_for,
            offset_minutes=config.reminder_offset_minutes,
            config=config,
        )
        return self._wrap_event(payload)

    def _maybe_build_last_call_event(
        self,
        *,
        context: RunReminderContext,
        config: ChannelReminderConfig,
        pickup_time: datetime,
    ) -> KafkaEvent | None:
        if not config.last_call_enabled or not config.last_call_lead_minutes:
            return None
        scheduled_for = self._ensure_future(
            pickup_time - timedelta(minutes=config.last_call_lead_minutes)
        )
        payload = self._build_payload(
            context=context,
            reminder_type="last_call",
            scheduled_for=scheduled_for,
            offset_minutes=config.last_call_lead_minutes,
            config=config,
        )
        return self._wrap_event(payload)

    def _build_payload(
        self,
        *,
        context: RunReminderContext,
        reminder_type: ReminderPayload.ReminderType,
        scheduled_for: datetime,
        offset_minutes: int,
        config: ChannelReminderConfig,
    ) -> ReminderPayload:
        return ReminderPayload(
            reminder_id=self._id_factory(),
            run_id=context.run_id,
            channel_id=context.channel_id,
            runner_user_id=context.runner_user_id,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            reminder_offset_minutes=offset_minutes,
            channel_reminders_enabled=config.reminders_enabled,
            last_call_enabled=config.last_call_enabled,
            correlation_id=context.correlation_id,
        )

    def _wrap_event(self, payload: ReminderPayload) -> KafkaEvent:
        return KafkaEvent(
            event_type=self._event_type,
            correlation_id=payload.correlation_id,
            payload=payload.model_dump(),
        )

    def _ensure_timezone(self, timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    def _ensure_future(self, scheduled_for: datetime) -> datetime:
        now = self._clock()
        minimum = now + timedelta(seconds=1)
        if scheduled_for < minimum:
            LOGGER.info(
                "Reminder scheduled_for adjusted to future minimum",
                extra={"original": scheduled_for.isoformat(), "adjusted": minimum.isoformat()},
            )
            return minimum
        return scheduled_for


def _get_payload_value(events: Iterable[KafkaEvent], reminder_type: str) -> str | None:
    for event in events:
        payload = event.payload
        if payload["reminder_type"] == reminder_type:
            return payload["reminder_id"]
    return None
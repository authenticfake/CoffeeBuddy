from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from coffeebuddy.jobs.reminders.scheduler import (
    ChannelReminderConfig,
    ReminderScheduler,
    RunReminderContext,
)
from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.infra.kafka.topics import REMINDER_EVENTS_TOPIC


class FakePublisher:
    def __init__(self) -> None:
        self.published: List[tuple[str, KafkaEvent]] = []

    def publish(self, *, topic: str, event: KafkaEvent) -> None:
        self.published.append((topic, event))


def _context() -> RunReminderContext:
    return RunReminderContext(
        run_id="run-123",
        channel_id="channel-uuid",
        runner_user_id="runner-uuid",
        correlation_id="corr-1",
    )


def _config() -> ChannelReminderConfig:
    return ChannelReminderConfig(
        channel_id="channel-uuid",
        reminders_enabled=True,
        reminder_offset_minutes=5,
        last_call_enabled=True,
        last_call_lead_minutes=10,
    )


def test_scheduler_emits_runner_and_last_call_events() -> None:
    clock_now = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    publisher = FakePublisher()
    scheduler = ReminderScheduler(
        publisher,
        clock=lambda: clock_now,
        id_factory=lambda: "reminder-id",
    )
    pickup_time = clock_now + timedelta(minutes=20)

    result = scheduler.schedule(context=_context(), config=_config(), pickup_time=pickup_time)

    assert result.runner_reminder_id == "reminder-id"
    assert result.last_call_reminder_id == "reminder-id"
    assert len(publisher.published) == 2
    topics = {topic for topic, _ in publisher.published}
    assert topics == {REMINDER_EVENTS_TOPIC.name}
    runner_payload = ReminderPayload.model_validate(publisher.published[0][1].payload)
    assert runner_payload.reminder_type == "runner"
    assert runner_payload.scheduled_for == pickup_time - timedelta(minutes=5)


def test_scheduler_skips_when_disabled() -> None:
    publisher = FakePublisher()
    scheduler = ReminderScheduler(publisher)
    config = ChannelReminderConfig(
        channel_id="channel",
        reminders_enabled=False,
        reminder_offset_minutes=5,
        last_call_enabled=True,
        last_call_lead_minutes=10,
    )
    pickup_time = datetime.now(timezone.utc) + timedelta(minutes=20)

    result = scheduler.schedule(context=_context(), config=config, pickup_time=pickup_time)

    assert result.runner_reminder_id is None
    assert not publisher.published


def test_scheduler_adjusts_past_schedule_to_future_minimum() -> None:
    clock_now = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    publisher = FakePublisher()
    scheduler = ReminderScheduler(
        publisher,
        clock=lambda: clock_now,
        id_factory=lambda: "runner-reminder",
    )
    pickup_time = clock_now + timedelta(minutes=2)

    scheduler.schedule(context=_context(), config=_config(), pickup_time=pickup_time)

    (_, event) = publisher.published[0]
    payload = ReminderPayload.model_validate(event.payload)
    assert payload.scheduled_for == clock_now + timedelta(seconds=1)
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.jobs.reminders.scheduler import (
    ChannelReminderConfig,
    ReminderScheduler,
    RunReminderContext,
)
from coffeebuddy.infra.kafka.topics import REMINDER_EVENTS_TOPIC


class FakePublisher:
    def __init__(self) -> None:
        self.events: List[KafkaEvent] = []

    def publish(self, *, topic: str, event: KafkaEvent) -> None:
        self.events.append(event)
        assert topic == REMINDER_EVENTS_TOPIC.name


def deserialize(payload: dict) -> ReminderPayload:
    return ReminderPayload.model_validate(payload)


def make_context(pickup_time: datetime | None = None, runner_user_id: str | None = "U01") -> RunReminderContext:
    return RunReminderContext(
        run_id="RUN123",
        channel_id="CH01",
        runner_user_id=runner_user_id,
        pickup_time=pickup_time,
        correlation_id="corr-1",
    )


def make_config(
    *,
    reminders_enabled: bool = True,
    reminder_offset_minutes: int = 5,
    last_call_enabled: bool = True,
    last_call_lead_minutes: int | None = 10,
) -> ChannelReminderConfig:
    return ChannelReminderConfig(
        channel_id="CH01",
        reminders_enabled=reminders_enabled,
        reminder_offset_minutes=reminder_offset_minutes,
        last_call_enabled=last_call_enabled,
        last_call_lead_minutes=last_call_lead_minutes,
    )


def test_schedules_runner_and_last_call_events() -> None:
    now = datetime(2024, 5, 20, 15, 0, tzinfo=timezone.utc)
    pickup = now + timedelta(minutes=20)
    publisher = FakePublisher()
    scheduler = ReminderScheduler(publisher, clock=lambda: now)

    events = scheduler.schedule_for_run(context=make_context(pickup_time=pickup), config=make_config())

    assert len(events) == 2
    runner_payload = deserialize(events[0].payload)
    last_call_payload = deserialize(events[1].payload)

    assert runner_payload.reminder_type == "runner"
    assert last_call_payload.reminder_type == "last_call"

    runner_scheduled_for = datetime.fromisoformat(runner_payload.scheduled_for.isoformat())
    last_call_scheduled_for = datetime.fromisoformat(last_call_payload.scheduled_for.isoformat())

    assert runner_scheduled_for == pickup - timedelta(minutes=5)
    assert last_call_scheduled_for == pickup - timedelta(minutes=10)


def test_runner_event_clamped_into_future_when_offset_past_now() -> None:
    now = datetime(2024, 5, 20, 15, 0, tzinfo=timezone.utc)
    pickup = now + timedelta(minutes=1)
    scheduler = ReminderScheduler(FakePublisher(), clock=lambda: now)

    events = scheduler.schedule_for_run(
        context=make_context(pickup_time=pickup),
        config=make_config(reminder_offset_minutes=5),
    )

    assert len(events) == 2
    runner_payload = deserialize(events[0].payload)
    scheduled_for = runner_payload.scheduled_for
    assert scheduled_for >= now + timedelta(seconds=5)


def test_skips_when_runner_missing() -> None:
    scheduler = ReminderScheduler(FakePublisher(), clock=lambda: datetime.now(timezone.utc))
    events = scheduler.schedule_for_run(
        context=make_context(pickup_time=datetime.now(timezone.utc) + timedelta(minutes=10), runner_user_id=None),
        config=make_config(),
    )
    assert all(deserialize(e.payload).reminder_type != "runner" for e in events)


def test_skips_entirely_when_reminders_disabled() -> None:
    scheduler = ReminderScheduler(FakePublisher())
    result = scheduler.schedule_for_run(
        context=make_context(pickup_time=datetime.now(timezone.utc) + timedelta(minutes=15)),
        config=make_config(reminders_enabled=False),
    )
    assert result == []


def test_no_last_call_when_not_enabled() -> None:
    scheduler = ReminderScheduler(FakePublisher())
    events = scheduler.schedule_for_run(
        context=make_context(pickup_time=datetime.now(timezone.utc) + timedelta(minutes=30)),
        config=make_config(last_call_enabled=False, last_call_lead_minutes=None),
    )
    assert all(deserialize(e.payload).reminder_type != "last_call" for e in events)


def test_no_scheduling_without_pickup_time() -> None:
    scheduler = ReminderScheduler(FakePublisher())
    events = scheduler.schedule_for_run(context=make_context(pickup_time=None), config=make_config())
    assert events == []
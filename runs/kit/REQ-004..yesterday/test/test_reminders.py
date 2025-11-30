from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.infra.kafka.reminder_worker import ReminderSender, ReminderWorker
from coffeebuddy.jobs.reminders.scheduler import (
    ChannelReminderConfig,
    ReminderScheduler,
)

UTC = timezone.utc


class FakeProducer:
    def __init__(self) -> None:
        self.events: List[tuple[str, KafkaEvent]] = []

    def publish(self, *, topic: str, event: KafkaEvent) -> None:
        self.events.append((topic, event))


class StubSender(ReminderSender):
    def __init__(self) -> None:
        self.runner_calls: List[ReminderPayload] = []
        self.last_call_calls: List[ReminderPayload] = []

    async def send_runner_reminder(self, payload: ReminderPayload) -> None:
        self.runner_calls.append(payload)

    async def send_last_call_reminder(self, payload: ReminderPayload) -> None:
        self.last_call_calls.append(payload)


class ManualClock:
    def __init__(self, start: datetime) -> None:
        self._current = start

    def now(self) -> datetime:
        return self._current

    def advance(self, seconds: float) -> None:
        self._current = self._current + timedelta(seconds=seconds)


class ManualSleep:
    def __init__(self, clock: ManualClock) -> None:
        self.calls: List[float] = []
        self._clock = clock

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)
        self._clock.advance(seconds)


def test_scheduler_emits_runner_and_last_call_events() -> None:
    producer = FakeProducer()
    ids = iter(["runner-rem", "last-call-rem"])
    scheduler = ReminderScheduler(producer, id_factory=lambda: next(ids))
    pickup_time = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    channel = ChannelReminderConfig(
        channel_id="C123",
        reminders_enabled=True,
        reminder_offset_minutes=5,
        last_call_enabled=True,
        last_call_lead_minutes=15,
    )

    payloads = scheduler.schedule_for_run(
        run_id="run-1",
        pickup_time=pickup_time,
        runner_user_id="U777",
        channel=channel,
        correlation_id="corr-1",
    )

    assert len(producer.events) == 2
    runner_event = producer.events[0][1]
    last_call_event = producer.events[1][1]

    assert runner_event.payload["reminder_type"] == "runner"
    assert runner_event.payload["runner_user_id"] == "U777"
    assert runner_event.payload["scheduled_for"] == (pickup_time - timedelta(minutes=5))

    assert last_call_event.payload["reminder_type"] == "last_call"
    assert last_call_event.payload["runner_user_id"] is None
    assert last_call_event.payload["scheduled_for"] == (pickup_time - timedelta(minutes=15))

    assert {p.reminder_type for p in payloads} == {"runner", "last_call"}


def test_scheduler_skips_when_channel_disabled() -> None:
    producer = FakeProducer()
    scheduler = ReminderScheduler(producer)
    pickup_time = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    channel = ChannelReminderConfig(
        channel_id="C123",
        reminders_enabled=False,
        reminder_offset_minutes=5,
        last_call_enabled=True,
        last_call_lead_minutes=10,
    )

    payloads = scheduler.schedule_for_run(
        run_id="run-1",
        pickup_time=pickup_time,
        runner_user_id="U777",
        channel=channel,
        correlation_id="corr-1",
    )

    assert payloads == []
    assert producer.events == []


@pytest.mark.asyncio
async def test_worker_waits_and_dispatches_runner_reminder() -> None:
    clock = ManualClock(datetime(2024, 1, 1, 10, 0, tzinfo=UTC))
    sleep = ManualSleep(clock)
    sender = StubSender()
    worker = ReminderWorker(
        sender,
        tolerance_seconds=60,
        clock=clock.now,
        sleep=sleep.__call__,
    )
    payload = ReminderPayload(
        reminder_id="rem-1",
        run_id="run-1",
        channel_id="C123",
        runner_user_id="U777",
        reminder_type="runner",
        scheduled_for=clock.now() + timedelta(seconds=45),
        reminder_offset_minutes=5,
        channel_reminders_enabled=True,
        last_call_enabled=False,
        correlation_id="corr-1",
    )
    event = KafkaEvent(
        event_type="reminder_scheduled",
        correlation_id="corr-1",
        payload=payload.model_dump(),
    )

    await worker.process_event(event)

    assert sender.runner_calls and sender.runner_calls[0].runner_user_id == "U777"
    assert sender.last_call_calls == []
    assert sum(sleep.calls) >= 0.0


@pytest.mark.asyncio
async def test_worker_skips_runner_when_disabled() -> None:
    clock = ManualClock(datetime(2024, 1, 1, 10, 0, tzinfo=UTC))
    sender = StubSender()
    worker = ReminderWorker(sender, clock=clock.now)
    payload = ReminderPayload(
        reminder_id="rem-1",
        run_id="run-1",
        channel_id="C123",
        runner_user_id="U777",
        reminder_type="runner",
        scheduled_for=clock.now(),
        reminder_offset_minutes=5,
        channel_reminders_enabled=False,
        last_call_enabled=False,
        correlation_id="corr-1",
    )
    event = KafkaEvent(
        event_type="reminder_scheduled",
        correlation_id="corr-1",
        payload=payload.model_dump(),
    )

    await worker.process_event(event)

    assert sender.runner_calls == []
    assert sender.last_call_calls == []
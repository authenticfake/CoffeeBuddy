from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.jobs.reminders.worker import ReminderWorker


class StubCounter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def labels(self, *, reminder_type: str, status: str):  # type: ignore[override]
        self.calls.append((reminder_type, status))
        return self

    def inc(self) -> None:
        pass


class StubHistogram:
    def __init__(self) -> None:
        self.observations: list[float] = []

    def observe(self, value: float) -> None:  # type: ignore[override]
        self.observations.append(value)


class FakeSender:
    def __init__(self) -> None:
        self.runner_payloads: list[ReminderPayload] = []
        self.last_call_payloads: list[ReminderPayload] = []

    async def send_runner_reminder(self, payload: ReminderPayload) -> None:
        self.runner_payloads.append(payload)

    async def send_last_call_reminder(self, payload: ReminderPayload) -> None:
        self.last_call_payloads.append(payload)


class ManualClock:
    def __init__(self, start: datetime) -> None:
        self._current = start

    def now(self) -> datetime:
        return self._current

    async def sleep(self, seconds: float) -> None:
        self._current += timedelta(seconds=seconds)


def _event(payload: ReminderPayload) -> KafkaEvent:
    return KafkaEvent(event_type="reminder_scheduled", correlation_id="corr", payload=payload.model_dump())


@pytest.mark.asyncio
async def test_worker_waits_until_within_tolerance(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    clock = ManualClock(now)
    sender = FakeSender()
    worker = ReminderWorker(sender, tolerance_seconds=30, clock=clock.now, sleep=clock.sleep)

    payload = ReminderPayload(
        reminder_id="runner-1",
        run_id="run",
        channel_id="channel",
        runner_user_id="runner",
        reminder_type="runner",
        scheduled_for=now + timedelta(minutes=2),
        reminder_offset_minutes=5,
        channel_reminders_enabled=True,
        last_call_enabled=True,
        correlation_id="corr",
    )
    histogram = StubHistogram()
    counter = StubCounter()
    monkeypatch.setattr("coffeebuddy.jobs.reminders.worker.REMINDER_DELAY_SECONDS", histogram)
    monkeypatch.setattr("coffeebuddy.jobs.reminders.worker.REMINDER_SEND_TOTAL", counter)

    await worker.process_event(_event(payload))

    assert sender.runner_payloads
    assert histogram.observations[-1] >= 0
    assert ("runner", "sent") in counter.calls


@pytest.mark.asyncio
async def test_worker_skips_when_channel_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(timezone.utc)
    sender = FakeSender()
    worker = ReminderWorker(sender, clock=lambda: now, sleep=asyncio.sleep)
    payload = ReminderPayload(
        reminder_id="runner-1",
        run_id="run",
        channel_id="channel",
        runner_user_id="runner",
        reminder_type="runner",
        scheduled_for=now,
        reminder_offset_minutes=5,
        channel_reminders_enabled=False,
        last_call_enabled=True,
        correlation_id="corr",
    )
    histogram = StubHistogram()
    counter = StubCounter()
    monkeypatch.setattr("coffeebuddy.jobs.reminders.worker.REMINDER_DELAY_SECONDS", histogram)
    monkeypatch.setattr("coffeebuddy.jobs.reminders.worker.REMINDER_SEND_TOTAL", counter)

    await worker.process_event(_event(payload))

    assert not sender.runner_payloads
    assert not histogram.observations
    assert not counter.calls


@pytest.mark.asyncio
async def test_worker_dispatches_last_call(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(timezone.utc)
    sender = FakeSender()
    worker = ReminderWorker(sender, clock=lambda: now, sleep=asyncio.sleep)
    payload = ReminderPayload(
        reminder_id="last-call-1",
        run_id="run",
        channel_id="channel",
        runner_user_id=None,
        reminder_type="last_call",
        scheduled_for=now,
        reminder_offset_minutes=10,
        channel_reminders_enabled=True,
        last_call_enabled=True,
        correlation_id="corr",
    )
    histogram = StubHistogram()
    counter = StubCounter()
    monkeypatch.setattr("coffeebuddy.jobs.reminders.worker.REMINDER_DELAY_SECONDS", histogram)
    monkeypatch.setattr("coffeebuddy.jobs.reminders.worker.REMINDER_SEND_TOTAL", counter)

    await worker.process_event(_event(payload))

    assert sender.last_call_payloads
    assert ("last_call", "sent") in counter.calls
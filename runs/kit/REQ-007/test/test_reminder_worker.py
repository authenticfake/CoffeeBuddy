from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.infra.kafka.reminder_worker import ReminderWorker


@pytest.mark.asyncio
async def test_runner_reminder_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = AsyncMock()
    worker = ReminderWorker(sender, clock=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc))
    payload = ReminderPayload(
        reminder_id="rem-1",
        run_id="run-1",
        channel_id="chan-1",
        runner_user_id="user-1",
        reminder_type="runner",
        scheduled_for=datetime(2024, 1, 1, tzinfo=timezone.utc),
        reminder_offset_minutes=5,
        channel_reminders_enabled=False,
    )
    event = KafkaEvent(event_type="reminder_due", correlation_id="corr", payload=payload.model_dump())
    await worker.process_event(event)
    sender.send_runner_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_last_call_reminder_invokes_sender(monkeypatch: pytest.MonkeyPatch) -> None:
    sender = AsyncMock()
    worker = ReminderWorker(sender, clock=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc))
    payload = ReminderPayload(
        reminder_id="rem-2",
        run_id="run-1",
        channel_id="chan-1",
        runner_user_id=None,
        reminder_type="last_call",
        scheduled_for=datetime(2024, 1, 1, tzinfo=timezone.utc),
        reminder_offset_minutes=10,
        channel_reminders_enabled=True,
        last_call_enabled=True,
    )
    event = KafkaEvent(event_type="reminder_due", correlation_id="corr", payload=payload.model_dump())
    await worker.process_event(event)
    sender.send_last_call_reminder.assert_awaited_once()
from __future__ import annotations

import asyncio
from typing import Any, List

import pytest

from coffeebuddy.infra.kafka.models import ReminderPayload
from coffeebuddy.jobs.reminders.sender import SlackReminderSender
from coffeebuddy.jobs.reminders.messages import ReminderMessageBuilder


class FakeDMClient:
    def __init__(self) -> None:
        self.calls: List[dict[str, Any]] = []

    async def send_dm(self, *, user_id: str, text: str, blocks: list[dict[str, Any]] | None = None) -> None:
        self.calls.append({"user_id": user_id, "text": text, "blocks": blocks})


class FakeChannelMessenger:
    def __init__(self) -> None:
        self.calls: List[dict[str, Any]] = []

    async def post_message(self, *, channel_id: str, text: str, blocks: list[dict[str, Any]] | None = None) -> None:
        self.calls.append({"channel_id": channel_id, "text": text, "blocks": blocks})


@pytest.mark.asyncio
async def test_runner_reminder_sends_dm() -> None:
    sender = SlackReminderSender(
        dm_client=FakeDMClient(),
        channel_messenger=FakeChannelMessenger(),
        message_builder=ReminderMessageBuilder(),
    )
    payload = ReminderPayload(
        reminder_id="rem-1",
        run_id="run-1",
        channel_id="CH01",
        runner_user_id="U01",
        reminder_type="runner",
        scheduled_for=ReminderMessageBuilder()._format_time.__self__ if False else asyncio.get_event_loop().time  # type: ignore[assignment]
    )
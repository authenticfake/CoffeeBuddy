from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

import pytest

from coffeebuddy.infra.kafka.models import ReminderPayload
from coffeebuddy.jobs.reminders.sender import (
    ChannelContact,
    ReminderContextResolver,
    ReminderDispatchError,
    RunnerContact,
    SlackReminderMessenger,
    SlackReminderSender,
)


class FakeMessenger(SlackReminderMessenger):
    def __init__(self) -> None:
        self.dms: list[tuple[str, str, List[dict[str, Any]]]] = []
        self.messages: list[tuple[str, str, List[dict[str, Any]]]] = []

    async def send_dm(self, slack_user_id: str, *, text: str, blocks: List[dict[str, Any]]) -> None:
        self.dms.append((slack_user_id, text, blocks))

    async def post_channel_message(
        self, slack_channel_id: str, *, text: str, blocks: List[dict[str, Any]]
    ) -> None:
        self.messages.append((slack_channel_id, text, blocks))


class FakeResolver(ReminderContextResolver):
    def __init__(self) -> None:
        self.runner: Optional[RunnerContact] = RunnerContact(
            user_id="runner",
            slack_user_id="U123",
            display_name="Alex Runner",
        )
        self.channel: Optional[ChannelContact] = ChannelContact(
            channel_id="channel",
            slack_channel_id="C123",
            name="coffee-buddies",
        )

    def get_runner_contact(self, user_id: str | None) -> RunnerContact | None:
        if user_id != "runner":
            return None
        return self.runner

    def get_channel_contact(self, channel_id: str) -> ChannelContact | None:
        if channel_id != "channel":
            return None
        return self.channel


def _payload(reminder_type: str) -> ReminderPayload:
    return ReminderPayload(
        reminder_id="rem-1",
        run_id="run-1",
        channel_id="channel",
        runner_user_id="runner",
        reminder_type=reminder_type,
        scheduled_for=datetime.now(timezone.utc),
        reminder_offset_minutes=5,
        channel_reminders_enabled=True,
        last_call_enabled=True,
        correlation_id="corr",
    )


@pytest.mark.asyncio
async def test_slack_sender_dispatches_runner_dm() -> None:
    messenger = FakeMessenger()
    sender = SlackReminderSender(messenger, resolver=FakeResolver())

    await sender.send_runner_reminder(_payload("runner"))

    assert messenger.dms
    user_id, text, blocks = messenger.dms[0]
    assert user_id == "U123"
    assert "CoffeeBuddy reminder" in text
    assert blocks[0]["type"] == "section"


@pytest.mark.asyncio
async def test_slack_sender_dispatches_last_call_message() -> None:
    messenger = FakeMessenger()
    sender = SlackReminderSender(messenger, resolver=FakeResolver())

    await sender.send_last_call_reminder(_payload("last_call"))

    assert messenger.messages
    channel_id, text, blocks = messenger.messages[0]
    assert channel_id == "C123"
    assert "last call" in text.lower()
    assert blocks[0]["type"] == "section"


@pytest.mark.asyncio
async def test_slack_sender_raises_when_contact_missing() -> None:
    messenger = FakeMessenger()
    resolver = FakeResolver()
    resolver.runner = None
    sender = SlackReminderSender(messenger, resolver=resolver)

    with pytest.raises(ReminderDispatchError):
        await sender.send_runner_reminder(_payload("runner"))
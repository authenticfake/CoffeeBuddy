from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Protocol

from .metrics import REMINDER_DELAY_SECONDS, REMINDER_SEND_TOTAL
from .models import KafkaEvent, ReminderPayload, ReminderType

logger = logging.getLogger(__name__)

SleepFn = Callable[[float], Awaitable[None]]


class ReminderSender(Protocol):
    """Abstraction for delivering reminders via Slack or other transports."""

    async def send_runner_reminder(self, payload: ReminderPayload) -> None: ...

    async def send_last_call_reminder(self, payload: ReminderPayload) -> None: ...


class ReminderWorker:
    """Reminder worker harness composable with KafkaEventConsumer."""

    def __init__(
        self,
        sender: ReminderSender,
        *,
        tolerance_seconds: int = 60,
        clock: Callable[[], datetime] | None = None,
        sleep: SleepFn | None = None,
    ) -> None:
        self._sender = sender
        self._tolerance_seconds = tolerance_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._sleep = sleep or asyncio.sleep

    async def process_event(self, event: KafkaEvent) -> None:
        payload = ReminderPayload.model_validate(event.payload)
        reminder_type = payload.reminder_type
        if not self._should_dispatch(payload):
            REMINDER_SEND_TOTAL.labels(reminder_type=reminder_type, status="skipped").inc()
            logger.info(
                "Skipping reminder %s (type=%s) due to channel settings.",
                payload.reminder_id,
                reminder_type,
                extra={"reminder_id": payload.reminder_id, "reminder_type": reminder_type},
            )
            return

        await self._wait_until(payload.scheduled_for, payload)

        send_fn = (
            self._sender.send_runner_reminder
            if reminder_type == "runner"
            else self._sender.send_last_call_reminder
        )

        try:
            await send_fn(payload)
            REMINDER_SEND_TOTAL.labels(reminder_type=reminder_type, status="sent").inc()
            REMINDER_DELAY_SECONDS.observe(
                abs((self._clock() - payload.scheduled_for).total_seconds())
            )
            logger.info(
                "Reminder dispatched",
                extra={"reminder_id": payload.reminder_id, "reminder_type": reminder_type},
            )
        except Exception:
            REMINDER_SEND_TOTAL.labels(reminder_type=reminder_type, status="error").inc()
            logger.exception(
                "Failed to dispatch reminder",
                extra={"reminder_id": payload.reminder_id, "reminder_type": reminder_type},
            )
            raise

    def _should_dispatch(self, payload: ReminderPayload) -> bool:
        if not payload.channel_reminders_enabled:
            return False
        if payload.reminder_type == "runner":
            return payload.runner_user_id is not None
        if payload.reminder_type == "last_call":
            return payload.last_call_enabled
        return False

    async def _wait_until(self, scheduled_for: datetime, payload: ReminderPayload) -> None:
        target = (
            scheduled_for
            if scheduled_for.tzinfo
            else scheduled_for.replace(tzinfo=timezone.utc)
        )
        while True:
            now = self._clock()
            delay = (target - now).total_seconds()
            if delay <= 0:
                if abs(delay) > self._tolerance_seconds:
                    logger.warning(
                        "Reminder %s is late by %.2fs.",
                        payload.reminder_id,
                        abs(delay),
                    )
                return
            await self._sleep(delay if delay <= self._tolerance_seconds else delay - self._tolerance_seconds)
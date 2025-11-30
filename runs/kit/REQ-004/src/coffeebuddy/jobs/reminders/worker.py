from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable

from coffeebuddy.infra.kafka.metrics import REMINDER_DELAY_SECONDS, REMINDER_SEND_TOTAL
from coffeebuddy.infra.kafka.models import KafkaEvent, ReminderPayload
from coffeebuddy.infra.kafka.reminder_worker import ReminderSender

LOGGER = logging.getLogger(__name__)

Clock = Callable[[], datetime]
SleepFn = Callable[[float], Awaitable[None]]


class ReminderWorker:
    """Processes reminder events and dispatches Slack notifications."""

    def __init__(
        self,
        sender: ReminderSender,
        *,
        tolerance_seconds: int = 60,
        clock: Clock | None = None,
        sleep: SleepFn | None = None,
    ) -> None:
        self._sender = sender
        self._tolerance_seconds = tolerance_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._sleep = sleep or asyncio.sleep

    async def process_event(self, event: KafkaEvent) -> None:
        payload = ReminderPayload.model_validate(event.payload)
        if not self._should_process(payload):
            return
        await self._await_within_tolerance(payload.scheduled_for)
        await self._dispatch(payload)

    def _should_process(self, payload: ReminderPayload) -> bool:
        if not payload.channel_reminders_enabled:
            LOGGER.info(
                "Reminder skipped because channel disabled reminders",
                extra={"run_id": payload.run_id, "reminder_id": payload.reminder_id},
            )
            return False
        if payload.reminder_type == "runner" and payload.runner_user_id is None:
            LOGGER.warning(
                "Runner reminder skipped due to missing runner",
                extra={"run_id": payload.run_id, "reminder_id": payload.reminder_id},
            )
            return False
        if payload.reminder_type == "last_call" and not payload.last_call_enabled:
            LOGGER.debug(
                "Last call reminder skipped because feature disabled",
                extra={"run_id": payload.run_id, "reminder_id": payload.reminder_id},
            )
            return False
        return True

    async def _await_within_tolerance(self, scheduled_for: datetime) -> None:
        while True:
            now = self._clock()
            delta = (scheduled_for - now).total_seconds()
            if delta <= self._tolerance_seconds:
                return
            await self._sleep(delta - self._tolerance_seconds)

    async def _dispatch(self, payload: ReminderPayload) -> None:
        reminder_type = payload.reminder_type
        try:
            if reminder_type == "runner":
                await self._sender.send_runner_reminder(payload)
            else:
                await self._sender.send_last_call_reminder(payload)
            REMINDER_SEND_TOTAL.labels(reminder_type=reminder_type, status="sent").inc()
        except Exception:
            REMINDER_SEND_TOTAL.labels(reminder_type=reminder_type, status="error").inc()
            LOGGER.exception(
                "Reminder dispatch failed",
                extra={"reminder_id": payload.reminder_id, "reminder_type": reminder_type},
            )
            raise

        actual_delay = abs((self._clock() - payload.scheduled_for).total_seconds())
        REMINDER_DELAY_SECONDS.observe(actual_delay)
        LOGGER.info(
            "Reminder dispatched",
            extra={
                "reminder_id": payload.reminder_id,
                "reminder_type": reminder_type,
                "delay_seconds": actual_delay,
            },
        )
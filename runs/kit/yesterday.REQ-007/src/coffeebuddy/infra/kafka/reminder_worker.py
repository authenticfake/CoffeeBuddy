from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Protocol

from .metrics import REMINDER_DELAY_SECONDS, REMINDER_SEND_TOTAL
from .models import KafkaEvent, ReminderPayload, ReminderType

logger = logging.getLogger(__name__)


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
        clock: callable[[], datetime] | None = None,
    ) -> None:
        self._sender = sender
        self._tolerance_seconds = tolerance_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def process_event(self, event: KafkaEvent) -> None:
        payload = ReminderPayload.model_validate(event.payload)
        scheduled_for = payload.scheduled_for
        now = self._clock()
        delay = abs((now - scheduled_for).total_seconds())
        REMINDER_DELAY_SECONDS.observe(delay)
        payload_message = payload.model_dump()

        logger.debug(
            "Processing reminder event",
            extra={
                "reminder_id": payload.reminder_id,
                "reminder_type": payload.reminder_type,
                "delay_seconds": delay,
            },
        )

        if payload.reminder_type == "runner":
            if not payload.channel_reminders_enabled:
                REMINDER_SEND_TOTAL.labels(reminder_type="runner", status="skipped_disabled").inc()
                logger.info(
                    "Runner reminder skipped; channel disabled reminders.",
                    extra=payload_message,
                )
                return
            await self._dispatch(self._sender.send_runner_reminder, payload, ReminderType("runner"))
        else:
            if not payload.last_call_enabled:
                REMINDER_SEND_TOTAL.labels(reminder_type="last_call", status="skipped_disabled").inc()
                logger.info(
                    "Last call reminder skipped; feature disabled.",
                    extra=payload_message,
                )
                return
            await self._dispatch(self._sender.send_last_call_reminder, payload, ReminderType("last_call"))

    async def _dispatch(
        self,
        action: callable[[ReminderPayload], asyncio.Future | None | asyncio.Task],
        payload: ReminderPayload,
        reminder_type: ReminderType,
    ) -> None:
        try:
            await action(payload)
            REMINDER_SEND_TOTAL.labels(reminder_type=reminder_type, status="sent").inc()
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
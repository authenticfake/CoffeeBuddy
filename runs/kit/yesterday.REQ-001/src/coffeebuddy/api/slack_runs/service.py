from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from coffeebuddy.api.slack_runs.messages import SlackMessageBuilder
from coffeebuddy.api.slack_runs.models import RunCommandOptions, SlackCommandPayload
from coffeebuddy.events.run import RunCreatedEvent, RunEventPublisher
from coffeebuddy.models.run import Run


class SlackRunCommandService:
    """Coordinates slash command handling, persistence, and event emission."""

    def __init__(
        self,
        *,
        session: Session,
        event_publisher: RunEventPublisher,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._event_publisher = event_publisher
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def handle(self, command: SlackCommandPayload, options: RunCommandOptions) -> dict:
        now = self._clock()

        run = Run(
            id=str(uuid4()),
            channel_id=command.channel_id,
            initiator_user_id=command.user_id,
            status="open",
            pickup_time=options.pickup_time,
            pickup_note=options.pickup_note,
            correlation_id=str(uuid4()),
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        self._session.add(run)
        self._session.flush()

        event = RunCreatedEvent(
            run_id=run.id,
            channel_id=run.channel_id,
            initiator_user_id=run.initiator_user_id,
            pickup_time=run.pickup_time.isoformat() if run.pickup_time else None,
            pickup_note=run.pickup_note,
            correlation_id=run.correlation_id,
            created_at=run.started_at.isoformat(),
        )
        self._event_publisher.publish_run_created(event)

        return SlackMessageBuilder.build_run_created(run)
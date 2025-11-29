from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from coffeebuddy.core.orders.models import Clock
from coffeebuddy.core.runs.exceptions import (
    RunNotFoundError,
    RunNotOpenError,
    RunnerSelectionError,
    UnauthorizedRunCloseError,
)
from coffeebuddy.core.runs.models import (
    CloseRunRequest,
    CloseRunResult,
    ParticipantOrder,
    RunSummary,
)
from coffeebuddy.infra.db.models import Channel, Order, Run, RunStatus, User
from coffeebuddy.services.fairness.service import FairnessService


class CloseRunAuthorizer(Protocol):
    """Adapter used to verify whether an actor can close a given run."""

    def is_authorized(self, *, run: Run, actor_user_id: str) -> bool:
        """Return True when the actor can close the run."""


class CloseRunService:
    """Coordinates validation, fairness, and summary generation for run closing."""

    def __init__(
        self,
        *,
        session: Session,
        fairness: FairnessService,
        authorizer: CloseRunAuthorizer,
        clock: Clock | None = None,
    ) -> None:
        self._session = session
        self._fairness = fairness
        self._authorizer = authorizer
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def close_run(self, request: CloseRunRequest) -> CloseRunResult:
        run = self._get_run(request.run_id)
        if run.status != RunStatus.OPEN:
            raise RunNotOpenError(f"Run {request.run_id} is not open.")
        if not self._authorizer.is_authorized(run=run, actor_user_id=request.actor_user_id):
            raise UnauthorizedRunCloseError(
                f"Actor {request.actor_user_id} is not allowed to close run {request.run_id}."
            )

        channel = self._get_channel(run.channel_id)
        orders = self._load_active_orders(run.id)
        if not orders:
            raise RunnerSelectionError("Cannot close run without active participant orders.")

        last_runner_id = self._get_previous_runner_id(run)
        decision = self._fairness.assign_runner(
            channel_id=str(channel.id),
            participant_user_ids=[str(order.user_id) for order, _ in orders],
            last_runner_id=last_runner_id,
            allow_immediate_repeat=request.allow_immediate_repeat,
        )

        runner_uuid = _as_uuid(decision.runner_user_id)
        runner = self._session.get(User, runner_uuid)
        if runner is None:
            raise RunnerSelectionError(
                f"Runner {decision.runner_user_id} missing from persistence during close."
            )

        now = self._clock()
        self._finalize_run(run=run, runner_id=runner_uuid, closed_at=now)
        participants = self._snapshot_orders(orders=orders, snapshot_at=now)

        summary = RunSummary(
            run_id=str(run.id),
            channel_id=str(channel.id),
            channel_name=channel.name,
            runner_user_id=decision.runner_user_id,
            runner_display_name=runner.display_name,
            pickup_time=run.pickup_time,
            pickup_note=run.pickup_note,
            participants=tuple(participants),
            total_orders=len(participants),
            reminder_offset_minutes=channel.reminder_offset_minutes,
            reminders_enabled=channel.reminders_enabled,
            last_call_enabled=channel.last_call_enabled,
            closed_at=now,
        )

        return CloseRunResult(
            run_id=str(run.id),
            channel_id=str(channel.id),
            runner_user_id=decision.runner_user_id,
            closed_at=now,
            summary=summary,
            fairness_note=decision.rationale,
        )

    def _get_run(self, run_id: str) -> Run:
        run = self._session.get(Run, _as_uuid(run_id))
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found.")
        return run

    def _get_channel(self, channel_id: UUID) -> Channel:
        channel = self._session.get(Channel, channel_id)
        if channel is None:
            raise RunNotFoundError(f"Channel {channel_id} missing for run close.")
        return channel

    def _load_active_orders(self, run_id: UUID) -> list[tuple[Order, User]]:
        stmt = (
            select(Order, User)
            .join(User, User.id == Order.user_id)
            .where(
                Order.run_id == run_id,
                Order.canceled_at.is_(None),
            )
            .order_by(User.display_name.asc(), User.id.asc())
        )
        rows = self._session.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]

    def _snapshot_orders(
        self, *, orders: list[tuple[Order, User]], snapshot_at: datetime
    ) -> list[ParticipantOrder]:
        participants: list[ParticipantOrder] = []
        for order, user in orders:
            order.is_final = True
            order.updated_at = snapshot_at
            participants.append(
                ParticipantOrder(
                    user_id=str(order.user_id),
                    display_name=user.display_name,
                    order_text=order.order_text,
                    provenance=order.provenance,
                )
            )
        return participants

    def _finalize_run(self, *, run: Run, runner_id: UUID, closed_at: datetime) -> None:
        run.runner_user_id = runner_id
        run.status = RunStatus.CLOSED
        run.closed_at = closed_at
        run.updated_at = closed_at

    def _get_previous_runner_id(self, run: Run) -> str | None:
        stmt = (
            select(Run.runner_user_id)
            .where(
                Run.channel_id == run.channel_id,
                Run.status == RunStatus.CLOSED,
                Run.closed_at.is_not(None),
                Run.id != run.id,
                Run.runner_user_id.is_not(None),
            )
            .order_by(Run.closed_at.desc())
            .limit(1)
        )
        result = self._session.scalars(stmt).first()
        return str(result) if result else None


def _as_uuid(value: str | UUID) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(value)
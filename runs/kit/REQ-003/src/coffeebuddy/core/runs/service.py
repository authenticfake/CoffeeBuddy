from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, Sequence
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from coffeebuddy.core.runs import exceptions as run_exc
from coffeebuddy.core.runs.models import (
    CloseRunRequest,
    CloseRunResult,
    OrderSnapshot,
    RunnerSnapshot,
    RunSummary,
)
from coffeebuddy.core.runs.summary import RunSummaryBuilder
from coffeebuddy.infra.db.models import (
    Channel,
    Order,
    Run,
    RunStatus,
    RunnerStat,
    User,
)
from coffeebuddy.infra.kafka.models import KafkaEvent
from coffeebuddy.infra.kafka.topics import RUN_EVENTS_TOPIC
from coffeebuddy.services.fairness import FairnessSelector, RunnerSelection


class RunCloseAuthorizer(Protocol):
    """Run close authorization contract."""

    def assert_can_close(self, *, run: Run, actor_user_id: str) -> None: ...


class RunEventPublisher(Protocol):
    """Abstraction for publishing Kafka events."""

    def publish(self, *, topic: str, event: KafkaEvent) -> None: ...


class CloseRunService:
    """Coordinates the close → assign runner → summarize flow."""

    def __init__(
        self,
        session: Session,
        fairness_selector: FairnessSelector,
        summary_builder: RunSummaryBuilder,
        authorizer: RunCloseAuthorizer,
        publisher: RunEventPublisher,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        from typing import Callable

        self._session = session
        self._fairness_selector = fairness_selector
        self._summary_builder = summary_builder
        self._authorizer = authorizer
        self._publisher = publisher
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def close_run(self, request: CloseRunRequest) -> CloseRunResult:
        run, channel = self._load_run_for_update(run_id=request.run_id)
        if channel.enabled is False:
            raise run_exc.ChannelDisabledError(
                f"Channel {channel.id} is disabled; run cannot be closed."
            )
        if run.status != RunStatus.OPEN:
            raise run_exc.RunAlreadyClosedError(f"Run {run.id} is not open.")

        self._authorizer.assert_can_close(run=run, actor_user_id=request.actor_user_id)

        order_snapshots = self._collect_active_orders(run_id=run.id)
        if not order_snapshots:
            raise run_exc.NoEligibleRunnerError(
                f"No eligible participants for run {run.id}"
            )

        candidate_user_ids = tuple({order.user_id for order in order_snapshots})
        selection = self._select_runner(
            run=run,
            channel=channel,
            candidates=candidate_user_ids,
            allow_repeat=request.allow_consecutive_runner,
        )

        runner_user = self._session.get(User, selection.runner_user_id)
        if runner_user is None:
            raise run_exc.RunNotFoundError(
                f"Runner {selection.runner_user_id} could not be resolved."
            )

        now = self._clock()
        self._finalize_run(
            run=run,
            runner_user_id=selection.runner_user_id,
            closed_at=now,
            orders=order_snapshots,
        )
        self._update_runner_stats(
            channel_id=channel.id,
            runner_user_id=selection.runner_user_id,
            served_at=now,
        )

        summary = self._build_summary(
            run=run,
            channel=channel,
            runner=runner_user,
            orders=order_snapshots,
            fairness_explanation=selection.explanation,
        )

        event_names = self._emit_events(
            run=run,
            channel=channel,
            runner=runner_user,
            participant_count=len(order_snapshots),
            correlation_id=request.correlation_id,
            fairness_explanation=selection.explanation,
        )

        self._session.commit()

        return CloseRunResult(
            run_id=str(run.id),
            runner_user_id=selection.runner_user_id,
            summary=summary,
            events_emitted=event_names,
        )

    # --- internal helpers -------------------------------------------------

    def _load_run_for_update(self, *, run_id: str) -> tuple[Run, Channel]:
        query: Select[tuple[Run, Channel]] = (
            select(Run, Channel)
            .join(Channel, Channel.id == Run.channel_id)
            .where(Run.id == run_id)
            .with_for_update()
        )
        row = self._session.execute(query).one_or_none()
        if row is None:
            raise run_exc.RunNotFoundError(f"Run {run_id} not found.")
        return row

    def _collect_active_orders(self, *, run_id: str) -> list[OrderSnapshot]:
        query: Select[tuple[Order, User]] = (
            select(Order, User)
            .join(User, User.id == Order.user_id)
            .where(Order.run_id == run_id, Order.canceled_at.is_(None))
            .order_by(Order.created_at)
        )
        rows = self._session.execute(query).all()

        snapshots: list[OrderSnapshot] = []
        for order, user in rows:
            order.is_final = True
            snapshots.append(
                OrderSnapshot(
                    order_id=str(order.id),
                    user_id=str(user.id),
                    slack_user_id=user.slack_user_id,
                    display_name=user.display_name,
                    order_text=order.order_text,
                    provenance=order.provenance,
                    submitted_at=order.updated_at or order.created_at,
                    confirmed=order.is_final,
                )
            )
        return snapshots

    def _select_runner(
        self,
        *,
        run: Run,
        channel: Channel,
        candidates: Sequence[str],
        allow_repeat: bool,
    ) -> RunnerSelection:
        return self._fairness_selector.select_runner(
            channel_id=str(channel.id),
            candidate_user_ids=candidates,
            fairness_window_runs=channel.fairness_window_runs,
            allow_immediate_repeat=allow_repeat,
        )

    def _finalize_run(
        self,
        *,
        run: Run,
        runner_user_id: str,
        closed_at: datetime,
        orders: Sequence[OrderSnapshot],
    ) -> None:
        run.runner_user_id = runner_user_id
        run.status = RunStatus.CLOSED
        run.closed_at = closed_at
        run.updated_at = closed_at
        for snapshot in orders:
            # Order rows are already marked final in _collect_active_orders; flush ensures persistence.
            self._touch_order(snapshot_id=snapshot.order_id, closed_at=closed_at)

    def _touch_order(self, *, snapshot_id: str, closed_at: datetime) -> None:
        order = self._session.get(Order, snapshot_id)
        if order is None:
            return
        order.is_final = True
        order.updated_at = closed_at

    def _update_runner_stats(
        self, *, channel_id: str, runner_user_id: str, served_at: datetime
    ) -> None:
        stat = (
            self._session.execute(
                select(RunnerStat)
                .where(
                    RunnerStat.channel_id == channel_id,
                    RunnerStat.user_id == runner_user_id,
                )
                .with_for_update()
            )
            .scalars()
            .one_or_none()
        )

        if stat is None:
            stat = RunnerStat(
                id=uuid4(),
                channel_id=channel_id,
                user_id=runner_user_id,
                runs_served_count=0,
            )
            self._session.add(stat)

        stat.runs_served_count += 1
        stat.last_run_at = served_at
        stat.updated_at = served_at

    def _build_summary(
        self,
        *,
        run: Run,
        channel: Channel,
        runner: User,
        orders: Sequence[OrderSnapshot],
        fairness_explanation: str,
    ) -> RunSummary:
        runner_snapshot = RunnerSnapshot(
            user_id=str(runner.id),
            slack_user_id=runner.slack_user_id,
            display_name=runner.display_name,
        )
        return self._summary_builder.build(
            run_id=str(run.id),
            channel_id=str(channel.id),
            channel_name=channel.name,
            pickup_time=run.pickup_time,
            pickup_note=run.pickup_note,
            runner=runner_snapshot,
            participant_orders=orders,
            reminder_offset_minutes=channel.reminder_offset_minutes,
            fairness_explanation=fairness_explanation,
        )

    def _emit_events(
        self,
        *,
        run: Run,
        channel: Channel,
        runner: User,
        participant_count: int,
        correlation_id: str,
        fairness_explanation: str,
    ) -> list[str]:
        event_names: list[str] = []
        closed_event = KafkaEvent(
            event_type="run_closed",
            correlation_id=correlation_id,
            payload={
                "run_id": str(run.id),
                "channel_id": str(channel.id),
                "runner_user_id": str(runner.id),
                "participant_count": participant_count,
                "closed_at": run.closed_at.isoformat(),
            },
        )
        runner_event = KafkaEvent(
            event_type="runner_assigned",
            correlation_id=correlation_id,
            payload={
                "run_id": str(run.id),
                "channel_id": str(channel.id),
                "runner_user_id": str(runner.id),
                "explanation": fairness_explanation,
            },
        )
        for event in (closed_event, runner_event):
            self._publisher.publish(topic=RUN_EVENTS_TOPIC.name, event=event)
            event_names.append(event.event_type)
        return event_names
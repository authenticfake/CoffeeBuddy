from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Channel,
    ChannelAdminAction,
    Order,
    RunnerStat,
    Run,
    RunStatus,
    User,
    UserPreference,
)

UTC = timezone.utc


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, *, slack_user_id: str, display_name: str) -> User:
        user = (
            self._session.execute(
                select(User).where(User.slack_user_id == slack_user_id)
            ).scalar_one_or_none()
        )
        now = _utcnow()
        if user:
            if user.display_name != display_name:
                user.display_name = display_name
                user.updated_at = now
            return user
        user = User(slack_user_id=slack_user_id, display_name=display_name)
        user.created_at = now
        user.updated_at = now
        self._session.add(user)
        return user


@dataclass(frozen=True)
class ChannelSettingsPatch:
    reminder_offset_minutes: int | None = None
    fairness_window_runs: int | None = None
    data_retention_days: int | None = None
    reminders_enabled: bool | None = None
    last_call_enabled: bool | None = None
    last_call_lead_minutes: int | None = None
    enabled: bool | None = None


class ChannelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_slack_id(self, slack_channel_id: str) -> Channel | None:
        return (
            self._session.execute(
                select(Channel).where(Channel.slack_channel_id == slack_channel_id)
            ).scalar_one_or_none()
        )

    def upsert(self, *, slack_channel_id: str, name: str) -> Channel:
        channel = self.get_by_slack_id(slack_channel_id)
        now = _utcnow()
        if channel:
            if channel.name != name:
                channel.name = name
                channel.updated_at = now
            return channel
        channel = Channel(slack_channel_id=slack_channel_id, name=name)
        channel.created_at = now
        channel.updated_at = now
        self._session.add(channel)
        return channel

    def update_settings(self, channel: Channel, patch: ChannelSettingsPatch) -> Channel:
        need_update = False
        now = _utcnow()
        for field, value in patch.__dict__.items():
            if value is None:
                continue
            setattr(channel, field, value)
            need_update = True
        if need_update:
            channel.updated_at = now
        return channel


class RunRepository:
    _valid_transitions: dict[str, set[str]] = {
        RunStatus.OPEN.value: {
            RunStatus.CLOSED.value,
            RunStatus.CANCELED.value,
            RunStatus.FAILED.value,
        },
        RunStatus.CLOSED.value: set(),
        RunStatus.CANCELED.value: set(),
        RunStatus.FAILED.value: set(),
    }

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        channel_id: str,
        initiator_user_id: str,
        pickup_time: datetime | None,
        pickup_note: str | None,
    ) -> Run:
        run = Run(
            channel_id=channel_id,
            initiator_user_id=initiator_user_id,
            pickup_time=pickup_time,
            pickup_note=pickup_note,
            status=RunStatus.OPEN.value,
        )
        run.started_at = _utcnow()
        run.created_at = run.started_at
        run.updated_at = run.started_at
        self._session.add(run)
        return run

    def get_latest_for_channel(self, channel_id: str) -> Run | None:
        return (
            self._session.execute(
                select(Run)
                .where(Run.channel_id == channel_id)
                .order_by(Run.started_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        )

    def list_by_status(self, channel_id: str, status: RunStatus) -> Sequence[Run]:
        return (
            self._session.execute(
                select(Run).where(Run.channel_id == channel_id, Run.status == status.value)
            )
            .scalars()
            .all()
        )

    def update_status(self, run: Run, new_status: RunStatus) -> Run:
        current = run.status
        if current == new_status.value:
            return run
        allowed = self._valid_transitions.get(current, set())
        if new_status.value not in allowed:
            raise ValueError(
                f"Invalid run status transition: {current} -> {new_status.value}"
            )
        now = _utcnow()
        run.status = new_status.value
        run.updated_at = now
        if new_status == RunStatus.CLOSED:
            run.closed_at = now
        return run

    def assign_runner(self, run: Run, runner_user_id: str) -> Run:
        run.runner_user_id = runner_user_id
        run.updated_at = _utcnow()
        return run


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_order(
        self,
        *,
        run_id: str,
        user_id: str,
        order_text: str,
        is_final: bool,
    ) -> Order:
        existing = (
            self._session.execute(
                select(Order).where(Order.run_id == run_id, Order.user_id == user_id)
            ).scalar_one_or_none()
        )
        now = _utcnow()
        if existing:
            existing.order_text = order_text
            existing.is_final = is_final
            existing.canceled_at = None
            existing.updated_at = now
            return existing
        order = Order(
            run_id=run_id,
            user_id=user_id,
            order_text=order_text,
            is_final=is_final,
        )
        order.created_at = now
        order.updated_at = now
        self._session.add(order)
        return order

    def cancel(self, order: Order) -> Order:
        order.canceled_at = _utcnow()
        order.updated_at = order.canceled_at
        return order

    def list_active_orders(self, run_id: str) -> Sequence[Order]:
        return (
            self._session.execute(
                select(Order).where(Order.run_id == run_id, Order.canceled_at.is_(None))
            )
            .scalars()
            .all()
        )


class UserPreferenceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_preference(
        self, *, user_id: str, channel_id: str, order_text: str, last_used_at: datetime | None = None
    ) -> UserPreference:
        preference = (
            self._session.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id, UserPreference.channel_id == channel_id
                )
            ).scalar_one_or_none()
        )
        now = _utcnow()
        last_used = last_used_at or now
        if preference:
            preference.last_order_text = order_text
            preference.last_used_at = last_used
            preference.updated_at = now
            return preference
        preference = UserPreference(
            user_id=user_id,
            channel_id=channel_id,
            last_order_text=order_text,
            last_used_at=last_used,
        )
        preference.created_at = now
        preference.updated_at = now
        self._session.add(preference)
        return preference


class RunnerStatsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def increment(
        self, *, user_id: str, channel_id: str, served_at: datetime | None = None
    ) -> RunnerStat:
        stat = (
            self._session.execute(
                select(RunnerStat).where(
                    RunnerStat.user_id == user_id, RunnerStat.channel_id == channel_id
                )
            ).scalar_one_or_none()
        )
        now = served_at or _utcnow()
        if stat:
            stat.runs_served_count += 1
            stat.last_run_at = now
            stat.updated_at = now
            return stat
        stat = RunnerStat(
            user_id=user_id,
            channel_id=channel_id,
            runs_served_count=1,
            last_run_at=now,
        )
        stat.created_at = now
        stat.updated_at = now
        self._session.add(stat)
        return stat

    def list_for_channel(self, channel_id: str) -> Sequence[RunnerStat]:
        return (
            self._session.execute(
                select(RunnerStat).where(RunnerStat.channel_id == channel_id)
            )
            .scalars()
            .all()
        )


class ChannelAdminActionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        channel_id: str,
        admin_user_id: str,
        action_type: str,
        action_details: dict[str, object],
    ) -> ChannelAdminAction:
        action = ChannelAdminAction(
            channel_id=channel_id,
            admin_user_id=admin_user_id,
            action_type=action_type,
            action_details=action_details,
        )
        self._session.add(action)
        return action

    def list_actions(self, channel_id: str) -> Iterable[ChannelAdminAction]:
        return (
            self._session.execute(
                select(ChannelAdminAction)
                .where(ChannelAdminAction.channel_id == channel_id)
                .order_by(ChannelAdminAction.created_at.desc())
            )
            .scalars()
            .all()
        )
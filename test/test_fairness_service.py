from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from coffeebuddy.core.runs.exceptions import RunnerSelectionError
from coffeebuddy.infra.db.models import Base, Channel, RunnerStat, User
from coffeebuddy.services.fairness.service import FairnessService


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _create_user(session, slack_id: str, display_name: str) -> User:
    now = _utcnow()
    user = User(
        id=uuid4(),
        slack_user_id=slack_id,
        display_name=display_name,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.commit()
    return user


def _create_channel(session, name: str = "coffee-pilot") -> Channel:
    now = _utcnow()
    channel = Channel(
        id=uuid4(),
        slack_channel_id=f"C{name.upper()}",
        name=name,
        enabled=True,
        reminder_offset_minutes=5,
        fairness_window_runs=5,
        data_retention_days=90,
        reminders_enabled=True,
        last_call_enabled=True,
        last_call_lead_minutes=None,
        created_at=now,
        updated_at=now,
    )
    session.add(channel)
    session.commit()
    return channel


def _create_runner_stat(
    session, channel: Channel, user: User, *, runs: int, last_run_delta: timedelta
) -> RunnerStat:
    now = _utcnow()
    stat = RunnerStat(
        id=uuid4(),
        channel_id=channel.id,
        user_id=user.id,
        runs_served_count=runs,
        last_run_at=now - last_run_delta,
        created_at=now - last_run_delta,
        updated_at=now - last_run_delta,
    )
    session.add(stat)
    session.commit()
    return stat


def test_assign_runner_prefers_lowest_runs_served(session):
    channel = _create_channel(session)
    user_a = _create_user(session, "U001", "Alpha")
    user_b = _create_user(session, "U002", "Bravo")
    user_c = _create_user(session, "U003", "Charlie")

    _create_runner_stat(session, channel, user_a, runs=3, last_run_delta=timedelta(days=2))
    _create_runner_stat(session, channel, user_b, runs=1, last_run_delta=timedelta(hours=5))

    now = _utcnow()
    fairness = FairnessService(session=session, clock=lambda: now)

    decision = fairness.assign_runner(
        channel_id=str(channel.id),
        participant_user_ids=[str(user_a.id), str(user_b.id), str(user_c.id)],
        last_runner_id=None,
        allow_immediate_repeat=False,
    )

    assert decision.runner_user_id == str(user_c.id)
    stat = session.scalar(
        select(RunnerStat).where(
            RunnerStat.channel_id == channel.id,
            RunnerStat.user_id == user_c.id,
        )
    )
    assert stat is not None
    assert stat.runs_served_count == 1
    assert stat.last_run_at == now


def test_assign_runner_skips_previous_runner_when_not_allowed(session):
    channel = _create_channel(session)
    user_prev = _create_user(session, "U010", "Prev")
    user_candidate = _create_user(session, "U011", "Next")

    _create_runner_stat(session, channel, user_prev, runs=0, last_run_delta=timedelta(hours=1))

    now = _utcnow()
    fairness = FairnessService(session=session, clock=lambda: now)

    decision = fairness.assign_runner(
        channel_id=str(channel.id),
        participant_user_ids=[str(user_prev.id), str(user_candidate.id)],
        last_runner_id=str(user_prev.id),
        allow_immediate_repeat=False,
    )

    assert decision.runner_user_id == str(user_candidate.id)
    assert "Previous runner excluded" in decision.rationale


def test_assign_runner_allows_repeat_when_only_candidate(session):
    channel = _create_channel(session)
    solo_user = _create_user(session, "U020", "Solo")

    fairness = FairnessService(session=session, clock=_utcnow)

    decision = fairness.assign_runner(
        channel_id=str(channel.id),
        participant_user_ids=[str(solo_user.id)],
        last_runner_id=str(solo_user.id),
        allow_immediate_repeat=False,
    )

    assert decision.runner_user_id == str(solo_user.id)


def test_assign_runner_requires_participants(session):
    channel = _create_channel(session)
    fairness = FairnessService(session=session, clock=_utcnow)

    with pytest.raises(RunnerSelectionError):
        fairness.assign_runner(
            channel_id=str(channel.id),
            participant_user_ids=[],
            last_runner_id=None,
            allow_immediate_repeat=False,
        )